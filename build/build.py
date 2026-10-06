#!/usr/bin/env python3
"""Builds every edition of the business card maker into dist/<folder>/.

    python3 build/build.py              # all editions (public + build/editions.local.json)
    python3 build/build.py en bn        # only these
    python3 build/build.py --no-minify  # readable output, for debugging

Needs Python 3.8+ and Node.js 18+ (for minifying; run `npm install` once).
"""
import base64, gzip, hashlib, json, os, re, shutil, subprocess, sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, BUILD, PUBLIC, SERVER, DIST = (os.path.join(ROOT, d) for d in ('src', 'build', 'public', 'server', 'dist'))
sys.path.insert(0, BUILD)
sys.path.insert(0, os.path.join(SRC, 'i18n'))
from pwa import pwa_patch  # noqa: E402

OG_VERSION = 3   # bump when public/og-image*.png change, so Facebook, LinkedIn and X refetch them


def read(*p):
    with open(os.path.join(*p), encoding='utf-8') as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def load_editions():
    eds = {k: v for k, v in json.loads(read(BUILD, 'editions.json')).items() if not k.startswith('_')}
    local = os.path.join(BUILD, 'editions.local.json')
    if os.path.exists(local):
        eds.update({k: v for k, v in json.loads(read(local)).items() if not k.startswith('_')})
    return eds


def assemble():
    """The app with its QR library and PDF writer inlined: one self-contained page."""
    src = read(SRC, 'app.html')
    qr = read(ROOT, 'vendor', 'qrcode-generator', 'qrcode.js')
    assert '</script' not in qr.lower()
    assert src.count('/*QRLIB*/') == 1 and src.count('/*PDFWRITER*/') == 1
    return src.replace('/*QRLIB*/', '\n' + qr + '\n').replace('/*PDFWRITER*/', read(SRC, 'pdf-writer.js'))


TEXT = {
    'en': dict(
        title='Free Business Card Maker with QR Code & PDF | AiInfos',
        desc='Design a professional two-sided business card online, free. 148 designs, 20 colors, '
             'a vCard QR code and a 300 dpi print-ready PDF. No sign-up, no watermark.',
        app='Free Business Card Maker', alt_name='Business Card Generator with QR Code', short='Card Maker',
        og_alt='A business card designed with the free business card maker, with a QR code on the back', locale='en_US',
        lang_label='English',
        features=["148 card designs in 35 styles, plus 5 back styles",
                  "Social links (LinkedIn, X, Facebook, Instagram, YouTube, TikTok, GitHub) on the card and in the QR contact",
                  "vCard QR code that saves the contact to a phone", "20 color palettes and custom colors",
                  "13 typefaces: Montserrat, Poppins, Inter, Roboto, Raleway, Nunito, Oswald, Playfair Display, Lora, Merriweather, Syne, Cormorant and Manrope",
                  "Adjustable text size and weight", "300 dpi print-ready PDF with 3 mm bleed", "PNG export of each side",
                  "3.5 x 2 in, 85 x 55 mm and 90 x 55 mm card sizes", "Add the card to Apple Wallet or Google Wallet",
                  "Installable app that works offline"]),
    'bn': dict(
        title='ফ্রি ভিজিটিং কার্ড মেকার: বাংলা ফন্ট, QR কোড ও PDF | AiInfos',
        desc='অনলাইনে ফ্রি ভিজিটিং কার্ড তৈরি করুন। ১৪৮টি ডিজাইন, জনপ্রিয় বাংলা ফন্ট, QR কোড, সোশ্যাল লিংক '
             'আর প্রেসে দেওয়ার মতো ৩০০ ডিপিআই PDF। কোনো অ্যাকাউন্ট বা ওয়াটারমার্ক নেই।',
        app='ফ্রি ভিজিটিং কার্ড মেকার', alt_name='বাংলা বিজনেস কার্ড মেকার, Bangla Business Card Maker', short='কার্ড মেকার',
        og_alt='ফ্রি ভিজিটিং কার্ড মেকারে তৈরি কার্ড, পেছনে QR কোড', locale='bn_BD', lang_label='বাংলা',
        features=["১৪৮টি ভিজিটিং কার্ড ডিজাইন",
                  "জনপ্রিয় বাংলা ফন্ট: নোটো সান্স বাংলা, নোটো সেরিফ বাংলা, অনেক বাংলা, বালু দা, তিরো বাংলা, গালাদা",
                  "কন্টাক্ট সেভ করার QR কোড ও সোশ্যাল লিংক", "৩০০ ডিপিআই প্রিন্ট-রেডি PDF, ৩ মিমি ব্লিডসহ",
                  "Apple Wallet ও Google Wallet", "মোবাইলে অ্যাপ হিসেবে ইনস্টল করা যায়"]),
}


