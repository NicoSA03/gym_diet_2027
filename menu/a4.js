let fase = "F0", dia = 0;   // dia: 0-4 de lunes a viernes, -1 el fin de semana (descanso)

const el = (t,c,x)=>{const n=document.createElement(t); if(c)n.className=c;
  if(x!==undefined)n.textContent=x; return n;};
const guarda=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const lee=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
const TAG = {T1:"T1",T2:"T2",T3:"T3",TF:"Fijo"};

function estructura(nombre){
  const g = E.grupo[fase];
  const e = E.estructura[nombre];
  return (e && e[g]) || E.generico[g];
}

function pintaFases(){
  const box = document.getElementById("fases");
  box.replaceChildren();
  Object.keys(E.fases).forEach(k=>{
    const c = el("button","chip", k.replace(/^F/,"B")+": "+E.fases[k].n);
    c.setAttribute("role","tab");
    c.setAttribute("aria-selected", k===fase?"true":"false");
    c.addEventListener("click", ()=>{ fase=k; guarda("e_fase",k); render(); });
    box.append(c);
  });
  const f = E.fases[fase];
  document.getElementById("f-n").textContent = f.lema;
  document.getElementById("f-f").textContent =
    "Semanas " + f.s0 + "-" + f.s1;
}

function pintaDias(){
  const box = document.getElementById("dias");
  box.replaceChildren();
  E.dias.forEach((d,i)=>{
    const b = el("button","dia-btn");
    b.setAttribute("role","tab");
    b.setAttribute("aria-selected", i===dia?"true":"false");
    b.append(el("span",null,d.dia.slice(0,3)),
             el("small",null, d.tipo==="fuerza" ? d.n : "Carrera"));
    b.addEventListener("click", ()=>{ dia=i; render(); });
    box.append(b);
  });
  const fin = document.getElementById("finde");
  fin.setAttribute("aria-selected", dia<0 ? "true":"false");
  fin.onclick = ()=>{ dia=-1; render(); };
}

function pintaSesion(){
  const box = document.getElementById("sesion");
  box.replaceChildren();
  if(dia < 0){
    const w = (new Date().getDay()+6)%7;
    const c = el("div","descanso");
    c.append(el("h3",null, w>=5 ? "Hoy descanso" : "Fin de semana, descanso"));
    box.append(c);
    return;
  }
  const d = E.dias[dia], f = E.fases[fase];

  const top = el("div","ses-top");
  const izq = el("div");
  izq.append(el("h3",null, d.dia + ": " + d.n), el("p","sub", d.sub));
  top.append(izq, el("span","dur", d.cod==="J" ? f.largo[0]+"-"+f.largo[1]+" min" : d.dur));
  box.append(top);
  const marca = marcaVigente();
  if(marca) box.append(el("p","ses-marca", (marca==="reentrada" ? "Reentrada" : "Repetir cargas")+": no subas peso, una serie menos, RIR +1."));

  if(d.cal.length){
    const c = el("div","cal-box");
    c.append(el("h5",null, d.cod==="J" ? "Antes de salir" : "Calentamiento"));
    const ul = el("ul");
    d.cal.forEach(x=>ul.append(el("li",null,x)));
    c.append(ul);
    box.append(c);
  }

  if(d.tipo==="fuerza"){
    d.ej.forEach(([tier,nombre])=>{
      const ej = E.ej[nombre], es = estructura(nombre);
      const p0 = f.esquema[tier];
      const p = marca ? [Math.max(1, p0[0]-1), p0[1], String(p0[2]).replace(/\d+/g, n=>String(+n+1))] : p0;
      const row = el("div","ejer");
      const fila = el("div","fila");
      fila.append(el("span","t "+tier.toLowerCase(), TAG[tier]), el("h4",null,nombre));
      const pres = el("div","pres", p[0]+" × "+p[1]);
      pres.append(el("small",null,p[2]));
      fila.append(pres);
      row.append(fila, el("p","cue", ej.cue));
      const est = el("div","est");
      est.append(el("b",null,es[0]), document.createTextNode(es[1]));
      row.append(est);
      if(ej.gif) row.append(comoSeHace(nombre, ej.gif));
      box.append(row);
    });
    if(d.tabata){
      const t = E.tabata[d.tabata];
      const c = el("div","tab");
      c.append(el("span","reloj","Abdominales, tabata 20-20, "+t.dur), el("h5",null,t.n));
      [["1, 3, 5, 7",t.a],["2, 4, 6, 8",t.b]].forEach(([k,par])=>{
        const p = el("div","par");
        p.append(el("span","k",k));
        const txt = el("div");
        txt.append(el("b",null,par[0]+". "), document.createTextNode(par[1]));
        p.append(txt);
        c.append(p);
      });
      const como = el("div","como");
      como.append(el("i",null,"Cómo se sube"));
      t.sube.forEach(([n,s])=>{
        const l = el("div");
        l.append(el("b",null,n+": "), document.createTextNode(s));
        como.append(l);
      });
      if(t.regla) como.append(el("div","regla",t.regla));
      c.append(como);
      box.append(c);
    }
  } else {
    const c = el("div","carrera-caja");
    c.append(el("p","ppal", d.cod==="M" ? f.mar : f.jue));
    c.append(el("p","nota", d.cod==="M"
      ? "Diez minutos de trote suave antes de la primera serie. A las siete de la mañana no es opcional."
      : "Toda en Z2: si no puedes hablar frases completas, vas demasiado rápido."));
    box.append(c);
  }
  if(d.nota) box.append(el("p","ses-nota", d.nota));
}

