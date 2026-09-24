# -*- coding: utf-8 -*-
"""Los platos. Ya no viven dentro de modelo.py: están en datos/platos.csv, que se
   edita con el Bloc de notas o con Excel, igual que datos/alimentos.csv.

   Cada fila es un plato:

     toma      a qué toma del día pertenece (C = comida, N = cena, D = desayuno...)
     plato     el nombre que sale en la app
     alimentos los ingredientes, separados por barra vertical, tal cual se llaman
               en datos/alimentos.csv
     gramos    los gramos de cada uno, en el mismo orden y separados por barra
     notas     para ti; la app no los usa

   Los gramos son la RECETA BASE, no lo que vas a comer. La app los reescala
   según el bloque del macrociclo y el tipo de día, y además iguala todas las
   opciones de una misma toma para que dé igual cuál elijas. Por eso un plato
   nuevo tiene que salir más o menos con las mismas calorías base que sus
   compañeros de toma: ver_platos.py avisa si te desvías.

   El orden de las filas es el orden de los botones en la app. En la comida y la
   cena, las SIETE PRIMERAS son la semana por defecto (lunes a domingo) y son las
   que entran en la lista de la compra.
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import A

CSV = os.path.join("datos", "platos.csv")
COLUMNAS = ["toma", "plato", "alimentos", "gramos", "notas"]


def cargar(ruta=CSV):
    if not os.path.exists(ruta):
        sys.exit(f"No encuentro {ruta}. Ejecuta las órdenes desde la carpeta del proyecto.")
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    if not filas:
        sys.exit(f"{ruta} está vacío.")
    faltan = [c for c in COLUMNAS if c not in filas[0]]
    if faltan:
        sys.exit(f"A {ruta} le faltan columnas: {faltan}")

    out, vistos = {}, set()
    for i, fila in enumerate(filas, 2):                 # 2 = primera fila de datos
        toma = (fila["toma"] or "").strip()
        nom = (fila["plato"] or "").strip()
        if not toma and not nom:
            continue
        if not toma or not nom:
            sys.exit(f"{ruta}, línea {i}: hacen falta la toma y el nombre del plato.")
        if (toma, nom) in vistos:
            sys.exit(f"{ruta}, línea {i}: «{nom}» ya está en la toma {toma}.")
        vistos.add((toma, nom))

        nombres = [x.strip() for x in (fila["alimentos"] or "").split("|") if x.strip()]
        crudos = [x.strip().replace(",", ".") for x in (fila["gramos"] or "").split("|") if x.strip()]
        if not nombres:
            sys.exit(f"{ruta}, línea {i} ({nom}): no tiene ingredientes.")
        if len(nombres) != len(crudos):
            sys.exit(f"{ruta}, línea {i} ({nom}): {len(nombres)} ingredientes "
                     f"pero {len(crudos)} cantidades. Tienen que ir a la par.")
        items = []
        for al, g in zip(nombres, crudos):
            if al not in A:
                parecidos = [x for x in A if x.lower().startswith(al.lower()[:5])]
                pista = f" ¿Querías decir «{parecidos[0]}»?" if parecidos else ""
                sys.exit(f"{ruta}, línea {i} ({nom}): «{al}» no está en "
                         f"datos/alimentos.csv.{pista}")
            try:
                g = float(g)
            except ValueError:
                sys.exit(f"{ruta}, línea {i} ({nom}): «{g}» no es un número de gramos.")
            if g <= 0:
                sys.exit(f"{ruta}, línea {i} ({nom}): {al} tiene {g:g} g.")
            items.append((al, int(round(g))))
        out.setdefault(toma, []).append((nom, items))
    return out


def guardar(toma, nombre, items, notas="", ruta=CSV):
    """Añade un plato al final del CSV. Lo usa generar.py con --guardar."""
    with open(ruta, "a", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter=";", lineterminator="\n").writerow(
            [toma, nombre, "|".join(n for n, _ in items),
             "|".join(str(g) for _, g in items), notas])


PLATOS = cargar()

if __name__ == "__main__":
    from db import macros
    for toma, ops in PLATOS.items():
        ks = [macros(it)[0] for _, it in ops]
        print(f"{toma:3} {len(ops):2} platos · base media {sum(ks)/len(ks):6.0f} kcal")
    print(f"\n{sum(len(v) for v in PLATOS.values())} platos en {CSV}")
