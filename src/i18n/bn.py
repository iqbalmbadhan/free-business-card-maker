# -*- coding: utf-8 -*-
"""Bengali (বাংলা) edition: turns the English build into a fully Bengali one.

Every replacement must match the English source; if the source changes and a string
no longer matches, the build stops so nothing ships half-translated.
"""
import json, re

FONT_LINK_EN = re.compile(r'href="https://fonts\.googleapis\.com/css2\?[^"]+"')
FONT_LINK_BN = ('href="https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;500;600;700&family=Noto+Serif+Bengali:wght@400;500;600;700'
                '&family=Anek+Bangla:wght@400;500;600;700&family=Baloo+Da+2:wght@400;500;600;700'
                '&family=Tiro+Bangla&family=Galada&family=Geist+Mono:wght@400;500&display=swap"')

# Card typefaces: popular Bengali families from Google Fonts (free, open licence).
# Keys stay the same as the English edition because the designs refer to them.
PAIRS_BN = '''  const PAIRS = {
    geometric: { name: "আধুনিক",     d: '"Anek Bangla"', dw: 700, b: '"Anek Bangla"', bw: 400, dk: 0.95, dfb: "sans-serif", sample: "অআ" },
    classic:   { name: "ঐতিহ্যবাহী", d: '"Tiro Bangla"', dw: 400, b: '"Noto Serif Bengali"', bw: 400, dk: 1.05, dfb: "serif", sample: "অআ" },
    modern:    { name: "পরিচ্ছন্ন",   d: '"Noto Sans Bengali"', dw: 700, b: '"Noto Sans Bengali"', bw: 400, dk: 0.95, dfb: "sans-serif", sample: "অআ" },
    friendly:  { name: "গোলগাল",     d: '"Baloo Da 2"', dw: 700, b: '"Baloo Da 2"', bw: 400, dk: 1.0, dfb: "sans-serif", sample: "অআ" },
    artistic:  { name: "শৈল্পিক",     d: '"Galada"', dw: 400, b: '"Noto Sans Bengali"', bw: 400, dk: 1.1, dfb: "cursive", sample: "অআ" }
  };'''

L10N = {
    "fontSample": "অআকখগ Aa0@",
    "digits": dict(zip("0123456789", "০১২৩৪৫৬৭৮৯")),
    "contactLabels": {"T": "ফোন", "E": "ইমেইল", "W": "ওয়েব", "A": "ঠিকানা"},
    "cats": {"All": "সব", "Classic": "ক্লাসিক", "Corporate": "কর্পোরেট", "Minimal": "মিনিমাল", "Elegant": "রুচিশীল",
             "Luxury": "অভিজাত", "Creative": "সৃজনশীল", "Bold": "জোরালো", "Nature": "প্রকৃতি", "Tech": "টেক", "Playful": "রঙিন"},
    "templates": {"ledger": "খাতা", "split": "দুই ভাগ", "monogram": "মনোগ্রাম", "band": "পট্টি", "frame": "ফ্রেম",
                  "corner": "কোণা", "centered": "মাঝখানে", "bold": "জোরালো"},
    "palettes": {"meghna": "মেঘনা", "shapla": "শাপলা", "paddy": "ধানক্ষেত", "turmeric": "হলুদ", "graphite": "গ্রাফাইট",
                 "brass": "পিতল", "indigo": "নীল", "plum": "জাম", "lilac": "বেগুনি", "ruby": "রুবি", "coral": "প্রবাল",
                 "rust": "মরিচা", "sand": "বালু", "olive": "জলপাই", "forest": "বনানী", "teal": "সবুজাভ নীল", "ocean": "সাগর",
                 "sky": "আকাশ", "midnight": "মধ্যরাত", "onyx": "কষ্টিপাথর"},
    "families": {"Sidebar": "পাশের রেখা", "Edge Bar": "কিনারা রেখা", "Color Block": "রঙের ব্লক", "Header Band": "উপরের পট্টি",
                 "Footer Band": "নিচের পট্টি", "Diagonal": "আড়াআড়ি", "Corner Cut": "কোণা কাটা", "Twin Corners": "জোড়া কোণা",
                 "Waves": "ঢেউ", "Side Wave": "পাশের ঢেউ", "Bubbles": "বুদবুদ", "Low Poly": "লো-পলি", "Pinstripe": "সরু ডোরা",
                 "Halftone": "হাফটোন", "Gradient": "গ্রেডিয়েন্ট", "Gold Frame": "সোনালি ফ্রেম", "Brushstroke": "তুলির টান",
                 "Botanical": "লতাপাতা", "Honeycomb": "মৌচাক", "Orbit": "কক্ষপথ", "Split Tone": "দুই রং", "Ripples": "তরঙ্গ",
                 "Chevron": "শেভরন", "Hairline": "সূক্ষ্ম রেখা", "Neon Line": "নিয়ন রেখা", "Confetti": "কনফেটি", "Ribbon": "ফিতা",
                 "Blueprint": "নকশা খাতা", "Circuit": "সার্কিট", "Crest": "অর্ধচন্দ্র", "Triple Bar": "তিন রেখা",
                 "Brackets": "বন্ধনী", "Mosaic": "মোজাইক", "Sunburst": "সূর্যরশ্মি", "Zigzag": "আঁকাবাঁকা"},
    "backs": {"pro": {"name": "প্রফেশনাল", "sub": "লোগো, লিংক ও QR কোড"}, "solid": {"name": "এক রং"},
              "lines": {"name": "রেখা"}, "dots": {"name": "ফোঁটা"}, "light": {"name": "হালকা"}},
}

