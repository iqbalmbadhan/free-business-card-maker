#!/usr/bin/env node
// End-to-end checks in a real browser for the public editions (English and Bengali), on a computer and a phone size.
// Run after `npm run build`:  npm test
// First time only: npx playwright install chromium
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { start } = require('../tools/serve');
const fonts = require('../tools/font-route');

const EDITIONS = [
  { id: 'en', folder: 'business-card-maker', lang: 'en', next: 'Next', page2: /13–24/ },
  { id: 'bn', folder: 'bangla-business-card-maker', lang: 'bn', next: 'পরের', page2: /১৩–২৪/ },
];
const SIZES = [
  { name: 'desktop', viewport: { width: 1440, height: 900 } },
  { name: 'iphone', viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' },
];

let failed = 0, passed = 0;
function check(label, ok, detail = '') {
  if (ok) { passed++; console.log(`  ✓ ${label}`); }
  else { failed++; console.log(`  ✗ ${label}${detail ? '  (' + detail + ')' : ''}`); }
}

(async () => {
  for (const e of EDITIONS) {
    if (!fs.existsSync(path.join(__dirname, '..', 'dist', e.folder, 'index.html'))) {
      console.error(`dist/${e.folder}/index.html is missing. Run npm run build first.`); process.exit(1);
    }
  }
  const server = await start(0);
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});

  for (const e of EDITIONS) for (const s of SIZES) {
    console.log(`\n${e.id} · ${s.name}`);
    const { name, ...opts } = s;
    const ctx = await browser.newContext({ ...opts, acceptDownloads: true });
    await fonts(ctx);   // real fonts, served locally
    const p = await ctx.newPage();
    const errors = []; p.on('pageerror', err => errors.push(err.message));
    // anything the Content Security Policy blocks is a bug: record it
    await p.addInitScript(() => { window.__csp = []; document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.violatedDirective + ' ' + (e.blockedURI || 'inline'))); });
    await p.goto(`${base}/${e.folder}/`, { waitUntil: 'load' });
    await p.waitForTimeout(600);

    check('page language', await p.getAttribute('html', 'lang') === e.lang);
    check('cards are drawn', await p.evaluate(() => document.getElementById('cvFront').width > 300 && document.getElementById('cvBack').width > 300));

    const phone = s.name === 'iphone';
    // on a phone each section is its own screen, picked from the bottom tab bar
    const tab = async (t) => { if (phone) { await p.click(`#tabbar button[data-tab="${t}"]`); await p.waitForTimeout(350); } };
    const overlap = (a, b) => p.evaluate(([a, b]) => { const r = document.querySelector(a).getBoundingClientRect(), q = document.querySelector(b).getBoundingClientRect(); return r.bottom > q.top + 1 && q.bottom > r.top + 1; }, [a, b]);

    if (!phone) {
      // section bar jumps to Print and highlights it
      await p.click('#secnav button[data-to="g-print"]'); await p.waitForTimeout(900);
      const gap = await p.evaluate(() => document.getElementById('g-print').getBoundingClientRect().top - document.getElementById('secnav').getBoundingClientRect().bottom);
      check('section bar scrolls to a section', gap >= -2 && gap < 40, `gap ${Math.round(gap)}px`);
      check('section bar highlights it', await p.evaluate(() => document.querySelector('#secnav [aria-current="true"]')?.dataset.to) === 'g-print');
      check('no tab bar on a computer', !(await p.isVisible('#tabbar')));
    } else {
      check('app tab bar shown, section bar hidden', await p.isVisible('#tabbar') && !(await p.isVisible('#secnav')));
      check('first screen shows only Details', await p.isVisible('#g-details') && !(await p.isVisible('#g-print')));
      await tab('export');
      check('Download tab shows its screen', await p.isVisible('#g-export') && await p.isVisible('#g-print') && !(await p.isVisible('#g-details')));
      check('Download tab is highlighted', await p.getAttribute('#tabbar button[data-tab="export"]', 'aria-current') === 'page');
      check('new screen starts under the card', await p.evaluate(() => { const g = document.getElementById('g-export').getBoundingClientRect().top, st = document.querySelector('.stage').getBoundingClientRect().bottom; return g >= st - 1 && g < st + 60; }));
      // nothing pinned covers anything else, at the top and deep in the page
      for (const y of [0, 600, 99999]) {
        await p.evaluate(y => scrollTo(0, y), y); await p.waitForTimeout(300);
        check(`no overlap: top bar / card / tab bar (scroll ${y === 99999 ? 'end' : y})`, !(await overlap('.top', '.stage')) && !(await overlap('.stage', '#tabbar')) && !(await overlap('.top', '#tabbar')));
      }
      await p.evaluate(() => scrollTo(0, 0));
    }

    // design browser: opens, pages, applies a design
    await tab('design');
    await p.click('#browseBtn'); await p.waitForSelector('#dbGrid .db-item');
    check('design browser shows 12 designs', await p.locator('#dbGrid .db-item').count() === 12);
    await p.click(`#dbPager button:has-text("${e.next}")`); await p.waitForTimeout(400);
    check('next page of designs', e.page2.test(await p.textContent('.pager-info')));
    check('new page starts at the top', await p.evaluate(() => document.getElementById('designBrowser').scrollTop) === 0);
    const before = await p.textContent('#curName');
    await p.click('#dbGrid .db-item >> nth=3'); await p.waitForTimeout(300);
    check('picking a design applies it', await p.evaluate(() => document.getElementById('designBrowser').hidden) && (await p.textContent('#curName')) !== before);

    // "Letters on the design": shown only when the design draws letters, and the letters can be changed
    await p.click('.tpl[data-v="ledger"]'); await p.waitForTimeout(300);
    check('letters field hidden when a design shows none', !(await p.isVisible('#f-mono')));
    for (const t of ['monogram', 'split', 'corner']) {
      await p.click(`.tpl[data-v="${t}"]`); await p.waitForTimeout(300);
      check(`letters field shown for ${t}`, await p.isVisible('#f-mono'));
    }
    await p.click('#browseBtn'); await p.fill('#dbSearch', 'block'); await p.waitForTimeout(500);
    await p.click('#dbGrid .db-item >> nth=0'); await p.waitForTimeout(300);
    check('letters field shown for a design with "WA"-style letters', await p.isVisible('#f-mono'));
    const frontBefore = await p.evaluate(() => document.getElementById('cvFront').toDataURL());
    await p.fill('#f-mono', 'ZQ'); await p.waitForTimeout(300);
    check('custom letters change the card', frontBefore !== await p.evaluate(() => document.getElementById('cvFront').toDataURL()));
    await p.fill('#f-mono', ''); await p.click('.tpl[data-v="ledger"]'); await p.waitForTimeout(300);

    // social links reach the back of the card
    await tab('back');
    await p.click('#backSeg button[data-v="pro"]'); await p.waitForTimeout(200);
    const backBefore = await p.evaluate(() => document.getElementById('cvBack').toDataURL());
    await tab('info');
    await p.fill('#s-linkedin', 'https://www.linkedin.com/in/test-user/'); await p.waitForTimeout(300);
    check('social link changes the back', backBefore !== await p.evaluate(() => document.getElementById('cvBack').toDataURL()));

    // "Light" back stays light with a dark color set
    await tab('style'); await p.click('#swatches button[data-v="midnight"]'); await tab('back'); await p.click('#backSeg button[data-v="light"]'); await p.waitForTimeout(300);
    const lum = await p.evaluate(() => {
      const c = document.getElementById('cvBack'), d = c.getContext('2d').getImageData(Math.round(c.width * 0.1), Math.round(c.height * 0.15), 4, 4).data;
      return (0.2126 * d[0] + 0.7152 * d[1] + 0.0722 * d[2]) / 255;
    });
    check('Light back is light on a dark palette', lum > 0.6, `luminance ${lum.toFixed(2)}`);

    // Bengali edition: nothing left in English
    if (e.lang === 'bn' && s.name === 'desktop') {
      const txt = await p.evaluate(() => document.body.innerText);
      const allowed = /^(PDF|PNG|SVG|JPG|QR|vCard|AiInfos|Apple|Google|Wallet|iPhone|iPad|Android|Safari|Photos|Create|a|Pass|Add|to|Home|Screen|Everything|else|LinkedIn|X|Facebook|Instagram|YouTube|TikTok|GitHub|Dawn|C|Simmons|ISO|Pass2U|Save|Download|image|fit|page|iOS|com|org|vcf|Share|WhatsApp|English|LI|FB|IG|YT|TT|GH|WEB|test|user|in|linkedin|Wallet-|PDF-)$/;
      const left = [...new Set(txt.match(/[A-Za-z][A-Za-z0-9'-]*/g) || [])].filter(w => !allowed.test(w) && !/@|\./.test(w));
      check('no untranslated English', left.length === 0, left.slice(0, 10).join(', '));
    }

    // About & FAQ: in the page for search engines, shown in a sheet on demand
    check('article not shown on the page itself', !(await p.isVisible('#about')));
    check('one-line footer with credits', await p.isVisible('.site-foot') && (await p.textContent('.site-foot')).includes('Dawn C Simmons'));
    await p.click('#helpBtn'); await p.waitForTimeout(500);
    check('About & FAQ opens', await p.isVisible('#helpSheet') && await p.isVisible('.faq'));
    check('sheet fits the screen', await p.evaluate(() => { const r = document.querySelector('#helpSheet .sheet-box').getBoundingClientRect(); return r.top >= -1 && r.bottom <= innerHeight + 1; }));
    await p.goBack(); await p.waitForTimeout(400);
    check('back button closes the sheet and stays on the page', !(await p.isVisible('#helpSheet')) && await p.isVisible('.stage') && p.url().endsWith(`/${e.folder}/`));
    await p.click('#helpBtn'); await p.waitForTimeout(400);
    await p.keyboard.press('Escape'); await p.waitForTimeout(300);
    check('Escape closes it', !(await p.isVisible('#helpSheet')));
    check('footer is the credit line only', !(await p.$('.site-foot button')));
    check('FAQ structured data kept', await p.evaluate(() => [...document.querySelectorAll('script[type="application/ld+json"]')].some(s => s.textContent.includes('FAQPage'))));

    // print-ready PDF
    const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 20000 }).catch(() => null), phone ? (async () => { await tab('export'); await p.click('[data-proxy="exPdf"]'); })() : p.click('#exPdf')]);
    if (dl) {
      const buf = fs.readFileSync(await dl.path());
      check('PDF downloads and is valid', buf.slice(0, 5).toString() === '%PDF-' && buf.length > 50000, `${buf.length} bytes`);
    } else check('PDF downloads and is valid', false, 'no download');

    // free wallet route on iPhone
    if (s.name === 'iphone') {
      await p.click('#walletGroup .apple'); await p.waitForTimeout(1200);
      check('Add to Apple Wallet opens the free steps', await p.isVisible('#freeWallet'));
    }

    check('no script errors', errors.length === 0, errors.join(' | '));
    const csp = await p.evaluate(() => window.__csp || []);
    check('Content Security Policy active and nothing blocked', (await p.$('meta[http-equiv="Content-Security-Policy"]')) !== null && csp.length === 0, csp.join(' | '));
    await ctx.close();
  }

  await browser.close(); server.close();
  console.log(`\n${passed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(err => { console.error(err); process.exit(1); });
