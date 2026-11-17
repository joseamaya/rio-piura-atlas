import json
import unittest
from pathlib import Path

import yaml
from shapely.geometry import LineString, Point, shape

from etl.topology import Tolerances, audit_partition

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "web" / "public" / "data"
RAW = ROOT / "data" / "raw"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class TestDatosPublicados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cuenca_feature = load("cuenca.geojson")["features"][0]
        cls.cuenca = shape(cls.cuenca_feature["geometry"])
        cls.subs_features = load("subcuencas.geojson")["features"]
        cls.subs = [shape(f["geometry"]) for f in cls.subs_features]
        cls.red = [shape(f["geometry"]) for f in load("red_hidrica.geojson")["features"]]
        cls.cortes = load("cortes.geojson")["features"]
        cls.perfiles = load("cortes_perfiles.json")

    def test_cuenca_y_subcuencas_validas(self):
        self.assertTrue(self.cuenca.is_valid)
        self.assertTrue(all(geom.is_valid for geom in self.subs))

    def test_areas_coherentes(self):
        declared = self.cuenca_feature["properties"]["area_km2"]
        sum_subs = sum(
            f["properties"]["area_km2"] for f in self.subs_features
        )
        self.assertAlmostEqual(sum_subs, declared, delta=declared * 0.005)

    def test_particion_limpia(self):
        named = [
            (f["properties"]["nombre"], shape(f["geometry"]))
            for f in self.subs_features
        ]
        report = audit_partition(self.cuenca, named, Tolerances())
        self.assertEqual(report.errors, [])
        self.assertEqual(report.overlap_pairs, 0)
        self.assertEqual(report.outside_total_km2, 0.0)
        self.assertEqual(report.gap_total_km2, 0.0)

    def test_bajo_piura_es_derivado(self):
        bajo = next(
            f for f in self.subs_features
            if f["properties"]["nombre"] == "Bajo Piura"
        )
        self.assertEqual(bajo["properties"]["fuente"], "bajo-piura-derivado")
        sources = yaml.safe_load(
            (ROOT / "data" / "sources.yml").read_text(encoding="utf-8")
        )["fuentes"]
        source = next(s for s in sources if s["id"] == "bajo-piura-derivado")
        self.assertIn("Río Piura Atlas", source["institucion"])
        self.assertEqual(source["tipo"], "elaboracion_propia")
        self.assertEqual(source["certeza"], "derivado")

    def test_red_dentro_de_cuenca(self):
        for line in self.red:
            # El redondeo a 6 decimales puede dejar milímetros fuera del borde.
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
            self.assertTrue(
                any(corte.intersects(line) for line in lines),
                feature["properties"]["id"],
            )

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

    def test_flood_publica_solo_observado_y_por_fecha(self):
        total = 0.0
        for feature in load("flood_2017.geojson")["features"]:
            props = feature["properties"]
            self.assertEqual(props["clase"], "Flooded Area")
            obs = props["observaciones"]
            self.assertTrue(obs)
            dates = [o["fecha"] for o in obs]
            expected = dates[0] if len(dates) == 1 else f"{min(dates)}/{max(dates)}"
            self.assertEqual(props["fecha"], expected)
            observed_max = max(o["area_original_km2"] for o in obs)
            observed_sum = sum(o["area_original_km2"] for o in obs)
            self.assertGreaterEqual(props["area_km2"], observed_max * 0.98)
            self.assertAlmostEqual(
                props["area_observaciones_sum_km2"], observed_sum, delta=0.01
            )
            self.assertAlmostEqual(
                props["area_union_original_km2"],
                observed_sum - props["solapamiento_observaciones_km2"],
                delta=0.02,
            )
            self.assertAlmostEqual(
                props["area_original_km2"], props["area_union_original_km2"], delta=0.001
            )
            self.assertAlmostEqual(
                props["area_publicada_utm_km2"], props["area_km2"], delta=0.001
            )
            self.assertGreater(
                props["area_publicada_geodesica_km2"], props["area_km2"]
            )
            self.assertLessEqual(
                props["area_filtrada_km2"], props["area_union_original_km2"] + 0.01
            )
            self.assertAlmostEqual(
                props["area_simplificada_km2"], props["area_km2"], delta=0.01
            )
            self.assertIn("no es una mancha simultánea", props["metodo"])
            self.assertIsInstance(props["reparaciones"], list)
            total += props["area_km2"]
        self.assertGreaterEqual(total, 500)
        self.assertLessEqual(total, 600)

    def test_fidelidad_declarada_en_limits(self):
        data = json.loads((RAW / "limits.json").read_text(encoding="utf-8"))
        rec = data["reconciliacion"]
        self.assertEqual(rec["crs_metrico"], "EPSG:32717")
        self.assertEqual(len(rec["fidelidad"]), 9)
        self.assertIn("reasignacion", rec)
        self.assertIn("reparaciones", rec)
        for name, item in rec["fidelidad"].items():
            self.assertIn("fuente_a_reconciliada", item, name)
            full = item["fuente_a_reconciliada"]
            self.assertGreater(full["iou"], 0.98, name)
            self.assertGreaterEqual(full["hausdorff_m"], 0.0, name)
            self.assertGreaterEqual(full["distancia_p95_limite_m"], 0.0, name)
        self.assertGreaterEqual(
            rec["reasignacion"]["superficie_asignada_por_proximidad_km2"], 0.0
        )


if __name__ == "__main__":
    unittest.main()
