let fase = "F0";

const el = (t,c,x)=>{const n=document.createElement(t); if(c)n.className=c;
  if(x!==undefined)n.textContent=x; return n;};
const guarda=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const lee=k=>{try{return localStorage.getItem(k)}catch(e){return null}};

const TIER = {
  T1:["T1","Básicos pesados: sentadilla, banca, peso muerto, dominadas, sentadilla frontal"],
  T2:["T2","Secundarios: rumano, remo, búlgara, militar, hip thrust"],
  T3:["T3","Accesorios y aislamiento: flexión, curl, laterales, face pull"],
  TF:["Fijo","Gemelo: la misma prescripción todo el año, porque la carrera ya lo castiga"]
};
const GRUPOS = [
  ["V","Volumen","F0 · F1 · F3"],
  ["F","Fuerza","F2"],
  ["D","Definición","F4"],
  ["P","Pico","F5"]
];

function pintaCabecera(){
  document.getElementById("v-peso").textContent = T.peso.toFixed(0)+" kg";
  document.getElementById("v-vdot").textContent = T.vdot.hoy.toFixed(0);
  document.getElementById("v-vdotf").textContent = T.vdot.fin.toFixed(0);
  document.getElementById("tab-regla").textContent = T.tabata_regla;
}

function pintaFases(){
  const box = document.getElementById("fases");
  box.replaceChildren();
  Object.keys(T.fases).forEach(k=>{
    const c = el("button","chip", k+" · "+T.fases[k].n);
    c.setAttribute("role","tab");
    c.setAttribute("aria-selected", k===fase?"true":"false");
    c.addEventListener("click", ()=>{ fase=k; guarda("t_fase",k); pintaFases(); pintaBloque(); });
    box.append(c);
  });
}

function pintaBloque(){
  const f = T.fases[fase];
  document.getElementById("b-n").textContent = fase + " · " + f.n;
  document.getElementById("b-meta").textContent =
    f.sem + " semanas · sem " + f.s0 + "–" + f.s1 + "\n" + f.ini + " → " + f.fin +
    "\nDieta: bloque " + f.dieta;
  document.getElementById("b-lema").textContent = f.lema;
  document.getElementById("b-foco").textContent = f.foco;

  const tb = document.getElementById("t-esquema");
  tb.replaceChildren();
  ["T1","T2","T3","TF"].forEach(t=>{
    const p = f.esquema[t]; if(!p) return;
    const tr = el("tr");
    tr.append(el("td","ex",TIER[t][0]), el("td","cue",TIER[t][1]),
              el("td","num",String(p[0])), el("td","num",p[1]), el("td","num",p[2]));
    tb.append(tr);
  });
}

function pintaCargas(){
  const tb = document.getElementById("t-cargas");
  Object.keys(T.arranque).forEach(n=>{
    const a = T.arranque[n];
    const tr = el("tr");
    tr.append(el("td","ex",n), el("td","num",a.antes+" kg"), el("td","num","~"+a.ahora+" kg"),
              el("td","num",String(a.s1).replace(".",",")+" kg"),
              el("td","num",String(a.s4).replace(".",",")+" kg"));
    tb.append(tr);
  });
}

function pintaEjercicios(){
  const box = document.getElementById("ejercicios");
  // orden por sesión, como aparecen en la semana
  const orden = [];
  T.dias.forEach(d=>d.ej.forEach(([,n])=>{ if(orden.indexOf(n)<0) orden.push(n); }));
  Object.keys(T.ej).forEach(n=>{ if(orden.indexOf(n)<0) orden.push(n); });

  orden.forEach(n=>{
    const e = T.ej[n];
    const d = el("details","ejcard");
    const s = el("summary");
    s.append(el("span",null,n), el("span","pat", e.p));
    d.append(s);
    const c = el("div","cuerpo");

    const m = el("div","musc");
    e.m.forEach(x=>m.append(el("span",null,x)));
    c.append(m, el("p","tec", e.nota));
    c.append(el("p","sus", e.sus === "Ninguno: este no se sustituye"
      ? "No se sustituye." : "Si está ocupado: " + e.sus));

    const ser = el("div","series");
    GRUPOS.forEach(([g,et,bloques])=>{
      const x = (T.estructura[n] && T.estructura[n][g]) || T.generico[g];
      const row = el("div","serie");
      row.append(el("span","g", et + "\n" + bloques));
      const txt = el("div");
      txt.append(el("h5",null,x[0]), el("p",null,x[1]));
      row.append(txt);
      ser.append(row);
    });
    c.append(ser);
    d.append(c);
    box.append(d);
  });
}

function pintaTablas(){
  const box = document.getElementById("tablas");
  const DIA = {A:"Lunes · Fuerza A", B:"Miércoles · Fuerza B", C:"Viernes · Fuerza C"};
  Object.keys(T.tabata).forEach(k=>{
    const t = T.tabata[k];
    const d = el("details","ejcard");
    const s = el("summary");
    s.append(el("span",null,t.n), el("span","pat", DIA[k]));
    d.append(s);
    const c = el("div","cuerpo");
    c.append(el("p","sus", t.como + " · " + t.dur));
    [t.a,t.b].forEach(par=>{
      const p = el("p","tec");
      p.append(el("b",null,par[0]+". "), document.createTextNode(par[1]));
      c.append(p);
    });
    const ser = el("div","series");
    const row = el("div","serie");
    row.append(el("span","g","Cómo se sube"));
    const txt = el("div");
    txt.append(el("p",null,t.sube));
    row.append(txt);
    ser.append(row);
    c.append(ser);
    d.append(c);
    box.append(d);
  });
}

function pintaEstaticos(){
  const tz = document.getElementById("t-zonas");
  T.zonas.forEach(([z,a,b,desc])=>{
    const tr = el("tr");
    tr.append(el("td","ex",z), el("td","num",a+"–"+b), el("td","cue",desc));
    tz.append(tr);
  });
  const ts = document.getElementById("t-seguimiento");
  T.seguimiento.forEach(([q,de,sig])=>{
    const tr = el("tr");
    tr.append(el("td","ex",q), el("td","cue",de), el("td","cue",sig));
    ts.append(tr);
  });
  const rb = document.getElementById("reglas");
  T.reglas.forEach(([t,x],i)=>{
    const r = el("div","rule");
    r.append(el("span","i", String(i+1).padStart(2,"0")));
    const p = el("p");
    p.append(el("b",null,t+". "), document.createTextNode(x));
    r.append(p);
    rb.append(r);
  });
}

try{ const f = lee("t_fase"); if(f && T.fases[f]) fase = f; }catch(e){}
pintaCabecera(); pintaFases(); pintaBloque(); pintaCargas();
pintaEjercicios(); pintaTablas(); pintaEstaticos();
