# -*- coding: utf-8 -*-
"""Plazos y reajuste dinámico del plan (v2.6). Solo la cuenta, sin pantalla ni archivos.

   La misma lógica está en menu/plazos.js, que es la que usa la app. Si cambias
   una, cambia la otra: menu/ver_plazos.py comprueba que dan lo mismo.

   Nunca modifica el registro que recibe: aplicar y deshacer devuelven una copia.
   Cada propuesta aplicada deja un apunte en registro["ajustes"]; deshacer_ajuste
   lo deshace en cualquier momento, sin necesitar la propuesta original.
   Las fechas son texto AAAA-MM-DD y se cuentan en días enteros.
   Sin fecha de inicio no hay propuestas. Con `desde` (la fecha en que empezó a
   usarse esto) no se juzga nada anterior a esa fecha."""
import copy
import datetime
import math
import unicodedata

# Semana: buena con el 80 % o más, repetir cargas con el 60 % o más, alargar por debajo.
# Con 5 sesiones: 4 o 5 bien, 3 repetir, 2 o menos alargar.
DIAS_SIN_ENTRENAR = 10  # a partir de aquí, semana de reentrada
PESAJES_MIN = 10        # pesajes en 21 días (y 3 por semana) para opinar del peso
PASO_KCAL = 100

# MET por tipo e intensidad (suave, media, alta)
MET = {"caminar": [3, 4, 5], "carrera": [7, 9, 11.5], "bici": [5, 7, 10], "fuerza": [3.5, 5, 6],
       "natacion": [6, 8, 10], "deporte": [5, 7, 9], "otro": [3, 5, 7]}
# Entreno previsto de cada sesión del plan: minutos y MET
PREVISTO = {"L": (70, 5), "M": (55, 9), "X": (70, 5), "J": (60, 7), "V": (70, 5)}
PLAN = {"dias": [
    {"cod": "L", "n": "Fuerza A", "tipo": "fuerza"},
    {"cod": "M", "n": "Carrera de calidad", "tipo": "carrera"},
    {"cod": "X", "n": "Fuerza B", "tipo": "fuerza"},
    {"cod": "J", "n": "Tirada larga", "tipo": "carrera"},
    {"cod": "V", "n": "Fuerza C", "tipo": "fuerza"}]}
# Bloques de la dieta con regla de peso (README, «Cuándo tocar las calorías»).
# B0, B2 y B5 no tienen regla.
CONSTRUCCION, DEFINICION = {"B1", "B3"}, {"B4"}
MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
NOMBRES_DIA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_EPOCA = datetime.date(1970, 1, 1)


# ---------------------------------------------------------------- utilidades

def _media(xs):
    # Suma de izquierda a derecha, igual que reduce en plazos.js (sum() de
    # Python 3.12 o más suma con otra precisión y cambiaría el redondeo).
    t = 0.0
    for x in xs:
        t += x
    return t / len(xs)

def _redond(x):
    return math.floor(x + 0.5)


def _r2(x):
    return math.floor(x * 100 + 0.5) / 100


def _r3(x):
    return math.floor(x * 1000 + 0.5) / 1000


def _a_dias(s):
    a, m, d = (int(x) for x in s.split("-"))
    return (datetime.date(a, m, d) - _EPOCA).days


def _a_iso(n):
    return (_EPOCA + datetime.timedelta(days=n)).isoformat()


def _dia_semana(s):          # lunes = 0
    return (_a_dias(s) + 3) % 7


def _lunes_de(s):
    return _a_iso(_a_dias(s) - _dia_semana(s))


def _suma_dias(s, n):
    return _a_iso(_a_dias(s) + n)


def _corta(s):
    """«15 oct», como en a6.js."""
    _, m, d = (int(x) for x in s.split("-"))
    return "%d %s" % (d, MES[m - 1])


def _num(x):
    """Como JavaScript escribe un número (3 y no 3.0), con coma decimal."""
    return (str(int(x)) if x == int(x) else str(x)).replace(".", ",")


