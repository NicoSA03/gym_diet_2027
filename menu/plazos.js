// Plazos y reajuste dinámico del plan (v2.6). Sin pantalla y sin almacenamiento:
// solo la cuenta. La misma lógica está en menu/plazos.py, que es la que usa la
// verificación (menu/ver_plazos.py). Si cambias una, cambia la otra.
//
// Qué hace: mira lo que has entrenado cada semana (sesiones de la app, del reloj
// y otras actividades que apuntas día a día) y propone, sin imponer:
//   1. cuánto comer el resto del día si cambias de entreno (dietaDelDia),
//   2. recuperar una sesión pendiente o una semana de reentrada (propuestaDia),
//   3. repetir cargas o alargar el bloque si la semana fue floja (propuestaSemana),
//   4. subir o bajar 100 kcal si el peso no va como toca (propuestaPeso).
// Reglas fijas:
//   Nunca modifica el registro que recibe: aplicar y deshacer devuelven una copia.
//   Quien llama decide si la guarda.
//   Los datos nuevos viven en registro.dias y registro.ajustes (lo viejo no se toca).
//   Cada propuesta aplicada deja un apunte en registro.ajustes con lo que había
//   antes y lo que puso; deshacerAjuste(registro, indice) lo deshace en cualquier
//   momento, sin necesitar la propuesta original.
//   Las fechas son texto AAAA-MM-DD y se cuentan en días enteros (sin horas).
//   Sin fecha de inicio no hay propuestas. Con `desde` (la fecha en que empezó a
//   usarse esto) no se juzga nada anterior a esa fecha.
// El plan de días (DIAS de menu/entreno.py) se puede pasar como `plan`; si no,
// se usa el de abajo. El hueco i del plan es el día i de la semana (0 = lunes).

