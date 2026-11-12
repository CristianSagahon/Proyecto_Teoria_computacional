# Analizador de redes mediante grafos (Proyecto 4)

**Proyecto Final Integrador – Teoría Computacional**
Universidad Politécnica de San Luis Potosí – Ingeniería en Tecnologías de la Información

**Integrantes:** David, Jared, Cristian

## Descripción

Programa de consola que lee la descripción de una red (`red.txt`) y los resultados
de ping de sus dispositivos (`pings.txt`). Valida los archivos con los modelos del
curso y responde preguntas sobre la red:

| Fase | Modelo teórico | Archivo |
|------|----------------|---------|
| Tokens (palabras del lenguaje) | Expresiones regulares | `lexer.py` |
| Balanceo de llaves `{ }` | Autómata de pila | `automata_pila.py` |
| Estructura del archivo | Gramática libre de contexto + descenso recursivo | `parser.py` |
| Reglas de contexto (nombres repetidos, ENLACE) | Validación semántica | `parser.py` |
| Red como grafo, BFS, Dijkstra, ciclos, puntos críticos | Teoría de grafos | `grafo.py` |
| Estado de cada dispositivo según sus pings | AFN → AFD (subconjuntos) | `automata.py` |
| Imágenes | (matplotlib solo dibuja) | `visual.py` |
| Colores, cuadros y tablas en la consola | (solo presentación) | `consola.py` |

Los dispositivos que el AFD marca en **Falla** se quitan del grafo y se recalcula la
conectividad: así se unen los autómatas con los grafos.

## Requisitos y lenguaje

- Lenguaje: **Python 3** (probado con 3.10).
- Biblioteca externa: `matplotlib`, **solo** para dibujar las imágenes (opción 11).
  Si no está instalada, el resto del programa funciona igual; las imágenes se
  intentan generar con Graphviz (`dot`) o se guardan como archivos `.dot`.
- No se usa networkx, lark, ply ni ninguna biblioteca que construya autómatas o parsers.

```bash
pip install -r requirements.txt
```

## Cómo ejecutar

Desde la carpeta `02_Codigo`:

```bash
python main.py
```

```bash
python main.py ejemplos/red_ejemplo.txt
```

```bash
python main.py ejemplos/red_ejemplo.txt ejemplos/pings_ejemplo.txt
```

El primer argumento carga la red al iniciar y el segundo (opcional) procesa los pings.

Pruebas automáticas:

```bash
python -m unittest discover -s tests -v
```

## Formato de entrada

`red.txt` (bloques anidados; cada hijo se conecta con su padre y el número después
de `:` es la latencia en ms; `ENLACE` agrega conexiones extra; `#` inicia un comentario):

```
RED {
  ROUTER R1 {
    SWITCH SW1 : 5 { PC PC1 : 2 ; PC PC2 : 2 ; }
    SWITCH SW2 : 4 { SERVER SRV1 : 1 ; }
  }
  DB DB1 ;
  ENLACE PC2 DB1 : 3 ;
  ENLACE SRV1 DB1 : 2 ;
}
```

Un hijo directo de `RED` (como `DB1`) no tiene arista hacia RED, porque RED no es un
dispositivo. Si un dispositivo anidado no trae peso, se usa 1 ms (con advertencia).

`pings.txt` (una línea por ping, en orden de tiempo):

```
PC2 OK
PC2 TIMEOUT
```

## Gramática

```
S → RED { L }
L → E L | E
E → T id P ; | T id P { L } | ENLACE id id : n ;
P → : n | ε
T → ROUTER | SWITCH | PC | SERVER | DB
```

## Menú

```
 1. Cargar red desde archivo
 2. Mostrar V, E y lista de adyacencia
 3. ¿Existe ruta entre A y B? (BFS)
 4. Ruta más corta entre A y B (Dijkstra)
 5. Grados y nodos aislados
 6. Ciclos y puntos críticos
 7. Procesar pings (estado de cada dispositivo con el AFD)
 8. Simular fallas
 9. Mostrar AFN, procedimiento de subconjuntos y tabla del AFD
10. Mostrar derivación con la gramática
11. Generar imágenes
 0. Salir
```

Cómo ayuda el menú a usarlo:

- Arriba hay una **barra de estado** que dice si ya hay una red cargada y si ya se procesaron los pings.
- Las opciones que necesitan una red se ven en gris hasta que cargas una con la opción 1.
- Cada pregunta trae un ejemplo de qué escribir y dice qué pasa si solo das Enter
  (por ejemplo, `Enter = ejemplos\red_ejemplo.txt` o `Enter = regresar al menú`).
