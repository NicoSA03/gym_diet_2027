# Junio 2027 · plan de entreno y dieta

Todo el sistema cabe en **un único archivo, `Junio2027.html`**, que funciona igual en el PC y en el móvil, sin Claude y sin cargar otros archivos. Además se publica como **app instalable en Android** (una PWA) desde GitHub Pages: icono propio, pantalla completa y funciona sin internet. Tiene siete pestañas:

| Pestaña | Para qué |
|---|---|
| El entreno | La sesión de hoy: series, repeticiones, esfuerzo, abdominales, carrera y variantes |
| Registro | Apuntar series como en Hevy, peso corporal, carrera, gráficas de progreso e historial |
| La teoría | El porqué de todo, el desglose de cada ejercicio y el seguimiento semanal |
| Cómo funciona | La dieta: calorías por bloque y tipo de día, y qué hacer cuando la vida se cruza |
| Menús | Qué comer hoy, con los gramos exactos y todas las alternativas |
| La compra | La lista de Mercadona de la semana, con casillas |
| Actualizar | Este manual y los valores con los que está generado el archivo |

El archivo no se edita a mano: se **genera** a partir de unos pocos archivos de datos en Python. Cambias un dato, ejecutas una orden y sale un `Junio2027.html` nuevo. Para eso solo necesitas **Python 3.8 o superior**, sin librerías extra. Todo lo que se calcula (el plan, los datos del registro, la app instalable y sus iconos) se hace en Python; en el móvil solo corre el JavaScript mínimo para pintar y guardar. Y si no quieres tocar código, pídeselo a Claude en el proyecto «gym_dieta» (sección 7).

---

## 1. En 30 segundos

```bash
# 1. Cambia el dato en menu/entreno.py (entreno) o en menu/modelo.py (dieta)
# 2. Regenera todo
python3 actualizar.py
# 3. El resultado está en salida/Junio2027.html y la app instalable en docs/
```

Si has tocado **platos, alimentos o calorías de la dieta**, usa `python3 actualizar.py --recalcular` (tarda unos 20 segundos más).

Si la verificación encuentra un problema, **no se genera nada** y te dice qué ha fallado. Así nunca acabas con un archivo roto en el móvil.

---

## 2. Qué hay en cada sitio

```
junio2027/
├── actualizar.py        ← la única orden que necesitas
├── restaurar.py         ← reconstruye menu/ desde el paquete del proyecto de Claude
├── README.md
├── menu/
│   ├── entreno.py       ← TODO el entreno: peso, bloques, ejercicios, series, tabata, carrera, variantes
│   ├── modelo.py        ← la dieta: calorías por bloque, platos, cenas, tomas, tipos de día
│   ├── db.py            ← los alimentos: macros, formato de venta y precio de Mercadona
│   ├── payload3.py      ← en qué pasillo del súper está cada alimento
│   ├── payload_registro.py ← datos del Registro: descansos, ejercicios de peso corporal, volumen y km del plan
│   ├── pwa.py           ← convierte docs/ en app instalable: manifiesto, iconos y modo sin conexión
│   ├── ver_entreno.py   ← verificación del entreno
│   ├── ver_menu.py      ← verificación de la dieta
│   ├── a1…a6 *.html/.js ← diseño e interacción de cada pestaña (a6 es el Registro)
│   └── …                ← el resto son piezas internas del montaje
├── salida/
│   └── Junio2027.html   ← EL ARCHIVO DEL MÓVIL
└── docs/                ← LA APP: esto es lo que publica GitHub Pages
    ├── index.html       ← el mismo archivo
    ├── manifest.webmanifest, sw.js, icon-192.png, icon-512.png
```

**Regla de oro:** el 95 % de los cambios se hacen en `menu/entreno.py`. El resto, en `menu/modelo.py` y `menu/db.py`.

---

## 3. Los cambios de siempre, uno a uno

### Peso de la semana

`menu/entreno.py`, arriba del todo:

```python
PESO = 79.5        # kg, media real de partida (22 sep 2026)
```

Usa la **media de 7 días**, nunca el dato de un día suelto. Este número se muestra en la teoría y sirve de base para calcular la proteína por kilo que comprueba la verificación.

**Cuándo tocar las calorías** (esto es criterio, no automático). Mira la tendencia de dos semanas:

