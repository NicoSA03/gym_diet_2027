/* Conectividad v3.0: datos del reloj, métricas del perfil y viabilidad del plan.
   Módulo sin interfaz: no toca el DOM ni el plan en curso. Lo usan las pantallas
   «Conectar reloj», «Datos que faltan» y el aviso de imposible.
   Gemelo en Python: menu/conectividad.py (la verificación compara los dos). */
var Conectividad = (function(){
"use strict";

const AVISO_IMPOSIBLE = "Imposible hacer rutina con esas métricas en este tiempo, reajuste";

/* ---------------------------------------------------------------- marcas
   Cada marca: dónde se descargan los datos y qué archivo hay que subir. */
const MARCAS = [
 {id:"garmin", n:"Garmin", url:"https://connect.garmin.com/modern/activities",
  pasos:["Abre Garmin Connect en el navegador, entra en una carrera y pulsa el engranaje, «Exportar original» (.FIT).",
         "Para el resumen de todas, en la lista de actividades pulsa «Exportar CSV»."],
  tipos:[".fit",".zip",".csv",".gpx",".tcx"]},
 {id:"polar", n:"Polar", url:"https://flow.polar.com/diary/training-list",
  pasos:["Abre Polar Flow, entra en una sesión y pulsa «Exportar sesión».",
         "Elige TCX o GPX y sube el archivo."], tipos:[".tcx",".gpx",".csv"]},
 {id:"apple", n:"Apple Watch", url:"x-apple-health://",
  pasos:["En el iPhone abre Salud, toca tu foto y «Exportar todos los datos de salud».",
         "En Archivos descomprime exportar.zip y sube export.xml."], tipos:[".xml"]},
 {id:"suunto", n:"Suunto", url:"https://www.suunto.com/es-es/Support/",
  pasos:["En la app Suunto abre la actividad, menú de tres puntos y «Exportar como FIT».",
         "Sube el archivo .fit."], tipos:[".fit",".gpx"]},
 {id:"coros", n:"Coros", url:"https://training.coros.com/",
  pasos:["Entra en COROS Training Hub, abre la actividad y pulsa «Exportar».",
         "Elige FIT y súbelo."], tipos:[".fit",".gpx",".tcx"]},
 {id:"strava", n:"Strava", url:"https://www.strava.com/account",
  pasos:["En Strava, Ajustes, Mi cuenta, «Descarga o elimina tu cuenta», y pide el archivo (no borra nada).",
         "Cuando llegue el correo, descomprime y sube activities.csv o los .gpx."], tipos:[".csv",".gpx",".fit"]},
 {id:"otro", n:"Otro reloj", url:"",
  pasos:["Busca en la app de tu reloj la opción de exportar una actividad.",
         "Vale cualquier archivo .FIT, .GPX, .TCX o .CSV."], tipos:[".fit",".gpx",".tcx",".csv",".xml"]},
];

/* ---------------------------------------------------------------- métricas
   obl: obligatoria (sin ella no hay plan). reloj: puede venir del reloj.
   Para cada una: reloj, luego cálculo, luego se pide a mano. */
const METRICAS = [
 {k:"edad",        n:"Edad",                       u:"años",   obl:true,  reloj:true,  min:14,  max:90},
 {k:"sexo",        n:"Sexo",                       u:"",       obl:true,  reloj:true,  op:["h","m"]},
 {k:"altura",      n:"Altura",                     u:"cm",     obl:true,  reloj:true,  min:120, max:230},
 {k:"peso",        n:"Peso",                       u:"kg",     obl:true,  reloj:true,  min:35,  max:250},
 {k:"objetivo",    n:"Objetivo",                   u:"",       obl:true,  reloj:false, op:["5k","perder","ganar","mantener"]},
 {k:"dias_plan",   n:"Días que dura el plan",      u:"días",   obl:true,  reloj:false, min:7,   max:730},
 {k:"dias_semana", n:"Días de entreno por semana", u:"días",   obl:true,  reloj:false, min:2,   max:7},
 {k:"test_5k",     n:"Mejor 5 km reciente",        u:"mm:ss",  obl:false, reloj:true},
 {k:"objetivo_5k", n:"5 km que quieres",           u:"mm:ss",  obl:false, reloj:false},
 {k:"peso_objetivo",n:"Peso que quieres",          u:"kg",     obl:false, reloj:false, min:35, max:250},
 {k:"semanas_parado",n:"Semanas sin entrenar",     u:"sem",    obl:false, reloj:true,  min:0,   max:520},
 {k:"vo2max",      n:"VO2máx",                     u:"",       obl:false, reloj:true,  min:15,  max:90},
 {k:"fc_reposo",   n:"Pulso en reposo",            u:"ppm",    obl:false, reloj:true,  min:30,  max:110},
 {k:"fc_max",      n:"Pulso máximo",               u:"ppm",    obl:false, reloj:true,  min:120, max:230},
 {k:"km_semana",   n:"Km por semana (último mes)", u:"km",     obl:false, reloj:true,  min:0,   max:300},
 {k:"actividad",   n:"Actividad fuera del gimnasio",u:"",      obl:false, reloj:true,  op:["sedentario","ligero","activo","muy_activo"]},
];
/* Qué opcionales pasan a ser necesarias según el objetivo */
const NECESITA = {"5k":["test_5k","objetivo_5k"], perder:["peso_objetivo"], ganar:["peso_objetivo"], mantener:[]};

/* ---------------------------------------------------------------- utilidades */
function seg(mmss){ const p=String(mmss).trim().split(":").map(Number); return p.reduce((a,b)=>a*60+b,0); }
function mmss(s){ s=Math.round(s); return Math.floor(s/60)+":"+String(s%60).padStart(2,"0"); }   /* siempre mm:ss, aunque pase de la hora */
function r1(x){ return Math.round(x*10)/10; }
function vdot(dist, s){            /* igual que vdot() de menu/entreno.py */
  const v = dist/(s/60), t = s/60;
  const vo2 = -4.60 + 0.182258*v + 0.000104*v*v;
  const pct = 0.8 + 0.1894393*Math.exp(-0.012778*t) + 0.2989558*Math.exp(-0.1932605*t);
  return vo2/pct;
}
function tiempoPara(vd, dist){     /* inversa de vdot por bisección, en segundos */
  let lo=60, hi=36000;
  for(let i=0;i<80;i++){ const m=(lo+hi)/2; if(vdot(dist,m)>vd) lo=m; else hi=m; }
  return (lo+hi)/2;
}
/* Fecha local AAAA-MM-DD, igual que guarda el Registro (a6.js) */
function fechaLocal(d){ return d && !isNaN(d) ? d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0") : null; }
function fechaISO(x){ return x ? fechaLocal(new Date(x)) : null; }
const MESES={jan:1,ene:1,feb:2,mar:3,apr:4,abr:4,may:5,jun:6,jul:7,aug:8,ago:8,sep:9,oct:10,nov:11,dec:12,dic:12};
function fechaTexto(x){                /* «2026-10-30 07:05», «Oct 20, 2026, 7:00 AM», «20 oct 2026», «30/10/2026» */
  if(!x) return null; x=String(x).trim();
  let m=x.match(/^(\d{4})-(\d{2})-(\d{2})/); if(m) return m[1]+"-"+m[2]+"-"+m[3];
  m=x.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if(m){ let d=+m[1], me=+m[2]; if(me>12 && d<=12){ const t=d; d=me; me=t; }   /* 10/29/2026 de EE. UU. */
    return me>=1 && me<=12 && d>=1 && d<=31 ? m[3]+"-"+String(me).padStart(2,"0")+"-"+String(d).padStart(2,"0") : null; }
  m=x.match(/^([A-Za-z]{3})[a-z]*\.? (\d{1,2}),? (\d{4})/) || null;
  if(m && MESES[m[1].toLowerCase()]) return m[3]+"-"+String(MESES[m[1].toLowerCase()]).padStart(2,"0")+"-"+m[2].padStart(2,"0");
  m=x.match(/^(\d{1,2})\.? (?:de )?([A-Za-z]{3})[a-z]*\.? (?:de )?(\d{4})/i);
  if(m && MESES[m[2].toLowerCase()]) return m[3]+"-"+String(MESES[m[2].toLowerCase()]).padStart(2,"0")+"-"+m[1].padStart(2,"0");
  return null;
}
function equivalente5k(dist, s){   /* Riegel: tiempo de 5 km a partir de otra distancia */
  return s*Math.pow(5000/dist, 1.06);
}

/* Tipo de sesión común a todas las marcas: carrera, fuerza, bici, natación, caminar u otro */
function tipoSesion(x){
  x=String(x||"").toLowerCase();
  if(/run|carrera|correr|trail|cinta/.test(x)) return "carrera";
  if(/strength|fuerza|gym|gimnasio|pesas|weight|training|entreno|functional|hiit|crossfit/.test(x)) return "fuerza";
  if(/bik|cycl|bici|ciclismo/.test(x)) return "bici";
  if(/swim|nata|piscina/.test(x)) return "natación";
  if(/walk|camin|hik|sender/.test(x)) return "caminar";
  return "otro";
}

/* ---------------------------------------------------------------- lectores
   Todos devuelven {actividades:[{fecha, deporte, dist (m), seg, fc_media, fc_max}], perfil:{...}} */
function vacio(){ return {actividades:[], perfil:{}}; }
function attr(tag, nombre){ const m = tag.match(new RegExp(nombre+'="([^"]*)"')); return m? m[1] : null; }
function haversine(a,b,c,d){
  const R=6371000, r=Math.PI/180, x=(c-a)*r, y=(d-b)*r;
  const h=Math.sin(x/2)**2+Math.cos(a*r)*Math.cos(c*r)*Math.sin(y/2)**2;
  return 2*R*Math.asin(Math.sqrt(h));
}

function leerGPX(txt){
  const out=vacio(), pts=[...txt.matchAll(/<trkpt\b([^>]*)>([\s\S]*?)<\/trkpt>/g)];
  if(!pts.length) return out;
  let d=0, prev=null, fcs=[], t0=null, t1=null;
  for(const p of pts){
    const la=+attr(p[1],"lat"), lo=+attr(p[1],"lon");
    const tm=(p[2].match(/<time>([^<]+)<\/time>/)||[])[1];
    const hr=(p[2].match(/<(?:\w+:)?hr>(\d+)</)||[])[1];
    if(prev) d+=haversine(prev[0],prev[1],la,lo);
    prev=[la,lo]; if(tm){ if(!t0) t0=tm; t1=tm; } if(hr) fcs.push(+hr);
  }
  const s = t0&&t1 ? (Date.parse(t1)-Date.parse(t0))/1000 : 0;
  const tipo=(txt.match(/<trk>[\s\S]*?<type>([^<]+)<\/type>/)||[])[1]||"running";
  out.actividades.push({fecha:fechaISO(t0), deporte:tipoSesion(tipo),
    dist:Math.round(d), seg:Math.round(s),
    fc_media:fcs.length? Math.round(fcs.reduce((a,b)=>a+b,0)/fcs.length):null, fc_max:fcs.length? Math.max(...fcs):null});
  return out;
}

function leerTCX(txt){
  const out=vacio();
  for(const a of txt.matchAll(/<Activity\b([^>]*)>([\s\S]*?)<\/Activity>/g)){
    const dep=attr(a[1],"Sport")||"";
    let d=0, s=0, fm=[], fx=null, f=null;
    for(const l of a[2].matchAll(/<Lap\b([^>]*)>([\s\S]*?)<\/Lap>/g)){
      if(!f) f=attr(l[1],"StartTime");
      s+=+((l[2].match(/<TotalTimeSeconds>([\d.]+)</)||[])[1]||0);
      d+=+((l[2].match(/<DistanceMeters>([\d.]+)</)||[])[1]||0);
      const am=(l[2].match(/<AverageHeartRateBpm>\s*<Value>(\d+)/)||[])[1]; if(am) fm.push(+am);
      const mx=(l[2].match(/<MaximumHeartRateBpm>\s*<Value>(\d+)/)||[])[1]; if(mx) fx=Math.max(fx||0,+mx);
    }
    out.actividades.push({fecha:fechaISO(f), deporte:tipoSesion(dep),
      dist:Math.round(d), seg:Math.round(s),
      fc_media:fm.length? Math.round(fm.reduce((x,y)=>x+y,0)/fm.length):null, fc_max:fx});
  }
  return out;
}

/* CSV de Garmin Connect, Strava (activities.csv) y similares, en español o en inglés */
function partirCSV(linea, sep){
  const r=[]; let c="", q=false;
  for(let i=0;i<linea.length;i++){
    const ch=linea[i];
    if(ch==='"'){ if(q && linea[i+1]==='"'){ c+='"'; i++; } else q=!q; }
    else if(ch===sep && !q){ r.push(c); c=""; }
    else c+=ch;
  }
  r.push(c); return r.map(x=>x.trim());
}
function num(x){ if(x==null) return NaN; x=String(x).replace(/\s/g,""); if(/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(x)) x=x.replace(/\./g,""); return parseFloat(x.replace(",",".")); }
function duracion(x){ if(x==null||x==="") return NaN; return /:/.test(x)? seg(x.split(".")[0].split(",")[0]) : num(x); }
const COL = {
  tipo:  [/^tipo de actividad$/i,/^activity type$/i,/^tipo$/i,/^type$/i],
  fecha: [/^fecha$/i,/^date$/i,/^activity date$/i,/^fecha de la actividad$/i],
  dist:  [/^distancia$/i,/^distance$/i],
  tiempo:[/^tiempo$/i,/^time$/i,/^elapsed time$/i,/^moving time$/i,/^tiempo transcurrido$/i,/^duraci[oó]n$/i],
  fcm:   [/^(frecuencia cardiaca|fc) media$/i,/^avg hr$/i,/^average heart rate$/i],
  fcx:   [/^(fc|frecuencia cardiaca) m[aá]xima$/i,/^max hr$/i,/^max heart rate$/i],
};
function leerCSV(txt){
  const out=vacio(), lineas=txt.replace(/^﻿/,"").split(/\r?\n/).filter(l=>l.trim());
  if(lineas.length<2) return out;
  const sep = (lineas[0].split(";").length > lineas[0].split(",").length) ? ";" : ",";
  const cab = partirCSV(lineas[0], sep);
  const ix = {}; for(const k in COL){ ix[k] = cab.findIndex(h=>COL[k].some(r=>r.test(h))); }
  if(ix.dist<0 || ix.tiempo<0) return out;
  /* Garmin da km (natación en metros) y el export de Strava da metros: se decide fila a fila.
     Más de 300 son metros: nadie hace 300 km de una vez. */
  const filas = lineas.slice(1).map(l=>partirCSV(l, sep));
  for(const f of filas){
    const d=num(f[ix.dist]), s=duracion(f[ix.tiempo]);
    if(!(s>0)) continue;            /* sin distancia vale (fuerza): cuenta para el calendario */
    const tipo = ix.tipo>=0 ? f[ix.tipo] : "carrera";
    out.actividades.push({fecha: ix.fecha>=0 ? fechaTexto(f[ix.fecha]) : null,
      deporte: tipoSesion(tipo),
      dist: d>0 ? Math.round(d>300 ? d : d*1000) : 0, seg: Math.round(s),
      fc_media: ix.fcm>=0 && num(f[ix.fcm])>0 ? Math.round(num(f[ix.fcm])) : null,
      fc_max:   ix.fcx>=0 && num(f[ix.fcx])>0 ? Math.round(num(f[ix.fcx])) : null});
  }
  return out;
}

/* export.xml de Apple Salud: perfil, últimas medidas y entrenos de carrera */
function leerApple(txt){
  const out=vacio(), P=out.perfil, ult={};
  const me=txt.match(/<Me\b[^>]*>/);
  if(me){
    const nac=attr(me[0],"HKCharacteristicTypeIdentifierDateOfBirth");
    if(nac){ const n=new Date(nac), h=new Date(); P.edad=h.getFullYear()-n.getFullYear()-((h.getMonth()<n.getMonth()||(h.getMonth()==n.getMonth()&&h.getDate()<n.getDate()))?1:0); }
    const sx=attr(me[0],"HKCharacteristicTypeIdentifierBiologicalSex");
    if(/Female/.test(sx||"")) P.sexo="m"; else if(/Male/.test(sx||"")) P.sexo="h";
  }
  const TIPOS={HKQuantityTypeIdentifierBodyMass:"peso", HKQuantityTypeIdentifierHeight:"altura",
    HKQuantityTypeIdentifierRestingHeartRate:"fc_reposo", HKQuantityTypeIdentifierVO2Max:"vo2max"};
  for(const r of txt.matchAll(/<Record\b[^>]*>/g)){
    const k=TIPOS[attr(r[0],"type")]; if(!k) continue;
    const f=attr(r[0],"startDate")||""; if(ult[k] && ult[k].f>=f) continue;
    let v=+attr(r[0],"value"); const u=attr(r[0],"unit")||"";
    if(k==="altura" && u==="m") v*=100; if(k==="altura" && u==="ft") v*=30.48;
    if(k==="peso" && u==="lb") v*=0.4536;
    ult[k]={f, v};
  }
  for(const k in ult) P[k]= k==="vo2max" ? r1(ult[k].v) : Math.round(ult[k].v*(k==="peso"?10:1))/(k==="peso"?10:1);
  for(const w of txt.matchAll(/<Workout\b([^>]*?)(\/>|>([\s\S]*?)<\/Workout>)/g)){
    const t=w[1], cuerpo=w[3]||"", tipo=tipoSesion((attr(t,"workoutActivityType")||"").replace("HKWorkoutActivityType",""));
    let d=+(attr(t,"totalDistance")||0), du=attr(t,"totalDistanceUnit")||"km";
    if(!d){                              /* desde iOS 16 la distancia va en WorkoutStatistics */
      const st=cuerpo.match(/<WorkoutStatistics\b[^>]*type="HKQuantityTypeIdentifierDistance(?:WalkingRunning|Cycling|Swimming)"[^>]*>/);
      if(st){ d=+(attr(st[0],"sum")||0); du=attr(st[0],"unit")||"km"; }
    }
    d = du==="km"? d*1000 : du==="mi"? d*1609.34 : d;
    let s=+(attr(t,"duration")||0); if((attr(t,"durationUnit")||"min")==="min") s*=60;
    if(s>0) out.actividades.push({fecha:fechaTexto(attr(t,"startDate")), deporte:tipo,
      dist:Math.round(d), seg:Math.round(s), fc_media:null, fc_max:null});
  }
  return out;
}

/* .FIT binario (Garmin, Coros, Suunto, Wahoo, Polar). Lee los mensajes session (18)
   y user_profile (3); ignora los demás. Respeta cabeceras comprimidas y campos de desarrollador. */
function leerFIT(buf){
  const out=vacio(), dv=new DataView(buf instanceof ArrayBuffer? buf : buf.buffer.slice(buf.byteOffset, buf.byteOffset+buf.byteLength));
  const hl=dv.getUint8(0);
  if(dv.byteLength<12 || String.fromCharCode(dv.getUint8(8),dv.getUint8(9),dv.getUint8(10),dv.getUint8(11))!==".FIT") throw new Error("No es un archivo FIT");
  const fin = hl + dv.getUint32(4,true);
  if(fin > dv.byteLength) throw new Error("FIT dañado o incompleto: vuelve a descargarlo");
  const defs={}; let p=hl;
  const leer=(o,tam,base,le)=>{
    const t=base&0x1F;
    if(tam===1) return t===1? dv.getInt8(o) : dv.getUint8(o);
    if(tam===2) return t===3? dv.getInt16(o,le) : dv.getUint16(o,le);
    if(tam===4) return t===5? dv.getInt32(o,le) : t===8? dv.getFloat32(o,le) : dv.getUint32(o,le);
    return null;
  };
  const INV={1:0xFF,2:0xFFFF,4:0xFFFFFFFF};
  while(p<fin){
    const h=dv.getUint8(p++);
    if(h & 0x80){                                   /* cabecera de tiempo comprimido */
      const d=defs[(h>>5)&3]; if(!d) throw new Error("FIT dañado");
      p=dato(d,p); continue;
    }
    const loc=h&0x0F;
    if(h & 0x40){                                   /* definición */
      p++; const le=dv.getUint8(p++)===0; const g=dv.getUint16(p,le); p+=2;
      const n=dv.getUint8(p++), campos=[];
      for(let i=0;i<n;i++){ campos.push([dv.getUint8(p),dv.getUint8(p+1),dv.getUint8(p+2)]); p+=3; }
      let dev=0; if(h & 0x20){ const nd=dv.getUint8(p++); for(let i=0;i<nd;i++){ dev+=dv.getUint8(p+1); p+=3; } }
      defs[loc]={g, le, campos, dev};
    } else {
      const d=defs[loc]; if(!d) throw new Error("FIT dañado");
      p=dato(d,p);
    }
  }
  function dato(d,p){
    const v={};
    for(const [num,tam,base] of d.campos){
      const x = (tam===1||tam===2||tam===4) ? leer(p,tam,base,d.le) : null;
      if(x!==null && x!==INV[tam] && !((base&0x1F)===1 && x===0x7F) && !((base&0x1F)===3 && x===0x7FFF) && !((base&0x1F)===5 && x===0x7FFFFFFF)) v[num]=x;
      p+=tam;
    }
    p+=d.dev;
    if(d.g===18){                                   /* session */
      const SPORT={1:"carrera",2:"bici",5:"natación",10:"fuerza",11:"caminar",17:"caminar"};
      out.actividades.push({
        fecha: v[2]!=null ? fechaLocal(new Date((v[2]+631065600)*1000)) : null,
        deporte: SPORT[v[5]] || "otro",
        dist: v[9]!=null ? Math.round(v[9]/100) : 0,
        seg:  v[8]!=null ? Math.round(v[8]/1000) : v[7]!=null ? Math.round(v[7]/1000) : 0,   /* 8: en movimiento; 7: con pausas */
        fc_media: v[16]!=null ? v[16] : null, fc_max: v[17]!=null ? v[17] : null});
    } else if(d.g===3){                             /* user_profile */
      const P=out.perfil;
      if(v[1]!=null) P.sexo = v[1]===1? "h" : "m";
      if(v[2]!=null) P.edad = v[2];
      if(v[3]!=null) P.altura = Math.round(v[3]);   /* escala 100: viene en cm */
      if(v[4]!=null) P.peso = v[4]/10;
      if(v[8]!=null) P.fc_reposo = v[8];
      if(v[11]!=null) P.fc_max = v[11];
    }
    return p;
  }
  return out;
}

/* Elige el lector por el nombre o el contenido */
function leerArchivo(nombre, contenido){
  const ext=(nombre.match(/\.[^.]+$/)||[""])[0].toLowerCase();
  if(ext===".fit") return leerFIT(contenido);
  const txt = typeof contenido==="string" ? contenido : new TextDecoder().decode(contenido);
  if(ext===".gpx" || /<gpx\b/.test(txt.slice(0,2000))) return leerGPX(txt);
  if(ext===".tcx" || /<TrainingCenterDatabase\b/.test(txt.slice(0,2000))) return leerTCX(txt);
  if(ext===".xml" || /<HealthData\b/.test(txt.slice(0,5000))) return leerApple(txt);
  if(ext===".csv") return leerCSV(txt);
  throw new Error("Formato no reconocido. Sube un .FIT, .GPX, .TCX, .CSV o el export.xml de Apple Salud.");
}

/* ---------------------------------------------------------------- de actividades a métricas */
function metricasDeActividades(acts, hoy){
  const dl = f=>new Date(f+"T00:00:00");            /* medianoche local, no UTC */
  hoy = hoy ? dl(String(hoy).slice(0,10)) : dl(fechaLocal(new Date()));
  const m={}, dia=864e5;
  const car = acts.filter(a=>a.deporte==="carrera" && a.dist>=1000 && a.seg>0 && a.fecha);
  /* mejor 5 km: carreras de 4,5 a 25 km de los últimos 90 días, llevadas a 5 km */
  const rec = car.filter(a=>(hoy-dl(a.fecha))/dia<=90 && a.dist>=4500 && a.dist<=25000);
  if(rec.length) m.test_5k = mmss(Math.min(...rec.map(a=>a.dist>=4950&&a.dist<=5100? a.seg*5000/a.dist : equivalente5k(a.dist,a.seg))));
  /* km por semana: media de las últimas 4 semanas */
  const ult = car.filter(a=>{ const x=(hoy-dl(a.fecha))/dia; return x>=0 && x<28; });
  if(car.length) m.km_semana = r1(ult.reduce((s,a)=>s+a.dist,0)/1000/4);
  const fx = acts.map(a=>a.fc_max).filter(Boolean);
  if(fx.length) m.fc_max_observada = Math.max(...fx);
  const todas = acts.filter(a=>a.fecha).map(a=>dl(a.fecha)).sort((a,b)=>b-a);
  if(todas.length) m.semanas_parado = Math.max(0, Math.floor((hoy-todas[0])/dia/7));
  return m;
}

/* Junta varios archivos: si dos traen el mismo dato de perfil, gana el último que se sube; y las actividades se suman sin repetir */
function juntar(lecturas, hoy){
  const perfil={}, vistas=new Set(), acts=[];
  for(const l of lecturas){
    Object.assign(perfil, l.perfil);
    for(const a of l.actividades){ const k=a.fecha+"|"+Math.round(a.dist/100)+"|"+Math.round(a.seg/30); if(!vistas.has(k)){ vistas.add(k); acts.push(a); } }
  }
  const m = metricasDeActividades(acts, hoy);
  const fcm = m.fc_max_observada; delete m.fc_max_observada;
  if(fcm && !(perfil.fc_max >= fcm)) perfil.fc_max = fcm;
  return {datos:Object.assign(m, perfil), actividades:acts.length, sesiones:sesionesCalendario(acts)};
}

/* ---------------------------------------------------------------- calendario
   Sesiones del reloj listas para el calendario de entrenos: una por actividad, sin
   repetir, ordenadas por fecha. Con el mismo formato que la carrera del Registro
   (km y min) para que la vista las pueda juntar. No guarda nada: quien la use decide. */
function sesionesCalendario(acts){
  const vistas=new Set(), out=[];
  for(const a of acts){
    if(!a.fecha || !(a.seg>0)) continue;
    const k=a.fecha+"|"+a.deporte+"|"+Math.round(a.dist/100)+"|"+Math.round(a.seg/30);
    if(vistas.has(k)) continue; vistas.add(k);
    out.push({fecha:a.fecha, tipo:a.deporte, km: a.dist? r1(a.dist/1000) : null, min: r1(a.seg/60),
      fc_media:a.fc_media, origen:"reloj"});
  }
  return out.sort((x,y)=>x.fecha<y.fecha?-1:x.fecha>y.fecha?1:0);
}

/* Pasa las sesiones del reloj al formato de registro_v1 (menu/a6.js) sin tocarlo:
   devuelve solo las nuevas. Una carrera o una fuerza que ya esté apuntada a mano
   ese mismo día no se repite (manda lo de la app, que tiene los ejercicios).
   Quien la llame decide si las añade, después de preguntar al usuario. */
function aRegistro(sesiones, D){
  D = D || {sesiones:[], carrera:[]};
  const conFuerza = new Set((D.sesiones||[]).map(x=>x.fecha));
  const conCarrera = new Set((D.carrera||[]).map(x=>x.f));
  const out = {sesiones:[], carrera:[]};
  let id = Date.now();
  for(const x of sesiones){
    if(x.tipo==="carrera" && x.km>0){
      if(conCarrera.has(x.fecha)) continue;
      out.carrera.push({id:id++, f:x.fecha, tipo:"Rodaje", km:x.km, min:x.min, origen:"reloj"});
    } else if(x.tipo==="fuerza"){
      if(conFuerza.has(x.fecha)) continue;
      out.sesiones.push({id:id++, fecha:x.fecha, fase:null, dia:null, nombre:"Fuerza (reloj)",
        dur:Math.round(x.min*60), ej:[], abd:null, origen:"reloj"});
    }
  }
  return out;
}

/* ---------------------------------------------------------------- resolver métricas
   reloj: lo que salió de los archivos. manual: lo que escribió el usuario (manda sobre el reloj).
   Devuelve valores, de dónde sale cada uno y qué hay que pedir por pantalla. */
function resolver(reloj, manual){
  reloj = reloj||{}; manual = manual||{};
  const val={}, origen={};
  for(const M of METRICAS){
    const k=M.k;
    if(manual[k]!=null && manual[k]!==""){ val[k]=manual[k]; origen[k]="manual"; }
    else if(M.reloj && reloj[k]!=null){ val[k]=reloj[k]; origen[k]="reloj"; }
    if(val[k]!=null && M.min!=null) val[k]=num(val[k]);      /* «79,5» vale; «abc» queda NaN y se marca */
    if(val[k]!=null && M.u==="mm:ss") val[k]=String(val[k]).trim();
  }
  /* cálculos a partir de otras */
  if(val.fc_max==null && val.edad>=14 && val.edad<=90){ val.fc_max=Math.round(208-0.7*val.edad); origen.fc_max="calculado"; }
  if(val.vo2max==null && val.test_5k && /^\d{1,3}:[0-5]\d$/.test(val.test_5k)){ val.vo2max=r1(vdot(5000, seg(val.test_5k))); origen.vo2max="calculado"; }
  if(val.semanas_parado==null){ val.semanas_parado=0; origen.semanas_parado="supuesto"; }
  const pide = new Set(METRICAS.filter(M=>M.obl).map(M=>M.k));
  (NECESITA[val.objetivo]||[]).forEach(k=>pide.add(k));
  const faltan = METRICAS.filter(M=>pide.has(M.k) && val[M.k]==null).map(M=>M.k);
  const malas = METRICAS.filter(M=>{
    const x=val[M.k]; if(x==null || origen[M.k]==="calculado") return false;   /* solo se valida lo que viene de fuera */
    if(M.min!=null) return !(x>=M.min && x<=M.max);
    if(M.op) return M.op.indexOf(x)<0;
    if(M.u==="mm:ss") return !(/^\d{1,3}:[0-5]\d$/.test(x) && seg(x)>=600 && seg(x)<=5400);   /* 5 km entre 10 y 90 min */
    return false;
  }).map(M=>M.k);
  /* objetivos que se contradicen con el punto de partida */
  const bien = k=>val[k]!=null && malas.indexOf(k)<0;
  if(val.objetivo==="perder" && bien("peso") && bien("peso_objetivo") && val.peso_objetivo>=val.peso) malas.push("peso_objetivo");
  if(val.objetivo==="ganar"  && bien("peso") && bien("peso_objetivo") && val.peso_objetivo<=val.peso) malas.push("peso_objetivo");
  if(val.objetivo==="5k" && bien("test_5k") && bien("objetivo_5k") && seg(val.objetivo_5k)>=seg(val.test_5k)) malas.push("objetivo_5k");
  return {valores:val, origen, faltan, malas};
}

/* ---------------------------------------------------------------- viabilidad
   Ritmos máximos seguros (revisables con Backend). */
const RITMO = {perder:0.007, ganar:0.25, vdot:0.3, rearranque:4, minimo:4};
function viabilidad(v){
  const sem = v.dias_plan/7, motivos=[], alc={};
  let necesarias = 0;
  const rearr = (+v.semanas_parado||0) >= 4 ? RITMO.rearranque : 0;
  const util = Math.max(0, sem - rearr);
  if(v.objetivo==="5k"){
    const a=vdot(5000,seg(v.test_5k)), b=vdot(5000,seg(v.objetivo_5k));
    const n=Math.max(0,(b-a)/RITMO.vdot); necesarias=n;
    motivos.push("Bajar el 5 km de "+v.test_5k+" a "+v.objetivo_5k+" son "+r1(b-a).toString().replace(".",",")+" puntos de VDOT: unas "+Math.ceil(n)+" semanas.");
    alc.objetivo_5k = mmss(tiempoPara(a + RITMO.vdot*util, 5000));
  } else if(v.objetivo==="perder"){
    const kg=v.peso-v.peso_objetivo, n=Math.max(0,kg/(v.peso*RITMO.perder)); necesarias=n;
    motivos.push("Perder "+r1(kg).toString().replace(".",",")+" kg sin perder músculo lleva unas "+Math.ceil(n)+" semanas.");
    alc.peso_objetivo = r1(v.peso - v.peso*RITMO.perder*util);
  } else if(v.objetivo==="ganar"){
    const kg=v.peso_objetivo-v.peso, n=Math.max(0,kg/RITMO.ganar); necesarias=n;
    motivos.push("Ganar "+r1(kg).toString().replace(".",",")+" kg de músculo lleva unas "+Math.ceil(n)+" semanas.");
    alc.peso_objetivo = r1(v.peso + RITMO.ganar*util);
  }
  if(rearr) motivos.push("Llevas "+v.semanas_parado+" semanas parado: se suman "+rearr+" de rearranque.");
  const total = Math.max(RITMO.minimo, Math.ceil(necesarias + rearr));
  if(Math.ceil(necesarias + rearr) < RITMO.minimo) motivos.push("El plan más corto que tiene sentido son "+RITMO.minimo+" semanas.");
  const minDias = total*7;
  const ok = v.dias_plan >= minDias;
  return {ok, aviso: ok? null : AVISO_IMPOSIBLE, min_dias:minDias, motivos, alcanzable: ok? null : alc};
}

/* ---------------------------------------------------------------- todo junto */
function evaluar(reloj, manual){
  const r = resolver(reloj, manual);
  if(r.faltan.length || r.malas.length) return Object.assign(r, {estado:"faltan"});
  return Object.assign(r, {estado:"listo"}, {viabilidad: viabilidad(r.valores)});
}

/* ---------------------------------------------------------------- pulso por Bluetooth
   Perfil estándar Heart Rate (0x180D). Solo Chrome en Android y PC. Llama a cb(ppm). */
async function conectarPulso(cb){
  if(!(typeof navigator!=="undefined" && navigator.bluetooth)) throw new Error("Este navegador no puede leer el pulso por Bluetooth. Prueba con Chrome en Android o en el PC.");
  const dev = await navigator.bluetooth.requestDevice({filters:[{services:["heart_rate"]}]});
  const srv = await dev.gatt.connect();
  const car = await (await srv.getPrimaryService("heart_rate")).getCharacteristic("heart_rate_measurement");
  car.addEventListener("characteristicvaluechanged", e=>{
    const d=e.target.value, f=d.getUint8(0);
    cb(f & 1 ? d.getUint16(1,true) : d.getUint8(1));
  });
  await car.startNotifications();
  return ()=>{ try{ dev.gatt.disconnect(); }catch(e){} };
}

return {AVISO_IMPOSIBLE, MARCAS, METRICAS, NECESITA, RITMO,
  leerArchivo, leerFIT, leerGPX, leerTCX, leerCSV, leerApple,
  metricasDeActividades, juntar, sesionesCalendario, aRegistro, tipoSesion, resolver, viabilidad, evaluar, conectarPulso,
  vdot, tiempoPara, seg, mmss};
})();
if(typeof module!=="undefined") module.exports = Conectividad;
