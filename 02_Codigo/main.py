"""
main.py - Menú CLI del Analizador de redes mediante grafos (Proyecto 4).

Flujo de análisis de un archivo de red (cada fase usa un modelo teórico):
    texto --(regex / lexer)--> tokens
          --(autómata de pila)--> llaves balanceadas
          --(gramática libre de contexto / parser)--> árbol de derivación
          --(validación semántica)--> red correcta
          --> grafo no dirigido ponderado
Los pings se procesan con el AFD (obtenido del AFN por subconjuntos) y los
dispositivos en Falla se quitan del grafo para recalcular la conectividad.

La presentación (colores, cuadros, tablas) está en consola.py.

Uso:
    python main.py
    python main.py ejemplos/red_ejemplo.txt
    python main.py ejemplos/red_ejemplo.txt ejemplos/pings_ejemplo.txt
"""

import os
import sys

from lexer import analizar_lexico, solo_comentarios_o_vacio
from automata_pila import ejecutar_automata_pila
from parser import analizar_sintaxis, ErrorSintactico, validar_semantica, derivacion_izquierda
from grafo import construir_grafo
import automata
from consola import (titulo, subtitulo, explicacion, exito, error, aviso, dato, preguntar,
                     pausa, tabla, negrita, gris, rojo, verde, amarillo, cian, morado, ANCHO)

# Carpeta del programa (también funciona dentro de un .exe de PyInstaller)
if getattr(sys, "frozen", False):
    CARPETA_BASE = os.path.dirname(sys.executable)
else:
    CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))

RED_POR_DEFECTO = os.path.join("ejemplos", "red_ejemplo.txt")
PINGS_POR_DEFECTO = os.path.join("ejemplos", "pings_ejemplo.txt")


class Cancelado(Exception):
    """El usuario dejó un dato vacío para regresar al menú."""


# ---------------------------------------------------------------------------
# PROCESAMIENTO DE LA RED (todas las fases)
# ---------------------------------------------------------------------------
class ResultadoCarga:
    """Resultado de analizar un archivo de red, fase por fase."""

    def __init__(self):
        self.aceptada = False
        self.fase_error = None     # 'archivo', 'léxico', 'pila', 'sintáctico', 'semántico'
        self.errores = []
        self.advertencias = []
        self.tokens = []
        self.pila = None
        self.parser = None
        self.grafo = None


def procesar_red(texto):
    """Ejecuta las fases en orden. Se detiene en la primera fase con errores."""
    r = ResultadoCarga()

    # Fase 0: archivo vacío
    if solo_comentarios_o_vacio(texto):
        r.fase_error = "archivo"
        r.errores = ["El archivo está vacío: no contiene ninguna definición de red "
                     "(se esperaba 'RED { ... }')"]
        return r

    # Fase 1: análisis léxico (expresiones regulares)
    r.tokens, errores_lexicos = analizar_lexico(texto)
    if errores_lexicos:
        r.fase_error = "léxico"
        r.errores = [str(e) for e in errores_lexicos]
        return r

    # Fase 2: autómata de pila (balanceo de llaves)
    r.pila = ejecutar_automata_pila(r.tokens)
    if not r.pila.aceptada:
        r.fase_error = "pila"
        r.errores = r.pila.errores
        return r

    # Fase 3: análisis sintáctico (gramática libre de contexto)
    try:
        r.parser = analizar_sintaxis(r.tokens)
    except ErrorSintactico as e:
        r.fase_error = "sintáctico"
        r.errores = [str(e)]
        return r

    # Fase 4: validación semántica
    errores, r.advertencias = validar_semantica(r.parser)
    if errores:
        r.fase_error = "semántico"
        r.errores = errores
        return r

    # Fase 5: construcción del grafo
    r.grafo = construir_grafo(r.parser)
    r.aceptada = True
    return r


def simular_fallas(grafo, en_falla):
    """Quita los nodos en Falla y recalcula la conectividad."""
    reducido = grafo.copia_sin(set(en_falla))
    componentes = reducido.componentes_conexos()
    antes = len(grafo.componentes_conexos())
    return {
        "grafo": reducido,
        "antes": antes,
        "componentes": componentes,
        "dividida": len(componentes) > antes,
        "sin_conexion": reducido.aislados(),
    }


# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------
def leer_archivo(ruta):
    """Lee un archivo de texto. Busca la ruta tal cual o relativa al programa."""
    candidatos = [ruta, os.path.join(CARPETA_BASE, ruta)]
    for candidato in candidatos:
        if os.path.isfile(candidato):
            with open(candidato, "r", encoding="utf-8") as f:
                return f.read(), candidato
    raise FileNotFoundError(f"No se encontró el archivo '{ruta}'. Revisa que la ruta "
                            f"esté bien escrita (ej. ejemplos/red_ejemplo.txt)")


class Estado:
    """Lo que el programa recuerda entre opciones del menú."""

    def __init__(self):
        self.carga = None          # ResultadoCarga de la red
        self.ruta_red = None
        self.pings = None          # resultado de automata.procesar_pings
        self.estados = {}          # {dispositivo: 'Falla'/'Activo'}

    def hay_red(self):
        return self.carga is not None and self.carga.aceptada


def pedir_nodo(estado, pregunta, ejemplo):
    """
    Pide el nombre de un equipo. Acepta mayúsculas o minúsculas (pc1 = PC1),
    vuelve a preguntar si no existe y regresa al menú si se deja vacío.
    """
    nodos = estado.carga.grafo.nodos()
    por_mayusculas = {n.upper(): n for n in nodos}
    while True:
        respuesta = preguntar(pregunta, ejemplo=ejemplo, por_defecto="",
                              texto_enter="regresar al menú")
        if not respuesta:
            raise Cancelado()
        if respuesta.upper() in por_mayusculas:
            return por_mayusculas[respuesta.upper()]
        error(f"'{respuesta}' no existe en la red.")
        print(gris("     Equipos disponibles: ") + ", ".join(nodos))


def mostrar_equipos(estado):
    print(gris("  Equipos de la red: ") + cian(", ".join(estado.carga.grafo.nodos())))


def ruta_bonita(ruta):
    return gris(" → ").join(negrita(n) for n in ruta)


# ---------------------------------------------------------------------------
# OPCIONES DEL MENÚ
# ---------------------------------------------------------------------------
def opcion_cargar_red(estado, ruta=None):
    titulo("1. CARGAR RED DESDE ARCHIVO", "📂")
    explicacion("Lee el archivo y lo revisa con: regex (lexer) → autómata de pila → "
                "gramática (parser) → semántica.")
    if ruta is None:
        ruta = preguntar("Archivo de red", ejemplo="ejemplos/invalido_peso.txt",
                         por_defecto=RED_POR_DEFECTO)
    texto, ruta_real = leer_archivo(ruta)
    dato("Archivo", ruta_real)
    carga = procesar_red(texto)

    if carga.tokens:
        subtitulo(f"Fase 1 · Análisis léxico: {len(carga.tokens) - 1} tokens")
        tabla(["Lín:Col", "Tipo", "Lexema"],
              [(f"{t.linea}:{t.columna}", t.tipo, t.valor) for t in carga.tokens])
    if carga.pila is not None:
        subtitulo("Fase 2 · Autómata de pila (pila con el tope a la izquierda)")
        filas = []
        for paso, simbolo, transicion, pila in carga.pila.traza:
            color = verde if "ACEPTA" in transicion else rojo if "RECHAZO" in transicion else str
            filas.append((paso, simbolo, (transicion, color), pila))
        tabla(["Paso", "Símbolo", "Transición aplicada", "Pila"], filas)
        if carga.pila.aceptada:
            exito("Llaves balanceadas: el autómata de pila ACEPTA")
    if carga.parser is not None:
        subtitulo("Fase 3 · Parser (gramática libre de contexto)")
        exito(f"Sintaxis correcta: {len(carga.parser.dispositivos)} dispositivos y "
              f"{len(carga.parser.enlaces)} ENLACE")

    for a in carga.advertencias:
        aviso(a)

    print()
    if carga.aceptada:
        g = carga.grafo
        print("  " + verde(negrita(f"✔ RED ACEPTADA: {len(g.nodos())} nodos y "
                                  f"{len(g.aristas())} aristas")))
        estado.carga = carga
        estado.ruta_red = ruta_real
        estado.pings = None
        estado.estados = {}
    else:
        nombres_fase = {"archivo": "de archivo", "léxico": "léxico",
                        "pila": "del autómata de pila (llaves)",
                        "sintáctico": "sintáctico", "semántico": "semántico"}
        print("  " + rojo(negrita(f"✖ RED RECHAZADA - error {nombres_fase[carga.fase_error]}:")))
        for e in carga.errores:
            print("     " + rojo("• ") + e)
        if estado.hay_red():
            aviso("Se conserva la red que estaba cargada antes.")