// «Cómo se hace» (v2.2): animación del ejercicio, plegada. La imagen solo se pide
// a ExerciseDB cuando la abres, así no gasta datos ni hace la página más lenta.
function comoSeHace(nombre, gif){
  const d = el("details","gif-ej");
  d.append(el("summary",null,"Cómo se hace"));
  d.addEventListener("toggle", ()=>{
    if(!d.open || d.dataset.cargado) return;
    d.dataset.cargado = "1";
    const img = new Image(180, 180);
    img.alt = "Animación de " + nombre.toLowerCase();
    img.decoding = "async";
    img.onerror = ()=>img.replaceWith(el("p","gif-err","No se ha podido cargar la animación: hace falta internet."));
    img.src = E.gif_url + gif + ".gif";
    d.append(img);
  });
  return d;
}

function pintaZonas(){
  const box = document.getElementById("zmini");
  box.replaceChildren();
  E.zonas.forEach(([z,a,b])=>{
    const d = el("div");
    d.append(el("span","z",z.split(": ")[1]), el("span","r",a+"-"+b),
             el("span","z",z.split(": ")[0]));
    box.append(d);
  });
}

function pintaKm(){
  const f = E.fases[fase];
  const box = document.getElementById("kmline");
  box.replaceChildren();
  const max = Math.max.apply(null, f.km);
  box.style.gridTemplateColumns = "repeat(" + f.km.length + ", 1fr)";
  f.km.forEach((k,i)=>{
    const col = el("div","col");
    col.append(el("span","n",String(k)));
    const bar = el("div","bar"+(f.des.indexOf(i+1)>=0 ? " des":""));
    bar.style.height = Math.round(14 + 80*(k/max)) + "px";
    col.append(bar, el("span","s","s"+(f.s0+i)));
    box.append(col);
  });
  document.getElementById("km-tope").textContent = max + " km en la semana tope";
}

function pintaVariantes(){
  const box = document.getElementById("variantes");
  if(box.childElementCount) return;
  E.variantes.forEach(v=>{
    const d = el("details","varcard");
    const s = el("summary");
    s.append(el("span",null,v.n), el("span","tag", v.dias+", "+v.dur));
    d.append(s);
    const c = el("div","cuerpo");
    c.append(el("p","cuando",v.cuando), el("p",null,v.regla));
    v.detalle.forEach(([t,x])=>{
      const s2 = el("div","ses-v");
      s2.append(el("h5",null,t), el("p",null,x));
      c.append(s2);
    });
    c.append(el("p","conserva",v.conserva));
    d.append(c);
    box.append(d);
  });
}

