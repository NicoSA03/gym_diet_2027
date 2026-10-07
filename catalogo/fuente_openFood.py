# -*- coding: utf-8 -*-
"""Lidl y Carrefour a través de Open Food Facts (https://world.openfoodfacts.org).

   Es la base de datos abierta de alimentos más grande: los datos los suben
   usuarios escaneando el código de barras, con licencia libre (ODbL).
   Normas de uso que respetamos: identificarnos con un User-Agent y no pasar
   de 10 búsquedas por minuto."""
import time, urllib.parse
from comun import descargar, alimento

BASE = "https://world.openfoodfacts.org/api/v2/search"
CAMPOS = ("code,product_name_es,product_name,brands,stores_tags,nutriments,"
          "product_quantity,categories_tags_es,categories")
POR_PAGINA = 100
MAX_PAGINAS = 10          # los 1.000 productos más escaneados de cada tienda.
                          # Open Food Facts corta las búsquedas a partir de la página 11
                          # (error 503 o 401), así que no tiene sentido pedir más.
PAUSA = 6.5               # segundos entre búsquedas (límite: 10 por minuto)

TIENDAS = {"L": "lidl", "C": "carrefour"}


def _categoria(x):
    cats = x.get("categories") or ""
    return cats.split(",")[-1].strip() if cats else None


def obtener_tienda(letra, log=print):
    tienda = TIENDAS[letra]
    filas = {}
    for pagina in range(1, MAX_PAGINAS + 1):
        q = urllib.parse.urlencode({
            "countries_tags_en": "spain", "stores_tags": tienda,
            "fields": CAMPOS, "page_size": POR_PAGINA, "page": pagina})
        try:
            datos = descargar(f"{BASE}?{q}", espera=10)
        except RuntimeError as e:
            # Si ya hay productos de las páginas anteriores, se guardan esos y se
            # para aquí. Solo es un fallo de verdad si no ha llegado ninguno.
            if not filas:
                raise
            log(f"  {tienda.capitalize()}: paro en la página {pagina} ({str(e).split(' (')[0]})")
            break
        lote = datos.get("products") or []
        for x in lote:
            n = x.get("nutriments") or {}
            ean = x.get("code")
            if not ean or ean in filas:
                continue
            f = alimento(
                id_="O" + ean, super_=letra,
                nombre=x.get("product_name_es") or x.get("product_name"),
                marca=(x.get("brands") or "").split(",")[0], ean=ean,
                kcal=n.get("energy-kcal_100g"), p=n.get("proteins_100g"),
                g=n.get("fat_100g"), c=n.get("carbohydrates_100g"),
                fibra=n.get("fiber_100g"), azucar=n.get("sugars_100g"),
                sal=n.get("salt_100g"), sat=n.get("saturated-fat_100g"),
                formato_g=x.get("product_quantity"), categoria=_categoria(x))
            if f:
                filas[ean] = f
        if len(lote) < POR_PAGINA:
            break
        time.sleep(PAUSA)
    log(f"  {tienda.capitalize()}: {len(filas)} alimentos con macros completos")
    return list(filas.values())
