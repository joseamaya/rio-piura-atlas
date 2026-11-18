"""Pruebas de integración con servicios reales.

No se ejecutan en CI. Se activan explícitamente con:

    RUN_LIVE_TESTS=1 python3 -m unittest etl.tests.test_live_sources -v

El certificado de GEOCATMIN no es confiable en este entorno; la prueba lo
desactiva solo cuando el usuario pidió la integración en vivo.
"""

from __future__ import annotations

import os
import unittest
import warnings

import requests

RUN_LIVE = os.environ.get("RUN_LIVE_TESTS") == "1"
SENAMHI = "https://servicios.senamhi.gob.pe/api/researchers/historical-download"
INGEMMET = (
    "https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/"
    "SERV_GEOLOGIA_100K_INTEGRADA/MapServer"
)
ZEE = (
    "https://geoservidorperu.minam.gob.pe/arcgis/rest/services/ZEE_VISOR/"
    "09_POTENCIALIDADES_Y_LIMITACIONES_PIURA/MapServer/3"
)


@unittest.skipUnless(RUN_LIVE, "definir RUN_LIVE_TESTS=1 para integración en vivo")
class TestLiveSources(unittest.TestCase):
    def test_senamhi_catalogo_y_una_serie(self):
        response = requests.get(
            f"{SENAMHI}/stations",
            timeout=60,
            headers={"User-Agent": "rio-piura-atlas/0.4 (test en vivo)"},
        )
        response.raise_for_status()
        payload = response.json()
        piura = [
            e
            for e in payload["data"]
            if str(e.get("departmentName", "")).upper() == "PIURA"
        ]
        self.assertEqual(len(piura), 20)
        sid = piura[0]["id"]
        serie = requests.get(
            f"{SENAMHI}/stations/{sid}/series",
            timeout=120,
            headers={"User-Agent": "rio-piura-atlas/0.4 (test en vivo)"},
        )
        serie.raise_for_status()
        self.assertGreater(len(serie.json()["data"]), 1000)

    def test_ingemmet_geologia(self):
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        response = requests.get(
            f"{INGEMMET}?f=pjson", timeout=60, verify=False
        )
        response.raise_for_status()
        payload = response.json()
        names = [layer.get("name") for layer in payload.get("layers", [])]
        self.assertIn("Geología", names)
        self.assertIn("27 mapas", payload.get("serviceDescription", ""))

    def test_zee_peligro_inundacion_78(self):
        response = requests.get(
            f"{ZEE}/query",
            params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
            timeout=60,
        )
        response.raise_for_status()
        self.assertEqual(response.json().get("count"), 78)


if __name__ == "__main__":
    unittest.main()
