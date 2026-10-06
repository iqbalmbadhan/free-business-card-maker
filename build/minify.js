// Minifies the inline <style> and <script> blocks of a built index.html in place.
const fs = require('fs');
const esbuild = require('esbuild');
const file = process.argv[2];
let html = fs.readFileSync(file, 'utf8');
const before = html.length;
html = html.replace(/<style>([\s\S]*?)<\/style>/g, (m, css) =>
  '<style>' + esbuild.transformSync(css, { loader: 'css', minify: true, target: ['chrome100', 'safari15', 'firefox100'] }).code.trim() + '</style>');
html = html.replace(/<script>([\s\S]*?)<\/script>/g, (m, js) => {
  if (!js.trim()) return m;
  const out = esbuild.transformSync(js, { loader: 'js', minify: true, legalComments: 'inline', target: ['es2020'] }).code.trim();
  if (/<\/script/i.test(out)) throw new Error('minified script contains </script');
  return '<script>' + out + '</script>';
});
// collapse whitespace between tags (outside pre/textarea/scripts, which this page doesn't use for content)
html = html.replace(/>\s*\n\s*</g, '>\n<');
fs.writeFileSync(file, html);
console.log(`${file.split('/').slice(-2).join('/')}: ${before} -> ${html.length} bytes`);
