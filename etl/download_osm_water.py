#!/usr/bin/env python3
"""Descarga los cuerpos de agua de OpenStreetMap y construye data/raw/water.json.

Consulta Overpass por `natural=water` y `water=reservoir` dentro de la ventana del
atlas. Conserva los cuerpos marcados como manuales en el archivo existente (por
ejemplo, la represa de Poechos), porque no provienen de OSM.

La API pública de Overpass puede estar saturada; el script prueba varios
endpoints, divide la ventana en teselas y falla con un mensaje claro si ninguno
responde. Ajusta `--tile` si necesitas consultas más pequeñas.

Uso:
    python3 etl/download_osm_water.py
    python3 etl/download_osm_water.py --out data/raw/water.json --force
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BBOX = (-81.45, -6.25, -79.30, -4.55)
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
USER_AGENT = "rio-piura-atlas/0.1 (atlas documentado; uso manual)"


def tile_bbox(bbox, size: float):
    west, south, east, north = bbox
    x = west
    while x < east - 1e-9:
        y = south
        nx = min(x + size, east)
        while y < north - 1e-9:
            ny = min(y + size, north)
            yield (x, y, nx, ny)
            y = ny
        x = nx


def overpass_query(bbox, timeout: int, endpoints: list[str]) -> dict:
    west, south, east, north = bbox
    query = f"""
