// Menús v2.0: lista del día, calculadora de raciones y diario.
// Los datos del plan (M) los genera menu/payload3.py. La cuenta de raciones está
// en menu/calculadora.js (CALC). Aquí solo se pinta y se guarda en el navegador.

const DIAS_SEM = ["Domingo","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"];
const CORTO = ["D","L","M","X","J","V","S"];
const MES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
const TIPO_DE = {1:"A",2:"B",3:"A",4:"B",5:"C",6:"D",0:"E"};   // getDay() -> tipo de día
const KEY = "diario_v1", KEY_EXTRA = "menu_extra_v1", KEY_REG = "registro_v1";
const DETALLE_DIAS = 14;          // días con detalle; lo anterior se resume por semanas
const MARGEN = 0.05, MARGEN_MIN = 25;

const CANDADO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>';
const ABIERTO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.5-2"/></svg>';
const CHECK = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
const QUITAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';

const el = (t,c,x)=>{const n=document.createElement(t); if(c)n.className=c; if(x!==undefined)n.textContent=x; return n;};
const nf = n => Math.round(n).toLocaleString("es-ES");
const z2 = n => String(n).padStart(2,"0");
const iso = d => d.getFullYear()+"-"+z2(d.getMonth()+1)+"-"+z2(d.getDate());
const deIso = s => { const [a,m,d]=s.split("-").map(Number); return new Date(a,m-1,d); };
const hoy = () => iso(new Date());
const sumaDias = (s,n) => { const d=deIso(s); d.setDate(d.getDate()+n); return iso(d); };
const lunes = s => { const d=deIso(s); d.setDate(d.getDate()-(d.getDay()+6)%7); return iso(d); };
const sinTildes = t => t.normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase();

// ---------------------------------------------------------------- almacenamiento
function leeJSON(k, def){ try{ const t=localStorage.getItem(k); if(t){ const d=JSON.parse(t); if(d) return d; } }catch(e){} return def; }
function vacio(){ return {v:1, dias:{}, semanas:{}}; }
let D = Object.assign(vacio(), leeJSON(KEY, {}));
let EXTRA = leeJSON(KEY_EXTRA, {});          // alimentos añadidos desde el catálogo
function guarda(){
  try{ localStorage.setItem(KEY, JSON.stringify(D)); localStorage.setItem(KEY_EXTRA, JSON.stringify(EXTRA)); }
  catch(e){ aviso("No se ha podido guardar: el navegador tiene el almacenamiento lleno o bloqueado."); }
}
let avisoT=null;
function aviso(t){ const a=document.getElementById("m-aviso"); a.textContent=t; a.hidden=false;
  clearTimeout(avisoT); avisoT=setTimeout(()=>{a.hidden=true;},2600); }

// Los días con más de DETALLE_DIAS se convierten en una línea por semana:
// días apuntados, kcal y macros medios y el objetivo medio. Así el diario no crece.
function compacta(){
  const limite = sumaDias(hoy(), -DETALLE_DIAS);
  let cambios = false;
  Object.keys(D.dias).forEach(f=>{
    if(f >= limite) return;
    const d = D.dias[f], t = totalesDia(f, d), w = lunes(f);
    if(t.n){
      const s = D.semanas[w] || {n:0, m:[0,0,0,0], obj:0};
      s.n += 1; for(let i=0;i<4;i++) s.m[i] += t.comido[i]; s.obj += t.obj[0];
      D.semanas[w] = s;
    }
    delete D.dias[f]; cambios = true;
  });
  if(cambios) guarda();
}

// El peso vive en el Registro (registro_v1), para que las dos pestañas vean el mismo.
function registro(){ return leeJSON(KEY_REG, null); }
function guardaPeso(fecha, kg){
  const r = registro() || {v:1, inicio:null, sesiones:[], peso:[], carrera:[], activa:null};
  r.peso = (r.peso||[]).filter(x=>x.f!==fecha); r.peso.push({f:fecha, kg});
  r.peso.sort((a,b)=>a.f<b.f?-1:1);
  try{ localStorage.setItem(KEY_REG, JSON.stringify(r)); }catch(e){ aviso("No se ha podido guardar el peso."); return; }
  window.dispatchEvent(new CustomEvent("gd:registro"));
}

