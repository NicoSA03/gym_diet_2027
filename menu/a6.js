// Registro al estilo Hevy. Los datos del plan (R) los genera menu/payload_registro.py;
// aquí solo se pinta, se guarda en el navegador y se dibujan las gráficas.
const KEY = "registro_v1";
const MES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
const CHECK = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
const RELOJ = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9.5 2.5h5"/></svg>';

const el = (t,c,x)=>{const n=document.createElement(t); if(c)n.className=c; if(x!==undefined)n.textContent=x; return n;};
const nf = (n,d)=>Number(n).toLocaleString("es-ES",{maximumFractionDigits:d===undefined?1:d});
const num = v=>{ const x=parseFloat(String(v).replace(",",".")); return isFinite(x)?x:null; };

// ---------------------------------------------------------------- almacenamiento
function vacio(){ return {v:1, sesiones:[], peso:[], carrera:[], activa:null}; }
function cargaDatos(){
  try{ const t=localStorage.getItem(KEY); if(t){ const d=JSON.parse(t); if(d && d.v===1) return Object.assign(vacio(), d); } }catch(e){}
  return vacio();
}
let D = cargaDatos();
function guarda(){
  try{ localStorage.setItem(KEY, JSON.stringify(D)); }
  catch(e){ aviso("No se ha podido guardar: el navegador tiene el almacenamiento lleno o bloqueado."); }
}
let avisoT = null;
function aviso(txt){
  const a = document.getElementById("r-aviso");
  a.textContent = txt; a.hidden = false;
  clearTimeout(avisoT); avisoT = setTimeout(()=>{ a.hidden = true; }, 2600);
}

// ---------------------------------------------------------------- fechas
const z2 = n=>String(n).padStart(2,"0");
const iso = d=>d.getFullYear()+"-"+z2(d.getMonth()+1)+"-"+z2(d.getDate());
const hoy = ()=>iso(new Date());
const deIso = s=>{ const [a,m,d]=s.split("-").map(Number); return new Date(a,m-1,d); };
const corta = s=>{ const d=deIso(s); return d.getDate()+" "+MES[d.getMonth()]; };
const lunes = s=>{ const d=deIso(s); d.setDate(d.getDate()-(d.getDay()+6)%7); return iso(d); };
function faseDe(s){
  const ks = Object.keys(R.fases);
  for(const k of ks){ const f=R.fases[k]; if(s>=f.ini && s<=f.fin) return k; }
  return s < R.fases[ks[0]].ini ? ks[0] : ks[ks.length-1];
}
function diaDe(s){ const w=(deIso(s).getDay()+6)%7; return w<5 ? w : null; }
function fmtDur(seg){
  seg = Math.max(0, Math.floor(seg));
  const h=Math.floor(seg/3600), m=Math.floor(seg%3600/60), s=seg%60;
  return h ? h+"h "+m+"min" : m ? m+"min "+s+"s" : s+"s";
}
const fmtMS = s=>Math.floor(s/60)+":"+z2(s%60);
const fmtDesc = s=>s%60 ? Math.floor(s/60)+"min "+s%60+"s" : (s/60)+"min";
function ritmo(km, min){ if(!(km>0) || !(min>0)) return "—"; const s=Math.round(min*60/km); return fmtMS(s)+"/km"; }

// ---------------------------------------------------------------- cálculos
function e1rm(kg, reps){
  if(!(reps>0) || !(kg>0)) return 0;
  const ep = kg*(1+reps/30);
  if(reps>10) return ep;
  return (ep + kg/(1.0278-0.0278*reps))/2;
}
function pesoEn(s){
  let p = null;
  D.peso.forEach(x=>{ if(x.f<=s && (!p || x.f>p.f)) p=x; });
  return p ? p.kg : R.peso;
}
const corporal = n=>!!(R.ej[n] && R.ej[n].corporal);
const carga = (n,kg,fecha)=>corporal(n) ? pesoEn(fecha)+(kg||0) : (kg||0);
const cuenta = s=>s.tipo!=="C";
function volumen(ses){
  let v=0; ses.ej.forEach(e=>e.series.filter(cuenta).forEach(s=>{ v+=(s.kg||0)*(s.reps||0); })); return v;
}
function nSeries(ses){ let n=0; ses.ej.forEach(e=>{ n+=e.series.filter(cuenta).length; }); return n; }
function mejor1rm(n){
  let b=0;
  D.sesiones.forEach(ses=>ses.ej.forEach(e=>{ if(e.n===n) e.series.filter(cuenta).forEach(s=>{ b=Math.max(b, e1rm(carga(n,s.kg,ses.fecha),s.reps)); }); }));
  return b;
}
function anterior(n){
  for(let i=D.sesiones.length-1;i>=0;i--){
    const e = D.sesiones[i].ej.find(x=>x.n===n);
    if(e && e.series.length) return e.series;
  }
  return null;
}
function txtSerie(n, s){
  if(corporal(n)) return (s.kg ? "+"+nf(s.kg)+"kg " : "")+"× "+s.reps;
  return nf(s.kg)+"kg × "+s.reps;
}

