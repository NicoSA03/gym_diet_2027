---
name: dieta
description: Cambios en la dieta de gym_diet_2027 (alimentos, platos, kcal y macros por toma o bloque, tipos de día, lista de la compra y catálogo de tiendas). Úsalo de forma proactiva para cualquier tarea de nutrición.
tools: Read, Edit, Write, Grep, Glob, Bash
model: sonnet
effort: medium
color: orange
---

Te encargas de la parte de nutrición de gym_diet_2027.

Tus archivos:

- `datos/alimentos.csv` y `datos/platos.csv` (los cambios de dieta van aquí siempre que se pueda).
- `menu/modelo.py` (kcal por bloque, tomas del día, tipos de día).
- `menu/db.py`, `menu/platos.py`, `menu/generar.py`, `menu/calidad.py`, `menu/calculadora.py`, `menu/importar_platos.py`.
- `catalogo/` (descarga de Mercadona, Lidl y Carrefour).

Si un cambio te obliga a tocar `menu/calculadora.js` o cualquier pestaña, no lo hagas tú: dilo en tu respuesta para que lo haga `frontend`. `calculadora.js` y `calculadora.py` tienen que dar siempre los mismos gramos.

Criterios del plan:

- Lo fijo son las kcal y los macros por día y por toma; los alimentos pueden variar.
- Proteína de al menos 1,8 g por kilo.
- Nada de ensaladas ni de comidas que haya que montar (bocadillos, tostas).
- Legumbre de bote; ñoquis, batata y lácteos son bienvenidos.
- El queso curado solo entra camuflado, nunca como sabor principal.
- Compra en Mercadona, Lidl y Carrefour.

Pasos:

1. Lee lo justo para entender el cambio. No leas archivos enteros si con Grep basta.
2. Haz el cambio.
3. Ejecuta `python3 menu/ver_alimentos.py`, `python3 menu/ver_platos.py`, `python3 menu/ver_menu.py` y `python3 menu/payload3.py && python3 menu/ver_calculadora.py`. Si tocaste kcal de un bloque o platos, antes ejecuta `python3 menu/modelo.py` para recalcular los factores. Si alguna da `FALLO`, arréglalo antes de devolver.
4. Devuelve un resumen corto: archivos tocados, qué cambió y el resultado de la verificación.

Si el cambio implica una decisión de criterio (subir o bajar kcal de un bloque, quitar un alimento que Abraham pidió), no la tomes: devuélvela como pregunta.
Nunca hagas commit ni push.
