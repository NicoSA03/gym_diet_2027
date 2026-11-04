# -*- coding: utf-8 -*-
"""Pestaña «Actualizar» de la v2.4 (retirada de la app en la v2.5).
   Estaba en menu/standalone.py: CSS_MANUAL y seccion_manual(), más la entrada
   ("manual", "Actualizar", None, None, None, None) de SECCIONES y la rama de construir()
   que la montaba. Usaba md.py (convertir) para pasar README.md a HTML.
   Se guarda por si hace falta; el manual se lee en README.md."""

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
.doc p code,.doc li code,.doc blockquote code{overflow-wrap:anywhere}
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
        filas.append(f"<tr><td class='ex'>{k}: {f['n']}</td><td>{cal[k]['s0']}-{cal[k]['s1']}</td>"
                     f"<td class='num'>{d[2]:,}".replace(",", ".") + f"</td><td class='num'>{max(f['km'])}</td></tr>")
    valores = f"""
<div class="vgrid">
  <div><div class="v">{str(PESO).replace('.',',')} kg</div><div class="eyebrow">PESO, perfil.json</div></div>
  <div><div class="v">{TEST_5K}</div><div class="eyebrow">TEST_5K</div></div>
  <div><div class="v">{OBJETIVO_5K}</div><div class="eyebrow">OBJETIVO_5K</div></div>
  <div><div class="v">{vdot(5000, seg(TEST_5K)):.0f} → {vdot(5000, seg(OBJETIVO_5K)):.0f}</div><div class="eyebrow">VO₂máx estimado</div></div>
</div>
<div class="tscroll valores"><table><thead><tr><th>Bloque</th><th>Semanas</th><th class="num">kcal/día</th><th class="num">km/sem</th></tr></thead>
<tbody>{''.join(filas)}</tbody></table></div>
<p class="nota">Las kcal se cambian en <code>menu/modelo.py</code>; peso y 5 km, en <code>datos/perfil.json</code>; el resto, en <code>menu/entreno.py</code>.</p>"""
    manual = convertir(open('README.md', encoding='utf-8').read())
    return ('<div class="wrap">\n<header class="masthead">'
            '<p class="eyebrow">Manual, cómo se actualiza este archivo</p>'
            '<h1>Cómo se <em>actualiza</em></h1>'
            '<p class="dek">Los valores con los que está generado este archivo y el manual completo para cambiarlos, desde tu ordenador o pidiéndoselo a Claude en el proyecto «gym_dieta».</p>'
            '</header>\n<section><div class="sec-head"><span class="num">01</span><h2>Valores actuales</h2></div>'
            + valores + '</section>\n<section><div class="sec-head"><span class="num">02</span><h2>El manual</h2></div>'
            '<div class="doc">' + manual + '</div></section>\n</div>')
