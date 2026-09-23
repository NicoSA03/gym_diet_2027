# -*- coding: utf-8 -*-
"""Modelo único: bloques, platos, fases y tipos de día. Resuelve los factores
   por (fase × tipo de día) para que el navegador solo tenga que multiplicar."""
import sys, json, itertools
sys.path.insert(0,'menu')
from db import F, macros

# ---------- tomas ----------
# Snacks reducidos: solo cabe 1 bolsita de frutos secos y 1 potito en la mochila
BLOQUES = {
"P": ("Pre-entreno","06:30","En casa, 15 min antes de salir",[
  ("Plátano y batido",  [("Plátano",165),("Proteína en polvo",13)]),
  ("Avena líquida",     [("Leche semidesnatada",250),("Copos de avena Hacendado",22)]),
  ("De bolsillo",       [("Pan integral de molde",50),("Crema de cacahuete",9),("Proteína en polvo",10)]),
]),
"D": ("Desayuno post-entreno","08:45","En casa, al volver del entreno",[
  ("Avena completa",    [("Copos de avena Hacendado",165),("Leche semidesnatada",380),("Queso batido 0% / skyr",210),("Plátano",160),("Crema de cacahuete",16)]),
  ("Salado",            [("Huevos",180),("Pan integral de molde",165),("Yogur natural",250),("Plátano",165),("Crema de cacahuete",15),("Queso batido 0% / skyr",120)]),
  ("Batido con prisa",  [("Leche semidesnatada",480),("Copos de avena Hacendado",140),("Plátano",170),("Crema de cacahuete",22),("Proteína en polvo",28)]),
  ("Avena con kéfir",   [("Copos de avena Hacendado",165),("Leche semidesnatada",380),("Kéfir natural",210),("Plátano",160),("Proteína en polvo",20)]),
]),
"S1":("Frutos secos","17:00","1 bolsita, en la mochila",[
  ("Nueces",            [("Nueces",40)]),
  ("Almendras",         [("Almendras",40)]),
  ("Mezcla",            [("Nueces",20),("Almendras",20)]),
]),
"S2":("Potito de fruta","19:30","1 potito, en la mochila",[
  ("Bolsita de fruta",  [("Bolsita de fruta",100)]),
  ("Bolsita grande",    [("Bolsita de fruta",120)]),
  ("Plátano",           [("Plátano",95)]),
]),
"T": ("Kit de turno de bar","01:00","En la mochila del trabajo",[
  ("Frutos secos y batido",[("Nueces",32),("Plátano",130),("Proteína en polvo",20)]),
  ("Botella y almendras",[("Batido proteínas (botella)",330),("Almendras",28),("Bolsita de fruta",100)]),
  ("Mezcla",            [("Almendras",25),("Nueces",15),("Manzana",200),("Proteína en polvo",16)]),
]),
"T2":("Segunda parada del turno","21:00","Solo el sábado, turno de 9 h",[
  ("Frutos secos",      [("Nueces",30),("Bolsita de fruta",100)]),
  ("Botella",           [("Batido proteínas (botella)",330),("Almendras",20)]),
  ("Fruta y almendras", [("Almendras",30),("Manzana",200)]),
]),
"Z": ("Antes de dormir","04:15","Al llegar del turno",[
  ("Skyr",              [("Queso batido 0% / skyr",230),("Nueces",14)]),
  ("Leche",             [("Leche semidesnatada",300),("Proteína en polvo",19)]),
  ("Yogur",             [("Yogur natural",250),("Proteína en polvo",18)]),
]),
}

