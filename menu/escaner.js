// Escáner de códigos de barras (v2.1). Solo la cámara y la lectura; qué se hace con
// el código lo decide quien lo llama (menu/a2.js).
//
// Cómo lee:
//   1. Si el navegador trae lector propio (BarcodeDetector: Chrome en Android y en
//      algunos ordenadores), usa ese. No carga nada extra.
//   2. Si no (iPhone, Firefox, la mayoría de PC), carga docs/vendor/quagga.min.js
//      (Quagga2, licencia MIT, unos 150 KB) la primera vez que escaneas. Queda
//      guardado para usarlo sin conexión.
//   3. Si no hay cámara, no das permiso o abres el archivo suelto (sin https), se
//      puede escribir el código a mano.
// Solo acepta códigos de producto (EAN-13, EAN-8, UPC) y comprueba su dígito de
// control, así que no se cuela una lectura mal hecha.

const ESCANER = (function(){
  const FORMATOS = ["ean_13", "ean_8", "upc_a", "upc_e"];
  let quaggaCargada = null;
  // Según cómo se empaquete, Quagga2 queda en window.Quagga o en window.Quagga.default
  const Q = () => window.Quagga && (window.Quagga.default || window.Quagga);

  // Dígito de control de EAN-8, UPC-A (12) y EAN-13
  function valido(c){
    if(!/^\d+$/.test(c) || [8, 12, 13].indexOf(c.length) < 0) return false;
    const d = c.split("").map(Number), control = d.pop();
    let s = 0;
    d.reverse().forEach((x, i) => { s += x * (i % 2 === 0 ? 3 : 1); });
    return (10 - s % 10) % 10 === control;
  }
  // Los UPC-A de 12 cifras son EAN-13 con un 0 delante: así se buscan igual
  const normaliza = c => c.length === 12 ? "0" + c : c;

  function cargaQuagga(){
    if(Q()) return Promise.resolve();
    if(quaggaCargada) return quaggaCargada;
    quaggaCargada = new Promise((ok, mal) => {
      const s = document.createElement("script");
      s.src = "vendor/quagga.min.js";
      s.onload = () => Q() ? ok() : mal();
      s.onerror = () => { quaggaCargada = null; mal(); };
      document.head.append(s);
    });
    return quaggaCargada;
  }

  async function nativoSirve(){
    if(!("BarcodeDetector" in window)) return false;
    try{
      const f = await window.BarcodeDetector.getSupportedFormats();
      return FORMATOS.some(x => f.indexOf(x) >= 0);
    }catch(e){ return false; }
  }

  const nodo = (t, c, x) => { const n = document.createElement(t); if(c) n.className = c; if(x !== undefined) n.textContent = x; return n; };

  // Abre la pantalla de la cámara. alLeer(código) se llama una sola vez.
  function abrir(alLeer){
    const capa = nodo("div", "esc-capa");
    capa.setAttribute("role", "dialog"); capa.setAttribute("aria-label", "Escanear código de barras");
    const vista = nodo("div", "esc-vista");
    const marco = nodo("div", "esc-marco");
    const texto = nodo("p", "esc-texto", "Abriendo la cámara...");
    const manual = nodo("form", "esc-manual");
    const inp = nodo("input"); inp.inputMode = "numeric"; inp.placeholder = "8 o 13 cifras";
    inp.setAttribute("aria-label", "Código de barras");
    const ir = nodo("button", "m-btn prim", "Buscar"); ir.type = "submit";
    manual.append(inp, ir); manual.hidden = true;
    const pie = nodo("div", "esc-pie");
    const bManual = nodo("button", "m-btn", "Escribir el código");
    const bCerrar = nodo("button", "m-btn", "Cancelar");
    pie.append(bManual, bCerrar);
    vista.append(marco);
    capa.append(vista, texto, manual, pie);
    document.body.append(capa);

    let vivo = true, flujo = null, bucle = null, usaQuagga = false;
    const ultimas = [];
    function cerrar(){
      vivo = false;
      if(bucle) clearTimeout(bucle);
      if(usaQuagga && Q()){ try{ Q().offDetected(); Q().stop(); }catch(e){} }
      if(flujo) flujo.getTracks().forEach(t => t.stop());
      capa.remove();
    }
    function entrega(c){
      if(!vivo) return;
      if(navigator.vibrate) navigator.vibrate(60);
      cerrar(); alLeer(normaliza(c));
    }
    // sinCamara: la cámara no ha abierto, así que se quita el recuadro negro
    function aMano(msg, sinCamara){
      if(msg) texto.textContent = msg;
      if(sinCamara) vista.hidden = true;
      manual.hidden = false; bManual.hidden = true;
      setTimeout(() => inp.focus(), 0);
    }
    bCerrar.addEventListener("click", cerrar);
    bManual.addEventListener("click", () => aMano("Escribe los números que hay debajo de las barras."));
    manual.addEventListener("submit", e => {
      e.preventDefault();
      const c = inp.value.replace(/\D/g, "");
      if(valido(c)) entrega(c); else texto.textContent = "Ese código no es válido: revisa los números.";
    });

    (async () => {
      if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.isSecureContext)
        return aMano("La cámara solo funciona en la app instalada. Escribe el código.", true);
      try{
        if(await nativoSirve()){
          flujo = await navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}, audio: false});
          if(!vivo){ flujo.getTracks().forEach(t => t.stop()); return; }
          const v = nodo("video"); v.setAttribute("playsinline", ""); v.muted = true; v.srcObject = flujo;
          vista.prepend(v); await v.play();
          texto.textContent = "Apunta al código de barras";
          const det = new window.BarcodeDetector({formats: FORMATOS});
          const mira = async () => {
            if(!vivo) return;
            try{
              const r = await det.detect(v);
              const c = r.map(x => x.rawValue).find(valido);
              if(c) return entrega(c);
            }catch(e){}
            bucle = setTimeout(mira, 180);
          };
          mira();
        } else {
          await cargaQuagga();
          if(!vivo) return;
          usaQuagga = true;
          Q().init({
            inputStream: {type: "LiveStream", target: vista,
                          constraints: {facingMode: "environment", width: {ideal: 1280}, height: {ideal: 720}}},
            decoder: {readers: ["ean_reader", "ean_8_reader", "upc_reader"]},
            // «large» encuentra mejor el código cuando lo acercas a la cámara, que es lo normal
            locate: true, locator: {patchSize: "large", halfSample: true},
            frequency: 10                     // 10 intentos por segundo: suficiente y gasta menos batería
          }, err => {
            if(err || !vivo){ if(vivo) aMano("No se ha podido abrir la cámara. Escribe el código.", true); return; }
            Q().start();
            texto.textContent = "Apunta al código de barras";
          });
          // Quagga a veces lee mal una barra: solo vale si sale igual tres veces seguidas
          Q().onDetected(r => {
            const c = r && r.codeResult && r.codeResult.code;
            if(!c || !valido(c)) return;
            ultimas.push(c); if(ultimas.length > 3) ultimas.shift();
            if(ultimas.length === 3 && ultimas.every(x => x === c)) entrega(c);
          });
        }
      }catch(e){
        aMano(e && e.name === "NotAllowedError"
          ? "No has dado permiso a la cámara. Puedes escribir el código."
          : "No se ha podido abrir la cámara. Escribe el código.", true);
      }
    })();
  }

  return {abrir, valido};
})();
if (typeof module !== "undefined") module.exports = ESCANER;
