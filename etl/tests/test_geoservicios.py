import json
import unittest

from etl.geoservicios import (
    arcgis_json_to_geojson,
    catalog_search_titles,
    compare_sheets,
    count_values,
    geojson_to_esri_geometry,
    license_summary,
    normalize_sheet,
    parse_official_sheets,
    parse_wfs_capabilities,
    parse_wmts_capabilities,
)

DESCRIPCION_GEOLOGIA = """27 mapas geológicos digitales a escala 1:100 000.
09a, 09b, 09c, 09d, 09f, 09g, 09h, 10e, 10f, 10g, 10h, 11e, 11f, 11g, 11h,
12e, 12f, 12g, 12h, 13e, 13f, 13g, 13h, 14e, 14f, 14g, 14h.
Y 27 líneas de secciones geológicas para cada mapa."""

ACTUALES_CUENCA = [
    "10b",
    "10c",
    "10d",
    "11a",
    "11b",
    "11c",
    "11d",
    "11e",
    "12b",
    "12c",
    "12d",
    "12e",
]

WFS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:WFS_Capabilities xmlns:wfs="http://www.opengis.net/wfs/2.0"
  xmlns:ows="http://www.opengis.net/ows/1.1" version="2.0.0">
  <ows:ServiceIdentification>
    <ows:Title>WFS</ows:Title>
    <ows:Abstract>Geología</ows:Abstract>
    <ows:Fees>1</ows:Fees>
    <ows:AccessConstraints>referencial</ows:AccessConstraints>
  </ows:ServiceIdentification>
  <ows:OperationsMetadata>
    <ows:Operation name="GetCapabilities"/>
    <ows:Operation name="GetFeature"/>
  </ows:OperationsMetadata>
  <wfs:FeatureTypeList>
    <wfs:FeatureType>
      <wfs:Name>SERV_GEOLOGIA_100K_INTEGRADA:Geología</wfs:Name>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::4326</wfs:DefaultCRS>
    </wfs:FeatureType>
    <wfs:FeatureType>
      <wfs:Name>SERV_GEOLOGIA_100K_INTEGRADA:Hojas</wfs:Name>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::32718</wfs:DefaultCRS>
    </wfs:FeatureType>
  </wfs:FeatureTypeList>
</wfs:WFS_Capabilities>"""

WMTS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<Capabilities xmlns="http://www.opengis.net/wmts/1.0"
  xmlns:ows="http://www.opengis.net/ows/1.1" version="1.0.0">
  <ows:ServiceIdentification>
    <ows:Title>SERV_GEOLOGIA_100K_INTEGRADA</ows:Title>
  </ows:ServiceIdentification>
  <Contents>
    <Layer>
      <ows:Title>Geología</ows:Title>
      <ows:Identifier>geologia</ows:Identifier>
      <Format>image/png</Format>
      <TileMatrixSetLink><TileMatrixSet>default028mm</TileMatrixSet></TileMatrixSetLink>
    </Layer>
    <TileMatrixSet>
      <ows:Identifier>default028mm</ows:Identifier>
    </TileMatrixSet>
  </Contents>
</Capabilities>"""


class TestHojas(unittest.TestCase):
    def test_normaliza_codigos(self):
        self.assertEqual(normalize_sheet("10-b"), "10b")
        self.assertEqual(normalize_sheet("09A"), "9a")
        self.assertEqual(normalize_sheet(" 9 ñ "), "9n")

    def test_descripcion_oficial_27_sin_falso_27l(self):
        official = parse_official_sheets(DESCRIPCION_GEOLOGIA)
        self.assertEqual(len(official), 27)
        self.assertNotIn("27l", official)
        self.assertNotIn("y", official)
        self.assertIn("10e", official)
        self.assertIn("9a", official)

    def test_discrepancia_con_la_cuenca(self):
        official = parse_official_sheets(DESCRIPCION_GEOLOGIA)
        comparison = compare_sheets(official, ACTUALES_CUENCA)
        self.assertIn("10d", comparison["reales_fuera_de_la_descripcion"])
        self.assertIn("11d", comparison["reales_fuera_de_la_descripcion"])
        self.assertIn("12d", comparison["reales_fuera_de_la_descripcion"])
        self.assertNotIn("13d", comparison["reales"])
        self.assertEqual(comparison["en_ambos"], ["11e", "12e"])


