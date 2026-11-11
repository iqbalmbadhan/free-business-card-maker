#!/usr/bin/env python3
"""Builds the self-contained offline mobile app bundle into dist/mobile/ for Capacitor (iOS & Android).

- Runs the main unified multi-language build (dist/business-card-maker/)
- Copies the web assets into dist/mobile/
- Bundles all local @fontsource .woff2 fonts into dist/mobile/fonts/ with a local fonts/fonts.css
- Replaces the external Google Fonts stylesheet link with local fonts/fonts.css so all 27 fonts work 100% offline
- Updates the Content-Security-Policy SHA-256 hashes and directives for Capacitor WebViews
"""
import base64
import hashlib
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as web_build  # noqa: E402

FAMILIES = {
    'Hind Siliguri': 'hind-siliguri',
    'Anek Bangla': 'anek-bangla',
    'Noto Sans Bengali': 'noto-sans-bengali',
    'Noto Serif Bengali': 'noto-serif-bengali',
    'Baloo Da 2': 'baloo-da-2',
    'Tiro Bangla': 'tiro-bangla',
    'Galada': 'galada',
    'Geist': 'geist-sans',
    'Geist Mono': 'geist-mono',
    'Syne': 'syne',
    'DM Sans': 'dm-sans',
    'Manrope': 'manrope',
    'Work Sans': 'work-sans',
    'Cormorant Garamond': 'cormorant-garamond',
    'Montserrat': 'montserrat',
    'Open Sans': 'open-sans',
    'Poppins': 'poppins',
    'Inter': 'inter',
    'Roboto': 'roboto',
    'Raleway': 'raleway',
    'Lato': 'lato',
    'Nunito': 'nunito',
    'Oswald': 'oswald',
    'Playfair Display': 'playfair-display',
    'Lora': 'lora',
    'Source Sans 3': 'source-sans-3',
    'Merriweather': 'merriweather',
}

RANGES = {
    'bengali': 'U+0951-0952,U+0964-0965,U+0980-09FE,U+1CD0-1CF9,U+200C-200D,U+20B9,U+25CC,U+A8F1',
    'latin': 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD',
}


def bundle_fonts(mobile_dir):
    fontsource_root = os.path.join(ROOT, 'node_modules', '@fontsource')
    fonts_out = os.path.join(mobile_dir, 'fonts')
    os.makedirs(fonts_out, exist_ok=True)
    rules = []
    copied = 0
    for fam, pkg_dir in FAMILIES.items():
        for weight in (400, 500, 600, 700, 800):
            for sub in ('bengali', 'latin'):
                fname = f'{pkg_dir}-{sub}-{weight}-normal.woff2'
                src = os.path.join(fontsource_root, pkg_dir, 'files', fname)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(fonts_out, fname))
                    copied += 1
                    rules.append(
                        f'@font-face{{font-family:"{fam}";font-weight:{weight};font-style:normal;'
                        f'font-display:swap;unicode-range:{RANGES[sub]};src:url("{fname}") format("woff2");}}'
                    )
    css_path = os.path.join(fonts_out, 'fonts.css')
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(rules) + '\n')
    return copied


def patch_mobile_index(index_path):
    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Remove Google Fonts preconnect links and point #fontCss to local bundled fonts/fonts.css
    html = re.sub(r'<link[^>]*href="https://fonts\.googleapis\.com"[^>]*>\s*', '', html)
    html = re.sub(r'<link[^>]*href="https://fonts\.gstatic\.com"[^>]*>\s*', '', html)
    html = re.sub(
        r'<link[^>]*id="fontCss"[^>]*>',
        '<link rel="stylesheet" id="fontCss" href="fonts/fonts.css">',
        html,
        count=1,
    )

    # Recompute CSP with 'self' font-src and style-src so offline fonts and Capacitor bridges work cleanly
    html = re.sub(r'<meta http-equiv="Content-Security-Policy" content="[^"]*">\n?', '', html, count=1)
    hashes = [
        "'sha256-" + base64.b64encode(hashlib.sha256(js.encode('utf-8')).digest()).decode() + "'"
        for js in re.findall(r'<script>(.*?)</script>', html, re.S)
    ]
    csp = '; '.join([
        "default-src 'self' capacitor: http://localhost https://localhost",
        "script-src 'self' " + ' '.join(hashes),
        "style-src 'self' 'unsafe-inline'",
        "font-src 'self' data:",
        "img-src 'self' data: blob:",
        "connect-src 'self' https://api.country.is https://get.geojs.io",
        "worker-src 'self'",
        "manifest-src 'self'",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'none'",
    ])
    html = html.replace(
        '<meta charset="utf-8">',
        f'<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="{csp}">',
        1,
    )
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    web_build.main(['en'])
    web_out = os.path.join(ROOT, 'dist', 'business-card-maker')
    mobile_out = os.path.join(ROOT, 'dist', 'mobile')
    shutil.rmtree(mobile_out, ignore_errors=True)
    os.makedirs(mobile_out, exist_ok=True)

    for item in ('index.html', 'manifest.json', 'sw.js', 'og-image.png', 'LICENSE'):
        src = os.path.join(web_out, item)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(mobile_out, item))
    shutil.copytree(os.path.join(web_out, 'icons'), os.path.join(mobile_out, 'icons'))

    copied_fonts = bundle_fonts(mobile_out)
    patch_mobile_index(os.path.join(mobile_out, 'index.html'))
    size_kb = os.path.getsize(os.path.join(mobile_out, 'index.html')) // 1024
    print(f'        mobile  ->  dist/mobile/  ({size_kb} KB index.html + {copied_fonts} offline .woff2 font files)')


if __name__ == '__main__':
    main()