const PLAZOS = (function(){
  // Semana: buena con el 80 % o más, repetir cargas con el 60 % o más, alargar por debajo.
  // Con 5 sesiones: 4 o 5 bien, 3 repetir, 2 o menos alargar.
  const DIAS_SIN_ENTRENAR = 10; // a partir de aquí, semana de reentrada
  const PESAJES_MIN = 10;       // pesajes en 21 días (y 3 por semana) para opinar del peso
  const PASO_KCAL = 100;

  // MET por tipo e intensidad [suave, media, alta]
  const MET = {caminar:[3,4,5], carrera:[7,9,11.5], bici:[5,7,10], fuerza:[3.5,5,6],
               natacion:[6,8,10], deporte:[5,7,9], otro:[3,5,7]};
  // Entreno previsto de cada sesión del plan: min y MET
  const PREVISTO = {L:{min:70,met:5}, M:{min:55,met:9}, X:{min:70,met:5}, J:{min:60,met:7}, V:{min:70,met:5}};
  const PLAN = {dias:[
    {cod:"L", n:"Fuerza A", tipo:"fuerza"},
    {cod:"M", n:"Carrera de calidad", tipo:"carrera"},
    {cod:"X", n:"Fuerza B", tipo:"fuerza"},
    {cod:"J", n:"Tirada larga", tipo:"carrera"},
    {cod:"V", n:"Fuerza C", tipo:"fuerza"}]};
  // Bloques de la dieta con regla de peso (README, «Cuándo tocar las calorías»).
  // B0, B2 y B5 no tienen regla.
  const CONSTRUCCION = {B1:1, B3:1}, DEFINICION = {B4:1};
  const MES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
  const NOMBRES_DIA = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"];

  // ---------------------------------------------------------------- utilidades
  const clon = o => JSON.parse(JSON.stringify(o));
  const redond = x => Math.floor(x + 0.5);
  const r2 = x => Math.floor(x * 100 + 0.5) / 100;
  const r3 = x => Math.floor(x * 1000 + 0.5) / 1000;
  // Días enteros desde 1970-01-01 y vuelta atrás. Lunes = 0 en diaSemana.
  function aDias(s){ const p = s.split("-").map(Number); return Math.round(Date.UTC(p[0], p[1]-1, p[2]) / 864e5); }
  function aIso(n){ return new Date(n * 864e5).toISOString().slice(0, 10); }
  const diaSemana = s => (((aDias(s) + 3) % 7) + 7) % 7;
  const lunesDe = s => aIso(aDias(s) - diaSemana(s));
  const sumaDias = (s, n) => aIso(aDias(s) + n);
  const corta = s => { const p = s.split("-").map(Number); return p[2] + " " + MES[p[1]-1]; };
  const conComa = x => String(x).replace(".", ",");
  const planDe = plan => (plan && plan.dias && plan.dias.length) ? plan.dias : PLAN.dias;
  const sinTildes = t => String(t || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  const ajustesDe = r => (r && r.ajustes) || [];
  // La fecha más tardía de las que no son null
  const ultimaDe = xs => xs.reduce((u, f) => (f && (!u || f > u)) ? f : u, null);

  // ---------------------------------------------------------------- kcal
  function metDe(act){
    const t = sinTildes(act && act.tipo), tabla = MET[t] || MET.otro;
    const i = {suave:0, media:1, alta:2}[sinTildes(act && act.int)];
    return tabla[i === undefined ? 1 : i];
  }
  // kcal netas (MET menos 1: las del reposo ya van en el objetivo del día)
  function netas(met, min, peso){ return (met - 1) * peso * min / 60; }

  // kcalActividad({nombre, tipo, min, int}, peso) -> kcal enteras
  function kcalActividad(act, peso){
    if(!act || !(peso > 0) || !(act.min > 0)) return 0;
    return redond(netas(metDe(act), act.min, peso));
  }

  function kcalPrevista(cod, peso){
    const p = PREVISTO[cod];
    return p && peso > 0 ? netas(p.met, p.min, peso) : 0;
  }

  // Sesión que toca por el día de la semana, o null el fin de semana
  function sesionDeHoy(fecha, plan){
    const d = planDe(plan)[diaSemana(fecha)];
    return d ? d.cod : null;
  }

  // dietaDelDia(registro, fecha, objPlan, peso)
  //   Si en Menús se elige a mano el tipo E (descanso), pasa sesion:null para no
  //   restar un entreno que ya no está en el objetivo.
  //   objPlan = {kcal, kcalE, kcalD, sesion?}: kcal previstas del día, las del día de
  //   descanso (tipo E), las del sábado (tipo D) y, si el día no es el de siempre,
  //   la sesión que toca (código o null).
  //   Devuelve {factor, kcal, motivo}: por cuánto multiplicar las tomas que quedan.
  function dietaDelDia(registro, fecha, objPlan, peso){
    const base = objPlan.kcal;
    const igual = m => ({factor:1, kcal:base, motivo:m});
    let d = registro && registro.dias && registro.dias[fecha];
    // Un día corregido después (corregirDia) no cambia su comida: vale lo que se marcó aquel día, si lo hubo
    if(d && d.corregido) d = d.comida || null;
    if(!d || !(peso > 0)) return igual("Sin cambios sobre el plan");
    const prev = objPlan.sesion !== undefined ? objPlan.sesion : sesionDeHoy(fecha);
    const kPrev = prev ? kcalPrevista(prev, peso) : 0;
    let kHoy, que;
    if(d.modo === "descanso"){ kHoy = 0; que = "Descanso"; }
    else if(d.modo === "otra"){ kHoy = d.act ? kcalActividad(d.act, peso) : 0; que = (d.act && d.act.nombre) || "Otra actividad"; }
    else if(d.modo === "otro_plan" && PREVISTO[d.sesion]){ kHoy = kcalPrevista(d.sesion, peso); que = "Otro entreno del plan"; }
    else return igual("Sin cambios sobre el plan");
    const nuevo = base - kPrev + kHoy;
    const lo = Math.min(objPlan.kcalE, objPlan.kcalD), hi = Math.max(objPlan.kcalE, objPlan.kcalD);
    const kcal = redond(Math.min(hi, Math.max(lo, nuevo)));
    if(kcal === redond(base)) return igual("Sin cambios sobre el plan");
    const tope = nuevo < lo ? " (mínimo: día de descanso)" : nuevo > hi ? " (máximo: día de sábado)" : "";
    return {factor:r3(kcal / base), kcal, motivo: que + ": " + (kcal > base ? "más" : "menos") + " comida que el plan" + tope};
  }

  // ---------------------------------------------------------------- semana
  const tipoAct = t => { t = sinTildes(t); return t === "carrera" ? "carrera" : t === "fuerza" ? "fuerza" : "otro"; };
  const via = x => x.origen === "reloj" ? "reloj" : "app";

  // Lo que hay registrado un día: {tipo, medio, via, slot, natural} o null.
  // tipo "otro" = actividad que no sustituye una sesión entera (vale 0,5 si medio).
  function pruebaDia(r, f, plan){
    const d = r.dias && r.dias[f];
    const sesion = (r.sesiones || []).filter(s => s.fecha === f)[0];
    const carr = (r.carrera || []).filter(c => c.f === f)[0];
    const natural = sesionDeHoy(f, plan);
    const tipoNat = natural ? planDe(plan)[diaSemana(f)].tipo : null;
    const explicito = d && d.modo === "otro_plan" && d.sesion ? d.sesion : null;
    // si hay fuerza y carrera el mismo día cuenta una (la que toca ese día)
    let e = null;
    if(sesion && carr) e = (tipoNat === "carrera") ? {tipo:"carrera", via:via(carr)} : {tipo:"fuerza", via:via(sesion)};
    else if(sesion) e = {tipo:"fuerza", via:via(sesion)};
    else if(carr) e = {tipo:"carrera", via:via(carr)};
    else if(d && d.modo === "otra" && d.act){
      // Otra actividad: vale 1 solo si es del tipo de la sesión prevista ese día
      const t = tipoAct(d.act.tipo);
      const medio = d.act.min >= 30 && (sinTildes(d.act.int) === "media" || sinTildes(d.act.int) === "alta");
      e = (t !== "otro" && t === tipoNat) ? {tipo:t, via:"otra"} : {tipo:"otro", via:"otra", medio};
    }
    else if(d && d.hecho && (d.modo === "plan" || d.modo === "otro_plan")){
      // Sesión del plan hecha pero sin apuntar las series (marcada a mano, corregirDia)
      const cod = d.sesion || natural, dp = planDe(plan).filter(x => x.cod === cod)[0];
      if(dp) e = {tipo:dp.tipo, via:"manual"};
    }
    if(!e) return null;
    e.slot = explicito; e.natural = natural;
    return e;
  }

  // adherencia(registro, lunesIso, plan?, desde?) -> {hechas, previstas, pct, detalle}
  //   Los huecos de días anteriores a la fecha de inicio (o a `desde`) no son previstos.
  //   pct es null si no hay ninguno previsto.
  function adherencia(registro, lunesIso, plan, desde){
    const r = registro || {}, dias = planDe(plan), n = dias.length;
    const lun = lunesDe(lunesIso);
    const arranque = ultimaDe([r.inicio || null, desde || null]);
    const detalle = dias.map((d, i) => ({sesion:d.cod, fecha:null, valor:0, via:null,
                                          prevista: !arranque || sumaDias(lun, i) >= arranque}));
    const libre = i => detalle[i].prevista && detalle[i].valor === 0 && detalle[i].fecha === null;
    const idx = cod => dias.findIndex(d => d.cod === cod);
    const pruebas = [];
    for(let k = 0; k < 7; k++){
      const f = sumaDias(lun, k);
      if(arranque && f < arranque) continue;
      const e = pruebaDia(r, f, plan);
      if(e){ e.f = f; pruebas.push(e); }
    }
    const poner = (i, e, valor) => { detalle[i].fecha = e.f; detalle[i].valor = valor; detalle[i].via = e.via; };
    const hecho = {};
    // Primera pasada: cada día en su hueco (el que dijo el usuario o el que toca ese día)
    pruebas.forEach((e, p) => {
      let i = -1;
      if(e.tipo !== "otro"){
        if(e.slot && idx(e.slot) >= 0 && dias[idx(e.slot)].tipo === e.tipo) i = idx(e.slot);
        else if(e.natural && idx(e.natural) >= 0 && dias[idx(e.natural)].tipo === e.tipo) i = idx(e.natural);
        if(i >= 0 && libre(i)){ poner(i, e, 1); hecho[p] = 1; }
      } else {
        if(e.slot && idx(e.slot) >= 0) i = idx(e.slot); else if(e.natural) i = idx(e.natural);
        if(i >= 0 && libre(i)){ if(e.medio) poner(i, e, 0.5); hecho[p] = 1; }
      }
    });
    // Segunda pasada: lo que sobra va al primer hueco libre del mismo tipo (o a cualquiera si es de otro tipo)
    pruebas.forEach((e, p) => {
      if(hecho[p]) return;
      for(let i = 0; i < n; i++){
        if(!libre(i)) continue;
        if(e.tipo === "otro"){ if(e.medio) poner(i, e, 0.5); break; }
        if(dias[i].tipo === e.tipo){ poner(i, e, 1); break; }
      }
    });
    const hechas = detalle.reduce((a, x) => a + x.valor, 0);
    const previstas = detalle.filter(x => x.prevista).length;
    return {hechas, previstas, pct: previstas ? r3(Math.min(1, hechas / previstas)) : null, detalle};
  }

  // ---------------------------------------------------------------- ajustes
  // Apunta un ajuste en una copia del registro.
  function conAjuste(registro, aj){
    const c = clon(registro); c.ajustes = ajustesDe(c).concat([aj]); return c;
  }
  const hayAjuste = (r, que, semana) => ajustesDe(r).some(a => !a.deshecho && a.que === que && a.semana === semana);
  const mismoDia = (a, b) => !!a && !!b && a.modo === b.modo && (a.sesion || null) === (b.sesion || null);

  // deshacerAjuste(registro, indice) -> copia con ajustes[indice] deshecho.
  //   alargar: vuelve al inicio de antes si sigue el que puso el ajuste.
  //   recuperar: vuelve el día a como estaba si sigue como lo dejó el ajuste.
  //   kcal, repetir, reentrada: solo se marca (kcalExtra deja de sumarlo).
  function deshacerAjuste(registro, indice){
    const c = clon(registro); c.ajustes = ajustesDe(c);
    const a = c.ajustes[indice];
    if(!a || a.deshecho) return c;
    if(a.que === "alargar" && a.antes && a.despues && c.inicio === a.despues.inicio) c.inicio = a.antes.inicio;
    if(a.que === "recuperar" && a.antes && a.despues){
      c.dias = c.dias || {};
      if(mismoDia(c.dias[a.f], a.despues.dia)){
        if(a.antes.dia) c.dias[a.f] = a.antes.dia; else delete c.dias[a.f];
      }
    }
    a.deshecho = true;
    return c;
  }
  // Índice del último apunte activo que cuadra, o -1
  function buscaAjuste(r, f, que, semana){
    const as = ajustesDe(r);
    for(let i = as.length - 1; i >= 0; i--){
      const a = as[i];
      if(!a.deshecho && a.f === f && a.que === que && (semana === undefined || a.semana === semana)) return i;
    }
    return -1;
  }
  const deshacerUltimo = (r, f, que, semana) => deshacerAjuste(r, buscaAjuste(r, f, que, semana));

  // ---------------------------------------------------------------- corregir un día
  const esIso = f => typeof f === "string" && /^\d{4}-\d{2}-\d{2}$/.test(f) && aIso(aDias(f)) === f;

  // corregirDia(registro, fecha, dia, hoy, ahora?) -> registro nuevo, o null si no se puede.
  //   Marca o cambia qué se hizo un día de hoy hacia atrás (nunca un día futuro).
  //   dia = {modo, sesion?, act?, hecho?} o null para quitar la corrección.
  //   hecho:true (solo con plan u otro_plan) = «la hice, pero no apunté las series»: cuenta 1 en la semana.
  //   Un día pasado queda con corregido:true y su comida no cambia: si aquel día ya se
  //   había marcado algo, se guarda en `comida` y la dieta de ese día sigue saliendo de ahí.
  function corregirDia(registro, fecha, dia, hoy, ahora){
    if(!esIso(fecha) || !esIso(hoy) || fecha > hoy) return null;
    const c = clon(registro || {}); c.dias = (c.dias && typeof c.dias === "object") ? c.dias : {};
    const prev = c.dias[fecha] || null, pasado = fecha < hoy;
    const comida = !prev ? null : prev.corregido ? (prev.comida || null)
                 : {modo:prev.modo, sesion:prev.sesion || null, act:prev.act || null, t:prev.t || 0};
    if(dia === null || dia === undefined){
      if(pasado && comida) c.dias[fecha] = comida; else delete c.dias[fecha];
      return c;
    }
    const t = ahora === undefined ? Date.now() : ahora;
    let n;
    if(dia.modo === "plan"){
      const cod = dia.sesion || sesionDeHoy(fecha);
      if(cod && !PREVISTO[cod]) return null;
      n = {modo:"plan", sesion:cod || null, act:null};
    } else if(dia.modo === "otro_plan"){
      if(!PREVISTO[dia.sesion]) return null;
      n = {modo:"otro_plan", sesion:dia.sesion, act:null};
    } else if(dia.modo === "otra"){
      if(!dia.act || !(dia.act.min > 0)) return null;
      n = {modo:"otra", sesion:null, act:clon(dia.act)};
    } else if(dia.modo === "descanso"){
      n = {modo:"descanso", sesion:null, act:null};
    } else return null;
    if(dia.hecho && n.sesion) n.hecho = true;
    if(pasado){ n.t = comida ? comida.t : t; n.corregido = true; n.tc = t; n.comida = comida; }
    else n.t = t;
    c.dias[fecha] = n;
    return c;
  }

  // revisarAjustes(registro, fecha, plan?, desde?) -> índices de `ajustes` que ya no se sostienen
  //   Tras corregir un día: los «repetir» o «alargar» activos de esa semana cuya cuenta ya
  //   no los justifica. No deshace nada: la interfaz ofrece deshacerAjuste(registro, i).
  function revisarAjustes(registro, fecha, plan, desde){
    const r = registro || {};
    if(!esIso(fecha)) return [];
    const lun = lunesDe(fecha), out = [];
    let ad = null;
    ajustesDe(r).forEach((a, i) => {
      if(!a || a.deshecho || a.semana !== lun || (a.que !== "repetir" && a.que !== "alargar")) return;
      // con el inicio de antes de alargar, para contar la semana igual que cuando salió el aviso
      const base = (a.que === "alargar" && a.antes && a.antes.inicio && r.inicio === (a.despues || {}).inicio)
                 ? Object.assign({}, r, {inicio:a.antes.inicio}) : r;
      ad = adherencia(base, lun, plan, desde);
      if(!ad.previstas) return;
      const corte = a.que === "repetir" ? 4 : 3;
      if(ad.hechas * 5 >= ad.previstas * corte) out.push(i);
    });
    return out;
  }

  // ---------------------------------------------------------------- propuestas
  function ultimaActividad(r, hoy){
    const fs = [];
    (r.sesiones || []).forEach(s => fs.push(s.fecha));
    (r.carrera || []).forEach(c => fs.push(c.f));
    Object.keys(r.dias || {}).forEach(f => { const d = r.dias[f]; if(d && ((d.modo === "otra" && d.act) || (d.hecho && (d.modo === "plan" || d.modo === "otro_plan")))) fs.push(f); });
    return ultimaDe(fs.filter(f => f && f <= hoy));
  }

  // propuestaDia(registro, hoy, plan?, desde?) -> null | {tipo, texto, aplicar(r, ahora?), deshacer(r)}
  function propuestaDia(registro, hoy, plan, desde){
    const r = registro || {}, dias = planDe(plan);
    if(!r.inicio || r.inicio > hoy) return null;
    const lun = lunesDe(hoy);
    // 1. Reentrada: diez días o más sin entrenar (contando desde el inicio o desde `desde`)
    const ref = ultimaDe([ultimaActividad(r, hoy), r.inicio, (desde && desde <= hoy) ? desde : null]);
    const sin = aDias(hoy) - aDias(ref);
    if(sin >= DIAS_SIN_ENTRENAR){
      if(hayAjuste(r, "reentrada", lun)) return null;
      return {
        tipo:"reentrada",
        texto:"Llevas " + sin + " días sin entrenar. Esta semana es de reentrada: cargas más suaves y lejos del fallo.",
        aplicar: reg => conAjuste(reg, {f:hoy, que:"reentrada", semana:lun, antes:{reentrada:false}, despues:{reentrada:true}, deshecho:false}),
        deshacer: reg => deshacerUltimo(reg, hoy, "reentrada", lun)
      };
    }
    // 2. Sesión pendiente: la más reciente de esta semana sin hacer ni descartada
    const d0 = r.dias && r.dias[hoy];
    if(d0 && d0.modo) return null;
    const ad = adherencia(r, lun, plan, desde);
    for(let k = Math.min(diaSemana(hoy), dias.length) - 1; k >= 0; k--){
      const f = sumaDias(lun, k), s = ad.detalle[k];
      if(!s.prevista || s.valor !== 0 || s.fecha !== null) continue;
      const dd = r.dias && r.dias[f];
      if(dd && (dd.modo === "descanso" || dd.modo === "otra")) continue;
      const cod = s.sesion, nombre = dias[k].n;
      const hubo = (r.sesiones || []).some(x => x.fecha === f) || (r.carrera || []).some(x => x.f === f);
      return {
        tipo:"recuperar",
        texto:"El " + NOMBRES_DIA[k] + " " + corta(f) + " tocaba " + nombre + (hubo ? " e hiciste otro entreno." : " y no hay registro.") + " ¿La haces hoy?",
        aplicar: (reg, ahora) => {
          const antes = (reg.dias && reg.dias[hoy]) ? clon(reg.dias[hoy]) : null;
          const c = conAjuste(reg, {f:hoy, que:"recuperar", semana:lun, antes:{dia:antes}, despues:{dia:{modo:"otro_plan", sesion:cod}}, deshecho:false});
          c.dias = c.dias || {};
          c.dias[hoy] = {modo:"otro_plan", sesion:cod, act:null, t: ahora === undefined ? Date.now() : ahora};
          return c;
        },
        deshacer: reg => deshacerUltimo(reg, hoy, "recuperar", lun)
      };
    }
    return null;
  }

  // propuestaSemana(registro, hoy, plan?, desde?) -> null | {tipo, texto, aplicar(r), deshacer(r)}
  // Mira la semana anterior a la de hoy.
  function propuestaSemana(registro, hoy, plan, desde){
    const r = registro || {};
    if(!r.inicio || r.inicio > hoy) return null;
    const ant = sumaDias(lunesDe(hoy), -7);
    if(ant < lunesDe(r.inicio)) return null;
    if(desde && sumaDias(ant, 6) < desde) return null;
    const ad = adherencia(r, ant, plan, desde);
    if(!ad.previstas) return null;
    // en múltiplos de 0,5: sin errores de coma flotante
    if(ad.hechas * 5 >= ad.previstas * 4) return null;
    const txt = conComa(ad.hechas) + " de " + ad.previstas;
    if(ad.hechas * 5 >= ad.previstas * 3){
      if(hayAjuste(r, "repetir", ant)) return null;
      return {
        tipo:"repetir",
        texto:"La semana pasada hiciste " + txt + " sesiones. Repite las cargas de esa semana antes de subirlas.",
        aplicar: reg => conAjuste(reg, {f:hoy, que:"repetir", semana:ant, antes:{}, despues:{repetir:true}, deshecho:false}),
        deshacer: reg => deshacerUltimo(reg, hoy, "repetir", ant)
      };
    }
    if(hayAjuste(r, "alargar", ant)) return null;
    // Nunca un inicio posterior a hoy (pasa si empezaste a mitad de la semana pasada;
    // hoy cae en la misma semana, así que el efecto es el mismo)
    const mueve = ini => { const x = sumaDias(ini, 7); return x > hoy ? hoy : x; };
    return {
      tipo:"alargar",
      texto:"La semana pasada hiciste " + txt + " sesiones. Alarga el bloque una semana: la fecha de inicio pasa al " + corta(mueve(r.inicio)) + " y el final se retrasa.",
      aplicar: reg => {
        if(hayAjuste(reg, "alargar", ant)) return clon(reg);
        const nuevo = mueve(reg.inicio);
        const c = conAjuste(reg, {f:hoy, que:"alargar", semana:ant, antes:{inicio:reg.inicio}, despues:{inicio:nuevo}, deshecho:false});
        c.inicio = nuevo;
        return c;
      },
      deshacer: reg => deshacerUltimo(reg, hoy, "alargar", ant)
    };
  }

  // kcal extra (o menos) acumuladas por los avisos de peso aplicados en un bloque
  function kcalExtra(registro, bloque){
    return ajustesDe(registro).filter(a => !a.deshecho && a.que === "kcal" && a.bloque === bloque)
      .reduce((s, a) => s + (a.despues.kcal - a.antes.kcal), 0);
  }

  // propuestaPeso(registro, hoy, bloque) -> null | {tipo, kcal, texto, aplicar(r), deshacer(r)}
  //   bloque: código de la dieta, "B0" a "B5". La regla tiene que cumplirse dos semanas
  //   seguidas: media de cada semana frente a la anterior en los últimos 21 días.
  //   Hacen falta 10 pesajes en esos 21 días y 3 por semana.
  function propuestaPeso(registro, hoy, bloque){
    const r = registro || {}, h = aDias(hoy);
    const en = (a, b) => (r.peso || []).filter(p => { const d = aDias(p.f); return d > h - b && d <= h - a; }).map(p => p.kg);
    const sem = [en(0, 7), en(7, 14), en(14, 21)];
    if(sem.reduce((n, x) => n + x.length, 0) < PESAJES_MIN || sem.some(x => x.length < 3)) return null;
    const media = xs => xs.reduce((a, b) => a + b, 0) / xs.length;
    // dos comparaciones semanales seguidas: la última semana con la anterior, y esa con la previa
    const d1 = media(sem[0]) - media(sem[1]), d2 = media(sem[1]) - media(sem[2]);
    const delta = (d1 + d2) / 2;             // kg por semana
    let paso = 0, que = "";
    if(CONSTRUCCION[bloque]){
      if(d1 < 0.05 && d2 < 0.05){ paso = PASO_KCAL; que = "no estás subiendo de peso"; }
      else if(d1 > 0.35 && d2 > 0.35){ paso = -PASO_KCAL; que = "estás subiendo más rápido de lo previsto"; }
    } else if(DEFINICION[bloque]){
      if(d1 > -0.15 && d2 > -0.15){ paso = -PASO_KCAL; que = "no estás bajando de peso"; }
      else if(d1 < -0.5 && d2 < -0.5){ paso = PASO_KCAL; que = "estás bajando demasiado rápido"; }
    }
    if(!paso) return null;
    // si ya aplicaste un ajuste en estas dos semanas, espera a ver su efecto
    const reciente = ajustesDe(r).some(a => !a.deshecho && a.que === "kcal" && a.bloque === bloque && aDias(a.f) > h - 14);
    if(reciente) return null;
    const dr = r2(delta);
    return {
      tipo:"peso", kcal:paso,
      texto:"En las últimas dos semanas " + que + " (" + (dr > 0 ? "+" : "") + dr.toFixed(2).replace(".", ",") + " kg/sem). Prueba " + (paso > 0 ? "+" : "") + paso + " kcal al día.",
      aplicar: reg => { const k = kcalExtra(reg, bloque); return conAjuste(reg, {f:hoy, que:"kcal", bloque, antes:{kcal:k}, despues:{kcal:k + paso}, deshecho:false}); },
      deshacer: reg => deshacerUltimo(reg, hoy, "kcal")
    };
  }

  return {kcalActividad, dietaDelDia, adherencia, propuestaDia, propuestaSemana, propuestaPeso,
          deshacerAjuste, kcalExtra, corregirDia, revisarAjustes, PLAN};
})();
if (typeof module !== "undefined") module.exports = PLAZOS;
