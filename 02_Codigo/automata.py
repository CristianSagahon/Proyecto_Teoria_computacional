"""
automata.py - AFN del estado de un dispositivo, conversión por subconjuntos
a AFD, simulación con traza y procesamiento del archivo de pings.

CONCEPTO TEÓRICO
----------------
Cada dispositivo tiene una cadena con el historial de sus pings:
    o = OK,  t = TIMEOUT        Alfabeto Σ = {o, t}
Un dispositivo está en FALLA si sus DOS ÚLTIMOS pings fueron TIMEOUT, o sea,
si su cadena pertenece al lenguaje regular  L = (o|t)* t t.

AFN  N = (Q, Σ, δ, q0, F)
    Q = {q0, q1, q2}, q0 inicial, F = {q2}
    δ(q0, o) = {q0}
    δ(q0, t) = {q0, q1}     <- no determinismo: "adivina" que este t es el penúltimo
    δ(q1, t) = {q2}
    q2 no tiene transiciones (si llega otro símbolo, esa rama muere)

CONSTRUCCIÓN POR SUBCONJUNTOS: cada estado del AFD es un CONJUNTO de estados
del AFN. Se parte de {q0} y, para cada conjunto y cada símbolo, se calcula la
unión de las transiciones de sus estados. Se repite hasta que no aparezcan
conjuntos nuevos. Un conjunto es final si contiene algún estado final del AFN.
(Este AFN no tiene transiciones ε, por eso no se necesita cerradura-ε.)

AFD resultante:
    A = {q0}          inicial    o -> A, t -> B
    B = {q0,q1}                  o -> A, t -> C
    C = {q0,q1,q2}    final      o -> A, t -> C
"""

from itertools import product

from lexer import REGEX_LINEA_PING, REGEX_COMENTARIO

# ---------------------------------------------------------------------------
# AFN representado como diccionario
# transiciones[estado][simbolo] = conjunto de estados destino
# ---------------------------------------------------------------------------
AFN_ESTADO = {
    "estados": ["q0", "q1", "q2"],
    "alfabeto": ["o", "t"],
    "transiciones": {
        "q0": {"o": {"q0"}, "t": {"q0", "q1"}},
        "q1": {"t": {"q2"}},
        "q2": {},
    },
    "inicial": "q0",
    "finales": {"q2"},
}

# Traducción de los resultados del archivo de pings a símbolos del alfabeto.
SIMBOLO_DE_PING = {"OK": "o", "TIMEOUT": "t"}


def conjunto_a_texto(conjunto):
    """{q1, q0} -> '{q0,q1}' (ordenado para que siempre se vea igual)."""
    if not conjunto:
        return "∅"
    return "{" + ",".join(sorted(conjunto)) + "}"


