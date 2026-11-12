"""
grafo.py - Grafo de la red y algoritmos programados a mano.

CONCEPTO TEÓRICO
----------------
Un grafo G = (V, E) tiene un conjunto de vértices V (los dispositivos) y un
conjunto de aristas E (las conexiones). Nuestro grafo es:
    - NO DIRIGIDO: si R1 se conecta con SW1, SW1 también con R1.
    - PONDERADO: cada arista tiene un peso = latencia en milisegundos.

Se guarda como LISTA DE ADYACENCIA en un diccionario de diccionarios:
    {"R1": {"SW1": 5, "SW2": 4}, "SW1": {"R1": 5, "PC1": 2, ...}, ...}

Algoritmos (sin networkx):
    BFS        -> ¿existe ruta entre A y B?
    Dijkstra   -> ruta de menor latencia total
    Grados     -> número de vecinos de cada nodo; grado 0 = nodo aislado
    DFS        -> detección de ciclos y rutas alternativas
    Componentes conexos -> puntos críticos (nodos de articulación)
"""


class Grafo:
    def __init__(self):
        # Lista de adyacencia. Python conserva el orden de inserción de las
        # llaves, así los resultados salen en el orden en que se declararon.
        self.adyacencia = {}

    # --------------------------- construcción ---------------------------
    def agregar_nodo(self, nombre):
        if nombre not in self.adyacencia:
            self.adyacencia[nombre] = {}

    def agregar_arista(self, a, b, peso):
        """Arista no dirigida: se guarda en ambos sentidos."""
        self.agregar_nodo(a)
        self.agregar_nodo(b)
        self.adyacencia[a][b] = peso
        self.adyacencia[b][a] = peso

    def copia_sin(self, nodos_quitados):
        """Devuelve un grafo nuevo sin los nodos indicados (ni sus aristas)."""
        nuevo = Grafo()
        for nodo in self.adyacencia:
            if nodo not in nodos_quitados:
                nuevo.agregar_nodo(nodo)
        for a, b, peso in self.aristas():
            if a not in nodos_quitados and b not in nodos_quitados:
                nuevo.agregar_arista(a, b, peso)
        return nuevo

    # ----------------------------- consultas -----------------------------
    def nodos(self):
        return list(self.adyacencia.keys())

    def aristas(self):
        """Lista de (a, b, peso) sin repetir (a-b y b-a es la misma arista)."""
        vistas = set()
        lista = []
        for a, vecinos in self.adyacencia.items():
            for b, peso in vecinos.items():
                par = frozenset((a, b))
                if par not in vistas:
                    vistas.add(par)
                    lista.append((a, b, peso))
        return lista

    def existe(self, nodo):
        return nodo in self.adyacencia

    # ------------------------------- BFS -------------------------------
    def bfs(self, origen, destino):
        """
        Búsqueda en ANCHURA: visita los nodos por niveles usando una COLA.
        Si en algún momento se visita 'destino', existe ruta.
        Devuelve (existe, orden_de_visita, ruta_en_saltos).
        """
        visitados = {origen}
        padre = {origen: None}
        cola = [origen]
        orden = []
        while cola:
            actual = cola.pop(0)          # sacar del frente de la cola (FIFO)
            orden.append(actual)
            if actual == destino:
                break
            for vecino in self.adyacencia[actual]:
                if vecino not in visitados:
                    visitados.add(vecino)
                    padre[vecino] = actual
                    cola.append(vecino)
        if destino not in padre:
            return False, orden, []
        return True, orden, _reconstruir_ruta(padre, destino)

    # ----------------------------- Dijkstra -----------------------------
    def dijkstra(self, origen, destino):
        """
        Algoritmo de Dijkstra (pesos positivos):
          1. distancia[origen] = 0, las demás = infinito.
          2. Elegir el nodo NO visitado con menor distancia y marcarlo visitado.
          3. RELAJAR sus aristas: si distancia[u] + peso(u,v) < distancia[v],
             se actualiza distancia[v] y se recuerda que se llegó desde u.
          4. Repetir hasta visitar el destino o no quedar nodos alcanzables.
        Devuelve (distancia_total o None, ruta, pasos_explicados).
        """
        infinito = float("inf")
        distancia = {nodo: infinito for nodo in self.adyacencia}
        anterior = {nodo: None for nodo in self.adyacencia}
        distancia[origen] = 0
        visitados = set()
        pasos = []

        while len(visitados) < len(self.adyacencia):
            # Paso 2: buscar a mano el nodo no visitado de menor distancia.
            u = None
            for nodo in self.adyacencia:
                if nodo not in visitados and (u is None or distancia[nodo] < distancia[u]):
                    u = nodo
            if distancia[u] == infinito:
                break                      # lo que queda no es alcanzable
            visitados.add(u)

            # Paso 3: relajación de las aristas de u
            cambios = []
            for v, peso in self.adyacencia[u].items():
                if v not in visitados and distancia[u] + peso < distancia[v]:
                    distancia[v] = distancia[u] + peso
                    anterior[v] = u
                    cambios.append(f"{v}={distancia[v]}")
            pasos.append(f"Se fija {u} (dist {distancia[u]}). Actualiza: "
                         + (", ".join(cambios) if cambios else "nada"))
            if u == destino:
                break

        if distancia[destino] == infinito:
            return None, [], pasos
        return distancia[destino], _reconstruir_ruta(anterior, destino), pasos

    def peso_de_ruta(self, ruta):
        return sum(self.adyacencia[ruta[i]][ruta[i + 1]] for i in range(len(ruta) - 1))

    # -------------------------- grados y aislados --------------------------
    def grados(self):
        """Grado de un nodo = cantidad de aristas que inciden en él."""
        return {nodo: len(vecinos) for nodo, vecinos in self.adyacencia.items()}

    def aislados(self):
        """Nodos con grado 0 (sin ninguna conexión)."""
        return [nodo for nodo, grado in self.grados().items() if grado == 0]

    # -------------------------- DFS: ciclos y rutas --------------------------
    def tiene_ciclo(self):
        """
        DFS para detectar ciclos en un grafo NO dirigido: si al explorar
        encontramos un vecino ya visitado que NO es el nodo del que venimos
        (arista de retroceso), hay un ciclo.
        """
        visitados = set()
        for inicio in self.adyacencia:
            if inicio in visitados:
                continue
            pila = [(inicio, None)]        # (nodo, padre en el árbol DFS)
            while pila:
                nodo, padre = pila.pop()
                if nodo in visitados:
                    return True
                visitados.add(nodo)
                for vecino in self.adyacencia[nodo]:
                    if vecino != padre:
                        if vecino in visitados:
                            return True
                        pila.append((vecino, nodo))
        return False

    def encontrar_ciclos(self, limite=100):
        """
        Enumera los ciclos simples con DFS. Para no repetir el mismo ciclo:
          - cada ciclo se cuenta desde su nodo de menor índice (orden de declaración)
          - y en un solo sentido (el 2.º nodo debe tener menor índice que el último).
        Devuelve una lista de ciclos, cada uno como lista que termina en su inicio.
        """
        indice = {nodo: i for i, nodo in enumerate(self.adyacencia)}
        ciclos = []

        def dfs(inicio, actual, camino):
            if len(ciclos) >= limite:
                return
            for vecino in self.adyacencia[actual]:
                if vecino == inicio and len(camino) >= 3:
                    if indice[camino[1]] < indice[camino[-1]]:
                        ciclos.append(camino + [inicio])
                elif vecino not in camino and indice[vecino] > indice[inicio]:
                    dfs(inicio, vecino, camino + [vecino])

        for inicio in self.adyacencia:
            dfs(inicio, inicio, [inicio])
        return ciclos

    def rutas_alternativas(self, origen, destino, limite=20):
        """
        Todas las rutas simples (sin repetir nodos) de origen a destino, con DFS
        y "backtracking". Se ordenan por latencia total.
        """
        rutas = []

        def dfs(actual, camino):
            if len(rutas) >= limite:
                return
            if actual == destino:
                rutas.append(list(camino))
                return
            for vecino in self.adyacencia[actual]:
                if vecino not in camino:
                    camino.append(vecino)
                    dfs(vecino, camino)
                    camino.pop()          # backtracking

        dfs(origen, [origen])
        rutas.sort(key=self.peso_de_ruta)
        return [(ruta, self.peso_de_ruta(ruta)) for ruta in rutas]

    # --------------------- componentes y puntos críticos ---------------------
    def componentes_conexos(self, excluir=()):
        """
        Agrupa los nodos en componentes: dos nodos están en el mismo componente
        si existe ruta entre ellos. Se hace un recorrido (BFS) desde cada nodo
        aún no visitado. 'excluir' simula que esos nodos no existen.
        """
        excluir = set(excluir)
        visitados = set()
        componentes = []
        for inicio in self.adyacencia:
            if inicio in visitados or inicio in excluir:
                continue
            componente = []
            cola = [inicio]
            visitados.add(inicio)
            while cola:
                actual = cola.pop(0)
                componente.append(actual)
                for vecino in self.adyacencia[actual]:
                    if vecino not in visitados and vecino not in excluir:
                        visitados.add(vecino)
                        cola.append(vecino)
            componentes.append(componente)
        return componentes

    def puntos_criticos(self):
        """
        Un nodo es PUNTO CRÍTICO (punto de articulación) si al quitarlo
        AUMENTA el número de componentes conexos: la red se divide.
        Devuelve (criticos, detalle) donde detalle[nodo] = componentes sin él.
        """
        base = len(self.componentes_conexos())
        criticos = []
        detalle = {}
        for nodo in self.adyacencia:
            sin_nodo = self.componentes_conexos(excluir=[nodo])
            detalle[nodo] = sin_nodo
            if len(sin_nodo) > base:
                criticos.append(nodo)
        return criticos, detalle


def _reconstruir_ruta(padre, destino):
    """Sigue los 'padres' desde el destino hasta el origen y voltea la lista."""
    ruta = []
    nodo = destino
    while nodo is not None:
        ruta.append(nodo)
        nodo = padre[nodo]
    ruta.reverse()
    return ruta


def construir_grafo(resultado_parser):
    """
    Crea el grafo a partir de lo que reconoció el parser:
      - cada dispositivo es un vértice
      - cada hijo se conecta con su padre (peso = latencia; 1 si no la trae)
      - cada ENLACE agrega una arista extra
    Los hijos directos de RED no se conectan con nada (RED no es dispositivo).
    """
    grafo = Grafo()
    for d in resultado_parser.dispositivos:
        grafo.agregar_nodo(d["nombre"])
    for d in resultado_parser.dispositivos:
        if d["padre"] is not None:
            peso = d["peso"] if d["peso"] is not None else 1
            grafo.agregar_arista(d["padre"], d["nombre"], peso)
    for e in resultado_parser.enlaces:
        grafo.agregar_arista(e["origen"], e["destino"], e["peso"])
    return grafo
