# -*- coding: utf-8 -*-
# kcal, Proteina, Grasa, Carbohidrato por 100 g | formato de venta (g) | precio | grupo | fuente
# grupos: carb (escala), grasa (escala), prot (escala), fijo (no escala)
F = {
 # --- añadidos ---
 "Kéfir natural":             ( 63,  3.4,  3.5,  4.5,    500,   1.25, "fijo", "e"),
 # --- cereales y tuberculos ---
 "Copos de avena Hacendado":  (375, 13.5,  7.0, 60.0,   1000,   1.30, "carb", "e"),
 "Arroz largo Hacendado":     (360,  7.0,  0.9, 79.0,   1000,   1.25, "carb", "e"),
 "Pasta integral":            (350, 13.0,  2.5, 63.0,   1000,   1.15, "carb", "e"),
 "Ñoquis de patata":          (160,  4.0,  1.0, 33.0,    500,   1.35, "carb", "e"),
 "Patata":                    ( 80,  2.0,  0.1, 17.0,   5000,   4.50, "carb", "e"),
 "Batata":                    ( 86,  1.6,  0.1, 20.0,   1000,   2.20, "carb", "e"),
 "Pan integral de molde":     (250,  9.0,  3.5, 43.0,    450,   1.20, "carb", "e"),
 # --- legumbre de bote (sin cocinar) ---
 "Lentejas cocidas (bote)":   ( 95,  7.0,  0.5, 14.0,    570,   1.00, "carb", "e"),
 "Garbanzos cocidos (bote)":  (120,  7.0,  2.5, 16.0,    570,   1.10, "carb", "e"),
 "Alubias cocidas (bote)":    (100,  7.0,  0.6, 15.0,    570,   1.05, "carb", "e"),
 # --- proteina animal ---
 "Pechuga de pollo":          (110, 23.0,  1.8,  0.0,   1200,   6.76, "prot", "f"),
 "Ternera magra (babilla)":   (135, 22.0,  5.0,  0.0,   1000,  11.00, "prot", "e"),
 "Filete de pavo":            (105, 22.0,  1.5,  0.0,    500,   4.00, "prot", "e"),
 "Pavo en lonchas":           (105, 18.0,  2.5,  2.0,    200,   2.20, "prot", "e"),

 "Merluza congelada":         ( 72, 16.0,  0.6,  0.0,   1000,   6.50, "prot", "e"),
 "Salmón fresco":             (200, 20.0, 13.0,  0.0,    500,   9.00, "prot", "e"),
 "Atún claro al natural":     (110, 25.0,  1.0,  0.0,    240,   2.40, "prot", "f"),
 "Huevos":                    (143, 12.6,  9.9,  0.7,    720,   2.63, "fijo", "f"),
 # --- lacteos ---
 "Leche semidesnatada":       ( 46,  3.2,  1.6,  4.8,   1000,   0.79, "fijo", "e"),
 "Queso batido 0% / skyr":    ( 60, 10.0,  0.3,  4.0,    500,   1.45, "prot", "e"),
 "Yogur natural":             ( 60,  4.0,  3.0,  4.5,    500,   0.95, "fijo", "e"),
 "Queso rallado (ingred.)":   (380, 26.0, 29.0,  2.0,    200,   2.20, "grasa","e"),
 "Proteína en polvo":         (380, 78.0,  5.0,  6.0,    500,   9.50, "prot", "e"),
 # --- fibra vegetal sin elaboracion ---
 "Gazpacho (brik)":           ( 40,  0.8,  2.5,  3.5,   1000,   1.55, "fijo", "e"),
 "Verdura congelada":         ( 40,  2.5,  0.4,  5.0,   1000,   1.80, "fijo", "e"),
 "Guisantes congelados":      ( 80,  5.5,  0.4, 11.0,   1000,   1.70, "fijo", "e"),
 "Champiñón laminado":        ( 22,  3.0,  0.3,  1.0,    500,   1.60, "fijo", "e"),
 "Verduras asadas (batch)":   ( 45,  1.5,  2.0,  5.0,   1000,   2.00, "fijo", "e"),
 "Tomate cherry":             ( 20,  1.0,  0.2,  3.0,    500,   1.70, "fijo", "e"),
 # --- para la mochila: cero preparación ---
 "Bolsita de fruta":          ( 65,  0.4,  0.2, 15.0,    400,   1.90, "carb", "e"),
 "Almendras":                 (600, 21.0, 53.0,  5.0,    200,   3.00, "grasa","e"),
 "Batido proteínas (botella)":( 60,  6.0,  1.5,  5.5,    330,   1.20, "prot", "e"),
 # --- fruta y grasas ---
 "Plátano":                   ( 89,  1.1,  0.3, 20.0,   1000,   1.75, "carb", "e"),
 "Manzana":                   ( 52,  0.3,  0.2, 12.0,   1000,   2.00, "carb", "e"),
 "Nueces":                    (654, 15.0, 65.0,  7.0,    500,   4.50, "grasa","e"),
 "Crema de cacahuete":        (600, 25.0, 50.0, 12.0,    500,   3.00, "grasa","e"),
 "Aguacate":                  (160,  2.0, 15.0,  2.0,    500,   3.50, "grasa","e"),
 "Aceite de oliva virgen ex.":(900,  0.0,100.0,  0.0,   1000,   7.50, "grasa","e"),
}

def macros(items):
    t=[0.0]*4
    for n,g in items:
        k,p,gr,c = F[n][:4]
        t[0]+=k*g/100; t[1]+=p*g/100; t[2]+=gr*g/100; t[3]+=c*g/100
    return tuple(round(x,1) for x in t)
