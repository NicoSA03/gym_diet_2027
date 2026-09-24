let fase = "B1", hechos = {};
const el=(t,c,x)=>{const n=document.createElement(t);if(c)n.className=c;if(x!==undefined)n.textContent=x;return n;};
const guarda=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const lee=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
const eur=n=>n.toFixed(2).replace(".",",")+" €";
const id=(f,n)=>"c-"+f+"-"+n.replace(/[^a-zA-Z0-9]/g,"");

function render(){
  const v = C[fase];
  const fb = document.getElementById("fases"); fb.replaceChildren();
  Object.keys(C).forEach(f=>{
    const c = el("button","chip", f+" · "+C[f].n);
    c.setAttribute("role","tab"); c.setAttribute("aria-selected", f===fase?"true":"false");
    c.addEventListener("click", ()=>{ fase=f; guarda("fase-compra",f); render(); });
    fb.append(c);
  });
  document.getElementById("f-nota").textContent =
    v.f + " · objetivo de " + v.obj.toLocaleString("es-ES") + " kcal al día de media.";

  const box = document.getElementById("lista"); box.replaceChildren();
  let total=0, n=0, marcados=0, gastado=0;
  v.secs.forEach(sec=>{
    const s = el("div","seccion");
    const sub = sec.items.reduce((a,i)=>a+i.e,0);
    const h = el("h4"); h.append(el("span",null,sec.s), el("span",null,eur(sub)));
    s.append(h);
    sec.items.forEach(it=>{
      total += it.e; n++;
      const k = id(fase,it.n), ok = hechos[k]===1;
      if(ok){ marcados++; gastado += it.e; }
      const row = el("div", ok ? "item done" : "item");
      const cb = el("input"); cb.type="checkbox"; cb.id=k; cb.checked=ok;
      cb.addEventListener("change", ()=>{
        if(cb.checked) hechos[k]=1; else delete hechos[k];
        guarda("hechos", JSON.stringify(hechos)); render();
      });
      const lab = el("label"); lab.htmlFor=k; lab.append(document.createTextNode(it.n));
      const q = el("i","cal "+(it.q==="—" ? "x" : it.q), it.q || "—");
      q.title = it.qm || "Faltan datos de la etiqueta";
      lab.append(q);
      if(it.v){ const d=el("span","vf"); d.title="Precio verificado en tienda"; lab.append(d); }
      row.append(cb, lab, el("span","cant",it.c), el("span","eur",eur(it.e)));
      s.append(row);
    });
    box.append(s);
  });
  document.getElementById("total").innerHTML =
    eur(total) + '<small>Total de la semana</small>';
  document.getElementById("cuenta").textContent =
    marcados + " de " + n + " en el carro · " + eur(gastado) + " gastados";
  document.getElementById("prog").style.width = (n ? marcados/n*100 : 0) + "%";
}
document.getElementById("reset").addEventListener("click", ()=>{
  Object.keys(hechos).forEach(k=>{ if(k.startsWith("c-"+fase+"-")) delete hechos[k]; });
  guarda("hechos", JSON.stringify(hechos)); render();
});
try{
  const f=lee("fase-compra"); if(f && C[f]) fase=f;
  const h=lee("hechos"); if(h) hechos=JSON.parse(h)||{};
}catch(e){ hechos={}; }
render();
