# -*- coding: utf-8 -*-
"""Genera UN solo archivo HTML autocontenido con las siete secciones del sistema.
   No depende de Claude: se abre desde el móvil, el escritorio o donde sea.
   Para actualizarlo solo hay que volver a ejecutar esto y sustituir el archivo."""
import re, json, hashlib, datetime as dt

SECCIONES = [
    ("menus",   "Menús",        "menu/a2_menus.html",   "menu/a2.js", "menu/pay_menus.json",   "M"),
    ("compra",  "La compra",    "menu/a3_compra.html",  "menu/a3.js", "menu/pay_compra.json",  "C"),
    ("entreno", "El entreno",   "menu/a4_entreno.html", "menu/a4.js", "menu/pay_entreno.json", "E"),
    ("registro","Registro",     "menu/a6_registro.html","menu/a6.js", "menu/pay_registro.json","R"),
    ("teoria",  "La teoría",    "menu/a5_teoria.html",  "menu/a5.js", "menu/pay_entreno.json", "T"),
    ("info",    "Cómo funciona","menu/a1_info.html",    "menu/a1.js", "menu/pay_info.json",    "I"),
    ("manual",  "Actualizar",   None, None, None, None),
]

CSS_MANUAL = """
.doc{max-width:72ch}
.doc h2{font-size:25px;font-weight:700;letter-spacing:-.018em;margin:38px 0 12px;
  padding-bottom:8px;border-bottom:1px solid var(--line)}
.doc h3{font-size:19px;font-weight:700;margin:26px 0 8px}
.doc h4{font-size:16px;font-weight:700;margin:20px 0 6px}
.doc p,.doc li{font-size:15.5px;color:var(--ink-2)}
.doc p{margin:0 0 12px}
.doc ul,.doc ol{margin:0 0 14px;padding-left:22px;display:flex;flex-direction:column;gap:4px}
.doc code{font-family:var(--mono);font-size:.86em;background:var(--surface-2);
  border-radius:3px;padding:1px 5px;color:var(--ink)}
.doc pre{background:var(--surface);border:1px solid var(--line);border-radius:3px;
  padding:13px 15px;overflow-x:auto;margin:0 0 14px}
.doc pre code{background:none;padding:0;font-size:12.5px;line-height:1.55;white-space:pre}
.doc blockquote{margin:0 0 14px;padding:12px 15px;background:var(--amber-soft);
  border-left:3px solid var(--amber);border-radius:3px;font-size:15px;color:var(--ink-2)}
.doc hr{border:none;border-top:1px solid var(--line);margin:30px 0}
.doc .tscroll{margin:0 0 14px}
.doc table{min-width:480px}
.valores td.num{font-weight:600;color:var(--accent-ink)}
.valores table{min-width:0}
.vgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:3px;overflow:hidden;margin-bottom:14px}
.vgrid>div{background:var(--surface);padding:13px 14px;min-width:0}
.vgrid .v{font-family:var(--mono);font-size:20px;font-weight:600;color:var(--accent-ink);font-variant-numeric:tabular-nums}
.vgrid .eyebrow{overflow-wrap:anywhere}
@media (max-width:640px){.vgrid{grid-template-columns:repeat(2,1fr)}}
"""