def _plan_de(plan):
    return plan["dias"] if plan and plan.get("dias") else PLAN["dias"]


def _sin_tildes(t):
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _ajustes(r):
    return (r or {}).get("ajustes") or []


def _ultima_de(xs):
    xs = [x for x in xs if x]
    return max(xs) if xs else None


# ---------------------------------------------------------------- kcal
def _met_de(act):
    tabla = MET.get(_sin_tildes((act or {}).get("tipo")), MET["otro"])
    i = {"suave": 0, "media": 1, "alta": 2}.get(_sin_tildes((act or {}).get("int")), 1)
    return tabla[i]


def _netas(met, minutos, peso):
    """kcal netas: MET menos 1, porque las del reposo ya van en el objetivo del día."""
    return (met - 1) * peso * minutos / 60


def kcal_actividad(act, peso):
    """kcal enteras de {nombre, tipo, min, int} para un peso en kg."""
    if not act or not (peso and peso > 0) or not ((act.get("min") or 0) > 0):
        return 0
    return _redond(_netas(_met_de(act), act["min"], peso))


def _kcal_prevista(cod, peso):
    p = PREVISTO.get(cod)
    return _netas(p[1], p[0], peso) if p and peso and peso > 0 else 0


def _sesion_de_hoy(fecha, plan=None):
    dias = _plan_de(plan)
    i = _dia_semana(fecha)
    return dias[i]["cod"] if i < len(dias) else None


def dieta_del_dia(registro, fecha, obj_plan, peso):
    """obj_plan = {kcal, kcalE, kcalD, sesion?}. Devuelve {factor, kcal, motivo}."""
    base = obj_plan["kcal"]

    def igual(m):
        return {"factor": 1, "kcal": base, "motivo": m}

    d = ((registro or {}).get("dias") or {}).get(fecha)
    # Un día corregido después (corregir_dia) no cambia su comida: vale lo que se marcó aquel día
    if d and d.get("corregido"):
        d = d.get("comida") or None
    if not d or not (peso and peso > 0):
        return igual("Sin cambios sobre el plan")
    prev = obj_plan["sesion"] if "sesion" in obj_plan else _sesion_de_hoy(fecha)
    k_prev = _kcal_prevista(prev, peso) if prev else 0
    modo = d.get("modo")
    if modo == "descanso":
        k_hoy, que = 0, "Descanso"
    elif modo == "otra":
        k_hoy = kcal_actividad(d["act"], peso) if d.get("act") else 0
        que = (d.get("act") or {}).get("nombre") or "Otra actividad"
    elif modo == "otro_plan" and d.get("sesion") in PREVISTO:
        k_hoy, que = _kcal_prevista(d["sesion"], peso), "Otro entreno del plan"
    else:
        return igual("Sin cambios sobre el plan")
    nuevo = base - k_prev + k_hoy
    lo, hi = min(obj_plan["kcalE"], obj_plan["kcalD"]), max(obj_plan["kcalE"], obj_plan["kcalD"])
    kcal = _redond(min(hi, max(lo, nuevo)))
    if kcal == _redond(base):
        return igual("Sin cambios sobre el plan")
    tope = " (mínimo: día de descanso)" if nuevo < lo else " (máximo: día de sábado)" if nuevo > hi else ""
    return {"factor": _r3(kcal / base), "kcal": kcal,
            "motivo": que + ": " + ("más" if kcal > base else "menos") + " comida que el plan" + tope}


# ---------------------------------------------------------------- semana
def _tipo_act(t):
    t = _sin_tildes(t)
    return t if t in ("carrera", "fuerza") else "otro"


def _via(x):
    return "reloj" if x.get("origen") == "reloj" else "app"


