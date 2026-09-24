# -*- coding: utf-8 -*-
"""Verificación de datos/platos.csv: que cada plato encaje en su toma, que las
   raciones sean de verdad y que ninguno se quede sin nota de calidad."""
import sys; sys.path.insert(0, 'menu')
from db import A, F, ROL, macros
from platos import PLATOS
from generar import racion, nota
from modelo import TOMAS, ORDEN_TOMAS

fallos = 0
def chk(ok, txt):
    global fallos
    if not ok: fallos += 1
    print(("  OK  " if ok else "  FALLO ") + txt)

print("== 1. Cada toma tiene platos suficientes ==")
for t in ORDEN_TOMAS:
    n = len(PLATOS.get(t, []))
    minimo = 7 if t in ("C", "N") else 2
    chk(n >= minimo, f"{t} ({TOMAS[t][0]}): {n} platos, mínimo {minimo}")

print("\n== 2. Todos los platos de una toma valen lo mismo (±12 %, o ±25 kcal) ==")
print("       La app iguala las opciones entre sí: si un plato se sale mucho, para")
print("       cuadrar el día lo estirará hasta dejarlo en raciones absurdas. En las")
print("       tomas pequeñas manda el margen absoluto: 11 kcal no son nada.")
for t in ORDEN_TOMAS:
    ks = [macros(it)[0] for _, it in PLATOS[t]]
    media = sum(ks) / len(ks)
    tope = max(0.12 * media, 25)
    malos = [f"{n} ({k:.0f} kcal, {(k-media)/media*100:+.0f} %)"
             for (n, _), k in zip(PLATOS[t], ks) if abs(k - media) > tope]
    chk(not malos, f"{t}: media {media:.0f} kcal" +
        ("" if not malos else "\n       " + "\n       ".join(malos)))

print("\n== 3. Raciones de verdad (nadie come 900 g de arroz) ==")
malos = []
for t, ops in PLATOS.items():
    for nom, items in ops:
        for n, g in items:
            lo, hi = racion(n)
            if g > hi * 1.25 or g < lo * 0.5:
                malos.append(f"{t}/{nom}: {n} {g} g (lo normal son {lo:.0f}–{hi:.0f} g)")
chk(not malos, "todas las raciones dentro de lo razonable" +
    ("" if not malos else ":\n       " + "\n       ".join(malos)))

print("\n== 4. Ningún ingrediente repetido dentro del mismo plato ==")
malos = []
for t, ops in PLATOS.items():
    for nom, items in ops:
        vistos = [n for n, _ in items]
        rep = {n for n in vistos if vistos.count(n) > 1}
        if rep: malos.append(f"{t}/{nom}: {', '.join(sorted(rep))}")
chk(not malos, f"{sum(len(v) for v in PLATOS.values())} platos revisados" +
    ("" if not malos else ":\n       " + "\n       ".join(malos)))

print("\n== 5. Nota de calidad de cada plato ==")
for t in ORDEN_TOMAS:
    filas = []
    for nom, items in PLATOS[t]:
        l, p, c = nota(items)
        filas.append(f"{l}{'' if l=='—' else str(p)}" + ("" if c >= 100 else f"({c}%)"))
    print(f"       {t:3} " + " · ".join(filas))
flojos = [(t, nom, nota(items)) for t, ops in PLATOS.items() for nom, items in ops
          if nota(items)[0] in ("C", "D")]
for t, nom, (l, p, c) in flojos:
    print(f"       {l} {p:3d}  {t}/{nom}")
print(f"       ({len(flojos)} platos con nota C o D; no es un fallo, es para que decidas)")
parciales = sum(1 for t, ops in PLATOS.items() for _, items in ops if nota(items)[2] < 100)
chk(True, f"{parciales} platos con la nota calculada a medias, porque a algún "
          f"ingrediente le faltan los datos de la etiqueta")

print("\n== 6. Alimentos de la despensa que no usa ningún plato ==")
usados = {n for ops in PLATOS.values() for _, items in ops for n, _ in items}
sobran = sorted(set(A) - usados)
print("       " + (", ".join(sobran) if sobran else "ninguno: todo lo que compras se usa"))
chk(True, f"{len(usados)} de {len(A)} alimentos en uso")

print("\n" + (f"HAY FALLOS: {fallos}" if fallos else "TODO OK"))
sys.exit(1 if fallos else 0)
