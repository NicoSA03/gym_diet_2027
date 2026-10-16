// Mis platos (v2.3): los platos que creas en la app. Sin pantalla: guardado,
// revisión de cantidades y exportación a CSV. La pantalla está en menu/a2.js.
//
// Se guardan en este móvil, en la clave mis_platos_v1:
//   {v:1, sig:8, p:[{id, t:toma, n:nombre, it:[[alimento, gramos]], no:notas, f:fecha}]}
// Solo admiten alimentos de datos/alimentos.csv. Así, al exportarlos y ejecutar
// «python3 actualizar.py --importar platos_app.csv», entran en datos/platos.csv
// sin tener que tocar nada más.
//
// Las cantidades lógicas: los gramos que dejan la receta con las calorías base de su
// toma (M.base: la media de sus compañeros en datos/platos.csv), calculados con la
// misma calculadora de raciones (CALC). Es lo que exige menu/ver_platos.py para que
// un plato entre en el CSV: ±12 % (o ±25 kcal) de la media y raciones razonables.

const MIS_PLATOS = (function(){
  const KEY = "mis_platos_v1";
  const sinT = t => String(t).normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase().trim();
  const z2 = n => String(n).padStart(2,"0");
  const hoyIso = () => { const d=new Date(); return d.getFullYear()+"-"+z2(d.getMonth()+1)+"-"+z2(d.getDate()); };

  function normaliza(d){
    d = d || {};
    const p = (Array.isArray(d.p) ? d.p : []).filter(x=>x && x.id>0 && x.t && x.n && Array.isArray(x.it));
    const sig = Math.max(d.sig||1, 1, ...p.map(x=>x.id+1));
    return {v:1, sig, p};
  }
  function carga(){
    try{ const t = localStorage.getItem(KEY); if(t) return normaliza(JSON.parse(t)); }catch(e){}
    return normaliza(null);
  }
  let D = carga();
  function guarda(){ try{ localStorage.setItem(KEY, JSON.stringify(D)); return true; }catch(e){ return false; } }

  // ¿Ya hay un plato con ese nombre en esa toma del plan (datos/platos.csv)?
  // Pasa después de importarlo: desde entonces manda el del CSV y el tuyo se oculta.
  function enPlan(t, n){
    const ops = (t==="C"||t==="N") ? M.principales.filter(p=>p.de===t) : ((M.bloques[t]||{}).ops||[]);
    return ops.some(o=>sinT(o.n)===sinT(n));
  }
  // ¿El nombre choca con otro plato de la misma toma (del plan o tuyo)?
  function nombreOcupado(t, n, id){
    return enPlan(t, n) || D.p.some(x=>x.id!==id && x.t===t && sinT(x.n)===sinT(n));
  }
  function lista(){ return D.p.slice(); }
  function uno(id){ return D.p.find(x=>x.id===id) || null; }
  // Los tuyos que se pueden elegir en una toma (los que ya están en el plan, no)
  function deTomas(ts){ return D.p.filter(x=>ts.indexOf(x.t)>=0 && !enPlan(x.t, x.n)); }

  // Guarda un plato: nuevo si no trae id. Devuelve el plato o null si no se pudo.
  function pon(pl){
    const it = pl.it.map(([n,g])=>[n, Math.round(g)]).filter(x=>x[1]>0);
    const limpio = {t:pl.t, n:pl.n.replace(/\s+/g," ").trim(), it, no:(pl.no||"").replace(/\s+/g," ").trim()};
    let x = pl.id ? uno(pl.id) : null;
    if(x) Object.assign(x, limpio);
    else { x = Object.assign({id:D.sig++, f:hoyIso()}, limpio); D.p.push(x); }
    return guarda() ? x : null;
  }
  function quita(id){ D.p = D.p.filter(x=>x.id!==id); return guarda(); }
  function paraCopia(){ return D; }
  function recupera(d){ D = normaliza(d); return guarda(); }

  function totales(it){
    const t=[0,0,0,0];
    it.forEach(([n,g])=>{ const f=M.foods[n]; if(!f) return; for(let m=0;m<4;m++) t[m]+=f[m]*g/100; });
    return t;
  }
  // ¿Encaja un plato de k kcal en la toma t? Igual que ver_platos.py: con él dentro,
  // TODOS los platos de la toma (también los que ya estaban) tienen que quedar a ±12 %
  // (o ±25 kcal) de la nueva media. «afecta»: los del plan que se saldrían por su culpa.
  function encajaEn(t, k){
    const ops = (t==="C"||t==="N") ? M.principales.filter(p=>p.de===t) : M.bloques[t].ops;
    const ks = ops.map(o=>totales(o.it)[0]).concat([k]);
    const m = ks.reduce((a,b)=>a+b, 0)/ks.length, tope = Math.max(0.12*m, 25);
    return {ok: ks.every(x=>Math.abs(x-m) <= tope),
            afecta: ops.filter((o,i)=>Math.abs(ks[i]-m) > tope).map(o=>o.n)};
  }
  // Ración fuera de lo razonable: la misma regla que ver_platos.py
  function racionMala(n, g){ const f=M.foods[n]; return !!f && g>0 && (g > f[8]*1.25 || g < f[7]*0.5); }

  // Revisión de una receta para la toma t.
  //   encaja: entra tal cual en datos/platos.csv
  //   logicas: [[alimento, gramos]] con las cantidades lógicas (0 = mejor quitarlo)
  //   logicasOk: si con las lógicas sí encaja
  function revisa(t, it){
    const base = M.base[t];
    const faltan = it.filter(([n])=>!M.foods[n]).map(([n])=>n);
    const buenos = it.filter(([n])=>M.foods[n]);
    const tot = totales(buenos);
    const raciones = buenos.filter(([n,g])=>racionMala(n,g)).map(([n,g])=>({n, g, lo:M.foods[n][7], hi:M.foods[n][8]}));
    const enc = encajaEn(t, tot[0]);
    const its = buenos.map(([n,g])=>CALC.item(n, g, M.foods[n], t, false));
    const gl = its.length ? CALC.resolver(its, base.m) : [];
    const logicas = its.map((x,i)=>[x.n, gl[i]]);
    const totL = CALC.suma(its, gl);
    const quedan = logicas.filter(x=>x[1]>0);
    const logicasOk = quedan.length>0 && encajaEn(t, totL[0]).ok && !quedan.some(([n,g])=>racionMala(n,g));
    return {base, tot, totL, faltan, raciones, logicas, logicasOk, afecta: enc.afecta,
            encaja: buenos.length>0 && !faltan.length && enc.ok && !raciones.length};
  }

  // Archivo para «python3 actualizar.py --importar»: mismas columnas que datos/platos.csv.
  // Solo van los que encajan y aún no están en el plan; los demás se devuelven en «fuera».
  function csv(){
    const q = s => /[;"\r\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s;
    const filas = ["toma;plato;alimentos;gramos;notas"], fuera = [];
    D.p.forEach(x=>{
      if(enPlan(x.t, x.n)) return;
      if(!revisa(x.t, x.it).encaja){ fuera.push(x); return; }
      filas.push([x.t, x.n, x.it.map(i=>i[0]).join("|"), x.it.map(i=>String(Math.round(i[1]))).join("|"), x.no||""].map(q).join(";"));
    });
    return {texto: "﻿"+filas.join("\r\n")+"\r\n", n: filas.length-1, fuera};
  }

  return {lista, uno, deTomas, enPlan, nombreOcupado, pon, quita, paraCopia, recupera, totales, revisa, csv};
})();
