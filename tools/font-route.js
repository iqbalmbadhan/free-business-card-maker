// Serves the app's Google Fonts from local @fontsource copies (this machine has no access to Google Fonts).
const fs = require('fs');
const FS = require('path').join(__dirname, '..', 'node_modules', '@fontsource') + '/';
const FAM = { 'Hind Siliguri': 'hind-siliguri', 'Anek Bangla': 'anek-bangla', 'Noto Sans Bengali': 'noto-sans-bengali', 'Noto Serif Bengali': 'noto-serif-bengali',
  'Baloo Da 2': 'baloo-da-2', 'Tiro Bangla': 'tiro-bangla', 'Galada': 'galada', 'Geist': 'geist-sans', 'Geist Mono': 'geist-mono', 'Syne': 'syne', 'DM Sans': 'dm-sans',
  'Manrope': 'manrope', 'Work Sans': 'work-sans', 'Cormorant Garamond': 'cormorant-garamond',
  'Montserrat': 'montserrat', 'Open Sans': 'open-sans', 'Poppins': 'poppins', 'Inter': 'inter', 'Roboto': 'roboto', 'Raleway': 'raleway',
  'Lato': 'lato', 'Nunito': 'nunito', 'Oswald': 'oswald', 'Playfair Display': 'playfair-display', 'Lora': 'lora', 'Source Sans 3': 'source-sans-3',
  'Merriweather': 'merriweather' };
const RANGE = { bengali: 'U+0951-0952,U+0964-0965,U+0980-09FE,U+1CD0-1CF9,U+200C-200D,U+20B9,U+25CC,U+A8F1', latin: 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD' };
let css = '';
for (const [fam, dir] of Object.entries(FAM)) for (const w of [400, 500, 600, 700, 800]) for (const sub of ['bengali', 'latin']) {
  const f = `${dir}/files/${dir}-${sub}-${w}-normal.woff2`;
  if (fs.existsSync(FS + f)) css += `@font-face{font-family:"${fam}";font-weight:${w};font-style:normal;font-display:swap;unicode-range:${RANGE[sub]};src:url(https://fonts.gstatic.com/local/${f}) format("woff2");}\n`;
}
module.exports = async (ctx) => {
  await ctx.route(/fonts\.googleapis\.com/, r => r.fulfill({ contentType: 'text/css', body: css }));
  await ctx.route(/fonts\.gstatic\.com\/local\//, r => r.fulfill({ contentType: 'font/woff2', body: fs.readFileSync(FS + r.request().url().split('/local/')[1]) }));
};
module.exports.css = css;