// ---------------------------------------------------------------- qué toca cada día
let fecha = hoy(), abierta = null, buscando = null;
let faseManual = leeJSON("menu_fase", null);

function faseDe(f){
  const r = registro();
  if(r && r.inicio){
    const sem = Math.round((deIso(lunes(f)) - deIso(lunes(r.inicio)))/6048e5) + 1;
    const ks = Object.keys(M.fases);
    if(sem < 1) return ks[0];
    for(const k of ks){ if(sem>=M.fases[k].s0 && sem<=M.fases[k].s1) return k; }
  }
  return faseManual && M.fases[faseManual] ? faseManual : Object.keys(M.fases)[0];
}
function dia(f){ return D.dias[f] || null; }
function faseDia(f){ const d=dia(f); return (d && d.fase) || faseDe(f); }
function tipoDia(f){ const d=dia(f); return (d && d.tipo) || TIPO_DE[deIso(f).getDay()]; }
function tomas(f){ return M.tipos[tipoDia(f)].tomas; }
function objToma(f, b){ return M.obj[faseDia(f)+"|"+tipoDia(f)][b]; }
function objDia(f){ const o=[0,0,0,0]; tomas(f).forEach(b=>{ const t=objToma(f,b); for(let i=0;i<4;i++) o[i]+=t[i]; }); return o; }
function asegura(f){
  if(!D.dias[f]) D.dias[f] = {fase:faseDia(f), tipo:tipoDia(f), tomas:{}};
  return D.dias[f];
}

// ---------------------------------------------------------------- platos y alimentos
function ficha(n){ return M.foods[n] || EXTRA[n]; }
function principalesDe(b){ return M.principales.map((p,i)=>({p, i})).filter(x=>x.p.de===b); }
function opciones(b){
  return (b==="C"||b==="N") ? M.principales.map((p,i)=>({clave:"P"+i, n:p.n, de:p.de, it:p.it}))
                            : M.bloques[b].ops.map((o,i)=>({clave:"O"+i, n:o.n, it:o.it}));
}
// Plato por defecto: en comida y cena, el de ese día de la semana (como la lista de la compra)
function claveDefecto(f, b){
  if(b==="C"||b==="N"){
    const lista = principalesDe(b), k = (deIso(f).getDay()+6)%7;
    return "P" + lista[Math.min(k, lista.length-1)].i;
  }
  return "O0";
}
function opcion(b, clave){ return opciones(b).find(o=>o.clave===clave) || opciones(b)[0]; }

// Estado de una toma: plato elegido y, para cada alimento, si lo has fijado tú.
// it: [[nombre, gramos de receta, fijado, gramos fijados]]
function estado(f, b){
  const d = dia(f), t = d && d.tomas[b];
  if(t) return t;
  const clave = claveDefecto(f, b);
  return {p:clave, it:opcion(b, clave).it.map(([n,g])=>[n,g,false,null]), ok:false};
}
function guardaEstado(f, b, t){ asegura(f).tomas[b] = t; guarda(); }

// Objetivo de la toma con el arrastre: lo que te has pasado o te ha faltado en las
// tomas ya hechas se reparte entre las que quedan, en proporción a su tamaño.
function objetivo(f, b){
  const base = objToma(f, b), st = estado(f, b);
  if(st.ok) return base;
  const od = objDia(f); let hechas=[0,0,0,0], quedan=0;
  tomas(f).forEach(x=>{ const e=estado(f,x);
    if(e.ok){ const m=e.m || calcula(f,x).tot; for(let i=0;i<4;i++) hechas[i]+=m[i]; }
    else quedan += objToma(f,x)[0]; });
  if(!quedan) return base;
  const fac = Math.max(0.5, Math.min(1.5, (od[0]-hechas[0]) / quedan));
  return base.map(v=>v*fac);
}

function calcula(f, b, obj){
  const st = estado(f, b);
  obj = obj || objetivo(f, b);
  const its = st.it.filter(x=>ficha(x[0])).map(([n,g,fij,gf])=>CALC.item(n, fij ? gf : g, ficha(n), b, fij));
  const g = CALC.resolver(its, obj);
  return {its, g, tot:CALC.suma(its, g), obj};
}
function totalesDia(f, d){
  const comido=[0,0,0,0]; let n=0;
  Object.values((d||dia(f)||{tomas:{}}).tomas).forEach(t=>{ if(t.ok && t.m){ n++; for(let i=0;i<4;i++) comido[i]+=t.m[i]; } });
  return {comido, n, obj: d && D.dias[f] ? objDia(f) : [0,0,0,0]};
}
function dentro(real, obj){ return Math.abs(real-obj) <= Math.max(MARGEN*obj, MARGEN_MIN); }

