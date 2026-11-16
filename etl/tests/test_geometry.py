import math
import unittest

import numpy as np
from shapely.geometry import LineString, Point, Polygon

from etl.build_cortes import (
    clip_to_basin,
    distance_km,
    effective_resolution_m,
    nearest_segment,
    perpendicular,
    sample_dem,
    transect,
)
from etl.build_layers import _geom_from_record, _json_geom, point_in_ring, rdp
from etl.download_ana import area_km2, polygon_record
from etl.download_osm_water import relation_rings, ring_area_km2


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
        a, b = clip_to_basin((-1, 1), (3, 1), Polygon(ring))
        self.assertGreaterEqual(a[0], 0)
        self.assertLessEqual(b[0], 2)
        self.assertAlmostEqual(a[1], 1.0)
        self.assertAlmostEqual(b[1], 1.0)

    def test_recorte_fuera_devuelve_none(self):
        ring = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]
        self.assertIsNone(clip_to_basin((-1, -1), (-1, 3), Polygon(ring)))

    def test_muestreo_bilineal(self):
        dem = np.array([[0.0, 10.0], [20.0, 30.0]])
        # lon0, lon1, lat0(norte), lat1(sur)
        self.assertAlmostEqual(sample_dem(dem, 0, 1, 1, 0, 0.5, 0.5), 15.0)
        self.assertAlmostEqual(sample_dem(dem, 0, 1, 1, 0, 0, 1), 0.0)
        self.assertAlmostEqual(sample_dem(dem, 0, 1, 1, 0, 1, 0), 30.0)

    def test_muestreo_fuera_devuelve_nan(self):
        dem = np.zeros((2, 2))
        self.assertTrue(math.isnan(sample_dem(dem, 0, 1, 1, 0, 2, 2)))

    def test_resolucion_efectiva(self):
        dem = np.zeros((3, 4))
        dx, dy = effective_resolution_m(dem, -80.0, -79.0, -5.0, -6.0)
        self.assertGreater(dx, 30_000)
        self.assertGreater(dy, 50_000)

    def test_rio_mas_cercano_y_transecto(self):
        rivers = [
            {"upland": 1000, "coords": [[0.0, 0.0], [2.0, 0.0]]},
            {"upland": 1000, "coords": [[0.0, 1.0], [2.0, 1.0]]},
        ]
        p1, p2, nearest = nearest_segment(rivers, 1.0, 0.2)
        self.assertEqual(tuple(p1), (0.0, 0.0))
        self.assertEqual(tuple(p2), (2.0, 0.0))
        self.assertAlmostEqual(nearest[0], 1.0)
        self.assertAlmostEqual(nearest[1], 0.0)
        perp = perpendicular(p1, p2, 0.2)
        a, b = transect(nearest[0], nearest[1], perp, 2.0)
        self.assertTrue(LineString([a, b]).intersects(LineString([p1, p2])))

    def test_area_geodesica(self):
        square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
        self.assertGreater(area_km2(square), 12_000)
        self.assertLess(area_km2(square), 12_500)


class TestPoligonos(unittest.TestCase):
    def test_conserva_agujeros(self):
        outer = [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]]
        hole = [[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]]
        geom = _geom_from_record({"ring": outer, "holes": [hole]})
        self.assertIsNotNone(geom)
        self.assertEqual(len(geom.interiors), 1)
        out = _json_geom(geom)
        self.assertEqual(out["type"], "Polygon")
        self.assertEqual(len(out["coordinates"]), 2)

    def test_conserva_multipolygon(self):
        a = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
        b = [[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]
        geom = _geom_from_record({"polygons": [{"ring": a}, {"ring": b}]})
        self.assertEqual(geom.geom_type, "MultiPolygon")
        self.assertEqual(len(geom.geoms), 2)

    def test_relacion_osm_conserva_huecos(self):
        def member(role, coords):
            return {"role": role, "geometry": [{"lon": x, "lat": y} for x, y in coords]}

        element = {
            "type": "relation",
            "members": [
                member("outer", [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]),
                member("inner", [(1, 1), (3, 1), (3, 3), (1, 3), (1, 1)]),
            ],
        }
        rings = relation_rings(element)
        self.assertEqual(len(rings), 1)
        self.assertEqual(len(rings[0]["holes"]), 1)
        outer_area = ring_area_km2(rings[0]["ring"])
        with_hole = ring_area_km2(rings[0]["ring"], rings[0]["holes"])
        self.assertLess(with_hole, outer_area)

    def test_polygon_record_conserva_hueco(self):
        poly = Polygon(
            [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)],
            [[(1, 1), (3, 1), (3, 3), (1, 3), (1, 1)]],
        )
        record = polygon_record(poly)
        self.assertEqual(len(record["holes"]), 1)
        self.assertEqual(record["ring"][0], record["ring"][-1])


if __name__ == "__main__":
    unittest.main()