// ---------------------------------------------------------------- navegación
const VISTAS = [["entrenar","Entrenar"],["cuerpo","Peso y carrera"],["progreso","Progreso"],["historial","Historial"]];
let vista = "entrenar";
try{ const v=localStorage.getItem("reg_vista"); if(v && VISTAS.some(x=>x[0]===v)) vista=v; }catch(e){}
if(D.activa) vista = "entrenar";

function pintaTabs(){
  const b = document.getElementById("r-tabs"); b.replaceChildren();
  VISTAS.forEach(([k,t])=>{
    const c = el("button","chip",t);
    c.setAttribute("role","tab"); c.setAttribute("aria-selected", k===vista?"true":"false");
    c.addEventListener("click", ()=>{ vista=k; try{ localStorage.setItem("reg_vista",k); }catch(e){} render(); });
    b.append(c);
  });
}
function render(){
  pintaTabs(); paraReloj();
  const box = document.getElementById("r-vista"); box.replaceChildren();
  ({entrenar:vEntrenar, cuerpo:vCuerpo, progreso:vProgreso, historial:vHistorial})[vista](box);
}

// ---------------------------------------------------------------- entrenar
let selFase = null, selDia = null, resumen = null;

function vEntrenar(box){
  if(D.activa){ vSesion(box); return; }
  if(resumen) box.append(tarjetaResumen(resumen));
  const h = hoy();
  if(selFase===null) selFase = faseDe(h);
  if(selDia===null){ const d=diaDe(h); selDia = d===null ? 0 : d; }
  const f = R.fases[selFase], d = R.dias[selDia];

  const card = el("div","r-card");
  card.append(el("p","eyebrow","Bloque"));
  const fc = el("div","chips");
  Object.keys(R.fases).forEach(k=>{
    const c = el("button","chip sm",k+" · "+R.fases[k].n);
    c.setAttribute("aria-selected", k===selFase?"true":"false");
    c.addEventListener("click", ()=>{ selFase=k; render(); });
    fc.append(c);
  });
  card.append(fc, el("p","eyebrow","Día"));
  const dg = el("div","r-dias");
  R.dias.forEach((x,i)=>{
    const b = el("button","dia-btn");
    b.setAttribute("aria-selected", i===selDia?"true":"false");
    b.append(el("span",null,x.dia.slice(0,3)), el("small",null, x.tipo==="fuerza" ? x.n : "Carrera"));
    b.addEventListener("click", ()=>{ selDia=i; render(); });
    dg.append(b);
  });
  card.append(dg);
  if(diaDe(h)===null) card.append(el("p","nota","Hoy es fin de semana y el plan no entrena. Si aun así vas a recuperar una sesión, elige cuál."));

  card.append(el("h3",null,d.dia+" · "+d.n), el("p","nota",d.sub));
  if(d.tipo==="fuerza"){
    const l = el("div","r-prev");
    d.ej.forEach(([t,n])=>{ const p=f.esquema[t]; const r=el("div"); r.append(el("span",null,n), el("b",null,p[0]+" × "+p[1])); l.append(r); });
    if(d.tabata){ const r=el("div"); r.append(el("span",null,"Abdominales · "+R.tabatas[d.tabata]), el("b",null,"8 × 20 s")); l.append(r); }
    card.append(l);
    const b = el("button","r-btn full","Empezar entreno");
    b.addEventListener("click", ()=>empezar(selFase, selDia));
    card.append(b);
  } else {
    card.append(el("p",null, d.cod==="M" ? f.mar : f.jue));
    card.append(formCarrera(d.cod==="M" ? "Calidad" : "Tirada larga"));
  }
  box.append(card);
  if(D.sesiones.length){
    const u = D.sesiones[D.sesiones.length-1];
    box.append(el("p","nota","Último entreno: "+corta(u.fecha)+" · "+u.nombre+" · "+nf(volumen(u),0)+" kg · "+nSeries(u)+" series"));
  }
}

function empezar(fk, di){
  const d = R.dias[di], f = R.fases[fk];
  D.activa = {
    id: Date.now(), inicio: Date.now(), fecha: hoy(), fase: fk, dia: d.cod, nombre: d.dia+" · "+d.n,
    abd: d.tabata ? {n:R.tabatas[d.tabata], hecha:false} : null,
    ej: d.ej.map(([t,n])=>({ n, t, notas:"",
      series: Array.from({length:f.esquema[t][0]}, ()=>({kg:"", reps:"", tipo:"N", hecha:false})) }))
  };
  resumen = null; guarda(); render(); window.scrollTo(0,0);
}