// ---------------------------------------------------------------- cabecera y resumen
function pintaCabecera(){
  const d = deIso(fecha), h = hoy();
  document.getElementById("m-dia").textContent = DIAS_SEM[d.getDay()]+" "+d.getDate()+" "+MES[d.getMonth()];
  const dif = Math.round((d - deIso(h))/864e5);
  document.getElementById("m-sub").textContent = dif===0 ? "Hoy" : dif===-1 ? "Ayer" : dif===1 ? "Mañana" : (dif<0 ? "Hace "+(-dif)+" días" : "Dentro de "+dif+" días");
  document.getElementById("m-hoy").hidden = dif===0;
  const sf = document.getElementById("m-fase"); sf.replaceChildren();
  Object.keys(M.fases).forEach(k=>{ const o=el("option",null,M.fases[k].n+" ("+k+")"); o.value=k; sf.append(o); });
  sf.value = faseDia(fecha);
  const r = registro(); sf.title = r && r.inicio ? "Sale de la fecha de inicio del Registro" : "Elige tu bloque";
  const stp = document.getElementById("m-tipo"); stp.replaceChildren();
  Object.keys(M.tipos).forEach(k=>{ const o=el("option",null,"Día "+k+": "+M.tipos[k].n.toLowerCase()); o.value=k; stp.append(o); });
  stp.value = tipoDia(fecha);
}

function pintaResumen(){
  const od = objDia(fecha), t = totalesDia(fecha);
  const pct = Math.min(1, t.comido[0]/od[0]);
  const arco = document.getElementById("m-arco");
  arco.setAttribute("stroke-dashoffset", String(351.86*(1-pct)));
  arco.setAttribute("stroke", t.comido[0] > od[0]*(1+MARGEN) ? "var(--clay)" : "var(--accent)");
  document.getElementById("m-kc").textContent = nf(t.comido[0]);
  document.getElementById("m-kc-obj").textContent = "de "+nf(od[0])+" kcal";
  const box = document.getElementById("m-macros"); box.replaceChildren();
  [["Proteína",1,"var(--p)"],["Grasa",2,"var(--g)"],["Hidratos",3,"var(--c)"]].forEach(([n,i,col])=>{
    const m = el("div","m-mac");
    const pista = el("div","pista"), fill = el("div","fill");
    fill.style.width = Math.min(100, t.comido[i]/od[i]*100)+"%"; fill.style.background = col;
    pista.append(fill);
    m.append(el("span","et",n), el("span","cif",nf(t.comido[i])+" / "+nf(od[i])+" g"), pista);
    box.append(m);
  });
  // peso
  const r = registro(), lista = (r && r.peso) || [];
  const delDia = lista.find(x=>x.f===fecha);
  const inp = document.getElementById("m-peso");
  if(document.activeElement !== inp) inp.value = delDia ? String(delDia.kg).replace(".",",") : "";
  const ult = lista.filter(x=>x.f<=fecha && x.f>sumaDias(fecha,-7)).map(x=>x.kg);
  document.getElementById("m-peso-media").textContent = ult.length ? "media 7 días: "+(ult.reduce((a,b)=>a+b,0)/ult.length).toFixed(1).replace(".",",")+" kg" : "";
}

// ---------------------------------------------------------------- lista de tomas
function pintaTomas(){
  const box = document.getElementById("m-tomas"); box.replaceChildren();
  tomas(fecha).forEach(b=>{
    const st = estado(fecha, b), op = opcion(b, st.p);
    const r = st.ok ? null : calcula(fecha, b);
    const kc = st.ok ? (st.m||[0])[0] : r.tot[0];
    const art = el("article","m-toma"+(abierta===b?" abierta":""));
    const fila = el("button","m-fila");
    fila.setAttribute("aria-expanded", abierta===b ? "true":"false");
    const tx = el("span","tx"); tx.append(el("b",null,M.nombres[b]), el("small",null,op.n));
    const k = el("span","kc", nf(kc)); k.append(el("small",null, st.ok ? "comido" : "kcal"));
    const e = el("span","m-est");
    if(st.ok){ e.classList.add("ok"); e.innerHTML = CHECK; e.setAttribute("aria-label","Hecha"); }
    else if(!dentro(r.tot[0], r.obj[0])){ e.classList.add("aviso"); e.textContent="!"; e.setAttribute("aria-label","Fuera del margen"); }
    fila.append(el("span","h",M.horas[b]), tx, k, e);
    fila.addEventListener("click", ()=>{ abierta = abierta===b ? null : b; buscando=null; render(); });
    art.append(fila);
    if(abierta===b) art.append(calculadora(b));
    box.append(art);
  });
}