# (English, Bengali). Replaced everywhere it appears; each must appear at least once.
T = [
    # ---------- header and preview ----------
    ('<a class="skip" href="#panel">Skip to card settings</a>', '<a class="skip" href="#panel">কার্ডের সেটিংসে যান</a>'),
    ('<span class="brand-name"><span class="brand-free">Free </span>Business Card Maker</span> <span class="brand-by">by AiInfos</span>', '<span class="brand-name"><span class="brand-free">ফ্রি </span>ভিজিটিং কার্ড মেকার</span> <span class="brand-by">AiInfos</span>'),
    ('<div class="spec" id="spec">3.5 × 2 in · 3 mm bleed · 300 dpi export</div>', '<div class="spec" id="spec">৩.৫ × ২ ইঞ্চি · ৩ মিমি ব্লিড · ৩০০ ডিপিআই</div>'),
    ('aria-label="Card preview"', 'aria-label="কার্ডের প্রিভিউ"'),
    ('aria-label="Card side"', 'aria-label="কার্ডের দিক"'),
    ('aria-pressed="true">Front</button>', 'aria-pressed="true">সামনে</button>'),
    ('aria-pressed="false">Back</button>', 'aria-pressed="false">পেছনে</button>'),
    ('<figcaption><span>Front</span>', '<figcaption><span>সামনের দিক</span>'),
    ('<figcaption><span>Back</span>', '<figcaption><span>পেছনের দিক</span>'),
    ('aria-label="Front of business card"', 'aria-label="ভিজিটিং কার্ডের সামনের দিক"'),
    ('aria-label="Back of business card"', 'aria-label="ভিজিটিং কার্ডের পেছনের দিক"'),
    ('<span><i></i>Trim line</span><span><i class="safe"></i>Safe zone: keep text inside</span><span>Shaded edge is bleed, cut off when trimmed</span>',
     '<span><i></i>কাটার দাগ</span><span><i class="safe"></i>নিরাপদ সীমা: লেখা এর ভেতরে রাখুন</span><span>ছায়া দেওয়া কিনারা ব্লিড, কাটার সময় বাদ যায়</span>'),
    ('id="exPdf" type="button">Download PDF</button>', 'id="exPdf" type="button">PDF ডাউনলোড</button>'),
    ('id="exFront" type="button">Front PNG</button>', 'id="exFront" type="button">সামনের PNG</button>'),
    ('id="exBack" type="button">Back PNG</button>', 'id="exBack" type="button">পেছনের PNG</button>'),
    ('<p class="export-note" id="exportNote">300 dpi. The PDF holds both sides, one per page, ready for a print shop.</p>',
     '<p class="export-note" id="exportNote">৩০০ ডিপিআই। PDF-এ দুই পাতায় দুই দিক থাকে, সরাসরি প্রেসে দেওয়া যায়।</p>'),
    # ---------- section bar ----------
    ('aria-label="Card settings"', 'aria-label="কার্ডের সেটিংস"'),
    ('aria-label="Settings sections"', 'aria-label="সেটিংসের অংশ"'),
    # ---------- About & FAQ sheet, footer ----------
    ('<span class="help-txt">About &amp; FAQ</span>', '<span class="help-txt">পরিচিতি ও প্রশ্নোত্তর</span>'),
    ('<strong id="helpTitle">About &amp; FAQ</strong>', '<strong id="helpTitle">পরিচিতি ও প্রশ্নোত্তর</strong>'),
    ('id="helpClose" type="button" aria-label="Close">', 'id="helpClose" type="button" aria-label="বন্ধ করুন">'),
    ('<p>Built by <a href="https://www.IqbalMahmud.com">Iqbal Mahmud</a> · Inspired by <a href="https://www.DawnCSimmons.com">Dawn C Simmons</a></p>',
     '<p>তৈরি করেছেন <a href="https://www.IqbalMahmud.com">ইকবাল মাহমুদ</a> · অনুপ্রেরণা <a href="https://www.DawnCSimmons.com">Dawn C Simmons</a></p>'),
    # ---------- phone: bottom tab bar and Download screen ----------
    ('<nav class="tabbar" id="tabbar" aria-label="Card sections">', '<nav class="tabbar" id="tabbar" aria-label="কার্ডের অংশ">'),
    ('<span class="tl">Details</span>', '<span class="tl">তথ্য</span>'),
    ('<span class="tl">Design</span>', '<span class="tl">ডিজাইন</span>'),
    ('<span class="tl">Style</span>', '<span class="tl">স্টাইল</span>'),
    ('<span class="tl">Back</span>', '<span class="tl">পেছন</span>'),
    ('<span class="tl">Download</span>', '<span class="tl">ডাউনলোড</span>'),
    ('<h2>Download your card</h2>', '<h2>কার্ড ডাউনলোড করুন</h2>'),
    ('data-proxy="exPdf">Download print PDF</button>', 'data-proxy="exPdf">প্রিন্টের PDF ডাউনলোড</button>'),
    ('data-proxy="exFront">Front PNG</button>', 'data-proxy="exFront">সামনের PNG</button>'),
    ('data-proxy="exBack">Back PNG</button>', 'data-proxy="exBack">পেছনের PNG</button>'),
    ('<p class="hint">300 dpi images. The PDF holds both sides, one per page, ready for a print shop.</p>',
     '<p class="hint">৩০০ ডিপিআই ছবি। PDF-এ দুই পাতায় দুই দিক থাকে, সরাসরি প্রেসে দেওয়া যায়।</p>'),
    ('data-to="g-details">Details</button>', 'data-to="g-details">তথ্য</button>'),
    ('data-to="g-social">Social</button>', 'data-to="g-social">সোশ্যাল</button>'),
    ('data-to="g-logo">Logo</button>', 'data-to="g-logo">লোগো</button>'),
    ('data-to="g-design">Design</button>', 'data-to="g-design">ডিজাইন</button>'),
    ('data-to="g-type">Text</button>', 'data-to="g-type">লেখা</button>'),
    ('data-to="g-color">Color</button>', 'data-to="g-color">রং</button>'),
    ('data-to="g-back">Back &amp; QR</button>', 'data-to="g-back">পেছন ও QR</button>'),
    ('data-to="g-print">Print</button>', 'data-to="g-print">প্রিন্ট</button>'),
    ('data-wallet-nav hidden>Wallet</button>', 'data-wallet-nav hidden>ওয়ালেট</button>'),
    ('data-to="g-saved">Saved</button>', 'data-to="g-saved">সংরক্ষণ</button>'),
    # ---------- details ----------
    ('<h2>Details</h2>', '<h2>আপনার তথ্য</h2>'),
    ('id="loadExample" type="button">Reset to default</button>', 'id="loadExample" type="button">শুরুর তথ্যে ফিরুন</button>'),
    ('id="clearAll" type="button">Clear</button>', 'id="clearAll" type="button">মুছুন</button>'),
    ('<label for="f-name">Full name</label>', '<label for="f-name">পুরো নাম</label>'),
    ('<label for="f-title">Job title</label>', '<label for="f-title">পদবি</label>'),
    ('<label for="f-company">Company</label>', '<label for="f-company">প্রতিষ্ঠান</label>'),
    ('<label for="f-phone">Phone</label>', '<label for="f-phone">মোবাইল</label>'),
    ('<label for="f-email">Email</label>', '<label for="f-email">ইমেইল</label>'),
    ('<label for="f-website">Website</label>', '<label for="f-website">ওয়েবসাইট</label>'),
    ('<label for="f-address">Address</label>', '<label for="f-address">ঠিকানা</label>'),
    ('<label for="f-tagline">Tagline (back of card)</label>', '<label for="f-tagline">স্লোগান (কার্ডের পেছনে)</label>'),
    # ---------- social ----------
    ('<h2>Social links</h2>', '<h2>সোশ্যাল লিংক</h2>'),
    ('id="socialClear" type="button" hidden>Clear links</button>', 'id="socialClear" type="button" hidden>লিংক মুছুন</button>'),
    ("Type a username or paste a link. Links appear on the back of the card and go into the QR code, so they're saved with your contact.",
     "ইউজারনেম লিখুন বা পুরো লিংক পেস্ট করুন। লিংকগুলো কার্ডের পেছনে ছাপা হয় এবং QR কোডেও যায়, তাই কন্টাক্টের সঙ্গে সেভ হয়।"),
    ('{ id: "x",         name: "X (Twitter)",', '{ id: "x",         name: "X (টুইটার)",'),
    ('ph: "in/yourname" }', 'ph: "in/apnar-nam" }'),
    ('ph: "@yourname" }', 'ph: "@apnar_nam" }'),
    ('ph: "yourpage" }', 'ph: "apnar.page" }'),
    ('ph: "@yourchannel", at: true }', 'ph: "@apnar_channel", at: true }'),
    ('ph: "@yourname", at: true }', 'ph: "@apnar_nam", at: true }'),
    ('ph: "yourname" }', 'ph: "apnar-nam" }'),
    # ---------- logo ----------
    ('<h2>Logo</h2>', '<h2>লোগো</h2>'),
    ('<div class="logo-thumb" id="logoThumb">None</div>', '<div class="logo-thumb" id="logoThumb">নেই</div>'),
    ('<span class="btn file-btn">Upload image<input', '<span class="btn file-btn">ছবি আপলোড<input'),
    ('aria-label="Upload logo image"', 'aria-label="লোগোর ছবি আপলোড"'),
    ('id="logoRemove" type="button" hidden>Remove</button>', 'id="logoRemove" type="button" hidden>সরান</button>'),
    ('A transparent PNG or SVG works best. Without a logo, the card uses your company name or initials.',
     'স্বচ্ছ ব্যাকগ্রাউন্ডের PNG বা SVG সবচেয়ে ভালো দেখায়। লোগো না দিলে কার্ডে প্রতিষ্ঠানের নাম বা আদ্যক্ষর থাকবে।'),
    # ---------- design ----------
    ('<h2>Design</h2>', '<h2>ডিজাইন</h2>'),
    ('<span>Current design</span><strong id="curName">Ledger</strong>', '<span>বর্তমান ডিজাইন</span><strong id="curName">খাতা</strong>'),
    ('id="browseBtn" type="button">Browse all designs</button>', 'id="browseBtn" type="button">সব ডিজাইন দেখুন</button>'),
    ('<label for="f-mono">Letters on the design</label>', '<label for="f-mono">ডিজাইনের অক্ষর</label>'),
    ('placeholder="Your initials">', 'placeholder="নামের আদ্যক্ষর">'),
    ('This design shows letters. Type the ones you want, up to 4 characters, or leave it empty to use your initials.',
     'এই ডিজাইনে অক্ষর দেখানো হয়। পছন্দের অক্ষর লিখুন, সর্বোচ্চ ৪টি; খালি রাখলে নামের আদ্যক্ষর বসবে।'),
    ('<p class="hint">Classic layouts</p>', '<p class="hint">ক্লাসিক লেআউট</p>'),
    ('<h2>Typeface</h2>', '<h2>ফন্ট</h2>'),
    # ---------- text size ----------
    ('<h2>Text size and weight</h2>', '<h2>লেখার আকার ও মোটা-চিকন</h2>'),
    ('id="tsReset" type="button">Reset</button>', 'id="tsReset" type="button">আগের মতো</button>'),
    ('<span class="showlabel">Show on front</span>', '<span class="showlabel">সামনে দেখাবে</span>'),
    ('id="sh-phone">Phone</label>', 'id="sh-phone">মোবাইল</label>'),
    ('id="sh-email">Email</label>', 'id="sh-email">ইমেইল</label>'),
    ('id="sh-website">Website</label>', 'id="sh-website">ওয়েবসাইট</label>'),
    ('id="sh-address">Address</label>', 'id="sh-address">ঠিকানা</label>'),
    ('id="sh-labels">T / E / W / A labels</label>', 'id="sh-labels">ফোন / ইমেইল / ওয়েব / ঠিকানা লেবেল</label>'),
    ('Hidden details still go into the QR code. Text that gets too long for its space shrinks to fit.',
     'লুকানো তথ্যও QR কোডে থাকে। জায়গার চেয়ে লম্বা লেখা নিজে থেকেই ছোট হয়ে যায়।'),
    ('{ id: "name", label: "Name",', '{ id: "name", label: "নাম",'),
    ('{ id: "title", label: "Job title",', '{ id: "title", label: "পদবি",'),
    ('{ id: "company", label: "Company",', '{ id: "company", label: "প্রতিষ্ঠান",'),
    ('{ id: "contacts", label: "Contact details",', '{ id: "contacts", label: "যোগাযোগ",'),
    ('{ id: "tagline", label: "Tagline",', '{ id: "tagline", label: "স্লোগান",'),
    ('const WEIGHTS = [["", "Auto"], ["400", "Regular"], ["500", "Medium"], ["600", "Semibold"], ["700", "Bold"], ["800", "Extra bold"]];',
     'const WEIGHTS = [["", "স্বয়ংক্রিয়"], ["400", "সাধারণ"], ["500", "মাঝারি"], ["600", "আধা মোটা"], ["700", "মোটা"], ["800", "খুব মোটা"]];'),
    ('sel.setAttribute("aria-label", el.label + " weight");', 'sel.setAttribute("aria-label", el.label + " – মোটা-চিকন");'),
    ('out.textContent = rng.value + "%";', 'out.textContent = num(rng.value) + "%";'),
    ('$("ts-" + el.id + "-o").textContent = pct + "%";', '$("ts-" + el.id + "-o").textContent = num(pct) + "%";'),
    # ---------- color, back, QR ----------
    ('<h2>Color</h2>', '<h2>রং</h2>'),
    ('id="c-accent">Accent</label>', 'id="c-accent">মূল রং</label>'),
    ('id="c-paper">Paper</label>', 'id="c-paper">কাগজ</label>'),
    ('id="c-ink">Ink</label>', 'id="c-ink">কালি</label>'),
    ('btn.setAttribute("aria-label", p.name + " palette");', 'btn.setAttribute("aria-label", p.name + " রং-সেট");'),
    ('<h2>Back style</h2>', '<h2>পেছনের স্টাইল</h2>'),
    ('<h2>QR code on back</h2>', '<h2>পেছনের QR কোড</h2>'),
    ('data-v="vcard">Save contact</button>', 'data-v="vcard">কন্টাক্ট সেভ</button>'),
    ('data-v="url">Website</button>', 'data-v="url">ওয়েবসাইট</button>'),
    ('data-v="none">None</button>', 'data-v="none">কিছু না</button>'),
    ('''<p class="hint" id="qrHint">Scanning adds you straight to the phone's contacts (vCard).</p>''',
     '<p class="hint" id="qrHint">স্ক্যান করলেই আপনার নম্বর ফোনের কন্টাক্টে সেভ হবে (vCard)।</p>'),
    ('''"Your QR code holds a lot of details, so it's very fine. Test-scan a printed copy, or remove a few links or details to make it easier to scan."''',
     '"QR কোডে অনেক তথ্য থাকায় এটি বেশ ঘন হয়েছে। প্রিন্ট করে একবার স্ক্যান করে দেখুন, অথবা কিছু লিংক বা তথ্য কমিয়ে দিন।"'),
    ('''"Scanning adds you straight to the phone's contacts, with your links (vCard)."''', '"স্ক্যান করলেই আপনার নম্বর ও লিংক ফোনের কন্টাক্টে সেভ হবে (vCard)।"'),
    ('"Scanning opens your website."', '"স্ক্যান করলে আপনার ওয়েবসাইট খুলবে।"'),
    ('"Add a website above to fill this QR code."', '"এই QR কোডের জন্য ওপরে ওয়েবসাইট লিখুন।"'),
    ('"The back shows your logo, tagline and website."', '"পেছনে আপনার লোগো, স্লোগান ও ওয়েবসাইট থাকবে।"'),
    # card captions drawn on the back
    ('"Scan to visit" : "Scan to save contact"', '"স্ক্যান করে ওয়েবসাইটে যান" : "স্ক্যান করে কন্টাক্ট সেভ করুন"'),
    ('"Point your phone camera here"', '"ফোনের ক্যামেরা এখানে ধরুন"'),
    # ---------- print ----------
    ('<h2>Print</h2>', '<h2>প্রিন্ট</h2>'),
    ('<label for="p-size">Card size</label>', '<label for="p-size">কার্ডের মাপ</label>'),
    ('<option value="us">3.5 × 2 in (88.9 × 50.8 mm)</option>', '<option value="us">৩.৫ × ২ ইঞ্চি (৮৮.৯ × ৫০.৮ মিমি), বাংলাদেশে প্রচলিত</option>'),
    ('<option value="eu">85 × 55 mm (Europe, ISO)</option>', '<option value="eu">৮৫ × ৫৫ মিমি (ইউরোপ, ISO)</option>'),
    ('<option value="au">90 × 55 mm (Australia, India)</option>', '<option value="au">৯০ × ৫৫ মিমি (ভারত, অস্ট্রেলিয়া)</option>'),
    ('id="p-guides">Show trim and safe-zone guides</label>', 'id="p-guides">কাটার দাগ ও নিরাপদ সীমা দেখান</label>'),
    ('id="p-bleed">Add 3 mm bleed to exports</label>', 'id="p-bleed">ডাউনলোডে ৩ মিমি ব্লিড যোগ করুন</label>'),
    ('Most print shops ask for bleed. Turn it off only for digital use, like email or WhatsApp.',
     'বেশিরভাগ প্রেস ব্লিড চায়। শুধু ইমেইল বা হোয়াটসঅ্যাপে পাঠানোর জন্য হলে বন্ধ রাখুন।'),
    ('us: { w: 88.9, h: 50.8, label: "3.5 × 2 in" }', 'us: { w: 88.9, h: 50.8, label: "৩.৫ × ২ ইঞ্চি" }'),
    ('eu: { w: 85, h: 55, label: "85 × 55 mm" }', 'eu: { w: 85, h: 55, label: "৮৫ × ৫৫ মিমি" }'),
    ('au: { w: 90, h: 55, label: "90 × 55 mm" }', 'au: { w: 90, h: 55, label: "৯০ × ৫৫ মিমি" }'),
    ('$("spec").textContent = `${sz.label} · ${state.bleed ? "3 mm bleed" : "no bleed"} · 300 dpi export`;',
     '$("spec").textContent = `${sz.label} · ${state.bleed ? "৩ মিমি ব্লিড" : "ব্লিড ছাড়া"} · ৩০০ ডিপিআই`;'),
    ('const dims = `${sz.w} × ${sz.h} mm`;', 'const dims = `${num(sz.w)} × ${num(sz.h)} মিমি`;'),
    ('$("exportNote").textContent = `300 dpi${state.bleed ? " with 3 mm bleed" : ""}. The PDF holds both sides, one per page, ready for a print shop.`;',
     '$("exportNote").textContent = `৩০০ ডিপিআই${state.bleed ? ", ৩ মিমি ব্লিডসহ" : ""}। PDF-এ দুই পাতায় দুই দিক থাকে, সরাসরি প্রেসে দেওয়া যায়।`;'),
    # ---------- wallet ----------
    ('<h2>Add to phone wallet</h2>', '<h2>ফোনের ওয়ালেটে রাখুন</h2>'),
    ('<span>Add to Apple Wallet</span>', '<span>Apple Wallet-এ যোগ করুন</span>'),
    ('<span>Add to Google Wallet</span>', '<span>Google Wallet-এ যোগ করুন</span>'),
    ('<span>Save contact (.vcf)</span>', '<span>কন্টাক্ট ফাইল (.vcf)</span>'),
    ('Keeps your card on your phone, ready to show. Anyone who scans its QR code gets your contact.',
     'কার্ডটি ফোনে থাকবে, যখন খুশি দেখাতে পারবেন। কেউ এর QR কোড স্ক্যান করলেই আপনার কন্টাক্ট পেয়ে যাবে।'),
    ('title: "Add to Apple Wallet for free"', 'title: "বিনামূল্যে Apple Wallet-এ যোগ করুন"'),
    ('<h3 id="fwTitle">Add to Apple Wallet for free</h3>', '<h3 id="fwTitle">বিনামূল্যে Apple Wallet-এ যোগ করুন</h3>'),
    ('title: "Add to Google Wallet for free"', 'title: "বিনামূল্যে Google Wallet-এ যোগ করুন"'),
    ('"On an iPhone with iOS 27 or later, Wallet reads this image and builds the pass for you: your details and the contact QR code. Free, no app needed."',
     '"iOS 27 বা নতুন সংস্করণের iPhone-এ Wallet এই ছবি পড়ে নিজেই পাস বানিয়ে দেয়: আপনার তথ্য ও কন্টাক্টের QR কোডসহ। বিনামূল্যে, কোনো অ্যাপ লাগে না।"'),
    ('<p id="fwIntro">On an iPhone with iOS 27 or later, Wallet can turn a QR code into a pass. No app, account or fee needed.</p>',
     '<p id="fwIntro">iOS 27 বা নতুন সংস্করণের iPhone-এ Wallet একটি QR কোড থেকে পাস বানাতে পারে। কোনো অ্যাপ, অ্যাকাউন্ট বা টাকা লাগে না।</p>'),
    ('"Save this image to Photos."', '"ছবিটি Photos-এ সেভ করুন।"'),
    ('"Open Wallet, tap <b>+</b>, then <b>Create a Pass</b>."', '"Wallet খুলে <b>+</b> চাপুন, তারপর <b>Create a Pass</b>।"'),
    ('"Tap the photo icon and choose the image you saved."', '"ছবির আইকনে চেপে সেভ করা ছবিটি বেছে নিন।"'),
    ('"Wallet fills in the pass from the image. Check it, then tap <b>Add</b>."', '"Wallet ছবি থেকে পাস পূরণ করে দেবে। দেখে নিয়ে <b>Add</b> চাপুন।"'),
    ('"When someone scans the pass, your contact card opens on their phone, ready to save. On older iPhones, a free app such as Pass2U Wallet can make a pass from the same QR code."',
     '"কেউ পাসটি স্ক্যান করলে তার ফোনে আপনার কন্টাক্ট খুলে যাবে, সেভ করার জন্য প্রস্তুত। পুরোনো iPhone-এ Pass2U Wallet-এর মতো ফ্রি অ্যাপ দিয়ে একই QR কোড থেকে পাস বানানো যায়।"'),
    ('here: "Touch and hold the image, then tap Save to Photos."', 'here: "ছবিতে কিছুক্ষণ চেপে ধরে Save to Photos চাপুন।"'),
    ('<figcaption id="fwCap">Touch and hold the code, then tap Save to Photos.</figcaption>', '<figcaption id="fwCap">কোডে কিছুক্ষণ চেপে ধরে Save to Photos চাপুন।</figcaption>'),
    ('elsewhere: "Download the image and send it to your iPhone."', 'elsewhere: "ছবিটি ডাউনলোড করে আপনার iPhone-এ পাঠান।"'),
    ('"Google Wallet reads this image, recognises it as a business card and fills in the pass for you, with the contact QR code. Free, no setup needed."',
     '"Google Wallet এই ছবিকে ভিজিটিং কার্ড হিসেবে চিনে নিজেই পাস পূরণ করে দেয়, কন্টাক্টের QR কোডসহ। বিনামূল্যে, কোনো সেটআপ লাগে না।"'),
    ('"Save this image to your phone."', '"ছবিটি ফোনে সেভ করুন।"'),
    ('"Open Google Wallet and tap <b>Add to Wallet</b>, then <b>Everything else</b>."', '"Google Wallet খুলে <b>Add to Wallet</b> চাপুন, তারপর <b>Everything else</b>।"'),
    ('"Choose the photo option and pick the image you saved."', '"ছবির অপশন বেছে নিয়ে সেভ করা ছবিটি দিন।"'),
    ('"Wallet fills in your details from the image. Check them, then tap <b>Add</b>."', '"Wallet ছবি থেকে আপনার তথ্য পূরণ করে দেবে। দেখে নিয়ে <b>Add</b> চাপুন।"'),
    ('''"When someone scans the pass, your contact card opens on their phone, ready to save. Everything else isn't offered in every country; if you don't see it, use Save contact (.vcf) instead."''',
     '"কেউ পাসটি স্ক্যান করলে তার ফোনে আপনার কন্টাক্ট খুলে যাবে। Everything else অপশনটি সব দেশে নেই; না দেখলে কন্টাক্ট ফাইল (.vcf) ব্যবহার করুন।"'),
    ('here: "Touch and hold the image, then tap Download image."', 'here: "ছবিতে কিছুক্ষণ চেপে ধরে Download image চাপুন।"'),
    ('elsewhere: "Download the image and send it to your Android phone."', 'elsewhere: "ছবিটি ডাউনলোড করে আপনার Android ফোনে পাঠান।"'),
    ('alt="Your business card, contact details and contact QR code in one image"', 'alt="আপনার ভিজিটিং কার্ড, যোগাযোগের তথ্য ও QR কোড একটি ছবিতে"'),
    ('id="fwSave" type="button">Download image</button>', 'id="fwSave" type="button">ছবি ডাউনলোড</button>'),
    ('id="fwVcf" type="button" data-vcf hidden>Save contact (.vcf)</button>', 'id="fwVcf" type="button" data-vcf hidden>কন্টাক্ট ফাইল (.vcf)</button>'),
    ('label.textContent = "Creating pass…";', 'label.textContent = "পাস তৈরি হচ্ছে…";'),
    ('"Opening Apple Wallet…" : "Pass downloaded. Open it on an iPhone to add it to Wallet."', '"Apple Wallet খোলা হচ্ছে…" : "পাস ডাউনলোড হয়েছে। Wallet-এ যোগ করতে iPhone-এ খুলুন।"'),
    ('toast("Opening Google Wallet…");', 'toast("Google Wallet খোলা হচ্ছে…");'),
    ('"Couldn\'t reach the server. Check your connection and try again."', '"সার্ভারে পৌঁছানো যায়নি। ইন্টারনেট সংযোগ দেখে আবার চেষ্টা করুন।"'),
    ('toast("Add your name or company first.");', 'toast("আগে আপনার নাম বা প্রতিষ্ঠানের নাম লিখুন।");'),
    ('toast("Add your name and phone or email first.");', 'toast("আগে আপনার নাম এবং মোবাইল বা ইমেইল লিখুন।");'),
    ('toast("Contact file saved. Open it to add the contact.");', 'toast("কন্টাক্ট ফাইল সেভ হয়েছে। খুললেই কন্টাক্ট যোগ হবে।");'),
    # ---------- saved design ----------
    ('<h2>Saved design</h2>', '<h2>সংরক্ষিত ডিজাইন</h2>'),
    ('Your design is saved in this browser as you edit and kept for 30 days after your last change.',
     'কাজ করার সঙ্গে সঙ্গে ডিজাইন এই ব্রাউজারে সেভ হয় এবং শেষ পরিবর্তনের পর ৩০ দিন থাকে।'),
    ('"This browser isn\'t allowing saves, so your design will be lost when you close the page."', '"এই ব্রাউজার সেভ করতে দিচ্ছে না, তাই পেজ বন্ধ করলে ডিজাইন হারিয়ে যাবে।"'),
    ('el.textContent = `Saved in this browser until ${exp.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}. Each change extends it by 30 days. Nothing is sent to a server unless you add the card to a wallet.`;',
     'el.textContent = `${exp.toLocaleDateString("bn-BD", { day: "numeric", month: "long", year: "numeric" })} পর্যন্ত এই ব্রাউজারে সেভ থাকবে। প্রতিটি পরিবর্তনে আরও ৩০ দিন বাড়ে। ওয়ালেটে যোগ না করলে কিছুই সার্ভারে যায় না।`;'),
    ('id="forgetBtn" type="button">Delete saved design</button>', 'id="forgetBtn" type="button">সেভ করা ডিজাইন মুছুন</button>'),
    ('<span>Delete it and start over?</span>', '<span>মুছে নতুন করে শুরু করবেন?</span>'),
    ('id="forgetYes" type="button">Delete</button>', 'id="forgetYes" type="button">মুছুন</button>'),
    ('id="forgetNo" type="button">Cancel</button>', 'id="forgetNo" type="button">বাতিল</button>'),
    ('toast("Saved design deleted.");', 'toast("সেভ করা ডিজাইন মুছে ফেলা হয়েছে।");'),
    # ---------- inputs, logo, export ----------
    ('$("f-mono").placeholder = w.length ? (Array.from(w[0])[0] + (w.length > 1 ? Array.from(w[w.length - 1])[0] : "")).toUpperCase() + " (from your name)" : "Your initials";',
     '$("f-mono").placeholder = w.length ? (Array.from(w[0])[0] + (w.length > 1 ? Array.from(w[w.length - 1])[0] : "")).toUpperCase() + " (নাম থেকে)" : "নামের আদ্যক্ষর";'),
    ('$("f-name").placeholder = "Your name"; $("f-email").placeholder = "you@company.com"; $("f-website").placeholder = "company.com";',
     '$("f-name").placeholder = "আপনার নাম"; $("f-email").placeholder = "apni@company.com"; $("f-website").placeholder = "company.com";'),
    ('i.alt = "Logo preview"; th.appendChild(i); } else th.textContent = "None";', 'i.alt = "লোগোর প্রিভিউ"; th.appendChild(i); } else th.textContent = "নেই";'),
    ('"That image couldn\'t be read. Try a PNG or JPG."', '"ছবিটি পড়া যায়নি। PNG বা JPG চেষ্টা করুন।"'),
    ('cvFront.setAttribute("aria-label", "Front of business card" + (label ? ": " + label : ""));', 'cvFront.setAttribute("aria-label", "ভিজিটিং কার্ডের সামনের দিক" + (label ? ": " + label : ""));'),
    ('toast("Downloading " + filename);', 'toast("ডাউনলোড হচ্ছে: " + filename);'),
    ('toast(r && r.status === "delivered" ? "Sent." : "Saved " + filename);', 'toast(r && r.status === "delivered" ? "পাঠানো হয়েছে।" : "সেভ হয়েছে: " + filename);'),
    ('toast("Download cancelled.");', 'toast("ডাউনলোড বাতিল হয়েছে।");'),
    ('toast("A save prompt is already open. Finish that one first.");', 'toast("একটি সেভ উইন্ডো আগে থেকেই খোলা। আগে সেটি শেষ করুন।");'),
    ('"Front of card" : canvases.length > 1 ? "Back of card" : "Card image"', '"কার্ডের সামনের দিক" : canvases.length > 1 ? "কার্ডের পেছনের দিক" : "কার্ডের ছবি"'),
    ('toast("Couldn\'t render the image. Try again.");', 'toast("ছবি তৈরি করা যায়নি। আবার চেষ্টা করুন।");'),
    ('btn.textContent = "Preparing PDF…";', 'btn.textContent = "PDF তৈরি হচ্ছে…";'),
    ('`${state.name || "Business card"} – business card`', '`${state.name || "ভিজিটিং কার্ড"} – ভিজিটিং কার্ড`'),
    ('<h3 id="viewerTitle">Save your card</h3>', '<h3 id="viewerTitle">আপনার কার্ড সেভ করুন</h3>'),
    ('''<p id="viewerMsg">Downloads aren't available in this view. Right-click or long-press an image to save it.</p>''',
     '<p id="viewerMsg">এই ভিউতে ডাউনলোড হয় না। ছবিতে রাইট-ক্লিক করে বা কিছুক্ষণ চেপে ধরে সেভ করুন।</p>'),
    ('''"Downloads aren't available in this view. Right-click or long-press the image to save it."''', '"এই ভিউতে ডাউনলোড হয় না। ছবিতে রাইট-ক্লিক করে বা কিছুক্ষণ চেপে ধরে সেভ করুন।"'),
    ('id="viewerClose" type="button">Close</button>', 'id="viewerClose" type="button">বন্ধ করুন</button>'),
    ('id="fwClose" type="button">Close</button>', 'id="fwClose" type="button">বন্ধ করুন</button>'),
    # ---------- design browser ----------
    ('<h3 id="dbTitle">Choose a design</h3>', '<h3 id="dbTitle">ডিজাইন বেছে নিন</h3>'),
    ('id="dbClose" type="button">Close</button>', 'id="dbClose" type="button">বন্ধ করুন</button>'),
    ('placeholder="Search, e.g. waves, gold, minimal" aria-label="Search designs"', 'placeholder="খুঁজুন, যেমন: ঢেউ, সোনালি, মিনিমাল" aria-label="ডিজাইন খুঁজুন"'),
    ('aria-label="Design categories"', 'aria-label="ডিজাইনের ধরন"'),
    ('aria-label="Design pages"', 'aria-label="ডিজাইনের পাতা"'),
    ('$("browseBtn").textContent = `Browse all ${ALL_DESIGNS.length} designs`;', '$("browseBtn").textContent = `সব ${num(ALL_DESIGNS.length)}টি ডিজাইন দেখুন`;'),
    ('const ALL_DESIGNS = TEMPLATES.map(t => ({ id: t.id, name: t.name, family: "Classic", cats: ["Classic"], classic: true }))',
     'const ALL_DESIGNS = TEMPLATES.map(t => ({ id: t.id, name: t.name, nameEn: t.nameEn, family: "ক্লাসিক", familyEn: "Classic", cats: ["Classic"], classic: true }))'),
    ('$("dbCount").textContent = list.length ? `${list.length} design${list.length === 1 ? "" : "s"}, shown with your details` : "No designs match. Try another word or category.";',
     '$("dbCount").textContent = list.length ? `${num(list.length)}টি ডিজাইন, আপনার তথ্য দিয়ে দেখানো হচ্ছে` : "কোনো ডিজাইন মেলেনি। অন্য শব্দ বা ধরন চেষ্টা করুন।";'),
    ('fam.textContent = x.classic ? "Classic layout" : x.family + " · " + x.cats.join(", ");',
     'fam.textContent = x.classic ? "ক্লাসিক লেআউট" : x.family + " · " + x.cats.map(c => (L10N.cats || {})[c] || c).join(", ");'),
    ('btn("‹ Prev", db.page - 1, { disabled: db.page <= 1, aria: "Previous page" });', 'btn("‹ আগের", db.page - 1, { disabled: db.page <= 1, aria: "আগের পাতা" });'),
    ('btn("Next ›", db.page + 1, { disabled: db.page >= pages, aria: "Next page" });', 'btn("পরের ›", db.page + 1, { disabled: db.page >= pages, aria: "পরের পাতা" });'),
    ('btn(num(p), p, { current: p === db.page, aria: `Page ${p}` });', 'btn(num(p), p, { current: p === db.page, aria: `পাতা ${num(p)}` });'),
    ('info.textContent = `Showing ${from}–${Math.min(list.length, from + DB_PER - 1)} of ${list.length}`;',
     'info.textContent = `${num(list.length)}টির মধ্যে ${num(from)}–${num(Math.min(list.length, from + DB_PER - 1))} দেখানো হচ্ছে`;'),
    ('toast(`“${name}” applied. You can still change colors and fonts.`);', 'toast(`“${name}” বসানো হয়েছে। রং ও ফন্ট এখনো বদলাতে পারবেন।`);'),
    # ---------- interface font ----------
    ('--f-ui: "Geist", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;', '--f-ui: "Noto Sans Bengali", system-ui, -apple-system, "Segoe UI", sans-serif;'),
]