// ---------------------------------------------------------------- v2.6: pregunta diaria, avisos y calendario
// Lo que se apunta aquí vive en registro_v1 (claves dias, ajustes, descartes y plazos_desde).
// Nunca se reescribe lo que ya había: se lee el registro, se cambia una clave y se guarda.
// La cuenta la hace PLAZOS (menu/plazos.js); aquí solo se pregunta, se pinta y se guarda.
const KEY_REG = "registro_v1", KEY_DIARIO = "diario_v1";
const MES_L = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];
const MES_C = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
const DIA_L = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"];
const TIPOS_ACT = [["caminar","Caminar"],["carrera","Carrera"],["bici","Bici"],["fuerza","Fuerza"],["natacion","Natación"],["deporte","Deporte"],["otro","Otro"]];
const INTS_ACT = [["suave","Suave"],["media","Media"],["alta","Alta"]];
const PLAN_E = {dias: E.dias.map(d=>({cod:d.cod, n:d.n, tipo:d.tipo}))};
const z2 = n=>String(n).padStart(2,"0");
const isoF = d=>d.getFullYear()+"-"+z2(d.getMonth()+1)+"-"+z2(d.getDate());
const deIso = s=>{ const [a,m,d]=s.split("-").map(Number); return new Date(a,m-1,d); };
const hoy = ()=>isoF(new Date());
const sumaDias = (s,n)=>{ const d=deIso(s); d.setDate(d.getDate()+n); return isoF(d); };
const lunesDe = s=>{ const d=deIso(s); d.setDate(d.getDate()-(d.getDay()+6)%7); return isoF(d); };
const cortaF = s=>{ const d=deIso(s); return d.getDate()+" "+MES_C[d.getMonth()]; };
const nfe = n=>Math.round(n).toLocaleString("es-ES");
const esFecha = s=>typeof s==="string" && /^\d{4}-\d{2}-\d{2}$/.test(s);
const idxDia = cod=>E.dias.findIndex(x=>x.cod===cod);

function leeJ(k){ try{ const t=localStorage.getItem(k); if(t){ const d=JSON.parse(t); if(d) return d; } }catch(e){} return null; }
function leeReg(){ const d = leeJ(KEY_REG); return d && d.v===1 ? d : null; }
function regVacio(){ return {v:1, inicio:null, sesiones:[], peso:[], carrera:[], activa:null}; }
// true si hay algo guardado en registro_v1 que no es un registro v1 legible
function registroIlegible(){
  try{ const t = localStorage.getItem(KEY_REG); if(!t) return false; const d = JSON.parse(t); return !(d && d.v===1); }catch(e){ return true; }
}
let silencio = false;
// Guarda el registro entero y avisa a Registro (que lo recarga) y a Menús (que repinta).
// No escribe si lo que hay guardado no es un registro v1 que se pueda leer.
function guardaReg(r){
  try{
    const crudo = localStorage.getItem(KEY_REG);
    if(crudo){ let p = null; try{ p = JSON.parse(crudo); }catch(e){} if(!p || p.v!==1) return false; }
    localStorage.setItem(KEY_REG, JSON.stringify(r));
  }catch(e){ return false; }
  silencio = true;
  try{ window.dispatchEvent(new CustomEvent("gd:registro")); window.dispatchEvent(new CustomEvent("gd:plazos")); }
  finally{ silencio = false; }
  return true;
}
const desdeDe = r=>(r && esFecha(r.plazos_desde)) ? r.plazos_desde : hoy();

// Semana vigente con marca de repetir o de reentrada (no se sube carga, una serie menos, RIR +1)
function marcaVigente(){
  const r = leeReg(); if(!r || !Array.isArray(r.ajustes)) return null;
  const lun = lunesDe(hoy()); let m = null;
  r.ajustes.forEach(a=>{
    if(a && !a.deshecho && (a.que==="repetir" || a.que==="reentrada") && esFecha(a.f) && lunesDe(a.f)===lun)
      if(!m || a.que==="reentrada") m = a.que;
  });
  return m;
}

