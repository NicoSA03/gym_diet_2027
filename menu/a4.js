let fase = "F0", dia = 0;

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
    const c = el("button","chip", k+" · "+E.fases[k].n);
    c.setAttribute("role","tab");
    c.setAttribute("aria-selected", k===fase?"true":"false");
    c.addEventListener("click", ()=>{ fase=k; guarda("e_fase",k); render(); });
    box.append(c);
  });
  const f = E.fases[fase];
  document.getElementById("f-n").textContent = f.lema;
  document.getElementById("f-f").textContent =
    "Semanas " + f.s0 + "–" + f.s1 + " · dieta " + f.dieta;
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
    b.addEventListener("click", ()=>{ dia=i; guarda("e_dia",String(i)); render(); });
    box.append(b);
  });
}

function pintaSesion(){
  const d = E.dias[dia], f = E.fases[fase];
  const box = document.getElementById("sesion");
  box.replaceChildren();

  const top = el("div","ses-top");
  const izq = el("div");
  izq.append(el("h3",null, d.dia + " · " + d.n), el("p","sub", d.sub));
  top.append(izq, el("span","dur", d.cod==="J" ? f.largo[0]+"–"+f.largo[1]+" min" : d.dur));
  box.append(top);

  if(d.cal.length){
    const c = el("div","cal-box");
    c.append(el("h5",null, d.cod==="J" ? "Antes de salir" : "Calentamiento"));
    const ul = el("ul");
    d.cal.forEach(x=>ul.append(el("li",null,"· "+x)));
    c.append(ul);
    box.append(c);
  }

  if(d.tipo==="fuerza"){
    d.ej.forEach(([tier,nombre])=>{
      const ej = E.ej[nombre], p = f.esquema[tier], es = estructura(nombre);
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
      box.append(row);
    });
    if(d.tabata){
      const t = E.tabata[d.tabata];
      const c = el("div","tab");
      c.append(el("span","reloj","Abdominales · tabata 20-20 · "+t.dur), el("h5",null,t.n));
      [["1·3·5·7",t.a],["2·4·6·8",t.b]].forEach(([k,par])=>{
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

function pintaZonas(){
  const box = document.getElementById("zmini");
  box.replaceChildren();
  E.zonas.forEach(([z,a,b])=>{
    const d = el("div");
    d.append(el("span","z",z.split(" · ")[1]), el("span","r",a+"–"+b),
             el("span","z",z.split(" · ")[0]));
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
    s.append(el("span",null,v.n), el("span","tag", v.dias+" · "+v.dur));
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

function render(){ pintaFases(); pintaDias(); pintaSesion(); pintaKm(); }

try{
  const f = lee("e_fase"); if(f && E.fases[f]) fase = f;
  const d = lee("e_dia");  if(d !== null && E.dias[+d]) dia = +d;
}catch(e){}
pintaZonas(); pintaVariantes(); render();