let refs = {}, reloj = null;
function arrancaReloj(){
  paraReloj();
  const t = ()=>{ if(D.activa && refs.dur) refs.dur.textContent = fmtDur((Date.now()-D.activa.inicio)/1000); };
  t(); reloj = setInterval(t, 1000);
}
function paraReloj(){ clearInterval(reloj); reloj = null; }
function actualizaTop(){
  if(!D.activa || !refs.vol) return;
  let v=0, n=0;
  D.activa.ej.forEach(e=>e.series.forEach(s=>{ if(s.hecha && cuenta(s)){ n++; v+=(num(s.kg)||0)*(num(s.reps)||0); } }));
  refs.vol.textContent = nf(v,0)+" kg"; refs.ser.textContent = String(n);
}

function vSesion(box){
  const a = D.activa, f = R.fases[a.fase];
  refs = {};
  const top = el("div","r-top");
  const cel = (k,id,cls)=>{ const d=el("div"); d.append(el("div","k",k)); const v=el("div","v"+(cls?" "+cls:"")); refs[id]=v; d.append(v); return d; };
  top.append(cel("Duración","dur","acc"), cel("Volumen","vol"), cel("Series","ser"));
  const fin = el("button","r-btn","Terminar"); fin.addEventListener("click", terminar);
  const x = el("button","r-x","✕"); x.title = "Descartar entreno"; x.setAttribute("aria-label","Descartar entreno");
  x.addEventListener("click", ()=>{
    if(confirm("¿Descartar este entreno? Se pierde todo lo apuntado.")){ D.activa=null; guarda(); paraDescanso(); render(); }
  });
  top.append(fin, x);
  box.append(top, el("h2","r-tit",a.nombre), el("p","nota",a.fase+" · "+f.n+" · "+corta(a.fecha)));
  a.ej.forEach(e=>box.append(bloqueEj(e, f)));
  if(a.abd){
    const ab = el("div","r-abd");
    const t = el("div"); t.append(el("b",null,"Abdominales"), el("p","nota",a.abd.n+" · tabata 20-20, 8 rondas"));
    const ok = el("button","r-ok"); ok.innerHTML = CHECK; ok.style.width="44px";
    if(a.abd.hecha){ ok.style.background="var(--accent)"; ok.style.color="#FFFFFF"; }
    ok.addEventListener("click", ()=>{ a.abd.hecha=!a.abd.hecha; guarda(); render(); });
    ab.append(t, ok); box.append(ab);
  }
  const fin2 = el("button","r-btn full","Terminar entreno"); fin2.style.marginTop="18px";
  fin2.addEventListener("click", terminar); box.append(fin2);
  actualizaTop(); arrancaReloj();
}

function bloqueEj(e, f){
  const p = f.esquema[e.t], ant = anterior(e.n) || [], cor = corporal(e.n);
  const minReps = String(p[1]).split("–")[0];
  const w = el("div","r-ej");
  w.append(el("h3",null,e.n));
  const meta = el("div","r-meta");
  meta.append(el("span","r-tier", e.t==="TF" ? "Fijo" : e.t), el("span","r-obj", p[0]+" × "+p[1]+" · "+p[2]));
  w.append(meta);
  if(R.ej[e.n] && R.ej[e.n].cue) w.append(el("p","r-cue",R.ej[e.n].cue));
  const notas = el("textarea","r-notas"); notas.rows=1; notas.placeholder="Agregar notas aquí…"; notas.value=e.notas;
  notas.addEventListener("input", ()=>{ e.notas=notas.value; guarda(); });
  w.append(notas);
  const ds = el("p","r-desc"); ds.innerHTML = RELOJ; ds.append(document.createTextNode("Descanso: "+fmtDesc(R.descanso[e.t])));
  w.append(ds);
  const hd = el("div","r-fila r-hd");
  ["Serie","Anterior", cor ? "+kg" : "kg","Reps"].forEach(t=>hd.append(el("span",null,t)));
  const hc = el("span"); hc.innerHTML = CHECK; hd.append(hc);
  w.append(hd);
  let n = 0;
  e.series.forEach((s,si)=>{ if(s.tipo!=="C") n++; w.append(filaSerie(e, s, s.tipo==="C" ? "C" : s.tipo==="F" ? "F" : String(n), ant[si], minReps, cor)); });
  const acc = el("div","r-acc");
  const add = el("button","r-btn sec","+ Agregar serie");
  add.addEventListener("click", ()=>{ e.series.push({kg:"",reps:"",tipo:"N",hecha:false}); guarda(); render(); });
  const qu = el("button","r-btn sec","Quitar");
  qu.addEventListener("click", ()=>{ if(e.series.length){ e.series.pop(); guarda(); render(); } });
  acc.append(add, qu); w.append(acc);
  return w;
}