# ---------------------------------------------------------------------------
# CONSTRUCCIÓN POR SUBCONJUNTOS (genérica: sirve para cualquier AFN sin ε)
# ---------------------------------------------------------------------------
def construir_afd(afn):
    """
    Convierte un AFN (diccionario) en un AFD.
    Devuelve (afd, pasos) donde 'pasos' es la lista de textos que explican
    cada cálculo, para imprimir el procedimiento.
    """
    alfabeto = afn["alfabeto"]
    inicial = frozenset([afn["inicial"]])

    nombres = {}               # frozenset -> nombre (A, B, C, ...)
    pendientes = [inicial]     # conjuntos por procesar (cola)
    transiciones = {}          # nombre -> {simbolo: nombre}
    pasos = []

    def nombre_de(conjunto):
        """Asigna una letra nueva a cada conjunto en el orden en que aparece."""
        if conjunto not in nombres:
            nombres[conjunto] = chr(ord("A") + len(nombres))
        return nombres[conjunto]

    nombre_de(inicial)
    pasos.append(f"Estado inicial del AFD: {nombres[inicial]} = {conjunto_a_texto(inicial)}")

    while pendientes:
        actual = pendientes.pop(0)
        nombre_actual = nombres[actual]
        transiciones[nombre_actual] = {}
        pasos.append(f"\nProcesando {nombre_actual} = {conjunto_a_texto(actual)}:")

        for simbolo in alfabeto:
            # Unión de δ(q, simbolo) para cada q del conjunto actual
            destino = set()
            partes = []
            for q in sorted(actual):
                alcanzados = afn["transiciones"].get(q, {}).get(simbolo, set())
                partes.append(f"δ({q},{simbolo})={conjunto_a_texto(alcanzados)}")
                destino |= alcanzados
            destino = frozenset(destino)

            es_nuevo = destino not in nombres
            nombre_destino = nombre_de(destino)
            if es_nuevo:
                pendientes.append(destino)
            transiciones[nombre_actual][simbolo] = nombre_destino

            nota = "  <- conjunto NUEVO" if es_nuevo else ""
            pasos.append(f"  δ'({nombre_actual}, {simbolo}) = " + " ∪ ".join(partes)
                         + f" = {conjunto_a_texto(destino)} = {nombre_destino}{nota}")

    # Un estado del AFD es final si contiene algún estado final del AFN.
    finales = {nombre for conjunto, nombre in nombres.items() if conjunto & afn["finales"]}
    pasos.append("\nEstados finales del AFD (contienen q2): "
                 + ", ".join(sorted(finales)))

    afd = {
        "estados": [nombres[c] for c in nombres],
        "conjuntos": {nombre: conjunto for conjunto, nombre in nombres.items()},
        "alfabeto": alfabeto,
        "transiciones": transiciones,
        "inicial": nombres[inicial],
        "finales": finales,
    }
    return afd, pasos


# AFD calculado una sola vez al importar el módulo.
AFD_ESTADO, PASOS_SUBCONJUNTOS = construir_afd(AFN_ESTADO)


# ---------------------------------------------------------------------------
# SIMULACIONES CON TRAZA
# ---------------------------------------------------------------------------
def simular_afn(afn, cadena):
    """
    Simula el AFN siguiendo TODOS los caminos a la vez: se mantiene el conjunto
    de estados activos. Acepta si al final algún estado activo es final.
    Devuelve (aceptada, traza).
    """
    activos = {afn["inicial"]}
    traza = [f"inicio: {conjunto_a_texto(activos)}"]
    for simbolo in cadena:
        nuevos = set()
        for q in activos:
            nuevos |= afn["transiciones"].get(q, {}).get(simbolo, set())
        traza.append(f"lee '{simbolo}': {conjunto_a_texto(activos)} -> {conjunto_a_texto(nuevos)}")
        activos = nuevos
    aceptada = bool(activos & afn["finales"])
    return aceptada, traza


def simular_afd(afd, cadena):
    """
    Simula el AFD: un solo estado actual, una transición por símbolo.
    Devuelve (aceptada, traza) con el recorrido 'A -o-> A -t-> B ...'.
    """
    estado = afd["inicial"]
    recorrido = estado
    for simbolo in cadena:
        if simbolo not in afd["alfabeto"]:
            raise ValueError(f"el símbolo '{simbolo}' no pertenece al alfabeto {{o, t}}")
        estado = afd["transiciones"][estado][simbolo]
        recorrido += f" -{simbolo}-> {estado}"
    return estado in afd["finales"], recorrido


def verificar_equivalencia(afn, afd, longitud_maxima=8):
    """
    Comprueba que AFN y AFD aceptan exactamente las mismas cadenas probando
    TODAS las cadenas de Σ* con longitud 0..longitud_maxima.
    Devuelve (son_equivalentes, cantidad_probada, contraejemplo_o_None).
    """
    probadas = 0
    for n in range(longitud_maxima + 1):
        for letras in product(afn["alfabeto"], repeat=n):
            cadena = "".join(letras)
            probadas += 1
            if simular_afn(afn, cadena)[0] != simular_afd(afd, cadena)[0]:
                return False, probadas, cadena
    return True, probadas, None