def opcion_mostrar_grafo(estado):
    titulo("2. EQUIPOS, CONEXIONES Y LISTA DE ADYACENCIA", "🌐")
    explicacion("V = vértices (equipos), E = aristas (conexiones con su latencia en ms).")
    g = estado.carga.grafo
    dato(f"V  (|V| = {len(g.nodos())})", "{" + ", ".join(g.nodos()) + "}")
    aristas = [f"({a},{b},{p})" for a, b, p in g.aristas()]
    dato(f"E  (|E| = {len(aristas)})", "{" + ", ".join(aristas) + "}")
    subtitulo("Lista de adyacencia")
    filas = [(nodo, ", ".join(f"{v} ({p} ms)" for v, p in vecinos.items()) or "(sin vecinos)")
             for nodo, vecinos in g.adyacencia.items()]
    tabla(["Equipo", "Conectado con"], filas)


def opcion_bfs(estado):
    titulo("3. ¿HAY CAMINO ENTRE DOS EQUIPOS? (BFS)", "🔎")
    explicacion("BFS recorre la red por niveles con una cola hasta encontrar el destino.")
    explicacion("Deja vacío y da Enter para regresar al menú.")
    mostrar_equipos(estado)
    a = pedir_nodo(estado, "Equipo de ORIGEN", "PC1")
    b = pedir_nodo(estado, "Equipo de DESTINO", "DB1")
    existe, orden, ruta = estado.carga.grafo.bfs(a, b)
    print()
    dato("Orden de visita BFS", gris(" → ").join(orden))
    if existe:
        exito(f"SÍ hay camino entre {a} y {b}  ({len(ruta) - 1} saltos)")
        print("     " + ruta_bonita(ruta))
    else:
        error(f"NO hay camino entre {a} y {b}.")


def opcion_dijkstra(estado):
    titulo("4. CAMINO MÁS RÁPIDO (DIJKSTRA)", "⚡")
    explicacion("Dijkstra encuentra la ruta con la MENOR latencia total (suma de ms).")
    explicacion("Deja vacío y da Enter para regresar al menú.")
    mostrar_equipos(estado)
    a = pedir_nodo(estado, "Equipo de ORIGEN", "PC1")
    b = pedir_nodo(estado, "Equipo de DESTINO", "SRV1")
    g = estado.carga.grafo
    distancia, ruta, pasos = g.dijkstra(a, b)
    subtitulo("Pasos del algoritmo")
    tabla(["#", "Qué hizo"], [(i, p) for i, p in enumerate(pasos, 1)])
    print()
    if distancia is None:
        error(f"No hay camino entre {a} y {b}.")
        return
    exito(f"Ruta más corta: {distancia} ms")
    print("     " + ruta_bonita(ruta))
    alternativas = g.rutas_alternativas(a, b)
    if len(alternativas) > 1:
        subtitulo("Todas las rutas posibles (DFS), de la más rápida a la más lenta")
        tabla(["Ruta", "Latencia"],
              [((" → ".join(r), verde if i == 0 else str), f"{p} ms")
               for i, (r, p) in enumerate(alternativas)])


def opcion_grados(estado):
    titulo("5. GRADOS Y EQUIPOS AISLADOS", "🔢")
    explicacion("Grado = cuántas conexiones tiene un equipo. Grado 0 = aislado.")
    g = estado.carga.grafo
    grados = g.grados()
    maximo = max(grados.values()) if grados else 0
    # La barra se arma como texto plano (tupla texto, color) para que la tabla
    # calcule bien el ancho de cada columna.
    tabla(["Equipo", "Grado", "Gráfica"],
          [(n, d, ("■" * d, cian) if d else ("aislado", rojo)) for n, d in grados.items()])
    dato("Suma de grados", f"{sum(grados.values())} = 2·|E| = 2·{len(g.aristas())}  "
                           f"(lema del apretón de manos)")
    dato("Mayor grado", f"{maximo}  ({', '.join(n for n, d in grados.items() if d == maximo)})")
    aislados = g.aislados()
    if aislados:
        aviso("Equipos aislados: " + ", ".join(aislados))
    else:
        exito("No hay equipos aislados")


