#!/usr/bin/env python3
"""Descarga los límites de la cuenca Piura desde el geoservidor de ANA/MINAM.

Fuente: Unidad Hidrográfica y Sub Cuenca Hidrográfica (ANA, R.M. 033-2008-AG).
Salida: data/raw/limits.json con el mismo formato que consume build_layers.py.

La capa oficial no trae «Bajo Piura» como subcuenca; se calcula como el resto de
la cuenca después de restar las ocho subcuencas publicadas. Esa decisión queda
declarada en el propio archivo (`metodo`).

Correcciones de integridad (v0.5):
- La validez de la cuenca y de las ocho subcuencas se comprueba antes de
  cualquier reparación. Si ANA entrega una geometría inválida, se repara solo con
  registro explícito en `reconciliacion.reparaciones`; no se oculta el error.
- «Bajo Piura» se calcula sobre las geometrías completas y se simplifica una sola
  vez, después de la diferencia.
- La cuenca y las nueve subcuencas se simplifican por separado y luego se
  reconcilian como una partición topológica: cada cara del grafo de límites se
  asigna a la subcuenca con mayor solapamiento y los huecos sin solapamiento a
  la más cercana. Así desaparecen los solapamientos y huecos de la simplificación
  independiente, sin inventar superficie.
- Se conservan agujeros y componentes MultiPolygon. Si una subcuenca trae un
  agujero interior, la reconciliación se detiene: no se rellena en silencio.
- El área publicada se calcula de la geometría (geodésica). `Shape_Area` de ANA
  se conserva aparte porque está calculado en EPSG:32718 (UTM 18S), fuera de la
  zona 17S que corresponde a esta cuenca.
- Se publica un bloque `reconciliacion.fidelidad` con IoU, diferencia simétrica,
  Hausdorff y distancia media/p95 entre límites, además de la superficie asignada
  por solapamiento y por proximidad.

Uso:
    python3 etl/download_ana.py
    python3 etl/download_ana.py --out data/raw/limits.json --force
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.ops import unary_union
from shapely.validation import explain_validity

try:  # Ejecución como módulo (`python -m etl.download_ana`)
    from etl.topology import (
        Tolerances,
        as_polygonal,
        fidelity_metrics,
        geodesic_area_km2,
        inspect_geometry,
        metric_area_km2,
        polygonal_parts,
        reconcile_partition,
        repair_to_polygonal,
    )
except ModuleNotFoundError:  # Ejecución directa (`python etl/download_ana.py`)
    from topology import (
        Tolerances,
        as_polygonal,
        fidelity_metrics,
        geodesic_area_km2,
        inspect_geometry,
        metric_area_km2,
        polygonal_parts,
        reconcile_partition,
        repair_to_polygonal,
    )

ROOT = Path(__file__).resolve().parents[1]
SERVICE = (
    "https://geoservidorperu.minam.gob.pe/arcgis/rest/services/"
    "ZEE_VISOR/09_CARACTERIZACI%C3%93N_DEL_TERRITORIO_PIURA/MapServer"
)
BASIN_LAYER = 18
SUBBASIN_LAYER = 19
DEFAULT_CODE = "1378"
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
    return geodesic_area_km2(geom)


def simplify_geom(geom, tolerance: float, label: str = "geometría"):
    """Simplifica una sola vez, conservando topología y agujeros.

    La geometría de entrada debe ser válida. La salida también se comprueba:
    una simplificación que produzca una geometría inválida se detiene.
    """
    audit = inspect_geometry(geom, label)
    if audit.empty:
        raise SystemExit(f"{label}: la geometría está vacía")
    if not audit.valid:
        raise SystemExit(f"{label}: la geometría no es válida: {audit.reason}")
    simplified = geom.simplify(tolerance, preserve_topology=True)
    result_audit = inspect_geometry(simplified, label)
    if result_audit.empty or not result_audit.valid:
        raise SystemExit(
            f"{label}: la simplificación produjo una geometría inválida: "
            f"{result_audit.reason or 'vacía'}"
        )
    if simplified.geom_type not in {"Polygon", "MultiPolygon"}:
        raise SystemExit(
            f"{label}: la simplificación produjo {simplified.geom_type}; "
            "se esperaba Polygon/MultiPolygon"
        )
    return simplified


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


def _record_geometry(record: dict):
    """Reconstruye la geometría serializada para comprobar que sigue siendo válida."""
    parts = [
        Polygon(p["ring"], p.get("holes") or [])
        for p in record.get("polygons") or [{"ring": record["ring"], "holes": record.get("holes") or []}]
    ]
    if not parts:
        return None
    return parts[0] if len(parts) == 1 else MultiPolygon(parts)


def geometry_record_from_geometry(geom, label: str, nd: int = 5) -> dict:
    """Serializa un Polygon/MultiPolygon ya simplificado, sin perder partes.

    No repara: si la geometría es inválida o no es poligonal, falla. Así una
    reparación no puede pasar inadvertida al serializar.

    El redondeo puede convertir dos vértices muy próximos en el mismo punto y
    crear una autointersección. Por eso se reconstruye el registro y, si no es
    válido, se añaden decimales hasta que lo sea (máximo 12). El número de
    decimales usado queda en ``precision_decimales``.
    """
    audit = inspect_geometry(geom, label)
    if audit.empty:
        raise SystemExit(f"{label}: la geometría está vacía")
    if not audit.valid:
        raise SystemExit(f"{label}: la geometría no es válida: {audit.reason}")
    original_parts = polygonal_parts(geom)
    if not original_parts:
        raise SystemExit(f"{label}: la geometría no contiene polígonos")

    # No se descartan componentes: si dos islas se tocan en un punto, un
    # MultiPolygon reconstruido puede resultar inválido. Se fusionan con
    # unary_union; la superficie es la misma y la representación queda válida.
    joined = unary_union(original_parts)
    joined_poly = as_polygonal(joined)
    if joined_poly is None:
        raise SystemExit(f"{label}: la unión de componentes no es poligonal")
    parts = polygonal_parts(joined_poly)

    def build_record(parts_for_record, precision: int) -> dict:
        if len(parts_for_record) == 1:
            record = polygon_record(parts_for_record[0], precision)
            record["area_km2"] = round(area_km2(parts_for_record[0]), 1)
            record["polygons"] = [{"ring": record["ring"], "holes": record["holes"]}]
            return record
        merged = MultiPolygon(parts_for_record)
        first = polygon_record(parts_for_record[0], precision)
        return {
            "ring": first["ring"],
            "holes": first["holes"],
            "polygons": [polygon_record(p, precision) for p in parts_for_record],
            "area_km2": round(area_km2(merged), 1),
        }

    last_reason = None
    for precision in range(nd, 13):
        record = build_record(parts, precision)
        fused = False
        if len(parts) > 1:
            serialized = [
                Polygon(p["ring"], p.get("holes") or [])
                for p in record["polygons"]
            ]
            serialized_union = as_polygonal(unary_union(serialized))
            if serialized_union is not None:
                serialized_parts = polygonal_parts(serialized_union)
                if len(serialized_parts) != len(parts):
                    record = build_record(serialized_parts, precision)
                    fused = True
        check = _record_geometry(record)
        if check is not None and check.is_valid and not check.is_empty:
            if precision != nd:
                print(
                    f"  aviso: {label}: se usaron {precision} decimales para "
                    "evitar una autointersección por redondeo"
                )
            record["precision_decimales"] = precision
            record["componentes_originales"] = len(original_parts)
            record["componentes_serializados"] = len(record["polygons"])
            record["fusionado"] = fused or len(original_parts) != len(record["polygons"])
            return record
        last_reason = explain_validity(check) if check is not None else "geometría vacía"
    raise SystemExit(
        f"{label}: el registro serializado no es válido incluso con 12 decimales: "
        f"{last_reason}"
    )


def geometry_record(geom, tolerance: float, label: str, nd: int = 5) -> dict:
    """Simplifica y serializa un Polygon o MultiPolygon sin perder partes."""
    return geometry_record_from_geometry(simplify_geom(geom, tolerance, label), label, nd)


def prepare_source(geom, label: str, repairs: list) -> object:
    """Valida una geometría de ANA y la repara solo si hace falta, con registro."""
    fixed, audit = repair_to_polygonal(geom, label, allow_repair=True)
    if fixed is None:
        raise SystemExit(f"{label}: no se pudo normalizar: {audit.note or 'sin detalle'}")
    if audit.repaired:
        repairs.append(audit)
        print(f"  aviso: {label}: {audit.note}")
    return fixed


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
    source_repairs: list = []
    basin_geom = prepare_source(shape(basin_feature["geometry"]), "cuenca ANA", source_repairs)
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
        name = props["SUB_CUENCA"].strip()
        geom = prepare_source(shape(feature["geometry"]), name, source_repairs)
        source_area = props.get("Shape_Area")
        sub_geoms.append(
            (
                name,
                geom,
                float(source_area) / 1e6 if source_area is not None else None,
            )
        )

    # Resta sobre las geometrías completas, antes de simplificar. Así el resto
    # no hereda los cortes internos de ocho simplificaciones independientes.
    union = unary_union([geom for _, geom, _ in sub_geoms])
    remainder = basin_geom.difference(union)
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
    basin_simplified = simplify_geom(basin_geom, args.tolerance, "cuenca")
    named_simplified = [
        (name, simplify_geom(geom, args.tolerance, name)) for name, geom in named_full
    ]
    try:
        reconciliation = reconcile_partition(
            basin_simplified,
            named_simplified,
            allow_repair=False,
        )
    except ValueError as exc:
        raise SystemExit(f"no se pudo reconciliar la partición: {exc}") from exc

    reconciled = dict(reconciliation.geoms)
    # La cuenca y las subcuencas comparten la rejilla de 1e-6° que fija la
    # reconciliación; serializar ambas a 6 decimales evita slivers de redondeo.
    basin_record = geometry_record_from_geometry(reconciliation.basin, "cuenca", nd=6)

    fidelity: dict[str, dict] = {}
    for name, full_geom in named_full:
        simplified_geom = dict(named_simplified)[name]
        reconciled_geom = reconciled[name]
        fidelity[name] = {
            "area_fuente_utm_km2": round(metric_area_km2(full_geom), 4),
            "area_simplificada_utm_km2": round(metric_area_km2(simplified_geom), 4),
            "area_reconciliada_utm_km2": round(metric_area_km2(reconciled_geom), 4),
            "fuente_a_simplificada": fidelity_metrics(full_geom, simplified_geom).as_dict(),
            "simplificada_a_reconciliada": reconciliation.fidelity[name].as_dict(),
            "fuente_a_reconciliada": fidelity_metrics(full_geom, reconciled_geom).as_dict(),
        }

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

    tolerances = Tolerances()
    output = {
        "source": "ANA — Unidades Hidrográficas Pfafstetter 1:100 000 (R.M. 033-2008-AG)",
        "code": args.code,
        "area_km2": basin_record["area_km2"],
        "area_fuente_km2": round(basin_source_area, 1) if basin_source_area is not None else None,
        "area_fuente_crs": "EPSG:32718 (UTM 18S), calculado por ANA; el polígono está en la zona 17S",
        "ring": basin_record["ring"],
        "holes": basin_record["holes"],
        "polygons": basin_record["polygons"],
        "precision_decimales": basin_record.get("precision_decimales"),
        "componentes_originales": basin_record.get("componentes_originales"),
        "componentes_serializados": basin_record.get("componentes_serializados"),
        "fusionado": basin_record.get("fusionado"),
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
            "cambios_area_pct": reconciliation.area_changes_pct,
            "area_antes_km2": reconciliation.area_before_km2,
            "area_despues_km2": reconciliation.area_after_km2,
            "reasignacion": {
                "superficie_asignada_por_solapamiento_km2": round(
                    reconciliation.overlap_assigned_km2, 4
                ),
                "superficie_asignada_por_proximidad_km2": round(
                    reconciliation.proximity_area_km2, 4
                ),
                "caras_por_proximidad": reconciliation.proximity_faces,
                "distancia_maxima_proximidad_m": round(
                    reconciliation.proximity_max_distance_m, 1
                ),
                "distancia_media_proximidad_m": round(
                    reconciliation.proximity_mean_distance_m, 1
                ),
                "superficie_solapada_original_km2": round(
                    reconciliation.overlap_before_km2, 4
                ),
                "superficie_fuera_original_km2": round(
                    reconciliation.outside_before_km2, 4
                ),
            },
            "fidelidad": fidelity,
            "reparaciones": [audit.as_dict() for audit in source_repairs],
            "umbrales": {
                "error_km2": tolerances.error_km2,
                "aviso_km2": tolerances.warn_km2,
                "p95_limite_aviso_m": round(tolerances.boundary_warn_m, 1),
                "nota": (
                    "Los umbrales de área son 1 mm² y 0,1 mm² a escala 1:100 000. "
                    "El aviso de p95 es 3 × la tolerancia de simplificación "
                    "(0,0006° ≈ 66 m), no un estándar externo."
                ),
            },
            "metodo": (
                "Se simplifican la cuenca y las nueve subcuencas por separado; se "
                "polygoniza el grafo de límites y cada cara se asigna a la subcuenca "
                "con mayor solapamiento. Los huecos sin solapamiento se asignan a la "
                "subcuenca más cercana. No se crea superficie nueva; el área total se "
                "conserva. La fidelidad se mide en EPSG:32717: IoU y diferencia "
                "simétrica por área; Hausdorff exacto entre límites; distancia media y "
                "p95 muestreadas cada 50 m. Hausdorff es sensible a un vértice aislado "
                "y se publica como diagnóstico, no como único criterio."
            ),
        },
        "metodo": (
            "Descarga GeoJSON del geoservidor ANA/MINAM. La validez de la cuenca y de "
            "las subcuencas se comprueba antes de reparar; cualquier reparación queda "
            "en reconciliacion.reparaciones. La cuenca y las subcuencas se simplifican "
            "una sola vez con tolerancia de 0.0006° y preserve_topology=True; después "
            "se reconcilia la partición para eliminar solapamientos y huecos de "
            "simplificación. «Bajo Piura» se calcula como la diferencia entre la cuenca "
            "completa y las ocho subcuencas publicadas, antes de simplificar. Las áreas "
            "publicadas son geodésicas (WGS84). Shape_Area de ANA se conserva como "
            "area_fuente_km2 y está calculado en EPSG:32718 (UTM 18S)."
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
    for name, metrics in fidelity.items():
        full_rec = metrics["fuente_a_reconciliada"]
        print(
            f"  {name:26s} Δtotal {full_rec['delta_area_km2']:+8.4f} km² · "
            f"IoU {full_rec['iou']:.6f} · p95 {full_rec['distancia_p95_limite_m']:.1f} m"
        )


if __name__ == "__main__":
    main()
