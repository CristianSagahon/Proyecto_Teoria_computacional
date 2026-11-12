"""
parser.py - Analizador sintáctico por DESCENSO RECURSIVO + validación semántica.

CONCEPTO TEÓRICO
----------------
La estructura del archivo se describe con una GRAMÁTICA LIBRE DE CONTEXTO
G = (V, Σ, P, S):

    V (no terminales) = {S, L, E, P, T}
    Σ (terminales)    = {RED, ENLACE, ROUTER, SWITCH, PC, SERVER, DB, id, n, {, }, :, ;}
    S (símbolo inicial) = S
    P (producciones):
        S → RED { L }
        L → E L | E
        E → T id P ; | T id P { L } | ENLACE id id : n ;
        P → : n | ε
        T → ROUTER | SWITCH | PC | SERVER | DB

    L = lista de elementos, E = elemento (dispositivo o enlace),
    P = peso opcional, T = tipo de dispositivo.

DESCENSO RECURSIVO: se programa UNA FUNCIÓN POR CADA NO TERMINAL. Cada función
mira el token actual (lookahead) para decidir qué producción usar y llama a las
funciones de los no terminales que aparecen del lado derecho.
Cómo se decide la producción:
    L : después de leer E, si el siguiente token es '}' se usa L → E,
        si no, se usa L → E L.
    E : si el token es ENLACE se usa la tercera producción; si es un tipo de
        dispositivo, se lee "T id P" y luego ';' elige la primera o '{' la segunda.
    P : si el token es ':' se usa P → : n, si no P → ε.

Mientras reconoce la entrada, el parser construye el ÁRBOL DE DERIVACIÓN.
De ese árbol se obtiene la DERIVACIÓN MÁS A LA IZQUIERDA paso a paso.
"""

from lexer import TIPOS_DISPOSITIVO

PESO_POR_DEFECTO = 1


class ErrorSintactico(Exception):
    """Error de sintaxis con número de línea y motivo."""


class Nodo:
    """
    Nodo del árbol de derivación.
    - Si es NO TERMINAL: simbolo = 'S', 'L', ...; produccion = texto de la regla; hijos = lista.
    - Si es TERMINAL:    simbolo = lexema (ej. 'R1', '{'); hijos = None.
    """

    def __init__(self, simbolo, produccion=None, hijos=None, terminal=False):
        self.simbolo = simbolo
        self.produccion = produccion
        self.hijos = hijos if hijos is not None else []
        self.terminal = terminal