function filaSerie(e, s, etiqueta, a, minReps, cor){
  const f = el("div","r-fila"+(s.hecha?" hecha":""));
  const nb = el("button","r-num "+s.tipo, etiqueta);
  nb.title = "Toca para cambiar: normal, calentamiento (C) o al fallo (F)";
  nb.addEventListener("click", ()=>{ s.tipo = s.tipo==="N" ? "C" : s.tipo==="C" ? "F" : "N"; guarda(); render(); });
  const an = el("span","r-ant", a ? txtSerie(e.n, a) : "—");
  const kg = el("input","r-in"); kg.inputMode="decimal"; kg.value=s.kg; kg.setAttribute("aria-label","kg");
  kg.placeholder = a ? nf(a.kg) : (cor ? "0" : "kg");
  const rp = el("input","r-in"); rp.inputMode="numeric"; rp.value=s.reps; rp.setAttribute("aria-label","repeticiones");
  rp.placeholder = a ? String(a.reps) : minReps;
  kg.addEventListener("input", ()=>{ s.kg=kg.value; guarda(); actualizaTop(); });
  rp.addEventListener("input", ()=>{ s.reps=rp.value; guarda(); actualizaTop(); });
  const ok = el("button","r-ok"); ok.innerHTML = CHECK; ok.setAttribute("aria-label","Serie hecha");
  ok.addEventListener("click", ()=>{
    if(!s.hecha){
      if(s.kg===""){
        if(kg.placeholder==="kg"){ aviso("Pon los kilos antes de marcar la serie."); kg.focus(); return; }
        s.kg = kg.placeholder;
      }
      if(s.reps==="") s.reps = rp.placeholder;
      if(!(num(s.reps)>0)){ aviso("Pon las repeticiones antes de marcar la serie."); rp.focus(); return; }
      kg.value = s.kg; rp.value = s.reps;
    }
    s.hecha = !s.hecha; f.classList.toggle("hecha", s.hecha); guarda(); actualizaTop();
    if(s.hecha) empiezaDescanso(R.descanso[e.t]);
  });
  f.append(nb, an, kg, rp, ok);
  return f;
}

function terminar(){
  const a = D.activa;
  const ej = a.ej.map(e=>({ n:e.n, t:e.t, notas:e.notas.trim(),
    series: e.series.filter(s=>s.hecha).map(s=>({kg:num(s.kg)||0, reps:num(s.reps)||0, tipo:s.tipo})) }))
    .filter(e=>e.series.length);
  if(!ej.length && !(a.abd && a.abd.hecha)){
    if(!confirm("No has marcado ninguna serie. ¿Cerrar el entreno sin guardar nada?")) return;
    D.activa = null; guarda(); paraDescanso(); render(); return;
  }
  const ses = {id:a.id, fecha:a.fecha, fase:a.fase, dia:a.dia, nombre:a.nombre,
               dur:Math.round((Date.now()-a.inicio)/1000), ej, abd: a.abd ? a.abd.hecha : null};
  const recs = [];
  ej.forEach(e=>{
    const antes = mejor1rm(e.n);
    const ahora = Math.max(0, ...e.series.filter(cuenta).map(s=>e1rm(carga(e.n,s.kg,ses.fecha), s.reps)));
    if(antes>0 && ahora>antes+0.05) recs.push({n:e.n, ahora, antes});
  });
  D.sesiones.push(ses);
  D.sesiones.sort((x,y)=>x.fecha<y.fecha ? -1 : x.fecha>y.fecha ? 1 : x.id-y.id);
  D.activa = null; guarda(); paraDescanso();
  resumen = {ses, recs}; render(); window.scrollTo(0,0);
}

function tarjetaResumen(r){
  const c = el("div","r-card");
  c.append(el("h3",null,"Entreno guardado · "+r.ses.nombre));
  const st = el("div","r-stats");
  [[fmtDur(r.ses.dur),"Duración"],[nf(volumen(r.ses),0)+" kg","Volumen"],[String(nSeries(r.ses)),"Series"]].forEach(([v,k])=>{
    const d=el("div"); d.append(el("span","v",v), el("span","k",k)); st.append(d);
  });
  c.append(st);
  r.recs.forEach(x=>c.append(el("p","r-rec","Récord en "+x.n+": 1RM estimado "+nf(x.ahora)+" kg (antes "+nf(x.antes)+")")));
  const b = el("button","r-btn sec","Cerrar"); b.addEventListener("click", ()=>{ resumen=null; render(); });
  c.append(b);
  return c;
}

// ---------------------------------------------------------------- descanso
let descFin = 0, descTotal = 0, descT = null;
function empiezaDescanso(seg){
  descTotal = seg; descFin = Date.now()+seg*1000; pintaDescanso();
  if(!descT) descT = setInterval(pintaDescanso, 250);
}
function pintaDescanso(){
  const r = Math.ceil((descFin-Date.now())/1000);
  if(r<=0){
    paraDescanso();
    try{ if(navigator.vibrate) navigator.vibrate([250,120,250]); }catch(e){}
    aviso("Descanso terminado");
    return;
  }
  document.getElementById("r-descanso").hidden = false;
  document.getElementById("r-desc-t").textContent = fmtMS(r);
  document.getElementById("r-desc-bar").style.width = Math.min(100, 100*r/descTotal)+"%";
}
function paraDescanso(){ clearInterval(descT); descT = null; document.getElementById("r-descanso").hidden = true; }