def _prueba_dia(r, f, plan):
    """Lo que hay registrado un día: {tipo, medio?, via, slot, natural} o None.
       tipo "otro" = actividad que no sustituye una sesión entera (vale 0,5 si medio)."""
    d = (r.get("dias") or {}).get(f)
    sesion = next((s for s in (r.get("sesiones") or []) if s.get("fecha") == f), None)
    carr = next((c for c in (r.get("carrera") or []) if c.get("f") == f), None)
    natural = _sesion_de_hoy(f, plan)
    tipo_nat = _plan_de(plan)[_dia_semana(f)]["tipo"] if natural else None
    explicito = d["sesion"] if d and d.get("modo") == "otro_plan" and d.get("sesion") else None
    e = None
    if sesion and carr:
        e = {"tipo": "carrera", "via": _via(carr)} if tipo_nat == "carrera" else {"tipo": "fuerza", "via": _via(sesion)}
    elif sesion:
        e = {"tipo": "fuerza", "via": _via(sesion)}
    elif carr:
        e = {"tipo": "carrera", "via": _via(carr)}
    elif d and d.get("modo") == "otra" and d.get("act"):
        # Otra actividad: vale 1 solo si es del tipo de la sesión prevista ese día
        t = _tipo_act(d["act"].get("tipo"))
        medio = (d["act"].get("min") or 0) >= 30 and _sin_tildes(d["act"].get("int")) in ("media", "alta")
        e = {"tipo": t, "via": "otra"} if t != "otro" and t == tipo_nat else {"tipo": "otro", "via": "otra", "medio": medio}
    elif d and d.get("hecho") and d.get("modo") in ("plan", "otro_plan"):
        # Sesión del plan hecha pero sin apuntar las series (marcada a mano, corregir_dia)
        cod = d.get("sesion") or natural
        dp = next((x for x in _plan_de(plan) if x["cod"] == cod), None)
        if dp:
            e = {"tipo": dp["tipo"], "via": "manual"}
    if not e:
        return None
    e["slot"], e["natural"] = explicito, natural
    return e


def adherencia(registro, lunes_iso, plan=None, desde=None):
    """{hechas, previstas, pct, detalle} de la semana que empieza ese lunes.
       Los huecos de días anteriores a la fecha de inicio (o a `desde`) no son
       previstos. pct es None si no hay ninguno previsto."""
    r = registro or {}
    dias = _plan_de(plan)
    n = len(dias)
    lun = _lunes_de(lunes_iso)
    arranque = _ultima_de([r.get("inicio"), desde])
    detalle = [{"sesion": d["cod"], "fecha": None, "valor": 0, "via": None,
                "prevista": not arranque or _suma_dias(lun, i) >= arranque} for i, d in enumerate(dias)]

    def libre(i):
        return detalle[i]["prevista"] and detalle[i]["valor"] == 0 and detalle[i]["fecha"] is None

    def idx(cod):
        return next((i for i, d in enumerate(dias) if d["cod"] == cod), -1)

    pruebas = []
    for k in range(7):
        f = _suma_dias(lun, k)
        if arranque and f < arranque:
            continue
        e = _prueba_dia(r, f, plan)
        if e:
            e["f"] = f
            pruebas.append(e)

    def poner(i, e, valor):
        detalle[i]["fecha"], detalle[i]["valor"], detalle[i]["via"] = e["f"], valor, e["via"]

    hecho = set()
    for p, e in enumerate(pruebas):             # primera pasada: cada día en su hueco
        i = -1
        if e["tipo"] != "otro":
            if e["slot"] and idx(e["slot"]) >= 0 and dias[idx(e["slot"])]["tipo"] == e["tipo"]:
                i = idx(e["slot"])
            elif e["natural"] and idx(e["natural"]) >= 0 and dias[idx(e["natural"])]["tipo"] == e["tipo"]:
                i = idx(e["natural"])
            if i >= 0 and libre(i):
                poner(i, e, 1)
                hecho.add(p)
        else:
            if e["slot"] and idx(e["slot"]) >= 0:
                i = idx(e["slot"])
            elif e["natural"]:
                i = idx(e["natural"])
            if i >= 0 and libre(i):
                if e["medio"]:
                    poner(i, e, 0.5)
                hecho.add(p)
    for p, e in enumerate(pruebas):             # segunda: lo que sobra, al primer hueco libre
        if p in hecho:
            continue
        for i in range(n):
            if not libre(i):
                continue
            if e["tipo"] == "otro":
                if e["medio"]:
                    poner(i, e, 0.5)
                break
            if dias[i]["tipo"] == e["tipo"]:
                poner(i, e, 1)
                break
    hechas = sum(x["valor"] for x in detalle)
    previstas = sum(1 for x in detalle if x["prevista"])
    return {"hechas": hechas, "previstas": previstas,
            "pct": _r3(min(1, hechas / previstas)) if previstas else None, "detalle": detalle}


