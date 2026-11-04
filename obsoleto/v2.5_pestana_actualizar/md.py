# -*- coding: utf-8 -*-
"""Conversor mínimo de Markdown a HTML (solo lo que usa el README), sin dependencias."""
import html, re


def _inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\w)", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    return t


def convertir(md):
    lineas = md.splitlines()
    out, i = [], 0
    while i < len(lineas):
        l = lineas[i]
        if l.startswith("```"):
            j = i + 1
            bloque = []
            while j < len(lineas) and not lineas[j].startswith("```"):
                bloque.append(lineas[j]); j += 1
            out.append("<pre><code>" + html.escape("\n".join(bloque), quote=False) + "</code></pre>")
            i = j + 1; continue
        if re.match(r"^-{3,}\s*$", l):
            out.append("<hr>"); i += 1; continue
        m = re.match(r"^(#{1,4})\s+(.*)", l)
        if m:
            n = len(m.group(1)) + 1          # el h1 del README pasa a h2 dentro de la página
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>"); i += 1; continue
        if l.startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].startswith("|"):
                celdas = [c.strip() for c in lineas[i].strip().strip("|").split("|")]
                if not all(re.match(r"^:?-{2,}:?$", c) for c in celdas):
                    filas.append(celdas)
                i += 1
            cab, *cuerpo = filas
            t = ['<div class="tscroll"><table><thead><tr>']
            t += [f"<th>{_inline(c)}</th>" for c in cab]
            t.append("</tr></thead><tbody>")
            for f in cuerpo:
                t.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in f) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t)); continue
        if l.startswith(">"):
            bloque = []
            while i < len(lineas) and lineas[i].startswith(">"):
                bloque.append(lineas[i].lstrip("> ").rstrip()); i += 1
            out.append("<blockquote>" + _inline(" ".join(bloque)) + "</blockquote>"); continue
        if re.match(r"^\s*[-*]\s+", l) or re.match(r"^\s*\d+\.\s+", l):
            ordenada = bool(re.match(r"^\s*\d+\.\s+", l))
            items = []
            while i < len(lineas) and (re.match(r"^\s*[-*]\s+", lineas[i]) or re.match(r"^\s*\d+\.\s+", lineas[i])):
                items.append(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lineas[i])); i += 1
            tag = "ol" if ordenada else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if not l.strip():
            i += 1; continue
        parr = []
        while i < len(lineas) and lineas[i].strip() and not re.match(r"^(#|```|\||>|-{3,}|\s*[-*]\s|\s*\d+\.\s)", lineas[i]):
            parr.append(lineas[i].strip()); i += 1
        out.append("<p>" + _inline(" ".join(parr)) + "</p>")
    return "\n".join(out)
