// Calculadora de raciones (v2.0). Sin pantalla: solo la cuenta.
// La misma lógica está en menu/calculadora.py, que es la que usa la verificación.
// Si cambias una, cambia la otra.
//
// Qué hace: recibe los alimentos de un plato con sus gramos de receta y el objetivo
// de la toma (kcal, proteína, grasa, carbohidrato) y busca los gramos que más se
// acercan al objetivo sin deformar el plato. Por orden de importancia:
//   1. las kcal, 2. la proteína, 3. la grasa y el carbohidrato.
// Reglas fijas:
//   La verdura no se toca nunca.
//   Lo que tú has fijado (por ejemplo, los 137 g de pollo que descongelaste) tampoco.
//   En la cena se recorta primero el pan y la grasa (cena ligera).
//   Cada alimento se queda dentro de su ración razonable (mín y máx de generar.py).
// Es un problema de mínimos cuadrados con límites: se resuelve exacto, sin azar,
// y siempre da el mismo resultado.

const CALC = (function(){
  const PESO = [10, 4, 0.3, 0.3];           // kcal, proteína, grasa, carbohidrato
  const FORMA = {proteina:0.3, base:0.1, grasa:0.15, fruta:0.15, lacteo:0.25};
  const FORMA_CORTAR = 0.003;               // pan y grasa en la cena: lo primero que se recorta

  // Resuelve A x = b (Gauss con pivote). Devuelve null si el sistema es singular.
  function sistema(A, b){
    const n = b.length, M = A.map((f,i)=>f.concat([b[i]]));
    for(let c=0;c<n;c++){
      let p=c; for(let r=c+1;r<n;r++) if(Math.abs(M[r][c])>Math.abs(M[p][c])) p=r;
      if(Math.abs(M[p][c])<1e-12) return null;
      [M[c],M[p]]=[M[p],M[c]];
      for(let r=0;r<n;r++){ if(r===c) continue;
        const f=M[r][c]/M[c][c]; if(!f) continue;
        for(let k=c;k<=n;k++) M[r][k]-=f*M[c][k]; }
    }
    return M.map((f,i)=>f[n]/f[i]);
  }

  // items: [{n, g, m:[kcal,P,G,C por 100 g], rol, lo, hi, fijo, cortar}]
  // obj: [kcal, P, G, C]. Devuelve los gramos de cada item, en el mismo orden.
  function resolver(items, obj){
    // La proteína es un mínimo, no un techo: si con la primera cuenta sobra
    // proteína, se repite dándole menos peso para clavar mejor las kcal.
    const g1 = cuenta(items, obj, PESO);
    const p1 = suma(items, g1)[1];
    if(p1 > obj[1]) return cuenta(items, obj, [PESO[0], PESO[1]/10, PESO[2], PESO[3]]);
    return g1;
  }

  function cuenta(items, obj, PESO){
    const g = items.map(it=>it.g);
    let libres = items.map((it,i)=>i).filter(i=>!items[i].fijo && items[i].rol!=="verdura" && items[i].g>0);
    const clavado = {};                      // índices que han tocado límite: valor fijo
    for(let vuelta=0; vuelta<=items.length; vuelta++){
      const vars = libres.filter(i=>!(i in clavado));
      // contribución fija (verdura, lo fijado por ti y lo que ha tocado límite)
      const fijo=[0,0,0,0];
      items.forEach((it,i)=>{ if(vars.indexOf(i)<0){
        const gi = (i in clavado) ? clavado[i] : g[i];
        for(let m=0;m<4;m++) fijo[m]+=it.m[m]*gi/100; }});
      if(!vars.length) break;
      // filas del problema: 4 de macros + 1 de forma por variable; incógnitas: gramos + escala k
      const nv = vars.length + 1, filas=[], rhs=[];
      for(let m=0;m<4;m++){
        if(!(obj[m]>0)) continue;
        const w = Math.sqrt(PESO[m])/obj[m];
        filas.push(vars.map(i=>w*items[i].m[m]/100).concat([0]));
        rhs.push(w*(obj[m]-fijo[m]));
      }
      vars.forEach((i,j)=>{
        const it=items[i], l=Math.sqrt(it.cortar ? FORMA_CORTAR : (FORMA[it.rol]||0.03))/it.g;
        const f=new Array(nv).fill(0); f[j]=l; f[nv-1]=-l*it.g;
        filas.push(f); rhs.push(0);
      });
      // ecuaciones normales con un poco de estabilidad
      const AtA=[], Atb=[];
      for(let a=0;a<nv;a++){ AtA.push(new Array(nv).fill(0)); Atb.push(0); }
      filas.forEach((f,r)=>{ for(let a=0;a<nv;a++){ if(!f[a]) continue;
        Atb[a]+=f[a]*rhs[r]; for(let b2=0;b2<nv;b2++) AtA[a][b2]+=f[a]*f[b2]; }});
      for(let a=0;a<nv;a++) AtA[a][a]+=1e-9;
      const x = sistema(AtA, Atb);
      if(!x) break;
      // el que se salga de su ración se queda en el límite y se repite la cuenta
      // (y lo que se queda en menos de 3 g se quita, para que la cuenta lo sepa)
      let peor=-1, exceso=0, destino=0;
      vars.forEach((i,j)=>{ const it=items[i];
        const d = x[j]<it.lo ? it.lo : x[j]>it.hi ? it.hi : x[j]<3 ? 0 : x[j];
        const e = Math.abs(x[j]-d)/(it.hi||1);
        if(e>exceso){ exceso=e; peor=i; destino=d; }
        g[i]=x[j]; });
      if(peor<0) break;
      clavado[peor] = destino;
    }
    Object.keys(clavado).forEach(i=>{ g[i]=clavado[i]; });
    // gramos de verdad: de 5 en 5 (de 1 en 1 por debajo de 30 g); menos de 3 g es quitarlo
    return g.map((x,i)=>{
      if(items[i].fijo || items[i].rol==="verdura") return items[i].g;
      if(x<3) return 0;
      return x>=30 ? Math.round(x/5)*5 : Math.round(x);
    });
  }

  function suma(items, gramos){
    const t=[0,0,0,0];
    items.forEach((it,i)=>{ for(let m=0;m<4;m++) t[m]+=it.m[m]*gramos[i]/100; });
    return t;
  }

  // Ficha de un alimento para la cuenta. f = [kcal, P, G, C, rol, nota, motivo, mín, máx]
  function item(n, g, f, toma, fijado){
    return {n, g, m:f.slice(0,4), rol:f[4],
            lo: f[4]==="proteina" ? 0.6*f[7] : 0, hi: f[8],
            fijo: !!fijado || n==="Creatina monohidrato",
            cortar: toma==="N" && (n==="Pan de semillas" || f[4]==="grasa")};
  }

  return {resolver, suma, item};
})();
if (typeof module !== "undefined") module.exports = CALC;
