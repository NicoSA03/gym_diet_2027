# -*- coding: utf-8 -*-
"""Modelo del macrociclo de entrenamiento: 5 días, 39 semanas, 6 bloques.
   Fuente única de verdad para la página interactiva y para la verificación."""
import json, math, datetime as dt

PESO = 79.5        # kg, media real de partida (22 sep 2026)
TEST_5K = "27:30"   # último test de 5 km (mm:ss); fija las zonas de carrera
OBJETIVO_5K = "23:00"  # 5 km objetivo en junio

def seg(mmss):
    m, s = mmss.split(":")
    return int(m)*60 + int(s)
ALTURA = 182

# ---------------------------------------------------------------- bloques
# 21 sep 2026 (lunes) → 20 jun 2027 (domingo) = 39 semanas
FASES = {
"F0": dict(n="Rearranque", sem=4, ini="2026-09-21",
  lema="Recuperar el tejido, no la fuerza",
  foco="Vuelves de dos meses parados. El músculo recupera rápido; el tendón, "
       "el cartílago y la fascia no. Este bloque existe para que no te lesiones "
       "en la semana tres por una fuerza que sí tienes y una estructura que aún no.",
  esquema={"T1":(3,"8–10","RIR 4"), "T2":(3,"10–12","RIR 4"), "T3":(2,"12–15","RIR 3"), "TF":(3,"15–20","RIR 2")},
  pct=0.60, dieta="B0",
  mar="Continuo fácil, todo en Z2. Nada de series.",
  jue="Continuo fácil de 30 a 45 min. Subes 5 minutos por semana y nada más.",
  km=[7, 8, 9, 7], des=[4], largo=(30, 45)),

"F1": dict(n="Construcción I", sem=8, ini="2026-10-19",
  lema="El bloque que más músculo te va a dar",
  foco="Ocho semanas limpias, sin exámenes ni viajes. Es el tramo con mejor "
       "relación entre lo que cuesta y lo que devuelve en todo el año: volumen alto, "
       "superávit calórico y una vida razonablemente estable.",
  esquema={"T1":(4,"6–8","RIR 2"), "T2":(3,"8–12","RIR 2"), "T3":(3,"12–15","RIR 1"), "TF":(3,"15–20","RIR 2")},
  pct=0.75, dieta="B1",
  mar="Fartlek y series cortas. Empieza por 6×(2′ fuerte / 2′ suave).",
  jue="Tirada progresiva de 45 a 68 min. Al final del bloque son unos 10 km.",
  km=[10, 11, 12, 9, 13, 14, 15, 12], des=[4, 8], largo=(45, 68)),

"F2": dict(n="Fuerza y supervivencia", sem=5, ini="2026-12-14",
  lema="Exámenes y Navidad: menos volumen, más peso",
  foco="Cinco semanas en las que la vida no colabora. Bajamos el volumen y subimos "
       "la intensidad: es la combinación que mejor conserva lo ganado cuando duermes "
       "peor, comes fuera y entrenas en casa de tus padres sin gimnasio.",
  esquema={"T1":(5,"3–5","RIR 2"), "T2":(3,"6–8","RIR 2"), "T3":(2,"10–12","RIR 2"), "TF":(3,"15–20","RIR 2")},
  pct=0.85, dieta="B2",
  mar="5×1.000 m a ritmo de 10k, 2′ de trote entre series.",
  jue="Tirada sostenida de 50 a 62 min, unos 9 km. Sin prisa: el bloque es de sobrevivir.",
  km=[14, 15, 16, 12, 17], des=[4], largo=(50, 62)),

"F3": dict(n="Construcción II", sem=6, ini="2027-01-18",
  lema="El último empujón de volumen antes de definir",
  foco="La última ventana para añadir músculo con superávit. A partir de marzo todo "
       "lo que hagas será conservar, no construir, así que aquí se aprieta: es el "
       "bloque de más series de la temporada.",
  esquema={"T1":(4,"6–8","RIR 1"), "T2":(4,"8–12","RIR 1"), "T3":(3,"12–15","RIR 0–1"), "TF":(3,"15–20","RIR 2")},
  pct=0.78, dieta="B3",
  mar="6×1.000 m o 4×1.600 m a ritmo de umbral.",
  jue="Tirada larga de 62 a 75 min, hasta 11,5 km.",
  km=[18, 19, 20, 15, 21, 22], des=[4], largo=(62, 75)),

"F4": dict(n="Definición natural", sem=12, ini="2027-03-01",
  lema="Doce semanas a 300 kcal de déficit, ni una más",
  foco="Bajas 0,3 kg por semana. Es lento a propósito: a esa velocidad el cuerpo "
       "tira de grasa y respeta el músculo. La fuerza se mantiene porque las series "
       "principales siguen siendo pesadas; lo que baja es el volumen accesorio.",
  esquema={"T1":(4,"5–7","RIR 2"), "T2":(3,"8–10","RIR 1"), "T3":(3,"12–15","RIR 1"), "TF":(3,"15–20","RIR 2")},
  pct=0.80, dieta="B4",
  mar="Alterna semanas: VO2máx (5×3′) y ritmo de media (3×10′).",
  jue="Tirada larga de 70 a 80 min, hasta 13 km. Es el tope que permite tu hora y veinte.",
  km=[22, 23, 24, 18, 24, 25, 26, 19, 25, 26, 24, 20], des=[4, 8, 12], largo=(70, 80)),

"F5": dict(n="Pico y verano", sem=4, ini="2027-05-24",
  lema="Bajar el ruido y quedarse con la señal",
  foco="Menos volumen, misma intensidad. Es lo que hace que llegues a junio fresco "
       "y con los músculos llenos en vez de vaciado de tanto entrenar. Aquí no se "
       "gana nada nuevo: se revela lo de los nueve meses anteriores.",
  esquema={"T1":(3,"4–6","RIR 3"), "T2":(3,"8–10","RIR 2"), "T3":(2,"12–15","RIR 2"), "TF":(3,"15–20","RIR 2")},
  pct=0.80, dieta="B5",
  mar="4×1.000 m rápidos. Calidad alta, cantidad baja.",
  jue="Tirada que baja de 70 a 50 min según se acerca junio. Ni un minuto más.",
  km=[20, 18, 15, 12], des=[], largo=(70, 50)),
}

