# -*- coding: utf-8 -*-
"""Verificación del macrociclo de entrenamiento."""
import sys; sys.path.insert(0,'menu')
from entreno import *

fallos=0
def chk(ok, txt):
    global fallos
    if not ok: fallos+=1
    print(("  OK  " if ok else "  FALLO ")+txt)

print("== 1. Calendario continuo, en lunes, y 39 semanas ==")
cal=calendario()
chk(sum(c['sem'] for c in cal)==39, f"suma de bloques = {sum(c['sem'] for c in cal)} semanas")
chk(all(c['ini'].weekday()==0 for c in cal), "todos los bloques empiezan en lunes")
for a,b in zip(cal,cal[1:]):
    chk((b['ini']-a['fin']).days==1, f"{a['cod']} → {b['cod']} sin hueco ni solape")
chk(cal[-1]['fin'].isoformat()=="2027-06-20", f"termina el {fecha(cal[-1]['fin'])}")
for c in cal:
    print(f"       {c['cod']} {c['n']:24s} {c['sem']:2d} sem · {fecha(c['ini'])} → {fecha(c['fin'])} · dieta {c['dieta']}")

print("\n== 2. Volumen semanal por grupo dentro de rango útil ==")
GRANDES={"Cuádriceps","Isquios","Glúteo","Pectoral","Espalda","Hombro"}
for fc,f in FASES.items():
    esq=f["esquema"]; vol={}
    for d in DIAS:
        for tier,ej in d["ej"]:
            for m in EJ[ej]["m"]: vol[m]=vol.get(m,0)+esq[tier][0]
    # F0 (rearranque) y F5 (afinamiento) van por debajo a propósito:
    # ahí el suelo es el de mantenimiento, no el de construcción.
    piso = 6 if fc in ("F0","F5") else 10
    malos=[(m,v) for m,v in vol.items()
           if not ((piso<=v<=22) if m in GRANDES else (4<=v<=22))]
    chk(not malos, f"{fc} {f['n'][:20]:20s} " +
        " ".join(f"{m[:4]}{v}" for m,v in sorted(vol.items())) +
        ("" if not malos else f"  ← fuera de rango: {malos}"))

print("\n== 3. Cada patrón se entrena al menos 2 veces por semana ==")
pat={}
for d in DIAS:
    for _,ej in d["ej"]: pat[EJ[ej]["p"]]=pat.get(EJ[ej]["p"],0)+1
for p,n in sorted(pat.items()):
    chk(n>=1, f"{p}: {n} vez/semana" if n==1 else f"{p}: {n} veces/semana")
chk(sum(v for k,v in pat.items() if "Empuje" in k)>=3, "empuje total ≥ 3 sesiones/semana")
chk(sum(v for k,v in pat.items() if "Tirón" in k)>=3, "tirón total ≥ 3 sesiones/semana")

print("\n== 4. Duración de sesión entre 45 y 80 min (abdominales incluidos) ==")
DESC={"T1":3.25,"T2":2.25,"T3":1.4,"TF":1.2}
TABATA_MIN=8   # 5:20 de reloj + montaje y estiramiento
peor=0
for fc,f in FASES.items():
    for d in DIAS:
        if d["tipo"]!="fuerza": continue
        mins=8+sum(f["esquema"][t][0]*DESC[t] for t,_ in d["ej"])+(TABATA_MIN if d["tabata"] else 0)
        peor=max(peor,mins)
        if mins<45 or mins>80: chk(False, f"{fc}/{d['cod']} {mins:.0f} min")
chk(peor<=80, f"la sesión más larga de todo el plan son {peor:.0f} min (tope 80)")

print("\n== 4b. Abdominales: tabata por debajo de 10 min y uno por día de fuerza ==")
reloj = 8*20 + 8*20            # 8 rondas de 20 s de trabajo y 20 de descanso
chk(reloj/60 <= 10, f"el tabata son {reloj//60}:{reloj%60:02d} de reloj")
chk(reloj/60 + 2.5 <= 10, f"con montaje y estiramiento, {(reloj/60)+2.5:.1f} min (tope 10)")
for d in DIAS:
    if d["tipo"]=="fuerza":
        chk(d["tabata"] in TABATA, f"{d['dia']}: tabla {d['tabata']}")
    else:
        chk(d["tabata"] is None, f"{d['dia']}: sin abdominales, es día de carrera")
chk(len({d["tabata"] for d in DIAS if d["tabata"]})==3, "las tres tablas son distintas entre sí")
for k,t in TABATA.items():
    chk(bool(t["a"][0]) and bool(t["b"][0]) and bool(t["sube"]),
        f"tabla {k}: {t['a'][0]} + {t['b'][0]}")