| Bloque | Ritmo buscado | Si dos semanas seguidas vas… | Haz esto |
|---|---|---|---|
| Construcción (B1, B3) | +0,2 kg/sem | por debajo de +0,05 | +100 kcal a ese bloque |
| Construcción (B1, B3) | +0,2 kg/sem | por encima de +0,35 | −100 kcal |
| Definición (B4) | −0,3 kg/sem | más lento de −0,15 | −100 kcal |
| Definición (B4) | −0,3 kg/sem | más rápido de −0,5 | +100 kcal |

Las calorías están en `menu/modelo.py`, en `FASES`. El tercer número de cada línea son las kcal medias del bloque:

```python
"B1": ("Construcción I", "Sem 5–12 · 19 oct → 13 dic 2026", 3400,175,85,484),
#                                                           kcal  P   G   C
```

Cuando subas o bajes kcal, cambia también los carbohidratos (C) en la misma proporción: 100 kcal son unos 25 g de C. Después ejecuta `python3 actualizar.py --recalcular`.

### Test de 5 km (al final de cada bloque)

`menu/entreno.py`:

```python
TEST_5K = "27:30"      # último test de 5 km (mm:ss); fija las zonas de carrera
OBJETIVO_5K = "23:00"  # 5 km objetivo en junio
```

Pon el tiempo nuevo y todas las zonas (Z2 a Z5) y el VO₂máx estimado se recalculan solos.

### Series, repeticiones y esfuerzo de un bloque

En `FASES`, dentro de cada bloque (`F0` a `F5`):

```python
esquema={"T1":(4,"6–8","RIR 2"), "T2":(3,"8–12","RIR 2"), "T3":(3,"12–15","RIR 1"), "TF":(3,"15–20","RIR 2")},
#              series reps  esfuerzo
```

- **T1:** básicos pesados.
- **T2:** secundarios.
- **T3:** accesorios.
- **TF:** gemelo, que lleva la misma pauta todo el año.

La verificación comprueba que ningún grupo muscular se quede fuera del rango útil (10–22 series semanales en los grandes) y que ninguna sesión pase de 80 minutos.

### Cambiar un ejercicio por otro

Hay que tocar dos sitios de `menu/entreno.py`:

**1. Darlo de alta en `EJ`** (si no existe ya):

```python
"Press Arnold": dict(m=["Hombro","Tríceps"], p="Empuje vertical",
  nota="Explicación larga para la teoría.",
  cue="Frase corta para el día a día.",
  sus="Press con mancuernas sentado"),
```

`m` es la lista de músculos que trabaja de forma directa, y es lo que cuenta la verificación de volumen. `p` es el patrón de movimiento.

**2. Ponerlo en el día que toque, en `DIAS`**, sustituyendo al que sale:

```python
ej=[("T1","Sentadilla trasera"),("T1","Press banca"), ... ("T2","Press Arnold"), ...],
```

**Opcional:** si quieres explicar cómo organizar sus series (pirámide, series iguales, una pesada y el resto más ligeras…), añádelo en `ESTRUCTURA`. Si no lo pones, usa la regla genérica de series rectas.

### Cómo se organizan las series de un ejercicio

`ESTRUCTURA`, con una entrada por tipo de bloque:

```python
"Dominadas lastradas": {
 "V":("Lastre constante", "Explicación…"),      # volumen:    F0, F1, F3
 "F":("Pirámide ascendente", "Explicación…"),   # fuerza:     F2
 "D":("Serie top y descarga", "Explicación…"),  # definición: F4
 "P":("Tres iguales, lejos del fallo", "…"),    # pico:       F5
},
```

### Abdominales (tabata 20-20)

`TABATA`, con las tablas `A`, `B` y `C` (lunes, miércoles y viernes). Cada tabla tiene un ejercicio `a` para las rondas impares, un ejercicio `b` para las pares, y el texto `sube`, que explica cómo progresar. El reloj está fijado en 8 × (20 s de trabajo + 20 s de descanso); la verificación comprueba que todo el bloque de abdominales se quede por debajo de 10 minutos.

### Kilómetros de carrera

En cada bloque de `FASES`:

```python
km=[10, 11, 12, 9, 13, 14, 15, 12],   # uno por semana del bloque
des=[4, 8],                           # semanas de descarga (empezando en 1)
largo=(45, 68),                       # minutos de la tirada del jueves: primera → última semana
mar="Texto de la sesión del martes",
jue="Texto de la sesión del jueves",
```

La verificación es estricta aquí:

- Tiene que haber **un valor de `km` por cada semana del bloque**.
- **Ninguna subida** puede pasar del 10 % respecto a la semana anterior (o de +1,5 km si el volumen es bajo). Las semanas de descarga no cuentan en esta comprobación.
- **La tirada del jueves** no puede pasar de 80 minutos.

### Fechas o duración de un bloque

En `FASES`, `sem=` (número de semanas) e `ini="AAAA-MM-DD"` (fecha de inicio, siempre en lunes). Los bloques tienen que ir seguidos, sin huecos ni solapes, y la verificación exige 39 semanas en total, con final el 20 de junio de 2027.

Si mueves un bloque de entreno, mueve también el texto de fechas del bloque de dieta equivalente en `menu/modelo.py` (`B0` ↔ `F0`, `B1` ↔ `F1`…).

### El Registro

`menu/payload_registro.py`, arriba del todo:

```python
DESCANSO = {"T1": 180, "T2": 120, "T3": 90, "TF": 60}   # segundos entre series
CORPORAL = {"Flexión clásica", "Dominadas lastradas"}   # en estos, «kg» es el lastre
RITMO = {"F0": None, "F1": 0.2, ...}                    # kg/semana buscados en cada bloque
```

Las sesiones del Registro salen solas de `DIAS` y `FASES` de `menu/entreno.py`: si cambias un ejercicio o las series de un bloque, el Registro lo recoge al regenerar. El historial se guarda por nombre de ejercicio, así que si renombras uno, sus gráficas empiezan de cero.

---

## 4. Cambios en la dieta

### Cambiar un plato o una cena

`menu/modelo.py`, listas `COMIDA` (7 platos) y `CENA` (7 cenas). Cada una es un nombre y una lista de `(alimento, gramos_base)`:

```python
("Lentejas con huevo", [("Lentejas cocidas (bote)",520),("Pan integral de molde",110),
                        ("Huevos",140),("Verdura congelada",150),("Aceite de oliva virgen ex.",22)]),
```

Los gramos que pones aquí son de **referencia**: el sistema los escala para cada bloque y tipo de día, y además iguala solo las calorías entre las siete opciones, así que elijas el plato que elijas el día cuadra. Aun así, intenta que todos sumen parecido (unos 1.200–1.250 kcal las comidas y unas 475 las cenas). Si uno pesa mucho más o mucho menos que el resto, el sistema tendrá que encogerlo o estirarlo, y las porciones quedarán raras. La verificación avisa si algún alimento principal acaba en una cantidad absurda.

Después: `python3 actualizar.py --recalcular`.

### Añadir un alimento nuevo (así se añadió el kéfir)

**1.** En `menu/db.py`, dentro de `F`:

```python
"Kéfir natural":  (63, 3.4, 3.5, 4.5,  500,  1.25, "fijo", "e"),
#                  kcal P   G    C   formato precio grupo  fuente
```

- `grupo`: `carb`, `grasa` y `prot` se escalan según el bloque; `fijo` no se escala nunca.
- `fuente`: `"f"` si has comprobado el precio en tienda (sale con punto verde en la lista de la compra), `"e"` si es una estimación.

**2.** En `menu/payload3.py`, en `SECCION`, dile en qué pasillo está:

```python
"Kéfir natural":"Huevos y lácteos",
```

Si te saltas este paso, el montaje se para con un error que dice qué alimento falta.

**3.** Úsalo en un plato o en una toma (`BLOQUES`, en `menu/modelo.py`) y ejecuta `python3 actualizar.py --recalcular`. El kéfir entró como cuarta opción del desayuno:

```python
("Avena con kéfir", [("Copos de avena Hacendado",165),("Leche semidesnatada",380),
                     ("Kéfir natural",210),("Plátano",160),("Proteína en polvo",20)]),
```

El kéfir tiene un tercio de la proteína del queso batido, así que la opción lleva proteína en polvo y no lleva crema de cacahuete. Con eso queda con los mismos macros que «Avena completa».

### Añadir una alternativa a una toma

Cada toma de `BLOQUES` (pre-entreno, desayuno, frutos secos, potito, turno, antes de dormir) es una lista de opciones con sus gramos base. Para añadir una, pon una línea más en la lista. No hace falta que sume exactamente lo mismo que las otras: el sistema iguala las calorías de todas las opciones de una toma automáticamente, así que da igual cuál elijas en la pestaña Menús. Solo procura que tenga parecida proteína, porque eso no se iguala. Después, `--recalcular`.

