#!/usr/bin/env python3
"""Descarga los límites de la cuenca Piura desde el geoservidor de ANA/MINAM.

Fuente: Unidad Hidrográfica y Sub Cuenca Hidrográfica (ANA, R.M. 033-2008-AG).
Salida: data/raw/limits.json con el mismo formato que consume build_layers.py.

La capa oficial no trae «Bajo Piura» como subcuenca; se calcula como el resto de
la cuenca después de restar las ocho subcuencas publicadas. Esa decisión queda
declarada en el propio archivo (`metodo`).

Uso:
    python3 etl/download_ana.py
    python3 etl/download_ana.py --out data/raw/limits.json --force
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests
import shapely
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
SERVICE = (
    "https://geoservidorperu.minam.gob.pe/arcgis/rest/services/"
    "ZEE_VISOR/09_CARACTERIZACI%C3%93N_DEL_TERRITORIO_PIURA/MapServer"
)
BASIN_LAYER = 18
SUBBASIN_LAYER = 19
DEFAULT_CODE = "1378"


def query_layer(layer: int, where: str) -> dict:
    url = f"{SERVICE}/{layer}/query"
    params = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    response = requests.get(url, params=params, timeout=120)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"ANA respondió con error: {data['error']}")
    return data


def largest_polygon(geom):
    if geom.geom_type == "Polygon":
        return geom
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda g: g.area)
    raise ValueError(f"geometría no poligonal: {geom.geom_type}")


def simplify_ring(ring, tolerance: float):
    geom = largest_polygon(shapely.make_valid(Polygon(ring)).simplify(tolerance, preserve_topology=True))
    coords = [[round(x, 5), round(y, 5)] for x, y in geom.exterior.coords]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return coords


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", default=DEFAULT_CODE, help="código Pfafstetter de la cuenca (1378)")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "raw" / "limits.json")
    parser.add_argument("--tolerance", type=float, default=0.0006, help="tolerancia de simplificación en grados")
    parser.add_argument("--force", action="store_true", help="sobrescribir la salida si ya existe")
    args = parser.parse_args()

    if args.out.exists() and not args.force:
        raise SystemExit(f"{args.out} ya existe. Usa --force para reemplazarlo.")

    print(f"descargando cuenca {args.code} desde ANA…")
    basin = query_layer(BASIN_LAYER, f"CODIGO='{args.code}'")
    if not basin.get("features"):
        raise SystemExit(f"ANA no devolvió la cuenca {args.code}")
    basin_feature = basin["features"][0]
    basin_geom = shape(basin_feature["geometry"])
    basin_area = basin_feature["properties"]["Shape_Area"] / 1e6

    print("descargando subcuencas…")
    sub_data = query_layer(SUBBASIN_LAYER, f"COD_CUENCA={int(args.code)}")
    if not sub_data.get("features"):
        raise SystemExit(f"ANA no devolvió subcuencas para {args.code}")

    subbasins = []
    for feature in sub_data["features"]:
        props = feature["properties"]
        geom = shape(feature["geometry"])
        subbasins.append(
            {
                "name": props["SUB_CUENCA"].strip(),
                "area_km2": round(props["Shape_Area"] / 1e6, 1),
                "ring": simplify_ring(list(geom.exterior.coords), args.tolerance),
            }
        )

    union = unary_union([shapely.make_valid(shape(f["geometry"])) for f in sub_data["features"]])
    remainder = largest_polygon(shapely.make_valid(basin_geom).difference(union))
    if remainder.is_empty:
        raise SystemExit("la diferencia de la cuenca con las subcuencas quedó vacía")

    subbasins.insert(
        0,
        {
            "name": "Bajo Piura",
            "area_km2": round(basin_area - sum(s["area_km2"] for s in subbasins), 1),
            "ring": simplify_ring(list(remainder.exterior.coords), args.tolerance),
        },
    )

    output = {
        "source": "ANA — Unidades Hidrográficas Pfafstetter 1:100 000 (R.M. 033-2008-AG)",
        "code": args.code,
        "area_km2": round(basin_area, 1),
        "ring": simplify_ring(list(basin_geom.exterior.coords), args.tolerance),
        "subbasins": subbasins,
        "metodo": (
            "Descarga GeoJSON del geoservidor ANA/MINAM. Cuenca y subcuencas simplificadas "
            "con tolerancia de 0.0006°. «Bajo Piura» se calcula como la diferencia entre "
            "la cuenca oficial y las ocho subcuencas publicadas."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"  {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}")
    print(f"  cuenca: {output['area_km2']:.0f} km² · {len(output['ring'])} puntos")
    for sub in output["subbasins"]:
        print(f"  {sub['name']:26s} {sub['area_km2']:7.1f} km² · {len(sub['ring'])} puntos")


if __name__ == "__main__":
    main()