def opcion_ciclos(estado):
    titulo("6. CICLOS Y PUNTOS CRÍTICOS", "🔁")
    explicacion("Ciclo = camino que regresa al inicio (hay rutas de respaldo).")
    explicacion("Punto crítico = equipo que si se cae, divide la red.")
    g = estado.carga.grafo
    if g.tiene_ciclo():
        ciclos = g.encontrar_ciclos()
        exito(f"SÍ hay ciclos (DFS encontró una arista de retroceso): {len(ciclos)}")
        for c in ciclos:
            print("     " + gris(" - ").join(negrita(n) for n in c))
    else:
        aviso("NO hay ciclos: la red es un árbol, no hay rutas de respaldo.")

    subtitulo(f"¿Qué pasa si quito cada equipo?  (componentes ahora: "
              f"{len(g.componentes_conexos())})")
    criticos, detalle = g.puntos_criticos()
    filas = []
    for nodo, comps in detalle.items():
        grupos = "  |  ".join("{" + ", ".join(c) + "}" for c in comps)
        if nodo in criticos:
            filas.append(((nodo, rojo), (len(comps), rojo), (grupos, rojo), ("CRÍTICO", rojo)))
        else:
            filas.append((nodo, len(comps), grupos, ("ok", verde)))
    tabla(["Sin", "Componentes", "Grupos que quedan", "¿Crítico?"], filas)
    if criticos:
        print()
        error("Puntos críticos: " + ", ".join(criticos))
    else:
        exito("No hay puntos críticos")


def opcion_pings(estado, ruta=None):
    titulo("7. PROCESAR PINGS (¿QUIÉN ESTÁ EN FALLA?)", "📡")
    explicacion("Cada ping se convierte en o (OK) o t (TIMEOUT) y la cadena entra al AFD.")
    explicacion("Si los 2 últimos pings son TIMEOUT, el AFD acepta → el equipo está en FALLA.")
    if ruta is None:
        ruta = preguntar("Archivo de pings", ejemplo="ejemplos/pings_invalido.txt",
                         por_defecto=PINGS_POR_DEFECTO)
    texto, ruta_real = leer_archivo(ruta)
    dato("Archivo", ruta_real)
    if not texto.strip():
        error("El archivo de pings está vacío.")
        return
    resultado = automata.procesar_pings(texto, estado.carga.grafo.nodos())
    for r in resultado["rechazadas"]:
        aviso("Rechazada por regex → " + r)
    for a in resultado["advertencias"]:
        aviso(a)
    print()
    filas = []
    for nombre, (estado_disp, aceptada, recorrido) in resultado["resultados"].items():
        color = rojo if estado_disp == "Falla" else verde
        icono = "✖ Falla" if estado_disp == "Falla" else "✔ Activo"
        filas.append((nombre, resultado["historial"][nombre], recorrido,
                      ("acepta" if aceptada else "rechaza", color), (icono, color)))
    tabla(["Equipo", "Cadena", "Recorrido en el AFD", "AFD", "Estado"], filas)
    sin_datos = [n for n in estado.carga.grafo.nodos() if n not in resultado["historial"]]
    if sin_datos:
        dato("Sin pings (se consideran Activos)", ", ".join(sin_datos))
    estado.pings = resultado
    estado.estados = {n: r[0] for n, r in resultado["resultados"].items()}
    en_falla = [n for n, e in estado.estados.items() if e == "Falla"]
    if en_falla:
        print()
        aviso(f"En Falla: {', '.join(en_falla)}  → usa la opción 8 para ver qué pasa con la red")