class ResultadoParser:
    """Lo que el parser obtiene del archivo: árbol, dispositivos y enlaces."""

    def __init__(self):
        self.arbol = None
        # Cada dispositivo: {'nombre', 'tipo', 'padre', 'peso', 'linea'}
        self.dispositivos = []
        # Cada enlace: {'origen', 'destino', 'peso', 'linea'}
        self.enlaces = []


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0
        self.resultado = ResultadoParser()

    # ----------------------------- utilidades -----------------------------
    def actual(self):
        """Token que estamos viendo (lookahead)."""
        return self.tokens[self.posicion]

    def anterior(self):
        """Último token consumido (sirve para decir 'después de X')."""
        if self.posicion == 0:
            return None
        return self.tokens[self.posicion - 1]

    def consumir(self, tipo_esperado, descripcion):
        """
        Si el token actual es del tipo esperado lo consume y devuelve un nodo
        terminal; si no, lanza un error sintáctico claro.
        """
        token = self.actual()
        if token.tipo == tipo_esperado:
            self.posicion += 1
            return Nodo(token.valor, terminal=True), token
        self.error(descripcion)

    def error(self, descripcion):
        token = self.actual()
        previo = self.anterior()
        encontrado = "el fin del archivo" if token.tipo == "FIN" else f"'{token.valor}'"
        if previo is not None:
            raise ErrorSintactico(
                f"Línea {previo.linea}: se esperaba {descripcion} después de "
                f"'{previo.valor}', pero se encontró {encontrado} (línea {token.linea})")
        raise ErrorSintactico(f"Línea {token.linea}: se esperaba {descripcion}, "
                              f"pero se encontró {encontrado}")

    # ---------------------- una función por no terminal ----------------------
    def parse_S(self):
        """S → RED { L }"""
        n_red, _ = self.consumir("RED", "la palabra RED al inicio del archivo")
        n_abre, _ = self.consumir("LLAVE_ABRE", "'{'")
        n_L = self.parse_L(padre=None)
        n_cierra, _ = self.consumir("LLAVE_CIERRA", "'}' para cerrar RED")
        if self.actual().tipo != "FIN":
            self.error("el fin del archivo (no debe haber nada después de cerrar RED)")
        return Nodo("S", "S → RED { L }", [n_red, n_abre, n_L, n_cierra])

    def parse_L(self, padre):
        """L → E L | E   (padre = dispositivo dueño del bloque, None si es RED)"""
        n_E = self.parse_E(padre)
        if self.actual().tipo == "LLAVE_CIERRA":
            return Nodo("L", "L → E", [n_E])
        n_L = self.parse_L(padre)
        return Nodo("L", "L → E L", [n_E, n_L])

    def parse_E(self, padre):
        """E → T id P ; | T id P { L } | ENLACE id id : n ;"""
        token = self.actual()

        if token.tipo == "ENLACE":
            n_enlace, t_enlace = self.consumir("ENLACE", "ENLACE")
            n_id1, t1 = self.consumir("ID", "el nombre del primer dispositivo")
            n_id2, t2 = self.consumir("ID", "el nombre del segundo dispositivo")
            n_dp, _ = self.consumir("DOS_PUNTOS", "':' antes del peso del enlace")
            n_num, t_num = self.consumir("NUM", "el peso (latencia) del enlace")
            n_pc, _ = self.consumir("PUNTO_Y_COMA", "';'")
            self.resultado.enlaces.append({"origen": t1.valor, "destino": t2.valor,
                                           "peso": int(t_num.valor), "linea": t_enlace.linea})
            return Nodo("E", "E → ENLACE id id : n ;",
                        [n_enlace, n_id1, n_id2, n_dp, n_num, n_pc])

        if token.tipo in TIPOS_DISPOSITIVO:
            n_T = self.parse_T()
            n_id, t_id = self.consumir("ID", f"el nombre del dispositivo después de {token.valor}")
            n_P, peso = self.parse_P()
            self.resultado.dispositivos.append({"nombre": t_id.valor, "tipo": token.valor,
                                                "padre": padre, "peso": peso,
                                                "linea": t_id.linea})
            if self.actual().tipo == "PUNTO_Y_COMA":
                n_pc, _ = self.consumir("PUNTO_Y_COMA", "';'")
                return Nodo("E", "E → T id P ;", [n_T, n_id, n_P, n_pc])
            if self.actual().tipo == "LLAVE_ABRE":
                n_abre, _ = self.consumir("LLAVE_ABRE", "'{'")
                n_L = self.parse_L(padre=t_id.valor)
                n_cierra, _ = self.consumir("LLAVE_CIERRA", f"'}}' para cerrar {t_id.valor}")
                return Nodo("E", "E → T id P { L }", [n_T, n_id, n_P, n_abre, n_L, n_cierra])
            # Ni ';' ni '{': el error se reporta mencionando al dispositivo.
            siguiente = self.actual()
            encontrado = "el fin del archivo" if siguiente.tipo == "FIN" else f"'{siguiente.valor}'"
            raise ErrorSintactico(
                f"Línea {self.anterior().linea}: se esperaba ';' después de {t_id.valor} "
                f"(o '{{' para abrir su bloque), pero se encontró {encontrado}")

        self.error("un dispositivo (ROUTER, SWITCH, PC, SERVER, DB) o ENLACE")

    def parse_P(self):
        """P → : n | ε    Devuelve (nodo, peso o None)."""
        if self.actual().tipo == "DOS_PUNTOS":
            n_dp, _ = self.consumir("DOS_PUNTOS", "':'")
            n_num, t_num = self.consumir("NUM", "el peso (latencia) después de ':'")
            return Nodo("P", "P → : n", [n_dp, n_num]), int(t_num.valor)
        return Nodo("P", "P → ε", []), None

    def parse_T(self):
        """T → ROUTER | SWITCH | PC | SERVER | DB"""
        token = self.actual()
        n_tipo, _ = self.consumir(token.tipo, "un tipo de dispositivo")
        return Nodo("T", f"T → {token.valor}", [n_tipo])