// ---- pregunta diaria
let editandoQ = false, subQ = null;
function textoDia(d){
  if(d.modo==="descanso") return "Descanso";
  if(d.modo==="otra" && d.act) return (d.act.nombre || "Otra actividad")+", "+d.act.min+" min";
  const i = idxDia(d.sesion);
  return i>=0 ? E.dias[i].n : "Descanso";
}
function guardaDia(d){
  const r = leeReg() || regVacio(), h = hoy();
  r.dias = (r.dias && typeof r.dias==="object") ? r.dias : {};
  r.dias[h] = Object.assign({modo:"plan", sesion:null, act:null}, d, {t:Date.now()});
  if(!esFecha(r.plazos_desde)) r.plazos_desde = h;
  if(!guardaReg(r)) return false;
  editandoQ = false; subQ = null;
  const i = idxDia(d.sesion); if(i>=0) dia = i;
  render();
  return true;
}
function pintaPregunta(){
  const box = document.getElementById("hoyq"); box.replaceChildren();
  if(registroIlegible()){ box.append(el("p","hq-err","No se puede leer el registro: no se guarda nada.")); return; }
  const r = leeReg(), h = hoy(), d = r && r.dias && r.dias[h];
  const w = (new Date().getDay()+6)%7, cod = w<5 ? E.dias[w].cod : null;
  if(d && d.modo && !editandoQ){
    const f = el("div","hq-lin");
    f.append(el("span","et","Hoy"), el("b",null,textoDia(d)));
    const b = el("button","hq-btn","Cambiar");
    b.addEventListener("click", ()=>{ editandoQ = true; subQ = d.modo==="otro_plan" ? "otro" : d.modo==="otra" ? "otra" : null; pintaPregunta(); });
    f.append(b); box.append(f); return;
  }
  const c = el("div","hq");
  c.append(el("h3",null,"¿Qué vas a hacer hoy?"));
  const ops = el("div","hq-ops");
  const op = (txt, sub, activo, fn)=>{
    const b = el("button","hq-op"); b.type = "button"; b.append(document.createTextNode(txt));
    if(sub) b.append(el("small",null,sub));
    b.setAttribute("aria-pressed", activo ? "true":"false");
    b.addEventListener("click", fn); ops.append(b);
  };
  const m = d && d.modo;
  op("Lo que toca", cod ? E.dias[w].n : "Fin de semana", m==="plan", ()=>guardaDia({modo:"plan", sesion:cod}));
  op("Otro entreno", "del plan", subQ==="otro" || m==="otro_plan", ()=>{ subQ = "otro"; pintaPregunta(); });
  op("Otra actividad", null, subQ==="otra" || m==="otra", ()=>{ subQ = "otra"; pintaPregunta(); });
  op("Descanso", null, m==="descanso", ()=>guardaDia({modo:"descanso", sesion:null}));
  c.append(ops);
  if(subQ==="otro"){
    const ch = el("div","hq-chips");
    E.dias.forEach(x=>{
      const b = el("button","chip",x.n); b.type = "button";
      b.setAttribute("aria-selected", d && d.modo==="otro_plan" && d.sesion===x.cod ? "true":"false");
      b.addEventListener("click", ()=>guardaDia({modo:"otro_plan", sesion:x.cod}));
      ch.append(b);
    });
    c.append(ch);
  }
  if(subQ==="otra") c.append(formActividad(d && d.modo==="otra" ? d.act : null));
  if(editandoQ){
    const x = el("button","hq-btn","Dejarlo como está"); x.type = "button";
    x.addEventListener("click", ()=>{ editandoQ = false; subQ = null; pintaPregunta(); });
    c.append(x);
  }
  box.append(c);
}
function formActividad(act){
  const f = el("div","hq-form");
  const campo = (txt, nodo, cl)=>{ const l = el("label",cl||null,txt); l.append(nodo); f.append(l); return nodo; };
  const nom = el("input"); nom.type = "text"; nom.maxLength = 30; nom.placeholder = "Qué haces"; nom.value = (act && act.nombre) || "";
  campo("Nombre", nom, "full");
  const tipo = el("select");
  TIPOS_ACT.forEach(([v,t])=>{ const o = el("option",null,t); o.value = v; tipo.append(o); });
  tipo.value = (act && act.tipo) || "caminar";
  campo("Tipo", tipo);
  const min = el("input"); min.type = "text"; min.inputMode = "numeric"; min.placeholder = "min"; min.value = act && act.min ? String(act.min) : "";
  campo("Minutos", min);
  let inten = (act && act.int) || "media";
  const seg = el("div","hq-seg");
  const pinta = ()=>seg.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed", b.dataset.v===inten ? "true":"false"));
  INTS_ACT.forEach(([v,t])=>{
    const b = el("button","hq-op",t); b.type = "button"; b.dataset.v = v; b.style.minHeight = "44px";
    b.addEventListener("click", ()=>{ inten = v; pinta(); }); seg.append(b);
  });
  pinta();
  const l = el("label","full","Intensidad"); l.append(seg); f.append(l);
  const ok = el("button","hq-btn prim","Guardar"); ok.type = "button"; ok.style.gridColumn = "1/-1";
  const err = el("p","nota"); err.style.gridColumn = "1/-1"; err.hidden = true;
  ok.addEventListener("click", ()=>{
    const mm = parseInt(min.value, 10);
    if(!(mm>0 && mm<=600)){ err.textContent = "Pon los minutos."; err.hidden = false; return; }
    const lbl = TIPOS_ACT.find(x=>x[0]===tipo.value)[1];
    guardaDia({modo:"otra", sesion:null, act:{nombre: nom.value.trim() || lbl, tipo:tipo.value, min:mm, int:inten}});
  });
  f.append(err, ok);
  return f;
}

