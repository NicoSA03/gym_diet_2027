# -*- coding: utf-8 -*-
"""Conectividad v3.0: gemelo en Python de la parte de cálculo de menu/conectividad.js
   (resolver métricas y viabilidad del plan de X días). Lo usa ver_conectividad.py
   para comprobar que el navegador y Python dan lo mismo. No toca el plan en curso."""
import math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from entreno import vdot

AVISO_IMPOSIBLE = "Imposible hacer rutina con esas métricas en este tiempo, reajuste"
RITMO = dict(perder=0.007, ganar=0.25, vdot=0.3, rearranque=4, minimo=4)

# (clave, obligatoria, puede venir del reloj, mínimo, máximo, opciones)
METRICAS = [
 ("edad", True, True, 14, 90, None), ("sexo", True, True, None, None, ("h", "m")),
 ("altura", True, True, 120, 230, None), ("peso", True, True, 35, 250, None),
 ("objetivo", True, False, None, None, ("5k", "perder", "ganar", "mantener")),
 ("dias_plan", True, False, 7, 730, None), ("dias_semana", True, False, 2, 7, None),
 ("test_5k", False, True, None, None, None), ("objetivo_5k", False, False, None, None, None),
 ("peso_objetivo", False, False, 35, 250, None), ("semanas_parado", False, True, 0, 520, None),
 ("vo2max", False, True, 15, 90, None), ("fc_reposo", False, True, 30, 110, None),
 ("fc_max", False, True, 120, 230, None), ("km_semana", False, True, 0, 300, None),
 ("actividad", False, True, None, None, ("sedentario", "ligero", "activo", "muy_activo")),
]
NECESITA = {"5k": ["test_5k", "objetivo_5k"], "perder": ["peso_objetivo"],
            "ganar": ["peso_objetivo"], "mantener": []}


def seg(t):
    """mm:ss o h:mm:ss a segundos (como seg() de conectividad.js)."""
    n = 0
    for p in str(t).strip().split(":"):
        n = n * 60 + float(p)
    return n


