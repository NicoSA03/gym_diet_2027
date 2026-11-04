# -*- coding: utf-8 -*-
"""Verificación de la conectividad con relojes (v3.0).

   1. Casos de viabilidad: que salga el aviso de imposible solo cuando toca y que
      lo alcanzable en X días tenga sentido.
   2. Métricas: que se pida por pantalla justo lo que falta según el objetivo y
      que lo escrito a mano mande sobre lo del reloj.
   3. Si Node está instalado: genera un .FIT, un .GPX, un .TCX, un CSV de Garmin,
      uno de Strava y un export.xml de Apple Salud de prueba, los lee con
      menu/conectividad.js y comprueba lo que saca. Además, que el JS y este
      Python dan exactamente lo mismo en todos los casos.
   No toca el plan en curso ni ningún archivo del repositorio."""
import calendar, datetime, json, os, shutil, struct, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conectividad import evaluar, AVISO_IMPOSIBLE

fallos = []
def comprueba(cond, txt):
    print(("  ok    " if cond else "  FALLO ") + txt)
    if not cond:
        fallos.append(txt)

BASE = dict(edad=30, sexo="h", altura=175, peso=79.5, dias_semana=5)
CASOS = [
 ("5 km 27:30 a 23:00 en 39 semanas (el plan de hoy)", None, dict(BASE, objetivo="5k", test_5k="27:30", objetivo_5k="23:00", dias_plan=273), True),
 ("5 km 27:30 a 23:00 en 90 días", None, dict(BASE, objetivo="5k", test_5k="27:30", objetivo_5k="23:00", dias_plan=90), False),
 ("5 km tras 8 semanas parado, 190 días", None, dict(BASE, objetivo="5k", test_5k="27:30", objetivo_5k="23:00", dias_plan=190, semanas_parado=8), False),
 ("Perder 5 kg en 120 días", None, dict(BASE, objetivo="perder", peso_objetivo=74.5, dias_plan=120), True),
 ("Perder 10 kg en 60 días", None, dict(BASE, objetivo="perder", peso_objetivo=69.5, dias_plan=60), False),
 ("Ganar 3 kg en 84 días", None, dict(BASE, objetivo="ganar", peso_objetivo=82.5, dias_plan=84), True),
 ("Ganar 6 kg en 84 días", None, dict(BASE, objetivo="ganar", peso_objetivo=85.5, dias_plan=84), False),
 ("Mantener 14 días (menos del mínimo de 4 semanas)", None, dict(BASE, objetivo="mantener", dias_plan=14), False),
 ("Mantener 28 días", None, dict(BASE, objetivo="mantener", dias_plan=28), True),
]

print("1. Viabilidad del plan de X días")
for txt, reloj, manual, esperado in CASOS:
    r = evaluar(reloj, manual)
    v = r.get("viabilidad") or {}
    comprueba(r["estado"] == "listo" and v.get("ok") == esperado,
              "%s: %s (mínimo %s días)" % (txt, "posible" if v.get("ok") else "imposible", v.get("min_dias")))
    if v and not v["ok"]:
        comprueba(v["aviso"] == AVISO_IMPOSIBLE, "  muestra el aviso de imposible")
    if v and not v["ok"] and v["alcanzable"] and "objetivo_5k" in v["alcanzable"]:
        a = v["alcanzable"]["objetivo_5k"]
        comprueba("23:00" < a <= "27:30", "  5 km alcanzable en ese tiempo: %s" % a)

print("2. Qué métricas se piden")
r = evaluar(None, dict(objetivo="5k", dias_plan=200))
comprueba(r["estado"] == "faltan" and r["faltan"] == ["edad", "sexo", "altura", "peso", "dias_semana", "test_5k", "objetivo_5k"],
          "Sin reloj y objetivo 5 km pide: " + ", ".join(r["faltan"]))
r = evaluar(dict(edad=30, sexo="h", altura=175, peso=80.1, test_5k="26:50"), dict(objetivo="5k", dias_plan=200, dias_semana=5, objetivo_5k="24:00"))
comprueba(r["faltan"] == [] and r["origen"]["peso"] == "reloj" and r["origen"]["test_5k"] == "reloj",
          "Con reloj solo pide objetivo, días y 5 km deseado")
