#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventa platos con los alimentos de datos/alimentos.csv y calcula los gramos
   exactos para las calorías que le pidas. No necesita internet ni Claude.

Ejemplos:

    python3 menu/generar.py comida
        Propone comidas nuevas con las mismas calorías base que las que ya tienes,
        listas para entrar en la app.

    python3 menu/generar.py cena --kcal 700 --proteina 55
        Una cena suelta de 700 kcal y 55 g de proteína, para hoy.

    python3 menu/generar.py comida --sin "Salmón fresco" --con Patata --nota B --n 8
        Ocho propuestas sin salmón, con patata sí o sí, y de calidad B o mejor.

    python3 menu/generar.py comida --guardar 3 --nombre "Patata con pavo"
        Guarda la propuesta número 3 en datos/platos.csv. Después:
        python3 actualizar.py --recalcular

Cómo funciona, en una frase: monta combinaciones de alimentos que tengan sentido
(una base, una proteína, una verdura, una grasa), resuelve por mínimos cuadrados
los gramos que clavan tus objetivos, descarta las raciones absurdas y te enseña
las mejores por calidad y precio. La aritmética es exacta y siempre da lo mismo.
"""
import argparse, itertools, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import A, F, ROL, macros
from calidad import calidad
from platos import PLATOS, guardar

# ─────────────────────────────────────────────────────────────────────────────
# Lo que puedes tocar sin miedo: las reglas de cocina.
# ─────────────────────────────────────────────────────────────────────────────

# Cómo se llama cada toma cuando la escribes en la orden.
ALIAS = {"comida": "C", "cena": "N", "desayuno": "D", "pre": "P", "preentreno": "P",
         "frutossecos": "S1", "snack": "S1", "potito": "S2", "fruta": "S2",
         "turno": "T", "turno2": "T2", "noche": "Z", "dormir": "Z"}

# De qué piezas se compone un plato de cada toma. Cada tupla es un molde distinto.
PATRONES = {
    "C":  [("base", "proteina", "verdura", "grasa"),
           ("base", "pan", "proteina", "verdura", "grasa")],
    "N":  [("base", "proteina", "verdura"),
           ("base", "proteina", "verdura", "grasa")],
    "D":  [("base", "lacteo", "proteina", "fruta", "grasa")],
    "P":  [("fruta", "proteina"), ("base", "lacteo"), ("pan", "grasa", "proteina")],
    "S1": [("grasa",), ("grasa", "grasa")],
    "S2": [("fruta",)],
    "T":  [("grasa", "fruta", "proteina")],
    "T2": [("grasa", "fruta")],
    "Z":  [("lacteo", "grasa"), ("lacteo", "proteina")],
}
PAN = ["Pan integral de molde"]          # la guarnición que acompaña, no la base

# Parejas que no pegan en el mismo plato. Añade las tuyas.
NO_JUNTOS = [
    {"Gazpacho (brik)", "Pasta integral"},
    {"Gazpacho (brik)", "Arroz largo Hacendado"},
    {"Gazpacho (brik)", "Ñoquis de patata"},
    {"Gazpacho (brik)", "Copos de avena Hacendado"},
    {"Gazpacho (brik)", "Queso rallado (ingred.)"},
    {"Salmón fresco", "Queso rallado (ingred.)"},
    {"Atún claro al natural", "Queso rallado (ingred.)"},
    {"Merluza congelada", "Queso rallado (ingred.)"},
    {"Tomate cherry", "Copos de avena Hacendado"},
    {"Crema de cacahuete", "Pechuga de pollo"},
    {"Crema de cacahuete", "Ternera magra (babilla)"},
    {"Crema de cacahuete", "Salmón fresco"},
    {"Crema de cacahuete", "Merluza congelada"},
    {"Crema de cacahuete", "Atún claro al natural"},
    {"Aguacate", "Copos de avena Hacendado"},
]

# Alimentos que no quieres que entren en platos nuevos de ninguna toma.
NUNCA = {"Batido proteínas (botella)", "Verduras asadas (batch)"}

# Un plato de mediodía o de cena no se hace con avena, batido ni fruta, por mucho
# que los números cuadren. Y un desayuno no se hace con lentejas.
NO_DE_PLATO = {"Copos de avena Hacendado", "Proteína en polvo", "Crema de cacahuete",
               "Leche semidesnatada", "Yogur natural", "Kéfir natural",
               "Plátano", "Manzana", "Bolsita de fruta", "Nueces", "Almendras"}
NO_DE_DESAYUNO = {"Lentejas cocidas (bote)", "Garbanzos cocidos (bote)",
                  "Alubias cocidas (bote)", "Gazpacho (brik)", "Champiñón laminado",
                  "Verdura congelada", "Guisantes congelados", "Tomate cherry",
                  "Ternera magra (babilla)", "Merluza congelada", "Salmón fresco",
                  "Atún claro al natural", "Pechuga de pollo", "Filete de pavo",
                  "Patata", "Ñoquis de patata", "Pasta integral", "Arroz largo Hacendado",
                  "Aceite de oliva virgen ex.", "Queso rallado (ingred.)"}
NO_EN = {"C": NO_DE_PLATO, "N": NO_DE_PLATO, "D": NO_DE_DESAYUNO}

# Ración razonable de cada alimento, en gramos. Lo que no esté aquí se deduce de
# su papel y de lo que concentra (más abajo, en racion()).
#
# Ojo con los máximos: estos gramos son la receta BASE. La app los multiplica
# después por el factor del bloque, que llega a 1,50 en el carbohidrato y a 1,44
# en la proteína. Los topes de aquí ya dejan ese margen para que ninguna ración
# acabe siendo absurda en el bloque más cargado (lo comprueba ver_menu.py).
RACION = {
    "Pechuga de pollo": (110, 215), "Filete de pavo": (110, 215),
    "Ternera magra (babilla)": (100, 190), "Pavo en lonchas": (60, 130),
    "Salmón fresco": (110, 200), "Merluza congelada": (120, 215),
    "Atún claro al natural": (80, 135), "Huevos": (60, 200),
    "Proteína en polvo": (10, 35), "Queso batido 0% / skyr": (120, 300),
    "Patata": (150, 700), "Batata": (150, 650), "Ñoquis de patata": (150, 500),
    "Lentejas cocidas (bote)": (200, 560), "Garbanzos cocidos (bote)": (200, 560),
    "Alubias cocidas (bote)": (200, 395), "Pan integral de molde": (30, 170),
    "Arroz largo Hacendado": (50, 220), "Pasta integral": (50, 220),
    "Copos de avena Hacendado": (40, 200),
    "Aceite de oliva virgen ex.": (5, 28), "Queso rallado (ingred.)": (8, 35),
    "Crema de cacahuete": (8, 35), "Nueces": (15, 50), "Almendras": (15, 50),
    "Aguacate": (50, 150),
    "Gazpacho (brik)": (150, 300), "Champiñón laminado": (100, 250),
    "Verdura congelada": (100, 250), "Guisantes congelados": (100, 220),
    "Tomate cherry": (80, 200),
    "Plátano": (90, 220), "Manzana": (100, 250), "Bolsita de fruta": (100, 200),
    "Leche semidesnatada": (150, 450), "Yogur natural": (125, 375),
    "Kéfir natural": (125, 375),
    "Batido proteínas (botella)": (330, 330),    # formato cerrado: una botella
}
POR_ROL = {"base": (60, 300), "proteina": (100, 250), "verdura": (100, 250),
           "grasa": (10, 40), "fruta": (90, 220), "lacteo": (125, 400)}

# Nombre corto para bautizar el plato.
CORTO = {"Pechuga de pollo": "pollo", "Filete de pavo": "pavo", "Pavo en lonchas": "pavo",
         "Ternera magra (babilla)": "ternera", "Salmón fresco": "salmón",
         "Merluza congelada": "merluza", "Atún claro al natural": "atún", "Huevos": "huevo",
         "Proteína en polvo": "batido", "Queso batido 0% / skyr": "skyr",
         "Arroz largo Hacendado": "arroz", "Pasta integral": "pasta",
         "Copos de avena Hacendado": "avena", "Ñoquis de patata": "ñoquis",
         "Lentejas cocidas (bote)": "lentejas", "Garbanzos cocidos (bote)": "garbanzos",
         "Alubias cocidas (bote)": "alubias", "Pan integral de molde": "pan",
         "Leche semidesnatada": "leche", "Yogur natural": "yogur", "Kéfir natural": "kéfir",
         "Gazpacho (brik)": "gazpacho", "Champiñón laminado": "champiñón",
         "Verdura congelada": "verdura", "Guisantes congelados": "guisantes",
         "Tomate cherry": "tomate", "Bolsita de fruta": "fruta",
         "Aceite de oliva virgen ex.": "aceite", "Queso rallado (ingred.)": "queso",
         "Crema de cacahuete": "cacahuete"}

PESOS = (3.0, 2.0, 1.0, 1.0)       # kcal, proteína, grasa, carbohidrato
LETRAS = {"A": 85, "B": 70, "C": 50, "D": 0}

# ─────────────────────────────────────────────────────────────────────────────
# De aquí para abajo, la maquinaria.
# ─────────────────────────────────────────────────────────────────────────────


def racion(n):
    if n in RACION:
        return RACION[n]
    r, k = ROL[n], A[n]["kcal"]
    if r == "base":
        return (40, 230) if k >= 300 else (100, 500) if k >= 140 else (150, 700)
    if r == "grasa":
        return (5, 30) if k >= 800 else (10, 50) if k >= 450 else (40, 150)
    if r == "proteina" and k >= 300:
        return (10, 35)
    return POR_ROL[r]


def objetivo_de_toma(t):
    """Las calorías y macros medias de los platos que ya hay en esa toma."""
    ms = [macros(it) for _, it in PLATOS[t]]
    return tuple(sum(m[i] for m in ms) / len(ms) for i in range(4))


def ajustar(nombres, obj, vueltas=40):
    """Gramos que mejor clavan el objetivo. Descenso por coordenadas sobre una
       parábola: en cada paso el óptimo de un ingrediente tiene fórmula cerrada,
       así que converge en un suspiro y siempre al mismo sitio."""
    m = [[F[n][j] / 100.0 for j in range(4)] for n in nombres]   # macros por gramo
    lim = [racion(n) for n in nombres]
    g = [(a + b) / 2 for a, b in lim]
    for _ in range(vueltas):
        for i in range(len(nombres)):
            num = den = 0.0
            for j in range(4):
                if not obj[j]:
                    continue
                resto = sum(m[k][j] * g[k] for k in range(len(nombres)) if k != i)
                w = PESOS[j] / obj[j] ** 2
                num += w * m[i][j] * (obj[j] - resto)
                den += w * m[i][j] ** 2
            if den:
                g[i] = min(lim[i][1], max(lim[i][0], num / den))
    # Se redondea a múltiplos de 5 g, pero sin salirse de la ración razonable:
    # 28 g de aceite no pueden convertirse en 30 al redondear.
    out = []
    for n, x, (lo, hi) in zip(nombres, g, lim):
        r = int(round(x / 5)) * 5
        if r > hi:
            r = int(hi / 5) * 5
        if r < lo:
            r = -(-int(lo) // 5) * 5
        out.append((n, max(5, r)))
    return out


def error(items, obj):
    m = macros(items)
    return sum(PESOS[j] * ((m[j] - obj[j]) / obj[j]) ** 2 for j in range(4) if obj[j])


def precio(items):
    return sum(F[n][5] * g / F[n][4] for n, g in items)


def nota(items):
    """Nota del plato: media de las notas de sus ingredientes, ponderada por las
       calorías que aporta cada uno. Devuelve (letra, puntos, % valorado)."""
    tot = con = 0.0
    suma = 0.0
    for n, g in items:
        k = F[n][0] * g / 100
        tot += k
        c = calidad(A[n])
        if c:
            con += k
            suma += c["puntos"] * k
    if not con or not tot:
        return ("—", 0, 0)
    p = suma / con
    letra = next(l for l, corte in LETRAS.items() if p >= corte)
    return (letra, round(p), round(con / tot * 100))


def combina(t, filtro_sin, filtro_con):
    """Todas las combinaciones de alimentos con sentido para esa toma."""
    veto = NUNCA | set(filtro_sin) | NO_EN.get(t, set())
    veto -= set(filtro_con)                      # lo que pidas expresamente, manda
    por_rol = {}
    for n in A:
        if n in veto:
            continue
        por_rol.setdefault(ROL[n], []).append(n)
    for v in por_rol.values():
        v.sort()
    por_rol["pan"] = [n for n in PAN if n not in filtro_sin]

    yanoestan = {frozenset(n for n, _ in it) for _, it in PLATOS[t]}
    vistos = set()
    for patron in PATRONES[t]:
        grupos, orden = {}, []
        for r in patron:
            if r not in grupos:
                grupos[r] = 0
                orden.append(r)
            grupos[r] += 1
        opciones = []
        for r in orden:
            cand = por_rol.get(r, [])
            if len(cand) < grupos[r]:
                opciones = None
                break
            opciones.append(list(itertools.combinations(cand, grupos[r])))
        if opciones is None:
            continue
        for trozos in itertools.product(*opciones):
            nombres = [n for t_ in trozos for n in t_]
            clave = frozenset(nombres)
            if len(clave) != len(nombres) or clave in vistos or clave in yanoestan:
                continue
            if any(p <= clave for p in NO_JUNTOS):
                continue
            if not all(c in clave for c in filtro_con):
                continue
            vistos.add(clave)
            yield nombres


def nombrar(items):
    cortos = [CORTO.get(n, n.split()[0].lower()) for n, _ in items
              if ROL[n] in ("base", "proteina") and n not in PAN]
    if len(cortos) >= 2:
        return f"{cortos[0].capitalize()} con {cortos[1]}"
    return (cortos[0] if cortos else CORTO.get(items[0][0], items[0][0])).capitalize()


def main():
    ap = argparse.ArgumentParser(
        description="Inventa platos con los alimentos que tienes y calcula los gramos.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("toma", help="comida, cena, desayuno, pre, snack, potito, turno, noche")
    ap.add_argument("--kcal", type=float, help="calorías del plato (por defecto, las de esa toma)")
    ap.add_argument("--proteina", type=float, help="gramos de proteína")
    ap.add_argument("--grasa", type=float, help="gramos de grasa")
    ap.add_argument("--carbohidrato", type=float, help="gramos de carbohidrato")
    ap.add_argument("--n", type=int, default=5, help="cuántas propuestas enseñar (5)")
    ap.add_argument("--sin", default="", help="alimentos a excluir, separados por coma")
    ap.add_argument("--con", default="", help="alimentos obligatorios, separados por coma")
    ap.add_argument("--nota", choices=list(LETRAS), help="calidad mínima del plato")
    ap.add_argument("--guardar", type=int, metavar="N",
                    help="guarda la propuesta N en datos/platos.csv")
    ap.add_argument("--nombre", help="nombre del plato al guardarlo")
    a = ap.parse_args()

    clave = a.toma.strip().lower().replace(" ", "").replace("-", "")
    t = ALIAS.get(clave, a.toma.strip().upper())
    if t not in PATRONES:
        sys.exit(f"No sé qué es «{a.toma}». Usa: {', '.join(sorted(ALIAS))}.")

    def resolver_nombres(txt):
        fuera = []
        for x in txt.split(","):
            x = x.strip()
            if not x:
                continue
            if x in A:
                fuera.append(x)
            else:
                iguales = [n for n in A if x.lower() in n.lower()]
                if len(iguales) != 1:
                    sys.exit(f"«{x}» no es un alimento claro. "
                             f"{'Puede ser: ' + ', '.join(iguales) if iguales else 'No está en datos/alimentos.csv.'}")
                fuera.append(iguales[0])
        return fuera

    sin, con = set(resolver_nombres(a.sin)), resolver_nombres(a.con)

    base = objetivo_de_toma(t)
    obj = (a.kcal if a.kcal else base[0],
           a.proteina if a.proteina is not None else (base[1] * a.kcal / base[0] if a.kcal else base[1]),
           a.grasa, a.carbohidrato)
    obj = (obj[0], obj[1],
           a.grasa if a.grasa is not None else (base[2] * obj[0] / base[0]),
           a.carbohidrato if a.carbohidrato is not None else (base[3] * obj[0] / base[0]))

    print(f"Toma «{t}» · objetivo {obj[0]:.0f} kcal · {obj[1]:.0f} g P · "
          f"{obj[2]:.0f} g G · {obj[3]:.0f} g C")
    if not a.kcal:
        print(f"(son las calorías base medias de los {len(PLATOS[t])} platos que ya tienes "
              f"en esa toma, que es lo que hace falta para que encaje en la app)")

    yausados = {n for _, it in PLATOS[t] for n, _ in it}
    props = []
    for nombres in combina(t, sin, con):
        items = ajustar(nombres, obj)
        d = (macros(items)[0] - obj[0]) / obj[0]
        if abs(d) > 0.04:
            continue                                  # no llega a las calorías pedidas
        letra, pts, cobertura = nota(items)
        if a.nota and (letra == "—" or LETRAS[letra] < LETRAS[a.nota]):
            continue
        pr = precio(items)
        nuevos = sum(1 for n, _ in items if n not in yausados)
        props.append({"items": items, "err": error(items, obj), "letra": letra,
                      "pts": pts, "cob": cobertura, "eur": pr, "nombre": nombrar(items),
                      # calidad, menos lo que no sabemos, menos lo que cuesta,
                      # menos lo que se desvía, más un empujón a lo que no repites
                      "score": pts - 0.15 * (100 - cobertura) - 4 * pr
                               - 300 * error(items, obj) + 3 * min(nuevos, 2)})
    props.sort(key=lambda p: (-p["score"], p["eur"]))

    # Un solo representante por nombre: el mejor. Si no, salen cinco variantes
    # del mismo plato con la verdura cambiada.
    mejor, unicos = set(), []
    for p in props:
        if p["nombre"] in mejor:
            continue
        mejor.add(p["nombre"])
        unicos.append(p)
    props = unicos

    if not props:
        sys.exit("\nNo sale ningún plato con esas condiciones. Prueba a quitar algún "
                 "filtro, a bajar --nota o a cambiar las calorías.")

    com = lambda x: x.replace(".", ",")
    print(f"\n{len(props)} platos distintos posibles. Los {min(a.n, len(props))} mejores:\n")
    for i, p in enumerate(props[:a.n], 1):
        m = macros(p["items"])
        d = (m[0] - obj[0]) / obj[0] * 100
        print(f"#{i}  {p['nombre']}")
        print("    " + " · ".join(f"{n} {g} g" for n, g in p["items"]))
        print(f"    {m[0]:.0f} kcal ({com(f'{d:+.1f}')} %) · {m[1]:.0f} g P · "
              f"{m[2]:.0f} g G · {m[3]:.0f} g C")
        cob = "" if p["cob"] == 100 else f", con datos del {p['cob']} % del plato"
        calidad_txt = f" ({p['pts']}{cob})" if p["letra"] != "—" else " (faltan datos de etiqueta)"
        print(f"    calidad {p['letra']}{calidad_txt} · {com('%.2f' % p['eur'])} € la ración\n")

    if a.guardar:
        if not 1 <= a.guardar <= len(props):
            sys.exit(f"Solo hay {len(props)} propuestas; no existe la número {a.guardar}.")
        p = props[a.guardar - 1]
        nom = a.nombre or nombrar(p["items"])
        if any(n == nom for n, _ in PLATOS[t]):
            sys.exit(f"Ya tienes un plato llamado «{nom}» en esa toma. Usa --nombre para otro.")
        guardar(t, nom, p["items"], "generado")
        print(f"✓ «{nom}» guardado en datos/platos.csv.")
        print("  Ahora: python3 actualizar.py --recalcular")
    else:
        print("Para quedarte con uno:  python3 menu/generar.py "
              f"{a.toma} --guardar 1 --nombre \"Como lo quieras llamar\"")


if __name__ == "__main__":
    main()