# ---------------------------------------------------------------- ejercicios
# musc: grupos que reciben estímulo DIRECTO (para la verificación de volumen)
EJ = {
"Sentadilla trasera":      dict(m=["Cuádriceps","Glúteo"], p="Rodilla",
  nota="Barra alta, profundidad hasta que el fémur pase la paralela. Es tu medidor de fuerza de piernas.",
  cue="Barra alta. Fémur por debajo de la paralela.",
  sus="Sentadilla en máquina Smith o prensa a 45°"),
"Press banca":             dict(m=["Pectoral","Tríceps"], p="Empuje horizontal",
  nota="Escápulas retraídas y pies clavados. Arco lumbar natural, no forzado.",
  cue="Escápulas retraídas, pies clavados.",
  sus="Press con mancuernas en banco plano"),
"Peso muerto rumano":      dict(m=["Isquios","Glúteo"], p="Cadera",
  nota="La barra roza el muslo todo el recorrido. Para cuando notes que la lumbar quiere redondearse, no antes ni después.",
  cue="La barra roza el muslo. Paras cuando la lumbar quiere redondearse.",
  sus="Peso muerto rumano con mancuernas"),
"Remo con barra":          dict(m=["Espalda","Bíceps"], p="Tirón horizontal",
  nota="Torso a 45°, barra al ombligo. Si tienes que dar tirones con la lumbar, has puesto demasiado.",
  cue="Torso a 45°, barra al ombligo.",
  sus="Remo en punta o remo en máquina apoyado"),
"Flexión clásica":         dict(m=["Pectoral","Tríceps"], p="Empuje horizontal",
  nota="Tu ejercicio. A partir de la semana 5, lastrada con disco en la espalda o con los pies elevados.",
  cue="Lastrada con disco a partir de la semana 5.",
  sus="Ninguno: este no se sustituye"),
"Curl de bíceps con barra Z": dict(m=["Bíceps"], p="Aislamiento",
  nota="Codos pegados al costado. Sin balanceo.",
  cue="Codos pegados al costado, sin balanceo.",
  sus="Curl con mancuernas"),
"Peso muerto convencional":dict(m=["Isquios","Glúteo","Espalda"], p="Cadera",
  nota="El ejercicio con más transferencia a todo lo demás y el que peor perdona la técnica con sueño de cinco horas. Si vienes del bar, baja el peso.",
  cue="Si vienes del turno con poco sueño, baja un 10 %.",
  sus="Peso muerto con trap bar o con hexagonal"),
"Dominadas lastradas":     dict(m=["Espalda","Bíceps"], p="Tirón vertical",
  nota="Agarre prono, ancho de hombros y medio. Si aún no llegas a 5 limpias, hazlas asistidas con goma.",
  cue="Agarre prono, ancho de hombros y medio.",
  sus="Jalón al pecho"),
"Zancada búlgara":         dict(m=["Cuádriceps","Glúteo"], p="Rodilla unilateral",
  nota="Mancuernas en las manos, pie trasero en el banco. Es el ejercicio que más corrige descompensaciones entre piernas.",
  cue="Mancuernas en las manos, pie trasero en el banco.",
  sus="Zancadas caminando"),
"Press militar de pie":    dict(m=["Hombro","Tríceps"], p="Empuje vertical",
  nota="De pie, glúteo y abdomen apretados. De pie y no sentado porque así el core trabaja de verdad.",
  cue="De pie. Glúteo y abdomen apretados.",
  sus="Press con mancuernas sentado"),
"Extensión de tríceps en polea": dict(m=["Tríceps"], p="Aislamiento",
  nota="Codos quietos. Solo se mueve el antebrazo.",
  cue="Codos quietos: solo se mueve el antebrazo.",
  sus="Press francés con barra Z"),
"Elevación de talones":    dict(m=["Gemelo"], p="Aislamiento",
  nota="Pausa de un segundo arriba y estiramiento completo abajo. Te protege el tendón de Aquiles de la carrera.",
  cue="Pausa arriba, estiramiento completo abajo.",
  sus="Elevación de talones de pie con mancuerna"),
"Sentadilla frontal":      dict(m=["Cuádriceps"], p="Rodilla",
  nota="Codos altos. Obliga al torso a quedarse vertical y castiga menos la lumbar que la trasera.",
  cue="Codos altos, torso vertical.",
  sus="Sentadilla goblet con mancuerna pesada"),
"Press inclinado con mancuernas": dict(m=["Pectoral","Hombro"], p="Empuje inclinado",
  nota="Banco a 30°. Más de eso y se convierte en un press de hombro.",
  cue="Banco a 30°, ni un grado más.",
  sus="Press inclinado en máquina"),
"Hip thrust":              dict(m=["Glúteo","Isquios"], p="Cadera",
  nota="Barbilla metida y pausa arriba. El glúteo fuerte es lo que te protege la rodilla al correr.",
  cue="Barbilla metida, pausa arriba.",
  sus="Puente de glúteo con barra en el suelo"),
"Remo con mancuerna a una mano": dict(m=["Espalda","Bíceps"], p="Tirón horizontal",
  nota="Rodilla y mano en el banco. Tira con el codo, no con la mano.",
  cue="Tira con el codo, no con la mano.",
  sus="Remo en polea baja unilateral"),
"Elevaciones laterales":   dict(m=["Hombro"], p="Aislamiento",
  nota="Sube hasta la altura del hombro y baja despacio. Es lo que da anchura a la silueta.",
  cue="Hasta la altura del hombro. Baja despacio.",
  sus="Elevaciones laterales en polea"),
"Face pull":               dict(m=["Hombro","Espalda"], p="Tirón alto",
  nota="A la altura de la cara, codos por encima de las muñecas. Compensa todo el empuje de la semana.",
  cue="A la altura de la cara, codos por encima de las muñecas.",
  sus="Pájaros con mancuernas tumbado en banco inclinado"),
}


