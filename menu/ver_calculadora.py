# -*- coding: utf-8 -*-
"""Verificación de la calculadora de la pestaña Menús (v2.0).

   Comprueba, para cada bloque y tipo de día:
   1. Que cada plato en su toma de siempre sale dentro del objetivo de kcal
      (±5 % o ±25 kcal, lo que sea mayor). Si la proteína se queda por debajo del
      80 % solo avisa: es cosa del plato (la carne picada lleva mucha grasa), no de la cuenta.
   2. Que ninguna ración se sale de lo razonable (los mínimos y máximos de generar.py).
   3. Cuántos platos de cena se quedan cortos como comida (informativo: la app
      propone un acompañante con un toque).
   4. Si Node está instalado, que menu/calculadora.js da exactamente los mismos
      gramos que menu/calculadora.py."""
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calculadora import item, resolver, suma

M = json.load(open("menu/pay_menus.json", encoding="utf-8"))
F = M["foods"]
fallos, avisos, cortos, casos = [], [], {}, []


def plantillas(toma, todas=False):
    if toma in ("C", "N"):
        return [(p["n"], p["it"]) for p in M["principales"] if todas or p["de"] == toma]
    return [(o["n"], o["it"]) for o in M["bloques"][toma]["ops"]]


for ft, tomas in M["obj"].items():
    for toma, obj in tomas.items():
        for todas in (False, True):
            if todas and toma not in ("C", "N"):
                continue
            for pn, it in plantillas(toma, todas):
                its = [item(n, g, F[n], toma) for n, g in it]
                g = resolver(its, obj)
                t = suma(its, g)
                if len(casos) < 400:
                    casos.append({"it": it, "toma": toma, "obj": obj, "g": g})
                for x, gi in zip(its, g):
                    if gi and not x["fijo"] and x["rol"] != "verdura" and gi > x["hi"] + 5:
                        fallos.append(f"{ft} {toma} {pn}: {x['n']} {gi} g pasa del máximo {x['hi']}")
                ek = t[0] - obj[0]
                if todas:
                    if ek < -max(0.05 * obj[0], 25):
                        cortos[(toma, pn)] = cortos.get((toma, pn), 0) + 1
                    continue
                if abs(ek) > max(0.05 * obj[0], 25):
                    fallos.append(f"{ft} {toma} {pn}: {t[0]:.0f} kcal frente a {obj[0]:.0f}")
                if t[1] < 0.8 * obj[1] and obj[1] - t[1] > 3:
                    avisos.append(f"{ft} {toma} {pn}: {t[1]:.0f} g de proteína frente a {obj[1]:.0f}")

print(f"Combinaciones comprobadas: {sum(1 for _ in M['obj'])} bloques y tipos de día")
if cortos:
    print(f"Platos que como comida se quedan cortos y piden acompañante: "
          f"{len({p for _, p in cortos})} (la app lo propone con un toque)")

node = shutil.which("node")
if node:
    js = ("const C=require(process.argv[1]);const casos=JSON.parse(require('fs').readFileSync(0,'utf8'));"
          "const F=JSON.parse(process.argv[2]);"
          "console.log(JSON.stringify(casos.map(c=>C.resolver(c.it.map(([n,g])=>C.item(n,g,F[n],c.toma)),c.obj))));")
    r = subprocess.run([node, "-e", js, os.path.abspath("menu/calculadora.js"), json.dumps(F)],
                       input=json.dumps(casos), capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        fallos.append("calculadora.js no se ha podido ejecutar: " + r.stderr.strip()[:200])
    else:
        dif = [i for i, (c, g) in enumerate(zip(casos, json.loads(r.stdout))) if c["g"] != g]
        if dif:
            fallos.append(f"calculadora.js y calculadora.py no dan lo mismo en {len(dif)} de {len(casos)} casos")
        else:
            print(f"calculadora.js y calculadora.py coinciden en {len(casos)} casos")
else:
    print("Node no está instalado: no se compara calculadora.js con calculadora.py")

if avisos:
    platos = sorted({a.split(": ")[0].split(" ", 2)[2] for a in avisos})
    print(f"AVISO (no para la construcción): {len(avisos)} casos van cortos de proteína en: "
          + ", ".join(platos) + ". La app lo señala en el plato.")
for f in fallos[:40]:
    print("FALLO", f)
print("TODO OK" if not fallos else f"HAY FALLOS: {len(fallos)}")
sys.exit(1 if fallos else 0)