r = evaluar(dict(peso=80.1), dict(BASE, objetivo="mantener", dias_plan=30))
comprueba(r["valores"]["peso"] == 79.5 and r["origen"]["peso"] == "manual", "Lo escrito a mano manda sobre el reloj")
comprueba(r["valores"]["fc_max"] == 187 and r["origen"]["fc_max"] == "calculado", "Pulso máximo calculado por la edad: 187")
r = evaluar(None, dict(BASE, objetivo="mantener", dias_plan=30, altura=18))
comprueba(r["estado"] == "faltan" and r["malas"] == ["altura"], "Una altura de 18 cm se rechaza")
r = evaluar(None, dict(BASE, objetivo="mantener", dias_plan=30, peso="79,5"))
comprueba(r["estado"] == "listo" and r["valores"]["peso"] == 79.5, "Un peso escrito «79,5» se entiende")
MALOS = [
 ("Un peso «abc» se rechaza", dict(peso="abc", objetivo="mantener"), ["peso"]),
 ("Un 5 km deseado de «23» (sin segundos) se rechaza", dict(objetivo="5k", test_5k="27:30", objetivo_5k="23"), ["objetivo_5k"]),
 ("Perder hasta un peso mayor que el actual se rechaza", dict(objetivo="perder", peso_objetivo=85), ["peso_objetivo"]),
 ("Ganar hasta un peso menor que el actual se rechaza", dict(objetivo="ganar", peso_objetivo=75), ["peso_objetivo"]),
 ("Una edad «abc» se rechaza sin pedir el pulso máximo", dict(edad="abc", objetivo="mantener"), ["edad"]),
 ("Un 5 km con 75 segundos se rechaza", dict(objetivo="5k", test_5k="27:75", objetivo_5k="25:00"), ["test_5k"]),
 ("Un 5 km de 1:02:30 (h:mm:ss) se acepta", dict(objetivo="5k", test_5k="1:02:30", objetivo_5k="55:00"), []),
 ("Un 5 km de 62:30 se acepta", dict(objetivo="5k", test_5k="62:30", objetivo_5k="55:00"), []),
 ("Un 5 km deseado más lento que el actual se rechaza", dict(objetivo="5k", test_5k="27:30", objetivo_5k="29:00"), ["objetivo_5k"]),
]
for txt, extra, esperado in MALOS:
    r = evaluar(None, dict(BASE, dias_plan=200, **extra))
    comprueba(r["malas"] == esperado and (r["estado"] == "faltan") == bool(esperado), txt)
CASOS += [("Caso malo: " + t, None, dict(BASE, dias_plan=200, **e), None) for t, e, _ in MALOS]
CASOS.append(("Caso malo: peso 79,5 con coma", None, dict(BASE, objetivo="mantener", dias_plan=30, peso="79,5"), None))

# ---------------------------------------------------------------- archivos de prueba
def fit_prueba():
    """FIT mínimo con user_profile y session (10,02 km en 52:13, FC 151/178)."""
    def crc(data, c=0):
        T = [0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
             0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400]
        for b in data:
            t = T[c & 0xF]; c = (c >> 4) & 0x0FFF; c ^= t ^ T[b & 0xF]
            t = T[c & 0xF]; c = (c >> 4) & 0x0FFF; c ^= t ^ T[(b >> 4) & 0xF]
        return c
    rec = b""
    # definición local 0: user_profile (3) gender, age, height, weight, resting_hr, max_hr
    rec += bytes([0x40, 0, 0]) + struct.pack("<H", 3) + bytes([6]) + bytes([1, 1, 0, 2, 1, 2, 3, 1, 2, 4, 2, 0x84, 8, 1, 2, 11, 1, 2])
    rec += bytes([0x00, 1, 30, 175]) + struct.pack("<H", 795) + bytes([52, 190])
    # definición local 1: session (18) start_time, sport, elapsed, distance, avg_hr, max_hr
    rec += bytes([0x41, 0, 0]) + struct.pack("<H", 18) + bytes([6]) + bytes([2, 4, 0x86, 5, 1, 0, 7, 4, 0x86, 9, 4, 0x86, 16, 1, 2, 17, 1, 2])
    t = calendar.timegm((2026, 11, 3, 12, 0, 0)) - 631065600   # 3 nov 2026 en tiempo FIT
    rec += bytes([0x01]) + struct.pack("<IBII", t, 1, 3133000, 1002000) + bytes([151, 178])
    cab = bytes([14, 0x20]) + struct.pack("<HI", 2132, len(rec)) + b".FIT"
    cab += struct.pack("<H", crc(cab))
    return cab + rec + struct.pack("<H", crc(cab + rec))