// ---------------------------------------------------------------- peso y carrera
function formCarrera(tipoDef){
  const w = el("div","r-form");
  const campo = (t,inp,ancho)=>{ const l=el("label",ancho?"ancho":null,t); l.append(inp); w.append(l); return inp; };
  const f = campo("Fecha", el("input")); f.type="date"; f.value=hoy();
  const tp = campo("Tipo", el("select"));
  ["Rodaje","Calidad","Tirada larga","Test 5 km"].forEach(x=>{ const o=el("option",null,x); o.value=x; if(x===tipoDef) o.selected=true; tp.append(o); });
  const km = campo("Km", el("input")); km.inputMode="decimal"; km.placeholder="8,2";
  const mi = campo("Minutos", el("input")); mi.inputMode="decimal"; mi.placeholder="52";
  const b = el("button","r-btn ancho","Guardar carrera");
  b.addEventListener("click", ()=>{
    const k=num(km.value), m=num(mi.value);
    if(!(k>0) || !(m>0)){ aviso("Pon los km y los minutos."); return; }
    D.carrera.push({id:Date.now(), f:f.value||hoy(), tipo:tp.value, km:k, min:m});
    D.carrera.sort((x,y)=>x.f<y.f?-1:x.f>y.f?1:0);
    guarda(); aviso("Carrera guardada · "+ritmo(k,m)); render();
  });
  w.append(b);
  return w;
}

function vCuerpo(box){
  const h = hoy(), fk = faseDe(h), f = R.fases[fk];
  const c = el("div","r-card");
  c.append(el("h3",null,"Peso corporal"));
  const w = el("div","r-form");
  const lf = el("label",null,"Fecha"); const fi = el("input"); fi.type="date"; fi.value=h; lf.append(fi);
  const lk = el("label",null,"Kg"); const ki = el("input"); ki.inputMode="decimal"; ki.placeholder=nf(pesoEn(h)); lk.append(ki);
  const b = el("button","r-btn ancho","Guardar peso");
  b.addEventListener("click", ()=>{
    const kg = num(ki.value);
    if(!(kg>30 && kg<250)){ aviso("Ese peso no parece correcto."); return; }
    const fe = fi.value || h;
    D.peso = D.peso.filter(x=>x.f!==fe); D.peso.push({f:fe, kg});
    D.peso.sort((x,y)=>x.f<y.f?-1:1); guarda(); aviso("Peso guardado"); render();
  });
  w.append(lf, lk, b); c.append(w);

  const media = (desde, hasta)=>{ const xs=D.peso.filter(x=>x.f>desde && x.f<=hasta).map(x=>x.kg); return xs.length ? xs.reduce((a,b)=>a+b,0)/xs.length : null; };
  const d7 = iso(new Date(deIso(h).getTime()-7*864e5)), d14 = iso(new Date(deIso(h).getTime()-14*864e5));
  const m1 = media(d7,h), m0 = media(d14,d7);
  const st = el("div","r-stats");
  [[m1===null?"—":nf(m1)+" kg","Media 7 días"],
   [m1===null||m0===null?"—":(m1-m0>=0?"+":"")+nf(m1-m0,2)+" kg","Cambio semanal"],
   [f.ritmo===null?"mantener":(f.ritmo>0?"+":"")+nf(f.ritmo)+" kg","Buscado en "+fk]].forEach(([v,k])=>{
    const d=el("div"); d.append(el("span","v",v), el("span","k",k)); st.append(d);
  });
  c.append(st, el("p","nota","Lo que decide si tocar las calorías es la media de 7 días durante dos semanas, nunca el dato de un día."));
  if(D.peso.length){
    const l = el("div","r-lista");
    D.peso.slice(-7).reverse().forEach(x=>{
      const r=el("div"); r.append(el("span",null,corta(x.f)), el("b",null,nf(x.kg)+" kg"));
      const del=el("button","r-mini","✕"); del.setAttribute("aria-label","Borrar");
      del.addEventListener("click", ()=>{ D.peso=D.peso.filter(y=>y!==x); guarda(); render(); });
      r.append(del); l.append(r);
    });
    c.append(l);
  }
  box.append(c);

  const c2 = el("div","r-card");
  c2.append(el("h3",null,"Carrera"), formCarrera("Rodaje"));
  if(D.carrera.length){
    const l = el("div","r-lista");
    D.carrera.slice(-5).reverse().forEach(x=>{
      const r=el("div"); r.append(el("span",null,corta(x.f)+" · "+x.tipo), el("b",null,nf(x.km)+" km · "+ritmo(x.km,x.min)));
      l.append(r);
    });
    c2.append(l);
  }
  box.append(c2);
}