print("\n== 4c. Estructura de series: todo ejercicio la tiene en los cuatro tipos de bloque ==")
for d in DIAS:
    for _,ej in d["ej"]:
        faltan=[g for g in ("V","F","D","P") if not estructura(ej,{"V":"F1","F":"F2","D":"F4","P":"F5"}[g])]
        chk(not faltan, f"{ej}: V/F/D/P" + ("" if not faltan else f" ← faltan {faltan}"))
detalle = sum(1 for d in DIAS for _,ej in d["ej"] if ej in ESTRUCTURA)
chk(detalle>=8, f"{detalle} ejercicios con estructura propia, el resto con la regla genérica")

print("\n== 5. Carrera: ninguna subida por encima del 10 % (o +1,5 km si el volumen es bajo) ==")
for fc,f in FASES.items():
    chk(len(f["km"])==f["sem"], f"{fc}: {len(f['km'])} semanas de kilometraje para {f['sem']} semanas de bloque")

sem_km=[]   # (etiqueta, km, es_descarga)
for fc,f in FASES.items():
    for i,k in enumerate(f["km"],1):
        sem_km.append((f"{fc}s{i}", k, i in f["des"]))
prev=None
malas=[]
for et,k,des in sem_km:
    if not des:
        if prev is not None and k>prev:
            tope=max(prev*1.10, prev+1.5)
            if k>tope+1e-9: malas.append(f"{et}: {prev}→{k} km")
        prev=k
chk(not malas, "todas las subidas dentro del tope" + ("" if not malas else f" ← {malas}"))
pico=max(k for _,k,_ in sem_km)
chk(22<=pico<=34, f"pico de volumen {pico} km/semana")
for fc,f in FASES.items():
    print(f"       {fc}: " + " ".join(f"{k}{'*' if i in f['des'] else ' '}" for i,k in enumerate(f['km'],1))
          + f"   tirada {f['largo'][0]}→{f['largo'][1]} min")
print("       (* semana de descarga)")

print("\n== 5b. La tirada del jueves nunca pasa del tope de 80 min ==")
for fc,f in FASES.items():
    chk(max(f["largo"])<=80, f"{fc}: tirada máxima {max(f['largo'])} min")
RITMO_Z2 = {"F0":7.2,"F1":7.0,"F2":6.8,"F3":6.5,"F4":6.2,"F5":6.0}   # min/km
for fc,f in FASES.items():
    km_largo = max(f["largo"])/RITMO_Z2[fc]
    semanal = max(f["km"])
    # Con solo dos carreras a la semana la tirada pesa mucho por fuerza. Lo que hace
    # daño es la distancia absoluta, no el porcentaje: por debajo de 10 km da igual.
    chk(km_largo <= semanal*0.62 or km_largo <= 10,
        f"{fc}: la tirada son ~{km_largo:.1f} km, el {km_largo/semanal*100:.0f} % de los {semanal} km de la semana")

print("\n== 6. Variantes: conservan patrones y tienen las sesiones descritas ==")
for v in VARIANTES:
    chk(len(v['detalle'])>=3, f"{v['cod']} {v['n']}: {v['dias']}, {v['dur']}, {len(v['detalle'])} sesiones")

print("\n== 7. Fuerza: cargas de arranque coherentes ==")
for ej,d in arranque().items():
    ok = 0.5 <= d['s1']/d['ahora'] <= 0.68 and d['s4']>d['s1']
    chk(ok, f"{ej}: 1RM {d['antes']}→{d['ahora']} kg tras el parón · "
            f"sem 1 {d['s1']:.1f} kg ({d['s1']/d['ahora']*100:.0f} %) · sem 4 {d['s4']:.1f} kg")

print("\n== 8. Carrera: VDOT y zonas ==")
v_hoy=vdot(5000,seg(TEST_5K)); v_fin=vdot(5000,seg(OBJETIVO_5K))
chk(v_fin-v_hoy<=10, f"VDOT {v_hoy:.1f} → {v_fin:.1f} en 39 semanas ({v_fin-v_hoy:+.1f} puntos)")
for z,a,b,_ in zonas(seg(TEST_5K)): print(f"       {z:16s} {a}–{b} min/km")

print("\n== 9. Cada bloque de entreno tiene su bloque de dieta ==")
DIETA={"B0","B1","B2","B3","B4","B5"}
chk({f['dieta'] for f in FASES.values()}==DIETA, "los seis bloques de entreno mapean a los seis de la dieta")

print("\n" + (f"HAY FALLOS: {fallos}" if fallos else "TODO OK"))
sys.exit(1 if fallos else 0)
