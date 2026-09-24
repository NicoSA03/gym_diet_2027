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
# 1. Cambia el dato: menu/entreno.py (entreno) o datos/*.csv (alimentos y platos)
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
├── datos/
│   ├── alimentos.csv    ← LOS ALIMENTOS: se edita con Excel o el Bloc de notas
│   └── platos.csv       ← LOS PLATOS: qué lleva cada uno y cuánto
├── menu/
│   ├── entreno.py       ← TODO el entreno: peso, bloques, ejercicios, series, tabata, carrera, variantes
│   ├── modelo.py        ← la dieta: calorías por bloque, tomas del día, tipos de día
│   ├── db.py            ← carga datos/alimentos.csv y lo deja listo para el resto
│   ├── platos.py        ← carga datos/platos.csv y comprueba que todo cuadre
│   ├── generar.py       ← INVENTA PLATOS: tú pides calorías, él resuelve los gramos
│   ├── calidad.py       ← la nota A–D de cada alimento, con sus reglas a la vista
│   ├── ver_alimentos.py ← verificación de la base de datos y lista de datos que faltan
│   ├── ver_platos.py    ← verificación de los platos: que encajen en su toma y las raciones sean de verdad
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

**Regla de oro:** los cambios de entreno se hacen en `menu/entreno.py`; los de dieta, en los dos CSV de `datos/`. Solo hace falta tocar Python para cambiar las calorías de un bloque o las horas de las tomas (`menu/modelo.py`).

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

### Cambiar o añadir un plato

Todos los platos están en **`datos/platos.csv`**, una fila por plato, y se edita igual que `alimentos.csv`:

| Columna | Qué poner |
|---|---|
| `toma` | A qué toma pertenece: `C` comida, `N` cena, `D` desayuno, `P` pre-entreno, `S1` frutos secos, `S2` potito, `T` y `T2` turno, `Z` antes de dormir |
| `plato` | El nombre que sale en la app |
| `alimentos` | Los ingredientes separados por barra vertical (`|`), escritos **exactamente** como en `alimentos.csv` |
| `gramos` | Los gramos de cada uno, en el mismo orden y separados por barra |
| `notas` | Para ti; la app no los usa |

```
C;Pasta con pollo;Pasta integral|Pechuga de pollo|Champiñón laminado|Aceite de oliva virgen ex.;220|145|250|25;
```

Dos cosas que conviene tener claras:

- **Los gramos son la receta base, no lo que vas a comer.** El sistema los escala para cada bloque y tipo de día, y además iguala las calorías entre todas las opciones de una toma, así que elijas el plato que elijas el día cuadra. Por eso un plato nuevo tiene que salir con calorías parecidas a sus compañeros de toma (unas 1.225 las comidas, unas 475 las cenas): si se sale mucho, el sistema tendrá que encogerlo o estirarlo y las porciones quedarán raras. `python3 menu/ver_platos.py` te avisa.
- **En la comida y la cena, las siete primeras filas son la semana por defecto**, de lunes a domingo, y son las que entran en la lista de la compra. Las demás están ahí como alternativas para elegir a mano en la app.

Después: `python3 actualizar.py --recalcular`.

### Inventar platos nuevos sin pensar los gramos

`menu/generar.py` monta platos con los alimentos que ya tienes y calcula **los gramos exactos** para las calorías que le pidas. No necesita internet ni nada de fuera: es aritmética, y siempre da el mismo resultado.

```bash
# Propuestas de comida con las calorías que hacen falta para encajar en la app
python3 menu/generar.py comida

# Una cena suelta de 700 kcal y 55 g de proteína, para hoy
python3 menu/generar.py cena --kcal 700 --proteina 55

# Ocho ideas sin salmón, con patata sí o sí, de calidad B o mejor
python3 menu/generar.py comida --sin "Salmón fresco" --con Patata --nota B --n 8

# Guardar la propuesta número 3 en datos/platos.csv
python3 menu/generar.py comida --guardar 3 --nombre "Patata con pavo"
```