- Los nombres de los equipos se aceptan en mayúsculas o minúsculas (`pc1` = `PC1`).
  Si escribes uno que no existe, te muestra la lista de equipos y vuelve a preguntar.
- Después de cada opción espera un Enter, para que el resultado no se pierda al volver al menú.
- Los resultados se muestran en tablas con colores: verde = bien/Activo, rojo = error/Falla,
  amarillo = aviso.

Los colores se apagan solos cuando la salida se guarda en un archivo. También se pueden
apagar a mano con la variable de entorno `NO_COLOR=1`.

Ante cualquier error (archivo inexistente, opción inválida, nodo que no existe,
archivo mal formado) el programa muestra un mensaje y vuelve al menú.

## Estructura del proyecto

```
Equipo_Proyecto4/
├── 01_Documentacion/      Proyecto_Final.pdf
├── 02_Codigo/
│   ├── main.py            menú CLI y orquestación de las fases
│   ├── lexer.py           regex y analizador léxico
│   ├── parser.py          gramática, descenso recursivo, derivación, semántica
│   ├── automata_pila.py   autómata de pila (llaves)
│   ├── automata.py        AFN, subconjuntos, AFD, pings
│   ├── grafo.py           grafo y algoritmos
│   ├── visual.py          imágenes
│   ├── consola.py         colores, cuadros y tablas del menú
│   ├── ejemplos/          red_ejemplo.txt, pings_ejemplo.txt e inválidos
│   ├── tests/test_casos.py
│   ├── requirements.txt
│   └── README.md
├── 03_Automatas/          AFN.png, AFD.png, AP.png
├── 04_Grafos/             Grafo.png
├── 05_Pruebas/            casos_prueba.md
├── 06_Presentacion/
└── 07_Evidencias/         Bitacora.md, salida_menu.txt, salida_pruebas.txt
```

## Ejemplos de uso (salida real)

Salida tomada de `07_Evidencias/salida_menu.txt`. En la terminal se ve a colores.

**Menú principal** (antes de cargar una red):

```
╭────────────────────────────────────────────────────────────────────────╮
│                  ANALIZADOR DE REDES MEDIANTE GRAFOS                   │
│               Proyecto 4 · Teoría Computacional · UPSLP                │
╰────────────────────────────────────────────────────────────────────────╯
  Red:   ✖ sin cargar  → empieza con la opción 1
  Pings: — sin procesar (opción 7)

  📂 ARCHIVO
     [1]  Cargar red desde archivo

  🌐 ANÁLISIS DEL GRAFO
     [2]  Ver equipos y conexiones (V, E)  (carga una red primero)
     [3]  ¿Hay camino entre dos equipos? (BFS)  (carga una red primero)
  ...
     [0]  🚪 Salir
  ➜ Escribe el número de una opción y da Enter:
```

**Opción 1 – cargar la red** (escribir `1` y dar Enter vacío). Final de la traza de la pila:

```
  │ 49   │ }       │ δ(q0, }, B) = (q0, ε)   pop B           │ Z0       │
  │ 50   │ ε       │ δ(q0, ε, Z0) = (qf, Z0)   ACEPTA        │ Z0       │
  └──────┴─────────┴─────────────────────────────────────────┴──────────┘
  ✔  Llaves balanceadas: el autómata de pila ACEPTA

▸ Fase 3 · Parser (gramática libre de contexto)
  ✔  Sintaxis correcta: 7 dispositivos y 2 ENLACE

  ✔ RED ACEPTADA: 7 nodos y 7 aristas
```

**Opción 4 – Dijkstra** (escribir `4`, luego `PC1` y `SRV1`):

```
▸ Pasos del algoritmo
  ┌───┬──────────────────────────────────────────────┐
  │ # │ Qué hizo                                     │
  ├───┼──────────────────────────────────────────────┤
  │ 1 │ Se fija PC1 (dist 0). Actualiza: SW1=2       │
  │ 2 │ Se fija SW1 (dist 2). Actualiza: R1=7, PC2=4 │
  │ 3 │ Se fija PC2 (dist 4). Actualiza: DB1=7       │
  │ 4 │ Se fija R1 (dist 7). Actualiza: SW2=11       │
  │ 5 │ Se fija DB1 (dist 7). Actualiza: SRV1=9      │
  │ 6 │ Se fija SRV1 (dist 9). Actualiza: SW2=10     │
  └───┴──────────────────────────────────────────────┘

  ✔  Ruta más corta: 9 ms
     PC1 → SW1 → PC2 → DB1 → SRV1
```