GPX = """<?xml version="1.0"?><gpx version="1.1" xmlns:gpxtpx="x"><trk><type>running</type><trkseg>
<trkpt lat="40.4000" lon="-3.7000"><time>2026-11-01T12:00:00Z</time><extensions><gpxtpx:hr>140</gpxtpx:hr></extensions></trkpt>
<trkpt lat="40.4225" lon="-3.7000"><time>2026-11-01T12:13:00Z</time><extensions><gpxtpx:hr>160</gpxtpx:hr></extensions></trkpt>
<trkpt lat="40.4450" lon="-3.7000"><time>2026-11-01T12:26:30Z</time><extensions><gpxtpx:hr>175</gpxtpx:hr></extensions></trkpt>
</trkseg></trk></gpx>"""
TCX = """<?xml version="1.0"?><TrainingCenterDatabase><Activities><Activity Sport="Running">
<Lap StartTime="2026-10-28T12:00:00Z"><TotalTimeSeconds>1650</TotalTimeSeconds><DistanceMeters>5000</DistanceMeters>
<AverageHeartRateBpm><Value>165</Value></AverageHeartRateBpm><MaximumHeartRateBpm><Value>181</Value></MaximumHeartRateBpm></Lap>
</Activity></Activities></TrainingCenterDatabase>"""
CSV_GARMIN = '﻿Tipo de actividad,Fecha,Favorito,Título,Distancia,Calorías,Tiempo,Frecuencia cardiaca media,FC máxima\n' \
             '"Carrera","2026-10-30 07:05:00","false","Madrid Carrera","6,50","480","00:36:10","158","176"\n' \
             '"Fuerza","2026-10-29 07:00:00","false","Fuerza","0,00","300","01:00:00","110","140"\n' \
             '"Natación en piscina","2026-10-27 00:30:00","false","Piscina","1.500","300","00:35:00","120","150"\n'
CSV_STRAVA = 'Activity ID,Activity Date,Activity Name,Activity Type,Elapsed Time,Distance\n' \
             '1,"Oct 20, 2026, 7:00:00 AM",Tirada,Run,3600,10500\n2,"Oct 13, 2026, 7:00:00 AM",Series,Run,2400,7000\n'
APPLE = """<?xml version="1.0"?><HealthData locale="es_ES">
<Me HKCharacteristicTypeIdentifierDateOfBirth="1996-03-10" HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexMale"/>
<Record type="HKQuantityTypeIdentifierBodyMass" unit="kg" startDate="2026-10-01 08:00:00 +0200" value="80.4"/>
<Record type="HKQuantityTypeIdentifierBodyMass" unit="kg" startDate="2026-11-02 08:00:00 +0200" value="79.8"/>
<Record type="HKQuantityTypeIdentifierHeight" unit="cm" startDate="2026-01-01 08:00:00 +0200" value="175"/>
<Record type="HKQuantityTypeIdentifierRestingHeartRate" unit="count/min" startDate="2026-11-02 08:00:00 +0200" value="54"/>
<Record type="HKQuantityTypeIdentifierVO2Max" unit="mL/min/kg" startDate="2026-11-02 08:00:00 +0200" value="41.26"/>
<Workout workoutActivityType="HKWorkoutActivityTypeTraditionalStrengthTraining" duration="62" durationUnit="min" startDate="2026-11-02 07:00:00 +0200"/>
<Workout workoutActivityType="HKWorkoutActivityTypeRunning" duration="40" durationUnit="min" startDate="2026-10-21 07:00:00 +0200">
 <WorkoutStatistics type="HKQuantityTypeIdentifierDistanceWalkingRunning" startDate="2026-10-21 07:00:00 +0200" sum="7.2" unit="km"/>
</Workout>
<Workout workoutActivityType="HKWorkoutActivityTypeRunning" duration="27.5" durationUnit="min" totalDistance="5.0" totalDistanceUnit="km" startDate="2026-10-25 07:00:00 +0200"/>
</HealthData>"""