def opcion_simular_fallas(estado):
    titulo("8. SIMULAR FALLAS", "💥")
    explicacion("Se quitan del grafo los equipos en Falla y se revisa si la red se divide.")
    g = estado.carga.grafo
    en_falla = [n for n, e in estado.estados.items() if e == "Falla" and g.existe(n)]
    if estado.pings is None:
        aviso("Aún no procesas pings (opción 7). Puedes escribir a mano qué equipos quitar.")
    dato("En Falla según el AFD", rojo(", ".join(en_falla)) if en_falla else "ninguno")
    mostrar_equipos(estado)
    extra = preguntar("¿Quitar otros equipos? Sepáralos con coma", ejemplo="R1,DB1",
                      por_defecto="", texto_enter="no quitar más")
    por_mayusculas = {n.upper(): n for n in g.nodos()}
    for nombre in [x.strip() for x in extra.split(",") if x.strip()]:
        real = por_mayusculas.get(nombre.upper())
        if real is None:
            aviso(f"'{nombre}' no existe en la red, se ignora.")
        elif real not in en_falla:
            en_falla.append(real)
    if not en_falla:
        aviso("No hay equipos que quitar: la red queda igual.")
        return
    resumen = simular_fallas(g, en_falla)
    print()
    dato("Se quitan", rojo(", ".join(en_falla)))
    dato("Componentes", f"antes {resumen['antes']}  →  después {len(resumen['componentes'])}")
    tabla(["Grupo", "Equipos que siguen conectados entre sí"],
          [(i, ", ".join(c)) for i, c in enumerate(resumen["componentes"], 1)])
    print()
    if resumen["dividida"]:
        error("¡La red se DIVIDIÓ!")
    else:
        exito("La red sigue conectada (hay rutas de respaldo).")
    if resumen["sin_conexion"]:
        error("Quedaron sin conexión: " + ", ".join(resumen["sin_conexion"]))


def opcion_automatas(estado):
    titulo("9. AFN → AFD (CONSTRUCCIÓN POR SUBCONJUNTOS)", "🤖")
    explicacion("Σ = {o, t}: o = OK, t = TIMEOUT. Se acepta (Falla) si termina en 'tt'.")
    afn, afd = automata.AFN_ESTADO, automata.AFD_ESTADO

    subtitulo("AFN  N = (Q, Σ, δ, q0, F)")
    dato("Q", "{" + ", ".join(afn["estados"]) + "}")
    dato("Σ", "{" + ", ".join(afn["alfabeto"]) + "}")
    dato("q0", afn["inicial"])
    dato("F", automata.conjunto_a_texto(afn["finales"]))
    filas = []
    for q in afn["estados"]:
        movs = afn["transiciones"].get(q, {})
        filas.append((q, *[automata.conjunto_a_texto(movs.get(s, set())) for s in afn["alfabeto"]]))
    tabla(["δ", "o", "t"], filas)

    subtitulo("Procedimiento de subconjuntos")
    for p in automata.PASOS_SUBCONJUNTOS:
        texto = p.strip("\n")
        if "NUEVO" in texto:
            texto = texto.replace("<- conjunto NUEVO", amarillo("← conjunto NUEVO"))
        print(("" if not p.startswith("\n") else "\n") + "  " + texto)

    subtitulo("Tabla del AFD   (→ inicial, * final)")
    filas = []
    for nombre in afd["estados"]:
        marca = ("→" if nombre == afd["inicial"] else " ") + ("*" if nombre in afd["finales"] else " ")
        fila = [marca + nombre, automata.conjunto_a_texto(afd["conjuntos"][nombre])]
        fila += [afd["transiciones"][nombre][s] for s in afd["alfabeto"]]
        filas.append(tuple(fila))
    tabla(["Estado", "Conjunto del AFN", "o", "t"], filas)

    iguales, n, contra = automata.verificar_equivalencia(afn, afd)
    print()
    if iguales:
        exito(f"AFN y AFD son equivalentes: aceptan lo mismo en las {n} cadenas de longitud 0 a 8")
    else:
        error(f"AFN y AFD NO son equivalentes, contraejemplo: {contra}")

    subtitulo("Ejemplos")
    for cadena in ("ootott", "ttto"):
        mostrar_simulacion(cadena)
    while True:
        cadena = preguntar("Prueba tu propia cadena de o/t", ejemplo="oottt", por_defecto="",
                           texto_enter="terminar")
        if not cadena:
            break
        cadena = cadena.lower()
        if any(c not in "ot" for c in cadena):
            error("Solo se permiten las letras 'o' y 't'.")
        else:
            mostrar_simulacion(cadena)