// ---------------------------------------------------------------- gráficas
const fx = t=>{ const d=new Date(t); return d.getDate()+" "+MES[d.getMonth()]; };
function svgLinea(linea, puntos, uni){
  const W=320, H=170, L=40, Rm=12, T=12, B=26;
  const todo = linea.concat(puntos||[]);
  let x0=Math.min(...todo.map(p=>p.x)), x1=Math.max(...todo.map(p=>p.x));
  if(x1===x0){ x0-=3*864e5; x1+=3*864e5; }
  let y0=Math.min(...todo.map(p=>p.y)), y1=Math.max(...todo.map(p=>p.y));
  const pad = (y1-y0)*0.15 || Math.max(1, y1*0.05); y0-=pad; y1+=pad;
  const X=x=>L+(x-x0)/(x1-x0)*(W-L-Rm), Y=y=>T+(1-(y-y0)/(y1-y0))*(H-T-B);
  let s = '<svg class="g-svg" viewBox="0 0 '+W+' '+H+'" role="img">';
  for(let i=0;i<=3;i++){
    const v=y0+(y1-y0)*i/3, yy=Y(v).toFixed(1);
    s += '<line class="g-grid" x1="'+L+'" x2="'+(W-Rm)+'" y1="'+yy+'" y2="'+yy+'"/><text class="g-eje" x="'+(L-6)+'" y="'+(+yy+3)+'" text-anchor="end">'+nf(v, Math.abs(v)>=100?0:1)+'</text>';
  }
  s += '<text class="g-eje" x="'+L+'" y="'+(H-8)+'">'+fx(x0)+'</text><text class="g-eje" x="'+(W-Rm)+'" y="'+(H-8)+'" text-anchor="end">'+fx(x1)+'</text>';
  (puntos||[]).forEach(q=>{ s += '<circle class="g-pt2" cx="'+X(q.x).toFixed(1)+'" cy="'+Y(q.y).toFixed(1)+'" r="2.5"/>'; });
  if(linea.length>1) s += '<polyline class="g-line" points="'+linea.map(q=>X(q.x).toFixed(1)+","+Y(q.y).toFixed(1)).join(" ")+'"/>';
  linea.forEach(q=>{ s += '<circle class="g-pt" cx="'+X(q.x).toFixed(1)+'" cy="'+Y(q.y).toFixed(1)+'" r="3.2"><title>'+fx(q.x)+": "+nf(q.y)+" "+uni+'</title></circle>'; });
  return s+'</svg>';
}
function svgBarras(items){
  const W=320, H=170, L=30, Rm=8, T=12, B=26;
  const max = Math.max(1, ...items.map(i=>Math.max(i.v, i.plan||0)))*1.1;
  const bw = (W-L-Rm)/items.length, Y=v=>T+(1-v/max)*(H-T-B);
  let s = '<svg class="g-svg" viewBox="0 0 '+W+' '+H+'" role="img">';
  for(let i=0;i<=2;i++){ const v=max*i/2, yy=Y(v).toFixed(1); s += '<line class="g-grid" x1="'+L+'" x2="'+(W-Rm)+'" y1="'+yy+'" y2="'+yy+'"/><text class="g-eje" x="'+(L-5)+'" y="'+(+yy+3)+'" text-anchor="end">'+nf(v,0)+'</text>'; }
  items.forEach((it,i)=>{
    const x=L+i*bw+bw*0.18, w=bw*0.64;
    if(it.v>0) s += '<rect class="g-bar'+(it.des?" des":"")+'" x="'+x.toFixed(1)+'" y="'+Y(it.v).toFixed(1)+'" width="'+w.toFixed(1)+'" height="'+(Y(0)-Y(it.v)).toFixed(1)+'" rx="2"><title>'+it.et+": "+nf(it.v)+' km</title></rect>';
    if(it.plan) s += '<line class="g-plan" x1="'+(x-2).toFixed(1)+'" x2="'+(x+w+2).toFixed(1)+'" y1="'+Y(it.plan).toFixed(1)+'" y2="'+Y(it.plan).toFixed(1)+'"/>';
    if(i%3===0) s += '<text class="g-eje" x="'+(x+w/2).toFixed(1)+'" y="'+(H-8)+'" text-anchor="middle">'+it.et+'</text>';
  });
  return s+'</svg>';
}
const leyenda = pares=>{ const l=el("div","g-ley"); pares.forEach(([c,t])=>{ const s=el("span"); s.innerHTML='<i class="'+c+'"></i>'; s.append(document.createTextNode(t)); l.append(s); }); return l; };
const hueco = t=>el("p","nota",t);

let selEj = null, selMet = "1rm";
const METRICAS = [["1rm","1RM estimado"],["max","Carga máxima"],["vol","Volumen"]];

