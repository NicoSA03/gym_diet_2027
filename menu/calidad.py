# -*- coding: utf-8 -*-
"""Nota de calidad de un alimento, con reglas explícitas y el porqué a la vista.

No es una opinión ni un número mágico: se parte de 100 puntos y se resta por
cuatro cosas medibles que vienen en la etiqueta, más un punto a favor por fibra.

  · Procesado (clasificación NOVA, de 1 a 4). 1 es el alimento tal cual;
    4 es un ultraprocesado formulado con ingredientes que no tienes en casa.
  · Azúcares por 100 g, con los cortes del semáforo británico (5 y 22,5).
  · Sal por 100 g (0,3 y 1,5).
  · Grasa saturada por 100 g (1,5 y 5).
  · Fibra por 100 g: suma puntos a partir de 3.

Los cortes son por 100 g de producto, así que castigan a los alimentos grasos
aunque la grasa sea buena: el aceite de oliva y los frutos secos pierden puntos
por saturadas. Es el precio de tener una regla simple y comprobable; lo que
decide de verdad es cuánto comes de cada cosa, y de eso se encarga el menú.

Si falta algún dato de la etiqueta, el alimento se queda «sin calificar» en vez
de inventarse una nota: ver_alimentos.py te dice cuáles te faltan.
"""

CLAVES = ("azucares", "sal", "saturadas", "nova")      # sin esto no hay nota
NOVA_TXT = {1: "sin procesar o mínimamente procesado", 2: "ingrediente culinario",
            3: "procesado", 4: "ultraprocesado"}
LETRAS = ((85, "A"), (70, "B"), (50, "C"), (0, "D"))


def calidad(a):
    """Devuelve {letra, puntos, motivos} o None si faltan datos de la etiqueta."""
    if any(a.get(k) is None for k in CLAVES):
        return None
    p, motivos = 100, []

    nova = int(a["nova"])
    resta = {1: 0, 2: 5, 3: 20, 4: 35}.get(nova, 20)
    p -= resta
    motivos.append(("−" + str(resta) if resta else "±0") + f" procesado: NOVA {nova}, {NOVA_TXT.get(nova,'?')}")

    def tramo(valor, bajo, alto, penas, etiqueta, unidad="g"):
        nonlocal p
        r = penas[0] if valor <= bajo else penas[1] if valor <= alto else penas[2]
        p -= r
        nivel = "bajo" if valor <= bajo else "medio" if valor <= alto else "alto"
        motivos.append(("−" + str(r) if r else "±0") + f" {etiqueta} {nivel}: {valor:g} {unidad}/100 g")

    tramo(a["azucares"], 5, 22.5, (0, 10, 25), "azúcares")
    tramo(a["sal"], 0.3, 1.5, (0, 8, 20), "sal")
    tramo(a["saturadas"], 1.5, 5, (0, 6, 15), "grasa saturada")

    fibra = a.get("fibra")
    if fibra is not None and fibra >= 3:
        suma = 8 if fibra >= 6 else 4
        p += suma
        motivos.append(f"+{suma} fibra: {fibra:g} g/100 g")

    p = max(0, min(100, p))
    letra = next(l for corte, l in LETRAS if p >= corte)
    return {"letra": letra, "puntos": p, "motivos": motivos}


def resumen(a):
    """Una línea para la app: «B · 78» o «— · faltan datos»."""
    c = calidad(a)
    return f"{c['letra']} · {c['puntos']}" if c else "— · faltan datos de la etiqueta"
