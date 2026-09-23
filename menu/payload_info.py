# -*- coding: utf-8 -*-
import sys, json; sys.path.insert(0,'menu')
from modelo import FASES, TIPOS, BLOQUES, dia_totales, escalar
from db import macros
FACT=json.load(open('menu/factores.json'))
DIAS_SEM={"A":2,"B":2,"C":1,"D":1,"E":1}

HOR = {
 "A":[("06:30","Pre-entreno","casa"),("07:00","Gimnasio · 75 min","fuera"),
      ("08:45","Desayuno · el grueso","casa"),("14:00","Comida · el grueso","casa"),
      ("14:45","Dejar la cena preparada","casa"),("15:05","Salida a la universidad","fuera"),
      ("17:00","Bolsita de frutos secos","uni"),("19:30","Potito de fruta","uni"),
      ("22:00","Cena · 3 min al microondas","casa"),("23:00","A dormir","casa")],
 "B":[("06:30","Pre-entreno","casa"),("07:00","Carrera","fuera"),
      ("08:45","Desayuno · el grueso","casa"),("11:45","Comida · el grueso","casa"),
      ("12:30","Salida a la universidad","fuera"),("17:00","Bolsita de frutos secos","uni"),
      ("19:30","Potito de fruta","uni"),("22:00","Cena","casa"),("23:00","A dormir","casa")],
 "C":[("06:30","Pre-entreno","casa"),("07:00","Gimnasio · 75 min","fuera"),
      ("08:45","Desayuno · el grueso","casa"),("14:00","Comida · el grueso","casa"),
      ("17:00","Bolsita de frutos secos","uni"),("19:30","Potito de fruta","uni"),
      ("22:00","Cena","casa"),("23:00","Turno de bar","trabajo"),
      ("01:00","Kit de turno","trabajo"),("04:15","Antes de dormir","casa")],
 "D":[("11:30","Despertar · 7 h de sueño","casa"),("12:00","Pre-tirada","casa"),
      ("12:30","Desayuno · el grueso","casa"),("14:00","Tirada larga","fuera"),
      ("15:30","Comida · el grueso","casa"),("17:15","Bolsita de frutos secos","casa"),
      ("18:00","Turno de bar","trabajo"),("21:00","Segunda parada","trabajo"),
      ("01:00","Kit de turno","trabajo"),("04:15","Antes de dormir","casa")],
 "E":[("11:30","Despertar · 7 h de sueño","casa"),("12:00","Desayuno","casa"),
      ("15:00","Comida","casa"),("17:30","Frutos secos","casa"),("19:30","Fruta","casa"),
      ("21:30","Cena","casa"),("23:30","A dormir","casa")],
}

fases={}
for fcod,(fn,ff,K,P,G,C) in FASES.items():
    tipos={}
    for tcod,(tn,td,mult,tomas) in TIPOS.items():
        fc,fg,fp = FACT[f"{fcod}|{tcod}"]
        ms=[sum(dia_totales(tomas,{"C":j,"N":j},fc,fg,fp)[i] for j in range(7))/7 for i in range(4)]
        tipos[tcod]={"kcal":round(ms[0]),"p":round(ms[1]),"g":round(ms[2]),"c":round(ms[3]),
                     "obj":round(K*mult),"tomas":len(tomas)}
    media=sum(tipos[t]["kcal"]*DIAS_SEM[t] for t in tipos)/7
    fases[fcod]={"n":fn,"f":ff,"obj":[K,P,G,C],"tipos":tipos,"media":round(media)}

tipos={t:{"n":v[0],"d":v[1],"mult":v[2],"hor":HOR[t],"dias":DIAS_SEM[t]} for t,v in TIPOS.items()}

