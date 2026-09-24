# -*- coding: utf-8 -*-
"""Verificación de datos/alimentos.csv: que los números se sostengan entre sí
   y lista de lo que falta por copiar de las etiquetas."""
import sys; sys.path.insert(0, 'menu')
from db import A, SECCION
from calidad import calidad, CLAVES

fallos = 0
def chk(ok, txt):
    global fallos
    if not ok: fallos += 1
    print(("  OK  " if ok else "  FALLO ") + txt)

print("== 1. Las calorías cuadran con los macros (4/4/9 y 2 por la fibra, margen del 12 %) ==")
malos = []
for n, a in A.items():
    teor = a["proteina"] * 4 + a["carbohidrato"] * 4 + a["grasa"] * 9 + (a["fibra"] or 0) * 2
    if a["kcal"] > 0 and abs(teor - a["kcal"]) > max(0.12 * a["kcal"], 10):
        malos.append(f"{n} (línea {a['linea']}): {a['kcal']:.0f} kcal declaradas, {teor:.0f} por macros")
chk(not malos, f"{len(A)} alimentos revisados" + ("" if not malos else "\n       " + "\n       ".join(malos)))

print("\n== 2. Los azúcares no pueden pasar del carbohidrato, ni las saturadas de la grasa ==")
for n, a in A.items():
    if a["azucares"] is not None and a["azucares"] > a["carbohidrato"] + 0.6:
        chk(False, f"{n}: {a['azucares']:g} g de azúcar con {a['carbohidrato']:g} g de carbohidrato")
    if a["saturadas"] is not None and a["saturadas"] > a["grasa"] + 0.6:
        chk(False, f"{n}: {a['saturadas']:g} g de saturadas con {a['grasa']:g} g de grasa")
chk(True, "coherencia interna de cada etiqueta")

print("\n== 3. Valores dentro de lo posible ==")
for n, a in A.items():
    for c, tope in (("kcal", 950), ("proteina", 100), ("grasa", 100), ("carbohidrato", 100),
                    ("sal", 30), ("precio_eur", 100)):
        v = a[c]
        if v is not None and (v < 0 or v > tope):
            chk(False, f"{n}: {c} = {v:g} está fuera de rango (0 a {tope})")
    if a["nova"] is not None and a["nova"] not in (1, 2, 3, 4):
        chk(False, f"{n}: NOVA = {a['nova']:g}; solo vale 1, 2, 3 o 4")
    if a["formato_g"] is not None and a["formato_g"] <= 0:
        chk(False, f"{n}: el formato de venta tiene que ser mayor que cero")
chk(True, "rangos de kcal, macros, sal, precio, NOVA y formato")

print("\n== 4. Notas de calidad ==")
notas = {}
for n, a in A.items():
    c = calidad(a)
    notas.setdefault(c["letra"] if c else "—", []).append(n)
for l in ("A", "B", "C", "D", "—"):
    if l in notas:
        print(f"       {l}: {len(notas[l]):2d} · " + ", ".join(sorted(notas[l])[:6]) +
              (" …" if len(notas[l]) > 6 else ""))
sin = notas.get("—", [])
chk(True, f"{len(A)-len(sin)} alimentos calificados, {len(sin)} pendientes de etiqueta")
if sin:
    print("\n       Te faltan datos de la etiqueta (azúcares, sal, saturadas o NOVA) en:")
    for n in sorted(sin):
        a = A[n]
        falta = [c for c in CLAVES if a.get(c) is None]
        print(f"       · línea {a['linea']:2d}  {n}  → {', '.join(falta)}")

print("\n== 5. Alimentos que piden revisión (ultraprocesados o mucha azúcar/sal) ==")
avisos = 0
for n, a in sorted(A.items()):
    c = calidad(a)
    if not c: continue
    if c["letra"] in ("C", "D"):
        avisos += 1
        print(f"       {c['letra']} {c['puntos']:3d}  {n}: " + " · ".join(m for m in c["motivos"] if m[0] == "−"))
print(f"       ({avisos} alimentos; no es un fallo, es para que decidas si los cambias)")

print("\n" + (f"HAY FALLOS: {fallos}" if fallos else "TODO OK"))
sys.exit(1 if fallos else 0)