# ------------------------------------------------- cómo se organizan las series
# Grupo de bloque: V=volumen (F0,F1,F3) · F=fuerza (F2) · D=definición (F4) · P=pico (F5)
GRUPO = {"F0":"V","F1":"V","F2":"F","F3":"V","F4":"D","F5":"P"}

GENERICO = {
"V":("Series rectas","Mismo peso en todas. Eliges el que te deja a RIR 2 en la primera y lo mantienes aunque la última se quede una repetición corta: esa caída es el estímulo, no un fallo."),
"F":("Series rectas pesadas","Mismo peso en todas y descanso largo. En este bloque el accesorio no busca fatiga, busca mantener el tejido."),
"D":("Series rectas","Mismo peso. En déficit el margen de recuperación es menor: quédate a RIR 1 real, no a RIR 1 optimista."),
"P":("Series rectas suaves","Mismo peso, lejos del fallo. Estas semanas no se gana nada: se conserva."),
}

ESTRUCTURA = {
"Dominadas lastradas": {
 "V":("Lastre constante","Las cuatro series con el mismo lastre. Empieza sin peso hasta que hagas 8 limpias; a partir de ahí añade 2,5 kg y vuelve a 6. Si la última serie se queda en 4, está bien: no bajes el lastre a mitad."),
 "F":("Pirámide ascendente","Cinco series subiendo lastre y bajando repeticiones: 5 con +5 kg, 4 con +10, 3 con +12,5, 3 con +15, y la quinta repitiendo el mejor peso que haya salido limpio. La serie en la que tengas que dar impulso con la cadera no cuenta: ahí se para la pirámide."),
 "D":("Serie top y descarga","Una serie pesada a 5 repeticiones y tres con 5 kg menos de lastre a 8. Conserva la fuerza con bastante menos fatiga, que es justo lo que necesitas comiendo por debajo de mantenimiento."),
 "P":("Tres iguales, lejos del fallo","Sin buscar récords. Si dudas entre dos lastres, el menor."),
},
"Sentadilla trasera": {
 "V":("Series rectas tras aproximación","Dos series de aproximación que no cuentan (barra sola y la mitad del peso) y luego todas las de trabajo con el mismo peso. La aproximación no es calentamiento social: es lo que hace que la primera serie de trabajo valga igual que la última."),
 "F":("Aproximación larga y cinco iguales","Sube en cuatro escalones hasta el peso de trabajo y haz las cinco series a ese peso. Tres minutos largos entre series. Si la cuarta se te va a RIR 0, quita peso en la quinta."),
 "D":("Series rectas pesadas","Cuatro series al mismo peso, 5–7 repeticiones. Este es el ejercicio que le dice a tu cuerpo que el músculo de las piernas sigue haciendo falta: no lo suavices por estar definiendo."),
 "P":("Tres series cómodas","Al 80 % de lo que moverías. Mantener el patrón, no la marca."),
},
"Press banca": {
 "V":("Series rectas tras aproximación","Igual que la sentadilla: dos aproximaciones y luego todo al mismo peso. Si la última serie cae dos repeticiones por debajo de la primera, el peso está bien elegido."),
 "F":("Serie top y dos descargas","Sube hasta una serie de 3 repeticiones exigente y luego haz cuatro series con un 10 % menos a 4–5. Es la forma con mejor relación fuerza/fatiga y la que mejor tolera entrenar a las siete de la mañana."),
 "D":("Series rectas pesadas","Cuatro al mismo peso. El banca es lo primero que se cae en déficit si lo abandonas: mantén la intensidad aunque bajes el volumen."),
 "P":("Tres series, RIR 3","Sin fallar ninguna repetición estas semanas."),
},
"Peso muerto convencional": {
 "V":("Series rectas y menos de las que crees","Cuatro series al mismo peso. El peso muerto genera más fatiga por serie que cualquier otro ejercicio: si un día dudas entre una serie más o parar, para."),
 "F":("Pirámide corta","Tres escalones de aproximación y luego tres series de 3–5 al peso de trabajo, no cinco. Con este ejercicio, en este bloque, menos series es más."),
 "D":("Series rectas al 80 %","Cuatro series. En déficit el peso muerto es el que peor perdona: baja el peso antes de bajar la técnica."),
 "P":("Dos o tres series ligeras","Solo para mantener el patrón. Aquí no se prueba nada."),
},
"Sentadilla frontal": {
 "V":("Series rectas","Cuatro al mismo peso. Si los codos se te caen antes de que fallen las piernas, el limitante es la movilidad de muñeca: usa agarre cruzado y sigue."),
 "F":("Cuatro series, la última abierta","Tres al peso de trabajo y en la cuarta haces las repeticiones que salgan limpias. Ese número es tu medidor semanal de progreso."),
 "D":("Series rectas","Cuatro iguales."),
 "P":("Tres series ligeras","Patrón, no carga."),
},
"Press inclinado con mancuernas": {
 "V":("Series rectas","Cuatro iguales. Con mancuernas la subida de peso es a saltos grandes: cuando llegues al tope del rango en todas las series, sube al par siguiente aunque te quedes en el extremo bajo."),
 "F":("Series rectas","Tres al mismo peso."),
 "D":("Series descendentes","Tres series bajando un par de mancuernas en cada una y manteniendo las repeticiones. Compensa la pérdida de fuerza del déficit sin recortar volumen."),
 "P":("Tres series cómodas","Sin buscar el fallo."),
},
"Flexión clásica": {
 "V":("Series al fallo menos dos","Tu ejercicio, así que aquí sí hay margen: haz las repeticiones que salgan menos dos en cada serie. Cuando pases de 20 sin lastre, ponte un disco en la espalda o eleva los pies y vuelve a 12."),
 "F":("Tres series lastradas","Con disco. Menos repeticiones y más peso, igual que el resto del bloque."),
 "D":("Series al fallo menos dos","Igual que en volumen. Es el ejercicio más barato en fatiga de todo el plan."),
 "P":("Dos series sueltas","Por gusto más que por estímulo."),
},
"Zancada búlgara": {
 "V":("Series rectas, empezando por la pierna mala","Siempre empiezas por la pierna que menos aguanta y la otra hace exactamente las mismas repeticiones, aunque le sobren. Es lo que corrige la descompensación en vez de perpetuarla."),
 "F":("Series rectas pesadas","Mismo criterio de pierna."),
 "D":("Series rectas","Mismo criterio de pierna."),
 "P":("Dos series ligeras","Mismo criterio de pierna."),
},
}