T += [
    ('${isD ? pair.d : pair.b}, "Hind Siliguri", ${isD ? pair.dfb : "sans-serif"}', '${isD ? pair.d : pair.b}, "Noto Sans Bengali", ${isD ? pair.dfb : "sans-serif"}'),
    ('specs.push(`${wt} 20px "Hind Siliguri"`)', 'specs.push(`${wt} 20px "Noto Sans Bengali"`)'),
    ('`${w} ${px}px "Geist", "Hind Siliguri", Arial, sans-serif`', '`${w} ${px}px "Noto Sans Bengali", Arial, sans-serif`'),
]

# Install prompt (added by pwa_patch after the main translation)
T_PWA = [
    ('<span class="ib-txt">Install<span class="ib-more"> app</span></span>', '<span class="ib-txt"><span class="ib-more">অ্যাপ </span>ইনস্টল</span>'),
    ('<strong id="ihTitle">Install Business Card Maker</strong>', '<strong id="ihTitle">ভিজিটিং কার্ড মেকার ইনস্টল করুন</strong>'),
    ('<p>On iPhone or iPad, tap the Share button in Safari, then choose <b>Add to Home Screen</b>.</p>',
     '<p>iPhone বা iPad-এ Safari-র শেয়ার বাটনে চাপুন, তারপর <b>Add to Home Screen</b> বেছে নিন।</p>'),
    ('id="ihClose" type="button">Got it</button>', 'id="ihClose" type="button">ঠিক আছে</button>'),
]

ABOUT_BN = open(__file__.replace('bn.py', 'about-bn.html'), encoding='utf-8').read()


def _apply(s, pairs, where):
    for en, bn in pairs:
        n = s.count(en)
        if n == 0:
            raise SystemExit(f'[bn] not found in {where}: {en[:100]!r}')
        s = s.replace(en, bn)
    return s


def translate(src):
    """Translate the assembled page (HTML + script) to Bengali."""
    s = src
    s = FONT_LINK_EN.sub(FONT_LINK_BN, s, count=1)
    a = s.index('  const PAIRS = {'); b = s.index('};', a) + 2
    s = s[:a] + PAIRS_BN + s[b:]
    a = s.index('<section class="about"'); b = s.index('</section>', a) + len('</section>')
    s = s[:a] + ABOUT_BN.strip() + s[b:]
    s = _apply(s, T, 'page')
    # translation data for names, labels and digits
    s = s.replace('<script>\n(() => {', '<script>window.CARD_L10N = ' + json.dumps(L10N, ensure_ascii=False) + ';</script>\n<script>\n(() => {', 1)
    return s


def translate_pwa(body):
    return _apply(body, T_PWA, 'install prompt')
