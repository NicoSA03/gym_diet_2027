// Service worker de «Junio 2027» · versión 479008f1 (lo genera menu/pwa.py)
const V = "junio2027-479008f1";
const BASE = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(BASE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k.startsWith("junio2027-") && k !== V).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const r = e.request;
  if (r.method !== "GET") return;
  if (r.mode === "navigate") {
    // la página: primero la red (así ves la versión nueva), y si no hay en 3 s, la copia guardada
    const red = fetch(r).then(res => {
      if (res.ok) { const c = res.clone(); caches.open(V).then(ca => ca.put("./index.html", c)); }
      return res;
    });
    const espera = new Promise((_, no) => setTimeout(no, 3000));
    e.respondWith(Promise.race([red, espera]).catch(() => caches.match("./index.html")));
    return;
  }
  // iconos, tipografías y demás: primero la copia guardada
  e.respondWith(caches.match(r).then(hit => hit || fetch(r).then(res => {
    if (res.ok || res.type === "opaque") { const c = res.clone(); caches.open(V).then(ca => ca.put(r, c)); }
    return res;
  })));
});