def mostrar_simulacion(cadena):
    acepta_afn, traza_afn = automata.simular_afn(automata.AFN_ESTADO, cadena)
    acepta_afd, recorrido = automata.simular_afd(automata.AFD_ESTADO, cadena)
    resultado = rojo("acepta → Falla") if acepta_afd else verde("rechaza → Activo")
    print(f"\n  Cadena {negrita(repr(cadena))}")
    print(f"    {gris('AFN (todos los caminos a la vez):')}")
    for paso in traza_afn:
        print(f"      {paso}")
    print(f"      → {'acepta' if acepta_afn else 'rechaza'} "
          f"{gris('(acepta si el conjunto final contiene q2)')}")
    print(f"    {gris('AFD:')} {recorrido}  →  {resultado}")


def opcion_derivacion(estado):
    titulo("10. DERIVACIÓN MÁS A LA IZQUIERDA", "🌳")
    explicacion("En cada paso se reemplaza el NO terminal de más a la izquierda.")
    subtitulo("Gramática G = (V, Σ, P, S)")
    for regla in ("S → RED { L }", "L → E L | E",
                  "E → T id P ; | T id P { L } | ENLACE id id : n ;",
                  "P → : n | ε", "T → ROUTER | SWITCH | PC | SERVER | DB"):
        print("    " + morado(regla))
    subtitulo("Derivación")
    pasos = derivacion_izquierda(estado.carga.parser.arbol)
    print(f"     {pasos[0][0]}")
    for i, (forma, produccion) in enumerate(pasos[1:], 1):
        print(f"  {gris(f'{i:>2}')} ⇒ {forma}   {amarillo('[' + produccion + ']')}")
    print()
    exito(f"Total: {len(pasos) - 1} pasos de derivación")


def opcion_imagenes(estado):
    titulo("11. GENERAR IMÁGENES", "🖼 ")
    import visual
    if not visual.HAY_MATPLOTLIB:
        aviso("matplotlib no está instalado: se intentará con Graphviz / archivos .dot")
    raiz = os.path.dirname(CARPETA_BASE)
    carpeta_aut = os.path.join(raiz, "03_Automatas")
    carpeta_grafo = os.path.join(raiz, "04_Grafos")
    os.makedirs(carpeta_aut, exist_ok=True)
    os.makedirs(carpeta_grafo, exist_ok=True)
    generados = [
        visual.dibujar_afn(automata.AFN_ESTADO, os.path.join(carpeta_aut, "AFN.png")),
        visual.dibujar_afd(automata.AFD_ESTADO, os.path.join(carpeta_aut, "AFD.png")),
        visual.dibujar_ap(os.path.join(carpeta_aut, "AP.png")),
    ]
    if estado.hay_red():
        tipos = {d["nombre"]: d["tipo"] for d in estado.carga.parser.dispositivos}
        generados.append(visual.dibujar_grafo(estado.carga.grafo, tipos,
                                              os.path.join(carpeta_grafo, "Grafo.png"),
                                              estado.estados))
    else:
        aviso("No hay red cargada: no se genera Grafo.png (usa la opción 1).")
    for archivo in generados:
        exito("Generado: " + archivo)


# ---------------------------------------------------------------------------
# MENÚ PRINCIPAL
# ---------------------------------------------------------------------------
# (número, texto, función, ¿necesita red?) agrupados por sección
SECCIONES = [
    ("📂 ARCHIVO", [("1", "Cargar red desde archivo", opcion_cargar_red, False)]),
    ("🌐 ANÁLISIS DEL GRAFO", [
        ("2", "Ver equipos y conexiones (V, E)", opcion_mostrar_grafo, True),
        ("3", "¿Hay camino entre dos equipos? (BFS)", opcion_bfs, True),
        ("4", "Camino más rápido (Dijkstra)", opcion_dijkstra, True),
        ("5", "Grados y equipos aislados", opcion_grados, True),
        ("6", "Ciclos y puntos críticos", opcion_ciclos, True),
    ]),
    ("📡 PINGS Y FALLAS", [
        ("7", "Procesar pings (¿quién está en Falla?)", opcion_pings, True),
        ("8", "Simular fallas", opcion_simular_fallas, True),
    ]),
    ("🤖 TEORÍA", [
        ("9", "AFN, subconjuntos y tabla del AFD", opcion_automatas, False),
        ("10", "Derivación con la gramática", opcion_derivacion, True),
    ]),
    ("🖼  IMÁGENES", [("11", "Generar imágenes (Grafo, AFN, AFD, AP)", opcion_imagenes, False)]),
]
OPCIONES = {num: (funcion, necesita_red)
            for _, items in SECCIONES for num, _, funcion, necesita_red in items}