# ---------- los 7 platos de mediodía y las 7 cenas ----------
COMIDA = [
 ("Ñoquis con pollo", [("Ñoquis de patata",455),("Pechuga de pollo",185),("Verdura congelada",200),("Queso rallado (ingred.)",15),("Aceite de oliva virgen ex.",18)]),
 ("Lentejas con huevo", [("Lentejas cocidas (bote)",520),("Pan integral de molde",110),("Huevos",140),("Verdura congelada",150),("Aceite de oliva virgen ex.",22)]),
 ("Pasta con ternera", [("Pasta integral",220),("Ternera magra (babilla)",140),("Champiñón laminado",150),("Queso rallado (ingred.)",15),("Aceite de oliva virgen ex.",18)]),
 ("Batata con pollo", [("Batata",600),("Pan integral de molde",100),("Pechuga de pollo",210),("Guisantes congelados",120),("Aceite de oliva virgen ex.",15)]),
 ("Arroz con salmón", [("Arroz largo Hacendado",190),("Salmón fresco",200),("Verdura congelada",200),("Aceite de oliva virgen ex.",8)]),
 ("Patata con pollo", [("Patata",650),("Pan integral de molde",100),("Pechuga de pollo",210),("Verduras asadas (batch)",200),("Aceite de oliva virgen ex.",15)]),
 ("Garbanzos con atún", [("Garbanzos cocidos (bote)",480),("Pan integral de molde",90),("Atún claro al natural",110),("Verduras asadas (batch)",200),("Aceite de oliva virgen ex.",24)]),
]
CENA = [
 ("Gazpacho y pollo", [("Gazpacho (brik)",250),("Pechuga de pollo",150),("Pan integral de molde",85)]),
 ("Arroz con pollo", [("Arroz largo Hacendado",70),("Pechuga de pollo",150),("Verdura congelada",150)]),
 ("Atún y gazpacho", [("Gazpacho (brik)",250),("Atún claro al natural",145),("Pan integral de molde",85)]),
 ("Alubias con huevo", [("Alubias cocidas (bote)",240),("Huevos",130),("Verdura congelada",120)]),
 ("Ñoquis con pollo", [("Ñoquis de patata",170),("Pechuga de pollo",150),("Champiñón laminado",150)]),
 ("Patata y huevos", [("Patata",230),("Huevos",120),("Queso batido 0% / skyr",205)]),
 ("Merluza con batata", [("Batata",240),("Merluza congelada",210),("Guisantes congelados",150)]),
]
BLOQUES["C"] = ("Comida","14:00","En casa, el plato fuerte del día", COMIDA)
BLOQUES["N"] = ("Cena","22:00","En casa, la dejas hecha al mediodía", CENA)

ORDEN_TOMAS = ["P","D","C","S1","S2","N","T2","T","Z"]

FASES = {
 "B0": ("Rearranque",     "Sem 1–4 · 21 sep → 18 oct 2026",    3050,170,80,413),
 "B1": ("Construcción I", "Sem 5–12 · 19 oct → 13 dic 2026",   3400,175,85,484),
 "B2": ("Fuerza",         "Sem 13–17 · 14 dic → 17 ene 2027",  3450,178,90,482),
 "B3": ("Construcción II","Sem 18–23 · 18 ene → 28 feb 2027",  3600,185,92,508),
 "B4": ("Definición",     "Sem 24–35 · 1 mar → 23 may 2027",   2950,200,72,375),
 "B5": ("Pico",           "Sem 36–39 · 24 may → 20 jun 2027",  3050,190,76,401),
}
TIPOS = {
 "A": ("Fuerza + universidad por la tarde",  "Lunes y miércoles", 0.91, ["P","D","C","S1","S2","N"]),
 "B": ("Carrera + universidad desde 12:30",  "Martes y jueves",   1.00, ["P","D","C","S1","S2","N"]),
 "C": ("Entreno + universidad + turno",      "Viernes",           1.07, ["P","D","C","S1","S2","N","T"]),
 "D": ("Tirada larga + turno de 9 h",        "Sábado",            1.21, ["P","D","C","S1","S2","T2","T","Z"]),
 "E": ("Descanso total",                     "Domingo",           0.88, ["D","C","S1","S2","N"]),
}
DIAS_SEM = {"A":2,"B":2,"C":1,"D":1,"E":1}

def escalar(items, fc, fg, fp, s=1.0):
    out=[]
    for n,g in items:
        grp=F[n][6]
        f = fc if grp=="carb" else fg if grp=="grasa" else fp if grp=="prot" else 1.0
        out.append((n, max(5, round(g*f*s/5)*5)))
    return out

