// Business Card Maker – AiInfos: service worker for offline use.
// Bump VERSION whenever you upload a new index.html so installed copies pick it up.
const VERSION = "bcm-iqbal-private-v8";
const APP_CACHE = VERSION + "-app";
const FONT_CACHE = "bcm-iqbal-private-fonts";

const APP_FILES = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./icons/apple-touch-icon.png",
  "./icons/favicon-32.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(APP_CACHE).then((cache) => cache.addAll(APP_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("bcm-iqbal-private-") && k !== APP_CACHE && k !== FONT_CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Google Fonts: serve from cache, refresh in the background
  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") {
    event.respondWith(
      caches.open(FONT_CACHE).then(async (cache) => {
        const cached = await cache.match(req);
        const network = fetch(req).then((res) => { if (res && (res.ok || res.type === "opaque")) cache.put(req, res.clone()); return res; }).catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  if (url.origin !== self.location.origin) return;

  // Wallet pass requests always go straight to the server and are never cached
  if (url.pathname.includes("/api/")) return;

  // The page itself: try the network first so updates show up, fall back to the cached copy offline
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) { const copy = res.clone(); caches.open(APP_CACHE).then((c) => c.put("./index.html", copy)); }
          return res;
        })
        .catch(() => caches.match("./index.html"))
    );
    return;
  }

  // Icons and manifest: cache first
  event.respondWith(caches.match(req).then((cached) => cached || fetch(req)));
});
