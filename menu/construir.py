# -*- coding: utf-8 -*-
import json, os
os.makedirs('salida/paginas', exist_ok=True)
CSS = open('menu/base.css',encoding='utf8').read()
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800'
 '&family=IBM+Plex+Mono:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">')

def pagina(titulo, cuerpo_f, js_f, datos=None, nombre_var=None):
    cuerpo = open(cuerpo_f,encoding='utf8').read()
    js     = open(js_f,encoding='utf8').read()
    bloque_datos = ""
    if datos:
        bloque_datos = f"const {nombre_var} = " + open(datos,encoding='utf8').read() + ";\n"
    return (f"<title>{titulo}</title>\n{FUENTES}\n<style>\n{CSS}\n</style>\n"
            f"{cuerpo}\n<script>\n{bloque_datos}{js}\n</script>\n")

import sys
if __name__=="__main__":
    cual = sys.argv[1] if len(sys.argv)>1 else "todos"
    if cual in ("todos","2"):
        h = pagina("Qué Como Hoy",'menu/a2_menus.html','menu/a2.js','menu/pay_menus.json','M')
        open('salida/paginas/menus.html','w',encoding='utf8').write(h)
        print("menus.html:", len(h)//1024, "KB")
    if cual in ("todos","3"):
        h = pagina("La Compra de la Semana",'menu/a3_compra.html','menu/a3.js','menu/pay_compra.json','C')
        open('salida/paginas/compra.html','w',encoding='utf8').write(h)
        print("compra.html:", len(h)//1024, "KB")
    if cual in ("todos","4"):
        h = pagina("Qué Toca Hoy",'menu/a4_entreno.html','menu/a4.js','menu/pay_entreno.json','E')
        open('salida/paginas/entreno.html','w',encoding='utf8').write(h)
        print("entreno.html:", len(h)//1024, "KB")
    if cual in ("todos","5"):
        h = pagina("Por Qué el Plan Es Así",'menu/a5_teoria.html','menu/a5.js','menu/pay_entreno.json','T')
        open('salida/paginas/teoria.html','w',encoding='utf8').write(h)
        print("teoria.html:", len(h)//1024, "KB")
    if cual in ("todos","1"):
        h = pagina("Cómo Funciona el Plan",'menu/a1_info.html','menu/a1.js','menu/pay_info.json','I')
        open('salida/paginas/info.html','w',encoding='utf8').write(h)
        print("info.html:", len(h)//1024, "KB")