# ---------------------------------------------------------------- ajustes
def _con_ajuste(registro, aj):
    c = copy.deepcopy(registro)
    c["ajustes"] = list(_ajustes(c)) + [aj]
    return c


def _hay_ajuste(r, que, semana):
    return any(not a.get("deshecho") and a.get("que") == que and a.get("semana") == semana for a in _ajustes(r))


def _mismo_dia(a, b):
    return bool(a) and bool(b) and a.get("modo") == b.get("modo") and (a.get("sesion") or None) == (b.get("sesion") or None)


def deshacer_ajuste(registro, indice):
    """Copia con registro["ajustes"][indice] deshecho.
       alargar: vuelve al inicio de antes si sigue el que puso el ajuste.
       recuperar: vuelve el día a como estaba si sigue como lo dejó el ajuste.
       kcal, repetir, reentrada: solo se marca (kcal_extra deja de sumarlo)."""
    c = copy.deepcopy(registro)
    c["ajustes"] = list(_ajustes(c))
    if not isinstance(indice, int) or indice < 0 or indice >= len(c["ajustes"]):
        return c
    a = c["ajustes"][indice]
    if a.get("deshecho"):
        return c
    if a.get("que") == "alargar" and a.get("antes") and a.get("despues") and c.get("inicio") == a["despues"].get("inicio"):
        c["inicio"] = a["antes"].get("inicio")
    if a.get("que") == "recuperar" and a.get("antes") and a.get("despues"):
        c["dias"] = c.get("dias") or {}
        if _mismo_dia(c["dias"].get(a["f"]), a["despues"].get("dia")):
            if a["antes"].get("dia"):
                c["dias"][a["f"]] = a["antes"]["dia"]
            else:
                c["dias"].pop(a["f"], None)
    a["deshecho"] = True
    return c


def _busca_ajuste(r, f, que, semana=None):
    """Índice del último apunte activo que cuadra, o -1."""
    aj = _ajustes(r)
    for i in range(len(aj) - 1, -1, -1):
        a = aj[i]
        if not a.get("deshecho") and a.get("f") == f and a.get("que") == que and (semana is None or a.get("semana") == semana):
            return i
    return -1


def _deshacer_ultimo(r, f, que, semana=None):
    return deshacer_ajuste(r, _busca_ajuste(r, f, que, semana))


# ---------------------------------------------------------------- propuestas
def _es_iso(f):
    try:
        return isinstance(f, str) and len(f) == 10 and _a_iso(_a_dias(f)) == f
    except (ValueError, TypeError):
        return False


