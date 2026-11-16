#!/usr/bin/env python3
"""Descarga los límites de la cuenca Piura desde el geoservidor de ANA/MINAM.

Fuente: Unidad Hidrográfica y Sub Cuenca Hidrográfica (ANA, R.M. 033-2008-AG).
Salida: data/raw/limits.json con el mismo formato que consume build_layers.py.

La capa oficial no trae «Bajo Piura» como subcuenca; se calcula como el resto de
la cuenca después de restar las ocho subcuencas publicadas. Esa decisión queda
declarada en el propio archivo (`metodo`).

Correcciones de integridad (v0.4):
- «Bajo Piura» se calcula sobre las geometrías completas y se simplifica una sola
  vez, después de la diferencia.
- La cuenca y las nueve subcuencas se simplifican por separado y luego se
  reconcilian como una partición topológica: cada cara del grafo de límites se
  asigna a la subcuenca con mayor solapamiento y los huecos sin solapamiento a
  la más cercana. Así desaparecen los 0,78 km² de solapamientos y el hueco de
  1,48 km² que dejaba la simplificación independiente, sin inventar superficie.
- Se conservan agujeros y componentes MultiPolygon. Si una subcuenca trae un
  agujero interior, la reconciliación se detiene: no se rellena en silencio.
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

try:  # Ejecución como módulo (`python -m etl.download_ana`)
    from etl.topology import reconcile_partition
except ModuleNotFoundError:  # Ejecución directa (`python etl/download_ana.py`)
    from topology import reconcile_partition

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
    return abs(GEOD.geometry_area_perimeter(make_valid(geom))[0]) / 1e6


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


def polygon_record(poly: Polygon, nd: int = 5) -> dict:
    ring = rounded_ring(poly.exterior.coords, nd)
    if ring and ring[0] != ring[-1]:
        ring.append(ring[0])
    holes = []
    for interior in poly.interiors:
        hole = rounded_ring(interior.coords, nd)
        if hole and hole[0] != hole[-1]:
            hole.append(hole[0])
        holes.append(hole)
    return {"ring": ring, "holes": holes}


def geometry_record_from_geometry(geom, label: str, nd: int = 5) -> dict:
    """Serializa un Polygon/MultiPolygon ya simplificado, sin perder partes."""
    clean = make_valid(geom)
    if not clean.is_valid:
        raise SystemExit(f"{label}: la geometría no es válida: {explain_validity(clean)}")
    parts = polygonal_parts(clean)
    if not parts:
        raise SystemExit(f"{label}: la geometría no contiene polígonos")

    # No se descartan componentes: la reconciliación ya decidió qué superficie
    # corresponde a cada subcuenca y borrar un islote abriría un hueco.
    if len(parts) == 1:
        record = polygon_record(parts[0], nd)
        record["area_km2"] = round(area_km2(parts[0]), 1)
        record["polygons"] = [{"ring": record["ring"], "holes": record["holes"]}]
    else:
        merged = MultiPolygon(parts)
        first = polygon_record(parts[0], nd)
        record = {
            "ring": first["ring"],
            "holes": first["holes"],
            "polygons": [polygon_record(p, nd) for p in parts],
            "area_km2": round(area_km2(merged), 1),
        }
    return record


def geometry_record(geom, tolerance: float, label: str, nd: int = 5) -> dict:
    """Simplifica y serializa un Polygon o MultiPolygon sin perder partes."""
    return geometry_record_from_geometry(simplify_geom(geom, tolerance), label, nd)


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
    remainder_parts = [
        p
        for p in remainder_parts
        if p.area * 111_320 * 110_540 >= MIN_COMPONENT_AREA_M2
    ]
    if not remainder_parts:
        raise SystemExit("la diferencia de la cuenca con las subcuencas solo dejó fragmentos mínimos")
    remainder_geom = remainder_parts[0] if len(remainder_parts) == 1 else MultiPolygon(remainder_parts)
    print(
        f"  Bajo Piura: {len(remainder_parts)} componente(s) · "
        f"{area_km2(remainder_geom):.1f} km² geodésicos"
    )

    # Bajo Piura va primero para conservar el orden que consume la web.
    named_full: list[tuple[str, object]] = [("Bajo Piura", remainder_geom)]
    named_full.extend((name, geom) for name, geom, _ in sub_geoms)

    print("reconciliando la partición de subcuencas…")
    basin_simplified = simplify_geom(basin_geom, args.tolerance)
    named_simplified = [
        (name, simplify_geom(geom, args.tolerance)) for name, geom in named_full
    ]
    try:
        reconciliation = reconcile_partition(basin_simplified, named_simplified)
    except ValueError as exc:
        raise SystemExit(f"no se pudo reconciliar la partición: {exc}") from exc

    reconciled = dict(reconciliation.geoms)
    # La cuenca y las subcuencas comparten la rejilla de 1e-6° que fija la
    # reconciliación; serializar ambas a 6 decimales evita slivers de redondeo.
    basin_record = geometry_record_from_geometry(reconciliation.basin, "cuenca", nd=6)

    subbasins = []
    for name, _, source_area in sub_geoms:
        record = geometry_record_from_geometry(reconciled[name], name, nd=6)
        record.update(
            {
                "name": name,
                "area_fuente_km2": round(source_area, 1) if source_area is not None else None,
                "origen": "ANA",
            }
        )
        subbasins.append(record)

    bajo = geometry_record_from_geometry(reconciled["Bajo Piura"], "Bajo Piura", nd=6)
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
        "reconciliacion": {
            "crs_metrico": "EPSG:32717",
            "tolerancia_simplificacion_deg": args.tolerance,
            "caras": reconciliation.face_count,
            "caras_de_hueco": reconciliation.gap_face_count,
            "slivers_asignados_km2": round(reconciliation.gap_before_km2, 4),
            "solapamientos_eliminados_km2": round(reconciliation.overlap_before_km2, 4),
            "superficie_fuera_eliminada_km2": round(reconciliation.outside_before_km2, 4),
            "cambios_area_km2": reconciliation.area_changes_km2,
            "metodo": (
                "Se simplifican la cuenca y las nueve subcuencas por separado; se "
                "polygoniza el grafo de límites y cada cara se asigna a la subcuenca "
                "con mayor solapamiento. Los huecos sin solapamiento se asignan a la "
                "subcuenca más cercana. No se crea superficie nueva; el área total se "
                "conserva. Si una subcuenca tuviera agujeros interiores, el proceso se "
                "detiene para revisión manual."
            ),
        },
        "metodo": (
            "Descarga GeoJSON del geoservidor ANA/MINAM. Cuenca y subcuencas simplificadas "
            "una sola vez con tolerancia de 0.0006° y preserve_topology=True; después se "
            "reconcilia la partición para eliminar solapamientos y huecos de simplificación. "
            "«Bajo Piura» se calcula como la diferencia entre la cuenca completa y las ocho "
            "subcuencas publicadas, antes de simplificar. Las áreas publicadas son geodésicas "
            "(WGS84). Shape_Area de ANA se conserva como area_fuente_km2 y está calculado en "
            "EPSG:32718 (UTM 18S)."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"  {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}")
    print(f"  cuenca: {output['area_km2']:.1f} km² · {len(output['ring'])} puntos")
    print(
        f"  reconciliación: {reconciliation.face_count} caras · "
        f"{reconciliation.gap_face_count} de hueco · "
        f"{reconciliation.overlap_before_km2:.4f} km² de solapamiento eliminado"
    )
    for sub in output["subbasins"]:
        print(f"  {sub['name']:26s} {sub['area_km2']:7.1f} km² · {len(sub['ring'])} puntos")


if __name__ == "__main__":
    main()
