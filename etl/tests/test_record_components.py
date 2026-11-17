import unittest

from shapely.geometry import MultiPolygon, Polygon

from etl.topology import Tolerances, audit_components

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


class TestComponentesDeRegistro(unittest.TestCase):
    def test_componentes_separados(self):
        audit = audit_components([box(0.0, 0.0), box(0.03, 0.0)], "separados")
        self.assertEqual(audit.count, 2)
        self.assertEqual(audit.valid_count, 2)
        self.assertEqual(audit.overlap_pairs, 0)
        self.assertEqual(audit.touching_pairs, 0)
        self.assertEqual(audit.separated_pairs, 1)
        self.assertIsNotNone(audit.compound_geometry)
        self.assertEqual(audit.compound_geometry.geom_type, "MultiPolygon")
        self.assertFalse([f for f in audit.findings if f.severity == "error"])

    def test_componentes_que_comparten_limite_no_son_solapamiento(self):
        audit = audit_components([box(0.0, 0.0, 0.01), box(0.01, 0.0, 0.01)], "contacto")
        self.assertEqual(audit.overlap_pairs, 0)
        self.assertEqual(audit.touching_pairs, 1)
        self.assertFalse([f for f in audit.findings if f.kind == "overlap"])
        self.assertIsNotNone(audit.compound_geometry)

    def test_solapamiento_se_detecta_antes_de_unir(self):
        partes = [box(0.0, 0.0), box(0.01, 0.0)]
        self.assertFalse(MultiPolygon(partes).is_valid)
        audit = audit_components(partes, "solapados")
        self.assertEqual(audit.overlap_pairs, 1)
        self.assertGreater(audit.overlap_km2, Tolerances().error_km2)
        overlap = [f for f in audit.findings if f.kind == "overlap"]
        self.assertTrue(overlap)
        self.assertEqual(overlap[0].severity, "error")
        # La unión posterior es válida, pero el defecto original ya quedó registrado.
        self.assertIsNotNone(audit.compound_geometry)
        self.assertTrue(audit.compound_geometry.is_valid)

    def test_poligono_individual_invalido(self):
        bow = Polygon(
            [
                (LON, LAT),
                (LON + 0.02, LAT + 0.02),
                (LON + 0.02, LAT),
                (LON, LAT + 0.02),
                (LON, LAT),
            ]
        )
        self.assertFalse(bow.is_valid)
        audit = audit_components([bow], "bow", allow_repair=False)
        self.assertEqual(audit.invalid_count, 1)
        self.assertEqual(audit.repaired_count, 0)
        self.assertEqual(audit.discarded_count, 1)
        self.assertIsNone(audit.compound_geometry)
        self.assertTrue([f for f in audit.findings if f.kind == "invalid"])

        reparado = audit_components([bow], "bow-reparado", allow_repair=True)
        self.assertEqual(reparado.invalid_count, 1)
        self.assertEqual(reparado.repaired_count, 1)
        self.assertEqual(reparado.valid_count, 1)
        self.assertIsNotNone(reparado.compound_geometry)
        self.assertTrue([f for f in reparado.findings if f.kind == "repair"])

    def test_componente_vacio(self):
        audit = audit_components([Polygon()], "vacío")
        self.assertEqual(audit.empty_count, 1)
        self.assertEqual(audit.discarded_count, 1)
        self.assertIsNone(audit.compound_geometry)
        self.assertTrue([f for f in audit.findings if f.kind == "empty"])

    def test_conjunto_que_genera_compuesto_invalido(self):
        partes = [box(0.0, 0.0, 0.02), box(0.01, 0.0, 0.02)]
        self.assertFalse(MultiPolygon(partes).is_valid)
        audit = audit_components(partes, "compuesto")
        self.assertEqual(audit.overlap_pairs, 1)
        self.assertIsNotNone(audit.compound_geometry)
        self.assertTrue(audit.compound_geometry.is_valid)
        self.assertTrue([f for f in audit.findings if f.kind == "overlap"])

    def test_un_solo_componente_valido_no_genera_hallazgos(self):
        parte = box(0.0, 0.0)
        audit = audit_components([parte], "simple")
        self.assertEqual(audit.count, 1)
        self.assertEqual(audit.valid_count, 1)
        self.assertEqual(audit.findings, [])
        self.assertTrue(audit.compound_geometry.equals(parte))


if __name__ == "__main__":
    unittest.main()