def estructura(ej, fase):
    g = GRUPO[fase]
    return ESTRUCTURA.get(ej, GENERICO if False else {}).get(g) or GENERICO[g]

# ------------------------------------------------------------------ abdominales
# Tabata 20-20: 20 s de trabajo, 20 s de descanso, 8 rondas alternando dos
# ejercicios. 5:20 de reloj; con montaje y estiramiento, menos de 8 minutos.
TABATA = {
"A": dict(n="Tabla A · Anti-extensión", dur="5:20 de reloj",
  a=("Plancha frontal", "Apoyo en antebrazos, glúteo apretado, costillas metidas. Si aguantas los 20 s sin temblar, ponte un disco en la zona alta de la espalda."),
  b=("Giro ruso con balón", "Sentado, pies en el aire, talones a un palmo del suelo. El balón cruza de cadera a cadera y el pecho gira con él: si solo se mueven los brazos, no estás entrenando el oblicuo."),
  como="Rondas impares plancha, rondas pares giro ruso. Cuatro de cada.",
  sube="Plancha: disco de 5 kg → 10 kg → 15 kg. Giro: balón de 3 kg → 5 kg → 7 kg. Sube una cosa cada dos semanas, nunca las dos a la vez."),
"B": dict(n="Tabla B · Anti-flexión lateral", dur="5:20 de reloj",
  a=("Plancha lateral", "Ronda 1 lado derecho, ronda 3 izquierdo, y así. Cadera alta y hombro apilado sobre el codo. El error típico es dejar caer la cadera en el segundo 15: mejor parar en el 15 con la forma buena que llegar a 20 hundido."),
  b=("Giro ruso con balón y pies elevados", "Igual que el de la tabla A pero con las piernas más altas y estiradas. Cambia mucho: el mismo balón pesa el doble."),
  como="Rondas impares plancha lateral alternando lado, rondas pares giro ruso.",
  sube="Plancha lateral: brazo libre estirado hacia el techo → pie de arriba elevado → disco sobre la cadera. El giro sube con el balón."),
"C": dict(n="Tabla C · Dinámica", dur="5:20 de reloj",
  a=("Hollow hold", "Tumbado boca arriba, lumbar pegada al suelo, brazos y piernas estirados y a un palmo del suelo. Si la lumbar se despega, sube las piernas hasta que vuelva a tocar."),
  b=("Giro ruso con balón de pie", "De pie, pies fijos, el balón dibuja un ocho alrededor de la cadera. Más cercano a lo que hace el torso en un saque de tenis o un remate de pádel que la versión sentada."),
  como="Rondas impares hollow, rondas pares giro de pie.",
  sube="Hollow: rodillas dobladas → una pierna estirada → las dos. El giro sube con el balón y con la velocidad, no con el recorrido."),
}
TABATA_REGLA = (
 "Ocho rondas de 20 segundos de trabajo y 20 de descanso, alternando los dos ejercicios "
 "de la tabla del día. Son 5 minutos y 20 segundos de reloj; con montarlo y estirar, menos "
 "de ocho minutos, que es lo que hace que la sesión entera siga cabiendo. "
 "Pon el Garmin en modo intervalos una vez y lo reutilizas todo el año.")