function calculadora(b){
  const st = estado(fecha, b), cont = el("div","m-calc");
  // plato
  const sel = el("select","m-plato"); sel.setAttribute("aria-label","Plato");
  const ops = opciones(b);
  if(b==="C"||b==="N"){
    [["C","Recetas de comida"],["N","Recetas de cena"]].forEach(([de,et])=>{
      const g = el("optgroup"); g.label = et;
      ops.filter(o=>o.de===de).forEach(o=>{ const x=el("option",null,o.n); x.value=o.clave; g.append(x); });
      sel.append(g);
    });
  } else ops.forEach(o=>{ const x=el("option",null,o.n); x.value=o.clave; sel.append(x); });
  sel.value = st.p; sel.disabled = st.ok;
  sel.addEventListener("change", ()=>{
    guardaEstado(fecha, b, {p:sel.value, it:opcion(b, sel.value).it.map(([n,g])=>[n,g,false,null]), ok:false});
    render();
  });
  cont.append(sel);

  const r = calcula(fecha, b);
  const lista = el("div","m-items");
  st.it.forEach((x, i)=>{
    const [n,,fij] = x, f = ficha(n); if(!f) return;
    const j = r.its.findIndex(it=>it.n===n), g = st.ok ? x[3] : r.g[j];
    const fila = el("div","m-it"+(fij?" fijo":"")+(g===0?" cero":""));
    const nom = el("div","nom"); nom.append(document.createTextNode(n));
    if(f[5]) { const q=el("i","cal "+f[5],f[5]); q.title=f[6]||""; nom.append(q); }
    nom.append(el("small",null, f[4]==="verdura" ? "verdura: no se toca" : fij ? "lo has fijado tú" : g===0 ? "mejor quitarlo hoy" : nf(f[0]*g/100)+" kcal"));
    const gr = el("label","gr"); const inp = el("input"); inp.type="text"; inp.inputMode="numeric";
    inp.value = String(g); inp.setAttribute("aria-label","Gramos de "+n); inp.disabled = st.ok;
    inp.addEventListener("change", ()=>{
      const v = parseFloat(inp.value.replace(",","."));
      if(!(v>=0 && v<5000)){ inp.value=String(g); return; }
      const t = estado(fecha, b); t.it[i] = [n, x[1], true, Math.round(v)];
      guardaEstado(fecha, b, t); render();
    });
    inp.addEventListener("focus", ()=>inp.select());
    gr.append(inp, el("span",null,"g"));
    const bt = el("button","m-ic");
    if(fij){ bt.innerHTML = CANDADO; bt.setAttribute("aria-pressed","true"); bt.setAttribute("aria-label","Soltar "+n+": que la calculadora lo ajuste"); }
    else { bt.innerHTML = QUITAR; bt.setAttribute("aria-label","Quitar "+n+" del plato"); }
    bt.disabled = st.ok;
    bt.addEventListener("click", ()=>{
      const t = estado(fecha, b);
      if(fij) t.it[i] = [n, x[1], false, null]; else t.it.splice(i,1);
      guardaEstado(fecha, b, t); render();
    });
    fila.append(nom, gr, bt);
    lista.append(fila);
  });
  cont.append(lista);

  if(!st.ok){
    if(buscando===b) cont.append(buscador(b));
    else { const a = el("button","m-btn","+ Añadir alimento"); a.addEventListener("click", ()=>{ buscando=b; render(); }); cont.append(a); }
  }

  // pie: total de la toma, estado y acciones
  const tot = st.ok ? st.m : r.tot, obj = st.ok ? objToma(fecha,b) : r.obj;
  const pie = el("div","m-pie");
  const f1 = el("div","fila1"); f1.append(el("b",null,nf(tot[0])+" kcal"), el("span",null,"objetivo "+nf(obj[0])));
  const pista = el("div","pista"), zona = el("i"), barra = el("em");
  const tope = Math.max(obj[0]*1.3, tot[0]*1.05);
  const mg = Math.max(MARGEN*obj[0], MARGEN_MIN);
  zona.style.left = ((obj[0]-mg)/tope*100)+"%"; zona.style.width = (2*mg/tope*100)+"%";
  barra.style.width = Math.min(100, tot[0]/tope*100)+"%";
  pista.append(zona, barra);
  const mini = el("div","mini");
  [["P",1],["G",2],["C",3]].forEach(([l,i])=>mini.append(el("span",null,l+" "+nf(tot[i])+" / "+nf(obj[i])+" g")));
  pie.append(f1, pista, mini);
  const est = el("p","m-estado");
  const dif = tot[0]-obj[0];
  if(st.ok){ est.classList.add("ok"); est.textContent = "Apuntado en tu diario."; }
  else if(dentro(tot[0], obj[0])){ est.classList.add("ok"); est.textContent = "Dentro del margen. Puedes comerlo así."; }
  else if(dif>0){ est.classList.add("aviso"); est.textContent = "Te pasas "+nf(dif)+" kcal. Si lo comes así, se restan de lo que queda del día."; }
  else { est.classList.add("aviso"); est.textContent = "Te faltan "+nf(-dif)+" kcal. Si lo dejas así, se suman a lo que queda del día."; }
  if(!st.ok && tot[1] < obj[1]*0.8 && obj[1]-tot[1] > 3)
    est.textContent += " Va justo de proteína: hoy apóyate más en la cena.";
  pie.append(est);
  if(!st.ok && dif < -Math.max(MARGEN*obj[0], MARGEN_MIN)){
    const s = acompanante(b, obj);
    if(s){ const bt = el("button","m-btn peq","Añadir "+s.n.toLowerCase()+" ("+s.g+" g)");
      bt.addEventListener("click", ()=>{ const t=estado(fecha,b); t.it.push([s.n, s.g, false, null]); guardaEstado(fecha,b,t); render(); });
      pie.append(bt); }
  }
  cont.append(pie);

  const acc = el("div","m-acc");
  if(st.ok){
    const ed = el("button","m-btn","Editar");
    ed.addEventListener("click", ()=>{ const t=estado(fecha,b); t.ok=false; delete t.m; guardaEstado(fecha,b,t); render(); });
    acc.append(ed);
  } else {
    const rs = el("button","m-btn","Restablecer");
    rs.addEventListener("click", ()=>{ const d=dia(fecha); if(d){ delete d.tomas[b]; guarda(); } render(); });
    const ok = el("button","m-btn prim","Hecho, lo he comido");
    ok.addEventListener("click", ()=>{
      const t = estado(fecha, b);
      t.it = t.it.map(x=>{ const j=r.its.findIndex(it=>it.n===x[0]); return [x[0], x[1], x[2], j>=0 ? r.g[j] : x[3]]; });
      t.ok = true; t.m = r.tot.map(v=>Math.round(v*10)/10);
      guardaEstado(fecha, b, t); abierta = null; aviso(M.nombres[b]+" apuntada"); render();
    });
    acc.append(rs, ok);
  }
  cont.append(acc);
  return cont;
}

