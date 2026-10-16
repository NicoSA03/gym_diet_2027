// Menús v2.3: lista del día, calculadora de raciones, diario, tus productos escaneados
// y tus platos. Los datos del plan (M) los genera menu/payload3.py. La cuenta de
// raciones está en menu/calculadora.js (CALC), la cámara en menu/escaner.js (ESCANER)
// y el guardado y la revisión de tus platos en menu/mis_platos.js (MIS_PLATOS). Aquí
// solo se pinta y se guarda en el navegador.

const DIAS_SEM = ["Domingo","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"];
const CORTO = ["D","L","M","X","J","V","S"];
const MES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
const TIPO_DE = {1:"A",2:"B",3:"A",4:"B",5:"C",6:"D",0:"E"};   // getDay() -> tipo de día
const KEY = "diario_v1", KEY_EXTRA = "menu_extra_v1", KEY_REG = "registro_v1", KEY_PROD = "mis_productos_v1";
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
let fecha = hoy(), abierta = null, buscando = null, eligiendo = null, verProductos = false;
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
// Tus platos (v2.3) se añaden al final con la clave «U» + su número. Los de comida
// y cena se comparten entre las dos, igual que los del plan.
function opciones(b){
  const cn = b==="C"||b==="N";
  const mios = MIS_PLATOS.deTomas(cn ? ["C","N"] : [b]).map(x=>({clave:"U"+x.id, n:x.n, de:x.t, it:x.it, mio:true}));
  return (cn ? M.principales.map((p,i)=>({clave:"P"+i, n:p.n, de:p.de, it:p.it}))
             : M.bloques[b].ops.map((o,i)=>({clave:"O"+i, n:o.n, it:o.it}))).concat(mios);
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
    fila.addEventListener("click", ()=>{ abierta = abierta===b ? null : b; buscando=null; eligiendo=null; render(); });
    art.append(fila);
    if(abierta===b) art.append(calculadora(b));
    box.append(art);
  });
}