# ---------------------------------------------------------------- semana
DIAS = [
dict(cod="L", dia="Lunes", n="Fuerza A", sub="Empuje y cuádriceps", tipo="fuerza", dur="65–75 min",
  cal=["Bici o remo suave 5 min",
       "Movilidad de cadera y tobillo 3 min",
       "2 × 5 saltos al cajón bajo — toda la pliometría de la semana empieza aquí"],
  ej=[("T1","Sentadilla trasera"),("T1","Press banca"),
      ("T2","Peso muerto rumano"),("T2","Remo con barra"),
      ("T3","Flexión clásica"),("T3","Curl de bíceps con barra Z"),("TF","Elevación de talones")],
  tabata="A",
  nota="El día con más margen de la semana: no tienes clase hasta las 15:05. Si un día vas a ir sobrado de tiempo, es este."),

dict(cod="M", dia="Martes", n="Carrera de calidad", sub="VO2máx y umbral", tipo="carrera", dur="50–60 min",
  cal=["Trote muy suave 10 min",
       "4 × 20 m de progresión",
       "Movilidad de tobillo y cadera 2 min"],
  ej=[], tabata=None,
  nota="Martes y jueves entras a la universidad a las 12:30, así que tienes la mañana entera. Es el mejor hueco de la semana para las series."),

dict(cod="X", dia="Miércoles", n="Fuerza B", sub="Tirón y cadena posterior", tipo="fuerza", dur="65–75 min",
  cal=["Remo suave 5 min",
       "Movilidad de cadera y dorsal 3 min",
       "2 × 10 pogos (saltitos con el tobillo rígido)"],
  ej=[("T1","Peso muerto convencional"),("T1","Dominadas lastradas"),
      ("T2","Zancada búlgara"),("T2","Press militar de pie"),
      ("T3","Extensión de tríceps en polea"),("TF","Elevación de talones")],
  tabata="B",
  nota="Peso muerto a las siete de la mañana pide diez minutos de calentamiento de verdad. No los recortes."),

dict(cod="J", dia="Jueves", n="Tirada larga", sub="Base aeróbica en Z2", tipo="carrera", dur="45–80 min",
  cal=["Los tres primeros kilómetros SON el calentamiento: sal más lento de lo que te pide el cuerpo"],
  ej=[], tabata=None,
  nota="Toda en Z2: tienes que poder hablar frases completas. Si no puedes, vas demasiado rápido, y una tirada larga rápida no entrena nada y te deja sin el viernes."),

dict(cod="V", dia="Fuerza C", n="Fuerza C", sub="Funcional y densidad", tipo="fuerza", dur="60–70 min",
  cal=["Cuerda o bici 5 min",
       "Movilidad global 3 min",
       "3 × 3 saltos horizontales"],
  ej=[("T1","Sentadilla frontal"),("T1","Press inclinado con mancuernas"),
      ("T2","Hip thrust"),("T2","Remo con mancuerna a una mano"),
      ("T3","Elevaciones laterales"),("T3","Face pull")],
  tabata="C",
  nota="Última sesión antes de dos días sin entrenar. Puedes dejarte más que ningún otro día: tienes el sábado y el domingo para recuperar."),
]
DIAS[4]["dia"]="Viernes"