[out:json][timeout:180];
(
  way["natural"="water"]({south},{west},{north},{east});
  relation["natural"="water"]({south},{west},{north},{east});
  way["water"="reservoir"]({south},{west},{north},{east});
);
out tags geom;
"""
    last_error = None
    for endpoint in endpoints:
        try:
            print(f"  consultando {endpoint}…")
            response = requests.post(
                endpoint,
                data={"data": query},
                headers={"User-Agent": USER_AGENT},
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("elements") is not None:
                return data
            last_error = RuntimeError(f"respuesta sin elementos: {data}")
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            last_error = exc
        time.sleep(1)
    raise SystemExit(f"Overpass no respondió: {last_error}")


def ring_area_km2(ring, holes=()) -> float:
    if len(ring) < 4:
        return 0.0

    def signed_area(points) -> float:
        lat0 = sum(p[1] for p in points) / len(points)
        kx = 111.32 * math.cos(math.radians(lat0))
        ky = 110.54
        area = 0.0
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            area += (x1 * kx) * (y2 * ky) - (x2 * kx) * (y1 * ky)
        return abs(area) / 2.0

    return max(0.0, signed_area(ring) - sum(signed_area(hole) for hole in holes if len(hole) >= 4))


def point_in_ring(x, y, ring) -> bool:
    inside = False
    for i in range(len(ring)):
        x1, y1 = ring[i - 1]
        x2, y2 = ring[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


def way_ring(element):
    geometry = element.get("geometry") or []
    ring = [[round(p["lon"], 6), round(p["lat"], 6)] for p in geometry if "lon" in p and "lat" in p]
    if len(ring) < 4 or ring[0] != ring[-1]:
        return None
    return ring


def assemble_rings(lines):
    """Une segmentos exteriores de una relación hasta cerrar anillos."""
    lines = [line[:] for line in lines if len(line) >= 2]
    rings = []
    while lines:
        ring = lines.pop(0)[:]
        changed = True
        while changed and ring[0] != ring[-1]:
            changed = False
            for i, line in enumerate(lines):
                if line[0] == ring[-1]:
                    ring.extend(line[1:])
                elif line[-1] == ring[-1]:
                    ring.extend(reversed(line[:-1]))
                elif line[-1] == ring[0]:
                    ring = line[:-1] + ring
                elif line[0] == ring[0]:
                    ring = list(reversed(line[1:])) + ring
                else:
                    continue
                lines.pop(i)
                changed = True
                break
        if ring[0] != ring[-1] or len(ring) < 4:
            return []
        rings.append(ring)
    return rings


def relation_rings(element):
    """Devuelve anillos exteriores con sus huecos interiores.

    Antes se descartaban los miembros `inner` de las relaciones OSM. Ahora se
    ensamblan y se asignan al exterior que los contiene.
    """
    members = element.get("members") or []
    outer_lines: list[list[list[float]]] = []
    inner_lines: list[list[list[float]]] = []
    for member in members:
        role = member.get("role")
        if role not in {"outer", "inner", ""}:
            continue
        geometry = member.get("geometry") or []
        line = [[round(p["lon"], 6), round(p["lat"], 6)] for p in geometry if "lon" in p and "lat" in p]
        if len(line) < 2:
            return []
        (inner_lines if role == "inner" else outer_lines).append(line)
    outers = assemble_rings(outer_lines)
    inners = assemble_rings(inner_lines)
    result = []
    for outer in outers:
        holes = [hole for hole in inners if hole and point_in_ring(hole[0][0], hole[0][1], outer)]
        result.append({"ring": outer, "holes": holes})
    return result


def is_intermittent(tags) -> bool:
    value = (tags.get("intermittent") or tags.get("seasonal") or "").lower()
    return value in {"yes", "true", "1"}


def parse_bodies(data, min_area_km2, max_area_km2):
    bodies = []
    for element in data.get("elements", []):
        tags = element.get("tags") or {}
        if (tags.get("water") or "").lower() in {"river", "stream", "canal", "ditch", "drain"}:
            continue
        rings = way_ring(element) if element.get("type") == "way" else None
        if rings is None:
            rings = relation_rings(element)
        else:
            rings = [{"ring": rings, "holes": []}]
        for item in rings:
            ring = item["ring"]
            holes = item.get("holes") or []
            area = round(ring_area_km2(ring, holes), 1)
            if area < min_area_km2 or area > max_area_km2:
                continue
            bodies.append(
                {
                    "name": tags.get("name") or tags.get("name:es") or "",
                    "intermittent": is_intermittent(tags),
                    "area_km2": area,
                    "ring": ring,
                    "holes": holes,
                }
            )
    bodies.sort(key=lambda b: (-b["area_km2"], b["name"]))
    return bodies


def load_manual(out: Path):
    if not out.exists():
        return []
    try:
        data = json.loads(out.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [b for b in data.get("bodies", []) if b.get("manual")]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "raw" / "water.json")
    parser.add_argument("--force", action="store_true", help="sobrescribir la salida si ya existe")
    parser.add_argument("--min-area-km2", type=float, default=5.0)
    parser.add_argument(
        "--tile",
        type=float,
        default=0.6,
        help="tamaño de tesela en grados para no saturar Overpass; 0 = una sola consulta",
    )
    parser.add_argument("--timeout", type=int, default=60, help="segundos por consulta y endpoint")
    parser.add_argument(
        "--endpoint",
        action="append",
        default=[],
        help="endpoint Overpass adicional (se prueba primero; se puede repetir)",
    )
    parser.add_argument(
        "--max-area-km2",
        type=float,
        default=500.0,
        help="descarta polígonos enormes que no son lagunas (por ejemplo, salares mal etiquetados)",
    )
    parser.add_argument("--bbox", type=float, nargs=4, default=BBOX, metavar=("W", "S", "E", "N"))
    args = parser.parse_args()

    if args.out.exists() and not args.force:
        raise SystemExit(f"{args.out} ya existe. Usa --force para reemplazarlo.")

    print("descargando cuerpos de agua de OpenStreetMap…")
    tiles = list(tile_bbox(args.bbox, args.tile)) if args.tile > 0 else [args.bbox]
    endpoints = args.endpoint + [e for e in ENDPOINTS if e not in args.endpoint]
    elements = {}
    for i, tile in enumerate(tiles, start=1):
        print(f"  tesela {i}/{len(tiles)}: {tile}")
        data = overpass_query(tile, args.timeout, endpoints)
        for element in data.get("elements", []):
            elements[(element.get("type"), element.get("id"))] = element
        if i < len(tiles):
            time.sleep(1)

    bodies = parse_bodies({"elements": list(elements.values())}, args.min_area_km2, args.max_area_km2)
    manual = load_manual(args.out)
    output = {"bodies": bodies + manual}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"  {args.out}: {len(bodies)} cuerpos OSM + {len(manual)} manuales")
    for body in output["bodies"]:
        print(f"  {body['name'] or '(sin nombre)':28s} {body['area_km2'] or 0:7.1f} km²")


if __name__ == "__main__":
    main()
