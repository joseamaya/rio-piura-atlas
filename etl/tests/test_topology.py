import math
import unittest

from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid

from etl.topology import (
    Tolerances,
    as_polygonal,
    audit_partition,
    fidelity_metrics,
    inspect_geometry,
    metric_area_km2,
    reconcile_partition,
    repair_to_polygonal,
)

# Coordenadas dentro de la zona 17S, cerca de Piura, para que la proyección
# métrica no introduzca distorsiones absurdas.
LON = -80.70
LAT = -5.30


def box(dx: float, dy: float, size: float = 0.02) -> Polygon:
    return Polygon(
        [
            (LON + dx, LAT + dy),
            (LON + dx + size, LAT + dy),
            (LON + dx + size, LAT + dy + size),
            (LON + dx, LAT + dy + size),
            (LON + dx, LAT + dy),
        ]
    )


class TestAuditoriaTopologica(unittest.TestCase):
    def test_solapamiento_entre_dos_subcuencas(self):
        a = box(0.0, 0.0, 0.02)
        b = box(0.01, 0.0, 0.02)
        basin = make_valid(unary_union([a, b]))
        report = audit_partition(basin, [("A", a), ("B", b)])
        overlap = [f for f in report.findings if f.kind == "overlap"]
        self.assertEqual(report.overlap_pairs, 1)
        self.assertGreater(report.overlap_total_km2, 0.01)
        self.assertTrue(overlap)
        self.assertEqual(overlap[0].severity, "error")
        self.assertEqual(set(overlap[0].names), {"A", "B"})

    def test_hueco_entre_dos_subcuencas(self):
        a = box(0.0, 0.0, 0.02)
        b = box(0.03, 0.0, 0.02)
        basin = box(-0.01, -0.01, 0.06)
        report = audit_partition(basin, [("A", a), ("B", b)])
        gaps = [f for f in report.findings if f.kind == "gap"]
        self.assertTrue(gaps)
        self.assertGreater(report.gap_total_km2, 0.01)
        self.assertGreater(report.gap_max_km2, 0.0)

    def test_subcuenca_parcialmente_fuera(self):
        a = box(0.0, 0.0, 0.02)
        b = box(0.02, 0.0, 0.02)
        basin = box(0.0, 0.0, 0.02)
        report = audit_partition(basin, [("A", a), ("B", b)])
        outside = [f for f in report.findings if f.kind == "outside"]
        self.assertTrue(outside)
        self.assertIn("B", [name for f in outside for name in f.names])
        self.assertGreater(report.outside_total_km2, 0.01)

    def test_subcuencas_contiguas_sin_hallazgos(self):
        a = box(0.0, 0.0, 0.02)
        b = box(0.02, 0.0, 0.02)
        basin = make_valid(unary_union([a, b]))
        report = audit_partition(basin, [("A", a), ("B", b)])
        self.assertEqual([f for f in report.findings if f.severity == "error"], [])
        self.assertEqual(report.overlap_pairs, 0)
        self.assertEqual(report.outside_total_km2, 0.0)
        self.assertEqual(report.gap_total_km2, 0.0)

    def test_multipolygon_no_falso_hueco(self):
        a1 = box(0.0, 0.0, 0.01)
        a2 = box(0.02, 0.0, 0.01)
        a = MultiPolygon([a1, a2])
        basin = box(-0.01, -0.01, 0.05)
        b = make_valid(basin.difference(a))
        report = audit_partition(basin, [("A", a), ("B", b)])
        self.assertEqual([f for f in report.findings if f.kind == "hole"], [])
        self.assertEqual(report.overlap_pairs, 0)
        self.assertEqual(report.gap_total_km2, 0.0)

    def test_agujero_interior_no_justificado(self):
        basin = box(-0.01, -0.01, 0.05)
        shell = [
            (LON, LAT),
            (LON + 0.03, LAT),
            (LON + 0.03, LAT + 0.03),
            (LON, LAT + 0.03),
            (LON, LAT),
        ]
        hole = [
            (LON + 0.01, LAT + 0.01),
            (LON + 0.02, LAT + 0.01),
            (LON + 0.02, LAT + 0.02),
            (LON + 0.01, LAT + 0.02),
            (LON + 0.01, LAT + 0.01),
        ]
        a = Polygon(shell, [hole])
        report = audit_partition(basin, [("A", a)])
        holes = [f for f in report.findings if f.kind == "hole"]
        self.assertEqual(len(holes), 1)
        self.assertEqual(holes[0].severity, "error")

    def test_agujero_justificado_es_aviso(self):
        basin = box(-0.01, -0.01, 0.05)
        shell = [
            (LON, LAT),
            (LON + 0.03, LAT),
            (LON + 0.03, LAT + 0.03),
            (LON, LAT + 0.03),
            (LON, LAT),
        ]
        hole = [
            (LON + 0.01, LAT + 0.01),
            (LON + 0.02, LAT + 0.01),
            (LON + 0.02, LAT + 0.02),
            (LON + 0.01, LAT + 0.02),
            (LON + 0.01, LAT + 0.01),
        ]
        a = Polygon(shell, [hole])
        report = audit_partition(basin, [("A", a)], hole_notes={"A": "lago documentado"})
        holes = [f for f in report.findings if f.kind == "hole"]
        self.assertEqual(len(holes), 1)
        self.assertEqual(holes[0].severity, "warning")
        self.assertIn("lago", holes[0].detail)

    def test_tolerancia_distingue_sliver_de_error(self):
        # Solape pequeño (~0,006 km²): aviso, no error.
        a = box(0.0, 0.0, 0.001)
        b = box(0.0005, 0.0, 0.001)
        basin = make_valid(unary_union([a, b]))
        report = audit_partition(basin, [("A", a), ("B", b)])
        overlap = [f for f in report.findings if f.kind == "overlap"]
        self.assertTrue(overlap)
        self.assertEqual(overlap[0].severity, "warning")

        # Solape grande (~1 km²): error.
        c = box(0.0, 0.0, 0.02)
        d = box(0.01, 0.0, 0.02)
        basin2 = make_valid(unary_union([c, d]))
        report2 = audit_partition(basin2, [("C", c), ("D", d)])
        overlap2 = [f for f in report2.findings if f.kind == "overlap"]
        self.assertTrue(overlap2)
        self.assertEqual(overlap2[0].severity, "error")

    def test_reconciliacion_elimina_solapamientos_y_huecos(self):
        a = box(0.0, 0.0, 0.02)
        b = box(0.01, 0.0, 0.02)
        basin = box(-0.01, -0.01, 0.05)
        result = reconcile_partition(basin, [("A", a), ("B", b)])
        report = audit_partition(basin, result.geoms, Tolerances())
        self.assertEqual(report.errors, [])
        self.assertEqual(report.overlap_pairs, 0)
        self.assertEqual(report.outside_total_km2, 0.0)
        self.assertEqual(report.gap_total_km2, 0.0)
        self.assertAlmostEqual(
            sum(metric_area_km2(geom) for _, geom in result.geoms),
            metric_area_km2(basin),
            places=4,
        )

    def test_reconciliacion_rechaza_agujeros(self):
        basin = box(-0.01, -0.01, 0.05)
        shell = [
            (LON, LAT),
            (LON + 0.03, LAT),
            (LON + 0.03, LAT + 0.03),
            (LON, LAT + 0.03),
            (LON, LAT),
        ]
        hole = [
            (LON + 0.01, LAT + 0.01),
            (LON + 0.02, LAT + 0.01),
            (LON + 0.02, LAT + 0.02),
            (LON + 0.01, LAT + 0.02),
            (LON + 0.01, LAT + 0.01),
        ]
        with self.assertRaises(ValueError):
            reconcile_partition(basin, [("A", Polygon(shell, [hole]))])


