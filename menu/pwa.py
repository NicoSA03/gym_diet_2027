# -*- coding: utf-8 -*-
"""Convierte docs/ en una app instalable (PWA) para Android, sin librerías externas.

Genera, junto a docs/index.html (que escribe standalone.py):
  manifest.webmanifest   nombre, colores e iconos de la app
  icon-192.png, icon-512.png   iconos dibujados aquí mismo, en Python puro
  sw.js                  service worker: guarda la app en el móvil para que abra sin internet
                         y se actualice sola cuando subes una versión nueva a GitHub

Una PWA solo se instala desde una web con https (GitHub Pages) o desde localhost.
Abierta como archivo suelto (doble clic) sigue funcionando, pero no se instala."""
import json, math, os, re, struct, zlib

DOCS = "docs"
NOMBRE, CORTO = "Junio 2027", "Junio 2027"
FONDO, TINTA = (0x0D, 0x5C, 0x4D), (0xF2, 0xF4, 0xF1)

# Mancuerna del favicon, en una rejilla de 32×32: segmentos con extremos redondeados
TRAZOS = [((8, 11.5), (8, 20.5)), ((24, 11.5), (24, 20.5)), ((11, 16), (21, 16))]
GROSOR = 2.4


def _dist(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def icono(n):
    """PNG n×n: fondo a sangre (Android le aplica su propia máscara) y mancuerna suavizada."""
    esc = n / 32
    filas = []
    for y in range(n):
        fila = bytearray([0])                       # filtro PNG «none»
        for x in range(n):
            px, py = (x + .5) / esc, (y + .5) / esc
            d = min(_dist(px, py, a, b) for a, b in TRAZOS)
            cob = max(0.0, min(1.0, (GROSOR / 2 - d) * esc + .5))   # antialias de un píxel
            fila += bytes(round(f + (t - f) * cob) for f, t in zip(FONDO, TINTA))
        filas.append(bytes(fila))
    def trozo(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
            + trozo(b"IDAT", zlib.compress(b"".join(filas), 9)) + trozo(b"IEND", b""))


MANIFIESTO = {
    "name": NOMBRE, "short_name": CORTO, "lang": "es",
    "description": "Plan de entrenamiento, dieta y registro de Abraham, septiembre 2026 a junio 2027.",
    "start_url": "./", "scope": "./", "display": "standalone", "orientation": "portrait",
    "background_color": "#0D1211", "theme_color": "#%02X%02X%02X" % FONDO,
    "icons": [{"src": f"icon-{s}.png", "sizes": f"{s}x{s}", "type": "image/png", "purpose": p}
              for s in (192, 512) for p in ("any", "maskable")],
}

SW = """// Service worker de «Junio 2027» · versión %(v)s (lo genera menu/pwa.py)
const V = "junio2027-%(v)s";
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
"""


def main():
    ruta = os.path.join(DOCS, "index.html")
    html = open(ruta, encoding="utf-8").read()
    m = re.search(r"versión ([0-9a-f]{8})", html)
    assert m, "docs/index.html no tiene la huella de versión: ejecuta antes standalone.py"
    assert 'rel="manifest"' in html and "serviceWorker" in html, \
        "docs/index.html no enlaza el manifiesto o no registra el service worker"
    v = m.group(1)
    for s in (192, 512):
        open(os.path.join(DOCS, f"icon-{s}.png"), "wb").write(icono(s))
    json.dump(MANIFIESTO, open(os.path.join(DOCS, "manifest.webmanifest"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(DOCS, "sw.js"), "w", encoding="utf-8").write(SW % {"v": v})
    open(os.path.join(DOCS, ".nojekyll"), "w").write("")      # GitHub Pages sirve los archivos tal cual
    faltan = [f for f in ("index.html", "manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png")
              if not os.path.exists(os.path.join(DOCS, f))]
    assert not faltan, f"faltan archivos de la app: {faltan}"
    print(f"PWA lista en docs/ · versión {v} · iconos 192 y 512 · sin conexión")


if __name__ == "__main__":
    main()
