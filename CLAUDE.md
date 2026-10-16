# Instrucciones para Claude en gym_diet_2027

Este archivo lo leen la sesión principal y todos los subagentes de `.claude/agents/`.

## Reglas que valen para todos

- Si hay cualquier duda, se pregunta antes de actuar. Es la regla número uno.
- Nunca hacer `git commit` ni `git push`. Los cambios los sube Abraham.
- No machacar archivos: lo obsoleto que pueda servir va a `obsoleto/<versión>_<nombre>/` y se apunta en `obsoleto/LEEME.md`. La basura se puede borrar.
- Las partes de la app se nombran por versión (v2.3, v2.4, v3.0), nunca «nuevo» ni «antiguo».
- Cada versión de la app vive en su propia rama, creada desde la rama de la versión anterior.
- Ni en el código, ni en los textos de la app, ni en las respuestas: nada de guiones largos (— o –) ni puntos medios (·) como separador.
- La interfaz es visual y con poca información de golpe.
- El repositorio es público: no se añaden datos personales nuevos (horarios, trabajo, salud) a ningún archivo.
- Python 3.8 o superior y solo la biblioteca estándar.
- El HTML final no se edita a mano: se genera con `python3 actualizar.py`.

## Cómo trabaja la sesión principal (el supervisor)

La sesión principal no programa: reparte, coordina y comprueba. Así gasta pocos tokens y deja el trabajo pesado a modelos más baratos.

1. **Entender y preguntar.** Si el encargo es ambiguo, pregunta a Abraham antes de lanzar nada.
2. **Partir en subtareas.** Cada subtarea va a un solo subagente, con un encargo cerrado: qué cambiar, en qué archivos y cómo se sabe que está bien.
3. **Elegir el subagente** según la tabla de abajo. Si dos subtareas no tocan los mismos archivos, se lanzan a la vez.
4. **Segunda lectura obligatoria.** Cuando terminan, se lanza siempre `revisor` sobre el resultado (`git diff`).
5. **Corregir.** Si el revisor encuentra fallos, se devuelven al subagente que hizo el cambio con la lista concreta. Como mucho dos vueltas; si sigue fallando, se para y se pregunta a Abraham.
6. **Cerrar.** Con el visto bueno del revisor, ejecuta `python3 actualizar.py` (o `--recalcular` si se tocó la dieta) y resume a Abraham qué cambió, en qué archivos y en qué rama. No hace commit.

| Subagente | Modelo | Para qué |
|---|---|---|
| `ajustes` | Haiku | Cambios de un valor: peso semanal, test de 5 km, objetivo, una cifra suelta |
| `dieta` | Sonnet | Alimentos, platos, kcal y macros, tomas, lista de la compra, catálogo |
| `entreno` | Sonnet | Ejercicios, series, bloques, tabata, carrera y variantes |
| `frontend` | Sonnet | Pestañas, diseño, interacción, PWA y todo lo que se ve en el móvil |
| `revisor` | Opus | Segunda lectura de cualquier cambio. Solo lee y verifica, nunca edita |

Para buscar algo en el código sin cambiarlo, usa el agente integrado `Explore` en vez de leer muchos archivos en la sesión principal.

## Verificación

Cada batería se puede ejecutar por separado, siempre desde la raíz del repositorio:

```bash
python3 menu/ver_entreno.py
python3 menu/ver_alimentos.py
python3 menu/ver_platos.py
python3 menu/ver_menu.py
python3 menu/payload3.py && python3 menu/ver_calculadora.py
```

`ver_calculadora.py` necesita antes `payload3.py`, que genera `menu/pay_menus.json` (está en `.gitignore`, no ensucia nada). Estas órdenes solo comprueban; `python3 actualizar.py` además reconstruye `salida/` y `docs/`, y eso lo hace el supervisor al final.

Si alguna da `FALLO`, el cambio no está terminado. Nunca usar `--forzar` sin permiso de Abraham.