function calculadora(b){
  const st = estado(fecha, b), cont = el("div","m-calc");
  // plato: botón con el nombre; al tocarlo se abre la lista con un buscador arriba
  const actual = opcion(b, st.p);
  const bp = el("button","m-plato");
  bp.setAttribute("aria-expanded", eligiendo===b ? "true" : "false");
  bp.append(el("span",null,actual.n), el("span","flecha",eligiendo===b ? "\u25B4" : "\u25BE"));
  bp.disabled = st.ok;
  bp.addEventListener("click", ()=>{ eligiendo = eligiendo===b ? null : b; buscando = null; render(); });
  cont.append(bp);
  if(eligiendo===b && !st.ok) cont.append(selectorPlato(b, actual));

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

// Lista de platos para elegir. Comida y cena comparten platos: si un nombre existe
// en las dos, se queda una sola vez (la receta de esta toma).
function platosDe(b){
  const ops = opciones(b);
  if(b!=="C" && b!=="N") return ops;
  const vistos = {};
  ops.forEach(o=>{ if(!vistos[o.n] || o.de===b) vistos[o.n] = o; });
  return Object.values(vistos).sort((x,y)=>x.n.localeCompare(y.n,"es"));
}
function selectorPlato(b, actual){
  const box = el("div","m-elegir");
  const inp = el("input"); inp.type="search"; inp.placeholder="Busca un plato o un ingrediente";
  inp.setAttribute("aria-label","Buscar plato");
  const lista = el("div","m-res-lista");
  const todos = platosDe(b);
  const pinta = ()=>{
    lista.replaceChildren();
    const pal = sinTildes(inp.value.trim()).split(/\s+/).filter(Boolean);
    const vale = o => { const t = sinTildes(o.n+" "+o.it.map(x=>x[0]).join(" ")); return pal.every(w=>t.indexOf(w)>=0); };
    const res = todos.filter(vale);
    res.forEach(o=>{
      const it = el("button","m-res-it"+(o.n===actual.n ? " sel" : ""));
      const nm = el("span",null,o.n); if(o.mio) nm.append(el("span","m-tag","tuyo"));
      it.append(nm);
      if(o.n===actual.n) it.append(el("small",null,"elegido"));
      it.addEventListener("click", ()=>{
        guardaEstado(fecha, b, {p:o.clave, it:o.it.map(([n,g])=>[n,g,false,null]), ok:false});
        eligiendo = null; render();
      });
      lista.append(it);
    });
    if(!res.length) lista.append(el("p","m-nota","Ningún plato con eso. Prueba con otra palabra."));
  };
  inp.addEventListener("input", pinta);
  const crear = el("button","m-btn peq","+ Crear un plato nuevo");
  crear.addEventListener("click", ()=>fichaPlato(0, b));
  box.append(inp, lista, crear);
  pinta();
  setTimeout(()=>inp.focus(), 0);
  return box;
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
let CAT = null, CAT_EAN = {}, catEstado = "sin", catPromesa = null;   // sin | cargando | ok | error
function cargaCatalogo(){
  if(catPromesa) return catPromesa;
  catEstado = "cargando";
  catPromesa = fetch("catalogo.json").then(r=>{ if(!r.ok) throw 0; return r.json(); })
    .then(j=>{ const c=j.campos; const ix=k=>c.indexOf(k);
      CAT = j.items.map(x=>({n:x[ix("nombre")], m:x[ix("marca")], s:x[ix("super")], k:x[ix("kcal")], p:x[ix("p")], g:x[ix("g")], c:x[ix("c")],
                             dud:x[ix("dudoso")], q:sinTildes(x[ix("nombre")]+" "+(x[ix("marca")]||""))}));
      // índice por código de barras, para el escáner (los UPC de 12 cifras, con un 0 delante)
      CAT_EAN = {};
      j.items.forEach((x,i)=>{ let e = x[ix("ean")]; if(!e) return; e = String(e); if(e.length===12) e = "0"+e;
        if(!CAT_EAN[e]) CAT_EAN[e] = CAT[i]; });
      catEstado = "ok"; if(buscando) render(); })
    .catch(()=>{ catEstado = "error"; if(buscando) render(); });
  return catPromesa;
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
  const fila = el("div","m-buscar-fila");
  const inp = el("input"); inp.type="search"; inp.placeholder="Busca: pollo, yogur, arroz..."; inp.setAttribute("aria-label","Buscar alimento");
  const esc = el("button","m-btn m-esc-btn"); esc.innerHTML = BARRAS; esc.append(document.createTextNode("Escanear"));
  esc.setAttribute("aria-label","Escanear el código de barras de un producto");
  esc.addEventListener("click", ()=>escanea(b));
  fila.append(inp, esc);
  const lista = el("div","m-res-lista"), pie = el("p","m-nota");
  const cerrar = el("button","m-btn peq","Cerrar");
  cerrar.addEventListener("click", ()=>{ buscando=null; render(); });
  const pinta = ()=>{
    lista.replaceChildren();
    const q = sinTildes(inp.value.trim()), pal = q.split(/\s+/).filter(Boolean);
    const vale = t => pal.every(w=>t.indexOf(w)>=0);
    const fila = (n, f, tag, accion) => { const it=el("button","m-res-it");
      const a=el("span",null,n); a.append(el("span","m-tag",tag));
      it.append(a, el("small",null,nf(f[0])+" kcal")); it.addEventListener("click", accion); lista.append(it); };
    // 1. tus productos escaneados
    const mp = Object.keys(PROD.p).filter(e=>!pal.length || vale(sinTildes(PROD.p[e][0]))).slice(0, pal.length?12:6);
    const deProductos = new Set(Object.keys(PROD.p).map(claveProducto));
    mp.forEach(e=>{ const x = PROD.p[e]; fila(x[0], x.slice(2,6), nombreEtq(x[1]), ()=>anadeProducto(b, e)); });
    // 2. los alimentos del plan y los que ya añadiste del catálogo
    const mios = Object.keys(M.foods).concat(Object.keys(EXTRA).filter(n=>!deProductos.has(n)))
      .filter(n=>!pal.length || vale(sinTildes(n))).slice(0, pal.length?12:6);
    mios.forEach(n=>{ const f=ficha(n); fila(n, f, M.foods[n] ? "del plan" : "añadido", ()=>anade(b, n, f)); });
    // 3. el catálogo de las tiendas
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
      : catEstado==="ok" ? "Primero lo tuyo; después, los de Mercadona, Lidl y Carrefour." : "";
  };
  inp.addEventListener("input", pinta);
  box.append(fila, lista, pie, cerrar);
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

// ---------------------------------------------------------------- mis productos (v2.1)
// Lo que escaneas se guarda en este móvil, en la clave mis_productos_v1, así de corto:
//   {v:1, etq:[[id, nombre], ...], p:{código: [nombre, etiqueta, kcal, P, G, C, fecha]}}
// Macros por 100 g con un decimal. Las etiquetas fijas (Tuyo, Mercadona, Lidl,
// Carrefour) no se guardan: solo las que creas tú. Cada producto ocupa unos 80 bytes,
// así que mil productos son menos de 100 KB.
const ETQ_FIJAS = [["T","Tuyo"],["M","Mercadona"],["L","Lidl"],["C","Carrefour"]];
const BARRAS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M3 7V4h3M18 4h3v3M21 17v3h-3M6 20H3v-3M7 8v8M10 8v8M13 8v8M17 8v8"/></svg>';
// Marcas propias de cada tienda, para adivinar la etiqueta de lo que viene de Open Food Facts
const MARCAS = {M:["hacendado","deliplus","bosque verde"], L:["milbona","pilos","alesto","crownfield","solevita","chef select","combino","baresa","freeway","vitasia"], C:["carrefour"]};

function esFija(id){ return ETQ_FIJAS.some(f=>f[0]===id); }
function normalizaProd(d){
  d = d || {};
  return {v:1, etq: ETQ_FIJAS.concat((d.etq||[]).filter(e=>Array.isArray(e) && !esFija(e[0]))), p: d.p || {}};
}
let PROD = normalizaProd(leeJSON(KEY_PROD, null));
function prodParaGuardar(){ return {v:1, etq:PROD.etq.filter(e=>!esFija(e[0])), p:PROD.p}; }
function guardaProductos(){
  try{ localStorage.setItem(KEY_PROD, JSON.stringify(prodParaGuardar())); return true; }
  catch(e){ aviso("No se ha podido guardar: el navegador tiene el almacenamiento lleno o bloqueado."); return false; }
}
function nombreEtq(id){ const e = PROD.etq.find(x=>x[0]===id); return e ? e[1] : "Tuyo"; }
// Nombre con el que entra en un plato: «Yogur natural (Mercadona)»; los tuyos, sin apellido
function claveProducto(e){
  const x = PROD.p[e]; let k = x[1]==="T" ? x[0] : x[0]+" ("+nombreEtq(x[1])+")";
  if(M.foods[k]) k += " (escaneado)";
  return k;
}
// Al añadirlo a un plato se copia a EXTRA: así el diario sigue bien aunque luego lo
// cambies o lo borres de Mis productos.
function anadeProducto(b, e){
  const x = PROD.p[e], k = claveProducto(e), [rol,lo,hi] = rolDe(x[2],x[3],x[4],x[5]);
  EXTRA[k] = [x[2],x[3],x[4],x[5],rol,"","",lo,hi];
  anade(b, k, EXTRA[k]);
}

function sugiereNombre(n, marca){
  n = (n||"").replace(/\s+/g," ").trim(); marca = (marca||"").trim();
  if(marca && sinTildes(n).indexOf(sinTildes(marca)) < 0) n = (n ? n+" " : "")+marca;
  return (n.charAt(0).toUpperCase()+n.slice(1)).slice(0, 60);
}
function etqDeOFF(tiendas, marcas){
  const slug = t => sinTildes(t).trim().replace(/\s+/g,"-");
  const ts = tiendas.map(t=>String(t).replace(/^[a-z]{2}:/,""));
  const porTienda = PROD.etq.find(e=>e[0]!=="T" && ts.some(t=>t===slug(e[1]) || t.indexOf(slug(e[1])+"-")===0));
  if(porTienda) return porTienda[0];
  const m = sinTildes(marcas);
  for(const id in MARCAS) if(MARCAS[id].some(x=>m.indexOf(x)>=0)) return id;
  return "T";
}
function buscaOFF(c){
  const ctl = window.AbortController ? new AbortController() : null;
  const t = setTimeout(()=>{ if(ctl) ctl.abort(); }, 8000);
  const url = "https://world.openfoodfacts.org/api/v2/product/"+c+".json?fields=product_name_es,product_name,brands,stores_tags,nutriments";
  return fetch(url, ctl ? {signal:ctl.signal} : {})
    .then(r=>r.ok ? r.json() : null)
    .then(j=>{
      clearTimeout(t);
      if(!j || j.status!==1 || !j.product) return null;
      const p = j.product, n = p.nutriments || {};
      const num = v => { const x = parseFloat(v); return isFinite(x) && x>=0 ? Math.round(x*10)/10 : null; };
      let k = num(n["energy-kcal_100g"]);
      if(k===null && num(n["energy_100g"])!==null) k = Math.round(num(n["energy_100g"])/4.184);   // viene en kJ
      return {nombre: sugiereNombre(p.product_name_es || p.product_name, (p.brands||"").split(",")[0]),
              etq: etqDeOFF(p.stores_tags||[], p.brands||""),
              m: [k, num(n.proteins_100g), num(n.fat_100g), num(n.carbohydrates_100g)]};
    })
    .catch(()=>{ clearTimeout(t); return null; });
}

// Capa a pantalla completa para la ficha del producto (se cierra con Cancelar o Esc)
function abreCapa(titulo){
  const capa = el("div","prod-capa"), panel = el("div","prod-panel");
  panel.setAttribute("role","dialog"); panel.setAttribute("aria-modal","true"); panel.setAttribute("aria-label", titulo);
  capa.append(panel); document.body.append(capa);
  const tecla = e=>{ if(e.key==="Escape") cierra(); };
  function cierra(){ document.removeEventListener("keydown", tecla); capa.remove(); }
  document.addEventListener("keydown", tecla);
  return {capa, panel, cierra};
}

// Escanear: b es la toma a la que se añadirá (o null si vienes de Mis productos)
function escanea(b){ ESCANER.abrir(c=>buscaCodigo(c, b)); }
async function buscaCodigo(c, b){
  if(PROD.p[c]) return fichaProducto({ean:c, b, editar:true});
  const v = abreCapa("Buscando el producto");
  v.panel.append(el("p","prod-buscando","Buscando el código "+c+"..."));
  await cargaCatalogo();
  const x = CAT_EAN[c];
  let o;
  if(x) o = {nombre: sugiereNombre(x.n, x.m), etq: x.s[0], m:[x.k,x.p,x.g,x.c],
             origen: "Está en el catálogo de "+x.s.split("").map(l=>TIENDA[l]).join(", ")+". Pon el nombre que quieras."};
  else {
    const off = await buscaOFF(c);
    o = off ? Object.assign(off, {origen:"Datos de Open Food Facts, una base abierta: comprueba que cuadran con la etiqueta."})
            : {nombre:"", etq:"T", m:[null,null,null,null],
               origen: navigator.onLine===false ? "Sin conexión no puedo buscarlo fuera. Copia los datos de la etiqueta (por 100 g)."
                                                : "No lo encuentro en ningún sitio. Copia los datos de la etiqueta (por 100 g)."};
  }
  v.cierra();
  fichaProducto(Object.assign(o, {ean:c, b}));
}

// Ficha de un producto: nombre, etiqueta y macros por 100 g
function fichaProducto(o){
  const viejo = o.editar ? PROD.p[o.ean] : null;
  if(viejo) Object.assign(o, {nombre:viejo[0], etq:viejo[1], m:viejo.slice(2,6),
    origen:"Guardado el "+deIso(viejo[6]||hoy()).toLocaleDateString("es-ES")+"."});
  const v = abreCapa(viejo ? "Editar producto" : "Producto nuevo"), p = v.panel;
  let etq = PROD.etq.some(e=>e[0]===o.etq) ? o.etq : "T";
  p.append(el("h2",null, viejo ? "Editar producto" : "Producto nuevo"),
           el("p","prod-cod","Código "+o.ean), el("p","m-nota",o.origen));

  const cNom = el("label","prod-campo"), nom = el("input");
  nom.value = o.nombre || ""; nom.maxLength = 60; nom.placeholder = "Por ejemplo: Yogur griego ligero";
  cNom.append(el("span",null,"Nombre"), nom);

  const cEtq = el("div","prod-campo"), chips = el("div","prod-etqs");
  const nueva = el("form","prod-nueva"); nueva.hidden = true;
  const inpN = el("input"); inpN.maxLength = 20; inpN.placeholder = "Por ejemplo: Dia"; inpN.setAttribute("aria-label","Nombre de la etiqueta nueva");
  const okN = el("button","m-btn peq","Crear"); okN.type = "submit";
  nueva.append(inpN, okN);
  const pintaChips = ()=>{
    chips.replaceChildren();
    PROD.etq.forEach(([id, n])=>{
      const ch = el("button","prod-chip", n); ch.type = "button";
      ch.setAttribute("aria-pressed", id===etq ? "true" : "false");
      ch.addEventListener("click", ()=>{ etq = id; pintaChips(); });
      chips.append(ch);
    });
    const mas = el("button","prod-chip mas","+ Nueva"); mas.type = "button";
    mas.addEventListener("click", ()=>{ nueva.hidden = false; inpN.focus(); });
    chips.append(mas);
  };
  nueva.addEventListener("submit", e=>{
    e.preventDefault();
    const n = inpN.value.replace(/\s+/g," ").trim(); if(!n) return;
    const ya = PROD.etq.find(x=>sinTildes(x[1])===sinTildes(n));
    if(ya) etq = ya[0];
    else {
      let i = 1; while(PROD.etq.some(x=>x[0]==="X"+i)) i++;
      PROD.etq.push(["X"+i, n.charAt(0).toUpperCase()+n.slice(1)]); etq = "X"+i;
      guardaProductos();
    }
    inpN.value = ""; nueva.hidden = true; pintaChips();
  });
  pintaChips();
  cEtq.append(el("span",null,"Etiqueta"), chips, nueva);

  const cMac = el("div","prod-campo"), rej = el("div","prod-macros");
  const campos = [["Kcal","kcal"],["Proteína","g"],["Grasa","g"],["Hidratos","g"]].map(([n,u],i)=>{
    const l = el("label"), inp = el("input"); inp.inputMode = "decimal";
    inp.value = o.m && o.m[i]!==null && o.m[i]!==undefined ? String(o.m[i]).replace(".",",") : "";
    l.append(el("span",null,n), inp, el("small",null,u)); rej.append(l); return inp;
  });
  const avisoM = el("p","prod-aviso"); avisoM.hidden = true;
  cMac.append(el("span",null,"Por cada 100 g"), rej, avisoM);

  const lee = ()=>campos.map(x=>{ const t = x.value.replace(",",".").trim(); return t==="" ? null : parseFloat(t); });
  const revisa = ()=>{
    const [k,pp,g,c] = lee();
    if(k>0 && pp!==null && g!==null && c!==null){
      const cuenta = 4*pp+4*c+9*g;
      if(Math.abs(cuenta-k) > Math.max(15, 0.2*k)){
        avisoM.textContent = "Las kcal no cuadran con los macros (darían unas "+nf(cuenta)+"). Revisa la etiqueta."; avisoM.hidden = false; return;
      }
    }
    avisoM.hidden = true;
  };
  campos.forEach(x=>x.addEventListener("input", revisa));
  revisa();

  const err = el("p","prod-err"); err.hidden = true;
  const acc = el("div","prod-acc");
  const guardar = anadir=>{
    const n = nom.value.replace(/\s+/g," ").trim();
    let [k,pp,g,c] = lee();
    const fallo = t=>{ err.textContent = t; err.hidden = false; };
    if(!n) return fallo("Ponle un nombre.");
    if([k,pp,g,c].some(x=>x!==null && !(x>=0))) return fallo("Revisa los números: solo cifras.");
    pp = pp||0; g = g||0; c = c||0;
    if(k===null) k = Math.round(4*pp+4*c+9*g);
    if(!(k>0 && k<=900)) return fallo("Faltan las kcal por 100 g (están en la etiqueta).");
    if(pp+g+c > 100.5) return fallo("Proteína, grasa e hidratos suman más de 100 g: revisa que sean por 100 g.");
    const r1 = x=>Math.round(x*10)/10;
    const choca = Object.keys(PROD.p).find(e=>e!==o.ean && PROD.p[e][1]===etq && sinTildes(PROD.p[e][0])===sinTildes(n));
    if(choca) return fallo("Ya tienes otro producto con ese nombre y esa etiqueta.");
    PROD.p[o.ean] = [n, etq, r1(k), r1(pp), r1(g), r1(c), viejo ? viejo[6] : hoy()];
    if(!guardaProductos()) return;
    v.cierra();
    if(anadir && o.b){ anadeProducto(o.b, o.ean); }
    else { aviso(viejo ? "Producto actualizado" : "Guardado en Mis productos"); render(); }
  };
  if(viejo){
    const borra = el("button","m-btn borrar","Borrar"); let seguro = false;
    borra.addEventListener("click", ()=>{
      if(!seguro){ seguro = true; borra.textContent = "Toca otra vez para borrar"; return; }
      delete PROD.p[o.ean]; guardaProductos(); v.cierra(); aviso("Producto borrado"); render();
    });
    acc.append(borra);
  }
  const cancel = el("button","m-btn","Cancelar"); cancel.addEventListener("click", v.cierra);
  const bg = el("button","m-btn"+(o.b ? "" : " prim"),"Guardar"); bg.addEventListener("click", ()=>guardar(false));
  acc.append(cancel, bg);
  if(o.b){ const ba = el("button","m-btn prim","Guardar y añadir a "+M.nombres[o.b].toLowerCase()); ba.addEventListener("click", ()=>guardar(true)); acc.append(ba); }
  p.append(cNom, cEtq, cMac, err, acc);
  // sin poner el cursor en el nombre: en el móvil sacaría el teclado y taparía la ficha
}

// Tarjeta «Mis productos» en la página
function pintaProductos(){
  const ks = Object.keys(PROD.p), n = ks.length;
  document.getElementById("m-prod-n").textContent = n ? n+(n===1 ? " producto guardado" : " productos guardados")+" en este móvil."
    : "Escanea un producto para tenerlo a mano al añadir alimentos.";
  const ver = document.getElementById("m-prod-ver"), box = document.getElementById("m-prod-lista");
  ver.hidden = !n; ver.textContent = verProductos ? "Ocultar la lista" : "Ver la lista";
  box.hidden = !(n && verProductos); box.replaceChildren();
  if(!n || !verProductos) return;
  let filtro = "";
  const lista = el("div","m-res-lista");
  const pinta = ()=>{
    lista.replaceChildren();
    const pal = sinTildes(filtro.trim()).split(/\s+/).filter(Boolean);
    ks.filter(e=>{ const t = sinTildes(PROD.p[e][0]+" "+nombreEtq(PROD.p[e][1])); return pal.every(w=>t.indexOf(w)>=0); })
      .sort((a,b)=>(PROD.p[b][6]||"").localeCompare(PROD.p[a][6]||"") || PROD.p[a][0].localeCompare(PROD.p[b][0],"es"))
      .forEach(e=>{ const x = PROD.p[e], it = el("button","m-res-it");
        const a = el("span",null,x[0]); a.append(el("span","m-tag",nombreEtq(x[1])));
        it.append(a, el("small",null,nf(x[2])+" kcal"));
        it.addEventListener("click", ()=>fichaProducto({ean:e, b:null, editar:true}));
        lista.append(it); });
    if(!lista.children.length) lista.append(el("p","m-nota","Ninguno con eso."));
  };
  if(n > 8){
    const inp = el("input","m-prod-filtro"); inp.type = "search"; inp.placeholder = "Busca en tus productos"; inp.setAttribute("aria-label","Buscar en tus productos");
    inp.addEventListener("input", ()=>{ filtro = inp.value; pinta(); });
    box.append(inp);
  }
  box.append(lista); pinta();
}
document.getElementById("m-prod-esc").innerHTML = BARRAS + "Escanear";
document.getElementById("m-prod-esc").addEventListener("click", ()=>escanea(null));
document.getElementById("m-prod-ver").addEventListener("click", ()=>{ verProductos = !verProductos; pintaProductos(); });

// ---------------------------------------------------------------- mis platos (v2.3)
// Crear un plato: nombre, toma e ingredientes con sus gramos, solo con alimentos de
// datos/alimentos.csv. Al guardar sale la revisión con las cantidades lógicas, las que
// hacen que el plato encaje con el resto de su toma (MIS_PLATOS.revisa, en mis_platos.js).
// El plato se puede elegir en la app al momento; para pasarlo a datos/platos.csv se
// exporta y se importa con «python3 actualizar.py --importar platos_app.csv».
let verPlatos = false;
const nomToma = t => M.nombres[t] || t;
const racionTipica = n => { const f = M.foods[n]; return Math.max(5, Math.round((f[7]+f[8])/2/5)*5); };

function fichaPlato(id, toma){
  const viejo = id ? MIS_PLATOS.uno(id) : null;
  const st = viejo ? {n:viejo.n, t:viejo.t, it:viejo.it.map(x=>x.slice()), no:viejo.no||""}
                   : {n:"", t:(toma && M.base[toma]) ? toma : "C", it:[], no:""};
  const v = abreCapa(viejo ? "Editar plato" : "Plato nuevo");
  edita();

  function edita(){
    const p = v.panel; p.replaceChildren();
    p.append(el("h2",null, viejo ? "Editar plato" : "Plato nuevo"),
      el("p","m-nota","Con los alimentos de tu plan. Al guardar te digo qué cantidades encajan con el resto de platos de esa toma."));

    const cNom = el("label","prod-campo"), nom = el("input");
    nom.value = st.n; nom.maxLength = 60; nom.placeholder = "Por ejemplo: Arroz con pavo y calabacín";
    nom.addEventListener("input", ()=>{ st.n = nom.value; });
    cNom.append(el("span",null,"Nombre"), nom);

    const cT = el("div","prod-campo"), chips = el("div","prod-etqs");
    const pintaChips = ()=>{
      chips.replaceChildren();
      M.orden.forEach(t=>{
        const ch = el("button","prod-chip", nomToma(t)); ch.type = "button";
        ch.setAttribute("aria-pressed", t===st.t ? "true" : "false");
        ch.addEventListener("click", ()=>{ st.t = t; pintaChips(); pintaRes(); });
        chips.append(ch);
      });
    };
    cT.append(el("span",null,"Toma"), chips);

    const cIng = el("div","prod-campo"), filas = el("div","m-items");
    const pintaIng = ()=>{
      filas.replaceChildren();
      if(!st.it.length) filas.append(el("p","m-nota","Aún no hay ingredientes. Búscalos aquí debajo."));
      st.it.forEach((x, i)=>{
        const n = x[0], f = M.foods[n];
        const fila = el("div","m-it"), nm = el("div","nom"), kc = el("small");
        const pintaKc = ()=>{ kc.textContent = f ? nf(f[0]*st.it[i][1]/100)+" kcal" : "ya no está en tu plan: quítalo"; };
        nm.append(document.createTextNode(n), kc); pintaKc();
        const gr = el("label","gr"), inp = el("input"); inp.type = "text"; inp.inputMode = "numeric";
        inp.value = String(x[1]); inp.setAttribute("aria-label","Gramos de "+n);
        inp.addEventListener("focus", ()=>inp.select());
        inp.addEventListener("input", ()=>{
          const g = parseFloat(inp.value.replace(",","."));
          if(g>0 && g<5000){ st.it[i][1] = Math.round(g); pintaKc(); pintaRes(); }
        });
        gr.append(inp, el("span",null,"g"));
        const bt = el("button","m-ic"); bt.type = "button"; bt.innerHTML = QUITAR; bt.setAttribute("aria-label","Quitar "+n);
        bt.addEventListener("click", ()=>{ st.it.splice(i,1); pintaIng(); pintaRes(); });
        fila.append(nm, gr, bt); filas.append(fila);
      });
    };
    const bus = el("input"); bus.type = "search"; bus.placeholder = "Añade un ingrediente: arroz, pollo..."; bus.setAttribute("aria-label","Buscar ingrediente");
    const res = el("div","m-res-lista");
    const pintaBus = ()=>{
      res.replaceChildren();
      const pal = sinTildes(bus.value.trim()).split(/\s+/).filter(Boolean);
      if(!pal.length) return;
      const ya = new Set(st.it.map(x=>x[0]));
      const hits = Object.keys(M.foods).filter(n=>!ya.has(n) && pal.every(w=>sinTildes(n).indexOf(w)>=0)).slice(0, 8);
      hits.forEach(n=>{
        const it = el("button","m-res-it"); it.type = "button";
        it.append(el("span",null,n), el("small",null,nf(M.foods[n][0])+" kcal/100 g"));
        it.addEventListener("click", ()=>{ st.it.push([n, racionTipica(n)]); bus.value = ""; pintaBus(); pintaIng(); pintaRes(); });
        res.append(it);
      });
      if(!hits.length) res.append(el("p","m-nota","No está en tu plan. Para usarlo, añádelo antes a datos/alimentos.csv."));
    };
    bus.addEventListener("input", pintaBus);
    cIng.append(el("span",null,"Ingredientes, en gramos de la receta"), filas, bus, res);

    const resu = el("p","m-nota");
    const pintaRes = ()=>{
      const b = M.base[st.t], t = MIS_PLATOS.totales(st.it);
      resu.textContent = (st.it.length ? "Tu receta: "+nf(t[0])+" kcal y "+nf(t[1])+" g de proteína. " : "")+
        "Los platos de "+nomToma(st.t).toLowerCase()+" rondan "+nf(b.m[0])+" kcal y "+nf(b.m[1])+" g de proteína.";
    };

    const cNo = el("label","prod-campo"), no = el("input");
    no.value = st.no; no.maxLength = 120; no.placeholder = "Opcional: cómo se prepara";
    no.addEventListener("input", ()=>{ st.no = no.value; });
    cNo.append(el("span",null,"Notas"), no);

    const err = el("p","prod-err"); err.hidden = true;
    const acc = el("div","prod-acc");
    if(viejo){
      const borra = el("button","m-btn borrar","Borrar"); let seguro = false;
      borra.addEventListener("click", ()=>{
        if(!seguro){ seguro = true; borra.textContent = "Toca otra vez para borrar"; return; }
        MIS_PLATOS.quita(viejo.id); v.cierra(); aviso("Plato borrado"); render();
      });
      acc.append(borra);
    }
    const cancel = el("button","m-btn","Cancelar"); cancel.addEventListener("click", v.cierra);
    const sig = el("button","m-btn prim","Guardar");
    sig.addEventListener("click", ()=>{
      const n = st.n.replace(/\s+/g," ").trim();
      const fallo = t=>{ err.textContent = t; err.hidden = false; };
      if(!n) return fallo("Ponle un nombre.");
      if(/[|;]/.test(n)) return fallo("El nombre no puede llevar «|» ni «;».");
      if(MIS_PLATOS.nombreOcupado(st.t, n, viejo ? viejo.id : 0)) return fallo("Ya hay un plato con ese nombre en "+nomToma(st.t).toLowerCase()+".");
      if(!st.it.length) return fallo("Añade al menos un ingrediente.");
      if(st.it.some(x=>!M.foods[x[0]])) return fallo("Quita los ingredientes que ya no están en tu plan.");
      st.n = n; revision();
    });
    acc.append(cancel, sig);
    p.append(cNom, cT, cIng, resu, cNo, err, acc);
    pintaChips(); pintaIng(); pintaRes();
    // sin poner el cursor en el nombre: en el móvil sacaría el teclado y taparía la ficha
  }

  // La revisión: tus cantidades al lado de las lógicas, y tú eliges con cuáles se guarda
  function revision(){
    const p = v.panel; p.replaceChildren();
    const r = MIS_PLATOS.revisa(st.t, st.it), b = r.base, tn = nomToma(st.t).toLowerCase();
    const lo = b.m[0]-b.tope, hi = b.m[0]+b.tope;
    p.append(el("h2",null,"Revisa las cantidades"));
    p.append(el("p","m-estado "+(r.encaja ? "ok" : "aviso"), r.encaja
      ? "Tus cantidades encajan con el resto de platos de "+tn+": "+nf(r.tot[0])+" kcal, y lo normal es de "+nf(lo)+" a "+nf(hi)+"."
      : "Así no encaja con el resto de platos de "+tn+": tu receta tiene "+nf(r.tot[0])+" kcal y lo normal es de "+nf(lo)+" a "+nf(hi)+"."));
    r.raciones.forEach(x=>p.append(el("p","prod-aviso", x.n+": "+x.g+" g es una ración rara (lo normal, de "+nf(x.lo)+" a "+nf(x.hi)+" g).")));
    if(r.afecta.length) p.append(el("p","prod-aviso","Con este plato la media de "+tn+" se mueve y se saldrían del margen: "+r.afecta.join(", ")+"."));
    p.append(el("p","m-nota","Las cantidades lógicas son las que dejan el plato en la media de "+tn+" ("+nf(b.m[0])+" kcal) sin cambiar su forma: la verdura no se toca y la proteína se mantiene."));

    const tabla = el("div","pla-tabla");
    const fila = (cls, a, b2, c)=>{ const f = el("div","pla-fila"+(cls ? " "+cls : "")); f.append(el("span",null,a), el("span",null,b2), el("span",null,c)); tabla.append(f); };
    fila("cab", "Ingrediente", "Tuyas", "Lógicas");
    r.logicas.forEach(([n, gl])=>{
      const g = st.it.find(x=>x[0]===n)[1];
      fila(Math.abs(gl-g) >= Math.max(5, 0.1*g) ? "cambia" : "", n, g+" g", gl>0 ? gl+" g" : "quitar");
    });
    fila("tot", "Kcal", nf(r.tot[0]), nf(r.totL[0]));
    fila("tot2", "Proteína", nf(r.tot[1])+" g", nf(r.totL[1])+" g");
    p.append(tabla);

    if(!r.logicasOk) p.append(el("p","prod-aviso","Ni con estas cantidades llega a encajar: cambia o añade algún ingrediente (una base como arroz o patata, o una proteína)."));
    p.append(el("p","m-nota","Son los gramos de la receta base. Cada día la calculadora los ajusta a lo que te toca, guardes las que guardes."));
    if(!r.encaja) p.append(el("p","m-nota","Si guardas las tuyas, el plato se puede usar en la app, pero no se exporta al CSV hasta que encaje."));

    const acc = el("div","prod-acc");
    const vol = el("button","m-btn","Volver"); vol.addEventListener("click", edita);
    const mias = el("button","m-btn"+(r.encaja ? " prim" : ""),"Guardar las mías");
    mias.addEventListener("click", ()=>guardaPlato(st.it));
    acc.append(vol, mias);
    if(r.logicasOk){
      const lg = el("button","m-btn"+(r.encaja ? "" : " prim"),"Guardar las lógicas");
      lg.addEventListener("click", ()=>guardaPlato(r.logicas.filter(x=>x[1]>0)));
      acc.append(lg);
    }
    p.append(acc);
  }

  function guardaPlato(it){
    const x = MIS_PLATOS.pon({id: viejo ? viejo.id : 0, t:st.t, n:st.n, it, no:st.no});
    if(!x){ aviso("No se ha podido guardar: el navegador tiene el almacenamiento lleno o bloqueado."); return; }
    v.cierra(); aviso(viejo ? "Plato actualizado" : "Guardado: ya lo puedes elegir en "+nomToma(x.t).toLowerCase()); render();
  }
}

// Descarga platos_app.csv y explica cómo meterlo en datos/platos.csv
function exportaPlatos(){
  const r = MIS_PLATOS.csv();
  const v = abreCapa("Exportar platos"), p = v.panel;
  p.append(el("h2",null,"Exportar para el CSV"));
  if(r.n){
    const blob = new Blob([r.texto], {type:"text/csv;charset=utf-8"});
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "platos_app.csv";
    document.body.append(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
    p.append(el("p",null, r.n+(r.n===1 ? " plato descargado" : " platos descargados")+" en platos_app.csv. Para "+(r.n===1 ? "meterlo" : "meterlos")+" en datos/platos.csv:"));
    const ol = el("ol","pla-pasos");
    const li1 = el("li",null,"Copia platos_app.csv a la carpeta gym_diet_2027.");
    const li2 = el("li",null,"Ejecuta "); li2.append(el("code",null,"python3 actualizar.py --importar platos_app.csv"));
    const li3 = el("li",null,"Sube los cambios a GitHub, como siempre.");
    ol.append(li1, li2, li3); p.append(ol);
    p.append(el("p","m-nota","Puedes importar el mismo archivo dos veces: lo que ya está en el CSV no se duplica."));
  } else p.append(el("p",null,"No hay ningún plato listo para exportar."));
  if(r.fuera.length) p.append(el("p","prod-aviso","No van porque no encajan con su toma: "+r.fuera.map(x=>x.n).join(", ")+". Ábrelos y guárdalos con las cantidades lógicas."));
  const acc = el("div","prod-acc"), ok = el("button","m-btn prim","Entendido");
  ok.addEventListener("click", v.cierra); acc.append(ok); p.append(acc);
}

// Tarjeta «Mis platos» en la página
function pintaMisPlatos(){
  const ps = MIS_PLATOS.lista(), n = ps.length;
  document.getElementById("m-pla-n").textContent = n ? n+(n===1 ? " plato tuyo" : " platos tuyos")+" en este móvil."
    : "Crea tus platos y elígelos en la toma que quieras.";
  const ver = document.getElementById("m-pla-ver"), exp = document.getElementById("m-pla-exp"), box = document.getElementById("m-pla-lista");
  ver.hidden = !n; exp.hidden = !n; ver.textContent = verPlatos ? "Ocultar la lista" : "Ver la lista";
  box.hidden = !(n && verPlatos); box.replaceChildren();
  if(!n || !verPlatos) return;
  const lista = el("div","m-res-lista");
  ps.sort((a,b)=>M.orden.indexOf(a.t)-M.orden.indexOf(b.t) || a.n.localeCompare(b.n,"es")).forEach(x=>{
    const it = el("button","m-res-it"), a = el("span",null,x.n);
    a.append(el("span","m-tag",nomToma(x.t)));
    if(MIS_PLATOS.enPlan(x.t, x.n)) a.append(el("span","m-tag","ya en el plan"));
    else if(!MIS_PLATOS.revisa(x.t, x.it).encaja) a.append(el("span","m-tag dud","no encaja"));
    it.append(a, el("small",null,nf(MIS_PLATOS.totales(x.it)[0])+" kcal"));
    it.addEventListener("click", ()=>fichaPlato(x.id));
    lista.append(it);
  });
  box.append(lista);
}
document.getElementById("m-pla-nuevo").addEventListener("click", ()=>fichaPlato(0, abierta));
document.getElementById("m-pla-ver").addEventListener("click", ()=>{ verPlatos = !verPlatos; pintaMisPlatos(); });
document.getElementById("m-pla-exp").addEventListener("click", exportaPlatos);

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
  const blob = new Blob([JSON.stringify({app:"gym_diet_2027", tipo:"diario", v:1, diario:D, extra:EXTRA, productos:prodParaGuardar(), platos:MIS_PLATOS.paraCopia()}, null, 1)], {type:"application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "diario_"+hoy()+".json";
  document.body.append(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
  aviso("Copia descargada: guárdala en tu carpeta del gimnasio");
});
document.getElementById("m-imp").addEventListener("click", ()=>document.getElementById("m-imp-f").click());
document.getElementById("m-imp-f").addEventListener("change", function(){
  const f = this.files && this.files[0]; if(!f) return;
  f.text().then(t=>{ const j=JSON.parse(t);
    if(!j || j.tipo!=="diario" || !j.diario || !j.diario.dias) throw 0;
    D = Object.assign(vacio(), j.diario); EXTRA = j.extra || {};
    if(j.productos){ PROD = normalizaProd(j.productos); guardaProductos(); }
    if(j.platos) MIS_PLATOS.recupera(j.platos);
    guarda(); compacta(); render(); aviso("Copia recuperada");
  }).catch(()=>aviso("Ese archivo no es una copia del diario"));
  this.value = "";
});

// ---------------------------------------------------------------- controles
document.getElementById("m-prev").addEventListener("click", ()=>{ fecha=sumaDias(fecha,-1); abierta=null; eligiendo=null; render(); });
document.getElementById("m-next").addEventListener("click", ()=>{ fecha=sumaDias(fecha,1); abierta=null; eligiendo=null; render(); });
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

function render(){ pintaCabecera(); pintaResumen(); pintaTomas(); pintaMisPlatos(); pintaProductos(); pintaSemana(); }
compacta();
render();
