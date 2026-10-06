#!/usr/bin/env node
// Makes the social preview images (1200 x 630) from real cards drawn by the app, with its real fonts.
//   node tools/og-image.js en   ->  public/og-image.png
//   node tools/og-image.js bn   ->  public/og-image-bn.png
// Run npm run build first. Afterwards bump OG_VERSION in build/build.py so social sites refetch the image.
const { chromium } = require('playwright');
const fonts = require('./font-route');
const path = require('path');
const css = fonts.css;
const BN = process.argv[2] === 'bn';
const DESIGN = BN ? 'ঢেউ' : 'coastal';   // the design shown on the cards
const DIST = path.join(__dirname, '..', 'dist');
const PAGE = 'file://' + path.join(DIST, BN ? 'bangla-business-card-maker' : 'business-card-maker', 'index.html');
const TXT = BN ? { brand: 'AiInfos', h1: 'ফ্রি ভিজিটিং কার্ড মেকার', p: 'বাংলা ফন্টে দুই পাশের কার্ড বানান, QR কোডসহ। প্রেসে দেওয়ার মতো PDF ডাউনলোড করুন।',
  chips: ['১৪৮টি ডিজাইন', '৬টি বাংলা ফন্ট', 'QR কন্টাক্ট', 'সোশ্যাল লিংক', 'অ্যাকাউন্ট লাগে না'], foot: 'ফ্রি · ওয়াটারমার্ক নেই · যেকোনো ফোনে চলে', font: '"Noto Sans Bengali"', h1size: 52 }
 : { brand: 'AiInfos', h1: 'Free Business Card Maker', p: 'Design a two-sided card with a QR code in minutes. Download a print-ready PDF.',
  chips: ['148 designs', 'QR contact', 'Social links', 'Apple &amp; Google Wallet', 'No sign-up'], foot: 'Free · No watermark · Works on any phone', font: 'Geist', h1size: 58 };
const OUTFILE = path.join(__dirname, '..', 'public', BN ? 'og-image-bn.png' : 'og-image.png');
(async () => {
  const b = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  const ctx = await b.newContext({ deviceScaleFactor: 1 });
  await fonts(ctx);
  const p = await ctx.newPage({ viewport: { width: 1440, height: 900 } });
  await p.goto(PAGE, { waitUntil: 'load' });
  await p.addStyleTag({ content: '[hidden]{display:none!important}' });
  await p.waitForTimeout(1200);
  await p.uncheck('#p-guides');
  await p.click('#browseBtn'); await p.fill('#dbSearch', DESIGN); await p.waitForTimeout(500);
  await p.click('#dbGrid .db-item >> nth=0'); await p.waitForTimeout(300);
  await p.click('#backSeg button[data-v="pro"]'); await p.waitForTimeout(800);
  const front = await p.evaluate(() => document.getElementById('cvFront').toDataURL('image/png'));
  const back = await p.evaluate(() => document.getElementById('cvBack').toDataURL('image/png'));
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>${css}
  *{box-sizing:border-box} body{margin:0;width:1200px;height:630px;overflow:hidden;font-family:${TXT.font},sans-serif;
  background:#2B5648;background-image:radial-gradient(120% 80% at 75% 10%,rgba(255,255,255,.13),transparent 60%),radial-gradient(80% 70% at 20% 110%,#1D3E33,transparent 70%),
  repeating-linear-gradient(0deg,rgba(255,255,255,.1) 0 1px,transparent 1px 120px),repeating-linear-gradient(90deg,rgba(255,255,255,.1) 0 1px,transparent 1px 120px),
  repeating-linear-gradient(0deg,rgba(255,255,255,.05) 0 1px,transparent 1px 24px),repeating-linear-gradient(90deg,rgba(255,255,255,.05) 0 1px,transparent 1px 24px);color:#fff;position:relative}
  .copy{position:absolute;left:64px;top:64px;width:440px}
  .brand{display:flex;align-items:center;gap:12px;font-weight:600;font-size:20px;opacity:.95}
  .mark{width:34px;height:23px;border-radius:5px;background:linear-gradient(135deg,#3FA184 0 46%,#0F1A15 46%);transform:rotate(-6deg);box-shadow:inset 0 0 0 1px rgba(255,255,255,.2)}
  h1{font-size:${TXT.h1size}px;line-height:1.02;letter-spacing:-.035em;margin:34px 0 18px;font-weight:700}
  p{font-size:23px;line-height:1.4;margin:0;color:#D5E8DF}
  .chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:30px}
  .chips span{font-size:16px;font-weight:500;padding:8px 13px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2)}
  .card{position:absolute;width:470px;border-radius:3px;box-shadow:0 2px 3px rgba(0,0,0,.3),0 24px 50px -10px rgba(0,0,0,.55)}
  .back{right:40px;top:300px;transform:rotate(3deg)} .front{right:150px;top:58px;transform:rotate(-4deg)}
  .url{position:absolute;left:64px;bottom:48px;font-size:17px;color:#BFD8CC;font-weight:500;letter-spacing:.01em}
  </style></head><body>
  <div class="copy"><div class="brand"><span class="mark"></span>${TXT.brand}</div>
  <h1>${TXT.h1}</h1>
  <p>${TXT.p}</p>
  <div class="chips">${TXT.chips.map(c => '<span>' + c + '</span>').join('')}</div></div>
  <img class="card back" src="${back}"><img class="card front" src="${front}">
  <div class="url">${TXT.foot}</div>
  </body></html>`;
  const og = await ctx.newPage(); await og.setViewportSize({ width: 1200, height: 630 });
  await og.setContent(html, { waitUntil: 'load' }); await og.waitForTimeout(500);
  await og.screenshot({ path: OUTFILE });
  await b.close();
})();
