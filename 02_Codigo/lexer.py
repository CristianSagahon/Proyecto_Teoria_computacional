"""
lexer.py - Analizador léxico (scanner) del archivo de red.

CONCEPTO TEÓRICO
----------------
El analizador léxico es la primera fase de un compilador. Lee el texto
carácter por carácter y lo agrupa en "tokens" (las palabras del lenguaje).
Cada clase de token se describe con una EXPRESIÓN REGULAR, es decir, con un
LENGUAJE REGULAR que se puede reconocer con un autómata finito.

Tokens del lenguaje de red:
    Palabras reservadas : RED ROUTER SWITCH PC SERVER DB ENLACE
    ID                  : nombre de un dispositivo (R1, SW1, PC2 ...)
    NUM                 : latencia en ms (entero positivo sin ceros a la izquierda)
    {  }  :  ;          : símbolos de puntuación
    # comentario        : se ignora

El lexer NO se detiene en el primer error: los junta todos en una lista para
que el usuario pueda corregir el archivo de una sola vez.
"""

import re

# ---------------------------------------------------------------------------
# EXPRESIONES REGULARES DEL PROYECTO
# ---------------------------------------------------------------------------

# Nombre: REGEX_IDENTIFICADOR
# Propósito: validar el nombre de un dispositivo (R1, SW1, PC2, SRV1, DB1).
# Explicación: [A-Z]          -> el primer carácter es una letra MAYÚSCULA
#              [A-Za-z0-9]*   -> después cero o más letras o dígitos
# Ejemplos aceptados: R1, SW1, Servidor2      Rechazados: pc1, 1PC, SW_1
REGEX_IDENTIFICADOR = re.compile(r"[A-Z][A-Za-z0-9]*")

# Nombre: REGEX_PESO
# Propósito: validar la latencia (peso de la arista) en milisegundos.
# Explicación: [1-9]   -> el primer dígito NO puede ser 0 (rechaza "0" y "05")
#              [0-9]*  -> después cualquier cantidad de dígitos
# Ejemplos aceptados: 1, 5, 10, 250      Rechazados: 0, 05, 007
REGEX_PESO = re.compile(r"[1-9][0-9]*")

# Nombre: REGEX_LINEA_PING
# Propósito: validar cada línea del archivo pings.txt.
# Explicación: ^                    -> inicio de la línea
#              ([A-Z][A-Za-z0-9]*)  -> grupo 1: nombre del dispositivo (mismo
#                                      patrón que REGEX_IDENTIFICADOR)
#              \s+                  -> uno o más espacios
#              (OK|TIMEOUT)         -> grupo 2: resultado del ping, solo OK o TIMEOUT
#              $                    -> fin de la línea (no se permite nada más)
# Ejemplos aceptados: "PC2 OK", "SW1   TIMEOUT"   Rechazados: "PC2 LOST", "pc2 OK"
REGEX_LINEA_PING = re.compile(r"^([A-Z][A-Za-z0-9]*)\s+(OK|TIMEOUT)$")

# Nombre: REGEX_COMENTARIO
# Propósito: reconocer comentarios para ignorarlos.
# Explicación: #        -> empieza con el carácter numeral
#              [^\n]*   -> cualquier carácter excepto salto de línea, hasta el
#                          final de la línea
# Ejemplo: "# esta es la red del laboratorio"
REGEX_COMENTARIO = re.compile(r"#[^\n]*")

# Expresiones auxiliares: sirven para "recortar" el lexema completo y después
# validarlo con las expresiones de arriba (así podemos explicar el error).
# Nombre: REGEX_PALABRA -> cualquier palabra formada por letras, dígitos o '_'
REGEX_PALABRA = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# Nombre: REGEX_NUMERO -> empieza con dígito y puede traer letras pegadas (p. ej. "5ms")
REGEX_NUMERO = re.compile(r"[0-9][A-Za-z0-9_]*")

# Palabras reservadas del lenguaje (terminales de la gramática).
PALABRAS_RESERVADAS = {"RED", "ROUTER", "SWITCH", "PC", "SERVER", "DB", "ENLACE"}

# Tipos de dispositivo (el no terminal T de la gramática).
TIPOS_DISPOSITIVO = {"ROUTER", "SWITCH", "PC", "SERVER", "DB"}

# Símbolos de un solo carácter y el nombre de su token.
SIMBOLOS = {
    "{": "LLAVE_ABRE",
    "}": "LLAVE_CIERRA",
    ":": "DOS_PUNTOS",
    ";": "PUNTO_Y_COMA",
}


class Token:
    """Un token: tipo, lexema (valor), línea y columna donde empieza."""

    def __init__(self, tipo, valor, linea, columna):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna

    def __repr__(self):
        return f"Token({self.tipo}, '{self.valor}', {self.linea}:{self.columna})"


