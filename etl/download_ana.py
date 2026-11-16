#!/usr/bin/env python3
"""Descarga los límites de la cuenca Piura desde el geoservidor de ANA/MINAM.

Fuente: Unidad Hidrográfica y Sub Cuenca Hidrográfica (ANA, R.M. 033-2008-AG).
Salida: data/raw/limits.json con el mismo formato que consume build_layers.py.

La capa oficial no trae «Bajo Piura» como subcuenca; se calcula como el resto de
la cuenca después de restar las ocho subcuencas publicadas. Esa decisión queda
declarada en el propio archivo (`metodo`).

Correcciones de integridad (v0.3):
- «Bajo Piura» se calcula sobre las geometrías completas y se simplifica una sola
  vez, después de la diferencia. Antes se simplificaban las subcuencas y recién
  después se restaban, lo que producía un anillo inválido y un hueco de ~3 km².
- Se conservan agujeros y componentes MultiPolygon. Si una fuente trae varios
  polígonos, se guardan en `polygons`; no se elige silenciosamente el mayor.
- El área publicada se calcula de la geometría (geodésica). `Shape_Area` de ANA
  se conserva aparte porque está calculado en EPSG:32718 (UTM 18S), fuera de la
  zona 17S que corresponde a esta cuenca.

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
from pyproj import Geod
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.ops import unary_union
from shapely.validation import explain_validity, make_valid

ROOT = Path(__file__).resolve().parents[1]
SERVICE = (
    "https://geoservidorperu.minam.gob.pe/arcgis/rest/services/"
    "ZEE_VISOR/09_CARACTERIZACI%C3%93N_DEL_TERRITORIO_PIURA/MapServer"
)
BASIN_LAYER = 18
SUBBASIN_LAYER = 19
DEFAULT_CODE = "1378"
GEOD = Geod(ellps="WGS84")
# Componentes menores que esto son artefactos numéricos de la diferencia.
MIN_COMPONENT_AREA_M2 = 1_000.0


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


def area_km2(geom) -> float:
    """Área geodésica (WGS84), independiente de la proyección de la fuente."""
    return abs(GEOD.geometry_area_perimeter(geom)[0]) / 1e6


def polygonal_parts(geom) -> list[Polygon]:
    if geom is None or geom.is_empty:
        return []
    geom = make_valid(geom)
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    parts: list[Polygon] = []
    if hasattr(geom, "geoms"):
        for child in geom.geoms:
            parts.extend(polygonal_parts(child))
    return parts


def simplify_geom(geom, tolerance: float):
    """Simplifica una sola vez, conservando topología y agujeros."""
    clean = make_valid(geom)
    simplified = clean.simplify(tolerance, preserve_topology=True)
    return make_valid(simplified)


def rounded_ring(coords, nd: int = 5) -> list[list[float]]:
    return [[round(float(x), nd), round(float(y), nd)] for x, y in coords]


def polygon_record(poly: Polygon) -> dict:
    ring = rounded_ring(poly.exterior.coords)
    if ring and ring[0] != ring[-1]:
        ring.append(ring[0])
    holes = []
    for interior in poly.interiors:
        hole = rounded_ring(interior.coords)
        if hole and hole[0] != hole[-1]:
            hole.append(hole[0])
        holes.append(hole)
    return {"ring": ring, "holes": holes}


def geometry_record(geom, tolerance: float, label: str) -> dict:
    """Simplifica y serializa un Polygon o MultiPolygon sin perder partes."""
    simplified = simplify_geom(geom, tolerance)
    if not simplified.is_valid:
        raise SystemExit(f"{label}: la geometría simplificada no es válida: {explain_validity(simplified)}")
    parts = polygonal_parts(simplified)
    if not parts:
        raise SystemExit(f"{label}: la geometría no contiene polígonos")
    kept: list[Polygon] = []
    dropped_area = 0.0
    for part in parts:
        if part.area * 111_320 * 110_540 >= MIN_COMPONENT_AREA_M2:
            kept.append(part)
        else:
            dropped_area += part.area * 111_320 * 110_540
    if not kept:
        raise SystemExit(f"{label}: todos los componentes quedaron por debajo del umbral")
    if dropped_area:
        print(f"  {label}: descartados {len(parts) - len(kept)} fragmentos de {dropped_area / 1e6:.4f} km²")
    if len(kept) == 1:
        record = polygon_record(kept[0])
        record["area_km2"] = round(area_km2(kept[0]), 1)
        record["polygons"] = [{"ring": record["ring"], "holes": record["holes"]}]
    else:
        merged = MultiPolygon(kept)
        record = {
            "ring": polygon_record(kept[0])["ring"],
            "holes": polygon_record(kept[0])["holes"],
            "polygons": [polygon_record(p) for p in kept],
            "area_km2": round(area_km2(merged), 1),
        }
    return record


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
    basin_source_area = basin_feature["properties"].get("Shape_Area")
    if basin_source_area is not None:
        basin_source_area = float(basin_source_area) / 1e6
    print(f"  cuenca fuente: {basin_geom.geom_type} · {area_km2(basin_geom):.1f} km² geodésicos")

    print("descargando subcuencas…")
    sub_data = query_layer(SUBBASIN_LAYER, f"COD_CUENCA={int(args.code)}")
    if not sub_data.get("features"):
        raise SystemExit(f"ANA no devolvió subcuencas para {args.code}")

    sub_geoms: list[tuple[str, object, float | None]] = []
    for feature in sub_data["features"]:
        props = feature["properties"]
        geom = shape(feature["geometry"])
        source_area = props.get("Shape_Area")
        sub_geoms.append(
            (
                props["SUB_CUENCA"].strip(),
                geom,
                float(source_area) / 1e6 if source_area is not None else None,
            )
        )

    # Resta sobre las geometrías completas, antes de simplificar. Así el resto
    # no hereda los cortes internos de ocho simplificaciones independientes.
    union = unary_union([make_valid(geom) for _, geom, _ in sub_geoms])
    remainder = make_valid(make_valid(basin_geom).difference(union))
    remainder_parts = polygonal_parts(remainder)
    if not remainder_parts:
        raise SystemExit("la diferencia de la cuenca con las subcuencas quedó vacía")
    remainder_parts = [p for p in remainder_parts if p.area * 111_320 * 110_540 >= MIN_COMPONENT_AREA_M2]
    if not remainder_parts:
        raise SystemExit("la diferencia de la cuenca con las subcuencas solo dejó fragmentos mínimos")
    remainder_geom = remainder_parts[0] if len(remainder_parts) == 1 else MultiPolygon(remainder_parts)
    print(
        f"  Bajo Piura: {len(remainder_parts)} componente(s) · "
        f"{area_km2(remainder_geom):.1f} km² geodésicos"
    )

    subbasins = []
    for name, geom, source_area in sub_geoms:
        record = geometry_record(geom, args.tolerance, name)
        record.update(
            {
                "name": name,
                "area_fuente_km2": round(source_area, 1) if source_area is not None else None,
                "origen": "ANA",
            }
        )
        subbasins.append(record)

    # Bajo Piura se coloca primero para conservar el orden que consume la web.
    bajo = geometry_record(remainder_geom, args.tolerance, "Bajo Piura")
    bajo.update(
        {
            "name": "Bajo Piura",
            "area_fuente_km2": round(basin_source_area - sum(s[2] for s in sub_geoms), 1)
            if basin_source_area is not None
            else None,
            "origen": "derivada: cuenca ANA menos las ocho subcuencas publicadas",
        }
    )
    subbasins.insert(0, bajo)

    basin_record = geometry_record(basin_geom, args.tolerance, "cuenca")
    output = {
        "source": "ANA — Unidades Hidrográficas Pfafstetter 1:100 000 (R.M. 033-2008-AG)",
        "code": args.code,
        "area_km2": basin_record["area_km2"],
        "area_fuente_km2": round(basin_source_area, 1) if basin_source_area is not None else None,
        "area_fuente_crs": "EPSG:32718 (UTM 18S), calculado por ANA; el polígono está en la zona 17S",
        "ring": basin_record["ring"],
        "holes": basin_record["holes"],
        "polygons": basin_record["polygons"],
        "subbasins": subbasins,
        "metodo": (
            "Descarga GeoJSON del geoservidor ANA/MINAM. Cuenca y subcuencas simplificadas "
            "una sola vez con tolerancia de 0.0006° y preserve_topology=True. «Bajo Piura» "
            "se calcula como la diferencia entre la cuenca completa y las ocho subcuencas "
            "publicadas, antes de simplificar; luego se simplifica junto con el resto. "
            "Las áreas publicadas son geodésicas (WGS84). Shape_Area de ANA se conserva como "
            "area_fuente_km2 y está calculado en EPSG:32718 (UTM 18S)."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"  {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}")
    print(f"  cuenca: {output['area_km2']:.1f} km² · {len(output['ring'])} puntos")
    for sub in output["subbasins"]:
        print(f"  {sub['name']:26s} {sub['area_km2']:7.1f} km² · {len(sub['ring'])} puntos")


if __name__ == "__main__":
    main()
