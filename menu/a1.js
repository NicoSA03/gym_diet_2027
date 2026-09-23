let fase = "B1", tipo = "A";
const el=(t,c,x)=>{const n=document.createElement(t);if(c)n.className=c;if(x!==undefined)n.textContent=x;return n;};
const guarda=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const lee=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
const nf=n=>Math.round(n).toLocaleString("es-ES");
const ZONA={casa:"Casa",uni:"Universidad",trabajo:"Trabajo",fuera:""};

function pintaFase(){
  const v = I.fases[fase];
  document.getElementById("f-nombre").textContent = fase + " · " + v.n;
  document.getElementById("f-fechas").textContent = v.f;
  const box = document.getElementById("f-macros"); box.replaceChildren();
  [["kcal / día",0,""],["Proteína",1,"g"],["Grasa",2,"g"],["Carbohidrato",3,"g"]].forEach(([n,i,u])=>{
    const d = el("div");
    d.append(el("span","mv", i===0 ? nf(v.obj[0]) : v.obj[i]+" "+u), el("span","ml",n));
    box.append(d);
  });
  const tb = document.getElementById("f-tipos"); tb.replaceChildren();
  Object.keys(I.tipos).forEach(t=>{
    const d = v.tipos[t], ti = I.tipos[t];
    const tr = el("tr");
    if(t===tipo) tr.className="destacada";
    tr.append(el("td","ex", t+" · "+ti.n));
    tr.append(el("td","dia", ti.d));
    tr.append(el("td","num", nf(d.kcal)));
    tr.append(el("td","num", d.p+" g"));
    tr.append(el("td","num", d.g+" g"));
    tr.append(el("td","num", d.c+" g"));
    tr.append(el("td","num", String(d.tomas)));
    tb.append(tr);
  });
  document.getElementById("f-nota").textContent =
    "La media ponderada de los siete días sale en " + nf(v.media) + " kcal, frente al objetivo de " +
    nf(v.obj[0]) + ". Lo que decide el cambio de peso es esa media, no el número de un día suelto.";
}

function pintaTipo(){
  const t = I.tipos[tipo];
  document.getElementById("t-nombre").textContent = tipo + " · " + t.n;
  document.getElementById("t-mult").textContent =
    "×" + t.mult.toFixed(2).replace(".",",") + " sobre la media · " + t.d.toLowerCase();
  const box = document.getElementById("t-hor"); box.replaceChildren();
  t.hor.forEach(([h,q,z])=>{
    const r = el("div","ln "+z);
    r.append(el("span","h",h), el("span","pt"));
    const s = el("span","q",q);
    if(z==="uni"||z==="trabajo") s.append(el("span","tag",ZONA[z]));
    r.append(s);
    box.append(r);
  });
}

function render(){
  const fb=document.getElementById("fases"); fb.replaceChildren();
  Object.keys(I.fases).forEach(f=>{
    const c=el("button","chip", f+" · "+I.fases[f].n);
    c.setAttribute("role","tab"); c.setAttribute("aria-selected", f===fase?"true":"false");
    c.addEventListener("click", ()=>{ fase=f; guarda("fase-info",f); render(); });
    fb.append(c);
  });
  const tb=document.getElementById("tipos"); tb.replaceChildren();
  Object.keys(I.tipos).forEach(t=>{
    const c=el("button","chip", t+" · "+I.tipos[t].d.split(" y ")[0]);
    c.setAttribute("role","tab"); c.setAttribute("aria-selected", t===tipo?"true":"false");
    c.addEventListener("click", ()=>{ tipo=t; guarda("tipo-info",t); render(); });
    tb.append(c);
  });
  pintaFase(); pintaTipo();
}

const eb = document.getElementById("escenarios");
I.esc.forEach(([titulo,, texto])=>{
  const d = el("details","esc");
  const s = el("summary", null, titulo);
  d.append(s, el("p", null, texto));
  eb.append(d);
});

try{
  const f=lee("fase-info"); if(f && I.fases[f]) fase=f;
  const t=lee("tipo-info"); if(t && I.tipos[t]) tipo=t;
}catch(e){}
render();