// ---- avisos de reajuste
let hechos = [];   // avisos aplicados en esta visita: se pueden deshacer desde su tarjeta
function claveAviso(p){
  // recuperar lleva la sesión perdida (va en su texto): mañana no repite el mismo aviso
  return p.tipo==="recuperar" ? "recuperar|"+p.texto : p.tipo+"|"+lunesDe(hoy());
}
function propuestas(r){
  const h = hoy(), des = desdeDe(r), out = [];
  try{
    // primero la del día (reentrada o recuperar) y luego la de la semana (repetir o alargar)
    [PLAZOS.propuestaDia(r, h, PLAN_E, des), PLAZOS.propuestaSemana(r, h, PLAN_E, des)].forEach(p=>{
      if(p && !(r.descartes && r.descartes[claveAviso(p)])) out.push(p);
    });
  }catch(e){}
  return out;
}
function tarjetaAviso(texto, hecho, botones){
  const c = el("div","avi"+(hecho ? " hecho" : ""));
  c.append(el("p",null,texto));
  const f = el("div","hq-fila");
  botones.forEach(([t,fn,prim])=>{ const b = el("button","hq-btn"+(prim?" prim":""),t); b.type = "button"; b.addEventListener("click", fn); f.append(b); });
  c.append(f);
  return c;
}
function pintaAvisos(){
  const box = document.getElementById("avisos"); box.replaceChildren();
  const r = leeReg(); if(!r) return;
  // una tarjeta aplicada solo vale mientras su ajuste siga activo (se puede deshacer desde el calendario)
  const h0 = hoy();
  hechos = hechos.filter(x=>Array.isArray(r.ajustes) && r.ajustes.some(a=>a && !a.deshecho && a.que===x.tipo && a.f===h0));
  hechos.forEach(x=>{
    box.append(tarjetaAviso(x.texto, true, [["Deshacer", ()=>{
      const r2 = leeReg(); if(!r2) return;
      let n; try{ n = x.prop.deshacer(r2); }catch(e){ return; }
      if(guardaReg(n)){ hechos = hechos.filter(y=>y!==x); render(); }
    }]]));
  });
  const p = propuestas(r)[0];
  if(!p) return;
  box.append(tarjetaAviso(p.texto, false, [
    ["Aplicar", ()=>{
      const r2 = leeReg(); if(!r2) return;
      let n; try{ n = p.aplicar(r2); }catch(e){ return; }
      if(guardaReg(n)){
        hechos.push({texto:p.texto, tipo:p.tipo, prop:p});
        const dd = n.dias && n.dias[hoy()]; const i = dd ? idxDia(dd.sesion) : -1; if(i>=0) dia = i;
        render();
      }
    }, true],
    ["Dejar como está", ()=>{
      const r2 = leeReg(); if(!r2) return;
      r2.descartes = (r2.descartes && typeof r2.descartes==="object") ? r2.descartes : {};
      r2.descartes[claveAviso(p)] = true;
      if(guardaReg(r2)) render();
    }]
  ]));
}