node = shutil.which("node")
if not node:
    print("3. Node no está instalado: se salta la lectura de archivos y la comparación con el JS")
else:
    print("3. Lectura de archivos del reloj con menu/conectividad.js")
    tmp = tempfile.mkdtemp()
    try:
        archivos = {"carrera.fit": fit_prueba(), "carrera.gpx": GPX, "carrera.tcx": TCX,
                    "Activities.csv": CSV_GARMIN, "activities.csv": CSV_STRAVA, "export.xml": APPLE}
        for n, c in archivos.items():
            with open(os.path.join(tmp, n), "wb") as f:
                f.write(c if isinstance(c, bytes) else c.encode("utf-8"))
        casos = [[c[1], c[2]] for c in CASOS]
        js = r"""
const C = require(process.argv[2]), fs = require("fs"), path = require("path");
const dir = process.argv[3], hoy = "2026-11-04";
const lect = {};
for (const n of fs.readdirSync(dir).sort()) {
  if (n === "casos.json" || n === "prueba.js") continue;
  const b = fs.readFileSync(path.join(dir, n));
  lect[n] = C.leerArchivo(n, n.endsWith(".fit") ? b : b.toString("utf8"));
}
const todo = C.juntar(Object.values(lect), hoy);
const casos = JSON.parse(fs.readFileSync(path.join(dir, "casos.json"), "utf8")).map(([r, m]) => C.evaluar(r, m));
const reg = C.aRegistro(todo.sesiones, {sesiones:[{fecha:"2026-11-02", ej:[{n:"Sentadilla"}]}], carrera:[{f:"2026-10-28", km:5, min:27.5}]});
console.log(JSON.stringify({lect, todo, casos, reg}));
"""
        with open(os.path.join(tmp, "casos.json"), "w", encoding="utf-8") as f:
            json.dump(casos, f)
        with open(os.path.join(tmp, "prueba.js"), "w", encoding="utf-8") as f:
            f.write(js)
        out = subprocess.run([node, os.path.join(tmp, "prueba.js"), os.path.abspath("menu/conectividad.js"), tmp],
                             capture_output=True, text=True, timeout=60)
        if out.returncode:
            comprueba(False, "El JS falla: " + " ".join(l for l in out.stderr.splitlines() if "Error" in l)[:300])
        else:
            R = json.loads(out.stdout)
            L = R["lect"]
            fit = L["carrera.fit"]
            s = fit["actividades"][0]
            comprueba(s["deporte"] == "carrera" and s["dist"] == 10020 and s["seg"] == 3133 and s["fc_max"] == 178 and s["fecha"] == "2026-11-03",
                      "FIT: carrera de 10,02 km en 52:13 del 3 nov, FC máx 178")
            comprueba(fit["perfil"] == dict(sexo="h", edad=30, altura=175, peso=79.5, fc_reposo=52, fc_max=190),
                      "FIT: perfil del reloj (edad, altura, peso, pulso)")
            g = L["carrera.gpx"]["actividades"][0]
            comprueba(4950 <= g["dist"] <= 5050 and g["seg"] == 1590 and g["fc_max"] == 175, "GPX: unos 5 km en 26:30 (%d m)" % g["dist"])
            t = L["carrera.tcx"]["actividades"][0]
            comprueba(t["dist"] == 5000 and t["seg"] == 1650 and t["fc_media"] == 165, "TCX: 5 km en 27:30")
            ga = L["Activities.csv"]["actividades"]
            comprueba(len(ga) == 3 and ga[0]["dist"] == 6500 and ga[0]["seg"] == 2170 and ga[1]["deporte"] == "fuerza" and ga[1]["dist"] == 0,
                      "CSV de Garmin: la carrera de 6,5 km y la sesión de fuerza (sin distancia)")
            comprueba(ga[2]["deporte"] == "natación" and ga[2]["dist"] == 1500 and ga[2]["fecha"] == "2026-10-27",
                      "CSV de Garmin: 1.500 m de natación en metros y la carrera en km, aunque vayan juntas; a las 00:30 sigue siendo el 27")
            st = L["activities.csv"]["actividades"]
            comprueba(len(st) == 2 and st[0]["dist"] == 10500 and st[0]["fecha"] == "2026-10-20", "CSV de Strava: distancia en metros detectada")
            h = datetime.date.today()
            edad_apple = h.year - 1996 - ((h.month, h.day) < (3, 10))
            ap = L["export.xml"]
            comprueba(ap["perfil"] == dict(edad=edad_apple, sexo="h", peso=79.8, altura=175, fc_reposo=54, vo2max=41.3),
                      "Apple Salud: perfil con la medida más reciente de cada cosa")
            comprueba([a["deporte"] for a in ap["actividades"]] == ["fuerza", "carrera", "carrera"] and ap["actividades"][2]["seg"] == 1650,
                      "Apple Salud: la sesión de fuerza y la carrera de 5 km")
            comprueba(ap["actividades"][1]["dist"] == 7200, "Apple Salud de iOS 16 o posterior: distancia sacada de WorkoutStatistics")
            d = R["todo"]["datos"]
            comprueba(d.get("test_5k") == "25:00", "Todo junto: mejor 5 km de los últimos 90 días = %s (los 10,02 km del FIT llevados a 5 km)" % d.get("test_5k"))
            comprueba(d.get("km_semana") == 14.1 and d.get("semanas_parado") == 0, "Todo junto: %s km por semana el último mes" % d.get("km_semana"))
            cal = R["todo"]["sesiones"]
            comprueba(len(cal) == 11 and [c["fecha"] for c in cal] == sorted(c["fecha"] for c in cal),
                      "Calendario: %d sesiones del reloj ordenadas por fecha" % len(cal))
            comprueba({"fecha": "2026-10-29", "tipo": "fuerza", "km": None, "min": 60, "fc_media": 110, "origen": "reloj"} in cal,
                      "Calendario: la sesión de fuerza del 29 oct con su hora de duración")
            reg = R["reg"]
            comprueba(len(reg["carrera"]) == 7 and all(x["origen"] == "reloj" and x["tipo"] == "Rodaje" for x in reg["carrera"]),
                      "Registro: 7 carreras nuevas con el formato de a6.js (la del 28 oct ya estaba apuntada)")
            comprueba([x["fecha"] for x in reg["sesiones"]] == ["2026-10-29"] and reg["sesiones"][0]["dur"] == 3600 and reg["sesiones"][0]["ej"] == [],
                      "Registro: solo la fuerza del 29 oct (la del 2 nov ya estaba en la app con sus ejercicios)")
            print("4. El JS y el Python dan lo mismo")
            iguales = 0
            for (txt, rl, mn, _), rj in zip(CASOS, R["casos"]):
                rp = json.loads(json.dumps(evaluar(rl, mn)).replace("NaN", "null"))   # JSON de JS escribe NaN como null
                if rp == rj:
                    iguales += 1
                else:
                    comprueba(False, "Distinto en «%s»: py %s / js %s" % (txt, rp.get("viabilidad"), rj.get("viabilidad")))
            comprueba(iguales == len(CASOS), "%d de %d casos idénticos" % (iguales, len(CASOS)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

print()
if fallos:
    print("FALLO: %d comprobaciones de conectividad no pasan" % len(fallos))
    sys.exit(1)
print("TODO OK: conectividad")
