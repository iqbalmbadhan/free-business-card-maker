PWA_BTN = '''<div class="top-actions"><button class="btn" id="installBtn" type="button" hidden><span class="ib-ico" aria-hidden="true"></span><span class="ib-txt">Install<span class="ib-more"> app</span></span></button></div>'''
PWA_HINT = '''<div class="install-hint" id="installHint" hidden role="dialog" aria-labelledby="ihTitle">
  <strong id="ihTitle">Install Business Card Maker</strong>
  <p>On iPhone or iPad, tap the Share button in Safari, then choose <b>Add to Home Screen</b>.</p>
  <button class="linkbtn" id="ihClose" type="button">Got it</button>
</div>'''
PWA_CSS = '''<style>
.top-actions { display: flex; align-items: center; gap: 10px; }
#installBtn { padding: 7px 12px; font-size: 13px; }
.install-hint { position: fixed; z-index: 25; left: 16px; right: 16px; top: calc(env(safe-area-inset-top, 0px) + 60px); max-width: 360px; margin: 0 auto;
  background: var(--panel); color: var(--ink); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  display: flex; flex-direction: column; gap: 6px; }
.install-hint p { margin: 0; color: var(--muted); }
@media (display-mode: standalone) { #installBtn { display: none !important; } }
</style>'''
PWA_JS = '''<script>
(() => {
  const btn = document.getElementById("installBtn"), hint = document.getElementById("installHint");
  const standalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
    window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
  }
  if (standalone) return;
  let deferred = null;
  window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); deferred = e; btn.hidden = false; });
  window.addEventListener("appinstalled", () => { deferred = null; btn.hidden = true; });
  const ios = /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  if (ios) btn.hidden = false;
  btn.addEventListener("click", async () => {
    if (deferred) { deferred.prompt(); try { await deferred.userChoice; } catch (e) {} deferred = null; btn.hidden = true; }
    else { hint.hidden = false; document.getElementById("ihClose").focus(); }
  });
  document.getElementById("ihClose").addEventListener("click", () => { hint.hidden = true; });
})();
</script>'''
def pwa_patch(body):
    marker = '<div class="spec" id="spec">'
    i = body.index(marker); j = body.index('</div>', i) + len('</div>')
    body = body[:j] + PWA_BTN + body[j:]
    body = body.replace('</main>', '</main>\n' + PWA_HINT, 1)
    return PWA_CSS + '\n' + body + '\n' + PWA_JS