def numero(x):
    """Como num() de conectividad.js: acepta «79,5» y «1.500»; si no es un número, NaN."""
    if isinstance(x, (int, float)):
        return x
    x = re.sub(r"\s", "", str(x))
    if re.match(r"^\d{1,3}(\.\d{3})+(,\d+)?$", x):
        x = x.replace(".", "")
    m = re.match(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?", x.replace(",", ".", 1))
    return float(m.group(0)) if m else float("nan")


MMSS = re.compile(r"^\d{1,3}:[0-5]\d$")


def r1(x):
    # igual que Math.round(x*10)/10 de JavaScript (redondea .5 hacia arriba)
    return math.floor(x * 10 + 0.5) / 10


def mmss(s):
    s = int(math.floor(s + 0.5))
    return "%d:%02d" % (s // 60, s % 60)      # siempre mm:ss, aunque pase de la hora


def tiempo_para(vd, dist):
    lo, hi = 60.0, 36000.0
    for _ in range(80):
        m = (lo + hi) / 2
        if vdot(dist, m) > vd:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def fmt(x):
    return str(r1(x)).rstrip("0").rstrip(".").replace(".", ",") if r1(x) != int(r1(x)) else str(int(r1(x)))


def resolver(reloj=None, manual=None):
    reloj, manual = reloj or {}, manual or {}
    val, origen = {}, {}
    for k, obl, de_reloj, mn, mx, op in METRICAS:
        if manual.get(k) not in (None, ""):
            val[k], origen[k] = manual[k], "manual"
        elif de_reloj and reloj.get(k) is not None:
            val[k], origen[k] = reloj[k], "reloj"
        if val.get(k) is not None and mn is not None:
            val[k] = numero(val[k])
        if val.get(k) is not None and k in ("test_5k", "objetivo_5k"):
            val[k] = str(val[k]).strip()
    if val.get("fc_max") is None and val.get("edad") is not None and 14 <= val["edad"] <= 90:
        val["fc_max"], origen["fc_max"] = int(math.floor(208 - 0.7 * val["edad"] + 0.5)), "calculado"
    if val.get("vo2max") is None and val.get("test_5k") and MMSS.match(val["test_5k"]):
        val["vo2max"], origen["vo2max"] = r1(vdot(5000, seg(val["test_5k"]))), "calculado"
    if val.get("semanas_parado") is None:
        val["semanas_parado"], origen["semanas_parado"] = 0, "supuesto"
    pide = {m[0] for m in METRICAS if m[1]} | set(NECESITA.get(val.get("objetivo"), []))
    faltan = [m[0] for m in METRICAS if m[0] in pide and val.get(m[0]) is None]
    malas = []
    for k, obl, de_reloj, mn, mx, op in METRICAS:
        v = val.get(k)
        if v is None or origen.get(k) == "calculado":   # solo se valida lo que viene de fuera
            continue
        if mn is not None:
            mala = not (mn <= v <= mx)          # NaN tampoco pasa
        elif op:
            mala = v not in op
        elif k in ("test_5k", "objetivo_5k"):
            mala = not (MMSS.match(v) and 600 <= seg(v) <= 5400)
        else:
            mala = False
        if mala:
            malas.append(k)
    bien = lambda k: val.get(k) is not None and k not in malas
    o = val.get("objetivo")
    if o == "perder" and bien("peso") and bien("peso_objetivo") and val["peso_objetivo"] >= val["peso"]:
        malas.append("peso_objetivo")
    if o == "ganar" and bien("peso") and bien("peso_objetivo") and val["peso_objetivo"] <= val["peso"]:
        malas.append("peso_objetivo")
    if o == "5k" and bien("test_5k") and bien("objetivo_5k") and seg(val["objetivo_5k"]) >= seg(val["test_5k"]):
        malas.append("objetivo_5k")
    return dict(valores=val, origen=origen, faltan=faltan, malas=malas)


def viabilidad(v):
    sem = v["dias_plan"] / 7
    motivos, alc, necesarias = [], {}, 0
    rearr = RITMO["rearranque"] if float(v.get("semanas_parado") or 0) >= 4 else 0
    util = max(0, sem - rearr)
    if v["objetivo"] == "5k":
        a, b = vdot(5000, seg(v["test_5k"])), vdot(5000, seg(v["objetivo_5k"]))
        necesarias = max(0, (b - a) / RITMO["vdot"])
        motivos.append("Bajar el 5 km de %s a %s son %s puntos de VDOT: unas %d semanas."
                       % (v["test_5k"], v["objetivo_5k"], fmt(b - a), math.ceil(necesarias)))
        alc["objetivo_5k"] = mmss(tiempo_para(a + RITMO["vdot"] * util, 5000))
    elif v["objetivo"] == "perder":
        kg = v["peso"] - v["peso_objetivo"]
        necesarias = max(0, kg / (v["peso"] * RITMO["perder"]))
        motivos.append("Perder %s kg sin perder músculo lleva unas %d semanas." % (fmt(kg), math.ceil(necesarias)))
        alc["peso_objetivo"] = r1(v["peso"] - v["peso"] * RITMO["perder"] * util)
    elif v["objetivo"] == "ganar":
        kg = v["peso_objetivo"] - v["peso"]
        necesarias = max(0, kg / RITMO["ganar"])
        motivos.append("Ganar %s kg de músculo lleva unas %d semanas." % (fmt(kg), math.ceil(necesarias)))
        alc["peso_objetivo"] = r1(v["peso"] + RITMO["ganar"] * util)
    if rearr:
        motivos.append("Llevas %s semanas parado: se suman %d de rearranque." % (v["semanas_parado"], rearr))
    total = max(RITMO["minimo"], math.ceil(necesarias + rearr))
    if math.ceil(necesarias + rearr) < RITMO["minimo"]:
        motivos.append("El plan más corto que tiene sentido son %d semanas." % RITMO["minimo"])
    ok = v["dias_plan"] >= total * 7
    return dict(ok=ok, aviso=None if ok else AVISO_IMPOSIBLE, min_dias=total * 7,
                motivos=motivos, alcanzable=None if ok else alc)


def evaluar(reloj=None, manual=None):
    r = resolver(reloj, manual)
    if r["faltan"] or r["malas"]:
        r["estado"] = "faltan"
        return r
    r["estado"] = "listo"
    r["viabilidad"] = viabilidad(r["valores"])
    return r
