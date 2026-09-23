# -*- coding: utf-8 -*-
import sys, json, itertools
sys.path.insert(0,'menu')
import modelo as M
from entreno import PESO

FACT=json.load(open('menu/factores.json'))
fallos=0

print("== 1. Dia por defecto de cada fase/tipo cae en objetivo ==")
for f,(fn,ff,K,P,G,C) in M.FASES.items():
    peor=0; peord=''
    for t,(tn,td,mult,tomas) in M.TIPOS.items():
        fc,fg,fp = FACT[f"{f}|{t}"]
        tgt=K*mult
        for j in range(7):
            k=M.dia_totales(tomas,{"C":j,"N":j},fc,fg,fp)[0]
            d=abs(k-tgt)/tgt*100
            if d>peor: peor, peord = d, f"{t}/opcion{j+1} {k:.0f} vs {tgt:.0f}"
    est = "OK " if peor<=5 else "FALLO"
    if peor>5: fallos+=1
    print(f"  {est} {f}: desviacion diaria max {peor:.1f} %  ({peord})")

print("\n== 2. CUALQUIER combinacion de opciones sigue en rango ==")
for f,(fn,ff,K,P,G,C) in M.FASES.items():
    for t,(tn,td,mult,tomas) in M.TIPOS.items():
        fc,fg,fp = FACT[f"{f}|{t}"]
        tgt=K*mult
        lo=1e9; hi=0
        keys=list(tomas)
        rangos=[range(len(M.BLOQUES[b][3])) if b in M.BLOQUES else range(7) for b in keys]
        for combo in itertools.product(*rangos):
            sel=dict(zip(keys,combo))
            k=M.dia_totales(tomas,sel,fc,fg,fp)[0]
            lo=min(lo,k); hi=max(hi,k)
        pl=(lo-tgt)/tgt*100; ph=(hi-tgt)/tgt*100
        est="OK " if (pl>=-12 and ph<=12) else "FALLO"
        if est=="FALLO": fallos+=1
        print(f"  {est} {f}/{t}: {lo:.0f}-{hi:.0f} sobre {tgt:.0f} ({pl:+.0f} % a {ph:+.0f} %)")

print("\n== 3. Media semanal ponderada = objetivo de la fase ==")
for f,(fn,ff,K,P,G,C) in M.FASES.items():
    dias=[("A",2),("B",2),("C",1),("D",1),("E",1)]
    tot=0
    for t,n in dias:
        fc,fg,fp=FACT[f"{f}|{t}"]
        tomas=M.TIPOS[t][3]
        med=sum(M.dia_totales(tomas,{"C":j,"N":j},fc,fg,fp)[0] for j in range(7))/7
        tot+=med*n
    med=tot/7
    d=(med-K)/K*100
    est="OK " if abs(d)<=3 else "FALLO"
    if est=="FALLO": fallos+=1
    print(f"  {est} {f}: media semanal {med:.0f} vs objetivo {K} ({d:+.1f} %)")

print(f"\n== 4. Proteina minima 1.8 g/kg ({PESO} kg) ==")
for f,(fn,ff,K,P,G,C) in M.FASES.items():
    fc,fg,fp=FACT[f"{f}|B"]
    p=sum(M.dia_totales(M.TIPOS["B"][3],{"C":j,"N":j},fc,fg,fp)[1] for j in range(7))/7
    gkg=p/PESO
    est="OK " if gkg>=1.8 else "FALLO"
    if est=="FALLO": fallos+=1
    print(f"  {est} {f}: {gkg:.2f} g/kg")

print("\n== 5. Porciones plausibles (ningun alimento fuera de rango) ==")
LIM={"Pechuga de pollo":320,"Salmón fresco":300,"Ternera magra (babilla)":280,
     "Atún claro al natural":200,"Merluza":320,"Huevos":220,
     "Aceite de oliva virgen ex.":35,"Crema de cacahuete":45,
     "Lentejas cocidas (bote)":850,"Garbanzos cocidos (bote)":850,"Alubias cocidas (bote)":600,
     "Patata":1200,"Batata":1100}
peores={}
for f in M.FASES:
    for t in M.TIPOS:
        fc,fg,fp=FACT[f"{f}|{t}"]
        for b in M.TIPOS[t][3]:
            opts = M.BLOQUES[b][3] if b in M.BLOQUES else (M.COMIDA if b=="C" else M.CENA)
            for nom,items in opts:
                for food,base in items:
                    g=M.escalar([(food,base)],fc,fg,fp)[0][1]
                    if food in LIM and g>LIM[food]:
                        if g>peores.get(food,(0,))[0]: peores[food]=(g,f,t,nom)
if not peores: print("  OK  todas las porciones dentro de limites")
for food,(g,f,t,nom) in peores.items():
    fallos+=1; print(f"  FALLO {food}: {g} g en {f}/{t} ({nom}) > {LIM[food]} g")

print("\n" + ("HAY FALLOS: %d" % fallos if fallos else "TODO OK"))
sys.exit(1 if fallos else 0)