// ---- calendario
let calMes = null, calSel = null;
function mesDeHoy(){ const d = new Date(); return {a:d.getFullYear(), m:d.getMonth()}; }
// Cuántas series cuenta una sesión de fuerza; las del reloj traen ej vacío
const serieN = s=>(Array.isArray(s.ej) ? s.ej : []).reduce((n,e)=>n+(Array.isArray(e && e.series) ? e.series.filter(x=>x && x.tipo!=="C").length : 0), 0);
function semanaCiclo(lun, r){
  if(!r || !esFecha(r.inicio)) return null;
  const w = Math.round((deIso(lun)-deIso(lunesDe(r.inicio)))/6048e5) + 1;
  const ks = Object.keys(E.fases);
  const k = ks.find(x=>w>=E.fases[x].s0 && w<=E.fases[x].s1);
  return k ? k.replace(/^F/,"B")+", sem "+w : null;
}
// Kcal extra de los avisos de peso aplicados y no deshechos, desde el día en que se aplicaron
function extraDesde(r, bloque, f){
  return (Array.isArray(r.ajustes) ? r.ajustes : []).reduce((s,a)=>
    (a && !a.deshecho && a.que==="kcal" && a.bloque===bloque && typeof a.f==="string" && a.f<=f && a.antes && a.despues) ? s+(a.despues.kcal-a.antes.kcal) : s, 0);
}
function kcTipo(fase, tipo){ const o = MO.obj[fase+"|"+tipo], t = MO.tipos[tipo]; return o && t ? t.tomas.reduce((a,b)=>a+(o[b]?o[b][0]:0), 0) : 0; }
// Sesión prevista cuando el tipo del día se cambió a mano en Menús (undefined = la que toca por fecha). Igual que en a2.js
function sesionDeTipo(t, f){
  const wd = deIso(f).getDay();
  if(t === ({1:"A",2:"B",3:"A",4:"B",5:"C",6:"D",0:"E"})[wd]) return undefined;
  const nat = ["L","M","X","J","V"][(wd+6)%7];
  return t==="A" ? (nat==="L"||nat==="X" ? nat : "L") : t==="B" ? (nat==="M"||nat==="J" ? nat : "M") : t==="C" ? "V" : null;
}
function pesoDe(r, f){ let p = null; (Array.isArray(r.peso) ? r.peso : []).forEach(x=>{ if(x && x.f<=f && (!p || x.f>p.f)) p = x; }); return p ? p.kg : 0; }
// Dieta del día según el diario de Menús: {estado, kc, obj, p, objP} o null.
// El objetivo es el mismo que ve Menús: kcal extra del bloque y, hoy, el factor de lo que vas a hacer
// (se aplica a las tomas por comer y a las comidas después de elegirlo).
function dietaDe(f, h, ctx){
  const d = ctx.diario && ctx.diario.dias && ctx.diario.dias[f];
  if(!d || !d.tomas) return null;
  try{
    let kc = 0, p = 0, n = 0;
    Object.keys(d.tomas).forEach(b=>{ const t = d.tomas[b]; if(t && t.ok && Array.isArray(t.m)){ n++; kc += t.m[0]||0; p += t.m[1]||0; } });
    const tipo = MO.tipos[d.tipo], tablaO = MO.obj[d.fase+"|"+d.tipo];
    if(!n || !tipo || !tablaO) return null;
    const base0 = kcTipo(d.fase, d.tipo), ex = extraDesde(ctx.r, d.fase, f);
    const k = base0 > 0 && ex ? (base0+ex)/base0 : 1;
    let fac = 1;
    if(ctx.r.dias && ctx.r.dias[f]){
      try{
        const plan = {kcal:base0+ex, kcalE:kcTipo(d.fase,"E")+ex, kcalD:kcTipo(d.fase,"D")+ex};
        const ses = sesionDeTipo(d.tipo, f); if(ses !== undefined) plan.sesion = ses;
        const a = PLAZOS.dietaDelDia(ctx.r, f, plan, pesoDe(ctx.r, f)); if(a && a.factor) fac = a.factor;
      }catch(e){}
    }
    const t0 = fac!==1 ? (ctx.r.dias[f].t || 0) : 0;
    let obj = 0, objP = 0, todas = true;
    tipo.tomas.forEach(b=>{
      const o = tablaO[b], t = d.tomas[b], ok = !!(t && t.ok);
      if(o){ const q = (fac!==1 && (!ok || (t.h>0 && t0>0 && t.h>t0))) ? k*fac : k; obj += o[0]*q; objP += o[1]*q; }
      if(!ok) todas = false;
    });
    if(!(obj > 0)) return null;
    if(!(f < h || (f===h && todas))) return {estado:null, kc, obj, p, objP};
    const dentro = Math.abs(kc-obj) <= Math.max(0.05*obj, 25);
    return {estado: dentro ? "ok" : kc < obj ? "corta" : "pasada", kc, obj, p, objP};
  }catch(e){ return null; }
}
function contexto(r){
  const ctx = {r, ses:{}, car:{}, adh:{}, diario:leeJ(KEY_DIARIO)};
  (Array.isArray(r.sesiones) ? r.sesiones : []).forEach(s=>{ if(s && esFecha(s.fecha)) (ctx.ses[s.fecha] = ctx.ses[s.fecha] || []).push(s); });
  (Array.isArray(r.carrera) ? r.carrera : []).forEach(c=>{ if(c && esFecha(c.f)) (ctx.car[c.f] = ctx.car[c.f] || []).push(c); });
  return ctx;
}
function adhDe(lun, ctx){
  if(!ctx.adh[lun]){ try{ ctx.adh[lun] = PLAZOS.adherencia(ctx.r, lun, PLAN_E); }catch(e){ ctx.adh[lun] = {detalle:[]}; } }
  return ctx.adh[lun];
}
function marcasDia(f, h, ctx){
  const r = ctx.r, dd = r.dias && r.dias[f];
  const k = (deIso(f).getDay()+6)%7;
  const m = {fuerza:!!ctx.ses[f], carrera:!!ctx.car[f], otra: !!(dd && dd.modo==="otra" && dd.act), descanso: !!(dd && dd.modo==="descanso"),
             falta:false, prev:null, ajuste:false, dieta:dietaDe(f, h, ctx)};
  const hecho = m.fuerza || m.carrera || m.otra;
  if(k<5 && !hecho && !m.descanso){
    if(f >= h) m.prev = E.dias[k].tipo==="carrera" ? "pc" : "pf";
    else if(esFecha(r.inicio)){
      const det = adhDe(lunesDe(f), ctx).detalle[k];
      if(det && det.prevista && det.valor===0) m.falta = true;
    }
  }
  m.ajuste = Array.isArray(r.ajustes) && r.ajustes.some(a=>a && a.f===f && !a.deshecho);
  return m;
}
const ETQ_AJ = {alargar:"Bloque alargado", recuperar:"Sesión recuperada", reentrada:"Reentrada", repetir:"Repetir cargas", kcal:"kcal del bloque"};
function pintaCalendario(){
  const box = document.getElementById("calen-cuerpo"); box.replaceChildren();
  if(!document.getElementById("calen").open) return;
  const r = leeReg() || regVacio(), h = hoy(), ctx = contexto(r);
  if(!calMes) calMes = mesDeHoy();
  if(!calSel) calSel = h;
  const cab = el("div","cal-cab");
  const mv = (n)=>{ const d = new Date(calMes.a, calMes.m+n, 1); calMes = {a:d.getFullYear(), m:d.getMonth()}; pintaCalendario(); };
  const ant = el("button",null,"‹"); ant.type = "button"; ant.setAttribute("aria-label","Mes anterior"); ant.addEventListener("click", ()=>mv(-1));
  const sig = el("button",null,"›"); sig.type = "button"; sig.setAttribute("aria-label","Mes siguiente"); sig.addEventListener("click", ()=>mv(1));
  cab.append(ant, el("b",null,MES_L[calMes.m]+" "+calMes.a), sig);
  box.append(cab);
  const g = el("div","cal-grid");
  ["L","M","X","J","V","S","D"].forEach(x=>g.append(el("span","cal-dow",x)));
  const primero = isoF(new Date(calMes.a, calMes.m, 1)), ultimo = isoF(new Date(calMes.a, calMes.m+1, 0));
  for(let lun = lunesDe(primero); lun <= ultimo; lun = sumaDias(lun, 7)){
    const et = semanaCiclo(lun, r);
    if(et) g.append(el("span","cal-sem",et));
    for(let i=0;i<7;i++){
      const f = sumaDias(lun, i), m = marcasDia(f, h, ctx);
      const b = el("button","cal-d"+(deIso(f).getMonth()!==calMes.m ? " fuera":"")+(f===h ? " hoy":"")+(f===calSel ? " sel":""));
      b.type = "button"; b.append(document.createTextNode(String(deIso(f).getDate())));
      const pts = el("span","cal-pts");
      if(m.fuerza) pts.append(el("i","cal-pt f"));
      if(m.carrera) pts.append(el("i","cal-pt c"));
      if(m.otra) pts.append(el("i","cal-pt o"));
      if(m.falta) pts.append(el("i","cal-pt x"));
      if(m.prev) pts.append(el("i","cal-pt "+m.prev));
      b.append(pts);
      if(m.dieta && m.dieta.estado) b.append(el("i","cal-dieta "+m.dieta.estado));
      if(m.ajuste) b.append(el("i","cal-aj"));
      b.setAttribute("aria-label", DIA_L[i]+" "+cortaF(f));
      b.addEventListener("click", ()=>{ calSel = f; pintaCalendario(); });
      g.append(b);
    }
  }
  box.append(g);
  const ley = el("div","cal-leyenda");
  [["f","Fuerza"],["c","Carrera"],["o","Otra"],["x","No hecha"]].forEach(([c,t])=>{ const s = el("span"); s.append(el("i","cal-pt "+c), document.createTextNode(t)); ley.append(s); });
  box.append(ley);
  box.append(detalleDia(calSel, r, h, ctx));
}
function detalleDia(f, r, h, ctx){
  const c = el("div","cal-det"), m = marcasDia(f, h, ctx), k = (deIso(f).getDay()+6)%7;
  c.append(el("h5",null,DIA_L[k]+" "+cortaF(f)));
  let n = 0;
  const linea = t=>{ c.append(el("p",null,t)); n++; };
  (ctx.ses[f]||[]).forEach(s=>{
    const ns = serieN(s);
    linea("Fuerza: "+(s.nombre || "sesión")+(ns ? ", "+ns+(ns===1 ? " serie" : " series") : "")+(s.origen==="reloj" ? ", reloj" : ""));
  });
  (ctx.car[f]||[]).forEach(x=>linea("Carrera: "+(x.km!=null ? String(x.km).replace(".",",")+" km" : "")+(x.min!=null ? ", "+Math.round(x.min)+" min" : "")+(x.origen==="reloj" ? ", reloj" : "")));
  const dd = r.dias && r.dias[f];
  if(dd && dd.modo==="otra" && dd.act) linea("Otra: "+(dd.act.nombre||"actividad")+", "+dd.act.min+" min, "+dd.act.int);
  if(dd && dd.modo==="descanso") linea("Descanso");
  if(m.falta) linea("Tocaba "+E.dias[k].n+" y no se hizo.");
  if(m.dieta){
    linea("Dieta: "+nfe(m.dieta.kc)+" de "+nfe(m.dieta.obj)+" kcal, proteína "+nfe(m.dieta.p)+" de "+nfe(m.dieta.objP)+" g"+
          (m.dieta.estado ? ", "+({ok:"cumplida", corta:"corta", pasada:"pasada"})[m.dieta.estado] : ""));
  }
  if(Array.isArray(r.ajustes)) r.ajustes.forEach((a, i)=>{
    if(!a || a.f!==f) return;
    const fila = el("div","fila");
    fila.append(el("p",null,"Ajuste: "+(ETQ_AJ[a.que]||a.que)+(a.deshecho ? ", deshecho" : "")));
    if(!a.deshecho){
      const b = el("button","hq-btn","Deshacer"); b.type = "button";
      b.addEventListener("click", ()=>{
        const r2 = leeReg(); if(!r2) return;
        let nr; try{ nr = PLAZOS.deshacerAjuste(r2, i); }catch(e){ return; }
        if(guardaReg(nr)) render();
      });
      fila.append(b);
    }
    c.append(fila); n++;
  });
  if(!n) c.append(el("p",null,"Sin registro."));
  return c;
}
document.getElementById("calen").addEventListener("toggle", pintaCalendario);

