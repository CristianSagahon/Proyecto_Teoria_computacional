"""
visual.py - Genera las imágenes del grafo y de los autómatas.

Aquí matplotlib se usa SOLO PARA DIBUJAR. Los autómatas y el grafo ya fueron
construidos a mano en automata.py, automata_pila.py y grafo.py; este módulo
solo recibe esas estructuras y las pinta.

Si matplotlib no está instalado, se intenta con Graphviz (programa 'dot').
Si tampoco está, se guardan los archivos .dot para dibujarlos después.
"""

import math
import os
import shutil
import subprocess

try:
    import matplotlib
    matplotlib.use("Agg")                      # dibuja en archivo, sin ventana
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch
    HAY_MATPLOTLIB = True
except ImportError:
    HAY_MATPLOTLIB = False

COLORES_TIPO = {
    "ROUTER": "#f4a261",
    "SWITCH": "#2a9d8f",
    "PC": "#8ecae6",
    "SERVER": "#b5838d",
    "DB": "#e9c46a",
}
COLOR_FALLA = "#e63946"


# ---------------------------------------------------------------------------
# GRAFO
# ---------------------------------------------------------------------------
def _posiciones_por_niveles(grafo):
    """
    Acomoda los nodos por NIVELES de BFS: el primer nodo de cada componente va
    arriba, sus vecinos en el nivel siguiente, etc. Dentro de un nivel, cada
    nodo se ordena según la posición promedio de sus vecinos del nivel de
    arriba (así se cruzan menos aristas). Los componentes van lado a lado.
    """
    posiciones = {}
    x_inicio = 0.0
    for componente in grafo.componentes_conexos():
        nivel = {componente[0]: 0}
        cola = [componente[0]]
        while cola:
            actual = cola.pop(0)
            for vecino in grafo.adyacencia[actual]:
                if vecino not in nivel:
                    nivel[vecino] = nivel[actual] + 1
                    cola.append(vecino)
        niveles = {}
        for nodo in componente:
            niveles.setdefault(nivel[nodo], []).append(nodo)
        ancho = max(len(nodos) for nodos in niveles.values())
        for n in sorted(niveles):
            nodos = niveles[n]
            if n > 0:
                def promedio_arriba(nodo):
                    xs = [posiciones[v][0] for v in grafo.adyacencia[nodo]
                          if nivel.get(v) == n - 1]
                    return sum(xs) / len(xs) if xs else 0
                nodos.sort(key=promedio_arriba)
            desplazamiento = (ancho - len(nodos)) / 2
            for i, nodo in enumerate(nodos):
                posiciones[nodo] = (x_inicio + desplazamiento + i, -float(n))
        x_inicio += ancho + 0.5
    return posiciones