def estado_dispositivo(cadena):
    """Falla si el AFD acepta la cadena; Activo si la rechaza."""
    aceptada, _ = simular_afd(AFD_ESTADO, cadena)
    return "Falla" if aceptada else "Activo"


# ---------------------------------------------------------------------------
# PROCESAMIENTO DEL ARCHIVO DE PINGS
# ---------------------------------------------------------------------------
def procesar_pings(texto, nodos_red=None):
    """
    Lee el texto de pings.txt. Cada línea se valida con REGEX_LINEA_PING;
    las líneas inválidas se rechazan (con su número) y el resto se procesa.
    Devuelve un diccionario con:
        'historial'   : {dispositivo: "ootot..."}
        'resultados'  : {dispositivo: (estado, aceptada, recorrido_afd)}
        'rechazadas'  : [mensajes de líneas inválidas]
        'advertencias': [mensajes]
    """
    historial = {}
    rechazadas = []
    advertencias = []

    for numero, linea in enumerate(texto.splitlines(), start=1):
        limpia = REGEX_COMENTARIO.sub("", linea).strip()
        if not limpia:
            continue  # línea vacía o solo comentario
        coincidencia = REGEX_LINEA_PING.match(limpia)
        if not coincidencia:
            rechazadas.append(f"Línea {numero}: '{limpia}' no cumple el formato "
                              f"'NOMBRE OK|TIMEOUT', se ignora")
            continue
        nombre, resultado = coincidencia.group(1), coincidencia.group(2)
        historial.setdefault(nombre, "")
        historial[nombre] += SIMBOLO_DE_PING[resultado]

    if nodos_red is not None:
        for nombre in historial:
            if nombre not in nodos_red:
                advertencias.append(f"{nombre} tiene pings pero no existe en la red")

    resultados = {}
    for nombre, cadena in historial.items():
        aceptada, recorrido = simular_afd(AFD_ESTADO, cadena)
        resultados[nombre] = ("Falla" if aceptada else "Activo", aceptada, recorrido)

    return {"historial": historial, "resultados": resultados,
            "rechazadas": rechazadas, "advertencias": advertencias}


# ---------------------------------------------------------------------------
# IMPRESIÓN
# ---------------------------------------------------------------------------
def imprimir_afn(afn):
    print("AFN  N = (Q, Σ, δ, q0, F)")
    print(f"  Q  = {{{', '.join(afn['estados'])}}}")
    print(f"  Σ  = {{{', '.join(afn['alfabeto'])}}}   (o = OK, t = TIMEOUT)")
    print(f"  q0 = {afn['inicial']}")
    print(f"  F  = {conjunto_a_texto(afn['finales'])}")
    print("  Transiciones:")
    for q in afn["estados"]:
        movimientos = afn["transiciones"].get(q, {})
        if not movimientos:
            print(f"    {q}: sin transiciones")
        for simbolo, destinos in movimientos.items():
            print(f"    δ({q}, {simbolo}) = {conjunto_a_texto(destinos)}")


def imprimir_tabla_afd(afd):
    print(f"{'':3}{'Estado':<8}{'Conjunto AFN':<15}" +
          "".join(f"{s:<6}" for s in afd["alfabeto"]))
    for nombre in afd["estados"]:
        marca = ("->" if nombre == afd["inicial"] else "  ") + ("*" if nombre in afd["finales"] else " ")
        conjunto = conjunto_a_texto(afd["conjuntos"][nombre])
        fila = "".join(f"{afd['transiciones'][nombre][s]:<6}" for s in afd["alfabeto"])
        print(f"{marca}{nombre:<8}{conjunto:<15}{fila}")
    print("  (-> estado inicial, * estado final)")
