#!/usr/bin/env python3
"""Clasificación geográfica de estaciones contra la cuenca ANA publicada.

La relación topológica se calcula con la geometría que el atlas ya publica
(`web/public/data/cuenca.geojson` y `subcuencas.geojson`). La distancia se mide
en EPSG:32717, la zona UTM del polígono. No se usa un umbral arbitrario para
decidir si una estación exterior es "relevante": todas las estaciones de Piura
que quedan fuera se conservan como contexto regional y se identifican como no
representativas de la cuenca.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[1]
BASIN = ROOT / "web" / "public" / "data" / "cuenca.geojson"
SUBBASINS = ROOT / "web" / "public" / "data" / "subcuencas.geojson"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def _geometries():
    import json

    cuenca_data = json.loads(BASIN.read_text(encoding="utf-8"))
    cuenca = shape(cuenca_data["features"][0]["geometry"])
    if not cuenca.is_valid or cuenca.is_empty:
        raise ValueError("cuenca.geojson no es una geometría válida")
    subs_data = json.loads(SUBBASINS.read_text(encoding="utf-8"))
    subs = []
    for feature in subs_data.get("features", []):
        nombre = (feature.get("properties") or {}).get("nombre", "?")
        geom = shape(feature["geometry"])
        if not geom.is_valid or geom.is_empty:
            raise ValueError(f"subcuenca {nombre} no es una geometría válida")
        subs.append((nombre, geom))
    return cuenca, subs


@lru_cache(maxsize=1)
def _transformer() -> Transformer:
    return Transformer.from_crs("EPSG:4326", "EPSG:32717", always_xy=True)


def _to_metric(geom):
    return transform(_transformer().transform, geom)


def classify_station(
    longitude: float | None,
    latitude: float | None,
    department: str = "PIURA",
) -> dict:
    """Devuelve la relación con la cuenca y la distancia al borde.

    Si las coordenadas no son numéricas o están fuera de rango, devuelve un
    resultado vacío y explícito; no inventa una ubicación.
    """
    empty = {
        "relacion_cuenca": "",
        "distancia_borde_km": None,
        "subcuenca_mas_cercana": "",
        "clasificacion": "",
        "nota_geografica": "coordenada inválida; no se clasifica",
    }
    if not isinstance(longitude, (int, float)) or isinstance(longitude, bool):
        return empty
    if not isinstance(latitude, (int, float)) or isinstance(latitude, bool):
        return empty
    if not (-180 <= float(longitude) <= 180 and -90 <= float(latitude) <= 90):
        return empty

    cuenca, subs = _geometries()
    punto = Point(float(longitude), float(latitude))
    dentro = bool(cuenca.covers(punto))
    cuenca_m = _to_metric(cuenca)
    punto_m = _to_metric(punto)
    distancia = punto_m.distance(cuenca_m.boundary) / 1000.0

    sub_nombre = ""
    sub_dist = float("inf")
    for nombre, geom in subs:
        geom_m = _to_metric(geom)
        if geom.covers(punto):
            sub_nombre = nombre
            sub_dist = 0.0
            break
        d = punto_m.distance(geom_m) / 1000.0
        if d < sub_dist:
            sub_dist = d
            sub_nombre = nombre

    if dentro:
        clasificacion = "dentro_cuenca"
        nota = "Dentro de la cuenca ANA"
    elif str(department or "").strip().upper() == "PIURA":
        clasificacion = "fuera_cuenca_contexto_regional"
        nota = (
            "Fuera de la cuenca ANA; se conserva como contexto regional "
            "y no se mezcla con las estaciones de la cuenca"
        )
    else:
        clasificacion = "fuera_ambito_estudio"
        nota = "Fuera del departamento de Piura y de la cuenca ANA"
    if 0 < distancia <= 1:
        nota += "; caso límite de borde (≤ 1 km)"

    return {
        "relacion_cuenca": "dentro" if dentro else "fuera",
        "distancia_borde_km": round(distancia, 2),
        "subcuenca_mas_cercana": sub_nombre,
        "clasificacion": clasificacion,
        "nota_geografica": nota,
    }