def analizar_sintaxis(tokens):
    """Ejecuta el parser. Devuelve ResultadoParser o lanza ErrorSintactico."""
    parser = Parser(tokens)
    parser.resultado.arbol = parser.parse_S()
    return parser.resultado


# ---------------------------------------------------------------------------
# DERIVACIÓN MÁS A LA IZQUIERDA
# ---------------------------------------------------------------------------
def derivacion_izquierda(arbol):
    """
    Recorre el árbol y genera la derivación más a la izquierda: en cada paso se
    reemplaza el NO TERMINAL que está más a la izquierda por el lado derecho de
    la producción que se usó al reconocerlo.
    Devuelve una lista de (forma_sentencial, produccion_aplicada).
    """
    forma = [arbol]                 # forma sentencial actual (lista de nodos)
    pasos = [(_forma_a_texto(forma), None)]
    while True:
        # Buscar el no terminal más a la izquierda
        indice = next((i for i, n in enumerate(forma) if not n.terminal), None)
        if indice is None:
            break
        nodo = forma[indice]
        forma = forma[:indice] + nodo.hijos + forma[indice + 1:]
        pasos.append((_forma_a_texto(forma), nodo.produccion))
    return pasos


def _forma_a_texto(forma):
    texto = " ".join(n.simbolo for n in forma)
    return texto if texto else "ε"


# ---------------------------------------------------------------------------
# VALIDACIÓN SEMÁNTICA
# ---------------------------------------------------------------------------
def validar_semantica(resultado):
    """
    Revisa reglas que la gramática no puede expresar (dependen del contexto):
      - nombres de dispositivo repetidos
      - ENLACE hacia un nodo no declarado
      - ENLACE de un nodo a sí mismo
      - conexión repetida entre los mismos dos nodos
    Devuelve (errores, advertencias).
    """
    errores = []
    advertencias = []
    declarados = {}

    for d in resultado.dispositivos:
        if d["nombre"] in declarados:
            errores.append(f"Línea {d['linea']}: el nombre '{d['nombre']}' está repetido "
                           f"(ya se declaró en la línea {declarados[d['nombre']]})")
        else:
            declarados[d["nombre"]] = d["linea"]
        if d["padre"] is None and d["peso"] is not None:
            advertencias.append(f"Línea {d['linea']}: {d['nombre']} está directamente en RED, "
                                f"su peso {d['peso']} se ignora (RED no es un dispositivo)")
        if d["padre"] is not None and d["peso"] is None:
            advertencias.append(f"Línea {d['linea']}: {d['nombre']} no tiene peso, se usa "
                                f"{PESO_POR_DEFECTO} ms para la conexión con {d['padre']}")

    # Conexiones jerárquicas ya existentes (para detectar ENLACE repetido)
    conexiones = set()
    for d in resultado.dispositivos:
        if d["padre"] is not None:
            conexiones.add(frozenset((d["nombre"], d["padre"])))

    for e in resultado.enlaces:
        a, b = e["origen"], e["destino"]
        hay_error = False
        for nombre in (a, b):
            if nombre not in declarados:
                errores.append(f"Línea {e['linea']}: ENLACE {a} {b} usa '{nombre}', "
                               f"que no está declarado en la red")
                hay_error = True
        if a == b:
            errores.append(f"Línea {e['linea']}: ENLACE {a} {b} conecta un nodo consigo mismo")
            hay_error = True
        if hay_error:
            continue
        par = frozenset((a, b))
        if par in conexiones:
            errores.append(f"Línea {e['linea']}: ya existe una conexión entre {a} y {b}")
        conexiones.add(par)

    return errores, advertencias
