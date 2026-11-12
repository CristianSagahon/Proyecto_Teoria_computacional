"""
test_casos.py - Pruebas automáticas (unittest) de los casos P01 a P17.

Ejecutar desde la carpeta 02_Codigo:
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

CARPETA_CODIGO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CARPETA_CODIGO)

from main import procesar_red, simular_fallas          # noqa: E402
import automata                                         # noqa: E402

CARPETA_EJEMPLOS = os.path.join(CARPETA_CODIGO, "ejemplos")


def leer(nombre):
    with open(os.path.join(CARPETA_EJEMPLOS, nombre), encoding="utf-8") as f:
        return f.read()


class PruebasRedEjemplo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.carga = procesar_red(leer("red_ejemplo.txt"))
        cls.grafo = cls.carga.grafo

    def test_P01_red_aceptada(self):
        self.assertTrue(self.carga.aceptada, self.carga.errores)
        self.assertEqual(len(self.grafo.nodos()), 7)
        self.assertEqual(len(self.grafo.aristas()), 7)

    def test_P02_ruta_mas_corta(self):
        distancia, ruta, _ = self.grafo.dijkstra("PC1", "SRV1")
        self.assertEqual(ruta, ["PC1", "SW1", "PC2", "DB1", "SRV1"])
        self.assertEqual(distancia, 9)

    def test_P03_ciclos(self):
        self.assertTrue(self.grafo.tiene_ciclo())
        ciclos = self.grafo.encontrar_ciclos()
        self.assertEqual(ciclos, [["R1", "SW1", "PC2", "DB1", "SRV1", "SW2", "R1"]])

    def test_P04_puntos_criticos(self):
        criticos, detalle = self.grafo.puntos_criticos()
        self.assertEqual(criticos, ["SW1"])
        self.assertIn(["PC1"], detalle["SW1"])     # PC1 queda solo

    def test_P05_pings_falla(self):
        resultado = automata.procesar_pings("PC2 OK\nPC2 OK\nPC2 TIMEOUT\nPC2 TIMEOUT\n")
        self.assertEqual(resultado["historial"]["PC2"], "oott")
        estado, aceptada, _ = resultado["resultados"]["PC2"]
        self.assertTrue(aceptada)
        self.assertEqual(estado, "Falla")

    def test_P06_pings_activo(self):
        resultado = automata.procesar_pings("PC2 TIMEOUT\nPC2 TIMEOUT\nPC2 OK\n")
        estado, aceptada, _ = resultado["resultados"]["PC2"]
        self.assertFalse(aceptada)
        self.assertEqual(estado, "Activo")

    def test_P07_simular_falla_SW1(self):
        resumen = simular_fallas(self.grafo, ["SW1"])
        self.assertTrue(resumen["dividida"])
        self.assertEqual(len(resumen["componentes"]), 2)
        self.assertIn("PC1", resumen["sin_conexion"])
        existe, _, _ = resumen["grafo"].bfs("PC1", "R1")
        self.assertFalse(existe)

    def test_bfs_existe_ruta(self):
        existe, _, ruta = self.grafo.bfs("PC1", "DB1")
        self.assertTrue(existe)
        self.assertEqual(ruta[0], "PC1")
        self.assertEqual(ruta[-1], "DB1")

    def test_grados(self):
        grados = self.grafo.grados()
        self.assertEqual(grados["SW1"], 3)
        self.assertEqual(sum(grados.values()), 2 * len(self.grafo.aristas()))
        self.assertEqual(self.grafo.aislados(), [])


class PruebasErrores(unittest.TestCase):
    def test_P08_falta_llave_final(self):
        carga = procesar_red(leer("invalido_falta_llave.txt"))
        self.assertEqual(carga.fase_error, "pila")
        self.assertIn("nunca se cerró", carga.errores[0])
        self.assertTrue(carga.errores[-1].startswith("Línea 1"))   # el bloque de RED

    def test_P09_llave_de_mas(self):
        carga = procesar_red(leer("invalido_llave_extra.txt"))
        self.assertEqual(carga.fase_error, "pila")
        self.assertIn("sin un bloque abierto", carga.errores[0])

    def test_P10_peso_invalido(self):
        carga = procesar_red(leer("invalido_peso.txt"))
        self.assertEqual(carga.fase_error, "léxico")
        self.assertEqual(len(carga.errores), 2)          # reporta el 0 y el 05
        self.assertIn("Línea 3", carga.errores[0])
        self.assertIn("mayor que 0", carga.errores[0])
        self.assertIn("ceros a la izquierda", carga.errores[1])

    def test_P11_nombre_minusculas(self):
        carga = procesar_red(leer("invalido_minusculas.txt"))
        self.assertEqual(carga.fase_error, "léxico")
        textos = " ".join(carga.errores)
        self.assertIn("¿quisiste decir ROUTER?", textos)
        self.assertIn("'pc1' no es un nombre válido: debe iniciar con mayúscula", textos)

    def test_P12_falta_punto_y_coma(self):
        carga = procesar_red(leer("invalido_falta_punto_coma.txt"))
        self.assertEqual(carga.fase_error, "sintáctico")
        self.assertIn("Línea 4: se esperaba ';' después de PC1", carga.errores[0])

    def test_P13_enlace_inexistente(self):
        carga = procesar_red(leer("invalido_enlace_inexistente.txt"))
        self.assertEqual(carga.fase_error, "semántico")
        self.assertIn("PC9", carga.errores[0])

    def test_P14_nombre_repetido(self):
        carga = procesar_red(leer("invalido_nombre_repetido.txt"))
        self.assertEqual(carga.fase_error, "semántico")
        self.assertIn("repetido", carga.errores[0])

    def test_P15_un_dispositivo(self):
        carga = procesar_red(leer("un_dispositivo.txt"))
        self.assertTrue(carga.aceptada)
        self.assertEqual(carga.grafo.nodos(), ["R1"])
        self.assertEqual(carga.grafo.aristas(), [])
        self.assertEqual(carga.grafo.aislados(), ["R1"])

    def test_P16_archivo_vacio(self):
        for texto in ("", "   \n\n", "# solo un comentario\n"):
            carga = procesar_red(texto)
            self.assertEqual(carga.fase_error, "archivo")
            self.assertIn("vacío", carga.errores[0])

    def test_P17_ping_invalido(self):
        resultado = automata.procesar_pings(leer("pings_invalido.txt"))
        self.assertEqual(len(resultado["rechazadas"]), 2)      # "PC2 LOST" y "pc1 OK"
        self.assertIn("PC2 LOST", resultado["rechazadas"][0])
        self.assertEqual(resultado["historial"]["PC2"], "oott")
        self.assertEqual(resultado["resultados"]["PC2"][0], "Falla")

    def test_enlace_a_si_mismo(self):
        carga = procesar_red("RED { PC PC1 ; ENLACE PC1 PC1 : 2 ; }")
        self.assertEqual(carga.fase_error, "semántico")
        self.assertIn("consigo mismo", carga.errores[0])


class PruebasAutomatas(unittest.TestCase):
    def test_afd_esperado(self):
        afd = automata.AFD_ESTADO
        self.assertEqual(afd["estados"], ["A", "B", "C"])
        self.assertEqual(afd["conjuntos"]["A"], {"q0"})
        self.assertEqual(afd["conjuntos"]["B"], {"q0", "q1"})
        self.assertEqual(afd["conjuntos"]["C"], {"q0", "q1", "q2"})
        self.assertEqual(afd["transiciones"], {
            "A": {"o": "A", "t": "B"},
            "B": {"o": "A", "t": "C"},
            "C": {"o": "A", "t": "C"},
        })
        self.assertEqual(afd["finales"], {"C"})

    def test_ejemplos_cadenas(self):
        self.assertTrue(automata.simular_afd(automata.AFD_ESTADO, "ootott")[0])
        self.assertFalse(automata.simular_afd(automata.AFD_ESTADO, "ttto")[0])
        self.assertTrue(automata.simular_afn(automata.AFN_ESTADO, "ootott")[0])
        self.assertFalse(automata.simular_afn(automata.AFN_ESTADO, "ttto")[0])

    def test_equivalencia(self):
        iguales, probadas, _ = automata.verificar_equivalencia(automata.AFN_ESTADO,
                                                               automata.AFD_ESTADO)
        self.assertTrue(iguales)
        self.assertEqual(probadas, 2 ** 9 - 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