class ErrorLexico:
    """Error léxico con su posición y un motivo entendible."""

    def __init__(self, linea, columna, lexema, motivo):
        self.linea = linea
        self.columna = columna
        self.lexema = lexema
        self.motivo = motivo

    def __str__(self):
        return f"Línea {self.linea}, columna {self.columna}: {self.motivo}"


def _clasificar_palabra(palabra):
    """
    Decide qué token es una palabra. Devuelve (tipo_token, None) si es válida
    o (None, motivo_del_error) si no lo es.
    """
    # 1) Palabra reservada escrita exactamente igual.
    if palabra in PALABRAS_RESERVADAS:
        return palabra, None
    # 2) Palabra reservada escrita en minúsculas o mezclando mayúsculas.
    if palabra.upper() in PALABRAS_RESERVADAS:
        return None, (f"'{palabra}' no es válido (las palabras reservadas van en "
                      f"mayúsculas), ¿quisiste decir {palabra.upper()}?")
    # 3) Identificador que cumple REGEX_IDENTIFICADOR completo.
    if REGEX_IDENTIFICADOR.fullmatch(palabra):
        return "ID", None
    # 4) Errores de identificador: explicamos el motivo exacto.
    if palabra[0].islower():
        return None, f"'{palabra}' no es un nombre válido: debe iniciar con mayúscula"
    return None, (f"'{palabra}' no es un nombre válido: solo se permiten letras y "
                  f"dígitos (sin '_')")


def _clasificar_numero(numero):
    """Valida un número con REGEX_PESO. Devuelve (tipo, None) o (None, motivo)."""
    if REGEX_PESO.fullmatch(numero):
        return "NUM", None
    if not numero.isdigit():
        return None, f"'{numero}' no es un peso válido: solo se permiten dígitos"
    if int(numero) == 0:
        return None, f"el peso '{numero}' no es válido: la latencia debe ser mayor que 0"
    return None, f"el peso '{numero}' no es válido: no puede tener ceros a la izquierda"


def analizar_lexico(texto):
    """
    Convierte el texto en una lista de tokens.

    Devuelve (tokens, errores). Al final de la lista de tokens se agrega un
    token especial FIN ('$') que marca el fin de la entrada (lo usa el parser).
    """
    tokens = []
    errores = []
    i = 0               # posición actual en el texto
    linea = 1           # línea actual (empieza en 1)
    inicio_linea = 0    # índice donde empezó la línea actual (para la columna)

    while i < len(texto):
        caracter = texto[i]
        columna = i - inicio_linea + 1

        # --- Saltos de línea: avanzamos el contador de líneas ---
        if caracter == "\n":
            linea += 1
            i += 1
            inicio_linea = i
            continue

        # --- Espacios y tabuladores: se ignoran ---
        if caracter in " \t\r":
            i += 1
            continue

        # --- Comentario: se reconoce con REGEX_COMENTARIO y se ignora ---
        coincidencia = REGEX_COMENTARIO.match(texto, i)
        if coincidencia:
            i = coincidencia.end()
            continue

        # --- Símbolos de puntuación ---
        if caracter in SIMBOLOS:
            tokens.append(Token(SIMBOLOS[caracter], caracter, linea, columna))
            i += 1
            continue

        # --- Palabras: reservadas o identificadores ---
        coincidencia = REGEX_PALABRA.match(texto, i)
        if coincidencia:
            palabra = coincidencia.group()
            tipo, motivo = _clasificar_palabra(palabra)
            if tipo:
                tokens.append(Token(tipo, palabra, linea, columna))
            else:
                errores.append(ErrorLexico(linea, columna, palabra, motivo))
            i = coincidencia.end()
            continue

        # --- Números: pesos (latencias) ---
        coincidencia = REGEX_NUMERO.match(texto, i)
        if coincidencia:
            numero = coincidencia.group()
            tipo, motivo = _clasificar_numero(numero)
            if tipo:
                tokens.append(Token(tipo, numero, linea, columna))
            else:
                errores.append(ErrorLexico(linea, columna, numero, motivo))
            i = coincidencia.end()
            continue

        # --- Cualquier otro carácter no pertenece al alfabeto del lenguaje ---
        errores.append(ErrorLexico(linea, columna, caracter,
                                   f"carácter no reconocido '{caracter}'"))
        i += 1

    tokens.append(Token("FIN", "$", linea, i - inicio_linea + 1))
    return tokens, errores


def solo_comentarios_o_vacio(texto):
    """True si el texto está vacío o solo tiene espacios y comentarios."""
    sin_comentarios = REGEX_COMENTARIO.sub("", texto)
    return sin_comentarios.strip() == ""
