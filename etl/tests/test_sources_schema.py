import json
import unittest
from pathlib import Path

import yaml

from etl.check_data import (
    DISPONIBILIDADES,
    ESTADOS,
    PUBLICACIONES,
    TIPOS_EVIDENCIA,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "data" / "sources.yml"
DATA = ROOT / "web" / "public" / "data"

NEW_SOURCES = {
    "ana-tratamiento-cauce-2014",
    "indeci-piura-castilla-2009",
    "lund-sediment-2024",
    "ingemmet-carta-geologica-100k",
    "ingemmet-geologia-integrada-100k",
    "ingemmet-peligros-geologicos",
    "pechp-inspeccion-2026",
    "peruverde-expedicion-2002",
    "pechp-hidrometeorologia-diaria",
    "pechp-topobatimetria-2026",
    "zee-piura-memoria-2012",
}

FUENTES_BLOQUEADAS = {
    "senamhi-historico-estaciones",
    "ingemmet-geologia-integrada-100k",
    "ingemmet-geomorfologia-vector",
    "ingemmet-susceptibilidad-inundacion-vector",
    "ingemmet-peligros-geologicos",
    "ana-zee-piura",
}


def load_sources():
    data = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    return data.get("fuentes") or []


class TestSourcesSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fuentes = load_sources()
        cls.por_id = {f["id"]: f for f in cls.fuentes}

    def test_ids_unicos(self):
        ids = [f["id"] for f in self.fuentes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_fuentes_nuevas_presentes(self):
        self.assertTrue(NEW_SOURCES.issubset(self.por_id))

    def test_estado_valido(self):
        for fuente in self.fuentes:
            self.assertIn(fuente["estado"], ESTADOS, fuente["id"])

    def test_disponibilidad_valida(self):
        for fuente in self.fuentes:
            if "disponibilidad" in fuente:
                self.assertIn(
                    fuente["disponibilidad"], DISPONIBILIDADES, fuente["id"]
                )

    def test_publicacion_valida(self):
        for fuente in self.fuentes:
            if "publicacion" in fuente:
                self.assertIn(
                    fuente["publicacion"], PUBLICACIONES, fuente["id"]
                )

    def test_fuentes_bloqueadas(self):
        for fid in FUENTES_BLOQUEADAS:
            self.assertEqual(
                self.por_id[fid].get("publicacion"),
                "bloqueada",
                f"{fid}: debe declarar publicacion: bloqueada",
            )

    def test_capas_no_usan_fuentes_bloqueadas(self):
        for path in sorted(DATA.glob("*.geojson")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for feature in data.get("features", []):
                fid = (feature.get("properties") or {}).get("fuente")
                fuente = self.por_id.get(fid) or {}
                if fuente.get("publicacion") is not None:
                    self.assertEqual(
                        fuente["publicacion"],
                        "autorizada",
                        f"{path.name}: usa {fid}, bloqueada para publicación",
                    )

    def test_tipo_evidencia_valido(self):
        for fuente in self.fuentes:
            if "tipo_evidencia" not in fuente:
                continue
            self.assertIsInstance(fuente["tipo_evidencia"], list, fuente["id"])
            self.assertTrue(fuente["tipo_evidencia"], fuente["id"])
            for evidencia in fuente["tipo_evidencia"]:
                self.assertIn(evidencia, TIPOS_EVIDENCIA, fuente["id"])

    def test_fuentes_nuevas_con_metadatos(self):
        for fid in NEW_SOURCES:
            fuente = self.por_id[fid]
            for campo in (
                "disponibilidad",
                "tipo_evidencia",
                "periodo",
                "formato",
                "limitaciones",
                "capas",
            ):
                self.assertIn(campo, fuente, f"{fid}: falta {campo}")

    def test_pisco_no_se_presenta_como_5_km(self):
        pisco = self.por_id["senamhi-pisco"]
        self.assertIn("0,1°", pisco["escala"])
        self.assertIn("1981–2025", pisco["periodo"])
        self.assertIn("GPL 3.0+", pisco["licencia"])
        self.assertIn("no está explícita", pisco["limitaciones"])

    def test_descargas_son_http_o_null(self):
        for fuente in self.fuentes:
            descarga = fuente.get("descarga")
            if descarga is not None:
                self.assertIsInstance(descarga, str, fuente["id"])
                self.assertTrue(descarga.startswith(("http://", "https://")), fuente["id"])

    def test_capas_es_lista(self):
        for fuente in self.fuentes:
            if "capas" in fuente:
                self.assertIsInstance(fuente["capas"], list, fuente["id"])
                self.assertTrue(all(isinstance(c, str) and c for c in fuente["capas"]))

    def test_fuentes_de_capas_publicables(self):
        for path in sorted(DATA.glob("*.geojson")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for feature in data.get("features", []):
                fid = (feature.get("properties") or {}).get("fuente")
                self.assertIn(fid, self.por_id, f"{path.name}: fuente {fid}")
                disp = self.por_id[fid].get("disponibilidad")
                self.assertIn(
                    disp,
                    {None, "validada", "procesada"},
                    f"{path.name}: {fid} tiene disponibilidad {disp}",
                )


if __name__ == "__main__":
    unittest.main()
