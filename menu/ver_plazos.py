# -*- coding: utf-8 -*-
"""Verificación del reajuste dinámico del plan (v2.6): menu/plazos.py y menu/plazos.js.

   Comprueba con casos fijos:
   1. La cuenta de la semana: perfecta, 4 de 5, 3 de 5, 2 de 5, pádel en vez de fuerza,
      carrera fuera del plan, sesión del plan hecha otro día, fuerza del reloj sin fase,
      otra actividad de otro tipo, inicio a mitad de semana y cambio de año.
   2. Las propuestas: repetir cargas, alargar (inicio +7 días y apunte en ajustes, nunca
      un inicio futuro), deshacer (también al día siguiente y tras guardar el registro),
      reentrada a los 10 días justos, sesión pendiente, `desde` y peso.
   3. La comida del día: cambio de actividad, límites entre el tipo E y el tipo D.
   4. Que ninguna función modifica el registro que recibe (en Python y en JavaScript).
   5. Si Node está instalado, que plazos.js da exactamente lo mismo que plazos.py."""
import copy, json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plazos as P
from modelo import FASES, TIPOS

fallos = []


def ok(cond, msg):
    if not cond:
        fallos.append(msg)


def casi(a, b, tol=1e-9):
    return a is not None and abs(a - b) <= tol


# ---------------------------------------------------------------- datos de prueba
LUN = "2026-10-05"            # lunes: L 5, M 6, X 7, J 8, V 9, S 10, D 11
HOY = "2026-10-12"            # lunes siguiente
INICIO = "2026-09-07"


def reg(**kw):
    r = {"v": 1, "inicio": INICIO, "sesiones": [], "peso": [], "carrera": [], "activa": None}
    r.update(kw)
    return r


def ses(f, reloj=False):
    s = {"id": f, "fecha": f, "fase": "F1", "dia": "L", "nombre": "Fuerza", "dur": 4200, "ej": [], "abd": None}
    if reloj:
        s.update({"fase": None, "dia": None, "ej": [], "origen": "reloj"})
    return s


def car(f, reloj=False):
    c = {"id": f, "f": f, "tipo": "calidad", "km": 8, "min": 50}
    if reloj:
        c["origen"] = "reloj"
    return c


def dia(modo, sesion=None, act=None):
    return {"modo": modo, "sesion": sesion, "act": act, "t": 1}


def pesos(valores, fin=HOY):
    """Un peso por día terminando en `fin`: valores[-1] es el de `fin`."""
    n = len(valores)
    return [{"f": P._suma_dias(fin, -(n - 1 - i)), "kg": v} for i, v in enumerate(valores)]


def obj_plan(fase, tipo):
    k = FASES[fase][2]
    return {"kcal": round(k * TIPOS[tipo][2]), "kcalE": round(k * TIPOS["E"][2]), "kcalD": round(k * TIPOS["D"][2])}


def ida_y_vuelta(r):
    """Como si el registro se guardara en el móvil y se volviera a leer."""
    return json.loads(json.dumps(r))


PADEL = {"nombre": "Pádel", "tipo": "deporte", "min": 60, "int": "media"}
TROTE = {"nombre": "Trote", "tipo": "carrera", "min": 40, "int": "media"}

# ---------------------------------------------------------------- casos
# Cada caso: (nombre, función, argumentos). Los mismos se pasan a plazos.js.
casos = []


def caso(nombre, fn, *args):
    casos.append({"nombre": nombre, "fn": fn, "args": list(args)})
    return len(casos) - 1