def add_csp(index):
    """Adds a Content Security Policy that allows only this page's own scripts (by SHA-256 fingerprint).
    Injected script is refused even if it reaches the page. frame-ancestors can't be set in a meta tag,
    so the server settings in deploy/ add it as a header."""
    page = read(index)
    hashes = ["'sha256-" + base64.b64encode(hashlib.sha256(js.encode('utf-8')).digest()).decode() + "'"
              for js in re.findall(r'<script>(.*?)</script>', page, re.S)]
    assert not re.search(r'\son[a-z]+=', page.split('<script', 1)[0]), 'inline event handler in the page head'
    csp = '; '.join([
        "default-src 'self'", "script-src 'self' " + ' '.join(hashes),
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com", "font-src https://fonts.gstatic.com",
        "img-src 'self' data: blob:", "connect-src 'self'", "worker-src 'self'", "manifest-src 'self'",
        "object-src 'none'", "base-uri 'none'", "form-action 'none'", "upgrade-insecure-requests"])
    page = page.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="{csp}">', 1)
    write(index, page)


def build(eid, ed, eds, minify=True):
    lang = ed.get('lang', 'en'); T = TEXT[lang]; bn = None
    site = ed['site']; out = os.path.join(DIST, ed['folder'])
    alt = eds.get(ed.get('alternate', '')) if ed.get('alternate') else None

    art = assemble()
    if lang == 'bn':
        import bn as bn  # src/i18n/bn.py
        art = bn.translate(art)
    if alt:   # link to the other language in the header
        art = art.replace('<div class="spec" id="spec">',
                          f'<a class="lang-link" href="{alt["site"]}" hreflang="{alt["lang"]}" lang="{alt["lang"]}">{TEXT[alt["lang"]]["lang_label"]}</a>\n  <div class="spec" id="spec">', 1)
    a = art.index('  const EXAMPLE = {'); b = art.index('};', a) + 2
    art = art[:a] + '  const EXAMPLE = ' + json.dumps(ed['example'], ensure_ascii=False) + ';' + art[b:]
    assert art.count('const KEY = "cardpress.v2";') == 1
    art = art.replace('const KEY = "cardpress.v2";', 'const KEY = ' + json.dumps(ed['storageKey']) + ';')

    body = art.replace(re.search(r'<title>.*?</title>', art).group(0), '', 1)
    links = re.findall(r'<link [^>]*>\n?', body)
    for l in links:
        body = body.replace(l, '', 1)
    body = pwa_patch(body.strip())
    if bn:
        body = bn.translate_pwa(body)

    og = site + f'og-image.png?v={OG_VERSION}'
    faq = [{"@type": "Question", "name": re.sub('<[^>]+>', '', q).strip(),
            "acceptedAnswer": {"@type": "Answer", "text": re.sub('<[^>]+>', '', a).strip()}}
           for q, a in re.findall(r'<summary>(.*?)</summary>\s*<p>(.*?)</p>', art, re.S)]
    ld = [{
        "@context": "https://schema.org", "@type": "WebApplication", "name": T['app'], "alternateName": T['alt_name'],
        "url": site, "description": T['desc'], "applicationCategory": "DesignApplication",
        "operatingSystem": "Any (runs in a web browser)", "browserRequirements": "Requires JavaScript", "inLanguage": lang,
        "isAccessibleForFree": True,
        "publisher": {"@type": "Organization", "name": "AiInfos", "url": "https://aiinfos.com"},
        "author": {"@type": "Person", "name": "Iqbal Mahmud", "alternateName": "ইকবাল মাহমুদ", "url": "https://www.IqbalMahmud.com"},
        "creator": {"@type": "Person", "name": "Iqbal Mahmud", "url": "https://www.IqbalMahmud.com"},
        "contributor": {"@type": "Person", "name": "Dawn C Simmons", "url": "https://www.DawnCSimmons.com", "description": "Suggested the idea"},
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "image": og, "screenshot": og,
        "featureList": T['features']}, {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq}]
    ld_json = json.dumps(ld, ensure_ascii=False, indent=1).replace('</', '<\\/')
    alt_links = ''
    if alt:   # hreflang pairs so Google shows each visitor the right language
        default = site if lang == 'en' else alt['site']
        alt_links = (f'<link rel="alternate" hreflang="{lang}" href="{site}">\n<link rel="alternate" hreflang="{alt["lang"]}" href="{alt["site"]}">\n'
                     f'<link rel="alternate" hreflang="x-default" href="{default}">\n')
    robots = 'index, follow, max-image-preview:large' if ed.get('index') else 'noindex, follow'
    head = f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{T['title']}</title>