class TestValidacionAntesDeReparar(unittest.TestCase):
    def test_bowtie_se_reporta_antes_de_reparar(self):
        bow = Polygon([(LON, LAT), (LON + 0.02, LAT + 0.02),
                       (LON + 0.02, LAT), (LON, LAT + 0.02), (LON, LAT)])
        self.assertFalse(bow.is_valid)
        self.assertFalse(inspect_geometry(bow, "bow").valid)
        with self.assertRaises(ValueError):
            as_polygonal(bow)

        basin = Polygon([
            (LON - 0.01, LAT - 0.01),
            (LON + 0.03, LAT - 0.01),
            (LON + 0.03, LAT + 0.03),
            (LON - 0.01, LAT + 0.03),
            (LON - 0.01, LAT - 0.01),
        ])
        report = audit_partition(basin, [("A", bow)])
        invalid = [f for f in report.findings if f.kind == "invalid"]
        repairs = [f for f in report.findings if f.kind == "repair"]
        self.assertTrue(invalid)
        self.assertEqual(invalid[0].severity, "error")
        self.assertTrue(repairs)
        self.assertTrue(report.repairs)
        self.assertTrue(report.repairs[0].repaired)
        with self.assertRaises(ValueError):
            reconcile_partition(basin, [("A", bow)])

    def test_anillo_invalido_se_reporta(self):
        # Anillo que se cruza en un punto intermedio: no es un polígono simple.
        ring = Polygon([
            (LON, LAT),
            (LON + 0.03, LAT),
            (LON + 0.03, LAT + 0.02),
            (LON + 0.01, LAT + 0.02),
            (LON + 0.01, LAT + 0.03),
            (LON + 0.01, LAT + 0.02),
            (LON, LAT + 0.02),
            (LON, LAT),
        ])
        self.assertFalse(ring.is_valid)
        self.assertFalse(inspect_geometry(ring, "anillo").valid)

    def test_geometria_vacia_no_produce_nan(self):
        empty = Polygon()
        audit = inspect_geometry(empty, "vacía")
        self.assertTrue(audit.empty)
        self.assertEqual(metric_area_km2(empty), 0.0)
        basin = box(-0.01, -0.01, 0.05)
        report = audit_partition(basin, [("A", empty)])
        self.assertTrue([f for f in report.findings if f.kind == "empty"])
        self.assertFalse(any(math.isnan(f.area_km2) for f in report.findings))

    def test_multipolygon_valido_sin_falsos_positivos(self):
        a = box(0.0, 0.0, 0.01)
        b = box(0.02, 0.0, 0.01)
        multi = MultiPolygon([a, b])
        audit = inspect_geometry(multi, "multi")
        self.assertTrue(audit.valid)
        self.assertFalse(audit.repaired)
        report = audit_partition(box(-0.01, -0.01, 0.05), [("A", multi)])
        self.assertFalse([f for f in report.findings if f.kind in {"invalid", "empty"}])

    def test_geometrycollection_registra_descarte(self):
        poly = box(0.0, 0.0, 0.02)
        line = LineString([(LON + 0.05, LAT), (LON + 0.06, LAT)])
        collection = GeometryCollection([poly, line])
        with self.assertRaises(ValueError):
            as_polygonal(collection)
        fixed, audit = repair_to_polygonal(collection, "colección", allow_repair=True)
        self.assertIsNotNone(fixed)
        self.assertTrue(audit.repaired)
        self.assertEqual(audit.repaired_type, "Polygon")
        self.assertEqual(audit.discarded_parts, 1)
        self.assertIn("LineString", audit.discarded_types)
        self.assertGreater(audit.discarded_length_m, 0)

    def test_geometria_no_poligonal_se_reporta(self):
        basin = box(-0.01, -0.01, 0.05)
        line = LineString([(LON, LAT), (LON + 0.01, LAT)])
        report = audit_partition(basin, [("A", line)])
        errors = [f for f in report.findings if f.kind == "repair" and f.severity == "error"]
        self.assertTrue(errors)

    def test_poligono_valido_no_se_repara(self):
        poly = box(0.0, 0.0, 0.02)
        fixed, audit = repair_to_polygonal(poly, "válido", allow_repair=True)
        self.assertIs(fixed, poly)
        self.assertFalse(audit.repaired)
        self.assertTrue(audit.valid)

    def test_area_metrica_no_usa_grados(self):
        # 0,01° × 0,01° cerca de Piura mide ~1,23 km², no 0,0001.
        square = box(0.0, 0.0, 0.01)
        area = metric_area_km2(square)
        self.assertGreater(area, 1.0)
        self.assertLess(area, 1.5)