R_PERF = reg(sesiones=[ses("2026-10-05"), ses("2026-10-07"), ses("2026-10-09")], carrera=[car("2026-10-06"), car("2026-10-08")])
R_CUATRO = reg(sesiones=[ses("2026-10-05"), ses("2026-10-07")], carrera=[car("2026-10-06"), car("2026-10-08")])
R_TRES = reg(sesiones=[ses("2026-10-05"), ses("2026-10-07")], carrera=[car("2026-10-06")])
R_DOS = reg(sesiones=[ses("2026-10-05")], carrera=[car("2026-10-06")])
c_perfecta = caso("semana perfecta", "adherencia", R_PERF, LUN)
c_cuatro = caso("4 de 5", "adherencia", R_CUATRO, LUN)
c_tres = caso("3 de 5", "adherencia", R_TRES, LUN)
c_dos = caso("2 de 5", "adherencia", R_DOS, LUN)
s_perfecta = caso("propuesta semana perfecta", "propuestaSemana", R_PERF, HOY)
s_cuatro = caso("propuesta 4 de 5", "propuestaSemana", R_CUATRO, HOY)
s_tres = caso("propuesta 3 de 5", "propuestaSemana", R_TRES, HOY)
s_dos = caso("propuesta 2 de 5", "propuestaSemana", R_DOS, HOY)
s_sin_inicio = caso("sin fecha de inicio: semana", "propuestaSemana", reg(inicio=None), HOY)
s_antes_inicio = caso("semana anterior al inicio", "propuestaSemana", reg(inicio=HOY), HOY)
s_desde = caso("semana anterior a desde", "propuestaSemana", R_DOS, HOY, None, "2026-10-12")

# inicio a mitad de semana (miércoles 7 oct): solo X, J y V son previstas
INI_X = "2026-10-07"
R_X3 = reg(inicio=INI_X, sesiones=[ses("2026-10-05"), ses("2026-10-07"), ses("2026-10-09")], carrera=[car("2026-10-08")])
R_X2 = reg(inicio=INI_X, sesiones=[ses("2026-10-07")], carrera=[car("2026-10-08")])
R_X1 = reg(inicio=INI_X, sesiones=[ses("2026-10-07")])
m_adh3 = caso("inicio miércoles: adherencia 3 de 3", "adherencia", R_X3, LUN)
m_adh2 = caso("inicio miércoles: adherencia 2 de 3", "adherencia", R_X2, LUN)
m_sem3 = caso("inicio miércoles: 3 de 3", "propuestaSemana", R_X3, HOY)
m_sem2 = caso("inicio miércoles: 2 de 3", "propuestaSemana", R_X2, HOY)
m_sem1 = caso("inicio miércoles: 1 de 3", "propuestaSemana", R_X1, HOY)
m_sab = caso("inicio en sábado: nada previsto", "propuestaSemana", reg(inicio="2026-10-10"), HOY)

# cambio de año: lunes 28 dic 2026 a domingo 3 ene 2027
R_ANIO = reg(inicio="2026-12-21", sesiones=[ses("2026-12-28"), ses("2026-12-30"), ses("2027-01-01")],
             carrera=[car("2026-12-29"), car("2026-12-31")])
y_adh = caso("cambio de año: semana perfecta", "adherencia", R_ANIO, "2027-01-01")
y_sem = caso("cambio de año: alargar", "propuestaSemana", reg(inicio="2026-12-21", sesiones=[ses("2026-12-28")]), "2027-01-04")

# reentrada y pendientes
d_diez = caso("reentrada a los 10 días justos", "propuestaDia", reg(sesiones=[ses("2026-10-02")]), HOY)
d_nueve = caso("9 días no es reentrada", "propuestaDia", reg(sesiones=[ses("2026-10-03")]), HOY)
d_nunca = caso("sin entrenar nunca desde el inicio", "propuestaDia", reg(inicio="2026-09-28"), HOY)
d_sin_inicio = caso("sin fecha de inicio: día", "propuestaDia", reg(inicio=None, sesiones=[ses("2026-09-01")]), HOY)
d_desde_ree = caso("desde reciente: no hay reentrada", "propuestaDia", reg(sesiones=[ses("2026-10-01")]), HOY, None, "2026-10-08")
d_pend = caso("sesión pendiente del martes", "propuestaDia", reg(sesiones=[ses("2026-10-05")]), "2026-10-07")
d_desde_pend = caso("desde hoy: no se recupera lo anterior", "propuestaDia", reg(sesiones=[ses("2026-10-05")]), "2026-10-07", None, "2026-10-07")
d_decidido = caso("hoy ya decidido", "propuestaDia", reg(sesiones=[ses("2026-10-05")], dias={"2026-10-07": dia("plan", "X")}), "2026-10-07")
d_descanso = caso("ayer descanso marcado", "propuestaDia", reg(sesiones=[ses("2026-10-05")], dias={"2026-10-06": dia("descanso")}), "2026-10-07")