class TestWfsWmts(unittest.TestCase):
    def test_wfs(self):
        data = parse_wfs_capabilities(WFS_FIXTURE)
        self.assertEqual(data["title"], "WFS")
        self.assertEqual(data["fees"], "1")
        self.assertEqual(data["access_constraints"], "referencial")
        self.assertEqual(len(data["feature_types"]), 2)
        self.assertEqual(data["feature_types"][0]["default_crs"], "urn:ogc:def:crs:EPSG::4326")
        self.assertIn("GetFeature", data["operations"])

    def test_wmts(self):
        data = parse_wmts_capabilities(WMTS_FIXTURE)
        self.assertEqual(data["title"], "SERV_GEOLOGIA_100K_INTEGRADA")
        self.assertEqual(data["formats"], ["image/png"])
        self.assertEqual(data["layers"], ["geologia"])
        self.assertEqual(data["tile_matrix_sets"], ["default028mm"])


class TestGeometria(unittest.TestCase):
    def test_geojson_a_esri(self):
        geom = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
        }
        esri = geojson_to_esri_geometry(geom)
        self.assertEqual(esri["spatialReference"]["wkid"], 4326)
        self.assertEqual(len(esri["rings"]), 1)
        self.assertEqual(esri["rings"][0][0], [0.0, 0.0])

    def test_arcgis_json_a_geojson(self):
        payload = {
            "spatialReference": {"wkid": 4326},
            "features": [
                {
                    "attributes": {"HOJA": "11c"},
                    "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
                }
            ],
        }
        result = arcgis_json_to_geojson(payload)
        self.assertEqual(result["type"], "FeatureCollection")
        self.assertEqual(len(result["features"]), 1)
        self.assertEqual(result["features"][0]["properties"]["HOJA"], "11c")

    def test_cuenta_valores(self):
        features = [
            {"properties": {"Nivel_Vuln": "Alta"}},
            {"properties": {"Nivel_Vuln": "Alta"}},
            {"properties": {"Nivel_Vuln": "Baja"}},
        ]
        self.assertEqual(
            count_values(features, "Nivel_Vuln"),
            [{"Nivel_Vuln": "Alta", "n": 2}, {"Nivel_Vuln": "Baja", "n": 1}],
        )


class TestCatalogoLicencia(unittest.TestCase):
    def test_catalogo(self):
        payload = {
            "hits": {
                "hits": [
                    {
                        "_id": "uuid",
                        "_source": {
                            "resourceTitleObject": {"default": "Geología"},
                            "resourceAbstractObject": {"default": "Resumen"},
                        },
                    }
                ]
            }
        }
        rows = catalog_search_titles(payload)
        self.assertEqual(rows[0]["uuid"], "uuid")
        self.assertEqual(rows[0]["title"], "Geología")

    def test_licencia(self):
        html = """
        <html><body>
        <h1>Licencia para Uso No Comercial</h1>
        <p>Datos.- La utilización, traducción y creación de obras derivadas
        están autorizadas, a condición de que se cite al INGEMMET.</p>
        <p>Duración y término: perpetua.</p>
        <p>Software.- Se prohíbe la reproducción.</p>
        </body></html>
        """
        data = license_summary(html)
        self.assertEqual(data["titulo"], "Licencia para Uso No Comercial")
        self.assertIn("obras derivadas", data["datos"])
        self.assertIn("perpetua", data["duracion"])


class TestLeyendas(unittest.TestCase):
    def test_susceptibilidad_vector_tres_clases(self):
        features = [
            {"properties": {"GRIDCODE": 2}},
            {"properties": {"GRIDCODE": 3}},
            {"properties": {"GRIDCODE": 4}},
        ]
        counts = count_values(features, "GRIDCODE")
        self.assertEqual([row["GRIDCODE"] for row in counts], [2, 3, 4])
        leyenda = ["Alto", "Moderado", "Bajo", "Muy bajo o nulo"]
        self.assertEqual(len(leyenda), 4)
        self.assertIn("Muy bajo o nulo", leyenda)


if __name__ == "__main__":
    unittest.main()