def corregir_dia(registro, fecha, dia, hoy, ahora=None):
    """Marca o cambia qué se hizo un día de hoy hacia atrás. Devuelve un registro nuevo,
       o None si no se puede (día futuro, fecha o datos no válidos). dia=None quita la corrección.
       Un día pasado queda con corregido=True y su comida no cambia."""
    if not _es_iso(fecha) or not _es_iso(hoy) or fecha > hoy:
        return None
    c = copy.deepcopy(registro or {})
    if not isinstance(c.get("dias"), dict):
        c["dias"] = {}
    prev = c["dias"].get(fecha)
    pasado = fecha < hoy
    if not prev:
        comida = None
    elif prev.get("corregido"):
        comida = prev.get("comida") or None
    else:
        comida = {"modo": prev.get("modo"), "sesion": prev.get("sesion") or None,
                  "act": prev.get("act") or None, "t": prev.get("t") or 0}
    if dia is None:
        if pasado and comida:
            c["dias"][fecha] = comida
        else:
            c["dias"].pop(fecha, None)
        return c
    t = int(datetime.datetime.now().timestamp() * 1000) if ahora is None else ahora
    modo = dia.get("modo")
    if modo == "plan":
        cod = dia.get("sesion") or _sesion_de_hoy(fecha)
        if cod and cod not in PREVISTO:
            return None
        n = {"modo": "plan", "sesion": cod or None, "act": None}
    elif modo == "otro_plan":
        if dia.get("sesion") not in PREVISTO:
            return None
        n = {"modo": "otro_plan", "sesion": dia["sesion"], "act": None}
    elif modo == "otra":
        act = dia.get("act")
        if not act or not (isinstance(act.get("min"), (int, float)) and act["min"] > 0):
            return None
        n = {"modo": "otra", "sesion": None, "act": copy.deepcopy(act)}
    elif modo == "descanso":
        n = {"modo": "descanso", "sesion": None, "act": None}
    else:
        return None
    if dia.get("hecho") and n["sesion"]:
        n["hecho"] = True
    if pasado:
        n.update({"t": comida["t"] if comida else t, "corregido": True, "tc": t, "comida": comida})
    else:
        n["t"] = t
    c["dias"][fecha] = n
    return c


def revisar_ajustes(registro, fecha, plan=None, desde=None):
    """Índices de los «repetir» o «alargar» activos de la semana de `fecha` que la cuenta
       ya no justifica (tras corregir un día). No deshace nada."""
    r = registro or {}
    if not _es_iso(fecha):
        return []
    lun, out = _lunes_de(fecha), []
    for i, a in enumerate(_ajustes(r)):
        if not a or a.get("deshecho") or a.get("semana") != lun or a.get("que") not in ("repetir", "alargar"):
            continue
        base = r
        if a["que"] == "alargar" and (a.get("antes") or {}).get("inicio") and r.get("inicio") == (a.get("despues") or {}).get("inicio"):
            base = dict(r, inicio=a["antes"]["inicio"])
        ad = adherencia(base, lun, plan, desde)
        if not ad["previstas"]:
            continue
        corte = 4 if a["que"] == "repetir" else 3
        if ad["hechas"] * 5 >= ad["previstas"] * corte:
            out.append(i)
    return out


def _ultima_actividad(r, hoy):
    fs = [s.get("fecha") for s in (r.get("sesiones") or [])]
    fs += [c.get("f") for c in (r.get("carrera") or [])]
    fs += [f for f, d in (r.get("dias") or {}).items()
           if d and ((d.get("modo") == "otra" and d.get("act"))
                     or (d.get("hecho") and d.get("modo") in ("plan", "otro_plan")))]
    return _ultima_de([f for f in fs if f and f <= hoy])