# cuenta de la semana con casos especiales
a_padel = caso("pádel 60 min media en vez de Fuerza A", "adherencia", reg(dias={"2026-10-05": dia("otra", None, PADEL)}), LUN)
a_padel_suave = caso("pádel suave no cuenta", "adherencia", reg(dias={"2026-10-05": dia("otra", None, dict(PADEL, int="suave"))}), LUN)
a_padel_corto = caso("pádel de 20 min no cuenta", "adherencia", reg(dias={"2026-10-05": dia("otra", None, dict(PADEL, min=20))}), LUN)
a_trote_lunes = caso("otra de carrera un lunes vale 0,5", "adherencia", reg(dias={"2026-10-05": dia("otra", None, TROTE)}), LUN)
a_trote_martes = caso("otra de carrera un martes vale 1", "adherencia", reg(dias={"2026-10-06": dia("otra", None, TROTE)}), LUN)
a_carrera_fuera = caso("carrera fuera del plan en día de carrera", "adherencia", reg(carrera=[dict(car("2026-10-06"), tipo="libre")], dias={"2026-10-06": dia("plan", "M")}), LUN)
a_otro_dia = caso("Fuerza A hecha el martes", "adherencia", reg(sesiones=[ses("2026-10-06")], dias={"2026-10-05": dia("descanso"), "2026-10-06": dia("otro_plan", "L")}), LUN)
a_reloj = caso("fuerza del reloj sin fase ni ejercicios", "adherencia", reg(sesiones=[ses("2026-10-07", True)]), LUN)
a_marca = caso("marcar el plan sin registro no cuenta", "adherencia", reg(dias={"2026-10-05": dia("plan", "L")}), LUN)
a_dia_max1 = caso("un día cuenta como máximo 1", "adherencia", reg(sesiones=[ses("2026-10-05")], carrera=[car("2026-10-05")], dias={"2026-10-05": dia("otra", None, PADEL)}), LUN)
a_extra = caso("cuarta fuerza de la semana no cuenta", "adherencia", reg(sesiones=[ses("2026-10-05"), ses("2026-10-07"), ses("2026-10-09"), ses("2026-10-10")]), LUN)
a_carrera_x = caso("carrera registrada en miércoles ocupa hueco de carrera", "adherencia", reg(carrera=[car("2026-10-07")]), LUN)

# comida del día
PESO = 75
LUNES_A = "2026-11-02"      # tipo A
DOMINGO = "2026-11-08"      # tipo E
OB_A = obj_plan("B1", "A")
OB_E = obj_plan("B1", "E")
f_sin = caso("sin marcar el día", "dietaDelDia", reg(), LUNES_A, OB_A, PESO)
f_plan = caso("modo plan", "dietaDelDia", reg(dias={LUNES_A: dia("plan", "L")}), LUNES_A, OB_A, PESO)
f_padel = caso("pádel por la mañana", "dietaDelDia", reg(dias={LUNES_A: dia("otra", None, PADEL)}), LUNES_A, OB_A, PESO)
f_carrera = caso("cambio a media tarde a carrera alta", "dietaDelDia", reg(dias={LUNES_A: dia("otra", None, {"nombre": "Carrera", "tipo": "carrera", "min": 40, "int": "alta"})}), LUNES_A, OB_A, PESO)
f_tipo_e = caso("tipo E elegido a mano con pádel", "dietaDelDia", reg(dias={LUNES_A: dia("otra", None, PADEL)}), LUNES_A, dict(OB_E, sesion=None), PESO)
d_otro = caso("fuerza hecha el día de carrera", "propuestaDia", reg(sesiones=[ses("2026-10-05"), ses("2026-10-06")]), "2026-10-07")
f_desc = caso("descanso un lunes", "dietaDelDia", reg(dias={LUNES_A: dia("descanso")}), LUNES_A, OB_A, PESO)
f_ultra = caso("actividad enorme un domingo", "dietaDelDia", reg(dias={DOMINGO: dia("otra", None, {"nombre": "Ruta", "tipo": "bici", "min": 400, "int": "alta"})}), DOMINGO, OB_E, PESO)
f_dom_desc = caso("descanso un domingo", "dietaDelDia", reg(dias={DOMINGO: dia("descanso")}), DOMINGO, OB_E, PESO)
f_otro_plan = caso("tirada larga en lunes de fuerza", "dietaDelDia", reg(dias={LUNES_A: dia("otro_plan", "J")}), LUNES_A, OB_A, PESO)
k_padel = caso("kcal del pádel", "kcalActividad", PADEL, PESO)
k_nat = caso("kcal de natación con tilde", "kcalActividad", {"tipo": "Natación", "min": 30, "int": "alta"}, 80)
k_raro = caso("tipo desconocido es otro", "kcalActividad", {"tipo": "yoga", "min": 60}, 70)
k_nada = caso("sin actividad", "kcalActividad", None, 70)

