#!/usr/bin/env python3
"""Utilidades para auditar servicios geoespaciales sin publicar sus datos.

No contiene lógica de publicación. Convierte metadatos ArcGIS/WFS/WMTS en
estructuras verificables, normaliza códigos de hoja y compara leyendas. El
cliente HTTP vive en `audit_geoservicios.py` para que estas funciones se puedan
probar con fixtures y sin red.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Iterable

WFS_NS = {
    "wfs": "http://www.opengis.net/wfs/2.0",
    "ows": "http://www.opengis.net/ows/1.1",
}
WMTS_NS = {
    "wmts": "http://www.opengis.net/wmts/1.0",
    "ows": "http://www.opengis.net/ows/1.1",
}


def normalize_sheet(code: object) -> str:
    """Normaliza 10-b, 10b, 10B y 10 b a '10b'."""
    if code is None:
        return ""
    text = str(code).strip().lower().replace("ñ", "n")
    text = re.sub(r"[^0-9a-z]", "", text)
    return text.lstrip("0") or "0"


def parse_official_sheets(description: str) -> list[str]:
    """Extrae códigos tipo 09a/14h de la descripción del servicio.

    Solo considera líneas con varias hojas separadas por comas. Así se evita
    confundir «Y 27 líneas de secciones» con la hoja 27l.
    """
    salida = []
    for line in description.lower().splitlines():
        matches = re.findall(
            r"\b(?:0?\d{1,2})\s*[-]?\s*[a-zñ]\b", line
        )
        codes = []
        for item in matches:
            code = normalize_sheet(item)
            if re.fullmatch(r"\d{1,2}[a-zñ]", code):
                codes.append(code)
        if len(codes) < 3:
            continue
        for code in codes:
            if code not in salida:
                salida.append(code)
    return salida


def compare_sheets(official: Iterable[str], actual: Iterable[str]) -> dict:
    of = {normalize_sheet(x) for x in official if normalize_sheet(x)}
    ac = {normalize_sheet(x) for x in actual if normalize_sheet(x)}
    return {
        "oficiales": sorted(of),
        "reales": sorted(ac),
        "en_ambos": sorted(of & ac),
        "reales_fuera_de_la_descripcion": sorted(ac - of),
        "descritas_sin_poligonos_en_la_cuenca": sorted(of - ac),
    }


def parse_wfs_capabilities(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    service = root.find("ows:ServiceIdentification", WFS_NS)
    fees = service.findtext("ows:Fees", default="", namespaces=WFS_NS) if service is not None else ""
    access = (
        service.findtext("ows:AccessConstraints", default="", namespaces=WFS_NS)
        if service is not None
        else ""
    )
    title = (
        service.findtext("ows:Title", default="", namespaces=WFS_NS)
        if service is not None
        else ""
    )
    abstract = (
        service.findtext("ows:Abstract", default="", namespaces=WFS_NS)
        if service is not None
        else ""
    )
    feature_types = []
    for ft in root.findall("wfs:FeatureTypeList/wfs:FeatureType", WFS_NS):
        name = ft.findtext("wfs:Name", default="", namespaces=WFS_NS)
        crs = ft.findtext("wfs:DefaultCRS", default="", namespaces=WFS_NS)
        feature_types.append({"name": name, "default_crs": crs})
    operations = []
    for op in root.findall("ows:OperationsMetadata/ows:Operation", WFS_NS):
        operations.append(op.attrib.get("name", ""))
    return {
        "title": title,
        "abstract": abstract,
        "fees": fees,
        "access_constraints": access,
        "feature_types": feature_types,
        "operations": operations,
    }


def parse_wmts_capabilities(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    service = root.find("ows:ServiceIdentification", WMTS_NS)
    title = (
        service.findtext("ows:Title", default="", namespaces=WMTS_NS)
        if service is not None
        else ""
    )
    formats = [
        el.text
        for el in root.findall(
            "wmts:Contents/wmts:Layer/wmts:Format", WMTS_NS
        )
        if el.text
    ]
    matrix_sets = [
        el.text
        for el in root.findall(
            "wmts:Contents/wmts:TileMatrixSet/ows:Identifier", WMTS_NS
        )
        if el.text
    ]
    layers = [
        el.text
        for el in root.findall(
            "wmts:Contents/wmts:Layer/ows:Identifier", WMTS_NS
        )
        if el.text
    ]
    return {
        "title": title,
        "formats": sorted(set(formats)),
        "tile_matrix_sets": matrix_sets,
        "layers": layers,
    }


def geojson_to_esri_geometry(geom: dict) -> dict:
    """Convierte un Polygon/MultiPolygon GeoJSON a Esri JSON de anillos."""
    if not isinstance(geom, dict):
        raise ValueError("geometría no es un objeto")
    gtype = geom.get("type")
    coords = geom.get("coordinates") or []
    if gtype == "Polygon":
        polygons = [coords]
    elif gtype == "MultiPolygon":
        polygons = coords
    else:
        raise ValueError(f"geometría no poligonal: {gtype}")
    rings = []
    for polygon in polygons:
        for ring in polygon:
            rings.append([[float(x), float(y)] for x, y in ring])
    if not rings:
        raise ValueError("geometría sin anillos")
    return {"rings": rings, "spatialReference": {"wkid": 4326}}


def count_values(features: Iterable[dict], field: str) -> list[dict]:
    counter = Counter()
    for feature in features:
        props = feature.get("properties") or feature.get("attributes") or {}
        value = props.get(field)
        counter[value] += 1
    return [
        {field: value, "n": count}
        for value, count in sorted(counter.items(), key=lambda item: str(item[0]))
    ]


def arcgis_json_to_geojson(payload: dict) -> dict:
    """Convierte una respuesta `f=json` de polígonos a GeoJSON.

    Se usa solo para el subconjunto de la cuenca, que cabe en una respuesta.
    No intenta reparar anillos ni unir partes: si el servicio devuelve anillos
    ambiguos, el auditor debe fallar y no inventar la topología.
    """
    features = []
    sr = (payload.get("spatialReference") or {}).get("wkid")
    for item in payload.get("features") or []:
        attrs = item.get("attributes") or {}
        geom = item.get("geometry") or {}
        rings = geom.get("rings") or []
        if not rings:
            continue
        if len(rings) == 1:
            geometry = {"type": "Polygon", "coordinates": [rings[0]]}
        else:
            geometry = {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}
        features.append(
            {
                "type": "Feature",
                "properties": attrs,
                "geometry": geometry,
            }
        )
    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": f"EPSG:{sr}"}} if sr else None,
        "features": features,
    }


def catalog_search_titles(payload: dict) -> list[dict]:
    hits = ((payload or {}).get("hits") or {}).get("hits") or []
    out = []
    for hit in hits:
        source = hit.get("_source") or {}
        title = (
            (source.get("resourceTitleObject") or {}).get("default")
            or (source.get("resourceTitleObject") or {}).get("langspa")
            or ""
        )
        out.append(
            {
                "uuid": hit.get("_id"),
                "title": title,
                "abstract": (
                    (source.get("resourceAbstractObject") or {}).get("default") or ""
                )[:400],
            }
        )
    return out


def strip_html(html: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def license_summary(html: str) -> dict:
    text = strip_html(html)
    def between(start: str, end: str | None = None) -> str:
        idx = text.find(start)
        if idx < 0:
            return ""
        end_idx = text.find(end, idx) if end else -1
        return text[idx : end_idx if end_idx > 0 else idx + 900].strip()

    return {
        "titulo": "Licencia para Uso No Comercial" if "Licencia para Uso No Comercial" in text else "",
        "datos": between("Datos.-", "Duración y término"),
        "software": between("Software.-", "Datos.-"),
        "duracion": between("Duración y término:", "Ley aplicable"),
        "texto": text[:2500],
    }


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()
