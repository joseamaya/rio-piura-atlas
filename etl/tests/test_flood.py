import unittest

from pyproj import Transformer
from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Polygon

from etl.build_layers import (
    _filter_flood_geometry,
    _flood_date_sensor_summary,
    _flood_fidelity,
    _flood_hausdorff_override,
    _flood_observations,
    _group_flood_records,
    _keep_parts,
    _polygonal,
    _publish_flood_geometry,
    _sensor_label,
    _simplify_flood_geometry,
)
# Coordenadas en EPSG:32717, cerca de Piura, para que las áreas y distancias
# sintéticas sean comparables con las del ETL real.
X0 = 540_000.0
Y0 = 9_400_000.0


def utm_box(dx: float, dy: float, size: float = 1000.0) -> Polygon:
    return Polygon(
        [
            (X0 + dx, Y0 + dy),
            (X0 + dx + size, Y0 + dy),
            (X0 + dx + size, Y0 + dy + size),
            (X0 + dx, Y0 + dy + size),
            (X0 + dx, Y0 + dy),
        ]
    )


def record(geom, fecha, sensor):
    return {"geom": geom, "fecha": fecha, "sensor": sensor}


class TestUnionObservaciones(unittest.TestCase):
    def test_dos_poligonos_sin_solapamiento(self):
        records = [
            record(utm_box(0, 0), "2017-03-26", "A"),
            record(utm_box(2000, 0), "2017-03-26", "A"),
        ]
        observaciones, _, suma, solape, union = _flood_observations(records)
        self.assertEqual(len(observaciones), 1)
        self.assertAlmostEqual(suma, 2.0, places=3)
        self.assertAlmostEqual(solape, 0.0, places=3)
        self.assertAlmostEqual(union.area / 1e6, 2.0, places=3)

    def test_dos_observaciones_con_solapamiento(self):
        records = [
            record(utm_box(0, 0), "2017-03-26", "A"),
            record(utm_box(500, 0), "2017-03-30", "B"),
        ]
        observaciones, _, suma, solape, union = _flood_observations(records)
        self.assertEqual(len(observaciones), 2)
        self.assertAlmostEqual(suma, 2.0, places=3)
        self.assertAlmostEqual(solape, 0.5, places=3)
        self.assertAlmostEqual(union.area / 1e6, 1.5, places=3)
        self.assertGreater(suma, union.area / 1e6)

    def test_dos_fechas_no_se_suman_como_si_fueran_simultaneas(self):
        records = [
            record(utm_box(0, 0), "2017-03-26", "A"),
            record(utm_box(2000, 0), "2017-03-30", "B"),
        ]
        observaciones, _, suma, solape, union = _flood_observations(records)
        self.assertEqual(len(observaciones), 2)
        self.assertAlmostEqual(suma, 2.0, places=3)
        self.assertAlmostEqual(solape, 0.0, places=3)
        self.assertAlmostEqual(union.area / 1e6, 2.0, places=3)
        fecha, fecha_texto, sensores = _flood_date_sensor_summary(observaciones)
        self.assertEqual(fecha, "2017-03-26/2017-03-30")
        self.assertIn("26–30 de marzo de 2017", fecha_texto)
        self.assertIn("A", sensores)
        self.assertIn("B", sensores)


