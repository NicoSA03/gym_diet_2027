# -*- coding: utf-8 -*-
"""Mercadona a través de MercaAPI (https://mercaapi.sgn.space).

   Es una API NO oficial y gratuita que copia la tienda online de Mercadona
   con sus valores nutricionales. Trae precio, formato y código de barras.
   Si algún día desaparece, el catálogo conserva los últimos datos buenos."""
import time
from comun import descargar, alimento

BASE = "https://mercaapi.sgn.space/api/products/"
POR_PAGINA = 200          # con páginas mayores el servidor corta la conexión
MAX_PAGINAS = 100         # tope de seguridad (~20.000 productos)


def obtener(log=print):
    filas, vistos = [], set()
    for pagina in range(MAX_PAGINAS):
        lote = descargar(f"{BASE}?skip={pagina * POR_PAGINA}&limit={POR_PAGINA}")
        if not lote:
            break
        for x in lote:
            n = x.get("nutritional_information") or {}
            if not x.get("is_food") or x.get("id") in vistos:
                continue
            vistos.add(x.get("id"))
            unidad = x.get("unit_size")
            f = alimento(
                id_="M" + str(x["id"]), super_="M", nombre=x.get("name"),
                marca=x.get("brand"), ean=x.get("ean"),
                kcal=n.get("calories"), p=n.get("protein"),
                g=n.get("total_fat"), c=n.get("total_carbohydrate"),
                fibra=n.get("dietary_fiber"), azucar=n.get("total_sugars"),
                sal=n.get("salt"), sat=n.get("saturated_fat"),
                precio=x.get("price"),
                formato_g=unidad * 1000 if unidad else None,
                categoria=(x.get("category") or {}).get("name"))
            if f:
                filas.append(f)
        time.sleep(0.5)   # sin prisa: es un servicio gratuito
    log(f"  Mercadona: {len(filas)} alimentos con macros completos")
    return filas