# peso
BASE = [80.0] * 21
p_estanc = caso("B1 estancado", "propuestaPeso", reg(peso=pesos(BASE)), HOY, "B1")
p_estanc3 = caso("B3 estancado", "propuestaPeso", reg(peso=pesos(BASE)), HOY, "B3")
p_pocos = caso("menos de 10 pesajes", "propuestaPeso", reg(peso=pesos(BASE)[12:]), HOY, "B1")
p_sube = caso("B1 subiendo bien", "propuestaPeso", reg(peso=pesos([80.0] * 7 + [80.2] * 7 + [80.4] * 7)), HOY, "B1")
p_una = caso("B1 solo una semana estancada", "propuestaPeso", reg(peso=pesos([80.0] * 7 + [80.2] * 7 + [80.2] * 7)), HOY, "B1")
p_rapido = caso("B1 subiendo demasiado dos semanas", "propuestaPeso", reg(peso=pesos([80.0] * 7 + [80.5] * 7 + [81.0] * 7)), HOY, "B1")
p_def = caso("B4 estancado", "propuestaPeso", reg(peso=pesos(BASE)), HOY, "B4")
p_def_sube = caso("B4 subiendo 0,125 por semana", "propuestaPeso", reg(peso=pesos([80.0] * 7 + [80.125] * 7 + [80.25] * 7)), HOY, "B4")
p_def_bien = caso("B4 bajando a su ritmo", "propuestaPeso", reg(peso=pesos([80.0] * 7 + [79.7] * 7 + [79.4] * 7)), HOY, "B4")
p_def_rapido = caso("B4 bajando demasiado", "propuestaPeso", reg(peso=pesos([80.0] * 7 + [79.4] * 7 + [78.8] * 7)), HOY, "B4")
p_sin_regla = [caso("%s sin regla de peso" % b, "propuestaPeso", reg(peso=pesos(BASE)), HOY, b) for b in ("B0", "B2", "B5")]
p_desigual = caso("pesajes sin datos de una semana", "propuestaPeso", reg(peso=pesos(BASE)[:2] + pesos(BASE)[7:]), HOY, "B1")

# deshacer persistente: el registro ya aplicado, guardado y leído otra vez, sin la propuesta
AHORA = 1000
AP_ALARGAR = ida_y_vuelta(P.propuesta_semana(R_DOS, HOY)["aplicar"](R_DOS))
AP_PESO = ida_y_vuelta(P.propuesta_peso(reg(peso=pesos(BASE)), HOY, "B1")["aplicar"](reg(peso=pesos(BASE))))
R_PEND = reg(sesiones=[ses("2026-10-05")])
AP_RECUP = ida_y_vuelta(P.propuesta_dia(R_PEND, "2026-10-07")["aplicar"](R_PEND, AHORA))
u_alargar = caso("deshacer alargar al día siguiente", "deshacerAjuste", AP_ALARGAR, 0)
u_movido = caso("deshacer alargar con el inicio cambiado a mano", "deshacerAjuste", dict(AP_ALARGAR, inicio="2026-09-21"), 0)
u_peso = caso("deshacer +100 kcal", "deshacerAjuste", AP_PESO, 0)
u_recup = caso("deshacer recuperar", "deshacerAjuste", AP_RECUP, 0)
u_fuera = caso("deshacer un índice que no existe", "deshacerAjuste", AP_ALARGAR, 5)
u_neg = caso("deshacer índice negativo", "deshacerAjuste", AP_ALARGAR, -1)

FNS = {"adherencia": P.adherencia, "propuestaSemana": P.propuesta_semana, "propuestaDia": P.propuesta_dia,
       "propuestaPeso": P.propuesta_peso, "dietaDelDia": P.dieta_del_dia, "kcalActividad": P.kcal_actividad,
       "deshacerAjuste": P.deshacer_ajuste}


