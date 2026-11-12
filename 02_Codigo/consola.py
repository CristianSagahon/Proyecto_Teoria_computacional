"""
consola.py - Utilidades para que la consola se vea bonita: colores, títulos
con recuadro, mensajes de éxito/error y tablas.

No tiene teoría del curso; solo es presentación. Usa códigos de escape ANSI
(ej. '\\033[32m' = verde). Si la salida no es una terminal (por ejemplo cuando
se redirige a un archivo), los colores se apagan solos para no ensuciar el texto.
"""

import os
import sys


def _soporta_color():
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not sys.stdout.isatty():
        return False
    if os.name == "nt":
        os.system("")          # activa los colores ANSI en la consola de Windows
    return True


USAR_COLOR = _soporta_color()
ANCHO = 72


def _c(codigo, texto):
    return f"\033[{codigo}m{texto}\033[0m" if USAR_COLOR else str(texto)


def negrita(t):  return _c("1", t)
def gris(t):     return _c("90", t)
def rojo(t):     return _c("91", t)
def verde(t):    return _c("92", t)
def amarillo(t): return _c("93", t)
def azul(t):     return _c("94", t)
def morado(t):   return _c("95", t)
def cian(t):     return _c("96", t)


# ------------------------------- mensajes -------------------------------
def titulo(texto, icono=""):
    linea = "─" * ANCHO
    print()
    print(cian("┌" + linea))
    print(cian("│ ") + negrita(f"{icono}  {texto}" if icono else texto))
    print(cian("└" + linea))


def subtitulo(texto):
    print("\n" + azul("▸ ") + negrita(texto))


def explicacion(texto):
    """Texto gris que explica qué hace la opción."""
    print(gris(f"  ℹ  {texto}"))


def exito(texto):   print(verde(f"  ✔  {texto}"))
def error(texto):   print(rojo(f"  ✖  {texto}"))
def aviso(texto):   print(amarillo(f"  ⚠  {texto}"))
def dato(etiqueta, valor):
    print(f"  {gris(etiqueta + ':')} {valor}")


def preguntar(pregunta, ejemplo=None, por_defecto=None, texto_enter=None):
    """
    Pide un dato mostrando un ejemplo de qué escribir.
    Si el usuario solo da Enter, regresa 'por_defecto'.
    'texto_enter' explica qué pasa al dar Enter vacío (ej. "regresar al menú").
    """
    pista = []
    if ejemplo:
        pista.append(f"ej. {ejemplo}")
    if por_defecto is not None:
        pista.append(f"Enter = {texto_enter or por_defecto or 'nada'}")
    extra = gris(f" ({', '.join(pista)})") if pista else ""
    respuesta = input(f"\n  {amarillo('➜')} {pregunta}{extra}: ").strip()
    if not respuesta and por_defecto is not None:
        return por_defecto
    return respuesta


def pausa():
    """Espera Enter para que el resultado no se pierda al volver al menú.
    Si la entrada no es un teclado (pruebas automáticas), no espera."""
    if sys.stdin.isatty():
        input(gris("\n  ⏎  Presiona Enter para volver al menú..."))


# -------------------------------- tablas --------------------------------
def tabla(encabezados, filas):
    """
    Dibuja una tabla con bordes. Cada celda puede ser un texto o una tupla
    (texto, funcion_de_color) para pintarla, ej. ("Falla", rojo).
    """
    def texto_de(celda):
        return str(celda[0]) if isinstance(celda, tuple) else str(celda)

    anchos = [len(h) for h in encabezados]
    for fila in filas:
        for i, celda in enumerate(fila):
            anchos[i] = max(anchos[i], len(texto_de(celda)))

    def borde(izq, medio, der):
        return gris(izq + medio.join("─" * (a + 2) for a in anchos) + der)

    def renglon(celdas, es_encabezado=False):
        partes = []
        for i, celda in enumerate(celdas):
            texto = texto_de(celda).ljust(anchos[i])
            if es_encabezado:
                texto = negrita(texto)
            elif isinstance(celda, tuple):
                texto = celda[1](texto)
            partes.append(f" {texto} ")
        return gris("│") + gris("│").join(partes) + gris("│")

    print("  " + borde("┌", "┬", "┐"))
    print("  " + renglon(encabezados, True))
    print("  " + borde("├", "┼", "┤"))
    for fila in filas:
        print("  " + renglon(fila))
    print("  " + borde("└", "┴", "┘"))