### Precios

`menu/db.py`, el sexto número de cada alimento. La lista de la compra y el total semanal se recalculan solos.

---

## 5. La app en el móvil (Android)

### Publicarla en GitHub Pages (una vez)

1. En GitHub, crea un repositorio llamado `junio2027`.
2. Sube el contenido de esta carpeta. Sin git: en la página del repositorio, «Add file → Upload files» y arrastra todo menos `salida/`. Con git: `git init`, `git add -A`, `git commit -m "Junio 2027"` y `git push`.
3. Ve a Settings → Pages → Deploy from a branch → rama `main`, carpeta `/docs` → Save.
4. En un par de minutos la app está en `https://tu-usuario.github.io/junio2027/`.

> **Ojo con la privacidad:** con una cuenta gratuita, GitHub Pages solo publica repositorios **públicos**, y el plan lleva tu peso y tus marcas (lo que apuntas en el Registro no: eso vive solo en tu móvil). Como estudiante puedes pedir gratis GitHub Pro con el *GitHub Student Developer Pack*, que permite Pages desde un repositorio privado.

### Instalarla

Abre esa dirección en **Chrome** en el móvil → menú ⋮ → **«Instalar aplicación»** (o «Añadir a pantalla de inicio»). Queda con su icono, se abre a pantalla completa y funciona sin cobertura.

### Actualizarla

```bash
python3 actualizar.py
git add -A && git commit -m "Semana 5: peso 79,8 kg" && git push     # o súbelo por la web
```

La app mira si hay versión nueva cada vez que la abres con conexión y la usa en ese momento; sin conexión abre la última que guardó. Tus registros no se tocan al actualizar.

### Probarla en el PC antes de subirla

```bash
python3 actualizar.py --probar
```

Abre `http://localhost:8000` en Chrome: funciona como la app de verdad, instalación incluida. Abierto con doble clic, `Junio2027.html` sigue funcionando entero, pero no se instala (una PWA necesita https o localhost).

### El Registro y tus datos

- **Entrenar:** eliges bloque y día (salen los de hoy) y pulsas «Empezar entreno». Cada ejercicio trae sus series del plan y, al lado, lo que hiciste la última vez. Si dejas un hueco vacío y marcas ✓, usa el valor de la vez anterior. Tocar el número de la serie la cambia a calentamiento (C, no cuenta) o al fallo (F). Al marcar una serie arranca el descanso y el móvil vibra al acabar. «Terminar» la guarda y avisa de los récords.
- **Peso y carrera:** el peso del día con su media de 7 días, y cada salida a correr con su ritmo.
- **Progreso:** 1RM estimado, carga máxima y volumen por ejercicio; peso corporal; km por semana frente al plan; y series por grupo muscular esta semana frente al rango útil.
- **Historial:** todo lo registrado y la **copia de seguridad**. Los datos viven solo en el navegador del móvil: si borras los datos de Chrome o cambias de teléfono, se pierden. Exporta una copia de vez en cuando y guárdala en tu carpeta del gimnasio; «Importar copia» la restaura en cualquier móvil o en el PC.

### En el PC o en iPhone

Doble clic en `Junio2027.html`, o abre la dirección de GitHub Pages: en Safari, Compartir → «Añadir a pantalla de inicio».

### Qué pasa con lo que tienes marcado

El bloque, el día, las opciones de cada toma y las casillas de la compra se guardan en el navegador, asociados a la **dirección** desde la que abres el archivo. Si actualizas en la misma dirección (el mismo archivo local o la misma web de GitHub Pages), se conservan. Si cambias de dirección, empiezas de cero.

### Cómo saber qué versión tienes

En el pie del archivo aparece `versión xxxxxxxx`: una huella de todo su contenido. Si cambia cualquier dato, cambia la huella.

---

## 6. La verificación

`actualizar.py` ejecuta dos baterías de comprobaciones antes de construir nada.

**Entreno** (`ver_entreno.py`):

- Calendario continuo de 39 semanas, con cada bloque empezando en lunes.
- Volumen semanal por grupo muscular dentro de rango.
- Ninguna sesión de más de 80 minutos, abdominales incluidos.
- Tabata por debajo de 10 minutos, con una tabla por día de fuerza.
- Todos los ejercicios tienen estructura de series en los cuatro tipos de bloque.
- Carrera: regla del 10 %, un valor de km por semana, tirada de 80 minutos como máximo.
- Cargas de arranque coherentes y cada bloque de entreno enlazado a su bloque de dieta.

