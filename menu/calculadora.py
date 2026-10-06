# -*- coding: utf-8 -*-
"""Calculadora de raciones (v2.0), la misma cuenta que menu/calculadora.js.
   La usa ver_calculadora.py para comprobar, antes de construir, que cualquier
   plato en cualquier toma, bloque y tipo de día sale bien.
   Si cambias una de las dos, cambia la otra (la verificación compara ambas
   cuando Node está instalado; si no, se fía de esta)."""

PESO = [10, 4, 0.3, 0.3]            # kcal, proteína, grasa, carbohidrato
FORMA = {"proteina": 0.3, "base": 0.1, "grasa": 0.15, "fruta": 0.15, "lacteo": 0.25}
FORMA_CORTAR = 0.003                # pan y grasa en la cena: lo primero que se recorta


def _sistema(A, b):
    n = len(b)
    M = [fila[:] + [b[i]] for i, fila in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-12:
            return None
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r == c:
                continue
            f = M[r][c] / M[c][c]
            if not f:
                continue
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]


def suma(items, gramos):
    t = [0.0] * 4
    for it, g in zip(items, gramos):
        for m in range(4):
            t[m] += it["m"][m] * g / 100
    return t


def _cuenta(items, obj, peso):
    import math
    g = [it["g"] for it in items]
    libres = [i for i, it in enumerate(items)
              if not it.get("fijo") and it["rol"] != "verdura" and it["g"] > 0]
    clavado = {}
    for _ in range(len(items) + 1):
        vars_ = [i for i in libres if i not in clavado]
        fijo = [0.0] * 4
        for i, it in enumerate(items):
            if i not in vars_:
                gi = clavado.get(i, g[i])
                for m in range(4):
                    fijo[m] += it["m"][m] * gi / 100
        if not vars_:
            break
        nv = len(vars_) + 1
        filas, rhs = [], []
        for m in range(4):
            if not obj[m] > 0:
                continue
            w = math.sqrt(peso[m]) / obj[m]
            filas.append([w * items[i]["m"][m] / 100 for i in vars_] + [0])
            rhs.append(w * (obj[m] - fijo[m]))
        for j, i in enumerate(vars_):
            it = items[i]
            l = math.sqrt(FORMA_CORTAR if it.get("cortar") else FORMA.get(it["rol"], 0.03)) / it["g"]
            f = [0.0] * nv
            f[j] = l
            f[nv - 1] = -l * it["g"]
            filas.append(f)
            rhs.append(0.0)
        AtA = [[0.0] * nv for _ in range(nv)]
        Atb = [0.0] * nv
        for f, r in zip(filas, rhs):
            for a in range(nv):
                if not f[a]:
                    continue
                Atb[a] += f[a] * r
                for b in range(nv):
                    AtA[a][b] += f[a] * f[b]
        for a in range(nv):
            AtA[a][a] += 1e-9
        x = _sistema(AtA, Atb)
        if x is None:
            break
        # (y lo que se queda en menos de 3 g se quita, para que la cuenta lo sepa)
        peor, exceso, destino = -1, 0.0, 0.0
        for j, i in enumerate(vars_):
            it = items[i]
            d = it["lo"] if x[j] < it["lo"] else it["hi"] if x[j] > it["hi"] else 0 if x[j] < 3 else x[j]
            e = abs(x[j] - d) / (it["hi"] or 1)
            if e > exceso:
                exceso, peor, destino = e, i, d
            g[i] = x[j]
        if peor < 0:
            break
        clavado[peor] = destino
    for i, v in clavado.items():
        g[i] = v
    out = []
    for it, x in zip(items, g):
        if it.get("fijo") or it["rol"] == "verdura":
            out.append(it["g"])
        elif x < 3:
            out.append(0)
        else:
            out.append(_redondea(x / 5) * 5 if x >= 30 else _redondea(x))
    return out


def _redondea(x):
    """Math.round de JavaScript: los .5 hacia arriba (round() de Python iría al par)."""
    import math
    return math.floor(x + 0.5)


def item(n, g, f, toma, fijado=False):
    """Ficha de un alimento para la cuenta. f = [kcal, P, G, C, rol, nota, motivo, mín, máx]."""
    return {"n": n, "g": g, "m": f[:4], "rol": f[4],
            "lo": 0.6 * f[7] if f[4] == "proteina" else 0, "hi": f[8],
            "fijo": bool(fijado) or n == "Creatina monohidrato",
            "cortar": toma == "N" and (n == "Pan de semillas" or f[4] == "grasa")}


def resolver(items, obj):
    g1 = _cuenta(items, obj, PESO)
    if suma(items, g1)[1] > obj[1]:
        return _cuenta(items, obj, [PESO[0], PESO[1] / 10, PESO[2], PESO[3]])
    return g1
