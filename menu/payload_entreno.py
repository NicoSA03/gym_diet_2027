# -*- coding: utf-8 -*-
import sys, json; sys.path.insert(0,'menu')
from entreno import (FASES, EJ, DIAS, VARIANTES, REGLAS, SEGUIMIENTO, TABATA,
                     TABATA_REGLA, ESTRUCTURA, GENERICO, GRUPO, TEST_5K, OBJETIVO_5K, seg,
                     calendario, fecha, arranque, zonas, vdot, PESO)

cal = {c["cod"]: c for c in calendario()}

PAY = {
 "peso": PESO,
 "fases": {k: dict(n=v["n"], lema=v["lema"], foco=v["foco"], sem=v["sem"],
                   ini=fecha(cal[k]["ini"]), fin=fecha(cal[k]["fin"]),
                   s0=cal[k]["s0"], s1=cal[k]["s1"], dieta=v["dieta"],
                   esquema={t: list(p) for t, p in v["esquema"].items()},
                   pct=v["pct"], mar=v["mar"], jue=v["jue"],
                   km=v["km"], des=v["des"], largo=list(v["largo"]))
           for k, v in FASES.items()},
 "dias": [dict(cod=d["cod"], dia=d["dia"], n=d["n"], sub=d["sub"], tipo=d["tipo"],
               dur=d["dur"], cal=d["cal"], ej=[list(x) for x in d["ej"]],
               tabata=d["tabata"], nota=d["nota"]) for d in DIAS],
 "ej": {k: dict(m=v["m"], p=v["p"], cue=v["cue"], nota=v["nota"], sus=v["sus"])
        for k, v in EJ.items()},
 "tabata": {k: dict(n=v["n"], dur=v["dur"], a=list(v["a"]), b=list(v["b"]),
                    como=v["como"], sube=v["sube"]) for k, v in TABATA.items()},
 "tabata_regla": TABATA_REGLA,
 "estructura": {k: {g: list(x) for g, x in v.items()} for k, v in ESTRUCTURA.items()},
 "generico": {g: list(x) for g, x in GENERICO.items()},
 "grupo": GRUPO,
 "variantes": [dict(cod=v["cod"], n=v["n"], dias=v["dias"], dur=v["dur"],
                    cuando=v["cuando"], regla=v["regla"],
                    detalle=[list(x) for x in v["detalle"]], conserva=v["conserva"])
               for v in VARIANTES],
 "zonas": [list(z) for z in zonas(seg(TEST_5K))],
 "seguimiento": [list(s) for s in SEGUIMIENTO],
 "reglas": [list(r) for r in REGLAS],
 "arranque": arranque(),
 "vdot": {"hoy": round(vdot(5000, seg(TEST_5K)), 1), "fin": round(vdot(5000, seg(OBJETIVO_5K)), 1)},
}
json.dump(PAY, open('menu/pay_entreno.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print("entreno:", len(open('menu/pay_entreno.json', encoding='utf8').read())//1024, "KB")
