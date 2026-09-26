# -*- coding: utf-8 -*-
"""Los alimentos. Los datos ya no viven aquí: están en datos/alimentos.csv, que se
   edita con Excel o con el Bloc de notas. Este archivo solo los carga y los deja
   listos para el resto del sistema.

   El CSV usa punto y coma como separador y punto decimal (3.5). Si Excel lo
   guarda con coma decimal (3,5) también se entiende. Las casillas vacías
   significan «todavía no lo he copiado de la etiqueta», no cero.

   Lo que exporta:
     F[nombre]   -> (kcal, proteína, grasa, carbohidrato, formato_g, precio, grupo, fuente)
     A[nombre]   -> todos los campos, incluidos azúcares, fibra, sal, saturadas, NOVA y rol
     SECCION[n]  -> pasillo del supermercado
     ROL[n]      -> papel en un plato: base, proteina, verdura, grasa, fruta o lacteo
     macros(items), calidad(a)
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calidad import calidad

CSV = os.path.join("datos", "alimentos.csv")
COLUMNAS = ["nombre", "kcal", "grasa", "saturadas", "carbohidrato", "azucares", "fibra",
            "proteina", "sal", "formato_g", "precio_eur", "grupo", "seccion", "nova",
            "fuente", "notas"]
GRUPOS = ("carb", "grasa", "prot", "fijo")      # carb/grasa/prot escalan; fijo no
ROLES = ("base", "proteina", "verdura", "grasa", "fruta", "lacteo")
# Si la columna «rol» está vacía se deduce del grupo. Es solo un apaño para que un
# alimento recién añadido no rompa nada: lo suyo es escribir el rol a mano.
ROL_POR_GRUPO = {"carb": "base", "prot": "proteina", "grasa": "grasa", "fijo": "verdura"}


def _num(x):
    """'3,5' -> 3.5 · vacío -> None (dato que falta, no cero)."""
    x = (x or "").strip().replace(",", ".")
    return float(x) if x else None


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
    out = {}
    for i, fila in enumerate(filas, 2):                 # 2 = primera fila de datos
        n = (fila["nombre"] or "").strip()
        if not n:
            continue
        if n in out:
            sys.exit(f"{ruta}, línea {i}: «{n}» está repetido.")
        a = {"nombre": n, "linea": i,
             "grupo": (fila["grupo"] or "").strip(),
             "seccion": (fila["seccion"] or "").strip(),
             "fuente": (fila["fuente"] or "e").strip() or "e",
             "notas": (fila["notas"] or "").strip()}
        for c in ("kcal", "proteina", "grasa", "carbohidrato", "azucares", "fibra",
                  "sal", "saturadas", "formato_g", "precio_eur", "nova"):
            a[c] = _num(fila[c])
        for c in ("kcal", "proteina", "grasa", "carbohidrato", "formato_g", "precio_eur"):
            if a[c] is None:
                sys.exit(f"{ruta}, línea {i} ({n}): falta «{c}», que es obligatorio.")
        if a["grupo"] not in GRUPOS:
            sys.exit(f"{ruta}, línea {i} ({n}): grupo «{a['grupo']}» no vale. Usa {GRUPOS}.")
        a["rol"] = (fila.get("rol") or "").strip() or ROL_POR_GRUPO[a["grupo"]]
        if a["rol"] not in ROLES:
            sys.exit(f"{ruta}, línea {i} ({n}): rol «{a['rol']}» no vale. Usa {ROLES}.")
        if not a["seccion"]:
            sys.exit(f"{ruta}, línea {i} ({n}): falta el pasillo del súper.")
        out[n] = a
    return out


A = cargar()
F = {n: (a["kcal"], a["proteina"], a["grasa"], a["carbohidrato"],
         a["formato_g"], a["precio_eur"], a["grupo"], a["fuente"]) for n, a in A.items()}
SECCION = {n: a["seccion"] for n, a in A.items()}
ROL = {n: a["rol"] for n, a in A.items()}


def macros(items):
    t = [0.0] * 4
    for n, g in items:
        k, p, gr, c = F[n][:4]
        t[0] += k * g / 100; t[1] += p * g / 100; t[2] += gr * g / 100; t[3] += c * g / 100
    return tuple(round(x, 1) for x in t)


if __name__ == "__main__":
    print(f"{len(A)} alimentos en {CSV}")
    sin = [n for n, a in A.items() if calidad(a) is None]
    print(f"con nota de calidad: {len(A)-len(sin)} · sin datos de etiqueta: {len(sin)}")