ESCENARIOS=[
 ("Comes fuera con amigos","social",
  "Una comida fuera a la semana no descuadra nada. Pide proteína a la plancha, arroz o patata de guarnición y salta el postre dulce. El error nunca es la comida fuera: es compensarla saltándote la cena, que es justo la toma que te sostiene la recuperación nocturna. Si sabes que vas a salir, come el desayuno de ese día igual y quita un poco de carbohidrato a la cena, no a la comida."),
 ("No te ha dado tiempo a cocinar","cocina",
  "Bote de legumbre escurrido, una lata de atún o dos huevos, verdura congelada al microondas y un vaso de gazpacho. Tres minutos, sin sartén y sin lavar nada. Esto sirve tanto para la comida como para la cena, y está calculado para no descuadrar: la legumbre de bote te da carbohidrato y proteína en el mismo plato."),
 ("Se te olvida la mochila","mochila",
  "Frutos secos y fruta los tienes en cualquier máquina o cafetería: es literalmente lo mismo que llevabas. No hace falta cambiar de estrategia ni recuperar nada después. Lo que sí descuadra es el refresco azucarado y la bollería del expositor; con agua o café el sustituto encaja sin tocar nada."),
 ("Te saltas el entreno de la mañana","entreno",
  "Quita el pre-entreno de las 06:30 y baja el desayuno a la versión del batido, que es la más pequeña de las tres. Con eso recortas unas 350 kcal, que es aproximadamente lo que no has gastado. No muevas la comida: el grueso del día se queda donde está."),
 ("Te pasas un día","exceso",
  "Al día siguiente vuelves al menú tal cual, sin recortar ni añadir cardio. Un día por encima son unas 800 kcal extra, menos de una décima de kilo de grasa. Lo que sí hace daño de verdad es la semana de compensación que viene después: ahí es donde la gente pierde adherencia y acaba abandonando el plan entero."),
 ("Semana de exámenes","examenes",
  "Pasas a la variante de exámenes del plan de entreno: tres días, cincuenta minutos, lunes y viernes fuerza condensada y miércoles carrera corta. En comida, tira de las versiones más rápidas de cada bloque y de legumbre de bote. Lo que no se negocia esa semana es el sueño: recortar de ahí para estudiar más es el peor cambio posible, porque también te destroza la retención de lo que estudias."),
 ("Noche larga en el bar o mal sueño","sueño",
  "Si has dormido menos de seis horas, baja la intensidad del entreno de ese día pero no lo saltes: cambia los intervalos por un rodaje suave, o quita una serie a cada ejercicio. En comida, sube ligeramente el carbohidrato del desayuno, porque con poco sueño el control del apetito empeora y llegar con hambre atrasada a la tarde es lo que dispara los antojos."),
 ("Te levantas sin hambre","apetito",
  "Pasa el desayuno a la versión del batido: entra mucho más fácil que un plato y aporta lo mismo. Si aun así no puedes, reparte: medio batido a las 08:45 y la otra mitad a las 11:00. Nunca lo saltes entero, porque a esa hora vienes de entrenar y es la única ventana grande del día."),
 ("Te pones enfermo","enfermedad",
  "Baja a mantenimiento (el objetivo del bloque B0) y prioriza proteína y líquidos por encima de cualquier otra cosa. Deja el entreno de fuerza y sustitúyelo por caminar si te apetece. Volver a entrenar con fiebre alarga la infección y no salva absolutamente nada del plan: tres días parado en octubre no se notan en junio."),
 ("Viaje o fin de semana fuera","viaje",
  "Céntrate solo en dos cosas: llegar a la proteína y no saltarte comidas. Todo lo demás es negociable durante tres o cuatro días. En cualquier supermercado tienes yogur, fruta, pan, atún y frutos secos, que es el 80 % de lo que come este plan. No intentes replicar el menú exacto: intenta replicar el reparto."),
 ("Se te acaba el presupuesto","dinero",
  "Los tres recortes que menos daño hacen: cambia el salmón por más atún o merluza, el pollo en bandeja grande sale más barato por kilo que en filetes, y la proteína en polvo sustituye a la botella ya hecha a menos de la mitad de precio. Con eso bajas la semana unos ocho euros sin tocar los macros."),
 ("Día de recarga en definición","recarga",
  "Un día a la semana subes a mantenimiento añadiendo carbohidrato: unos dos cazos más repartidos entre la comida y la cena. Ponlo el miércoles, la víspera de los intervalos, porque con los depósitos llenos la sesión clave de la semana rinde mucho más y te hace el bloque de definición bastante más llevadero."),
]

json.dump({"fases":fases,"tipos":tipos,"esc":ESCENARIOS,
           "dias_sem":DIAS_SEM}, open('menu/pay_info.json','w'), ensure_ascii=False, separators=(',',':'))
print("info:", len(open('menu/pay_info.json',encoding='utf8').read())//1024, "KB")
for f,v in fases.items():
    print(f"  {f}: media {v['media']} vs {v['obj'][0]} | " +
          " ".join(f"{t}:{v['tipos'][t]['kcal']}" for t in v['tipos']))
