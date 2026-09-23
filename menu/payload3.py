# -*- coding: utf-8 -*-
import sys, json, math; sys.path.insert(0,'menu')
from db import F, macros
from modelo import BLOQUES, FASES, TIPOS, ORDEN_TOMAS, escalar, dia_totales, normas
FACT=json.load(open('menu/factores.json'))
NORM=json.load(open('menu/normas.json'))

# ---- alimentos que necesita el navegador ----
usados=set()
for b,(n,h,nota,ops) in BLOQUES.items():
    for _,items in ops:
        for f,_ in items: usados.add(f)
FOODS={f:[F[f][0],F[f][1],F[f][2],F[f][3],F[f][6]] for f in sorted(usados)}

PAY={
 "foods":FOODS,
 "bloques":{b:{"n":v[0],"hora":v[1],"nota":v[2],
               "ops":[{"n":on,"it":[[f,g] for f,g in items]} for on,items in v[3]]}
            for b,v in BLOQUES.items()},
 "orden":ORDEN_TOMAS,
 "fases":{k:{"n":v[0],"f":v[1],"obj":[v[2],v[3],v[4],v[5]]} for k,v in FASES.items()},
 "tipos":{k:{"n":v[0],"d":v[1],"mult":v[2],"tomas":v[3]} for k,v in TIPOS.items()},
 "fact":FACT,
 "norm":NORM,
}
json.dump(PAY, open('menu/pay_menus.json','w'), ensure_ascii=False, separators=(',',':'))
print("menús:", len(open('menu/pay_menus.json',encoding='utf8').read())//1024, "KB")

# ---- lista de la compra: semana real (L=A, M=B, X=A, J=B, V=C, S=D, D=E) ----
SEMANA=[("Lunes","A",0),("Martes","B",1),("Miércoles","A",2),("Jueves","B",3),
        ("Viernes","C",4),("Sábado","D",5),("Domingo","E",6)]
SECCION={
 "Kéfir natural":"Huevos y lácteos",
 "Pechuga de pollo":"Carnicería","Ternera magra (babilla)":"Carnicería",
 "Huevos":"Huevos y lácteos","Leche semidesnatada":"Huevos y lácteos",
 "Queso batido 0% / skyr":"Huevos y lácteos","Yogur natural":"Huevos y lácteos",
 "Queso rallado (ingred.)":"Huevos y lácteos","Batido proteínas (botella)":"Huevos y lácteos",
 "Salmón fresco":"Pescadería",
 "Merluza congelada":"Congelados","Verdura congelada":"Congelados","Guisantes congelados":"Congelados",
 "Atún claro al natural":"Conservas y despensa","Gazpacho (brik)":"Conservas y despensa",
 "Lentejas cocidas (bote)":"Conservas y despensa","Garbanzos cocidos (bote)":"Conservas y despensa",
 "Alubias cocidas (bote)":"Conservas y despensa","Copos de avena Hacendado":"Conservas y despensa",
 "Arroz largo Hacendado":"Conservas y despensa","Pasta integral":"Conservas y despensa",
 "Aceite de oliva virgen ex.":"Conservas y despensa","Crema de cacahuete":"Conservas y despensa",
 "Nueces":"Conservas y despensa","Almendras":"Conservas y despensa",
 "Proteína en polvo":"Conservas y despensa","Bolsita de fruta":"Conservas y despensa",
 "Pan integral de molde":"Panadería","Ñoquis de patata":"Refrigerados",
 "Plátano":"Frutería","Manzana":"Frutería","Patata":"Frutería","Batata":"Frutería",
 "Champiñón laminado":"Frutería","Verduras asadas (batch)":"Frutería",
}
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
        return f"{g} ml · {g/1000:.1f} briks de 1 L".replace(".",",")
    if n=="Batido proteínas (botella)":
        return f"{round(g/330)} botellas"
    if n=="Verduras asadas (batch)": return f"{g} g de calabacín, pimiento y cebolla"
    base = f"{g/1000:.1f} kg".replace(".",",") if g>=1000 else f"{g} g"
    sem = fmt/g if g else 0
    if sem>=1.6: base += f" · 1 envase de {fmt} g dura {round(sem)} sem"
    elif g>fmt:  base += f" · {-(-g//fmt)} envases de {fmt} g"
    else:        base += f" · 1 envase de {fmt} g"
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
            {"n":n,"g":g,"c":cantidad(n,g),"e":round(eur,2),"v":F[n][7]=="f"})
    COMPRA[fcod]={"secs":[{"s":s,"items":secs[s]} for s in ORDEN if s in secs],
                  "total":round(coste,2),
                  "obj":FASES[fcod][2],"n":FASES[fcod][0],"f":FASES[fcod][1]}
json.dump(COMPRA, open('menu/pay_compra.json','w'), ensure_ascii=False, separators=(',',':'))
print("compra:", len(open('menu/pay_compra.json',encoding='utf8').read())//1024, "KB")
for k,v in COMPRA.items(): print(f"  {k}: {v['total']:.2f} €/semana, {sum(len(s['items']) for s in v['secs'])} productos")