# ---------------------------------------------------------------- variantes
VARIANTES = [
dict(cod="EX", n="Exámenes", dias="3 días", dur="50 min",
  cuando="Las dos semanas antes de cada convocatoria, y la semana de exámenes.",
  regla="Lunes fuerza, miércoles carrera corta, viernes fuerza. Martes y jueves, nada.",
  detalle=[
   ("Lunes · Fuerza condensada",
    "Sentadilla trasera, Press banca, Remo con barra, Peso muerto rumano. "
    "Tres series de cada, mismas repeticiones que el bloque, un RIR más conservador. "
    "Sin accesorios, sin core. 45 minutos de reloj."),
   ("Miércoles · Carrera corta",
    "30 minutos continuos en Z2 o 6×400 m si la cabeza te pide descargar. "
    "Correr en época de exámenes no es entrenar: es lo que hace que estudies mejor por la tarde."),
   ("Viernes · Fuerza condensada",
    "Peso muerto convencional, Dominadas, Press militar, Zancada búlgara. "
    "Mismo formato que el lunes."),
  ],
  conserva="Conservas los seis patrones y alrededor del 60 % de las series. Con eso no se pierde músculo en tres o cuatro semanas: se pierde a partir de la sexta."),

dict(cod="VJ", n="Viaje de una semana", dias="4 días", dur="30–40 min",
  cuando="Una semana fuera, con mochila: banda elástica o TRX y poco más.",
  regla="La carrera es el ancla porque no necesita nada. La fuerza pasa a peso corporal y banda.",
  detalle=[
   ("Día 1 · Empuje y pierna",
    "Flexión clásica 5 × máximas−2 · Sentadilla búlgara a una pierna 4×12 · "
    "Press de hombro con banda 3×15 · Flexión diamante 3×12 · Plancha 3×45 s"),
   ("Día 2 · Carrera",
    "Reconoce la ciudad corriendo: 35–45 min en Z2. La mejor forma de no perder el bloque."),
   ("Día 3 · Tirón y cadena posterior",
    "Remo con banda anclada a una puerta 4×15 · Peso muerto rumano a una pierna 4×12 · "
    "Puente de glúteo a una pierna 3×15 · Curl con banda 3×20 · Superman 3×15"),
   ("Día 4 · Carrera con series",
    "10 min suave + 8 × (1′ fuerte / 1′ suave) + 10 min suave. Sin material y sin excusa."),
  ],
  conserva="Una semana así mantiene todo. La pérdida real de músculo empieza a las dos o tres semanas de parar del todo, y esto no es parar."),

dict(cod="CF", n="Casa de la familia, sin gimnasio", dias="5 días", dur="45–60 min",
  cuando="Navidad y Semana Santa. Tienes tiempo de sobra, banda, TRX y mancuernas de 7,5 kg.",
  regla="Con 7,5 kg no puedes ir pesado, así que vas por repeticiones altas y tiempo bajo tensión. "
        "Cambias la moneda: donde antes ponías kilos, ahora pones lentitud y recorrido.",
  detalle=[
   ("Lunes · Empuje",
    "Flexión con pies elevados 4 × máximas−2 · Press de hombro con mancuernas 4×15 · "
    "Flexión diamante 3×12 · Fondos entre dos sillas 3×12 · Elevaciones laterales 3×20 · Rueda o plancha"),
   ("Martes · Carrera de calidad",
    "Lo mismo que en el plan normal. Las series no necesitan gimnasio."),
   ("Miércoles · Pierna",
    "Sentadilla búlgara con mancuernas 4×15 por pierna, bajando en 3 segundos · "
    "Peso muerto rumano a una pierna 4×12 · Zancadas caminando 3×20 · "
    "Puente de glúteo a una pierna 3×15 · Elevación de talones a una pierna 3×20"),
   ("Jueves · Tirada larga",
    "Igual que en el plan normal."),
   ("Viernes · Tirón y core",
    "Dominadas en el parque o remo invertido bajo una mesa 5 × máximas−1 · "
    "Remo con banda 4×15 · Face pull con banda 3×20 · Curl con mancuernas 3×15 · "
    "Circuito de core 3 rondas"),
  ],
  conserva="Tres semanas así te cuestan poco si mantienes la carrera y las repeticiones cerca del fallo. "
           "Lo que se pierde en estos bloques casi nunca es músculo: es la coordinación con la barra, y vuelve en dos sesiones."),

dict(cod="MN", n="Sesión mínima", dias="1 día", dur="25–30 min",
  cuando="El día que todo se tuerce: dormiste mal, se alargó el turno, se te fue la mañana.",
  regla="La regla del día malo es entrenar poco, no saltártelo. Una sesión de 25 minutos mantiene "
        "la costumbre, que es lo que realmente se rompe cuando fallas un día.",
  detalle=[
   ("Opción fuerza",
    "Calentamiento 5 min. Luego solo los dos T1 del día, tres series de cada, un RIR más suave. "
    "Te vas con el 70 % del estímulo en un tercio del tiempo."),
   ("Opción carrera",
    "20 minutos continuos en Z2. Nada más. Cuenta como sesión."),
   ("Lo que no vale",
    "Saltártelo y meter el doble al día siguiente. Nunca funciona y es la forma más habitual de lesionarse."),
  ],
  conserva="No conserva nada por sí sola: conserva la racha, que a nueve meses vista vale más que cualquier sesión concreta."),
]