**Dieta** (`ver_menu.py`):

- Cada día cae dentro del ±5 % de su objetivo de calorías.
- Cualquier combinación de opciones que elijas se queda dentro del ±12 %.
- La media semanal cuadra con el objetivo del bloque.
- Proteína de al menos 1,8 g por kilo.
- Ninguna porción absurda (1,3 kg de patata no cuenta como comida).

Si algo falla verás líneas que empiezan por `FALLO` con el motivo. Puedes ejecutar cualquiera de las dos por separado para ver el informe completo:

```bash
python3 menu/ver_entreno.py
python3 menu/ver_menu.py
```

`--forzar` construye aunque haya fallos. Úsalo solo si entiendes exactamente qué falla y por qué no importa.

---

## 7. Vinculado al proyecto «gym_dieta» de Claude

El proyecto guarda siempre la versión vigente de tres cosas:

- `claude/Junio2027.html` → el archivo de siete pestañas, listo para descargar desde cualquier dispositivo.
- `claude/README.md` → este manual.
- `claude/fuente_junio2027.txt` → todo el código en un solo archivo de texto.

**Cambiar algo desde Claude** es escribir en el proyecto lo que quieres, por ejemplo: «peso 80,1», «test de 5 km en 26:10» o «cambia las lentejas por alubias». Claude restaura la fuente, aplica el cambio, verifica, regenera el archivo y actualiza los tres documentos del proyecto. Tú solo descargas el nuevo `Junio2027.html`.

Para que Claude y tú trabajéis siempre sobre la misma versión:

**Si cambias tú algo:**

```bash
python3 actualizar.py --empaquetar
```

Genera un `fuente_junio2027.txt` nuevo. Súbelo al proyecto sustituyendo al anterior.

**Si Claude cambia algo:** descarga `fuente_junio2027.txt` del proyecto y:

```bash
python3 restaurar.py fuente_junio2027.txt
python3 actualizar.py --recalcular
```

Las cinco páginas publicadas en claude.ai **solo** se actualizan desde Claude. El archivo del móvil y GitHub Pages los controlas tú.

`python3 actualizar.py --paginas` genera también esas cinco páginas sueltas en `salida/paginas/`, por si alguna vez las quieres publicar tú. Son fragmentos pensados para claude.ai: para uso propio, usa siempre `Junio2027.html`.

---

## 8. Problemas frecuentes

| Qué ves | Qué pasa | Qué hacer |
|---|---|---|
| `KeyError: 'Kéfir natural'` | Alimento nuevo sin pasillo asignado | Añádelo a `SECCION` en `menu/payload3.py` |
| `KeyError` con el nombre de un ejercicio | Está en `DIAS` pero no en `EJ`, o está mal escrito | Revisa que el nombre sea idéntico en los dos sitios, tildes incluidas |
| `FALLO F1: 7 semanas de kilometraje para 8 semanas de bloque` | `km` no tiene un valor por semana | Iguala la longitud de `km` a `sem` |
| `FALLO … subidas … F1s3: 12→15 km` | Subida de más del 10 % | Reparte la subida en más semanas |
| `FALLO Patata: 1345 g en B3/D` | Un plato nuevo pesa mucho más o menos que el resto y el escalado lo lleva a una porción absurda | Ajusta sus gramos base para que ronde lo mismo que los otros, o reparte el carbohidrato entre dos alimentos |
| Los botones no hacen nada en el iPhone | Lo estás abriendo desde Archivos | Usa GitHub Pages (sección 5) |
| Chrome no ofrece «Instalar aplicación» | Lo abres como archivo o Pages aún no ha publicado | Abre la dirección https de GitHub Pages y espera un par de minutos tras subirlo |
| El Registro está vacío en otro móvil o en el PC | Los datos viven en cada navegador | Historial → Exportar copia en uno, Importar copia en el otro |
| Has perdido lo que tenías marcado | Has abierto el archivo desde otra dirección | Ábrelo siempre desde el mismo sitio |
| `SyntaxError` | Falta una coma, un paréntesis o unas comillas | El error indica la línea; casi siempre es la anterior a la que señala |

---

*Versión del sistema: 22 de septiembre de 2026 · peso de partida 79,5 kg · 5 km en 27:30 · con Registro y app instalable.*
