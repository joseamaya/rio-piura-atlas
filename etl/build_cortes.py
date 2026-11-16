#!/usr/bin/env python3
"""Genera cortes transversales de referencia y la malla de elevación del atlas.

Entrada:  DEM del laboratorio de modelos y data/raw/{network,limits}.json
Salida:   data/processed/cortes.geojson
          data/processed/cortes_perfiles.json
          data/processed/dem_grid.bin + dem_grid.meta.json
          y una copia de cada archivo en web/public/data/

Los cortes de referencia son transectos perpendiculares a la red hídrica en
puntos conocidos del valle. Se recortan a la cuenca oficial. La malla de
elevación permite que el visitante dibuje su propio corte en el mapa sin
descargar el DEM completo.

Uso:
    python3 etl/build_cortes.py
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
WEB = ROOT / "web" / "public" / "data"
DEM_PATH = Path(os.environ.get("PIURA_DEM", ROOT.parent / "blender/projects/piura/data/dem.npz"))

GRID_W = 512
MAX_MUESTRAS = 801

# id, nombre visible, longitud, latitud, largo total del transecto en km.
# El punto es un ancla; el transecto se centra en el punto más cercano de la red,
# no en el ancla, para que cruce el río.
ANCLAS = [
    ("bajo-piura", "Bajo Piura · La Unión", -80.74391, -5.40437, 24),
    ("piura", "Piura ciudad", -80.62666, -5.19711, 24),
    ("catacaos", "Catacaos", -80.67608, -5.26548, 22),
    ("chulucanas", "Chulucanas", -80.16092, -5.09651, 24),
    ("tambogrande", "Tambogrande", -80.34240, -4.93535, 24),
]


def point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i - 1]
        x2, y2 = ring[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


def _nearest_point_on_segment(lon, lat, p1, p2):
    """Punto más cercano de un segmento, en una proyección local en metros."""
    kx = 111_320.0 * math.cos(math.radians(lat))
    ky = 110_540.0

    def xy(point):
        return ((point[0] - lon) * kx, (point[1] - lat) * ky)

    ax, ay = xy(p1)
    bx, by = xy(p2)
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    t = 0.0 if denom == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / denom))
    px, py = ax + t * dx, ay + t * dy
    return math.hypot(px, py), (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)


def nearest_segment(rivers, lon, lat, min_upland=500.0):
    """Devuelve (extremo A, extremo B, punto más cercano) del río elegido.

    Se mide la distancia exacta al segmento, no a su punto medio. El transecto
    se centra luego en el punto más cercano para garantizar que cruce el río.
    """
    best = None
    for river in rivers:
        if river["upland"] < min_upland:
            continue
        for i in range(len(river["coords"]) - 1):
            p1, p2 = river["coords"][i], river["coords"][i + 1]
            distance, nearest = _nearest_point_on_segment(lon, lat, p1, p2)
            if best is None or distance < best[0]:
                best = (distance, p1, p2, nearest)
    if best is None:
        return None
    return best[1], best[2], best[3]


def perpendicular(p1, p2, lat):
    """Vector unitario perpendicular al segmento, en metros, ajustado a la latitud."""
    x1, y1 = p1
    x2, y2 = p2
    dx = (x2 - x1) * 111_320 * math.cos(math.radians(lat))
    dy = (y2 - y1) * 110_540
    norm = math.hypot(dx, dy)
    if norm < 1e-9:
        return 0.0, 1.0
    return -dy / norm, dx / norm


def transect(lon, lat, perp, length_km):
    half = length_km * 500.0
    dxl = perp[0] * half / (111_320 * math.cos(math.radians(lat)))
    dyl = perp[1] * half / 110_540
    return (lon - dxl, lat - dyl), (lon + dxl, lat + dyl)


def interpolate(lon, lat, a, b, t):
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def sample_dem(elev, lon0, lon1, lat0, lat1, lon, lat):
    """Muestreo bilineal. La fila 0 del DEM corresponde al norte (lat0)."""
    h, w = elev.shape
    col = (lon - lon0) / (lon1 - lon0) * (w - 1)
    row = (lat0 - lat) / (lat0 - lat1) * (h - 1)
    if col < 0 or row < 0 or col > w - 1 or row > h - 1:
        return float("nan")
    c0, r0 = int(math.floor(col)), int(math.floor(row))
    c1, r1 = min(c0 + 1, w - 1), min(r0 + 1, h - 1)
    fc, fr = col - c0, row - r0
    top = elev[r0, c0] * (1 - fc) + elev[r0, c1] * fc
    bottom = elev[r1, c0] * (1 - fc) + elev[r1, c1] * fc
    return float(top * (1 - fr) + bottom * fr)


def distance_km(a, b):
    dx = (b[0] - a[0]) * 111_320 * math.cos(math.radians((a[1] + b[1]) / 2))
    dy = (b[1] - a[1]) * 110_540
    return math.hypot(dx, dy) / 1000.0


def _line_parts(geom):
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "LineString":
        return [geom]
    if geom.geom_type in {"MultiLineString", "GeometryCollection"}:
        parts = []
        for child in geom.geoms:
            parts.extend(_line_parts(child))
        return parts
    return []


def clip_to_basin(a, b, basin):
    """Recorta el transecto al tramo continuo más largo dentro de la cuenca."""
    line = LineString([a, b])
    parts = _line_parts(line.intersection(make_valid(basin)))
    if not parts:
        return None
    longest = max(parts, key=lambda part: part.length)
    coords = list(longest.coords)
    return (coords[0][0], coords[0][1]), (coords[-1][0], coords[-1][1])


def clip_to_ring(a, b, ring, steps=400):
    """Compatibilidad: recorta contra un anillo usando intersección exacta."""
    return clip_to_basin(a, b, Polygon(ring))


def profile(a, b, elev, lon0, lon1, lat0, lat1, samples=None):
    dist_km, elev_m = [], []
    total = distance_km(a, b)
    n = samples or MAX_MUESTRAS
    n = max(2, min(MAX_MUESTRAS, int(n)))
    for i in range(n):
        t = i / (n - 1)
        lon, lat = interpolate(a[0], a[1], a, b, t)
        value = sample_dem(elev, lon0, lon1, lat0, lat1, lon, lat)
        dist_km.append(round(total * t, 2))
        elev_m.append(None if math.isnan(value) else round(value, 1))
    return dist_km, elev_m


def effective_resolution_m(elev, lon0, lon1, lat0, lat1) -> tuple[float, float]:
    """Resolución real de la malla de trabajo del DEM, en metros."""
    h, w = elev.shape
    lat_mid = (lat0 + lat1) / 2
    dx = abs(lon1 - lon0) * 111_320.0 * math.cos(math.radians(lat_mid)) / max(w - 1, 1)
    dy = abs(lat1 - lat0) * 110_540.0 / max(h - 1, 1)
    return dx, dy


def write_json(name, obj):
    for base in (OUT, WEB):
        base.mkdir(parents=True, exist_ok=True)
        path = base / name
        path.write_text(
            json.dumps(obj, separators=(",", ":"), ensure_ascii=False, allow_nan=False),
            encoding="utf-8",
        )
    size = (OUT / name).stat().st_size / 1e3
    print(f"  {name:28s} {size:7.0f} kB")


def build_cortes(dem, limits, network):
    elev = dem["elev"]
    lon0, lon1 = float(dem["lon"][0]), float(dem["lon"][1])
    lat0, lat1 = float(dem["lat"][0]), float(dem["lat"][1])
    dx_m, dy_m = effective_resolution_m(elev, lon0, lon1, lat0, lat1)
    effective_m = max(dx_m, dy_m)

    polygons = limits.get("polygons")
    if polygons:
        parts = [Polygon(p["ring"], p.get("holes") or []) for p in polygons]
        basin = parts[0] if len(parts) == 1 else unary_union(parts)
    else:
        basin = Polygon(limits["ring"], limits.get("holes") or [])
    basin = make_valid(basin)

    features, perfiles = [], {}
    for ident, nombre, lon, lat, length in ANCLAS:
        segment = nearest_segment(network["rivers"], lon, lat)
        if segment is None:
            print(f"  (sin río cerca de {nombre}; se omite el corte)")
            continue
        p1, p2, nearest = segment
        perp = perpendicular(p1, p2, lat)
        raw_a, raw_b = transect(nearest[0], nearest[1], perp, length)
        clipped = clip_to_basin(raw_a, raw_b, basin)
        if clipped is None:
            print(f"  (el transecto de {nombre} no cruza la cuenca; se omite)")
            continue
        a, b = clipped
        total_m = distance_km(a, b) * 1000
        samples = max(2, min(MAX_MUESTRAS, int(math.ceil(total_m / effective_m)) + 1))
        dist, values = profile(a, b, elev, lon0, lon1, lat0, lat1, samples=samples)
        clean = [v for v in values if v is not None]
        if len(clean) < 2:
            print(f"  (sin datos de DEM para {nombre}; se omite)")
            continue
        # El transecto debe cruzar la red elegida; si no, el perfil no es un corte
        # transversal del río y se omite en vez de publicar una línea engañosa.
        if not LineString([a, b]).intersects(LineString([p1, p2])):
            print(f"  (el transecto de {nombre} no cruza el río; se omite)")
            continue

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[round(a[0], 5), round(a[1], 5)], [round(b[0], 5), round(b[1], 5)]],
                },
                "properties": {
                    "id": ident,
                    "nombre": nombre,
                    "longitud_km": round(distance_km(a, b), 2),
                    "elev_min_m": round(min(clean)),
                    "elev_max_m": round(max(clean)),
                    "fuente": "copernicus-dem-30",
                    "metodo": "transecto perpendicular al río, centrado en el punto más cercano y recortado a la cuenca; perfil del DEM",
                    "resolucion_fuente_m": 30,
                    "resolucion_efectiva_m": round(effective_m),
                    "muestras": len(dist),
                },
            }
        )
        perfiles[ident] = {
            "nombre": nombre,
            "longitud_km": round(distance_km(a, b), 2),
            "elev_min_m": round(min(clean)),
            "elev_max_m": round(max(clean)),
            "paso_perfil_m": round(distance_km(a, b) * 1000 / (len(dist) - 1), 1),
            "resolucion_efectiva_m": round(effective_m),
            "dist_km": dist,
            "elev_m": values,
        }

    write_json("cortes.geojson", {"type": "FeatureCollection", "features": features})
    write_json(
        "cortes_perfiles.json",
        {
            "resolucion_fuente_m": 30,
            "resolucion_efectiva_m": round(effective_m),
            "resolucion_malla_m": round(111_320 * abs(lon1 - lon0) / GRID_W),
            "resolucion_malla_lat_m": round(110_540 * abs(lat1 - lat0) / int(round(GRID_W * elev.shape[0] / elev.shape[1]))),
            "nota": (
                "Perfiles de referencia calculados del DEM de trabajo (~140 m), derivado "
                "de Copernicus GLO-30. El paso de muestra se ajusta a la resolución efectiva; "
                "no se remuestrea a 30 m porque el DEM no tiene ese detalle. La malla del "
                "visor para cortes dibujados tiene otra resolución. No sirve para dimensionar obras."
            ),
            "perfiles": perfiles,
        },
    )


def build_grid(dem):
    """Malla compacta para cortes dibujados por el visitante (se carga a demanda)."""
    elev = dem["elev"]
    lon0, lon1 = float(dem["lon"][0]), float(dem["lon"][1])
    lat0, lat1 = float(dem["lat"][0]), float(dem["lat"][1])
    h, w = elev.shape
    grid_h = int(round(GRID_W * h / w))
    small = np.asarray(Image.fromarray(elev).resize((GRID_W, grid_h), Image.BILINEAR), dtype=np.float32)
    values = np.clip(np.rint(small), 0, 32767).astype("<i2")

    for base in (OUT, WEB):
        base.mkdir(parents=True, exist_ok=True)
        values.tofile(base / "dem_grid.bin")
    dx_m, dy_m = effective_resolution_m(elev, lon0, lon1, lat0, lat1)
    meta = {
        "bbox": [lon0, min(lat0, lat1), lon1, max(lat0, lat1)],
        "width": GRID_W,
        "height": grid_h,
        "dtype": "int16",
        "byte_order": "little",
        "row_order": "north-to-south",
        "resolution_m_aprox": round(max(111_320 * abs(lon1 - lon0) / GRID_W,
                                        110_540 * abs(lat1 - lat0) / max(grid_h, 1))),
        "resolution_fuente_m": 30,
        "resolution_efectiva_m": round(max(dx_m, dy_m)),
        "fuente": "copernicus-dem-30",
        "metodo": "remuestreo bilineal del DEM de trabajo (~140 m), derivado de Copernicus GLO-30",
    }
    write_json("dem_grid.meta.json", meta)
    size = (OUT / "dem_grid.bin").stat().st_size / 1e3
    print(f"  {'dem_grid.bin':28s} {size:7.0f} kB")


def main() -> None:
    if not DEM_PATH.exists():
        raise SystemExit(
            f"Falta el DEM en {DEM_PATH}. Define PIURA_DEM o copia el DEM del laboratorio de modelos."
        )
    dem = np.load(DEM_PATH)
    limits = json.loads((RAW / "limits.json").read_text(encoding="utf-8"))
    network = json.loads((RAW / "network.json").read_text(encoding="utf-8"))

    print("cortes transversales:")
    build_cortes(dem, limits, network)
    print("malla de elevación:")
    build_grid(dem)
    print("listo")


if __name__ == "__main__":
    main()