// Si un plato se queda corto (por ejemplo, una cena usada como comida), propone el
// acompañante que mejor lo completa: se prueba cada uno y se elige el que más acerca.
function acompanante(b, obj){
  const st = estado(fecha, b), ya = new Set(st.it.map(x=>x[0]));
  const cand = ["Arroz redondo Hacendado","Pan de semillas","Patata","Pasta integral","Aceite de oliva virgen ex."].filter(n=>!ya.has(n) && M.foods[n]);
  let mejor = null;
  cand.forEach(n=>{
    const f = M.foods[n], g0 = Math.round((f[7]+f[8])/2/5)*5;
    const its = st.it.filter(x=>ficha(x[0])).map(([m,g,fij,gf])=>CALC.item(m, fij?gf:g, ficha(m), b, fij)).concat([CALC.item(n, g0, f, b, false)]);
    const g = CALC.resolver(its, obj), e = Math.abs(CALC.suma(its,g)[0]-obj[0]);
    const gn = g[g.length-1];
    if(gn>0 && (!mejor || e<mejor.e)) mejor = {n, g:gn, e};
  });
  return mejor;
}

// ---------------------------------------------------------------- añadir alimento
let CAT = null, catEstado = "sin";      // sin | cargando | ok | error
function cargaCatalogo(){
  if(catEstado!=="sin") return;
  catEstado = "cargando";
  fetch("catalogo.json").then(r=>{ if(!r.ok) throw 0; return r.json(); })
    .then(j=>{ const c=j.campos; const ix=k=>c.indexOf(k);
      CAT = j.items.map(x=>({n:x[ix("nombre")], s:x[ix("super")], k:x[ix("kcal")], p:x[ix("p")], g:x[ix("g")], c:x[ix("c")],
                             dud:x[ix("dudoso")], q:sinTildes(x[ix("nombre")]+" "+(x[ix("marca")]||""))}));
      catEstado = "ok"; if(buscando) render(); })
    .catch(()=>{ catEstado = "error"; if(buscando) render(); });
}
const TIENDA = {M:"Mercadona", L:"Lidl", C:"Carrefour"};
// Papel que se le supone a un producto del catálogo, por sus macros
function rolDe(k,p,g,c){
  if(p*4 >= 0.35*k && k>0) return ["proteina",60,250];
  if(g*9 >= 0.6*k && k>0) return ["grasa",5,40];
  if(k < 60) return ["verdura",50,250];
  return ["base",20,300];
}
function buscador(b){
  cargaCatalogo();
  const box = el("div","m-buscar");
  const inp = el("input"); inp.type="search"; inp.placeholder="Busca: pollo, yogur, arroz..."; inp.setAttribute("aria-label","Buscar alimento");
  const lista = el("div","m-res-lista"), pie = el("p","m-nota");
  const cerrar = el("button","m-btn peq","Cerrar");
  cerrar.addEventListener("click", ()=>{ buscando=null; render(); });
  const pinta = ()=>{
    lista.replaceChildren();
    const q = sinTildes(inp.value.trim()), pal = q.split(/\s+/).filter(Boolean);
    const vale = t => pal.every(w=>t.indexOf(w)>=0);
    const mios = Object.keys(M.foods).concat(Object.keys(EXTRA)).filter(n=>!pal.length || vale(sinTildes(n))).slice(0, pal.length?12:8);
    mios.forEach(n=>{ const f=ficha(n); const it=el("button","m-res-it");
      const a=el("span",null,n); a.append(el("span","m-tag","tuyo"));
      it.append(a, el("small",null,nf(f[0])+" kcal")); it.addEventListener("click", ()=>anade(b, n, f)); lista.append(it); });
    if(pal.length && CAT){
      CAT.filter(x=>vale(x.q)).slice(0,25).forEach(x=>{ const it=el("button","m-res-it");
        const a=el("span",null,x.n); a.append(el("span","m-tag",x.s.split("").map(l=>TIENDA[l]).join(", ")));
        if(x.dud) a.append(el("span","m-tag dud","kcal dudosas"));
        it.append(a, el("small",null,nf(x.k)+" kcal"));
        it.addEventListener("click", ()=>{ const [rol,lo,hi]=rolDe(x.k,x.p,x.g,x.c);
          const nom = x.n+" ("+TIENDA[x.s[0]]+")";
          EXTRA[nom] = [x.k,x.p,x.g,x.c,rol,"","",lo,hi]; anade(b, nom, EXTRA[nom]); });
        lista.append(it); });
    }
    pie.textContent = catEstado==="cargando" ? "Cargando el catálogo de Mercadona, Lidl y Carrefour..."
      : catEstado==="error" ? "El catálogo de las tiendas solo está en la app instalada. Mientras, elige entre tus alimentos."
      : catEstado==="ok" ? "Tus alimentos primero; después, los de Mercadona, Lidl y Carrefour." : "";
  };
  inp.addEventListener("input", pinta);
  box.append(inp, lista, pie, cerrar);
  pinta();
  setTimeout(()=>inp.focus(), 0);
  return box;
}
function anade(b, n, f){
  const t = estado(fecha, b);
  if(t.it.some(x=>x[0]===n)){ aviso("Ya está en el plato"); return; }
  // Lo que añades entra fijado con una ración normal: cambia los gramos si quieres
  // y el resto del plato se ajusta a su alrededor.
  const g = EXTRA[n] ? 100 : Math.round((f[7]+f[8])/2/5)*5;
  t.it.push([n, g, true, g]);
  buscando = null; guardaEstado(fecha, b, t); aviso(n+": "+g+" g. Cambia los gramos si quieres"); render();
}

