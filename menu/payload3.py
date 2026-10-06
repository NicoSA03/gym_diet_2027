# -*- coding: utf-8 -*-
import sys, json, math; sys.path.insert(0,'menu')
from db import F, A, SECCION, macros
from calidad import calidad
from modelo import BLOQUES, FASES, TIPOS, ORDEN_TOMAS, escalar, dia_totales, normas
FACT=json.load(open('menu/factores.json'))
NORM=json.load(open('menu/normas.json'))

# ---- alimentos que necesita el navegador ----
# La pestaña Menús (v2.0) trabaja con TODOS los alimentos de datos/alimentos.csv,
# no solo con los de los platos: así puedes añadir cualquiera a una comida.
from db import ROL
from generar import racion
def nota(f):
    c = calidad(A[f])
    return [c["letra"], ". ".join(c["motivos"])] if c else ["", "Faltan datos de la etiqueta"]
# nombre -> [kcal, P, G, C (por 100 g), rol, nota, motivo, mín g, máx g]
FOODS={f:[F[f][0],F[f][1],F[f][2],F[f][3],ROL[f]]+nota(f)+list(racion(f)) for f in sorted(A)}

# Objetivo de cada toma (kcal, P, G, C) en cada bloque y tipo de día. Es la media de
# las opciones de esa toma ya escaladas: la misma cuenta que verifica ver_menu.py.
OBJ={}
for fcod in FASES:
    for tcod,(tn,td,mult,tomas) in TIPOS.items():
        fc,fg,fp = FACT[f"{fcod}|{tcod}"]
        d={}
        for b in tomas:
            ops=BLOQUES[b][3]; sN=normas(b,fc,fg,fp)
            ms=[macros(escalar(it,fc,fg,fp,sN[i])) for i,(_,it) in enumerate(ops)]
            d[b]=[round(sum(m[j] for m in ms)/len(ms),1) for j in range(4)]
        OBJ[f"{fcod}|{tcod}"]=d

# Platos: la comida y la cena comparten la misma lista (v2.0). Cada plato es una
# plantilla; la calculadora la ajusta a las kcal y la proteína de la toma.
PRINCIPALES=[{"n":on,"de":b,"it":[[f,g] for f,g in items]}
             for b in ("C","N") for on,items in BLOQUES[b][3]]

# Semanas de cada bloque de dieta, para saber cuál toca a partir de la fecha de
# inicio que guardas en el Registro.
from entreno import calendario
SEM={c["dieta"]:(c["s0"],c["s1"]) for c in calendario()}

PAY={
 "foods":FOODS,
 "bloques":{b:{"n":v[0],"hora":v[1],"nota":v[2],
               "ops":[{"n":on,"it":[[f,g] for f,g in items]} for on,items in v[3]]}
            for b,v in BLOQUES.items() if b not in ("C","N")},
 "principales":PRINCIPALES,
 "nombres":{b:BLOQUES[b][0] for b in BLOQUES},
 "horas":{b:BLOQUES[b][1] for b in BLOQUES},
 "orden":ORDEN_TOMAS,
 "fases":{k:{"n":v[0],"f":v[1],"obj":[v[2],v[3],v[4],v[5]],
           "s0":SEM[k][0],"s1":SEM[k][1]} for k,v in FASES.items()},
 "tipos":{k:{"n":v[0],"d":v[1],"mult":v[2],"tomas":v[3]} for k,v in TIPOS.items()},
 "obj":OBJ,
}
json.dump(PAY, open('menu/pay_menus.json','w'), ensure_ascii=False, separators=(',',':'))
print("menús:", len(open('menu/pay_menus.json',encoding='utf8').read())//1024, "KB")

# ---- lista de la compra: semana real (L=A, M=B, X=A, J=B, V=C, S=D, D=E) ----
SEMANA=[("Lunes","A",0),("Martes","B",1),("Miércoles","A",2),("Jueves","B",3),
        ("Viernes","C",4),("Sábado","D",5),("Domingo","E",6)]
ORDEN=["Frutería","Carnicería","Pescadería","Huevos y lácteos","Refrigerados","Congelados",
       "Conservas y despensa","Panadería"]

def cantidad(n,g):
    fmt=F[n][4]
    if n=="Huevos": return f"{round(g/60)} huevos"
    if "(bote)" in n:
        b=max(1,round(g/400)); return f"{b} bote{'s' if b>1 else ''} de 570 g"
    if n=="Bolsita de fruta":
        return f"{round(g/100)} bolsitas de 100 g"
    if n=="Gazpacho (brik)":
        return f"{g} ml, {g/1000:.1f} briks de 1 L".replace(".",",")
    if n=="Batido proteínas (botella)":
        return f"{round(g/330)} botellas"
    if n=="Verduras asadas (batch)": return f"{g} g de calabacín, pimiento y cebolla"
    base = f"{g/1000:.1f} kg".replace(".",",") if g>=1000 else f"{g} g"
    sem = fmt/g if g else 0
    if sem>=1.6: base += f", 1 envase de {fmt} g dura {round(sem)} sem"
    elif g>fmt:  base += f", {-(-g//fmt)} envases de {fmt} g"
    else:        base += f", 1 envase de {fmt} g"
    return base

COMPRA={}
for fcod in FASES:
    cons={}
    for dia,tcod,j in SEMANA:
        fc,fg,fp = FACT[f"{fcod}|{tcod}"]
        for b in TIPOS[tcod][3]:
            idx = j if b in ("C","N") else 0
            sN = normas(b, fc,fg,fp)[idx]
            for n,g in escalar(BLOQUES[b][3][idx][1], fc,fg,fp, sN):
                cons[n]=cons.get(n,0)+g
    secs={}
    coste=0
    for n,g in sorted(cons.items(), key=lambda x:-x[1]):
        g=round(g); eur=F[n][5]*g/F[n][4]; coste+=eur
        secs.setdefault(SECCION[n],[]).append(
            {"n":n,"g":g,"c":cantidad(n,g),"e":round(eur,2),"v":F[n][7]=="f",
             "q":nota(n)[0],"qm":nota(n)[1]})
    COMPRA[fcod]={"secs":[{"s":s,"items":secs[s]} for s in ORDEN if s in secs],
                  "total":round(coste,2),
                  "obj":FASES[fcod][2],"n":FASES[fcod][0],"f":FASES[fcod][1]}
json.dump(COMPRA, open('menu/pay_compra.json','w'), ensure_ascii=False, separators=(',',':'))
print("compra:", len(open('menu/pay_compra.json',encoding='utf8').read())//1024, "KB")
for k,v in COMPRA.items(): print(f"  {k}: {v['total']:.2f} €/semana, {sum(len(s['items']) for s in v['secs'])} productos")
