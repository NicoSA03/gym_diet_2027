#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restaura la carpeta menu/ a partir de fuente_junio2027.txt (el paquete del proyecto de Claude).

Uso:  python3 restaurar.py fuente_junio2027.txt
"""
import os, re, sys

if len(sys.argv) != 2:
    sys.exit(__doc__)
txt = open(sys.argv[1], encoding="utf-8").read()
bloques = re.findall(r"^=== ARCHIVO: ([^\n]+?) ===\n(.*?)\n=== FIN ===$", txt, re.S | re.M)
if not bloques:
    sys.exit("No encuentro archivos dentro de ese paquete.")
for nombre, contenido in bloques:
    # formato actual: rutas relativas a la raíz («menu/db.py», «README.md»);
    # formato antiguo: solo el nombre, que iba siempre dentro de menu/
    ruta = nombre if ("/" in nombre or nombre in ("README.md", "actualizar.py", "restaurar.py", ".gitignore")) \
           else os.path.join("menu", nombre)
    if os.path.dirname(ruta):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido + "\n")
print(f"Restaurados {len(bloques)} archivos. Ahora: python3 actualizar.py --recalcular")