# ---------------------------------------------------------------- calendario
def calendario():
    out=[]; sem=1
    for cod,f in FASES.items():
        ini=dt.date.fromisoformat(f["ini"])
        fin=ini+dt.timedelta(days=7*f["sem"]-1)
        out.append(dict(cod=cod, n=f["n"], sem=f["sem"], s0=sem, s1=sem+f["sem"]-1,
                        ini=ini, fin=fin, dieta=f["dieta"]))
        sem+=f["sem"]
    return out

MES={1:"ene",2:"feb",3:"mar",4:"abr",5:"may",6:"jun",7:"jul",8:"ago",9:"sep",10:"oct",11:"nov",12:"dic"}
def fecha(d): return f"{d.day} {MES[d.month]} {d.year}"

# ---------------------------------------------------------------- fuerza
def e1rm(kg, reps):
    """Media de Epley y Brzycki."""
    ep = kg*(1+reps/30)
    br = kg/(1.0278-0.0278*reps)
    return (ep+br)/2

MARCAS = {"Sentadilla trasera": (80,4), "Press banca": (70,4)}
DESENTR = 0.88          # ~12 % perdido en 8 semanas parado (rango 10-15 %)

def arranque():
    """Cargas de la semana 1 del bloque F0: 60 % del 1RM actual estimado."""
    out={}
    for ej,(kg,r) in MARCAS.items():
        antes=e1rm(kg,r); ahora=antes*DESENTR
        out[ej]=dict(antes=round(antes), ahora=round(ahora),
                     s1=round(ahora*0.60/2.5)*2.5, s4=round(ahora*0.70/2.5)*2.5)
    return out

# ---------------------------------------------------------------- carrera
def vdot(dist_m, seg):
    v = dist_m/(seg/60)                      # m/min
    vo2 = -4.60 + 0.182258*v + 0.000104*v*v
    t = seg/60
    pct = 0.8 + 0.1894393*math.exp(-0.012778*t) + 0.2989558*math.exp(-0.1932605*t)
    return vo2/pct