function pintaV26(){
  try{ pintaPregunta(); pintaAvisos(); pintaCalendario(); }catch(e){ if(window.console) console.error(e); }
}
// Si Registro o Menús cambian algo (un entreno, el peso), se repinta aquí
window.addEventListener("gd:peso", ()=>{ if(!silencio) pintaV26(); });
window.addEventListener("gd:registro", ()=>{ if(!silencio) pintaV26(); });

function render(){ pintaFases(); pintaDias(); pintaSesion(); pintaKm(); pintaV26(); }

// Al abrir: el día de hoy (sábado y domingo, descanso) y el bloque que toca hoy
// según la fecha de inicio del Registro (misma cuenta que menu/a6.js). Sin fecha
// o fuera del ciclo, el bloque que dejaste elegido a mano.
function faseDeHoy(){
  const t = lee("registro_v1"); if(!t) return null;
  const ini = JSON.parse(t).inicio;
  if(!/^\d{4}-\d{2}-\d{2}$/.test(ini||"")) return null;
  const lun = d=>{ const x=new Date(d.getFullYear(),d.getMonth(),d.getDate()); x.setDate(x.getDate()-(x.getDay()+6)%7); return x.getTime(); };
  const [a,m,d] = ini.split("-").map(Number);
  const w = Math.round((lun(new Date())-lun(new Date(a,m-1,d)))/6048e5) + 1;
  const ks = Object.keys(E.fases);
  if(w < 1) return ks[0];
  return ks.find(k=>w>=E.fases[k].s0 && w<=E.fases[k].s1) || null;
}
try{
  const f = lee("e_fase"); if(f && E.fases[f]) fase = f;
}catch(e){}
try{ const h = faseDeHoy(); if(h) fase = h; }catch(e){}
{ const w = (new Date().getDay()+6)%7; dia = w < 5 ? w : -1;
  try{ const r = leeReg(), d = r && r.dias && r.dias[hoy()]; const i = d && (d.modo==="plan" || d.modo==="otro_plan") ? idxDia(d.sesion) : -1; if(i>=0) dia = i; }catch(e){} }
pintaZonas(); pintaVariantes(); render();