**Opción 6 – ciclos y puntos críticos:**

```
  ✔  SÍ hay ciclos (DFS encontró una arista de retroceso): 1
     R1 - SW1 - PC2 - DB1 - SRV1 - SW2 - R1

▸ ¿Qué pasa si quito cada equipo?  (componentes ahora: 1)
  ┌──────┬─────────────┬─────────────────────────────────────┬───────────┐
  │ Sin  │ Componentes │ Grupos que quedan                   │ ¿Crítico? │
  ├──────┼─────────────┼─────────────────────────────────────┼───────────┤
  │ R1   │ 1           │ {SW1, PC1, PC2, DB1, SRV1, SW2}     │ ok        │
  │ SW1  │ 2           │ {R1, SW2, SRV1, DB1, PC2}  |  {PC1} │ CRÍTICO   │
  ...
  ✖  Puntos críticos: SW1
```

**Opción 7 – pings con el AFD** (escribir `7` y dar Enter vacío):

```
  ┌────────┬────────┬───────────────────────────────┬─────────┬──────────┐
  │ Equipo │ Cadena │ Recorrido en el AFD           │ AFD     │ Estado   │
  ├────────┼────────┼───────────────────────────────┼─────────┼──────────┤
  │ R1     │ oo     │ A -o-> A -o-> A               │ rechaza │ ✔ Activo │
  │ SW1    │ oott   │ A -o-> A -o-> A -t-> B -t-> C │ acepta  │ ✖ Falla  │
  │ PC1    │ oto    │ A -o-> A -t-> B -o-> A        │ rechaza │ ✔ Activo │
  │ PC2    │ tto    │ A -t-> B -t-> C -o-> A        │ rechaza │ ✔ Activo │
  ...
  ⚠  En Falla: SW1  → usa la opción 8 para ver qué pasa con la red
```

**Opción 8 – simular fallas** (escribir `8` y dar Enter vacío):

```
  Se quitan: SW1
  Componentes: antes 1  →  después 2
  ┌───────┬────────────────────────────────────────┐
  │ Grupo │ Equipos que siguen conectados entre sí │
  ├───────┼────────────────────────────────────────┤
  │ 1     │ R1, SW2, SRV1, DB1, PC2                │
  │ 2     │ PC1                                    │
  └───────┴────────────────────────────────────────┘

  ✖  ¡La red se DIVIDIÓ!
  ✖  Quedaron sin conexión: PC1
```

**Opción 9 – subconjuntos y tabla del AFD:**

```
  Procesando B = {q0,q1}:
    δ'(B, o) = δ(q0,o)={q0} ∪ δ(q1,o)=∅ = {q0} = A
    δ'(B, t) = δ(q0,t)={q0,q1} ∪ δ(q1,t)={q2} = {q0,q1,q2} = C  ← conjunto NUEVO
  ...
▸ Tabla del AFD   (→ inicial, * final)
  ┌────────┬──────────────────┬───┬───┐
  │ Estado │ Conjunto del AFN │ o │ t │
  ├────────┼──────────────────┼───┼───┤
  │ → A    │ {q0}             │ A │ B │
  │   B    │ {q0,q1}          │ A │ C │
  │  *C    │ {q0,q1,q2}       │ A │ C │
  └────────┴──────────────────┴───┴───┘

  ✔  AFN y AFD son equivalentes: aceptan lo mismo en las 511 cadenas de longitud 0 a 8
```

**Errores** (opción 1 escribiendo la ruta de un archivo de `ejemplos/`):

```
  ✖ RED RECHAZADA - error léxico:
     • Línea 2, columna 3: 'router' no es válido (las palabras reservadas van en mayúsculas), ¿quisiste decir ROUTER?
     • Línea 3, columna 25: 'pc1' no es un nombre válido: debe iniciar con mayúscula

  ✖ RED RECHAZADA - error sintáctico:
     • Línea 4: se esperaba ';' después de PC1 (o '{' para abrir su bloque), pero se encontró 'PC'

  ✖ RED RECHAZADA - error del autómata de pila (llaves):
     • Línea 5: se encontró '}' sin un bloque abierto que cerrar (la pila ya estaba en Z0, sobra una llave de cierre)
```

La salida completa de todas las opciones está en `07_Evidencias/salida_menu.txt`.

## Generar un .exe (opcional)

```bash
pip install pyinstaller
```

```bash
pyinstaller --onefile --name AnalizadorRed main.py
```

El ejecutable queda en `dist/AnalizadorRed.exe`. Copia la carpeta `ejemplos/` junto al
`.exe` para usar los archivos de ejemplo.