def dibujar_grafo(grafo, tipos, archivo, estados=None):
    """tipos = {nodo: 'ROUTER'...}; estados = {nodo: 'Falla'/'Activo'} (opcional)."""
    estados = estados or {}
    if not HAY_MATPLOTLIB:
        return _grafo_con_graphviz(grafo, tipos, archivo, estados)

    pos = _posiciones_por_niveles(grafo)
    fig, ax = plt.subplots(figsize=(9, 7))
    for a, b, peso in grafo.aristas():
        (x1, y1), (x2, y2) = pos[a], pos[b]
        ax.plot([x1, x2], [y1, y2], color="#555555", linewidth=2, zorder=1)
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, f"{peso} ms", fontsize=10, ha="center",
                va="center", bbox=dict(boxstyle="round", fc="white", ec="#999999"), zorder=3)
    for nodo, (x, y) in pos.items():
        color = COLOR_FALLA if estados.get(nodo) == "Falla" else COLORES_TIPO.get(tipos.get(nodo), "#cccccc")
        ax.add_patch(Circle((x, y), 0.22, fc=color, ec="black", zorder=2))
        ax.text(x, y + 0.04, nodo, ha="center", va="center", fontsize=11, fontweight="bold", zorder=4)
        ax.text(x, y - 0.1, tipos.get(nodo, ""), ha="center", va="center", fontsize=7, zorder=4)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 0.6, max(xs) + 0.6)
    ax.set_ylim(min(ys) - 0.6, max(ys) + 0.6)
    ax.set_aspect("equal")
    ax.axis("off")
    titulo = "Grafo de la red (peso = latencia)"
    if any(e == "Falla" for e in estados.values()):
        titulo += "  -  rojo = dispositivo en Falla"
    ax.set_title(titulo, fontsize=13)
    fig.savefig(archivo, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return archivo


# ---------------------------------------------------------------------------
# AUTÓMATAS (función genérica de dibujo de diagramas de estados)
# ---------------------------------------------------------------------------
def dibujar_automata(estados, posiciones, transiciones, inicial, finales, archivo, titulo,
                     etiquetas=None):
    """
    estados: lista de nombres; posiciones: {estado: (x, y)}
    transiciones: lista de (origen, destino, etiqueta, curvatura)
    etiquetas: texto extra debajo de cada estado (ej. el conjunto del AFD)
    """
    if not HAY_MATPLOTLIB:
        return _automata_con_graphviz(estados, transiciones, inicial, finales, archivo, titulo)

    radio = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))
    for origen, destino, etiqueta, curva in transiciones:
        x1, y1 = posiciones[origen]
        x2, y2 = posiciones[destino]
        if origen == destino:
            # Bucle (self-loop) dibujado arriba del estado
            flecha = FancyArrowPatch((x1 - 0.2, y1 + radio * 0.8), (x1 + 0.2, y1 + radio * 0.8),
                                     connectionstyle="arc3,rad=-2.2", arrowstyle="-|>",
                                     mutation_scale=18, linewidth=1.5, color="black")
            ax.add_patch(flecha)
            ax.text(x1, y1 + radio + 0.55, etiqueta, ha="center", va="bottom", fontsize=11)
        else:
            # Punto de control de la curva (como lo calcula matplotlib en arc3)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = x2 - x1, y2 - y1
            cx, cy = mx + curva * dy, my - curva * dx
            # La flecha sale y llega al BORDE de cada círculo, apuntando al control
            inicio = _punto_en_borde((x1, y1), (cx, cy), radio)
            fin = _punto_en_borde((x2, y2), (cx, cy), radio)
            flecha = FancyArrowPatch(inicio, fin, connectionstyle=f"arc3,rad={curva}",
                                     arrowstyle="-|>", mutation_scale=18, linewidth=1.5,
                                     shrinkA=0, shrinkB=0, color="black")
            ax.add_patch(flecha)
            # Etiqueta en el punto medio de la curva
            ax.text(mx + curva * dy * 0.55, my - curva * dx * 0.55 + 0.08, etiqueta,
                    ha="center", va="center", fontsize=11,
                    bbox=dict(boxstyle="round", fc="white", ec="none"))

    for estado in estados:
        x, y = posiciones[estado]
        ax.add_patch(Circle((x, y), radio, fc="#dbe9f6", ec="black", linewidth=1.5, zorder=2))
        if estado in finales:
            ax.add_patch(Circle((x, y), radio * 0.82, fc="none", ec="black", linewidth=1.5, zorder=3))
        ax.text(x, y, estado, ha="center", va="center", fontsize=13, fontweight="bold", zorder=4)
        if etiquetas and estado in etiquetas:
            ax.text(x, y - radio - 0.18, etiquetas[estado], ha="center", va="top", fontsize=10)
        if estado == inicial:
            ax.annotate("", xy=(x - radio, y), xytext=(x - radio - 0.6, y),
                        arrowprops=dict(arrowstyle="-|>", linewidth=1.5))
            ax.text(x - radio - 0.65, y + 0.12, "inicio", fontsize=9)

    xs = [p[0] for p in posiciones.values()]
    ys = [p[1] for p in posiciones.values()]
    ax.set_xlim(min(xs) - 1.3, max(xs) + 1.0)
    ax.set_ylim(min(ys) - 1.6, max(ys) + 1.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(titulo, fontsize=13)
    fig.savefig(archivo, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return archivo


def _punto_en_borde(centro, hacia, radio):
    """Punto sobre el borde del círculo 'centro' en dirección al punto 'hacia'."""
    dx, dy = hacia[0] - centro[0], hacia[1] - centro[1]
    distancia = math.hypot(dx, dy) or 1
    return centro[0] + radio * dx / distancia, centro[1] + radio * dy / distancia


def dibujar_afn(afn, archivo):
    posiciones = {"q0": (0, 0), "q1": (2.5, 0), "q2": (5, 0)}
    transiciones = []
    for origen, movimientos in afn["transiciones"].items():
        # Juntar los símbolos que van al mismo destino en una sola etiqueta
        por_destino = {}
        for simbolo, destinos in movimientos.items():
            for d in destinos:
                por_destino.setdefault(d, []).append(simbolo)
        for destino, simbolos in por_destino.items():
            transiciones.append((origen, destino, ", ".join(simbolos), 0))
    return dibujar_automata(afn["estados"], posiciones, transiciones, afn["inicial"],
                            afn["finales"], archivo,
                            "AFN: dispositivo en Falla si los 2 últimos pings son TIMEOUT")


def dibujar_afd(afd, archivo):
    from automata import conjunto_a_texto
    posiciones = {nombre: (2.5 * i, 0) for i, nombre in enumerate(afd["estados"])}
    orden = {nombre: i for i, nombre in enumerate(afd["estados"])}
    transiciones = []
    for origen, movimientos in afd["transiciones"].items():
        por_destino = {}
        for simbolo, destino in movimientos.items():
            por_destino.setdefault(destino, []).append(simbolo)
        for destino, simbolos in por_destino.items():
            # Hacia adelante: curva arriba; hacia atrás: curva abajo (más si es lejos)
            salto = orden[destino] - orden[origen]
            curva = 0 if salto == 0 else (-0.25 if salto > 0 else -(0.3 + 0.1 * abs(salto)))
            transiciones.append((origen, destino, ", ".join(simbolos), curva))
    etiquetas = {n: conjunto_a_texto(afd["conjuntos"][n]) for n in afd["estados"]}
    return dibujar_automata(afd["estados"], posiciones, transiciones, afd["inicial"],
                            afd["finales"], archivo, "AFD obtenido por subconjuntos", etiquetas)


def dibujar_ap(archivo):
    posiciones = {"q0": (0, 0), "qf": (3.5, 0)}
    transiciones = [
        ("q0", "q0", "{, Z0 / B Z0\n{, B / B B\n}, B / ε\na, X / X  (a ≠ { })", 0),
        ("q0", "qf", "ε, Z0 / Z0", 0),
    ]
    return dibujar_automata(["q0", "qf"], posiciones, transiciones, "q0", {"qf"}, archivo,
                            "Autómata de pila: balanceo de llaves  (Γ = {B, Z0})")


# ---------------------------------------------------------------------------
# Alternativa con Graphviz (solo si no hay matplotlib)
# ---------------------------------------------------------------------------
def _guardar_dot(texto_dot, archivo_png):
    archivo_dot = os.path.splitext(archivo_png)[0] + ".dot"
    with open(archivo_dot, "w", encoding="utf-8") as f:
        f.write(texto_dot)
    if shutil.which("dot"):
        subprocess.run(["dot", "-Tpng", archivo_dot, "-o", archivo_png], check=True)
        return archivo_png
    return archivo_dot


def _grafo_con_graphviz(grafo, tipos, archivo, estados):
    lineas = ["graph G {", "  node [shape=circle, style=filled];"]
    for nodo in grafo.nodos():
        color = "red" if estados.get(nodo) == "Falla" else "lightblue"
        lineas.append(f'  {nodo} [fillcolor={color}, label="{nodo}\\n{tipos.get(nodo, "")}"];')
    for a, b, peso in grafo.aristas():
        lineas.append(f'  {a} -- {b} [label="{peso} ms"];')
    lineas.append("}")
    return _guardar_dot("\n".join(lineas), archivo)


def _automata_con_graphviz(estados, transiciones, inicial, finales, archivo, titulo):
    lineas = ["digraph A {", "  rankdir=LR;", f'  label="{titulo}";', '  inicio [shape=point];']
    for e in estados:
        forma = "doublecircle" if e in finales else "circle"
        lineas.append(f"  {e} [shape={forma}];")
    lineas.append(f"  inicio -> {inicial};")
    for origen, destino, etiqueta, _ in transiciones:
        lineas.append(f'  {origen} -> {destino} [label="{etiqueta}"];')
    lineas.append("}")
    return _guardar_dot("\n".join(lineas), archivo)
