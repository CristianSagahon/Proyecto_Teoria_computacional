"""
automata_pila.py - Autómata de pila (AP) que valida el balanceo de llaves.

CONCEPTO TEÓRICO
----------------
Las llaves anidadas { { } } forman un lenguaje del tipo  a^n b^n  (n llaves que
abren seguidas de n que cierran). Ese lenguaje NO es regular: por el lema de
bombeo, un autómata finito no puede "contar" cuántas llaves faltan por cerrar
porque tiene memoria finita. Un AUTÓMATA DE PILA sí puede, porque guarda un
símbolo B en la pila por cada '{' y lo saca con cada '}'.

Definición formal  M = (Q, Σ, Γ, δ, q0, Z0, F)
    Q  = {q0, qf}
    Σ  = tokens del archivo ({, }, y "otros" símbolos: RED, ROUTER, id, n, :, ;)
    Γ  = {B, Z0}          (B = bloque abierto, Z0 = fondo de la pila)
    q0 = estado inicial,  Z0 = símbolo inicial de pila,  F = {qf}

Transiciones (formato  δ(estado, entrada, tope) = (nuevo_estado, lo_que_se_apila)):
    δ(q0, {, Z0) = (q0, B Z0)     push B
    δ(q0, {, B)  = (q0, B B)      push B
    δ(q0, }, B)  = (q0, ε)        pop B
    δ(q0, a, X)  = (q0, X)        cualquier otro símbolo a: la pila no cambia
    δ(q0, ε, Z0) = (qf, Z0)       al terminar la entrada con Z0 en el tope: aceptar

Rechazo:
    - Llega '}' y el tope es Z0  -> no hay bloque abierto que cerrar.
    - Termina la entrada y quedan B en la pila -> bloques sin cerrar.
"""


class ResultadoPila:
    """Guarda si se aceptó, la traza paso a paso y los errores."""

    def __init__(self):
        self.aceptada = False
        self.traza = []      # lista de (paso, simbolo, transicion, pila)
        self.errores = []


def _pila_a_texto(pila):
    """Muestra la pila con el TOPE A LA IZQUIERDA (ej. 'B B Z0')."""
    return " ".join(reversed(pila))


def ejecutar_automata_pila(tokens):
    """
    Simula el autómata de pila sobre la lista de tokens del lexer.
    La pila se guarda como lista de Python: el final de la lista es el tope.
    """
    resultado = ResultadoPila()
    estado = "q0"
    pila = ["Z0"]
    # En paralelo a cada B guardamos qué token abrió el bloque (para reportar la línea).
    aperturas = []
    paso = 0

    resultado.traza.append((paso, "-", "configuración inicial (q0, Z0)", _pila_a_texto(pila)))

    for i, token in enumerate(tokens):
        if token.tipo == "FIN":
            break
        paso += 1
        tope = pila[-1]
        simbolo = token.valor

        if token.tipo == "LLAVE_ABRE":
            # PUSH: δ(q0, {, tope) = (q0, B tope)
            pila.append("B")
            # Nombre del bloque = token anterior que no sea ':' ni número (ej. RED, R1, SW1)
            propietario = _nombre_del_bloque(tokens, i)
            aperturas.append((token, propietario))
            transicion = f"δ(q0, {{, {tope}) = (q0, B{tope})   push B"
        elif token.tipo == "LLAVE_CIERRA":
            if tope == "Z0":
                # No hay transición definida: el autómata se bloquea y rechaza.
                resultado.traza.append((paso, simbolo, "δ(q0, }, Z0) no está definida -> RECHAZO",
                                        _pila_a_texto(pila)))
                resultado.errores.append(
                    f"Línea {token.linea}: se encontró '}}' sin un bloque abierto que cerrar "
                    f"(la pila ya estaba en Z0, sobra una llave de cierre)")
                return resultado
            # POP: δ(q0, }, B) = (q0, ε)
            pila.pop()
            aperturas.pop()
            transicion = "δ(q0, }, B) = (q0, ε)   pop B"
        else:
            # Cualquier otro símbolo: la pila no cambia.
            transicion = f"δ(q0, {simbolo}, {tope}) = (q0, {tope})   sin cambio"

        resultado.traza.append((paso, simbolo, transicion, _pila_a_texto(pila)))

    # Fin de la entrada: transición ε hacia el estado final si el tope es Z0.
    paso += 1
    if pila[-1] == "Z0":
        estado = "qf"
        resultado.traza.append((paso, "ε", "δ(q0, ε, Z0) = (qf, Z0)   ACEPTA", _pila_a_texto(pila)))
        resultado.aceptada = True
    else:
        resultado.traza.append((paso, "ε", "fin de entrada con B en el tope -> RECHAZO",
                                _pila_a_texto(pila)))
        # Reportamos cada bloque que quedó abierto, del más interno al más externo.
        for token, propietario in reversed(aperturas):
            resultado.errores.append(
                f"Línea {token.linea}: el bloque '{{' de {propietario} se abrió y nunca se cerró "
                f"(falta '}}')")
    resultado.estado_final = estado
    return resultado


def _nombre_del_bloque(tokens, indice_llave):
    """Busca hacia atrás el nombre del dispositivo (o RED) propietario de la llave."""
    j = indice_llave - 1
    while j >= 0:
        if tokens[j].tipo in ("ID", "RED"):
            return tokens[j].valor
        if tokens[j].tipo in ("PUNTO_Y_COMA", "LLAVE_ABRE", "LLAVE_CIERRA"):
            break
        j -= 1
    return "(sin nombre)"


def imprimir_traza(resultado):
    """Imprime la traza en forma de tabla: paso | símbolo | transición | pila."""
    print(f"{'Paso':>4} | {'Símbolo':<8} | {'Transición aplicada':<45} | Pila (tope a la izq.)")
    print("-" * 95)
    for paso, simbolo, transicion, pila in resultado.traza:
        print(f"{paso:>4} | {simbolo:<8} | {transicion:<45} | {pila}")