def seccion_manual():
    """Manual (README) + valores con los que está generado el archivo."""
    import sys; sys.path.insert(0, 'menu')
    from md import convertir
    from entreno import PESO, TEST_5K, OBJETIVO_5K, FASES as FE, calendario, fecha, vdot, seg
    from modelo import FASES as FD
    cal = {c["cod"]: c for c in calendario()}
    filas = []
    for k, f in FE.items():
        d = FD[f["dieta"]]
        filas.append(f"<tr><td class='ex'>{k} · {f['n']}</td><td>{cal[k]['s0']}–{cal[k]['s1']}</td>"
                     f"<td class='num'>{d[2]:,}".replace(",", ".") + f"</td><td class='num'>{max(f['km'])}</td></tr>")
    valores = f"""
<div class="vgrid">
  <div><div class="v">{str(PESO).replace('.',',')} kg</div><div class="eyebrow">PESO · entreno.py</div></div>
  <div><div class="v">{TEST_5K}</div><div class="eyebrow">TEST_5K</div></div>
  <div><div class="v">{OBJETIVO_5K}</div><div class="eyebrow">OBJETIVO_5K</div></div>
  <div><div class="v">{vdot(5000, seg(TEST_5K)):.0f} → {vdot(5000, seg(OBJETIVO_5K)):.0f}</div><div class="eyebrow">VO₂máx estimado</div></div>
</div>
<div class="tscroll valores"><table><thead><tr><th>Bloque</th><th>Semanas</th><th class="num">kcal/día</th><th class="num">km/sem</th></tr></thead>
<tbody>{''.join(filas)}</tbody></table></div>
<p class="nota">Las kcal se cambian en <code>menu/modelo.py</code>; el resto de valores, en <code>menu/entreno.py</code>.</p>"""
    manual = convertir(open('README.md', encoding='utf-8').read())
    return ('<div class="wrap">\n<header class="masthead">'
            '<p class="eyebrow">Manual · cómo se actualiza este archivo</p>'
            '<h1>Cómo se <em>actualiza</em></h1>'
            '<p class="dek">Los valores con los que está generado este archivo y el manual completo para cambiarlos, desde tu ordenador o pidiéndoselo a Claude en el proyecto «gym_dieta».</p>'
            '</header>\n<section><div class="sec-head"><span class="num">01</span><h2>Valores actuales</h2></div>'
            + valores + '</section>\n<section><div class="sec-head"><span class="num">02</span><h2>El manual</h2></div>'
            '<div class="doc">' + manual + '</div></section>\n</div>')

CSS_BASE = open('menu/base.css', encoding='utf8').read()
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800'
 '&family=IBM+Plex+Mono:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">')

# Logo NK (docs/Icono@1x.png reescalado a 180x180). Va incrustado para que el HTML
# siga siendo un archivo unico que funciona sin cargar nada de fuera.
ICONO = ("data:image/png;base64,"
         "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"
         "AElFTkSuQmCC")

CSS_APP = """
html{scroll-padding-top:64px}
body{padding-top:0}
.appnav{position:sticky;top:0;z-index:40;background:var(--ground);
  border-bottom:1px solid var(--line);
  padding:10px max(14px,env(safe-area-inset-left)) 10px max(14px,env(safe-area-inset-right))}
.appnav .tiras{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;
  max-width:900px;margin:0 auto;-webkit-overflow-scrolling:touch}
.appnav .tiras::-webkit-scrollbar{display:none}
.appnav button{flex:none;font-family:var(--sans);font-size:13px;font-weight:700;
  padding:8px 14px;border-radius:999px;border:1px solid var(--line-2);background:var(--surface);
  color:var(--ink-2);cursor:pointer;white-space:nowrap;transition:all .12s}
.appnav button[aria-current="true"]{background:var(--accent);border-color:var(--accent);color:#FFFFFF}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .appnav button[aria-current="true"]{color:#FFFFFF}}
:root[data-theme="dark"] .appnav button[aria-current="true"]{color:#FFFFFF}
.app-sec{display:none}
.app-sec.on{display:block}
.app-sec .hermanos{display:none}
.app-sec .masthead{padding-block:28px 18px}
.sello{max-width:900px;margin:0 auto;padding:22px 20px 40px;font-family:var(--mono);
  font-size:11px;color:var(--ink-3);line-height:1.7;border-top:1px solid var(--line)}
.sello b{color:var(--ink-2);font-weight:600}
"""

NAV_JS = """
(function(){
  var SEC = %(lista)s;
  var nav = document.getElementById('appnav');
  var botones = {};
  function ir(id, guardar){
    SEC.forEach(function(s){
      var d = document.getElementById('s-'+s[0]);
      if(d) d.classList.toggle('on', s[0]===id);
      if(botones[s[0]]) botones[s[0]].setAttribute('aria-current', s[0]===id ? 'true':'false');
    });
    if(guardar){ try{ localStorage.setItem('app_sec', id); }catch(e){} }
    window.scrollTo(0,0);
    if(botones[id] && botones[id].scrollIntoView)
      botones[id].scrollIntoView({block:'nearest', inline:'center'});
  }
  SEC.forEach(function(s){
    var b = document.createElement('button');
    b.textContent = s[1];
    b.addEventListener('click', function(){ ir(s[0], true); });
    botones[s[0]] = b;
    nav.append(b);
  });
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('[data-ir]');
    if(a){ e.preventDefault(); ir(a.getAttribute('data-ir'), true); }
  });
  var ini = SEC[0][0];
  try{ var g = localStorage.getItem('app_sec');
       if(g && SEC.some(function(s){return s[0]===g;})) ini = g; }catch(e){}
  ir(ini, false);
})();
"""

