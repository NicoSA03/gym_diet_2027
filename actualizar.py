#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenera el sistema «Junio 2027» completo con una sola orden.

Uso:
    python3 actualizar.py                 cambios normales (peso, test de 5 km, ejercicios, series...)
    python3 actualizar.py --recalcular    si has tocado datos/platos.csv, datos/alimentos.csv
                                          o las kcal de una fase
    python3 actualizar.py --paginas       genera también las páginas sueltas para claude.ai
    python3 actualizar.py --empaquetar    genera fuente_junio2027.txt para subirlo al proyecto
    python3 actualizar.py --probar        sirve docs/ en http://localhost:8000 para probar la app
    python3 actualizar.py --forzar        construye aunque la verificación falle (no recomendado)

Solo usa la biblioteca estándar de Python 3.8 o superior.
"""
import argparse, os, subprocess, sys, time

RAIZ = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)

# En Windows Python escribe por defecto en cp1252, que no tiene ▶, ✓ ni −.
# Todo en UTF-8: la pantalla de aquí y los archivos que escriben los scripts de menu/.
os.environ["PYTHONUTF8"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

FUENTE = ["db.py", "platos.py", "modelo.py", "entreno.py", "payload3.py", "payload_info.py",
          "payload_entreno.py", "construir.py", "standalone.py", "generar.py",
          "ver_entreno.py", "ver_menu.py", "ver_alimentos.py", "ver_platos.py",
          "calidad.py", "base.css",
          "a1_info.html", "a1.js", "a2_menus.html", "a2.js", "a3_compra.html", "a3.js",
          "a4_entreno.html", "a4.js", "a5_teoria.html", "a5.js",
          "payload_registro.py", "a6_registro.html", "a6.js", "pwa.py",
          "factores.json", "normas.json", "md.py"]
RAIZ_FUENTE = ["README.md", "actualizar.py", "restaurar.py", ".gitignore",
               "datos/alimentos.csv", "datos/platos.csv"]


def paso(titulo, script, *args, obligatorio=True, silencioso=False):
    print(f"\n▶ {titulo}")
    t = time.time()
    r = subprocess.run([sys.executable, os.path.join("menu", script), *args],
                       capture_output=silencioso, text=True, encoding="utf-8")
    if silencioso:
        claves = ("FALLO", "TODO OK", "HAY FALLOS")
        utiles = [l for l in r.stdout.splitlines() if any(k in l for k in claves)]
        if utiles:                      # verificación: solo el resumen y los fallos
            for l in utiles: print("  " + l.strip())
        elif r.returncode != 0:         # error de Python: se enseña entero
            print(r.stdout); print(r.stderr, file=sys.stderr)
    print(f"  ({time.time()-t:.1f} s)")
    if r.returncode != 0 and obligatorio:
        sys.exit(f"\n✗ Paró en «{titulo}». Corrige lo que marca arriba y vuelve a ejecutar.")
    return r.returncode == 0


def empaquetar():
    out = ["# FUENTE DEL SISTEMA «JUNIO 2027»",
           "# Cada archivo va entre una línea de ARCHIVO y una de FIN (tres signos = a cada lado).",
           "# Se restaura con:  python3 restaurar.py fuente_junio2027.txt",
           "# (si no tienes restaurar.py, está dentro de este mismo archivo: cópialo a mano)", ""]
    rutas = RAIZ_FUENTE + [f"menu/{f}" for f in FUENTE]
    for f in rutas:
        out += [f"=== ARCHIVO: {f} ===",
                open(f, encoding="utf-8").read().rstrip("\n"),
                "=== FIN ===\n"]
    open("fuente_junio2027.txt", "w", encoding="utf-8").write("\n".join(out))
    print("\n▶ Paquete para el proyecto de Claude: fuente_junio2027.txt")


def main():
    ap = argparse.ArgumentParser(description="Regenera el sistema Junio 2027.")
    ap.add_argument("--recalcular", action="store_true",
                    help="recalcula los factores de la dieta (tras tocar platos, alimentos o kcal)")
    ap.add_argument("--paginas", action="store_true",
                    help="genera también las cinco páginas sueltas de claude.ai")
    ap.add_argument("--empaquetar", action="store_true",
                    help="genera fuente_junio2027.txt para subirlo al proyecto")
    ap.add_argument("--forzar", action="store_true",
                    help="construye aunque la verificación falle")
    ap.add_argument("--probar", action="store_true",
                    help="al terminar, sirve docs/ en http://localhost:8000 (Ctrl+C para parar)")
    a = ap.parse_args()

    if a.recalcular:
        paso("Recalculando factores de la dieta (≈20 s)", "modelo.py", silencioso=True)

    ok0 = paso("Verificando los alimentos", "ver_alimentos.py", obligatorio=False, silencioso=True)
    okp = paso("Verificando los platos", "ver_platos.py", obligatorio=False, silencioso=True)
    paso("Datos de la dieta y la compra", "payload3.py", silencioso=True)
    paso("Datos de «Cómo funciona»", "payload_info.py", silencioso=True)
    paso("Datos del entreno", "payload_entreno.py", silencioso=True)
    paso("Datos del registro", "payload_registro.py", silencioso=True)

    ok1 = paso("Verificando el entreno", "ver_entreno.py", obligatorio=False, silencioso=True)
    ok2 = paso("Verificando la dieta", "ver_menu.py", obligatorio=False, silencioso=True)
    if not (ok0 and okp and ok1 and ok2) and not a.forzar:
        sys.exit("\n✗ La verificación ha encontrado fallos. No se ha generado nada nuevo.\n"
                 "  Mira las líneas FALLO de arriba. Si sabes lo que haces: --forzar")

    paso("Construyendo el archivo del móvil", "standalone.py")
    paso("Preparando la app instalable (PWA)", "pwa.py")
    if a.paginas:
        paso("Construyendo las páginas sueltas", "construir.py", "todos")
    if a.empaquetar:
        empaquetar()

    print("\n✓ Listo.")
    print("  salida/planificacion_dieta_gym.html  → el archivo para el móvil")
    print("  docs/                  → la app instalable, lista para GitHub Pages")
    if a.probar:
        import functools, http.server
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=os.path.join(RAIZ, "docs"))
        print("\n▶ Probando en http://localhost:8000  (Ctrl+C para parar)")
        try: http.server.ThreadingHTTPServer(("localhost", 8000), h).serve_forever()
        except KeyboardInterrupt: print("\nParado.")


if __name__ == "__main__":
    main()
