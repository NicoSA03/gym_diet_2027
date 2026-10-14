# -*- coding: utf-8 -*-
"""La base de ejercicios (v2.2). Los datos viven en datos/ejercicios.csv, que se edita
   con Excel o con el Bloc de notas. Este archivo solo los carga.

   Columnas (punto y coma como separador, | para separar varios valores):
     nombre        el nombre en español; en los del plan, igual que en menu/entreno.py
     grupo         Pierna, Pecho, Espalda, Hombro, Brazo, Core o Antebrazo
     musculos      los que más trabajan; secundarios, los que ayudan
     patron        Rodilla, Cadera, Empuje horizontal, Tirón vertical, Aislamiento...
     material      lo que hace falta
     series, reps  rango de referencia (en el plan mandan las del bloque)
     garmin        el ejercicio en tu reloj, como categoría/nombre del FIT SDK de Garmin
     gif           código de la animación en ExerciseDB (se ve en El entreno)
     uso           plan, sustituto (de uno del plan) o extra
     sustituye_a   en los sustitutos, a qué ejercicio del plan reemplaza
     notas

   De dónde sale: la lista oficial de Garmin (garmin-fit-sdk, 1.846 ejercicios),
   ExerciseDB (datos/exercises.sql, 1.324 ejercicios con animación) y los rangos de
   series de datos/Workout.csv.

   Lo que exporta:
     EJS[nombre] -> dict con todas las columnas (las de varios valores, como listas)
     GIF_URL     -> dirección de las animaciones; el código va detrás, con .gif
"""
import csv, os

CSV = os.path.join("datos", "ejercicios.csv")
COLUMNAS = ["nombre", "grupo", "musculos", "secundarios", "patron", "material", "series",
            "reps", "garmin", "gif", "uso", "sustituye_a", "notas"]
LISTAS = ("musculos", "secundarios")
USOS = ("plan", "sustituto", "extra")
GIF_URL = "https://static.exercisedb.dev/media/"


def carga(ruta=CSV):
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    if not filas:
        raise SystemExit(f"{ruta} está vacío")
    faltan = [c for c in COLUMNAS if c not in filas[0]]
    if faltan:
        raise SystemExit(f"A {ruta} le faltan las columnas: {', '.join(faltan)}")
    out = {}
    for i, r in enumerate(filas, start=2):
        r = {k: (v or "").strip() for k, v in r.items() if k}
        if not r["nombre"]:
            continue
        if r["nombre"] in out:
            raise SystemExit(f"{ruta}, línea {i}: «{r['nombre']}» está repetido")
        if r["uso"] not in USOS:
            raise SystemExit(f"{ruta}, línea {i}: el uso tiene que ser {', '.join(USOS)}")
        for k in LISTAS:
            r[k] = [x.strip() for x in r[k].split("|") if x.strip()]
        out[r["nombre"]] = r
    return out


EJS = carga() if os.path.exists(CSV) else {}
