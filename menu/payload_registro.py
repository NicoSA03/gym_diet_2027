# -*- coding: utf-8 -*-
"""Datos de la pestaña «Registro»: plantillas de sesión por bloque, descansos, músculos,
   volumen y kilómetros que marca el plan. El móvil solo pinta y guarda: los números salen de aquí."""
import sys, json, datetime as dt; sys.path.insert(0, 'menu')
from entreno import FASES, EJ, DIAS, TABATA, calendario, PESO

# Segundos de descanso entre series según el escalón del ejercicio
DESCANSO = {"T1": 180, "T2": 120, "T3": 90, "TF": 60}

# Ejercicios de peso corporal: lo que se apunta en «kg» es el lastre, y el 1RM
# estimado se calcula con tu peso corporal + lastre
CORPORAL = {"Flexión clásica", "Dominadas lastradas"}

# Rango útil de series semanales por grupo (el mismo que usa ver_entreno.py)
GRANDES = ["Cuádriceps", "Isquios", "Glúteo", "Pectoral", "Espalda", "Hombro"]
TECHO, PISO_PEQ = 22, 4

# Ritmo de peso buscado en cada bloque, kg/semana (None = mantener)
RITMO = {"F0": None, "F1": 0.2, "F2": None, "F3": 0.2, "F4": -0.3, "F5": None}

for n in CORPORAL:
    assert n in EJ, f"{n} está en CORPORAL pero no en EJ (entreno.py)"
assert set(RITMO) == set(FASES), "RITMO tiene que tener una entrada por bloque"

cal = {c["cod"]: c for c in calendario()}


def volumen_plan(esq):
    """Series semanales por grupo muscular que marca el plan en un bloque."""
    vol = {}
    for d in DIAS:
        for t, ej in d["ej"]:
            for m in EJ[ej]["m"]:
                vol[m] = vol.get(m, 0) + esq[t][0]
    return vol


musculos = GRANDES + sorted({m for e in EJ.values() for m in e["m"]} - set(GRANDES))

km_plan = []            # [lunes de la semana, km, ¿descarga?]
for k, f in FASES.items():
    for i, km in enumerate(f["km"]):
        lunes = cal[k]["ini"] + dt.timedelta(weeks=i)
        km_plan.append([lunes.isoformat(), km, (i + 1) in f["des"]])

PAY = {
    "peso": PESO,
    "fases": {k: dict(n=f["n"], ini=cal[k]["ini"].isoformat(), fin=cal[k]["fin"].isoformat(),
                      esquema={t: list(p) for t, p in f["esquema"].items()},
                      piso=6 if k in ("F0", "F5") else 10, plan=volumen_plan(f["esquema"]),
                      ritmo=RITMO[k], mar=f["mar"], jue=f["jue"])
              for k, f in FASES.items()},
    "dias": [dict(cod=d["cod"], dia=d["dia"], n=d["n"], sub=d["sub"], tipo=d["tipo"],
                  ej=[list(x) for x in d["ej"]], tabata=d["tabata"]) for d in DIAS],
    "ej": {k: dict(m=v["m"], cue=v["cue"], corporal=k in CORPORAL) for k, v in EJ.items()},
    "tabatas": {k: v["n"] for k, v in TABATA.items()},
    "descanso": DESCANSO,
    "musculos": musculos, "grandes": GRANDES, "techo": TECHO, "piso_peq": PISO_PEQ,
    "km_plan": km_plan,
}
json.dump(PAY, open('menu/pay_registro.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print("registro:", len(open('menu/pay_registro.json', encoding='utf8').read()) // 1024, "KB")