def resumen(res, r):
    """Pasa a datos lo que devuelve una propuesta, ejecutando aplicar y deshacer."""
    if res is None or not isinstance(res, dict) or "aplicar" not in res:
        return res
    ap = res["aplicar"](r, AHORA)
    out = {k: v for k, v in res.items() if k not in ("aplicar", "deshacer")}
    out["aplicado"] = ap
    out["deshecho"] = res["deshacer"](ap)
    return out


R = []
for c in casos:
    args = copy.deepcopy(c["args"])
    res = FNS[c["fn"]](*args)
    R.append(resumen(res, args[0]) if c["fn"].startswith("propuesta") else res)
    if args != c["args"]:
        fallos.append(f"{c['nombre']}: plazos.py ha modificado el registro que recibe")


# ---------------------------------------------------------------- comprobaciones
def adh(i, hechas, previstas=5):
    ok(casi(R[i]["hechas"], hechas), f"{casos[i]['nombre']}: hechas {R[i]['hechas']} y debería ser {hechas}")
    ok(R[i]["previstas"] == previstas, f"{casos[i]['nombre']}: previstas {R[i]['previstas']} y debería ser {previstas}")


adh(c_perfecta, 5); ok(casi(R[c_perfecta]["pct"], 1), "semana perfecta: pct")
adh(c_cuatro, 4); ok(casi(R[c_cuatro]["pct"], 0.8), "4 de 5: pct 0,8")
adh(c_tres, 3); adh(c_dos, 2)
ok(R[s_perfecta] is None and R[s_cuatro] is None, "con 4 o 5 de 5 no debe proponer nada")

# 3 de 5: repetir cargas, sin mover el inicio
p = R[s_tres]
ok(p and p["tipo"] == "repetir", "3 de 5 debe proponer repetir cargas")
if p:
    ok(p["aplicado"]["inicio"] == INICIO, "repetir cargas no debe mover el inicio")
    ok(len(p["aplicado"]["ajustes"]) == 1 and p["aplicado"]["ajustes"][0]["que"] == "repetir", "repetir: apunte en ajustes")
    ok(p["deshecho"]["ajustes"][0]["deshecho"] is True, "repetir: deshacer marca el apunte")

# 2 de 5: alargar con inicio +7 días
p = R[s_dos]
ok(p and p["tipo"] == "alargar", "2 de 5 debe proponer alargar")
if p:
    ok(p["aplicado"]["inicio"] == "2026-09-14", f"alargar: inicio {p['aplicado']['inicio']} y debería ser 2026-09-14")
    ok("14 sep" in p["texto"] and "2026-" not in p["texto"], "alargar: la fecha del texto va como «14 sep»")
    aj = p["aplicado"]["ajustes"]
    ok(len(aj) == 1 and aj[0]["que"] == "alargar" and aj[0]["antes"] == {"inicio": INICIO}
       and aj[0]["despues"] == {"inicio": "2026-09-14"} and aj[0]["deshecho"] is False, "alargar: entrada en ajustes")
    ok(p["deshecho"]["inicio"] == INICIO, "deshacer debe volver al inicio previo")
    ok(p["deshecho"]["ajustes"][0]["deshecho"] is True, "deshacer marca el ajuste como deshecho")
    ok(P.propuesta_semana(p["aplicado"], HOY) is None, "tras alargar no debe volver a proponerlo la misma semana")
    prop = P.propuesta_semana(R_DOS, HOY)
    ok(prop["aplicar"](prop["aplicar"](R_DOS))["inicio"] == "2026-09-14", "aplicar dos veces no debe alargar dos semanas")
ok(R[s_sin_inicio] is None, "sin fecha de inicio no hay propuesta de semana")
ok(R[s_antes_inicio] is None, "la semana anterior al inicio no se evalúa")
ok(R[s_desde] is None, "una semana anterior a desde no se juzga")