def ritmo(seg_km):
    return f"{int(seg_km)//60}:{int(seg_km)%60:02d}"

def zonas(seg5k):
    """Ritmos por zona a partir del 5k actual, en segundos por km."""
    base = seg5k/5
    return [
      ("Z2 · Fácil",   ritmo(base+85), ritmo(base+115),
       "Hablas frases completas. Aquí va el 80 % de tus kilómetros."),
      ("Z3 · Medio",   ritmo(base+45), ritmo(base+70),
       "Frases cortas. Es la zona que más se usa por error y la que menos aporta."),
      ("Z4 · Umbral",  ritmo(base+15), ritmo(base+30),
       "Palabras sueltas. Ritmo de 10 km. Es donde se gana la media maratón."),
      ("Z5 · VO2máx",  ritmo(base-25), ritmo(base-5),
       "No hablas. Series de 3 a 5 minutos. Es donde sube el techo."),
    ]

SEGUIMIENTO = [
 ("Peso", "Media de 7 días, no el dato del lunes",
  "La báscula diaria oscila hasta 1,5 kg por sal, glucógeno y tránsito. La media semanal es el único número que significa algo. En construcción quieres +0,2 kg/semana; en definición, −0,3."),
 ("Kilómetros y reparto de zonas", "Strava, resumen semanal",
  "Objetivo: al menos el 75 % de los kilómetros en Z2. Si te sale 50 % en Z3 es la señal clásica de correr todo a ritmo medio, que cansa como el duro y entrena como el suave."),
 ("Carga aguda frente a crónica", "Garmin, pantalla de carga de entrenamiento",
  "El cociente entre la semana actual y la media de las cuatro anteriores. Entre 0,8 y 1,3 estás bien. Por encima de 1,5 es donde aparecen las periostitis y las tendinopatías."),
 ("VO2máx estimado", "Garmin, tendencia mensual",
  "No lo mires cada semana: el reloj tarda 3 o 4 semanas en reflejar un cambio real. De 36 a 44 en nueve meses es una progresión buena y realista."),
 ("e1RM de sentadilla, banca y peso muerto", "Cada 4 semanas, última serie",
  "Anota kilos y repeticiones de la última serie buena y calcula el 1RM estimado. Es lo que dice si el superávit está yendo a músculo o solo a grasa."),
 ("Sueño", "Garmin, media semanal",
  "Por debajo de 6,5 h de media la fuerza baja y el hambre sube. Con tus viernes y sábados, la única variable que puedes mover es la siesta del domingo."),
]

REGLAS = [
 ("Las dos primeras semanas vas a tener agujetas y no significan nada",
  "Después de dos meses parado, el dolor muscular tardío de las primeras sesiones es brutal y no guarda relación con lo bien que has entrenado. No añadas series porque te encuentres bien el día uno: el precio se paga el día tres."),
 ("El sábado y el domingo no se entrena, y es parte del plan",
  "Trabajas viernes y sábado hasta las tres de la mañana. Meter una sesión el fin de semana con cinco horas de sueño da un estímulo peor y un riesgo mayor que no meterla. Los cinco días de lunes a viernes ya cubren todo."),
 ("Si un día juegas al pádel, al fútbol sala o al baloncesto, no compenses",
  "Lo apuntas como lo que es, una sesión extra, y sigues el plan al día siguiente sin quitar nada. Lo único que sí conviene: no juegues el jueves por la tarde si el viernes toca sentadilla frontal."),
 ("Progresión doble: primero repeticiones, después kilos",
  "Cuando llegues al tope del rango en todas las series con el RIR que toca, sube el peso el mínimo que permita el gimnasio y vuelve al extremo bajo del rango. Nunca subas peso y repeticiones a la vez."),
 ("Descarga cada cuatro semanas",
  "La cuarta semana de cada bloque haces las mismas sesiones con dos series menos en los T1 y sin llegar a menos de RIR 3. No es opcional: es lo que hace que la quinta semana subas."),
 ("La regla del 10 % en carrera es la que te evita la periostitis",
  "Nunca subas el volumen semanal de carrera más de un 10 % respecto a la semana anterior, aunque te sientas bien. Es la lesión que más planes de nueve meses ha roto."),
 ("La barra no distingue entre un mal día y una mala técnica",
  "Si llegas del turno con cinco horas de sueño, baja el peso un 10 % y mantén las series. La sesión cuenta igual y el peso muerto a las siete de la mañana sin dormir es la forma más tonta de perder un mes."),
]
