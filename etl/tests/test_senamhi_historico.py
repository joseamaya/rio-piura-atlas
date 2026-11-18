import csv
import json
import tempfile
import unittest
from pathlib import Path

from etl.build_senamhi_historico import (
    COLUMNS,
    build,
    flatten_series,
    piura_stations,
    write_csv,
)


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


class TestSenamhiHistorico(unittest.TestCase):
    def test_filtra_piura_y_ordena(self):
        payload = {
            "data": [
                station("000256", "BERNAL", "SECHURA"),
                station("000255", "CHULUCANAS", "MORROPÓN"),
                {**station("000999", "OTRA", "LIMA"), "departmentName": "LIMA"},
            ]
        }
        estaciones = piura_stations(payload)
        self.assertEqual([e["id"] for e in estaciones], ["000255", "000256"])

    def test_aplana_conserva_nulos_y_ordena(self):
        payload = {
            "data": [
                {
                    "date": "1998-03-12",
                    "precipitation": 12.4,
                    "maximumTemperature": 33.1,
                    "minimumTemperature": None,
                },
                {
                    "date": "1983-04-21",
                    "precipitation": 0.0,
                    "maximumTemperature": 32.0,
                    "minimumTemperature": 22.5,
                },
            ]
        }
        rows = flatten_series(station(), payload)
        self.assertEqual([r["date"] for r in rows], ["1983-04-21", "1998-03-12"])
        self.assertIsNone(rows[1]["temperature_min_c"])
        self.assertEqual(rows[0]["precipitation_mm"], 0.0)

    def test_rechaza_fecha_duplicada(self):
        payload = {
            "data": [
                {"date": "1998-03-12", "precipitation": 1.0},
                {"date": "1998-03-12", "precipitation": 2.0},
            ]
        }
        with self.assertRaises(ValueError):
            flatten_series(station(), payload)

    def test_marca_precipitacion_negativa_sin_eliminarla(self):
        payload = {
            "data": [
                {
                    "date": "1998-03-12",
                    "precipitation": -0.1,
                    "maximumTemperature": None,
                    "minimumTemperature": None,
                }
            ]
        }
        rows = flatten_series(station(), payload)
        self.assertEqual(rows[0]["precipitation_mm"], -0.1)
        self.assertEqual(rows[0]["qc_precip_negativa"], 1)
        self.assertIn("precip_negativa", rows[0]["qc_flags"])

    def test_rechaza_fecha_invalida(self):
        payload = {"data": [{"date": "1998-02-30", "precipitation": 0.0}]}
        with self.assertRaises(ValueError):
            flatten_series(station(), payload)

    def test_escribe_csv_con_columnas_y_nulos(self):
        rows = flatten_series(
            station(),
            {
                "data": [
                    {
                        "date": "1998-03-12",
                        "precipitation": None,
                        "maximumTemperature": 33.1,
                        "minimumTemperature": 24.0,
                    }
                ]
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "estaciones.csv"
            write_csv(rows, path)
            with path.open(encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                self.assertEqual(reader.fieldnames, COLUMNS)
                fila = next(reader)
            self.assertEqual(fila["station_id"], "000255")
            self.assertEqual(fila["date"], "1998-03-12")
            self.assertEqual(fila["precipitation_mm"], "")
            self.assertEqual(float(fila["temperature_max_c"]), 33.1)

    def test_build_genera_csv_y_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw"
            out = Path(tmp) / "out"
            (raw / "series").mkdir(parents=True)
            (raw / "stations.json").write_text(
                json.dumps({"status": True, "data": [station()]}),
                encoding="utf-8",
            )
            (raw / "series" / "000255.json").write_text(
                json.dumps(
                    {
                        "status": True,
                        "data": [
                            {
                                "date": "1983-04-21",
                                "precipitation": 0.0,
                                "maximumTemperature": None,
                                "minimumTemperature": None,
                            },
                            {
                                "date": "1998-03-12",
                                "precipitation": 4.2,
                                "maximumTemperature": None,
                                "minimumTemperature": None,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            meta = build(raw, out)
            self.assertTrue((out / "estaciones_piura.csv").exists())
            self.assertEqual(meta["filas"], 2)
            self.assertEqual(meta["estaciones_catalogo_total"], 1)
            self.assertEqual(meta["estaciones_seleccionadas"], 1)
            self.assertEqual(meta["estaciones_con_datos"], 1)
            self.assertEqual(meta["periodo"], {"desde": "1983-04-21", "hasta": "1998-03-12"})
            self.assertFalse(meta["publicado"])


if __name__ == "__main__":
    unittest.main()