# inicio a mitad de semana
adh(m_adh3, 3, 3); ok(casi(R[m_adh3]["pct"], 1), "inicio miércoles: 3 de 3 es el 100 %")
ok([x["prevista"] for x in R[m_adh3]["detalle"]] == [False, False, True, True, True], "inicio miércoles: L y M no son previstas")
adh(m_adh2, 2, 3); ok(casi(R[m_adh2]["pct"], 0.667), "inicio miércoles: 2 de 3 es pct 0,667")
ok(R[m_sem3] is None, "inicio miércoles con 3 de 3: nada que proponer")
ok(R[m_sem2] and R[m_sem2]["tipo"] == "repetir" and "2 de 3" in R[m_sem2]["texto"], "inicio miércoles con 2 de 3: repetir cargas")
p = R[m_sem1]
ok(p and p["tipo"] == "alargar", "inicio miércoles con 1 de 3: alargar")
if p:
    ok(p["aplicado"]["inicio"] <= HOY, f"alargar nunca pone un inicio futuro ({p['aplicado']['inicio']})")
    ok(P._lunes_de(p["aplicado"]["inicio"]) == P._lunes_de(P._suma_dias(INI_X, 7)), "inicio limitado a hoy: misma semana que +7 días")
    ok(p["deshecho"]["inicio"] == INI_X, "deshacer vuelve al miércoles")
for i in (m_sem1, m_sem2, s_dos, s_tres):
    if R[i]:
        ok(R[i]["aplicado"]["inicio"] <= HOY, f"{casos[i]['nombre']}: inicio futuro")
ok(R[m_sab] is None, "inicio en sábado: sin sesiones previstas, sin propuesta")

# cambio de año
adh(y_adh, 5)
ok(R[y_adh]["detalle"][4]["fecha"] == "2027-01-01", "cambio de año: el viernes 1 de enero cuenta en la semana del 28 dic")
p = R[y_sem]
ok(p and p["tipo"] == "alargar" and p["aplicado"]["inicio"] == "2026-12-28" and "28 dic" in p["texto"],
   "cambio de año: alargar pasa el inicio al 28 dic")

# reentrada y pendientes
p = R[d_diez]
ok(p and p["tipo"] == "reentrada" and "10 días" in p["texto"], "10 días justos sin entrenar: reentrada")
if p:
    ok(p["aplicado"]["ajustes"][0]["que"] == "reentrada", "reentrada: apunte en ajustes")
    ok(p["deshecho"]["ajustes"][0]["deshecho"] is True, "reentrada: deshacer")
ok(R[d_nueve] is None, "9 días sin entrenar no es reentrada")
ok(R[d_nunca] and R[d_nunca]["tipo"] == "reentrada", "14 días desde el inicio sin entrenar nunca: reentrada")
ok(R[d_sin_inicio] is None, "sin fecha de inicio no hay propuesta de día")
ok(R[d_desde_ree] is None, "los días anteriores a desde no cuentan para la reentrada")
p = R[d_pend]
ok(p and p["tipo"] == "recuperar" and "martes 6 oct" in p["texto"], "debe proponer recuperar el martes 6 oct")
if p:
    d = p["aplicado"]["dias"]["2026-10-07"]
    ok(d["modo"] == "otro_plan" and d["sesion"] == "M" and d["t"] == AHORA, "recuperar: marca el día con la sesión pendiente")
    ok("2026-10-07" not in p["deshecho"].get("dias", {}), "recuperar: deshacer quita la marca")
ok(R[d_otro] and "hiciste otro entreno" in R[d_otro]["texto"], "recuperar: si ese día hubo otro entreno no dice que no hay registro")
ok(R[f_tipo_e]["kcal"] == min(OB_E["kcalD"], OB_E["kcal"] + P.kcal_actividad(PADEL, PESO)), "tipo E a mano: no resta el entreno del día")
ok(R[d_desde_pend] is None, "un día anterior a desde no se propone recuperar")
ok(R[d_decidido] is None, "si hoy ya está decidido no se propone recuperar")
ok(R[d_descanso] is None, "un descanso marcado no se propone recuperar")

# cuenta de la semana: casos especiales
adh(a_padel, 0.5)
ok(R[a_padel]["detalle"][0]["valor"] == 0.5 and R[a_padel]["detalle"][0]["via"] == "otra", "pádel: ocupa la Fuerza A con 0,5")
adh(a_padel_suave, 0); adh(a_padel_corto, 0)
adh(a_trote_lunes, 0.5)
ok(R[a_trote_lunes]["detalle"][0]["valor"] == 0.5 and R[a_trote_lunes]["detalle"][1]["valor"] == 0,
   "otra de carrera un lunes: 0,5 en la Fuerza A, sin ocupar la carrera del martes")