class TestFechasSensores(unittest.TestCase):
    def test_conserva_fecha_y_sensor(self):
        observaciones = [
            {"fecha": "2017-03-26", "sensor": "Radarsat", "area_original_km2": 1.0, "partes": 1},
            {"fecha": "2017-03-30", "sensor": "Cosmo-SkyMed", "area_original_km2": 1.0, "partes": 1},
        ]
        fecha, fecha_texto, sensores = _flood_date_sensor_summary(observaciones)
        self.assertEqual(fecha, "2017-03-26/2017-03-30")
        self.assertEqual(fecha_texto, "26–30 de marzo de 2017")
        self.assertEqual(sensores, "Radarsat (26/03); Cosmo-SkyMed (30/03)")

    def test_fecha_ausente_no_se_infiere(self):
        observaciones = [
            {"fecha": None, "sensor": "Radarsat", "area_original_km2": 1.0, "partes": 1},
        ]
        fecha, fecha_texto, sensores = _flood_date_sensor_summary(observaciones)
        self.assertIsNone(fecha)
        self.assertEqual(fecha_texto, "fecha no declarada")
        self.assertEqual(sensores, "Radarsat (fecha no declarada)")

    def test_fecha_parcial_no_se_completa_por_inferencia(self):
        observaciones = [
            {"fecha": "2017-03-26", "sensor": "A", "area_original_km2": 1.0, "partes": 1},
            {"fecha": None, "sensor": "B", "area_original_km2": 1.0, "partes": 1},
        ]
        fecha, fecha_texto, sensores = _flood_date_sensor_summary(observaciones)
        self.assertIsNone(fecha)
        self.assertEqual(fecha_texto, "fecha no declarada")
        self.assertIn("A (26/03)", sensores)
        self.assertIn("B (fecha no declarada)", sensores)

    def test_sensor_ausente_no_se_infiere(self):
        self.assertEqual(_sensor_label(None), "Sensor no declarado")
        self.assertEqual(_sensor_label(""), "Sensor no declarado")
        observaciones = [
            {"fecha": "2017-03-26", "sensor": "Sensor no declarado", "area_original_km2": 1.0, "partes": 1},
        ]
        _, _, sensores = _flood_date_sensor_summary(observaciones)
        self.assertIn("Sensor no declarado (26/03)", sensores)

    def test_agrupacion_por_fecha_y_sensor(self):
        records = [
            record(utm_box(0, 0), "2017-03-26", "A"),
            record(utm_box(0, 1000), "2017-03-26", "A"),
            record(utm_box(2000, 0), "2017-03-30", "B"),
        ]
        grouped = _group_flood_records(records)
        self.assertEqual(set(grouped), {("2017-03-26", "A"), ("2017-03-30", "B")})
        self.assertEqual(len(grouped[("2017-03-26", "A")]), 2)


class TestFiltrado(unittest.TestCase):
    def test_fragmentos_por_encima_y_por_debajo_del_umbral(self):
        grande = utm_box(0, 0, 1000)
        pequeno = utm_box(1500, 0, 60)  # 0,0036 km², por debajo de 0,5 ha
        filtered, removed, before, after, removed_geom = _filter_flood_geometry(
            MultiPolygon([grande, pequeno]),
            5_000,
        )
        self.assertIsNotNone(filtered)
        self.assertEqual(filtered.geom_type, "Polygon")
        self.assertEqual(before, 2)
        self.assertEqual(after, 1)
        self.assertAlmostEqual(removed, 0.0036, places=3)
        self.assertAlmostEqual(removed_geom.area / 1e6, 0.0036, places=3)

    def test_todo_por_debajo_del_umbral(self):
        filtered, removed, before, after, removed_geom = _filter_flood_geometry(
            utm_box(0, 0, 60),
            5_000,
        )
        self.assertIsNone(filtered)
        self.assertEqual(before, 1)
        self.assertEqual(after, 0)
        self.assertAlmostEqual(removed, 0.0036, places=3)
        self.assertIsNotNone(removed_geom)

    def test_multiparte_por_encima_del_umbral(self):
        geom = MultiPolygon([utm_box(0, 0, 1000), utm_box(2000, 0, 1000)])
        filtered, removed, before, after, removed_geom = _filter_flood_geometry(geom, 5_000)
        self.assertEqual(filtered.geom_type, "MultiPolygon")
        self.assertEqual(before, 2)
        self.assertEqual(after, 2)
        self.assertAlmostEqual(removed, 0.0, places=3)
        self.assertIsNone(removed_geom)

    def test_no_pierde_componentes_sin_registrar(self):
        geom = MultiPolygon([utm_box(0, 0, 1000), utm_box(1500, 0, 50)])
        _, removed, before, after, removed_geom = _filter_flood_geometry(geom, 5_000)
        self.assertEqual(before - after, 1)
        self.assertGreater(removed, 0.0)
        self.assertIsNotNone(removed_geom)
        self.assertAlmostEqual(removed_geom.area / 1e6, removed, places=4)


