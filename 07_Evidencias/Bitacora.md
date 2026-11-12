# Bitácora del proyecto – Proyecto 4: Analizador de redes mediante grafos

Equipo: David, Jared, Cristian

| Fecha | Actividad | Responsable | Resultado |
|-------|-----------|-------------|-----------|
| 2026-11-12 | Definición del formato de entrada (red.txt y pings.txt) y estructura del proyecto | Equipo | Estructura de carpetas creada |
| 2026-11-12 | Analizador léxico con expresiones regulares (lexer.py) | Jared | Reporta todos los errores léxicos con línea y columna |
| 2026-11-12 | Autómata de pila para el balanceo de llaves (automata_pila.py) | Cristian | Traza paso a paso; detecta llaves faltantes y sobrantes |
| 2026-11-12 | Parser de descenso recursivo y validación semántica (parser.py) | Cristian | Derivación más a la izquierda; errores con línea |
| 2026-11-12 | AFN, construcción por subconjuntos y AFD (automata.py) | Jared | AFD A/B/C; equivalencia verificada con 511 cadenas |
| 2026-11-12 | Grafo: BFS, Dijkstra, grados, ciclos, puntos críticos (grafo.py) | David | P02, P03 y P04 correctos |
| 2026-11-12 | Menú CLI, simulación de fallas e imágenes (main.py, visual.py) | Cristian | 11 opciones funcionando, no se cae con entradas inválidas |
| 2026-11-12 | Pruebas unittest P01–P17 | Equipo | 23 pruebas, todas pasan |
|  |  |  |  |
|  |  |  |  |

Evidencias generadas: `salida_menu.txt` (salida de todas las opciones del menú) y `salida_pruebas.txt` (resultado de las pruebas).