// ---------------------------------------------------------------- semana
function pintaSemana(){
  const box = document.getElementById("m-barras"); box.replaceChildren();
  const ini = lunes(fecha);
  for(let i=0;i<7;i++){
    const f = sumaDias(ini, i), d = dia(f), t = totalesDia(f, d);
    const col = el("div", f===fecha ? "sel" : null), bar = el("div","b");
    if(d && t.n){
      const od = objDia(f), r = t.comido[0]/od[0];
      bar.style.height = Math.max(4, Math.min(100, r*80))+"%";
      const completo = tomas(f).every(b=>{ const e=d.tomas[b]; return e && e.ok; });
      bar.classList.add(!completo && r<=1+MARGEN ? "curso" : dentro(t.comido[0], od[0]) ? "ok" : r>1 ? "alto" : "bajo");
      bar.title = nf(t.comido[0])+" de "+nf(od[0])+" kcal";
    }
    col.append(bar, el("span",null,CORTO[deIso(f).getDay()]));
    col.addEventListener("click", ()=>{ fecha=f; abierta=null; render(); });
    box.append(col);
  }
  const ns = Object.keys(D.dias).length, nw = Object.keys(D.semanas).length;
  document.getElementById("m-guardado").textContent = "En este móvil: "+ns+(ns===1?" día":" días")+" con detalle"+
    (nw ? " y "+nw+(nw===1?" semana resumida":" semanas resumidas") : "")+". Guarda una copia de vez en cuando.";
}