def propuesta_dia(registro, hoy, plan=None, desde=None):
    """None o {tipo, texto, aplicar(r, ahora), deshacer(r)}: reentrada o sesión pendiente."""
    r = registro or {}
    dias = _plan_de(plan)
    if not r.get("inicio") or r["inicio"] > hoy:
        return None
    lun = _lunes_de(hoy)
    # 1. Reentrada: diez días o más sin entrenar (contando desde el inicio o desde `desde`)
    ref = _ultima_de([_ultima_actividad(r, hoy), r["inicio"], desde if desde and desde <= hoy else None])
    sin = _a_dias(hoy) - _a_dias(ref)
    if sin >= DIAS_SIN_ENTRENAR:
        if _hay_ajuste(r, "reentrada", lun):
            return None
        return {
            "tipo": "reentrada",
            "texto": "Llevas %d días sin entrenar. Esta semana es de reentrada: cargas más suaves y lejos del fallo." % sin,
            "aplicar": lambda reg, ahora=None: _con_ajuste(reg, {"f": hoy, "que": "reentrada", "semana": lun, "antes": {"reentrada": False}, "despues": {"reentrada": True}, "deshecho": False}),
            "deshacer": lambda reg: _deshacer_ultimo(reg, hoy, "reentrada", lun),
        }
    # 2. Sesión pendiente: la más reciente de esta semana sin hacer ni descartada
    d0 = (r.get("dias") or {}).get(hoy)
    if d0 and d0.get("modo"):
        return None
    ad = adherencia(r, lun, plan, desde)
    for k in range(min(_dia_semana(hoy), len(dias)) - 1, -1, -1):
        f = _suma_dias(lun, k)
        s = ad["detalle"][k]
        if not s["prevista"] or s["valor"] != 0 or s["fecha"] is not None:
            continue
        dd = (r.get("dias") or {}).get(f)
        if dd and dd.get("modo") in ("descanso", "otra"):
            continue
        cod, nombre = s["sesion"], dias[k]["n"]

        def aplicar(reg, ahora=None, cod=cod):
            antes = copy.deepcopy((reg.get("dias") or {}).get(hoy))
            c = _con_ajuste(reg, {"f": hoy, "que": "recuperar", "semana": lun, "antes": {"dia": antes},
                                  "despues": {"dia": {"modo": "otro_plan", "sesion": cod}}, "deshecho": False})
            c["dias"] = c.get("dias") or {}
            c["dias"][hoy] = {"modo": "otro_plan", "sesion": cod, "act": None, "t": ahora}
            return c

        return {"tipo": "recuperar",
                "texto": "El %s %s tocaba %s%s ¿La haces hoy?" % (
                    NOMBRES_DIA[k], _corta(f), nombre,
                    " e hiciste otro entreno." if any(x.get("fecha") == f for x in (r.get("sesiones") or []))
                    or any(x.get("f") == f for x in (r.get("carrera") or [])) else " y no hay registro."),
                "aplicar": aplicar,
                "deshacer": lambda reg: _deshacer_ultimo(reg, hoy, "recuperar", lun)}
    return None


def propuesta_semana(registro, hoy, plan=None, desde=None):
    """None o {tipo, texto, aplicar(r), deshacer(r)}: mira la semana anterior a la de hoy."""
    r = registro or {}
    if not r.get("inicio") or r["inicio"] > hoy:
        return None
    ant = _suma_dias(_lunes_de(hoy), -7)
    if ant < _lunes_de(r["inicio"]):
        return None
    if desde and _suma_dias(ant, 6) < desde:
        return None
    ad = adherencia(r, ant, plan, desde)
    if not ad["previstas"]:
        return None
    # en múltiplos de 0,5: sin errores de coma flotante
    if ad["hechas"] * 5 >= ad["previstas"] * 4:
        return None
    txt = "%s de %d" % (_num(ad["hechas"]), ad["previstas"])
    if ad["hechas"] * 5 >= ad["previstas"] * 3:
        if _hay_ajuste(r, "repetir", ant):
            return None
        return {
            "tipo": "repetir",
            "texto": "La semana pasada hiciste %s sesiones. Repite las cargas de esa semana antes de subirlas." % txt,
            "aplicar": lambda reg, ahora=None: _con_ajuste(reg, {"f": hoy, "que": "repetir", "semana": ant, "antes": {}, "despues": {"repetir": True}, "deshecho": False}),
            "deshacer": lambda reg: _deshacer_ultimo(reg, hoy, "repetir", ant),
        }
    if _hay_ajuste(r, "alargar", ant):
        return None

    def mueve(ini):
        """Nunca un inicio posterior a hoy (pasa si empezaste a mitad de la semana
           pasada; hoy cae en la misma semana, así que el efecto es el mismo)."""
        x = _suma_dias(ini, 7)
        return hoy if x > hoy else x

    def aplicar(reg, ahora=None):
        if _hay_ajuste(reg, "alargar", ant):
            return copy.deepcopy(reg)
        nuevo = mueve(reg["inicio"])
        c = _con_ajuste(reg, {"f": hoy, "que": "alargar", "semana": ant, "antes": {"inicio": reg["inicio"]},
                              "despues": {"inicio": nuevo}, "deshecho": False})
        c["inicio"] = nuevo
        return c

    return {"tipo": "alargar",
            "texto": "La semana pasada hiciste %s sesiones. Alarga el bloque una semana: la fecha de inicio pasa al %s y el final se retrasa." % (txt, _corta(mueve(r["inicio"]))),
            "aplicar": aplicar,
            "deshacer": lambda reg: _deshacer_ultimo(reg, hoy, "alargar", ant)}