adh(a_trote_martes, 1)
adh(a_carrera_fuera, 1)
ok(R[a_carrera_fuera]["detalle"][1]["valor"] == 1, "carrera fuera del plan en martes: cuenta para la carrera de calidad")
adh(a_otro_dia, 1)
ok(R[a_otro_dia]["detalle"][0]["fecha"] == "2026-10-06" and R[a_otro_dia]["detalle"][1]["valor"] == 0,
   "sesión del plan hecha otro día: cuenta una vez, en su hueco")
adh(a_reloj, 1)
ok(R[a_reloj]["detalle"][2]["fecha"] == "2026-10-07" and R[a_reloj]["detalle"][2]["via"] == "reloj",
   "fuerza del reloj (fase y dia null, ej vacío): cuenta por fecha")
adh(a_marca, 0)
adh(a_dia_max1, 1)
adh(a_extra, 3)
adh(a_carrera_x, 1)
ok(R[a_carrera_x]["detalle"][1]["fecha"] == "2026-10-07", "carrera registrada en miércoles: ocupa el primer hueco de carrera")

# comida del día
ok(R[f_sin]["factor"] == 1 and R[f_sin]["kcal"] == OB_A["kcal"], "sin marcar el día: factor 1")
ok(R[f_plan]["factor"] == 1, "modo plan: factor 1")
esp = OB_A["kcal"] - P._netas(5, 70, PESO) + P.kcal_actividad(PADEL, PESO)
ok(abs(R[f_padel]["kcal"] - esp) <= 1 and casi(R[f_padel]["factor"], P._r3(R[f_padel]["kcal"] / OB_A["kcal"])),
   f"pádel: kcal {R[f_padel]['kcal']} y se esperaban {esp:.0f}")
ok(R[f_padel]["factor"] > 1, "pádel (más gasto que la fuerza prevista): el factor sube")
ok(R[f_carrera]["factor"] > R[f_padel]["factor"], "cambiar de actividad a media tarde cambia el factor de la comida")
ok(R[f_desc]["kcal"] == OB_A["kcalE"], f"descanso un lunes: se limita al tipo E ({R[f_desc]['kcal']} frente a {OB_A['kcalE']})")
ok(R[f_desc]["factor"] < 1 and "mínimo: día de descanso" in R[f_desc]["motivo"], "descanso un lunes: factor menor que 1 y motivo de mínimo")
ok(R[f_ultra]["kcal"] == OB_E["kcalD"], f"actividad enorme: se limita al tipo D ({R[f_ultra]['kcal']} frente a {OB_E['kcalD']})")
ok("(máximo: día de sábado)" in R[f_ultra]["motivo"], "actividad enorme: motivo «(máximo: día de sábado)»")
ok(R[f_dom_desc]["factor"] == 1, "descanso un domingo: sin cambios")
ok(abs(R[f_otro_plan]["kcal"] - round(OB_A["kcal"] - P._netas(5, 70, PESO) + P._netas(7, 60, PESO))) <= 1,
   "tirada larga en lunes de fuerza: usa 60 min a 7 MET")
ok(R[k_padel] == round(6 * PESO * 1), "kcal del pádel: (7-1) x peso x 1 h")
ok(R[k_nat] == round(9 * 80 * 0.5), "natación con tilde: MET 10 menos 1")
ok(R[k_raro] == round(4 * 70), "tipo desconocido: MET de otro (media)")
ok(R[k_nada] == 0, "sin actividad: 0 kcal")

# peso
p = R[p_estanc]
ok(p and p["kcal"] == 100, "B1 estancado debe proponer +100 kcal")
if p:
    ok(P.kcal_extra(p["aplicado"], "B1") == 100 and P.kcal_extra(p["deshecho"], "B1") == 0, "peso: aplicar suma 100 y deshacer lo quita")
    ok(P.propuesta_peso(p["aplicado"], HOY, "B1") is None, "tras aplicar no se vuelve a proponer en dos semanas")