def mostrar_menu(estado):
    print()
    print(cian("╭" + "─" * ANCHO + "╮"))
    print(cian("│") + negrita("ANALIZADOR DE REDES MEDIANTE GRAFOS".center(ANCHO)) + cian("│"))
    print(cian("│") + gris("Proyecto 4 · Teoría Computacional · UPSLP".center(ANCHO)) + cian("│"))
    print(cian("╰" + "─" * ANCHO + "╯"))

    # Barra de estado: qué está cargado y qué falta
    if estado.hay_red():
        g = estado.carga.grafo
        print(f"  Red:   {verde('✔')} {os.path.basename(estado.ruta_red)} "
              f"{gris(f'({len(g.nodos())} equipos, {len(g.aristas())} conexiones)')}")
    else:
        print(f"  Red:   {rojo('✖ sin cargar')}  {amarillo('→ empieza con la opción 1')}")
    if estado.pings is not None:
        fallas = [n for n, e in estado.estados.items() if e == "Falla"]
        texto = rojo(f"{len(fallas)} en Falla ({', '.join(fallas)})") if fallas else verde("todos Activos")
        print(f"  Pings: {verde('✔')} procesados · {texto}")
    else:
        print(f"  Pings: {gris('— sin procesar (opción 7)')}")

    for nombre_seccion, items in SECCIONES:
        print("\n  " + negrita(nombre_seccion))
        for num, texto, _, necesita_red in items:
            numero = f"[{num}]".rjust(5)
            if necesita_red and not estado.hay_red():
                print(f"   {gris(numero)}  {gris(texto + '  (carga una red primero)')}")
            else:
                print(f"   {amarillo(numero)}  {texto}")
    print(f"\n   {amarillo('[0]'.rjust(5))}  🚪 Salir")
    print(gris("  " + "─" * ANCHO))


def ejecutar_opcion(funcion, estado, *argumentos):
    """Ejecuta una opción atrapando cualquier error: el programa nunca se cae."""
    try:
        funcion(estado, *argumentos)
    except Cancelado:
        aviso("Cancelado, regresando al menú.")
    except (FileNotFoundError, ValueError) as e:
        error(str(e))
    except UnicodeDecodeError:
        error("El archivo no es de texto UTF-8 válido.")
    except OSError as e:
        error(f"No se pudo leer o escribir un archivo: {e}")
    except Exception as e:                      # red de seguridad final
        error(f"Error inesperado ({type(e).__name__}): {e}")


def main():
    # Para que los símbolos (δ, ε, Σ, ⇒, ✔) se vean bien en la consola de Windows
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    estado = Estado()
    if len(sys.argv) > 1:
        ejecutar_opcion(opcion_cargar_red, estado, sys.argv[1])
    if len(sys.argv) > 2 and estado.hay_red():
        ejecutar_opcion(opcion_pings, estado, sys.argv[2])

    while True:
        mostrar_menu(estado)
        try:
            opcion = input(f"  {amarillo('➜')} Escribe el número de una opción y da Enter: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  👋 Hasta luego.")
            break
        if opcion == "0":
            print("  👋 Hasta luego.")
            break
        try:
            if opcion not in OPCIONES:
                error(f"'{opcion}' no es una opción. Escribe solo el número, del 0 al 11.")
                continue
            funcion, necesita_red = OPCIONES[opcion]
            if necesita_red and not estado.hay_red():
                error("Primero carga una red: escribe 1 y da Enter dos veces.")
                continue
            ejecutar_opcion(funcion, estado)
            pausa()
        except (EOFError, KeyboardInterrupt):
            print("\n  Operación cancelada.")
            break


if __name__ == "__main__":
    main()