class TestFidelidad(unittest.TestCase):
    def test_geometrias_identicas(self):
        geom = box(0.0, 0.0, 0.02)
        metrics = fidelity_metrics(geom, geom)
        self.assertAlmostEqual(metrics.delta_area_km2, 0.0, places=6)
        self.assertAlmostEqual(metrics.iou, 1.0, places=6)
        self.assertAlmostEqual(metrics.symmetric_difference_km2, 0.0, places=6)
        self.assertAlmostEqual(metrics.hausdorff_m, 0.0, places=3)
        self.assertAlmostEqual(metrics.boundary_mean_m, 0.0, places=3)

    def test_desplazamiento_produce_metricas(self):
        source = box(0.0, 0.0, 0.02)
        target = box(0.001, 0.0, 0.02)  # ~111 m al este
        metrics = fidelity_metrics(source, target)
        self.assertLess(metrics.iou, 1.0)
        self.assertGreater(metrics.symmetric_difference_km2, 0.0)
        self.assertGreater(metrics.hausdorff_m, 80.0)
        self.assertLess(metrics.hausdorff_m, 150.0)
        self.assertGreater(metrics.boundary_mean_m, 0.0)

    def test_cambio_de_area(self):
        source = box(0.0, 0.0, 0.02)
        target = box(0.0, 0.0, 0.03)
        metrics = fidelity_metrics(source, target)
        self.assertGreater(metrics.delta_area_km2, 0.0)
        self.assertGreater(metrics.delta_area_pct, 0.0)
        self.assertLess(metrics.iou, 1.0)

    def test_reconciliacion_registra_proximidad(self):
        # A y B dejan una franja central sin cubrir; el hueco se asigna por
        # proximidad y debe quedar registrado con su área.
        basin = box(0.0, 0.0, 0.06)
        a = box(0.0, 0.0, 0.02)
        b = box(0.04, 0.0, 0.02)
        result = reconcile_partition(basin, [("A", a), ("B", b)])
        self.assertGreater(result.proximity_faces, 0)
        self.assertGreater(result.proximity_area_km2, 0.0)
        self.assertGreaterEqual(result.proximity_max_distance_m, 0.0)
        self.assertAlmostEqual(
            sum(result.area_changes_km2.values()),
            result.proximity_area_km2 + result.overlap_assigned_km2
            - sum(result.area_before_km2.values()),
            places=2,
        )

    def test_hausdorff_extremo_no_es_la_unica_medida(self):
        source = box(0.0, 0.0, 0.02)
        far = box(0.10, 0.10, 0.001)
        target = MultiPolygon([source, far])
        metrics = fidelity_metrics(source, target)
        self.assertGreater(metrics.hausdorff_m, 1000.0)
        self.assertLess(metrics.boundary_p95_m, 100.0)


if __name__ == "__main__":
    unittest.main()
