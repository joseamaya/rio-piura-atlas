import csv
import json
import tempfile
import unittest
from pathlib import Path

from etl.senamhi import (
    DAILY_COLUMNS,
    SchemaError,
    SeriesQualityError,
    coverage_stats,
    flatten_series,
    station_qc,
    write_csv,
)
from etl.senamhi_geo import classify_station


def station(sid="000255", nombre="CHULUCANAS", provincia="MORROPÓN"):
    return {
        "id": sid,
        "name": nombre,
        "provinceName": provincia,
        "districtName": nombre,
        "latitude": -5.10843,
        "longitude": -80.16956,
        "altitude": 89.0,
        "departmentName": "PIURA",
    }


def fila(fecha, precip=0.0, tmax=None, tmin=None):
    return {
        "date": fecha,
        "precipitation": precip,
        "maximumTemperature": tmax,
        "minimumTemperature": tmin,
    }


class TestCalidadSenamhi(unittest.TestCase):
    def test_conserva_nulos_y_ordena(self):
        rows = flatten_series(
            station(),
            {"data": [fila("1998-03-12", 12.4, 33.1, None), fila("1983-04-21")]},
        )
        self.assertEqual([r["date"] for r in rows], ["1983-04-21", "1998-03-12"])
        self.assertIsNone(rows[1]["temperature_min_c"])

    def test_rechaza_duplicado(self):
        with self.assertRaises(SeriesQualityError):
            flatten_series(
                station(),
                {"data": [fila("1998-03-12", 1.0), fila("1998-03-12", 2.0)]},
            )

    def test_rechaza_fecha_invalida(self):
        with self.assertRaises(SeriesQualityError):
            flatten_series(station(), {"data": [fila("1998-02-30")]})

    def test_rechaza_fecha_sin_formato_iso(self):
        with self.assertRaises(SeriesQualityError):
            flatten_series(station(), {"data": [fila("19980312")]})

    def test_rechaza_campo_ausente(self):
        with self.assertRaises(SchemaError):
            flatten_series(
                station(),
                {"data": [{"date": "1998-03-12", "precipitation": 1.0}]},
            )

    def test_rechaza_tipo_no_numerico(self):
        with self.assertRaises(SchemaError):
            flatten_series(
                station(),
                {"data": [fila("1998-03-12", "1.0")]},
            )

    def test_marca_precipitacion_negativa(self):
        rows = flatten_series(station(), {"data": [fila("1998-03-12", -0.1)]})
        self.assertEqual(rows[0]["qc_precip_negativa"], 1)
        self.assertEqual(rows[0]["precipitation_mm"], -0.1)

    def test_marca_tmax_menor_tmin(self):
        rows = flatten_series(
            station(), {"data": [fila("1998-03-12", 0.0, 20.0, 25.0)]}
        )
        self.assertEqual(rows[0]["qc_tmax_menor_tmin"], 1)

    def test_marca_tmax_igual_tmin(self):
        rows = flatten_series(
            station(), {"data": [fila("1998-03-12", 0.0, 25.0, 25.0)]}
        )
        self.assertEqual(rows[0]["qc_tmax_igual_tmin"], 1)

    def test_marca_extremo_sin_eliminarlo(self):
        rows = flatten_series(station(), {"data": [fila("1998-03-12", 250.0)]})
        self.assertEqual(rows[0]["qc_precip_extrema"], 1)
        self.assertEqual(rows[0]["precipitation_mm"], 250.0)

    def test_marca_temperatura_sospechosa(self):
        rows = flatten_series(
            station(), {"data": [fila("1998-03-12", 0.0, 60.0, 10.0)]}
        )
        self.assertEqual(rows[0]["qc_temp_sospechosa"], 1)

    def test_station_qc_coordenadas(self):
        self.assertEqual(station_qc(station())["coordenada_valida"], 1)
        invalida = {**station(), "latitude": 200}
        self.assertEqual(station_qc(invalida)["coordenada_valida"], 0)
        sin_coords = {**station(), "latitude": None, "longitude": None}
        self.assertEqual(station_qc(sin_coords)["coordenada_valida"], 0)

    def test_write_csv_conserva_nulos_y_columnas(self):
        rows = flatten_series(station(), {"data": [fila("1998-03-12", None)]})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "serie.csv"
            write_csv(rows, path)
            with path.open(encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                self.assertEqual(reader.fieldnames, DAILY_COLUMNS)
                fila_leida = next(reader)
            self.assertEqual(fila_leida["precipitation_mm"], "")
            self.assertEqual(fila_leida["station_id"], "000255")


class TestCoberturaSenamhi(unittest.TestCase):
    def test_sin_huecos(self):
        rows = flatten_series(
            station(),
            {
                "data": [
                    fila("1998-03-10", 1.0, 30.0, 20.0),
                    fila("1998-03-11", 2.0, 30.0, 20.0),
                    fila("1998-03-12", 3.0, 30.0, 20.0),
                ]
            },
        )
        stats = coverage_stats(rows)
        self.assertEqual(stats["expected_days"], 3)
        self.assertEqual(stats["observed_days"], 3)
        self.assertEqual(stats["missing_days"], 0)
        self.assertEqual(stats["n_gaps"], 0)
        self.assertEqual(stats["coverage_pct"], 100.0)
        self.assertEqual(stats["estado"], "ok")

    def test_hueco_contiguo(self):
        rows = flatten_series(
            station(),
            {
                "data": [
                    fila("1998-03-10", 1.0, 30.0, 20.0),
                    fila("1998-03-13", 2.0, 30.0, 20.0),
                ]
            },
        )
        stats = coverage_stats(rows)
        self.assertEqual(stats["expected_days"], 4)
        self.assertEqual(stats["missing_days"], 2)
        self.assertEqual(stats["n_gaps"], 1)
        self.assertEqual(stats["longest_gap_days"], 2)
        self.assertEqual(stats["gaps"][0][0], "1998-03-11")
        self.assertEqual(stats["gaps"][0][1], "1998-03-12")

    def test_nulos_por_variable(self):
        rows = flatten_series(
            station(),
            {
                "data": [
                    fila("1998-03-10", None, 30.0, None),
                    fila("1998-03-11", 1.0, None, 20.0),
                ]
            },
        )
        stats = coverage_stats(rows)
        self.assertEqual(stats["n_precip"], 1)
        self.assertEqual(stats["pct_precip_null"], 50.0)
        self.assertEqual(stats["n_tmax"], 1)
        self.assertEqual(stats["pct_tmax_null"], 50.0)
        self.assertEqual(stats["n_tmin"], 1)
        self.assertEqual(stats["pct_tmin_null"], 50.0)
        self.assertEqual(stats["estado"], "ok")

    def test_estado_sin_temperatura(self):
        rows = flatten_series(station(), {"data": [fila("1998-03-10", 1.0)]})
        stats = coverage_stats(rows)
        self.assertEqual(stats["estado"], "sin_temperatura")
        self.assertEqual(stats["pct_tmax_null"], 100.0)

    def test_estado_temperatura_parcial(self):
        rows = flatten_series(
            station(),
            {
                "data": [
                    fila("1998-03-10", 1.0, 30.0, 20.0),
                    fila("1998-03-11", 1.0),
                    fila("1998-03-12", 1.0),
                ]
            },
        )
        stats = coverage_stats(rows)
        self.assertEqual(stats["estado"], "temperatura_parcial")


class TestGeografiaSenamhi(unittest.TestCase):
    def test_dentro_de_cuenca(self):
        # Miraflores, cerca de Castilla.
        result = classify_station(-80.61654, -5.17528, "PIURA")
        self.assertEqual(result["relacion_cuenca"], "dentro")
        self.assertEqual(result["clasificacion"], "dentro_cuenca")
        self.assertIsNotNone(result["distancia_borde_km"])

    def test_fuera_contexto_regional(self):
        # Mallares, en Sullana, fuera de la cuenca ANA.
        result = classify_station(-80.73556, -4.85574, "PIURA")
        self.assertEqual(result["relacion_cuenca"], "fuera")
        self.assertEqual(result["clasificacion"], "fuera_cuenca_contexto_regional")
        self.assertIn("contexto regional", result["nota_geografica"])

    def test_coordenada_invalida_no_se_clasifica(self):
        result = classify_station(None, -5.0, "PIURA")
        self.assertEqual(result["relacion_cuenca"], "")
        self.assertIsNone(result["distancia_borde_km"])


class TestBuildGuard(unittest.TestCase):
    def test_no_escribe_en_web_public(self):
        from etl.build_senamhi_historico import PUBLIC, ensure_not_public

        with self.assertRaises(SystemExit):
            ensure_not_public(PUBLIC / "data")

    def test_hash_incorrecto_impide_usar_la_serie(self):
        from etl.build_senamhi_historico import build

        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw"
            out = Path(tmp) / "out"
            (raw / "series").mkdir(parents=True)
            (raw / "stations.json").write_text(
                json.dumps({"status": True, "data": [station()]}),
                encoding="utf-8",
            )
            (raw / "series" / "000255.json").write_text(
                json.dumps({"status": True, "data": [fila("1998-03-10", 1.0)]}),
                encoding="utf-8",
            )
            (raw / "manifest.json").write_text(
                json.dumps(
                    {
                        "estaciones": [{"id": "000255"}],
                        "archivos": {"series/000255.json": {"sha256": "0" * 64}},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                build(raw, out)


if __name__ == "__main__":
    unittest.main()
