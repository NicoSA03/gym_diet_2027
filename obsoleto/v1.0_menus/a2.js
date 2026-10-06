const DIAS = [
  ["Lunes","Lun","A"],["Martes","Mar","B"],["Miércoles","Mié","A"],["Jueves","Jue","B"],
  ["Viernes","Vie","C"],["Sábado","Sáb","D"],["Domingo","Dom","E"]
];
let fase = "B1", dia = 0, sel = {};

const el = (t,c,x)=>{const n=document.createElement(t); if(c)n.className=c;
  if(x!==undefined)n.textContent=x; return n;};
const guarda=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const lee=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
const nf = n => Math.round(n).toLocaleString("es-ES");

function factores(){ return M.fact[fase + "|" + DIAS[dia][2]]; }
function norma(b, oi){
  const t = M.norm[fase + "|" + DIAS[dia][2]];
  return (t && t[b] && t[b][oi] !== undefined) ? t[b][oi] : 1;
}

function gramos(food, base, s){
  const [fc,fg,fp] = factores();
  const grp = M.foods[food][4];
  const f = grp==="carb" ? fc : grp==="grasa" ? fg : grp==="prot" ? fp : 1;
  return Math.max(5, Math.round(base*f*(s||1)/5)*5);
}
function macrosDe(items, s){
  const t=[0,0,0,0];
  items.forEach(([n,b])=>{
    const g=gramos(n,b,s), m=M.foods[n];
    for(let i=0;i<4;i++) t[i]+=m[i]*g/100;
  });
  return t;
}
function insignia(n){
  const f = M.foods[n], q = f && f[5] ? f[5] : "—";
  const b = el("i","cal "+(q==="—" ? "x" : q), q);
  b.title = (f && f[6]) || "Faltan datos de la etiqueta";
  return b;
}
function claveSel(){ return fase + "|" + dia; }
function opcionDe(b){
  const k = claveSel()+"|"+b;
  if(sel[k]!==undefined) return sel[k];
  return (b==="C"||b==="N") ? dia : 0;   // por defecto, el plato y la cena del día
}
function tomasDelDia(){ return M.tipos[DIAS[dia][2]].tomas; }

function objetivoDia(){
  const mult = M.tipos[DIAS[dia][2]].mult;
  return M.fases[fase].obj.map(x => x*mult);
}

function pintaTomas(){
  const box = document.getElementById("tomas");
  box.replaceChildren();
  tomasDelDia().forEach(b=>{
    const bl = M.bloques[b], oi = opcionDe(b), op = bl.ops[oi];
    const sN = norma(b, oi);
    const m = macrosDe(op.it, sN);
    const row = el("div","toma");
    const top = el("div","toma-top");
    top.append(el("span","h",bl.hora), el("h4",null,bl.n), el("span","nota",bl.nota),
               el("span","kc", nf(m[0])+" kcal · "+Math.round(m[1])+" g P"));
    const ops = el("div","opciones");
    bl.ops.forEach((o,i)=>{
      const c = el("button","chip sm",o.n);
      c.setAttribute("role","tab");
      c.setAttribute("aria-selected", i===oi ? "true":"false");
      c.addEventListener("click", ()=>{
        sel[claveSel()+"|"+b] = i;
        guarda("sel", JSON.stringify(sel));
        render();
      });
      ops.append(c);
    });
    const ing = el("div","ing");
    op.it.forEach(([n,base])=>{
      const d = el("div");
      const et = el("span"); et.append(document.createTextNode(n), insignia(n));
      d.append(et, el("b",null, gramos(n,base,sN)+" g"));
      ing.append(d);
    });
    row.append(top, ops, ing);
    box.append(row);
  });
}

function pintaTotal(){
  const tot=[0,0,0,0];
  tomasDelDia().forEach(b=>{
    const oi = opcionDe(b);
    const m = macrosDe(M.bloques[b].ops[oi].it, norma(b, oi));
    for(let i=0;i<4;i++) tot[i]+=m[i];
  });
  const obj = objetivoDia();
  const desv = (tot[0]-obj[0])/obj[0]*100;
  const k = document.getElementById("t-kcal");
  k.textContent = nf(tot[0]) + " kcal";
  k.style.color = Math.abs(desv)>7 ? "var(--clay)" : "var(--ink)";

  const box = document.getElementById("barras");
  box.replaceChildren();
  [["Calorías",0,"kcal"],["Proteína",1,"g"],["Grasa",2,"g"],["Carbohidrato",3,"g"]]
   .forEach(([et,i,u])=>{
    const r = el("div","barra");
    const pista = el("div","pista");
    const pct = Math.min(100, tot[i]/obj[i]*100);
    const fill = el("div","fill");
    fill.style.width = pct + "%";
    if(tot[i]/obj[i] > 1.07) fill.classList.add("alto");
    const marca = el("div","marca");
    marca.style.left = Math.min(100, 100*obj[i]/Math.max(obj[i], tot[i]*1.02)) + "%";
    pista.append(fill, marca);
    const d = (tot[i]-obj[i]);
    r.append(el("span","et",et), pista,
             el("span","cif", nf(tot[i])+" "+u+"  ("+(d>=0?"+":"")+nf(d)+")"));
    box.append(r);
  });
}

function render(){
  const [nombre,corto,tipo] = DIAS[dia];
  document.getElementById("d-nombre").textContent = nombre + " · " + M.fases[fase].n;
  const t = M.tipos[tipo];
  const o = objetivoDia();
  document.getElementById("tipo-nota").textContent =
    "Día tipo " + tipo + ": " + t.n.toLowerCase() + ". Objetivo de hoy: " +
    nf(o[0]) + " kcal, el " + Math.round(t.mult*100) + " % de la media del bloque.";

  const fb = document.getElementById("fases");
  fb.replaceChildren();
  Object.keys(M.fases).forEach(f=>{
    const c = el("button","chip", f+" · "+M.fases[f].n);
    c.setAttribute("role","tab");
    c.setAttribute("aria-selected", f===fase?"true":"false");
    c.addEventListener("click", ()=>{ fase=f; guarda("fase",f); render(); });
    fb.append(c);
  });

  const db = document.getElementById("dias");
  db.replaceChildren();
  DIAS.forEach(([n,c2,tp],i)=>{
    const b = el("button","dia-btn");
    b.setAttribute("role","tab");
    b.setAttribute("aria-selected", i===dia?"true":"false");
    b.append(el("span",null,c2), el("small",null,"tipo "+tp));
    b.addEventListener("click", ()=>{ dia=i; guarda("dia",String(i)); render(); });
    db.append(b);
  });

  pintaTomas();
  pintaTotal();
}

document.getElementById("reset").addEventListener("click", ()=>{
  Object.keys(sel).forEach(k=>{ if(k.startsWith(claveSel()+"|")) delete sel[k]; });
  guarda("sel", JSON.stringify(sel));
  render();
});

try{
  const f = lee("fase"); if(f && M.fases[f]) fase = f;
  const d = lee("dia");  if(d !== null && DIAS[+d]) dia = +d;
  const s = lee("sel");  if(s) sel = JSON.parse(s) || {};
}catch(e){ sel = {}; }
render();