<meta name="description" content="{T['desc']}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{ed.get('canonical') or site}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="AiInfos">
<meta property="og:title" content="{T['title']}">
<meta property="og:description" content="{T['desc']}">
<meta property="og:url" content="{site}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{T['og_alt']}">
<meta property="og:locale" content="{T['locale']}">
{alt_links}<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{T['title']}">
<meta name="twitter:description" content="{T['desc']}">
<meta name="twitter:image" content="{og}">
<meta name="theme-color" content="#2E5A4D">
<link rel="manifest" href="manifest.json">
<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{T['short']}">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
{''.join(l if l.endswith(chr(10)) else l + chr(10) for l in links)}<script>window.CARD_WALLET = {{ endpoint: "api/wallet.php" }};</script>
<script type="application/ld+json">
{ld_json}
</script>
<style>body{{margin:0}} img{{max-width:100%}} [hidden]{{display:none!important}} :root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}</style>'''
    page = f'<!doctype html>\n<html lang="{lang}">\n<head>\n{head}\n</head>\n<body>\n{body}\n</body>\n</html>\n'

    shutil.rmtree(out, ignore_errors=True)
    index = os.path.join(out, 'index.html')
    write(index, page)
    if minify:
        subprocess.run(['node', os.path.join(BUILD, 'minify.js'), index], check=True)
    add_csp(index)
    with open(index, 'rb') as f_in, gzip.GzipFile(index + '.gz', 'wb', compresslevel=9, mtime=0) as f_out:
        f_out.write(f_in.read())   # served as-is by the deploy settings, so nothing is compressed per visit

    # static files
    shutil.copytree(os.path.join(PUBLIC, 'icons'), os.path.join(out, 'icons'))
    shutil.copy(os.path.join(PUBLIC, 'og-image-bn.png' if lang == 'bn' else 'og-image.png'), os.path.join(out, 'og-image.png'))
    manifest = json.loads(read(PUBLIC, 'manifest.json'))
    if lang == 'bn':
        manifest.update(name='ভিজিটিং কার্ড মেকার – AiInfos', short_name='কার্ড মেকার', lang='bn',
                        description='QR কোডসহ দুই পাশের ভিজিটিং কার্ড বানান, প্রিন্ট-রেডি PDF ডাউনলোড করুন। ফ্রি, কোনো অ্যাকাউন্ট লাগে না।')
    write(os.path.join(out, 'manifest.json'), json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    write(os.path.join(out, 'sw.js'), read(SRC, 'sw.template.js').replace('__PREFIX__', ed['cachePrefix']).replace('__NAME__', T['app']))

    # wallet endpoint and server settings, with paths for this edition's address
    shutil.copytree(os.path.join(SERVER, 'api'), os.path.join(out, 'api'),
                    ignore=shutil.ignore_patterns('config.php', '*.pem', '*.p12', '*.key', '*.cer', '*.json', 'keys', '*~', '*.bak'))
    setup = os.path.join(DIST, 'server-setup', ed['folder'])
    shutil.rmtree(setup, ignore_errors=True)
    os.makedirs(setup)
    shutil.copy(os.path.join(SERVER, 'WALLET-SETUP.md'), setup)
    path = urlparse(site).path or '/'
    for f in os.listdir(os.path.join(SERVER, 'deploy')):
        t = read(SERVER, 'deploy', f).replace('/business-card-maker/', path)
        t = t.replace('the business-card-maker folder', f'the {path.strip("/").split("/")[-1] or "site"} folder')
        write(os.path.join(setup, f), t)
    shutil.copy(os.path.join(ROOT, 'LICENSE'), out)
    if ed.get('index'):
        write(os.path.join(out, 'sitemap.xml'), '<?xml version="1.0" encoding="UTF-8"?>\n'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
              f'  <url>\n    <loc>{site}</loc>\n'
              + (f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{site}"/>\n'
                 f'    <xhtml:link rel="alternate" hreflang="{alt["lang"]}" href="{alt["site"]}"/>\n' if alt else '')
              + '    <changefreq>monthly</changefreq>\n  </url>\n</urlset>\n')
    size = os.path.getsize(index)
    print(f'{eid:>14}  ->  dist/{ed["folder"]}/  ({size // 1024} KB, {os.path.getsize(index + ".gz") // 1024} KB gzipped)  {site}')


def main(argv):
    minify = '--no-minify' not in argv
    eds = load_editions()
    wanted = [a for a in argv if not a.startswith('--')] or list(eds)
    for eid in wanted:
        if eid not in eds:
            raise SystemExit(f'Unknown edition "{eid}". Known: {", ".join(eds)}')
        build(eid, eds[eid], eds, minify)


if __name__ == '__main__':
    main(sys.argv[1:])