def kcal_extra(registro, bloque):
    """kcal acumuladas por los avisos de peso aplicados en un bloque."""
    return sum(a["despues"]["kcal"] - a["antes"]["kcal"] for a in _ajustes(registro)
               if not a.get("deshecho") and a.get("que") == "kcal" and a.get("bloque") == bloque)


def propuesta_peso(registro, hoy, bloque):
    """None o {tipo, kcal, texto, aplicar(r), deshacer(r)}. La regla tiene que cumplirse
       dos semanas seguidas: media de cada semana frente a la anterior en los últimos
       21 días. Hacen falta 10 pesajes en esos 21 días y 3 por semana."""
    r = registro or {}
    h = _a_dias(hoy)

    def en(a, b):
        return [p["kg"] for p in (r.get("peso") or []) if h - b < _a_dias(p["f"]) <= h - a]

    sem = [en(0, 7), en(7, 14), en(14, 21)]
    if sum(len(x) for x in sem) < PESAJES_MIN or any(len(x) < 3 for x in sem):
        return None
    # dos comparaciones semanales seguidas: la última semana con la anterior, y esa con la previa
    d1 = _media(sem[0]) - _media(sem[1])
    d2 = _media(sem[1]) - _media(sem[2])
    delta = (d1 + d2) / 2                                    # kg por semana
    paso, que = 0, ""
    if bloque in CONSTRUCCION:
        if d1 < 0.05 and d2 < 0.05:
            paso, que = PASO_KCAL, "no estás subiendo de peso"
        elif d1 > 0.35 and d2 > 0.35:
            paso, que = -PASO_KCAL, "estás subiendo más rápido de lo previsto"
    elif bloque in DEFINICION:
        if d1 > -0.15 and d2 > -0.15:
            paso, que = -PASO_KCAL, "no estás bajando de peso"
        elif d1 < -0.5 and d2 < -0.5:
            paso, que = PASO_KCAL, "estás bajando demasiado rápido"
    if not paso:
        return None
    # si ya aplicaste un ajuste en estas dos semanas, espera a ver su efecto
    if any(not a.get("deshecho") and a.get("que") == "kcal" and a.get("bloque") == bloque and _a_dias(a["f"]) > h - 14
           for a in _ajustes(r)):
        return None
    dr = _r2(delta)

    def aplicar(reg, ahora=None):
        k = kcal_extra(reg, bloque)
        return _con_ajuste(reg, {"f": hoy, "que": "kcal", "bloque": bloque, "antes": {"kcal": k},
                                 "despues": {"kcal": k + paso}, "deshecho": False})

    return {"tipo": "peso", "kcal": paso,
            "texto": "En las últimas dos semanas %s (%s%s kg/sem). Prueba %s%d kcal al día."
                     % (que, "+" if dr > 0 else "", ("%.2f" % dr).replace(".", ","), "+" if paso > 0 else "", paso),
            "aplicar": aplicar, "deshacer": lambda reg: _deshacer_ultimo(reg, hoy, "kcal")}
