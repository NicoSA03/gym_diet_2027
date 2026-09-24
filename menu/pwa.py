# -*- coding: utf-8 -*-
"""Convierte docs/ en una app instalable (PWA) para Android, sin librerías externas.

Genera, junto a docs/index.html (que escribe standalone.py):
  manifest.webmanifest   nombre, colores e iconos de la app
  icon-192.png, icon-512.png   iconos de la app. Si ya existen NO se tocan: puedes
                         poner ahí tu propio logo y se respeta. Solo si falta alguno
                         se dibuja uno en Python puro (la mancuerna).
                         Para volver a los dibujados: python3 menu/pwa.py --iconos
  sw.js                  service worker: guarda la app en el móvil para que abra sin internet
                         y se actualice sola cuando subes una versión nueva a GitHub

Una PWA solo se instala desde una web con https (GitHub Pages) o desde localhost.
Abierta como archivo suelto (doble clic) sigue funcionando, pero no se instala."""
import json, math, os, re, struct, sys, zlib

DOCS = "docs"
NOMBRE, CORTO = "GD plan", "GD plan"
FONDO, TINTA = (0xE0, 0x32, 0x3C), (0xFF, 0xFF, 0xFF)

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


def medida(ruta):
    """Lee el tamaño real de un PNG de su cabecera. Así el manifiesto dice la verdad
       aunque metas una imagen de 1024 en el archivo que se llama icon-192."""
    with open(ruta, "rb") as f:
        d = f.read(24)
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit(f"{ruta} no es un PNG. Los iconos de la app tienen que ser PNG.")
    return struct.unpack(">II", d[16:24])


MANIFIESTO = {
    "name": NOMBRE, "short_name": CORTO, "lang": "es",
    "description": "Plan de entrenamiento, dieta y registro de Abraham: un ciclo de 39 semanas, repetible.",
    "start_url": "./", "scope": "./", "display": "standalone", "orientation": "portrait",
    "background_color": "#000000", "theme_color": "#%02X%02X%02X" % FONDO,
}


def iconos_del_manifiesto(propios):
    """«maskable» significa: Android puede recortarte los bordes para encajar el icono
       en su forma (círculo, cuadrado redondeado...). La mancuerna que dibuja este
       archivo está pensada para eso, con el fondo a sangre. Un logo tuyo, no: si lo
       declaramos maskable, Android le come las esquinas. Por eso solo se marcan como
       maskable los iconos dibujados aquí."""
    out = []
    for s in (192, 512):
        ruta = os.path.join(DOCS, f"icon-{s}.png")
        w, h = medida(ruta)
        fines = ("any", "maskable") if s not in propios else ("any",)
        for p in fines:
            out.append({"src": f"icon-{s}.png", "sizes": f"{w}x{h}",
                        "type": "image/png", "purpose": p})
    return out

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

    # Los iconos: los tuyos mandan. Solo se dibuja el que falte, o todos con --iconos.
    forzar = "--iconos" in sys.argv
    propios = set()
    for s in (192, 512):
        ruta = os.path.join(DOCS, f"icon-{s}.png")
        if forzar or not os.path.exists(ruta):
            open(ruta, "wb").write(icono(s))
        else:
            propios.add(s)

    manifiesto = dict(MANIFIESTO, icons=iconos_del_manifiesto(propios))
    json.dump(manifiesto, open(os.path.join(DOCS, "manifest.webmanifest"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(DOCS, "sw.js"), "w", encoding="utf-8").write(SW % {"v": v})
    open(os.path.join(DOCS, ".nojekyll"), "w").write("")      # GitHub Pages sirve los archivos tal cual
    faltan = [f for f in ("index.html", "manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png")
              if not os.path.exists(os.path.join(DOCS, f))]
    assert not faltan, f"faltan archivos de la app: {faltan}"
    detalle = ", ".join(f"{s}: " + ("tuyo " if s in propios else "dibujado ") +
                        "%d×%d" % medida(os.path.join(DOCS, f"icon-{s}.png")) for s in (192, 512))
    print(f"PWA lista en docs/ · versión {v} · iconos {detalle} · sin conexión")


if __name__ == "__main__":
    main()
