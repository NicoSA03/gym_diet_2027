# -*- coding: utf-8 -*-
"""Modelo único: tomas, fases y tipos de día. Resuelve los factores por
   (fase × tipo de día) para que el navegador solo tenga que multiplicar.

   Los platos ya no están aquí: viven en datos/platos.csv y los carga platos.py.
   Aquí solo queda la ficha de cada toma (nombre, hora y dónde se come)."""
import sys, json, itertools
sys.path.insert(0,'menu')
from db import F, macros
from platos import PLATOS

# ---------- las tomas del día ----------
# Snacks reducidos: solo cabe 1 bolsita de frutos secos y 1 potito en la mochila
TOMAS = {
"P": ("Pre-entreno",             "06:30","En casa, 15 min antes de salir"),
"D": ("Desayuno post-entreno",   "08:45","En casa, al volver del entreno"),
"C": ("Comida",                  "14:00","En casa, el plato fuerte del día"),
"S1":("Frutos secos",            "17:00","1 bolsita, en la mochila"),
"S2":("Potito de fruta",         "19:30","1 potito, en la mochila"),
"N": ("Cena",                    "22:00","En casa, la dejas hecha al mediodía"),
"T2":("Segunda parada del turno","21:00","Solo el sábado, turno de 9 h"),
"T": ("Kit de turno de bar",     "01:00","En la mochila del trabajo"),
"Z": ("Antes de dormir",         "04:15","Al llegar del turno"),
}
ORDEN_TOMAS = ["P","D","C","S1","S2","N","T2","T","Z"]

_sobran = set(PLATOS) - set(TOMAS)
if _sobran:
    sys.exit(f"datos/platos.csv usa tomas que no existen: {sorted(_sobran)}. "
             f"Las válidas son {sorted(TOMAS)}.")
_vacias = [t for t in TOMAS if not PLATOS.get(t)]
if _vacias:
    sys.exit(f"Estas tomas se han quedado sin ningún plato en datos/platos.csv: {_vacias}")
for _t in ("C", "N"):
    if len(PLATOS[_t]) < 7:
        sys.exit(f"La toma {_t} necesita al menos 7 platos en datos/platos.csv "
                 f"(uno por día de la semana) y solo tiene {len(PLATOS[_t])}.")

BLOQUES = {t: (n, h, d, PLATOS[t]) for t, (n, h, d) in TOMAS.items()}
COMIDA = PLATOS["C"]     # se siguen usando por su nombre en las verificaciones
CENA = PLATOS["N"]
SEMANA_OPC = 7           # en la comida y la cena, los 7 primeros = lunes a domingo

FASES = {
 "B0": ("Rearranque",     "Sem 1–4",    3050,170,80,413),
 "B1": ("Construcción I", "Sem 5–12",   3400,175,85,484),
 "B2": ("Fuerza",         "Sem 13–17",  3450,178,90,482),
 "B3": ("Construcción II","Sem 18–23",  3600,185,92,508),
 "B4": ("Definición",     "Sem 24–35",   2950,200,72,375),
 "B5": ("Pico",           "Sem 36–39",  3050,190,76,401),
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
