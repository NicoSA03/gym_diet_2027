# -*- coding: utf-8 -*-
"""Piezas comunes del catálogo: descarga con reintentos, formato de cada
   alimento y control de calidad. Solo biblioteca estándar de Python."""
import json, time, urllib.request, urllib.error

AGENTE = "gym_diet_2027/1.0 (+https://github.com/NicoSA03/gym_diet_2027)"

# Orden de los campos de cada alimento en catalogo.json (se guardan como
# listas para que el archivo pese la mitad). Valores por 100 g.
CAMPOS = ["id", "super", "nombre", "marca", "ean", "kcal", "p", "g", "c",
          "fibra", "azucar", "sal", "sat", "precio", "formato_g",
          "categoria", "dudoso"]

SUPER = {"M": "Mercadona", "L": "Lidl", "C": "Carrefour"}


def descargar(url, intentos=4, espera=5, timeout=60):
    """GET que devuelve JSON. Reintenta con espera creciente; si al final
       falla, lanza la excepción para que la fuente se marque como caída."""
    ultimo = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENTE,
                                                       "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, ConnectionError,
                json.JSONDecodeError) as e:
            ultimo = e
            time.sleep(espera * (i + 1))
    raise RuntimeError(f"{ultimo} ({url})")   # el motivo primero: es lo que se lee


def num(x, dec=1):
    """Número redondeado, o None si no hay dato. Vacío significa «no lo sé»,
       nunca cero."""
    try:
        if x is None or x == "":
            return None
        return round(float(x), dec)
    except (TypeError, ValueError):
        return None


def dudoso(kcal, p, g, c, fibra):
    """True si las kcal declaradas no cuadran con los macros (4/4/9 y 2 por
       la fibra) con un margen del 15 % o 15 kcal. La app lo enseña con un
       aviso en vez de ocultarlo: el dato puede venir mal de la fuente."""
    est = 4 * p + 4 * c + 9 * g + 2 * (fibra or 0)
    return abs(est - kcal) > max(15, 0.15 * kcal)


def alimento(id_, super_, nombre, marca, ean, kcal, p, g, c, fibra=None,
             azucar=None, sal=None, sat=None, precio=None, formato_g=None,
             categoria=None):
    """Devuelve la fila lista para el catálogo, o None si no sirve
       (le falta nombre, kcal o alguno de los tres macros, o son imposibles)."""
    kcal, p, g, c = num(kcal, 0), num(p), num(g), num(c)
    if not nombre or None in (kcal, p, g, c):
        return None
    if not (0 <= kcal <= 900) or min(p, g, c) < 0 or p + g + c > 101:
        return None
    fibra = num(fibra)
    fila = [id_, super_, nombre.strip(), (marca or "").strip() or None,
            ean or None, kcal, p, g, c, fibra, num(azucar), num(sal, 2),
            num(sat), num(precio, 2), num(formato_g, 0),
            (categoria or "").strip() or None,
            1 if dudoso(kcal, p, g, c, fibra) else 0]
    return fila