ok(R[p_estanc3] and R[p_estanc3]["kcal"] == 100, "B3 estancado: +100 kcal")
ok(R[p_pocos] is None, "con menos de 10 pesajes no propone nada")
ok(R[p_sube] is None, "B1 subiendo a +0,2 kg por semana: nada que proponer")
ok(R[p_una] is None, "B1 con solo una semana estancada: nada (hacen falta dos seguidas)")
ok(R[p_rapido] and R[p_rapido]["kcal"] == -100, "B1 subiendo más de +0,35 dos semanas: -100 kcal")
ok(R[p_def] and R[p_def]["kcal"] == -100, "B4 estancado: -100 kcal")
p = R[p_def_sube]
ok(p and p["kcal"] == -100 and "(+0,13 kg/sem)" in p["texto"], "B4 subiendo 0,125: -100 kcal y texto «+0,13 kg/sem»")
ok(R[p_def_bien] is None, "B4 bajando a -0,3 kg por semana: nada que proponer")
ok(R[p_def_rapido] and R[p_def_rapido]["kcal"] == 100 and "(-0,60 kg/sem)" in R[p_def_rapido]["texto"],
   "B4 bajando más de -0,5 dos semanas: +100 kcal y texto «-0,60 kg/sem»")
ok(all(R[i] is None for i in p_sin_regla), "B0, B2 y B5 no tienen regla de peso")
ok(R[p_desigual] is None, "sin pesajes suficientes en una de las semanas: nada")

# deshacer persistente
ok(R[u_alargar]["inicio"] == INICIO and R[u_alargar]["ajustes"][0]["deshecho"] is True,
   "deshacerAjuste: alargar vuelve al inicio previo tras guardar y leer el registro")
ok(R[u_movido]["inicio"] == "2026-09-21" and R[u_movido]["ajustes"][0]["deshecho"] is True,
   "deshacerAjuste: si el inicio se cambió a mano, no lo toca y marca el apunte")
ok(P.kcal_extra(R[u_peso], "B1") == 0 and R[u_peso]["ajustes"][0]["deshecho"] is True, "deshacerAjuste: kcal deja de sumar")
ok("2026-10-07" not in R[u_recup]["dias"] and R[u_recup]["ajustes"][0]["deshecho"] is True, "deshacerAjuste: recuperar vuelve el día a como estaba")
ok(R[u_fuera] == AP_ALARGAR and R[u_neg] == AP_ALARGAR, "deshacerAjuste con un índice que no existe: no cambia nada")
otra_vez = P.deshacer_ajuste(R[u_alargar], 0)
ok(otra_vez == R[u_alargar], "deshacerAjuste dos veces: la segunda no cambia nada")

# ---------------------------------------------------------------- comparar con Node
node = shutil.which("node")
if node:
    js = r"""
const P = require(process.argv[1]);
const casos = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const AHORA = 1000;
function resumen(res, r){
  if(res === null || typeof res !== 'object' || typeof res.aplicar !== 'function') return res;
  const ap = res.aplicar(r, AHORA), out = {};
  Object.keys(res).forEach(k => { if(k !== 'aplicar' && k !== 'deshacer') out[k] = res[k]; });
  out.aplicado = ap; out.deshecho = res.deshacer(ap);
  return out;
}
console.log(JSON.stringify(casos.map(c => {
  const a = JSON.parse(JSON.stringify(c.args)), antes = JSON.stringify(a);
  const res = P[c.fn](...a);
  const r = c.fn.startsWith('propuesta') ? resumen(res, a[0]) : res;
  return {r, mutado: JSON.stringify(a) !== antes};
})));
"""
    r = subprocess.run([node, "-e", js, os.path.abspath(os.path.join(os.path.dirname(__file__), "plazos.js"))],
                       input=json.dumps(casos), capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        fallos.append("plazos.js no se ha podido ejecutar: " + r.stderr.strip()[:300])
    else:
        salida = json.loads(r.stdout)
        for i, s in enumerate(salida):
            if s["mutado"]:
                fallos.append(f"{casos[i]['nombre']}: plazos.js ha modificado el registro que recibe")
        py = json.loads(json.dumps(R))
        dif = [casos[i]["nombre"] for i, (a, b) in enumerate(zip(py, salida)) if a != b["r"]]
        if dif:
            fallos.append(f"plazos.js y plazos.py no dan lo mismo en {len(dif)} de {len(casos)} casos: " + ", ".join(dif[:6]))
        else:
            print(f"plazos.js y plazos.py coinciden en {len(casos)} casos")
else:
    print("Node no está instalado: no se compara plazos.js con plazos.py")

for f in fallos[:40]:
    print("FALLO", f)
print("TODO OK" if not fallos else f"HAY FALLOS: {len(fallos)}")
sys.exit(1 if fallos else 0)