// ---------------------------------------------------------------- copia de seguridad
document.getElementById("m-exp").addEventListener("click", ()=>{
  const blob = new Blob([JSON.stringify({app:"gym_diet_2027", tipo:"diario", v:1, diario:D, extra:EXTRA}, null, 1)], {type:"application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "diario_"+hoy()+".json";
  document.body.append(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
  aviso("Copia descargada: guárdala en tu carpeta del gimnasio");
});
document.getElementById("m-imp").addEventListener("click", ()=>document.getElementById("m-imp-f").click());
document.getElementById("m-imp-f").addEventListener("change", function(){
  const f = this.files && this.files[0]; if(!f) return;
  f.text().then(t=>{ const j=JSON.parse(t);
    if(!j || j.tipo!=="diario" || !j.diario || !j.diario.dias) throw 0;
    D = Object.assign(vacio(), j.diario); EXTRA = j.extra || {}; guarda(); compacta(); render(); aviso("Copia recuperada");
  }).catch(()=>aviso("Ese archivo no es una copia del diario"));
  this.value = "";
});

// ---------------------------------------------------------------- controles
document.getElementById("m-prev").addEventListener("click", ()=>{ fecha=sumaDias(fecha,-1); abierta=null; render(); });
document.getElementById("m-next").addEventListener("click", ()=>{ fecha=sumaDias(fecha,1); abierta=null; render(); });
document.getElementById("m-hoy").addEventListener("click", ()=>{ fecha=hoy(); abierta=null; render(); });
document.getElementById("m-fase").addEventListener("change", function(){
  faseManual = this.value; try{ localStorage.setItem("menu_fase", JSON.stringify(this.value)); }catch(e){}
  asegura(fecha).fase = this.value; guarda(); render();
});
document.getElementById("m-tipo").addEventListener("change", function(){
  asegura(fecha).tipo = this.value; guarda(); abierta=null; render();
});
document.getElementById("m-peso-ok").addEventListener("click", ()=>{
  const v = parseFloat(document.getElementById("m-peso").value.replace(",","."));
  if(!(v>30 && v<250)){ aviso("Ese peso no parece correcto"); return; }
  guardaPeso(fecha, Math.round(v*10)/10); aviso("Peso guardado"); render();
});
window.addEventListener("gd:peso", ()=>pintaResumen());

function render(){ pintaCabecera(); pintaResumen(); pintaTomas(); pintaSemana(); }
compacta();
render();