_NCACHE={}
def normas(b, fc, fg, fp):
    """Corrector por opción: todas las opciones de un bloque valen las mismas kcal.
       Así da igual cuál elija: el día siempre cuadra."""
    k=(b,round(fc,4),round(fg,4),round(fp,4))
    if k in _NCACHE: return _NCACHE[k]
    ks=[macros(escalar(it,fc,fg,fp))[0] for _,it in BLOQUES[b][3]]
    m=sum(ks)/len(ks)
    out=[round(m/x,4) if x else 1.0 for x in ks]
    _NCACHE[k]=out
    return out

def macros_bloque(b, idx, fc, fg, fp):
    s = normas(b, fc, fg, fp)[idx]
    return macros(escalar(BLOQUES[b][3][idx][1], fc, fg, fp, s))

def dia_totales(tomas, idx, fc, fg, fp):
    tot=[0.0]*4
    for b in tomas:
        for i,v in enumerate(macros_bloque(b, idx.get(b,0), fc, fg, fp)): tot[i]+=v
    return tot

def _error(tomas, tgt, fc, fg, fp):
    """Promedia los 7 platos de comida y las 7 cenas, cacheando lo que no cambia."""
    k,p,g,c = tgt
    fijo=[0.0]*4
    for b in tomas:
        if b in ("C","N"): continue
        for i,v in enumerate(macros_bloque(b,0,fc,fg,fp)): fijo[i]+=v
    var=[]
    for j in range(7):
        t=list(fijo)
        for b in tomas:
            if b in ("C","N"):
                for i,v in enumerate(macros_bloque(b,j,fc,fg,fp)): t[i]+=v
        var.append(t)
    e=0
    for t in var:
        e += ((t[0]-k)/k)**2*3 + ((t[1]-p)/p)**2*2 + ((t[2]-g)/g)**2 + ((t[3]-c)/c)**2
    return e/7

def resolver(tomas, tgt):
    """Malla gruesa y luego refinado alrededor del mejor punto."""
    best=None
    def barrer(rc, rg, rp):
        nonlocal best
        for fc in rc:
            for fg in rg:
                for fp in rp:
                    e=_error(tomas,tgt,fc,fg,fp)
                    if best is None or e<best[0]: best=(e,fc,fg,fp)
    lin=lambda a,b,n: [a+(b-a)*i/(n-1) for i in range(n)]
    barrer(lin(0.50,1.75,18), lin(0.30,1.50,17), lin(0.70,1.40,9))
    _,fc,fg,fp = best
    barrer(lin(max(0.40,fc-0.09), fc+0.09, 10),
           lin(max(0.25,fg-0.10), fg+0.10, 11),
           lin(max(0.65,fp-0.08), fp+0.08, 9))
    return best[1:]

if __name__=="__main__":
    FACT={}
    print(f"{'fase':5}{'tipo':5}{'fc':>6}{'fg':>6}{'fp':>6}  {'kcal':>6}{'P':>5}{'G':>5}{'C':>6}   objetivo   desvío")
    for fcod,(fn,ff,K,P,G,C) in FASES.items():
        for tcod,(tn,td,mult,tomas) in TIPOS.items():
            tgt=(K*mult, P*mult, G*mult, C*mult)
            fc,fg,fp = resolver(tomas,tgt)
            FACT[f"{fcod}|{tcod}"]=[round(fc,4),round(fg,4),round(fp,4)]
            ms=[sum(dia_totales(tomas,{"C":j,"N":j},fc,fg,fp)[i] for j in range(7))/7 for i in range(4)]
            print(f"{fcod:5}{tcod:5}{fc:6.2f}{fg:6.2f}{fp:6.2f}  {ms[0]:6.0f}{ms[1]:5.0f}{ms[2]:5.0f}{ms[3]:6.0f}   {tgt[0]:7.0f}   {(ms[0]-tgt[0])/tgt[0]*100:+5.1f} %")
    json.dump(FACT, open('menu/factores.json','w'))
    NORM={}
    for key,(fc,fg,fp) in FACT.items():
        NORM[key]={b: normas(b,fc,fg,fp) for b in BLOQUES}
    json.dump(NORM, open('menu/normas.json','w'))
    print("\nfactores guardados:", len(FACT), "· normas:", len(NORM))