Cómo trabaja: coge una base, una proteína, una verdura y una grasa; descarta las combinaciones que no pegan; resuelve los gramos que clavan tus objetivos; tira las raciones absurdas; y ordena lo que queda por nota de calidad y precio. Si no le dices calorías, usa las de la toma, que es lo que necesita un plato para entrar en la app sin descuadrar nada.

Las reglas están arriba del archivo, a la vista y para que las cambies: `NO_JUNTOS` son las parejas que no pegan, `NO_DE_PLATO` lo que no quieres ver en una comida por mucho que cuadren los números, y `RACION` el mínimo y el máximo razonables de cada alimento.

Lo que propone son **ideas con los números resueltos**, no recetas probadas. Léelas antes de guardarlas: el programa sabe de aritmética, no de cocina.

### Añadir un alimento nuevo

Todo pasa en **`datos/alimentos.csv`**, una fila por alimento. Se abre con Excel (o con el Bloc de notas): el separador es el punto y coma y los decimales van con coma, como los guarda Excel en español.

| Columna | Qué poner |
|---|---|
| `nombre` | Tal cual lo vas a escribir en los platos. Si lo cambias, cámbialo también en los platos |
| `kcal`, `proteina`, `grasa`, `carbohidrato` | Por 100 g. Obligatorios |
| `azucares`, `fibra`, `sal`, `saturadas` | Por 100 g, de la etiqueta. Déjalos vacíos si aún no los tienes: vacío significa «no lo sé», no cero |
| `formato_g` | Gramos del envase que compras (1000 para un kilo, 570 para un bote…) |
| `precio_eur` | Lo que cuesta ese envase |
| `grupo` | `carb`, `grasa` o `prot` si debe escalar con el bloque; `fijo` si no |
| `seccion` | Pasillo del súper: Frutería, Carnicería, Pescadería, Huevos y lácteos, Refrigerados, Congelados, Conservas y despensa o Panadería |
| `nova` | Grado de procesado, de 1 a 4 (ver más abajo) |
| `fuente` | `f` si el precio lo has visto en tienda (sale con punto verde en la compra), `e` si es estimación |
| `rol` | Qué papel juega en un plato: `base`, `proteina`, `verdura`, `grasa`, `fruta` o `lacteo`. Lo usa `generar.py` para no combinar cualquier cosa con cualquier cosa |
| `notas` | Lo que quieras recordar |

Después, úsalo en un plato de `datos/platos.csv` y ejecuta `python3 actualizar.py --recalcular`.

### La nota de calidad (A, B, C, D)

Cada alimento lleva una letra que se calcula sola en `menu/calidad.py` y aparece en Menús y en La compra; al pasar el dedo o el ratón por encima te dice **por qué**. Se parte de 100 puntos:

- **Procesado (NOVA):** 1 sin procesar (−0), 2 ingrediente de cocina como el aceite (−5), 3 procesado como una conserva (−20), 4 ultraprocesado (−35).
- **Azúcares por 100 g:** hasta 5 no resta, de 5 a 22,5 resta 10, por encima resta 25.
- **Sal por 100 g:** hasta 0,3 no resta, de 0,3 a 1,5 resta 8, por encima resta 20.
- **Grasa saturada por 100 g:** hasta 1,5 no resta, de 1,5 a 5 resta 6, por encima resta 15.
- **Fibra por 100 g:** de 3 a 6 suma 4, a partir de 6 suma 8.

A partir de 85 es A, de 70 a 84 B, de 50 a 69 C, y por debajo D. Si falta algún dato de la etiqueta el alimento sale como «—» y no se inventa nota.

