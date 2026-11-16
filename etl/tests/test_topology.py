import unittest

from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid

from etl.topology import (
    Tolerances,
    audit_partition,
    metric_area_km2,
    reconcile_partition,
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


if __name__ == "__main__":
    unittest.main()
