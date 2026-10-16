# -*- coding: utf-8 -*-
"""Importa a datos/platos.csv los platos que has creado en la app (v2.3).

Uso, desde la carpeta del proyecto:
    python3 actualizar.py --importar platos_app.csv        lo normal: importa y regenera todo
    python3 menu/importar_platos.py platos_app.csv         solo importa, sin regenerar
    python3 menu/importar_platos.py platos_app.csv --probar  dice qué pasaría, sin escribir nada

El archivo lo descarga la app en Menús, Mis platos, «Exportar para el CSV», y tiene
las mismas columnas que datos/platos.csv. Cada plato pasa las mismas reglas que
menu/ver_platos.py:

  - la toma existe y el plato no está ya en esa toma. Si ya está, se salta sin
    avisar de error: así puedes importar el mismo archivo dos veces sin duplicar nada.
  - todos los ingredientes están en datos/alimentos.csv, sin repetir y con gramos.
  - sus calorías caen a ±12 % (o ±25 kcal) de la media de su toma.
  - cada ración está dentro de lo razonable.

Los que pasan se añaden al FINAL de datos/platos.csv, así que los siete primeros de
la comida y la cena (la semana por defecto y la lista de la compra) no cambian.
Después se ejecuta la verificación completa de los platos y, si fallara,
datos/platos.csv vuelve a quedar exactamente como estaba.
"""
import csv, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import A, macros
from platos import PLATOS, CSV, COLUMNAS
from generar import racion
from modelo import TOMAS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def media(t):
    ks = [macros(it)[0] for _, it in PLATOS[t]]
    m = sum(ks) / len(ks)
    return m, max(0.12 * m, 25)


def revisar(fila, i, ya):
    """Devuelve (estado, texto, toma, nombre, items). estado: ok, salta o rechazo."""
    toma = (fila.get("toma") or "").strip()
    nom = (fila.get("plato") or "").strip()
    if not toma or not nom:
        return "rechazo", f"línea {i}: faltan la toma o el nombre", toma, nom, None
    if toma not in TOMAS:
        return "rechazo", f"{nom}: la toma «{toma}» no existe (valen {', '.join(TOMAS)})", toma, nom, None
    if (toma, nom.lower()) in ya:
        return "salta", f"{toma}/{nom}: ya está en datos/platos.csv", toma, nom, None
    if any(c in nom for c in "|;"):
        return "rechazo", f"{nom}: el nombre no puede llevar «|» ni «;»", toma, nom, None
    nombres = [x.strip() for x in (fila.get("alimentos") or "").split("|") if x.strip()]
    crudos = [x.strip().replace(",", ".") for x in (fila.get("gramos") or "").split("|") if x.strip()]
    if not nombres or len(nombres) != len(crudos):
        return "rechazo", f"{nom}: {len(nombres)} ingredientes y {len(crudos)} cantidades", toma, nom, None
    faltan = [n for n in nombres if n not in A]
    if faltan:
        return "rechazo", f"{nom}: no están en datos/alimentos.csv: {', '.join(faltan)}", toma, nom, None
    if len(set(nombres)) != len(nombres):
        return "rechazo", f"{nom}: tiene un ingrediente repetido", toma, nom, None
    items = []
    for n, g in zip(nombres, crudos):
        try:
            g = int(round(float(g)))
        except ValueError:
            return "rechazo", f"{nom}: «{g}» no es un número de gramos", toma, nom, None
        if g <= 0:
            return "rechazo", f"{nom}: {n} tiene {g} g", toma, nom, None
        items.append((n, g))
    k = macros(items)[0]
    m, tope = media(toma)
    if abs(k - m) > tope:
        return ("rechazo", f"{nom}: {k:.0f} kcal y los platos de {TOMAS[toma][0].lower()} rondan "
                f"{m:.0f} (de {m-tope:.0f} a {m+tope:.0f}). Ajústalo en la app con las cantidades lógicas",
                toma, nom, None)
    raras = []
    for n, g in items:
        lo, hi = racion(n)
        if g > hi * 1.25 or g < lo * 0.5:
            raras.append(f"{n} {g} g (lo normal, {lo:.0f}-{hi:.0f} g)")
    if raras:
        return "rechazo", f"{nom}: raciones raras: {'; '.join(raras)}", toma, nom, None
    return "ok", f"{toma}/{nom}: {k:.0f} kcal", toma, nom, items


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    probar = "--probar" in sys.argv
    if len(args) != 1:
        sys.exit("Uso: python3 menu/importar_platos.py platos_app.csv [--probar]")
    ruta = args[0]
    if not os.path.exists(ruta):
        sys.exit(f"No encuentro {ruta}.")
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    if not filas:
        sys.exit(f"{ruta} no tiene ningún plato.")
    faltan = [c for c in COLUMNAS if c not in filas[0]]
    if faltan:
        sys.exit(f"A {ruta} le faltan columnas: {faltan}. ¿Es el archivo que exporta la app?")

    ya = {(t, n.lower()) for t, ops in PLATOS.items() for n, _ in ops}
    nuevos, saltados, rechazos = [], [], []
    for i, fila in enumerate(filas, 2):
        estado, texto, toma, nom, items = revisar(fila, i, ya)
        if estado == "ok":
            nuevos.append((toma, nom, items, (fila.get("notas") or "").strip()))
            ya.add((toma, nom.lower()))
            print("  AÑADIDO    " + texto)
        elif estado == "salta":
            saltados.append(texto); print("  YA ESTABA  " + texto)
        else:
            rechazos.append(texto); print("  RECHAZADO  " + texto)

    print(f"\n  {len(nuevos)} nuevos, {len(saltados)} que ya estaban, {len(rechazos)} rechazados")
    if not nuevos or probar:
        if probar and nuevos:
            print("  (con --probar no se escribe nada)")
        return 0

    original = open(CSV, "rb").read()
    fin = "\r\n" if b"\r\n" in original else "\n"
    with open(CSV, "a", encoding="utf-8", newline="") as f:
        if original and not original.endswith(b"\n"):
            f.write(fin)
        w = csv.writer(f, delimiter=";", lineterminator=fin)
        for toma, nom, items, notas in nuevos:
            w.writerow([toma, nom, "|".join(n for n, _ in items), "|".join(str(g) for _, g in items), notas])

    r = subprocess.run([sys.executable, os.path.join("menu", "ver_platos.py")],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        open(CSV, "wb").write(original)
        for l in r.stdout.splitlines():
            if "FALLO" in l or l.startswith("       "):
                print("  " + l.strip())
        print(f"\n  FALLO: con los platos nuevos no pasa la verificación. {CSV} queda como estaba.")
        return 1
    print(f"  {CSV}: {len(nuevos)} platos añadidos al final")
    return 0


if __name__ == "__main__":
    sys.exit(main())
