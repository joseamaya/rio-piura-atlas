import unittest

from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Polygon

from etl.build_layers import _keep_parts, _polygonal


class TestMancha2017(unittest.TestCase):
    def test_descarta_fragmentos_pequenos(self):
        grande = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)])
        pequeno = Polygon([(2000, 0), (2010, 0), (2010, 10), (2000, 10), (2000, 0)])
        limpio = _keep_parts(MultiPolygon([grande, pequeno]), 5_000)
        self.assertIsNotNone(limpio)
        self.assertEqual(limpio.geom_type, "Polygon")
        self.assertAlmostEqual(limpio.area, 1_000_000, places=0)

    def test_si_todo_es_pequeno_devuelve_none(self):
        pequeno = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
        self.assertIsNone(_keep_parts(pequeno, 5_000))

    def test_extrae_solo_la_parte_poligonal(self):
        poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
        linea = LineString([(2, 2), (3, 3)])
        limpio = _polygonal(GeometryCollection([poly, linea]))
        self.assertIsNotNone(limpio)
        self.assertIn(limpio.geom_type, {"Polygon", "MultiPolygon"})
        self.assertAlmostEqual(limpio.area, 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
