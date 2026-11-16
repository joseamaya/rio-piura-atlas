import math
import unittest

import numpy as np

from etl.build_cortes import (
    clip_to_ring,
    distance_km,
    perpendicular,
    sample_dem,
    transect,
)
from etl.build_layers import point_in_ring, rdp


class TestGeometria(unittest.TestCase):
    def test_rdp_conserva_el_cierre(self):
        ring = [[0, 0], [1, 0], [2, 0], [2, 1], [2, 2], [1, 2], [0, 2], [0, 1], [0, 0]]
        out = rdp(ring, 0.1)
        self.assertEqual(out[0], out[-1])
        self.assertLess(len(out), len(ring))

    def test_punto_dentro_y_fuera(self):
        ring = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]
        self.assertTrue(point_in_ring(1, 1, ring))
        self.assertFalse(point_in_ring(3, 1, ring))

    def test_distancia_km(self):
        self.assertAlmostEqual(distance_km((0, 0), (1, 0)), 111.32, places=1)

    def test_perpendicular(self):
        px, py = perpendicular((0, 0), (1, 0), 0)
        self.assertAlmostEqual(px, 0.0, places=6)
        self.assertAlmostEqual(py, 1.0, places=6)

    def test_transecto_centrado(self):
        a, b = transect(-80.0, -5.0, (0.0, 1.0), 24.0)
        self.assertAlmostEqual((a[0] + b[0]) / 2, -80.0, places=6)
        self.assertAlmostEqual((a[1] + b[1]) / 2, -5.0, places=6)
        self.assertGreater(distance_km(a, b), 23.9)

    def test_recorte_a_la_cuenca(self):
        ring = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]
        a, b = clip_to_ring((-1, 1), (3, 1), ring, steps=200)
        self.assertGreaterEqual(a[0], 0)
        self.assertLessEqual(b[0], 2)
        self.assertAlmostEqual(a[1], 1.0)
        self.assertAlmostEqual(b[1], 1.0)

    def test_muestreo_bilineal(self):
        dem = np.array([[0.0, 10.0], [20.0, 30.0]])
        # lon0, lon1, lat0(norte), lat1(sur)
        self.assertAlmostEqual(sample_dem(dem, 0, 1, 1, 0, 0.5, 0.5), 15.0)
        self.assertAlmostEqual(sample_dem(dem, 0, 1, 1, 0, 0, 1), 0.0)
        self.assertAlmostEqual(sample_dem(dem, 0, 1, 1, 0, 1, 0), 30.0)

    def test_muestreo_fuera_devuelve_nan(self):
        dem = np.zeros((2, 2))
        self.assertTrue(math.isnan(sample_dem(dem, 0, 1, 1, 0, 2, 2)))


if __name__ == "__main__":
    unittest.main()