function vProgreso(box){
  // --- ejercicio
  const c = el("div","r-card");
  c.append(el("h3",null,"Por ejercicio"));
  const conDatos = Object.keys(R.ej).filter(n=>D.sesiones.some(s=>s.ej.some(e=>e.n===n)));
  if(!conDatos.length){
    c.append(hueco("Cuando termines tu primer entreno aparecerán aquí las gráficas de cada ejercicio."));
  } else {
    if(!conDatos.includes(selEj)) selEj = conDatos[0];
    const sel = el("select","r-sel");
    conDatos.forEach(n=>{ const o=el("option",null,n); o.value=n; if(n===selEj) o.selected=true; sel.append(o); });
    sel.addEventListener("change", ()=>{ selEj=sel.value; render(); });
    const ch = el("div","chips");
    METRICAS.forEach(([k,t])=>{ const b=el("button","chip sm",t); b.setAttribute("aria-selected",k===selMet?"true":"false"); b.addEventListener("click",()=>{ selMet=k; render(); }); ch.append(b); });
    c.append(sel, ch);
    const pts = []; let rec = 0, mejor = null;
    D.sesiones.forEach(ses=>ses.ej.filter(e=>e.n===selEj).forEach(e=>{
      const ss = e.series.filter(cuenta); if(!ss.length) return;
      let v = 0;
      ss.forEach(s=>{
        const cg = carga(selEj, s.kg, ses.fecha), r1 = e1rm(cg, s.reps);
        if(selMet==="1rm") v = Math.max(v, r1);
        else if(selMet==="max") v = Math.max(v, cg);
        else v += (s.kg||0)*(s.reps||0);
        if(r1>rec){ rec = r1; mejor = {cg, reps:s.reps}; }
      });
      pts.push({x:deIso(ses.fecha).getTime(), y:v});
    }));
    c.append(el("div")); c.lastChild.innerHTML = svgLinea(pts, [], "kg");
    const st = el("div","r-stats");
    [[nf(rec)+" kg","Récord 1RM"],[mejor?nf(mejor.cg)+" × "+mejor.reps:"—","Mejor serie"],[String(pts.length),"Sesiones"]].forEach(([v,k])=>{ const d=el("div"); d.append(el("span","v",v), el("span","k",k)); st.append(d); });
    c.append(st);
    if(corporal(selEj)) c.append(hueco("En este ejercicio la carga es tu peso corporal del día más el lastre."));
  }
  box.append(c);

  // --- peso corporal
  const c2 = el("div","r-card");
  c2.append(el("h3",null,"Peso corporal"));
  if(D.peso.length<2) c2.append(hueco("Apunta tu peso en «Peso y carrera»: con dos días ya sale la gráfica."));
  else {
    const pts = D.peso.map(p=>({x:deIso(p.f).getTime(), y:p.kg}));
    const med = D.peso.map(p=>{ const d=deIso(p.f).getTime(); const xs=D.peso.filter(q=>{ const t=deIso(q.f).getTime(); return t<=d && t>d-7*864e5; }); return {x:d, y:xs.reduce((a,q)=>a+q.kg,0)/xs.length}; });
    const g = el("div"); g.innerHTML = svgLinea(med, pts, "kg");
    c2.append(g, leyenda([["","Media de 7 días"],["d","Cada pesada"]]));
  }
  box.append(c2);

  // --- km por semana
  const c3 = el("div","r-card");
  c3.append(el("h3",null,"Kilómetros por semana"));
  const sem = lunes(hoy()), items = [];
  for(let i=11;i>=0;i--){
    const l = iso(new Date(deIso(sem).getTime()-i*7*864e5));
    const fin = iso(new Date(deIso(l).getTime()+6*864e5));
    const km = D.carrera.filter(x=>x.f>=l && x.f<=fin).reduce((a,x)=>a+x.km,0);
    const p = R.km_plan.find(x=>x[0]===l);
    items.push({et:corta(l), v:km, plan:p?p[1]:0, des:p?p[2]:false});
  }
  const g3 = el("div"); g3.innerHTML = svgBarras(items);
  c3.append(g3, leyenda([["","Hecho"],["p","Lo que marca el plan"]]));
  box.append(c3);

  // --- series por grupo esta semana
  const c4 = el("div","r-card");
  const fk = faseDe(hoy()), f = R.fases[fk], l0 = lunes(hoy());
  c4.append(el("h3",null,"Series por grupo · esta semana"));
  const cnt = {}; R.musculos.forEach(m=>{ cnt[m]=0; });
  D.sesiones.filter(s=>s.fecha>=l0).forEach(s=>s.ej.forEach(e=>{
    const k = e.series.filter(cuenta).length;
    ((R.ej[e.n]||{}).m||[]).forEach(m=>{ cnt[m]=(cnt[m]||0)+k; });
  }));
  const MAX = R.techo+4;
  R.musculos.forEach(m=>{
    const piso = R.grandes.includes(m) ? f.piso : R.piso_peq;
    const r = el("div","gb"); r.append(el("span",null,m));
    const p = el("div","pista");
    const rg = el("div","rango"); rg.style.left=(100*piso/MAX)+"%"; rg.style.width=(100*(R.techo-piso)/MAX)+"%";
    const fl = el("div","fill"); fl.style.width=Math.min(100,100*cnt[m]/MAX)+"%";
    const pl = el("div","plan"); pl.style.left=Math.min(99,100*(f.plan[m]||0)/MAX)+"%";
    p.append(rg, fl, pl);
    r.append(p, el("span","n",cnt[m]+" / "+(f.plan[m]||0)));
    c4.append(r);
  });
  c4.append(leyenda([["","Hechas"],["p","Plan de "+fk]]), hueco("La franja clara es el rango útil (de "+f.piso+" a "+R.techo+" series en los grupos grandes). Solo cuentan las series que no son de calentamiento."));
  box.append(c4);
}

