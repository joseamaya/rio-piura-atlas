import json
import math
import unittest
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "web" / "public" / "data"
RAW = ROOT / "data" / "raw"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class TestDatosPublicados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cuenca = shape(load("cuenca.geojson")["features"][0]["geometry"])
        cls.subs = [shape(f["geometry"]) for f in load("subcuencas.geojson")["features"]]
        cls.red = [shape(f["geometry"]) for f in load("red_hidrica.geojson")["features"]]
        cls.cortes = load("cortes.geojson")["features"]
        cls.perfiles = load("cortes_perfiles.json")

    def test_cuenca_y_subcuencas_validas(self):
        self.assertTrue(self.cuenca.is_valid)
        self.assertTrue(all(geom.is_valid for geom in self.subs))

    def test_areas_coherentes(self):
        declared = load("cuenca.geojson")["features"][0]["properties"]["area_km2"]
        sum_subs = sum(f["properties"]["area_km2"] for f in load("subcuencas.geojson")["features"])
        self.assertAlmostEqual(sum_subs, declared, delta=declared * 0.005)

    def test_sin_hueco_grande(self):
        gap = self.cuenca.difference(unary_union(self.subs)).area
        # grados²; 0.0002°² equivale a ~2,5 km² en esta latitud
        self.assertLess(gap, 0.0002)

    def test_red_dentro_de_cuenca(self):
        for line in self.red:
            # El redondeo a 5 decimales puede dejar milímetros fuera del borde.
            self.assertLess(line.difference(self.cuenca).length, 1e-5)

    def test_cortes_cruzan_rio(self):
        network = json.loads((RAW / "network.json").read_text(encoding="utf-8"))["rivers"]
        lines = [
            LineString(r["coords"])
            for r in network
            if r.get("upland", 0) >= 500 and len(r.get("coords", [])) >= 2
        ]
        for feature in self.cortes:
            corte = shape(feature["geometry"])
            self.assertTrue(any(corte.intersects(line) for line in lines), feature["properties"]["id"])

    def test_paso_de_perfil_no_inventa_resolucion(self):
        effective = self.perfiles["resolucion_efectiva_m"]
        for fid, perfil in self.perfiles["perfiles"].items():
            dist = perfil["dist_km"]
            paso = (dist[-1] - dist[0]) * 1000 / (len(dist) - 1)
            self.assertGreaterEqual(paso, effective * 0.9, fid)

    def test_poechos_en_el_dique(self):
        obras = load("obras.geojson")["features"]
        poechos = next(f for f in obras if f["properties"]["tipo"] == "represa")
        geom = shape(poechos["geometry"])
        self.assertEqual(geom.geom_type, "Point")
        self.assertLess(geom.distance(Point(-80.5036, -4.6686)), 0.001)


if __name__ == "__main__":
    unittest.main()
