# Casos de prueba – Proyecto 4

Se ejecutan automáticamente con `python -m unittest discover -s tests -v` (desde `02_Codigo`).
Resultado: **23 pruebas, 23 correctas** (P01–P17 + 5 pruebas extra de grafo y autómatas + ENLACE a sí mismo).

| ID | Entrada | Fase / modelo | Resultado esperado | Resultado obtenido | ¿Pasa? |
|----|---------|---------------|--------------------|--------------------|--------|
| P01 | `ejemplos/red_ejemplo.txt` | Todas las fases | Aceptada, 7 nodos y 7 aristas | Aceptada, 7 nodos y 7 aristas | Sí |
| P02 | Ruta más corta PC1→SRV1 | Dijkstra | PC1→SW1→PC2→DB1→SRV1, 9 ms | PC1→SW1→PC2→DB1→SRV1, 9 ms | Sí |
| P03 | Ciclos en la red de ejemplo | DFS | Hay ciclo R1-SW1-PC2-DB1-SRV1-SW2-R1 | 1 ciclo: R1-SW1-PC2-DB1-SRV1-SW2-R1 | Sí |
| P04 | Puntos críticos | Componentes conexos | Solo SW1 (PC1 queda aislado) | SW1; sin SW1 quedan {R1,SW2,SRV1,DB1,PC2} y {PC1} | Sí |
| P05 | PC2: OK OK TIMEOUT TIMEOUT | AFD | Acepta → Falla | `oott`: A→A→A→B→C, acepta, Falla | Sí |
| P06 | PC2: TIMEOUT TIMEOUT OK | AFD | Rechaza → Activo | `tto`: A→B→C→A, rechaza, Activo | Sí |
| P07 | Falla de SW1 | Grafo sin nodos en Falla | La red se divide, PC1 sin conexión | 2 componentes, PC1 aislado | Sí |
| P08 | `invalido_falta_llave.txt` | Autómata de pila | Error: bloque abierto sin cerrar | "Línea 1: el bloque '{' de RED se abrió y nunca se cerró" | Sí |
| P09 | `invalido_llave_extra.txt` | Autómata de pila | Error: cierre sin bloque abierto | "Línea 5: se encontró '}' sin un bloque abierto que cerrar" | Sí |
| P10 | `invalido_peso.txt` (pesos 0 y 05) | Léxico (REGEX_PESO) | Error léxico con línea | 2 errores en línea 3: "mayor que 0" y "ceros a la izquierda" | Sí |
| P11 | `invalido_minusculas.txt` (router, pc1) | Léxico (REGEX_IDENTIFICADOR) | Error léxico | "¿quisiste decir ROUTER?" y "'pc1' … debe iniciar con mayúscula" | Sí |
| P12 | `invalido_falta_punto_coma.txt` | Parser (gramática) | Error sintáctico | "Línea 4: se esperaba ';' después de PC1" | Sí |
| P13 | `invalido_enlace_inexistente.txt` | Semántico | Error semántico | "ENLACE PC1 PC9 usa 'PC9', que no está declarado" | Sí |
| P14 | `invalido_nombre_repetido.txt` | Semántico | Error semántico | "el nombre 'PC1' está repetido" | Sí |
| P15 | `un_dispositivo.txt` | Todas | Aceptada, 0 aristas, nodo aislado | 1 nodo (R1), 0 aristas, R1 aislado | Sí |
| P16 | `vacio.txt` (o solo comentarios) | Validación de archivo | Mensaje claro | "El archivo está vacío: no contiene ninguna definición de red" | Sí |
| P17 | `pings_invalido.txt` con "PC2 LOST" | Regex de ping + AFD | Esa línea se rechaza, el resto se procesa | Se rechazan "PC2 LOST" y "pc1 OK"; PC2 = `oott` → Falla | Sí |
| Extra | `ENLACE PC1 PC1 : 2 ;` | Semántico | Error: enlace a sí mismo | "conecta un nodo consigo mismo" | Sí |
| Extra | AFD por subconjuntos | Subconjuntos | A={q0}, B={q0,q1}, C={q0,q1,q2} | Igual al esperado | Sí |
| Extra | "ootott" / "ttto" | AFN y AFD | Acepta / rechaza | Acepta / rechaza en ambos | Sí |
| Extra | Equivalencia AFN = AFD | Simulación | Mismas cadenas aceptadas | 511 cadenas (long. 0–8) iguales | Sí |