// ---------------------------------------------------------------- historial y copia
function vHistorial(box){
  const items = D.sesiones.map(s=>({f:s.fecha, t:"s", o:s})).concat(D.carrera.map(c=>({f:c.f, t:"c", o:c})))
    .sort((a,b)=>a.f<b.f?1:a.f>b.f?-1:(b.o.id||0)-(a.o.id||0));
  if(!items.length) box.append(hueco("Todavía no hay nada registrado."));
  items.slice(0,60).forEach(it=>{
    const d = el("details","r-hist"), s = el("summary"), c = el("div","cuerpo");
    if(it.t==="s"){
      const x = it.o;
      s.append(el("b",null,x.nombre), el("span",null,corta(x.fecha)+" · "+fmtDur(x.dur)+" · "+nf(volumen(x),0)+" kg · "+nSeries(x)+" series"));
      x.ej.forEach(e=>{
        c.append(el("h5",null,e.n));
        let n=0;
        e.series.forEach(se=>{ const et = se.tipo==="C" ? "C" : se.tipo==="F" ? "F" : String(++n); c.append(el("p",null,et+"   "+txtSerie(e.n,se))); });
        if(e.notas) c.append(el("p","nota",e.notas));
      });
      if(x.abd!==null) c.append(el("p",null,"Abdominales: "+(x.abd?"hechos":"no")));
    } else {
      const x = it.o;
      s.append(el("b",null,"Carrera · "+x.tipo), el("span",null,corta(x.f)+" · "+nf(x.km)+" km · "+nf(x.min,0)+" min · "+ritmo(x.km,x.min)));
    }
    const del = el("button","r-btn peligro","Borrar");
    del.addEventListener("click", ()=>{
      if(!confirm("¿Borrar este registro?")) return;
      if(it.t==="s") D.sesiones = D.sesiones.filter(y=>y!==it.o); else D.carrera = D.carrera.filter(y=>y!==it.o);
      guarda(); render();
    });
    c.append(del); d.append(s, c); box.append(d);
  });

  const cp = el("div","r-card");
  cp.append(el("h3",null,"Copia de seguridad"),
    el("p","nota","Tienes "+D.sesiones.length+" entrenos, "+D.peso.length+" pesos y "+D.carrera.length+" carreras en este móvil. Si borras los datos del navegador o cambias de móvil, se pierden: exporta una copia de vez en cuando y guárdala en tu carpeta del gimnasio."));
  const dos = el("div","r-dos");
  const ex = el("button","r-btn","Exportar copia");
  ex.addEventListener("click", ()=>{
    const blob = new Blob([JSON.stringify(D,null,1)], {type:"application/json"});
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "junio2027-registro-"+hoy()+".json";
    document.body.append(a); a.click(); setTimeout(()=>{ URL.revokeObjectURL(a.href); a.remove(); }, 1500);
  });
  const inp = el("input"); inp.type="file"; inp.accept=".json,application/json"; inp.hidden=true;
  const im = el("button","r-btn sec","Importar copia"); im.addEventListener("click", ()=>inp.click());
  inp.addEventListener("change", ()=>{
    const fl = inp.files[0]; inp.value = ""; if(!fl) return;
    fl.text().then(t=>{
      const d = JSON.parse(t);
      if(!d || d.v!==1 || !Array.isArray(d.sesiones)) throw new Error("formato");
      if(!confirm("La copia tiene "+d.sesiones.length+" entrenos, "+(d.peso||[]).length+" pesos y "+(d.carrera||[]).length+" carreras. Sustituye a todo lo que hay ahora en este móvil. ¿Seguir?")) return;
      D = Object.assign(vacio(), d); guarda(); render(); aviso("Copia importada");
    }).catch(()=>aviso("Ese archivo no es una copia válida del registro."));
  });
  dos.append(ex, im); cp.append(dos, inp);
  box.append(cp);
}

// ---------------------------------------------------------------- arranque
document.getElementById("r-desc-menos").addEventListener("click", ()=>{ descFin -= 15000; pintaDescanso(); });
document.getElementById("r-desc-mas").addEventListener("click", ()=>{ descFin += 15000; descTotal = Math.max(descTotal, Math.ceil((descFin-Date.now())/1000)); pintaDescanso(); });
document.getElementById("r-desc-saltar").addEventListener("click", paraDescanso);
render();
