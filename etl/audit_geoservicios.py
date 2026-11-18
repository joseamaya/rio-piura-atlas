#!/usr/bin/env python3
"""Audita los servicios vectoriales de INGEMMET y la ZEE Piura.

No publica capas. Consulta metadatos, cuenta polígonos contra la cuenca ANA,
verifica CRS y leyendas, prueba WFS/WMTS y descarga solo el subconjunto de
geología que intersecta la cuenca. Las salidas quedan en
`data/processed/geoservicios/` (ignorado por Git).

El certificado TLS de GEOCATMIN no es confiable en este entorno. El script
verifica por defecto (`verify=True`); para una auditoría local explícita se puede
usar `--insecure`, que imprime una advertencia y queda registrado en el JSON.

Uso:
    python3 etl/audit_geoservicios.py --insecure
    python3 etl/audit_geoservicios.py --skip-memoria
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import requests
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

try:
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
        sha256_text,
        strip_html,
    )
except ModuleNotFoundError:
    from geoservicios import (  # type: ignore
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
        sha256_text,
        strip_html,
    )

ROOT = Path(__file__).resolve().parents[1]
OUT_DEFAULT = ROOT / "data" / "processed" / "geoservicios"
RAW_DEFAULT = ROOT / "data" / "raw" / "geoservicios"
PUBLIC = ROOT / "web" / "public"
BASIN = ROOT / "web" / "public" / "data" / "cuenca.geojson"

ARCGIS = "https://geocatmin.ingemmet.gob.pe/arcgis/rest/services"
ARCGIS_WFS = "https://geocatmin.ingemmet.gob.pe/arcgis/services"
SERVICES = {
    "geologia": f"{ARCGIS}/SERV_GEOLOGIA_100K_INTEGRADA/MapServer",
    "geomorfologia": f"{ARCGIS}/SERV_GEOMORFOLOGIA/MapServer",
    "susceptibilidad": (
        f"{ARCGIS}/SERV_SUSCEPTIBILIDAD_INUNDACION_FLUVIAL_MIL1/MapServer"
    ),
    "peligros": f"{ARCGIS}/SERV_PELIGROS_GEOLOGICOS/MapServer",
    "imagen_susceptibilidad": (
        f"{ARCGIS}/SERV_IMG_SUSCEP_INUN_FLUVIAL/ImageServer"
    ),
}
GEONETWORK = "https://metadatos.ingemmet.gob.pe:8443/geonetwork"
LICENSE_URL = "https://geocatminapp.ingemmet.gob.pe/descarga?id=8&str=GEO_INGEEX"
ZEE = "https://geoservidorperu.minam.gob.pe/arcgis/rest/services"
ZEE_POT = f"{ZEE}/ZEE_VISOR/09_POTENCIALIDADES_Y_LIMITACIONES_PIURA/MapServer"
ZEE_DIM = (
    f"{ZEE}/ZEE_VISOR/09_DIMENSI%C3%93N_DE_EVALUACI%C3%93N_TERRITORIAL_PIURA/MapServer"
)
ZEE_MEMORIA = (
    "https://sinia.minam.gob.pe/sites/default/files/sinia/archivos/public/docs/"
    "estudio_de_la_propuesta_de_zee_7.pdf"
)
ZEE_METADATA = "https://sinia.minam.gob.pe/metadatos/295867"
LICENCIA_INGEMMET = "Licencia para Uso No Comercial (GEOCATMIN)"
LEYENDA_SUSCEPTIBILIDAD = ["Alto", "Moderado", "Bajo", "Muy bajo o nulo"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_not_public(path: Path) -> None:
    resolved = path.resolve()
    if resolved == PUBLIC or PUBLIC in resolved.parents:
        raise SystemExit(
            f"destino no permitido: {path}. Los datos de terceros no se publican "
            "hasta confirmar la licencia."
        )


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(path)


def load_basin() -> tuple[dict, dict, str]:
    data = json.loads(BASIN.read_text(encoding="utf-8"))
    geom = data["features"][0]["geometry"]
    esri = geojson_to_esri_geometry(geom)
    import hashlib

    digest = hashlib.sha256(BASIN.read_bytes()).hexdigest()
    return geom, esri, digest


class Client:
    def __init__(self, timeout: int, retries: int, insecure: bool):
        self.timeout = timeout
        self.retries = retries
        self.insecure = insecure
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "rio-piura-atlas/0.4 (auditoria; uso manual)",
                "Accept": "application/json",
            }
        )
        if insecure:
            warnings.filterwarnings("ignore", message="Unverified HTTPS request")
            self.session.verify = False

    def _request(self, method: str, url: str, **kwargs):
        last = None
        for attempt in range(1, self.retries + 1):
            try:
                response = self.session.request(
                    method, url, timeout=self.timeout, **kwargs
                )
                if response.status_code >= 500:
                    raise RuntimeError(f"HTTP {response.status_code} en {url}")
                response.raise_for_status()
                return response
            except (requests.RequestException, RuntimeError) as exc:
                last = exc
                if attempt < self.retries:
                    time.sleep(2 ** (attempt - 1))
        hint = " (¿certificado TLS? prueba --insecure)" if "SSL" in str(last) else ""
        raise RuntimeError(f"no se pudo consultar {url}: {last}{hint}")

    def get_json(self, url: str, params: dict | None = None) -> dict:
        response = self._request("GET", url, params=params)
        return response.json()

    def post_json(self, url: str, data: dict) -> dict:
        response = self._request("POST", url, data=data)
        return response.json()

    def post_json_body(self, url: str, body: dict) -> dict:
        response = self._request(
            "POST", url, json=body, headers={"Content-Type": "application/json"}
        )
        return response.json()

    def get_text(self, url: str) -> str:
        response = self._request("GET", url)
        return response.text


def query(
    client: Client,
    base: str,
    layer: int,
    *,
    geometry: dict | None = None,
    count_only: bool = False,
    group_field: str | None = None,
    out_fields: str = "*",
    return_geometry: bool = False,
    out_sr: int = 4326,
    f: str = "json",
) -> dict:
    data = {"where": "1=1", "f": f}
    if geometry:
        data.update(
            {
                "geometry": json.dumps(geometry),
                "geometryType": "esriGeometryPolygon",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
            }
        )
    if count_only:
        data["returnCountOnly"] = "true"
    if group_field:
        data["outFields"] = group_field
        data["returnGeometry"] = "false"
        data["groupByFieldsForStatistics"] = group_field
        data["outStatistics"] = json.dumps(
            [
                {
                    "statisticType": "count",
                    "onStatisticField": "OBJECTID",
                    "outStatisticFieldName": "n",
                }
            ]
        )
    else:
        data["outFields"] = out_fields
        data["returnGeometry"] = "true" if return_geometry else "false"
        if return_geometry:
            data["outSR"] = str(out_sr)
    return client.post_json(f"{base}/{layer}/query", data)


def count(
    client: Client, base: str, layer: int, geometry: dict | None = None
) -> int | None:
    payload = query(client, base, layer, geometry=geometry, count_only=True)
    value = payload.get("count")
    return int(value) if isinstance(value, (int, float)) else None


def group(
    client: Client, base: str, layer: int, field: str, geometry: dict | None = None
) -> list[dict]:
    payload = query(client, base, layer, geometry=geometry, group_field=field)
    if payload.get("error"):
        return []
    return [f.get("attributes") or {} for f in payload.get("features") or []]


def fetch_geojson(
    client: Client, base: str, layer: int, geometry: dict
) -> dict:
    payload = query(
        client,
        base,
        layer,
        geometry=geometry,
        out_fields="*",
        return_geometry=True,
        f="geojson",
    )
    if payload.get("type") == "FeatureCollection":
        return payload
    if payload.get("error"):
        raise RuntimeError(payload["error"])
    return arcgis_json_to_geojson(payload)


def layer_meta(client: Client, base: str, layer: int) -> dict:
    return client.get_json(f"{base}/{layer}", params={"f": "pjson"})


def service_meta(client: Client, base: str) -> dict:
    return client.get_json(base, params={"f": "pjson"})


def parse_geonetwork_record(client: Client, uuid: str) -> dict:
    text = client._request(
        "GET",
        f"{GEONETWORK}/srv/api/records/{uuid}",
        headers={"Accept": "application/xml"},
    ).text
    import re

    def values(tag: str) -> list[str]:
        out = []
        for raw in re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", text, re.S):
            clean = re.sub(r"<[^>]+>", " ", raw)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean:
                out.append(clean)
        return out

    return {
        "uuid": uuid,
        "url": f"{GEONETWORK}/srv/api/records/{uuid}",
        "title": (values("gmd:title") or [""])[0],
        "abstract": (values("gmd:abstract") or [""])[0],
        "dates": values("gmd:date")[:3],
        "denominator": (values("gmd:denominator") or [""])[0],
        "access_constraints": values("gmd:accessConstraints"),
        "use_limitations": values("gmd:useLimitation"),
        "other_constraints": values("gmd:otherConstraints"),
        "urls": values("gmd:URL")[:8],
        "protocols": values("gmd:protocol")[:8],
        "sha256": sha256_text(text),
    }


def download_memoria(client: Client, raw_dir: Path, refresh: bool) -> dict:
    path = raw_dir / "zee_piura_memoria_2012.pdf"
    if path.exists() and not refresh:
        data = path.read_bytes()
    else:
        response = client._request("GET", ZEE_MEMORIA)
        data = response.content
        if len(data) < 1_000_000 or not data.startswith(b"%PDF"):
            raise RuntimeError("la descarga de la Memoria ZEE no parece un PDF")
        atomic_write(path, data)
    import hashlib

    return {
        "url": ZEE_MEMORIA,
        "metadata_url": ZEE_METADATA,
        "file": str(path.relative_to(ROOT)),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "paginas": 255,
        "fecha": "2012-11",
        "escala": "1:100 000",
        "autora": (
            "Gobierno Regional de Piura — Gerencia Regional de Recursos "
            "Naturales y Gestión del Medio Ambiente"
        ),
        "metodologia": (
            "ZEE regional 2008–2012; submodelos de valor productivo, "
            "bioecológico, histórico-cultural, peligros y vulnerabilidad, "
            "conflicto de uso y aptitud urbano-industrial. El submodelo de "
            "inundación combina geomorfología 40 %, fisiografía 40 %, "
            "pendiente 10 %, precipitación 5 % y cobertura vegetal 5 %. "
            "No es una probabilidad hidrológica."
        ),
        "licencia": "no declarada en la Memoria ni en el servicio",
    }


def audit_geologia(client: Client, basin_esri: dict, out_dir: Path) -> dict:
    base = SERVICES["geologia"]
    svc = service_meta(client, base)
    layer6 = layer_meta(client, base, 6)
    layer0 = layer_meta(client, base, 0)
    basin_count = count(client, base, 6, basin_esri)
    envelope = {
        "rings": [
            [
                [-81.6, -6.6],
                [-78.8, -6.6],
                [-78.8, -3.8],
                [-81.6, -3.8],
                [-81.6, -6.6],
            ]
        ],
        "spatialReference": {"wkid": 4326},
    }
    envelope_count = count(client, base, 6, envelope)
    by_sheet = group(client, base, 6, "HOJA", basin_esri)
    by_sheet = [r for r in by_sheet if r.get("HOJA")]
    actual = [str(r["HOJA"]) for r in by_sheet]
    description = svc.get("serviceDescription") or ""
    official = parse_official_sheets(description)
    comparison = compare_sheets(official, actual)
    by_unit = group(client, base, 6, "UNIDAD", basin_esri)
    by_unit = sorted(by_unit, key=lambda r: -int(r.get("N", r.get("n", 0))))
    by_name = group(client, base, 6, "NAME", basin_esri)
    by_name = sorted(by_name, key=lambda r: -int(r.get("N", r.get("n", 0))))

    # Solo el subconjunto de la cuenca. Es la única descarga geométrica de esta
    # auditoría; no se descarga la capa nacional.
    features = fetch_geojson(client, base, 6, basin_esri)
    out_geojson = out_dir / "geologia_cuenca.geojson"
    out_geojson.write_text(
        json.dumps(features, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32717", always_xy=True)
    basin_geom = shape(
        json.loads(BASIN.read_text(encoding="utf-8"))["features"][0]["geometry"]
    )
    basin_metric = transform(transformer.transform, basin_geom)
    valid = invalid = empty = 0
    total_area = 0.0
    clipped_area = 0.0
    invalid_details = []
    for feature in features.get("features") or []:
        try:
            geom = shape(feature["geometry"])
        except Exception as exc:
            invalid += 1
            invalid_details.append(
                {
                    "objectid": (feature.get("properties") or {}).get("OBJECTID"),
                    "error": str(exc),
                }
            )
            continue
        if geom.is_empty:
            empty += 1
            continue
        if not geom.is_valid:
            invalid += 1
            from shapely.validation import explain_validity

            invalid_details.append(
                {
                    "objectid": (feature.get("properties") or {}).get("OBJECTID"),
                    "hoja": (feature.get("properties") or {}).get("HOJA"),
                    "unidad": (feature.get("properties") or {}).get("UNIDAD"),
                    "motivo": explain_validity(geom),
                }
            )
            continue
        valid += 1
        metric = transform(transformer.transform, geom)
        total_area += metric.area / 1e6
        clipped_area += metric.intersection(basin_metric).area / 1e6
    import hashlib

    geojson_hash = hashlib.sha256(out_geojson.read_bytes()).hexdigest()

    # Hojas (layer 0) para nombres y fechas. La capa 6 tiene el código sin guion.
    hojas_count = count(client, base, 0, basin_esri)
    hojas_features = query(
        client,
        base,
        0,
        geometry=basin_esri,
        out_fields="QDR_CODIGO_ALFANUMERICO,QDR_NOMBRE",
        return_geometry=False,
    )
    nombres = {
        normalize_sheet((f.get("attributes") or {}).get("QDR_CODIGO_ALFANUMERICO")): (
            (f.get("attributes") or {}).get("QDR_NOMBRE") or ""
        )
        for f in hojas_features.get("features") or []
    }
    return {
        "servicio": base,
        "descripcion": description,
        "copyright": svc.get("copyrightText"),
        "version_arcgis": svc.get("currentVersion"),
        "spatial_reference": svc.get("spatialReference"),
        "capas": [
            {"id": l.get("id"), "name": l.get("name"), "type": l.get("type")}
            for l in svc.get("layers") or []
        ],
        "layer_6": {
            "name": layer6.get("name"),
            "fields": [
                {"name": f.get("name"), "alias": f.get("alias"), "type": f.get("type")}
                for f in layer6.get("fields") or []
            ],
            "max_record_count": layer6.get("maxRecordCount"),
            "supported_query_formats": layer6.get("supportedQueryFormats"),
            "supports_pagination": (
                layer6.get("advancedQueryCapabilities") or {}
            ).get("supportsPagination"),
            "object_id_field": layer6.get("objectIdField"),
        },
        "layer_0": {
            "name": layer0.get("name"),
            "fields": [f.get("name") for f in layer0.get("fields") or []],
        },
        "conteo_cuenca": basin_count,
        "conteo_rectangulo_piura": envelope_count,
        "conteo_hojas_cuenca": hojas_count,
        "poligonos_por_hoja": [
            {
                "hoja": str(r.get("HOJA")),
                "n": int(r.get("N", r.get("n", 0))),
                "en_descripcion": normalize_sheet(r.get("HOJA")) in set(official),
                "nombre_hoja": nombres.get(normalize_sheet(r.get("HOJA")), ""),
            }
            for r in sorted(by_sheet, key=lambda x: str(x.get("HOJA")))
        ],
        "comparacion_hojas": comparison,
        "poligonos_por_unidad": by_unit[:40],
        "poligonos_por_name": by_name[:40],
        "geometria_cuenca": {
            "file": str(out_geojson.relative_to(ROOT)),
            "sha256": geojson_hash,
            "features": len(features.get("features") or []),
            "validas": valid,
            "invalidas": invalid,
            "vacias": empty,
            "invalidas_detalle": invalid_details,
            "area_poligonos_utm_km2": round(total_area, 3),
            "area_interseccion_utm_km2": round(clipped_area, 3),
            "crs_salida": "EPSG:4326 (consulta) / EPSG:32717 (área)",
        },
        "limitaciones": [
            "maxRecordCount=1000; resultOffset/resultRecordCount no soportados.",
            "La extracción completa requiere paginar por OBJECTID; aquí solo se descargó el subconjunto de la cuenca.",
            "WFS 2.0 se anuncia, pero GetFeature devolvió numberReturned sin miembros en la prueba.",
            "El certificado TLS de GEOCATMIN no es confiable en este entorno.",
            "La descripción oficial no coincide con las hojas que contienen polígonos.",
            "La licencia de descarga es no comercial; la aplicación a WFS/WMTS no está declarada.",
        ],
    }


def audit_geomorfologia(client: Client, basin_esri: dict) -> dict:
    base = SERVICES["geomorfologia"]
    svc = service_meta(client, base)
    layer = layer_meta(client, base, 0)
    envelope = {
        "rings": [
            [
                [-81.6, -6.6],
                [-78.8, -6.6],
                [-78.8, -3.8],
                [-81.6, -3.8],
                [-81.6, -6.6],
            ]
        ],
        "spatialReference": {"wkid": 4326},
    }
    return {
        "servicio": base,
        "descripcion": svc.get("serviceDescription"),
        "copyright": svc.get("copyrightText"),
        "spatial_reference": svc.get("spatialReference"),
        "campos": [
            {"name": f.get("name"), "alias": f.get("alias"), "type": f.get("type")}
            for f in layer.get("fields") or []
        ],
        "conteo_cuenca": count(client, base, 0, basin_esri),
        "conteo_rectangulo_piura": count(client, base, 0, envelope),
        "por_etiqueta": sorted(
            group(client, base, 0, "ETIQUETA", basin_esri),
            key=lambda r: -int(r.get("N", r.get("n", 0))),
        )[:40],
        "por_subunidad": sorted(
            group(client, base, 0, "SUBUNIDAD", basin_esri),
            key=lambda r: -int(r.get("N", r.get("n", 0))),
        )[:40],
        "metadato": parse_geonetwork_record(
            client, "893f41d0-cd70-4bcb-bfad-92bc215e2d82"
        ),
        "limitaciones": [
            "El metadato del registro declara 1:3 000 000, el abstract declara "
            "trabajo 1:100 000 y presentación 1:250 000; la capa no declara escala.",
            "No se usa para cálculos locales.",
        ],
    }


def audit_susceptibilidad(client: Client, basin_esri: dict) -> dict:
    base = SERVICES["susceptibilidad"]
    svc = service_meta(client, base)
    layer = layer_meta(client, base, 0)
    envelope = {
        "rings": [
            [
                [-81.6, -6.6],
                [-78.8, -6.6],
                [-78.8, -3.8],
                [-81.6, -3.8],
                [-81.6, -6.6],
            ]
        ],
        "spatialReference": {"wkid": 4326},
    }
    image = service_meta(client, SERVICES["imagen_susceptibilidad"])
    renderer = layer.get("drawingInfo") or {}
    return {
        "servicio": base,
        "spatial_reference": svc.get("spatialReference"),
        "campos": [
            {"name": f.get("name"), "alias": f.get("alias"), "type": f.get("type")}
            for f in layer.get("fields") or []
        ],
        "renderer": renderer,
        "conteo_cuenca": count(client, base, 0, basin_esri),
        "conteo_rectangulo_piura": count(client, base, 0, envelope),
        "por_gridcode": group(client, base, 0, "GRIDCODE", basin_esri),
        "por_leyenda": group(client, base, 0, "LEYENDA", basin_esri),
        "imagen": {
            "servicio": SERVICES["imagen_susceptibilidad"],
            "pixel_size_x": image.get("pixelSizeX"),
            "pixel_size_y": image.get("pixelSizeY"),
            "spatial_reference": image.get("spatialReference"),
            "capabilities": image.get("capabilities"),
        },
        "metadato": parse_geonetwork_record(
            client, "2183b121-1f29-4cef-96e2-dc102ae96a76"
        ),
        "leyenda_2018": LEYENDA_SUSCEPTIBILIDAD,
        "limitaciones": [
            "El metadato 2018 declara escala 1:1 000 000 y formato ráster.",
            "La capa vectorial solo tiene GRIDCODE 2/3/4; la leyenda 2018 tiene "
            "cuatro clases e incluye «Muy bajo o nulo».",
            "LEYENDA está nula o vacía en la capa vectorial.",
            "No es una probabilidad hidrológica.",
        ],
    }


def audit_peligros(client: Client, basin_esri: dict) -> dict:
    base = SERVICES["peligros"]
    svc = service_meta(client, base)
    layers = []
    for layer in svc.get("layers") or []:
        lid = layer.get("id")
        layers.append(
            {
                "id": lid,
                "name": layer.get("name"),
                "geometry_type": layer.get("geometryType"),
                "conteo_cuenca": count(client, base, lid, basin_esri),
            }
        )
    layer0 = layer_meta(client, base, 0)
    return {
        "servicio": base,
        "descripcion": svc.get("serviceDescription"),
        "copyright": svc.get("copyrightText"),
        "spatial_reference": svc.get("spatialReference"),
        "capas": layers,
        "campos_peligros": [
            {"name": f.get("name"), "alias": f.get("alias"), "type": f.get("type")}
            for f in layer0.get("fields") or []
        ],
        "metadato_2026": parse_geonetwork_record(
            client, "c5580ab5-7277-4858-8d16-a982bd2cc23b"
        ),
        "limitaciones": [
            "La descripción del MapServer dice febrero de 2013; el metadato 2026 "
            "declara actualización a octubre de 2026.",
            "Es un inventario heterogéneo de puntos y polígonos, no una capa "
            "homogénea de susceptibilidad.",
        ],
    }


def audit_zee(client: Client, memoria: dict) -> dict:
    pot = service_meta(client, ZEE_POT)
    dim = service_meta(client, ZEE_DIM)
    layer3 = layer_meta(client, ZEE_POT, 3)
    layer12 = layer_meta(client, ZEE_DIM, 12)
    classes3 = group(client, ZEE_POT, 3, "Nivel_Vuln")
    # La capa 12 no acepta groupBy en este servicio; se leen sus 19 filas.
    payload12 = query(
        client,
        ZEE_DIM,
        12,
        out_fields="Nivel_Vuln",
        return_geometry=False,
    )
    from collections import Counter

    c12 = Counter(
        (f.get("attributes") or {}).get("Nivel_Vuln")
        for f in payload12.get("features") or []
    )
    return {
        "servicios": {"potencialidades": ZEE_POT, "dimension": ZEE_DIM},
        "spatial_reference_pot": pot.get("spatialReference"),
        "spatial_reference_dim": dim.get("spatialReference"),
        "memoria": memoria,
        "capa_peligro": {
            "nombre": layer3.get("name"),
            "campos": [
                {"name": f.get("name"), "alias": f.get("alias"), "type": f.get("type")}
                for f in layer3.get("fields") or []
            ],
            "extent": layer3.get("extent"),
            "conteo": sum(int(r.get("N", r.get("n", 0))) for r in classes3),
            "por_clase": classes3,
            "descripcion": layer3.get("description"),
        },
        "capa_vulnerabilidad": {
            "nombre": layer12.get("name"),
            "campos": [
                {"name": f.get("name"), "alias": f.get("alias"), "type": f.get("type")}
                for f in layer12.get("fields") or []
            ],
            "extent": layer12.get("extent"),
            "conteo": sum(c12.values()),
            "por_clase": [
                {"Nivel_Vuln": k, "n": v} for k, v in sorted(c12.items())
            ],
            "descripcion": layer12.get("description"),
        },
        "advertencia": (
            "La capa se llama «Peligro Inundación» pero el campo es "
            "«Nivel_Vuln». La Memoria 2012 describe un submodelo de peligro y "
            "otro de vulnerabilidad; no se puede asignar la semántica por "
            "intuición. No se usa como probabilidad hidrológica."
        ),
        "limitaciones": [
            "El servicio no declara fecha, escala, método ni licencia.",
            "La Memoria 2012 no declara licencia de reutilización.",
            "La capa de peligro tiene 78 polígonos; la de vulnerabilidad, 19.",
        ],
    }


def audit_wfs_wmts(client: Client, basin_esri: dict) -> dict:
    wfs_url = (
        f"{ARCGIS_WFS}/SERV_GEOLOGIA_100K_INTEGRADA/MapServer/WFSServer"
        "?service=WFS&version=2.0.0&request=GetCapabilities"
    )
    wfs_xml = client.get_text(wfs_url)
    wfs = parse_wfs_capabilities(wfs_xml)
    ws = wfs.get("feature_types") or []
    geologia_name = next(
        (ft["name"] for ft in ws if ft["name"].endswith("Geología")), None
    )
    hits = None
    sample = None
    if geologia_name:
        base = (
            f"{ARCGIS_WFS}/SERV_GEOLOGIA_100K_INTEGRADA/MapServer/WFSServer"
            "?service=WFS&version=2.0.0&request=GetFeature"
            f"&typeNames={requests.utils.quote(geologia_name, safe=':')}"
        )
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(client.get_text(base + "&resultType=hits"))
            hits = root.attrib.get("numberMatched")
            root = ET.fromstring(client.get_text(base + "&count=2"))
            sample = {
                "numberMatched": root.attrib.get("numberMatched"),
                "numberReturned": root.attrib.get("numberReturned"),
                "members": len(
                    root.findall(
                        "{http://www.opengis.net/wfs/2.0}member"
                    )
                ),
                "next": root.attrib.get("next"),
            }
        except Exception as exc:  # el WFS puede fallar sin tumbar la auditoría
            sample = {"error": str(exc)}
    wmts_url = (
        f"{ARCGIS}/SERV_GEOLOGIA_100K_INTEGRADA/MapServer/WMTS/1.0.0/"
        "WMTSCapabilities.xml"
    )
    wmts = parse_wmts_capabilities(client.get_text(wmts_url))
    return {
        "wfs": {
            **wfs,
            "url": wfs_url,
            "number_matched_geologia": hits,
            "get_feature_prueba": sample,
            "limitaciones": [
                "GetFeature devolvió numberReturned sin miembros en la prueba.",
                "El bbox EPSG:4326 usa orden lat/lon; el orden lon/lat devuelve 0.",
                "Fees=1 y AccessConstraints=referencial no equivalen a licencia.",
            ],
        },
        "wmts": {
            **wmts,
            "url": wmts_url,
            "tipo": "teselas ráster; no vectorial",
        },
    }


def audit_catalogo_idep(client: Client) -> dict:
    search_url = f"{GEONETWORK}/srv/api/search/records/_search"
    queries = {}
    for label, query_text in (
        ("servicio", "SERV_GEOLOGIA_100K_INTEGRADA"),
        ("geologia_100", 'resourceTitleObject.default:(geología AND 100*)'),
        ("geomorfologia_piura", 'Piura AND "Geomorfología"'),
        ("susceptibilidad_piura", 'Piura AND "susceptibilidad" AND "inundación"'),
    ):
        try:
            payload = client.post_json_body(
                search_url,
                {"query": {"query_string": {"query": query_text}}, "size": 20},
            )
            queries[label] = {
                "query": query_text,
                "total": ((payload.get("hits") or {}).get("total") or {}).get("value"),
                "records": catalog_search_titles(payload),
            }
        except Exception as exc:
            queries[label] = {"query": query_text, "error": str(exc)}
    record = None
    try:
        record = parse_geonetwork_record(
            client, "0cc58287-29e0-415c-bf19-63bb1f51c59a"
        )
    except Exception as exc:
        record = {"error": str(exc)}
    return {
        "catalogo": GEONETWORK,
        "host_idep": "https://idep.ingemmet.gob.pe/ (no resuelve en esta red)",
        "busquedas": queries,
        "registro_mas_cercano": record,
        "limitaciones": [
            "No se localizó un registro del servicio SERV_GEOLOGIA_100K_INTEGRADA.",
            "El registro más cercano no enlaza WFS/WMTS.",
            "La consulta CSW con AnyText presenta un error interno de GeoNetwork; "
            "se usó la API de búsqueda JSON.",
        ],
    }


def write_summaries(out_dir: Path, result: dict) -> None:
    import csv

    geo = result.get("geologia") or {}
    rows = geo.get("poligonos_por_hoja") or []
    with (out_dir / "hojas_geologia_cuenca.csv").open(
        "w", encoding="utf-8", newline=""
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["hoja", "nombre_hoja", "n", "en_descripcion"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "hoja": row.get("hoja"),
                    "nombre_hoja": row.get("nombre_hoja"),
                    "n": row.get("n"),
                    "en_descripcion": "sí" if row.get("en_descripcion") else "no",
                }
            )
    sus = result.get("susceptibilidad") or {}
    with (out_dir / "clases_susceptibilidad.csv").open(
        "w", encoding="utf-8", newline=""
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=["GRIDCODE", "n"])
        writer.writeheader()
        for row in sus.get("por_gridcode") or []:
            writer.writerow(
                {
                    "GRIDCODE": row.get("GRIDCODE"),
                    "n": row.get("N", row.get("n")),
                }
            )
    zee = result.get("zee") or {}
    with (out_dir / "zee_piura_clases.csv").open(
        "w", encoding="utf-8", newline=""
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=["capa", "clase", "n"])
        writer.writeheader()
        for row in zee.get("capa_peligro", {}).get("por_clase") or []:
            writer.writerow(
                {
                    "capa": "Peligro Inundación",
                    "clase": row.get("Nivel_Vuln"),
                    "n": row.get("N", row.get("n")),
                }
            )
        for row in zee.get("capa_vulnerabilidad", {}).get("por_clase") or []:
            writer.writerow(
                {
                    "capa": "Vulnerabilidad frente a Inundaciones",
                    "clase": row.get("Nivel_Vuln"),
                    "n": row.get("n"),
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DEFAULT)
    parser.add_argument("--insecure", action="store_true")
    parser.add_argument("--skip-memoria", action="store_true")
    parser.add_argument("--refresh-memoria", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()
    ensure_not_public(args.out_dir)
    ensure_not_public(args.raw_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    client = Client(args.timeout, args.retries, args.insecure)
    if args.insecure:
        print("ADVERTENCIA: verificación TLS desactivada para esta auditoría.")
    geom, basin_esri, basin_hash = load_basin()
    result = {
        "generado": now(),
        "publicado": False,
        "insecure_tls": args.insecure,
        "cuenca": {
            "file": str(BASIN.relative_to(ROOT)),
            "sha256": basin_hash,
            "geometry_type": geom.get("type"),
        },
        "licencia_ingemmet": {},
        "errores": [],
    }

    def section(name: str, fn):
        print(f"  {name}…")
        try:
            result[name] = fn()
        except Exception as exc:
            result["errores"].append(f"{name}: {exc}")
            print(f"    ERROR: {exc}")

    section("geologia", lambda: audit_geologia(client, basin_esri, args.out_dir))
    section("geomorfologia", lambda: audit_geomorfologia(client, basin_esri))
    section("susceptibilidad", lambda: audit_susceptibilidad(client, basin_esri))
    section("peligros", lambda: audit_peligros(client, basin_esri))
    section("wfs_wmts", lambda: audit_wfs_wmts(client, basin_esri))
    section("catalogo_idep", lambda: audit_catalogo_idep(client))

    try:
        print("  licencia…")
        html = client.get_text(LICENSE_URL)
        result["licencia_ingemmet"] = {
            "url": LICENSE_URL,
            "sha256": sha256_text(html),
            **license_summary(html),
        }
    except Exception as exc:
        result["errores"].append(f"licencia: {exc}")
        print(f"    ERROR: {exc}")

    memoria = None
    if not args.skip_memoria:
        try:
            print("  memoria ZEE…")
            memoria = download_memoria(
                client, args.raw_dir, args.refresh_memoria
            )
        except Exception as exc:
            result["errores"].append(f"memoria_zee: {exc}")
            print(f"    ERROR: {exc}")
    section("zee", lambda: audit_zee(client, memoria or {}))

    write_summaries(args.out_dir, result)
    (args.out_dir / "auditoria.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nlisto: {args.out_dir / 'auditoria.json'}")
    if result["errores"]:
        print(f"  {len(result['errores'])} error(es)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