Los cortes son por 100 g de producto, así que castigan a los alimentos grasos aunque la grasa sea buena: el aceite de oliva se queda en B por sus saturadas. Es el precio de una regla simple y comprobable. Lo que de verdad decide es **cuánto** comes de cada cosa, y de eso se encarga el menú. Si algún criterio no te convence, cámbialo en `menu/calidad.py` y se recalcula todo.

`python3 menu/ver_alimentos.py` te dice, en cualquier momento, qué alimentos siguen sin datos de etiqueta y cuáles se quedan en C o D.

### Añadir una alternativa a una toma pequeña

El pre-entreno, el desayuno, los frutos secos, el potito, el kit del turno y lo de antes de dormir funcionan igual que las comidas: una fila más en `datos/platos.csv` con su código de toma. El sistema iguala las calorías de todas las opciones de una toma, así que da igual cuál elijas en la app. Solo procura que tenga parecida proteína, porque eso no se iguala. Después, `--recalcular`.

Las horas y los nombres de las tomas (no los platos) están en el diccionario `TOMAS`, al principio de `menu/modelo.py`.

### Precios

`datos/alimentos.csv`, columna `precio_eur`. La lista de la compra y el total semanal se recalculan solos.

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

`actualizar.py` ejecuta cuatro baterías de comprobaciones antes de construir nada.

**Entreno** (`ver_entreno.py`):

- Calendario continuo de 39 semanas, con cada bloque empezando en lunes.
- Volumen semanal por grupo muscular dentro de rango.
- Ninguna sesión de más de 80 minutos, abdominales incluidos.
- Tabata por debajo de 10 minutos, con una tabla por día de fuerza.
- Todos los ejercicios tienen estructura de series en los cuatro tipos de bloque.
- Carrera: regla del 10 %, un valor de km por semana, tirada de 80 minutos como máximo.
- Cargas de arranque coherentes y cada bloque de entreno enlazado a su bloque de dieta.

**Alimentos** (`ver_alimentos.py`):

- Las calorías declaradas cuadran con los macros (4/4/9, y 2 por la fibra).
- Los azúcares no pasan del carbohidrato ni las saturadas de la grasa.
- Todo alimento tiene grupo de escalado y pasillo, y valores dentro de lo posible.
- Lista de los alimentos sin datos de etiqueta y de los que se quedan en C o D.

**Platos** (`ver_platos.py`):

- Cada toma tiene platos suficientes (siete como mínimo la comida y la cena).
- Todos los platos de una toma valen lo mismo, ±12 % o ±25 kcal.
- Ninguna ración se sale de lo razonable, ni por arriba ni por abajo.
- Ningún ingrediente repetido dentro del mismo plato.
- Nota de calidad de cada plato y aviso de los que la tienen calculada a medias porque a algún ingrediente le faltan los datos de la etiqueta.

**Dieta** (`ver_menu.py`):

- Cada día cae dentro del ±5 % de su objetivo de calorías.
- Cualquier combinación de opciones que elijas se queda dentro del ±12 %.
- La media semanal cuadra con el objetivo del bloque.
- Proteína de al menos 1,8 g por kilo.
- Ninguna porción absurda (1,3 kg de patata no cuenta como comida).

Si algo falla verás líneas que empiezan por `FALLO` con el motivo. Puedes ejecutar cualquiera por separado para ver el informe completo:

```bash
python3 menu/ver_entreno.py
python3 menu/ver_alimentos.py
python3 menu/ver_platos.py
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
| `KeyError` con el nombre de un alimento | Está en un plato pero no en `datos/alimentos.csv`, o escrito distinto | Revisa que el nombre sea idéntico, tildes incluidas |
| `datos/alimentos.csv, línea 12 (…): falta «kcal»` | Una fila incompleta | Rellena esa casilla; las de azúcares, fibra, sal y saturadas sí pueden ir vacías |
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

*Versión del sistema: 24 de septiembre de 2026 · peso de partida 79,5 kg · 5 km en 27:30 · con Registro, app instalable y base de datos de alimentos y platos.*