class TestSimplificacion(unittest.TestCase):
    def test_geometria_valida_antes_y_despues(self):
        geom = utm_box(0, 0, 1000)
        simplified, audit, delta = _simplify_flood_geometry(geom, 25)
        self.assertTrue(geom.is_valid)
        self.assertTrue(simplified.is_valid)
        self.assertTrue(audit.valid)
        self.assertAlmostEqual(delta, 0.0, places=3)

    def test_cambio_de_area_calculado(self):
        geom = utm_box(0, 0, 1000).buffer(0).union(utm_box(1100, 0, 200))
        simplified, _, delta = _simplify_flood_geometry(geom, 25)
        self.assertTrue(simplified.is_valid)
        self.assertAlmostEqual(
            delta,
            simplified.area / 1e6 - geom.area / 1e6,
            places=6,
        )

    def test_geometria_vacia_se_detecta(self):
        with self.assertRaises(ValueError):
            _simplify_flood_geometry(Polygon(), 25)

    def test_geometria_invalida_se_detecta(self):
        bow = Polygon(
            [
                (X0, Y0),
                (X0 + 100, Y0 + 100),
                (X0 + 100, Y0),
                (X0, Y0 + 100),
                (X0, Y0),
            ]
        )
        self.assertFalse(bow.is_valid)
        with self.assertRaises(ValueError):
            _simplify_flood_geometry(bow, 0)


class TestPublicacion(unittest.TestCase):
    def test_reproyeccion_y_area(self):
        geom = utm_box(0, 0, 1000)
        transformer = Transformer.from_crs("EPSG:32717", "EPSG:4326", always_xy=True)
        wgs, wgs_utm, audit, published_utm, delta = _publish_flood_geometry(
            geom,
            transformer,
        )
        self.assertTrue(wgs.is_valid)
        self.assertTrue(audit.valid)
        self.assertTrue(wgs_utm.is_valid)
        self.assertGreaterEqual(wgs.bounds[0], -81.5)
        self.assertLessEqual(wgs.bounds[2], -79.0)
        self.assertGreaterEqual(wgs.bounds[1], -6.5)
        self.assertLessEqual(wgs.bounds[3], -4.5)
        self.assertAlmostEqual(published_utm, 1.0, places=2)
        self.assertLess(abs(delta), 0.01)

    def test_hausdorff_dirigido_de_fragmentos_eliminados(self):
        removed = utm_box(0, 0, 100)
        filtered = utm_box(1000, 0, 1000)
        value, method = _flood_hausdorff_override(removed, filtered)
        self.assertGreater(value, 900)
        self.assertLess(value, 1100)
        self.assertIn("muestreado", method)

    def test_fidelidad_identica_y_desplazada(self):
        geom = utm_box(0, 0, 1000)
        identica = _flood_fidelity(geom, geom)
        self.assertAlmostEqual(identica.iou, 1.0, places=6)
        self.assertAlmostEqual(identica.symmetric_difference_km2, 0.0, places=3)
        self.assertAlmostEqual(identica.hausdorff_m, 0.0, places=1)

        desplazada = _flood_fidelity(geom, utm_box(100, 0, 1000))
        self.assertLess(desplazada.iou, 1.0)
        self.assertGreater(desplazada.symmetric_difference_km2, 0.0)
        self.assertGreater(desplazada.hausdorff_m, 0.0)
        self.assertGreaterEqual(desplazada.boundary_mean_m, 0.0)
        self.assertGreaterEqual(desplazada.boundary_p95_m, 0.0)

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
