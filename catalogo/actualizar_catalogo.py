# -*- coding: utf-8 -*-
"""Genera docs/catalogo.json: los alimentos de Mercadona, Lidl y Carrefour con
   sus valores por 100 g, listo para que la app lo lea sin conexión.

   Uso:
     python3 catalogo/actualizar_catalogo.py              # las tres tiendas
     python3 catalogo/actualizar_catalogo.py --solo M     # solo Mercadona (M, L, C)

   Lo ejecuta solo GitHub cada lunes (.github/workflows/catalogo.yml).

   Regla de seguridad: si una fuente falla o trae menos de la mitad de
   productos que la vez anterior, se conservan sus datos anteriores. Así una
   caída de un servidor nunca vacía el catálogo."""
import sys, os, json, argparse, hashlib, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import CAMPOS, SUPER
import fuente_mercadona, catalogo.fuente_openFood as fuente_openFood

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "docs", "catalogo.json")
MINIMO = 0.5    # fracción del recuento anterior por debajo de la cual se desconfía


def cargar_anterior():
    try:
        with open(SALIDA, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"fuentes": {}, "items": []}


def de_tienda(items, letra):
    i = CAMPOS.index("super")
    return [x for x in items if letra in x[i]]


def unir_off(listas):
    """Un mismo producto puede estar en Lidl y en Carrefour: una sola fila con
       las dos letras."""
    por_ean, i_sup = {}, CAMPOS.index("super")
    for filas in listas:
        for f in filas:
            ean = f[CAMPOS.index("ean")]
            if ean in por_ean:
                previo = por_ean[ean]
                previo[i_sup] = "".join(sorted(set(previo[i_sup] + f[i_sup])))
            else:
                por_ean[ean] = list(f)
    return list(por_ean.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--solo", default="MLC", help="tiendas a actualizar: M, L, C")
    args = ap.parse_args()

    anterior = cargar_anterior()
    hoy = dt.date.today().isoformat()
    fuentes = dict(anterior.get("fuentes", {}))
    por_tienda = {}

    print("▶ Descargando el catálogo")
    for letra in "MLC":
        previo = de_tienda(anterior.get("items", []), letra)
        if letra not in args.solo.upper():
            por_tienda[letra] = previo
            continue
        try:
            nuevo = (fuente_mercadona.obtener() if letra == "M"
                     else fuente_openFood.obtener_tienda(letra))
            if previo and len(nuevo) < MINIMO * len(previo):
                raise RuntimeError(f"solo {len(nuevo)} productos frente a "
                                   f"{len(previo)} la vez anterior")
            por_tienda[letra] = nuevo
            fuentes[letra] = {"tienda": SUPER[letra], "ok": True,
                              "n": len(nuevo), "fecha": hoy}
        except Exception as e:        # una fuente caída no tumba las demás
            print(f"  AVISO {SUPER[letra]}: {e}. Se conservan los datos anteriores.")
            por_tienda[letra] = previo
            f = fuentes.get(letra, {"tienda": SUPER[letra], "n": len(previo), "fecha": None})
            f.update(ok=False, error=str(e)[:200], fallo=hoy)
            fuentes[letra] = f

    items = por_tienda["M"] + unir_off([por_tienda["L"], por_tienda["C"]])
    items.sort(key=lambda x: (x[CAMPOS.index("nombre")].lower(), x[0]))

    huella = hashlib.sha1(json.dumps(items, ensure_ascii=False).encode()).hexdigest()[:10]
    if huella == anterior.get("huella") and fuentes == anterior.get("fuentes"):
        print("✓ Sin cambios: el catálogo ya estaba al día.")
        return

    salida = {"version": 1, "huella": huella, "actualizado": hoy,
              "fuentes": fuentes, "campos": CAMPOS, "items": items}
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    tmp = SALIDA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, SALIDA)           # escritura atómica: nunca queda a medias
    dudosos = sum(x[CAMPOS.index("dudoso")] for x in items)
    print(f"✓ {len(items)} alimentos ({dudosos} con kcal que no cuadran) → "
          f"docs/catalogo.json, {os.path.getsize(SALIDA) // 1024} KB")


if __name__ == "__main__":
    main()