# App instalable: solo se activa servida por https o localhost (GitHub Pages); abierta como
# archivo suelto no hace nada y el archivo sigue funcionando igual.
PWA_JS = """
if ("serviceWorker" in navigator && /^https?:$/.test(location.protocol)) {
  navigator.serviceWorker.register("sw.js").catch(function(){});
  try { if (navigator.storage && navigator.storage.persist) navigator.storage.persist(); } catch(e) {}
}
"""

def partes(ruta):
    """Separa los bloques <style> del cuerpo."""
    txt = open(ruta, encoding='utf8').read()
    estilos = re.findall(r'<style>(.*?)</style>', txt, re.S)
    cuerpo = re.sub(r'<style>.*?</style>\s*', '', txt, flags=re.S)
    return "\n".join(estilos), cuerpo.strip()

def construir():
    estilos, cuerpos, scripts = [], [], []
    for cod, etiqueta, html, js, datos, var in SECCIONES:
        if html is None:                       # sección estática: el manual
            estilos.append(CSS_MANUAL)
            cuerpos.append('<div class="app-sec" id="s-%s">\n%s\n</div>' % (cod, seccion_manual()))
            continue
        css, cuerpo = partes(html)
        estilos.append("/* === %s === */\n%s" % (cod, css))
        cuerpos.append('<div class="app-sec" id="s-%s">\n%s\n</div>' % (cod, cuerpo))

        codigo = open(js, encoding='utf8').read()
        # cada sección busca sus elementos SOLO dentro de su propio contenedor,
        # así los identificadores repetidos entre secciones no chocan
        codigo = codigo.replace('document.getElementById(', '$(')
        carga = open(datos, encoding='utf8').read()
        scripts.append(
            "(function(){\n"
            "var ROOT=document.getElementById('s-%s');\n"
            "var $=function(id){return ROOT.querySelector('#'+id);};\n"
            "const %s = %s;\n%s\n})();" % (cod, var, carga, codigo))

    lista = json.dumps([[c, e] for c, e, *_ in SECCIONES], ensure_ascii=False)
    hoy = dt.date.today()
    MES = {1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",
           7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"}
    cuerpo_todo = "\n\n".join(cuerpos)
    firma = hashlib.sha256((cuerpo_todo + "".join(scripts)).encode()).hexdigest()[:8]

    doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#000000">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="GD plan">
<meta name="description" content="Plan de entrenamiento y alimentación de Abraham: un ciclo de 39 semanas, repetible.">
<title>planificacion_dieta_gym</title>
<link rel="icon" href="{ICONO}">
<link rel="apple-touch-icon" href="{ICONO}">
<link rel="manifest" href="manifest.webmanifest">
{FUENTES}
<style>
{CSS_BASE}
{CSS_APP}
{"".join(chr(10)+e for e in estilos)}
</style>
</head>
<body>
<nav class="appnav"><div class="tiras" id="appnav"></div></nav>
<main>
{cuerpo_todo}
</main>
<div class="sello">
  versión {firma} · {hoy.day} de {MES[hoy.month]} de {hoy.year}
</div>
<script>
{NAV_JS % {"lista": lista}}
{PWA_JS}
</script>
{"".join(chr(10)+"<script>"+chr(10)+s+chr(10)+"</script>" for s in scripts)}
</body>
</html>
"""
    import os
    os.makedirs('salida', exist_ok=True); os.makedirs('docs', exist_ok=True)
    destino = 'salida/planificacion_dieta_gym.html'
    open(destino, 'w', encoding='utf8').write(doc)
    open('docs/index.html', 'w', encoding='utf8').write(doc)   # para GitHub Pages
    print(f"planificacion_dieta_gym.html: {len(doc)//1024} KB · versión {firma} · {len(SECCIONES)} secciones")
    return destino

if __name__ == "__main__":
    construir()
