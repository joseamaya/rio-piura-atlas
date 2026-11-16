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

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
WEB = ROOT / "web" / "public" / "data"
DEM_PATH = Path(os.environ.get("PIURA_DEM", ROOT.parent / "blender/projects/piura/data/dem.npz"))

GRID_W = 512
# 801 muestras sobre 24 km dan un paso de 30 m, la resolución real del DEM.
MUESTRAS = 801

# id, nombre visible, longitud, latitud, largo total del transecto en km.
# El punto es un ancla; la orientación se calcula perpendicular al río más cercano.
ANCLAS = [
    ("bajo-piura", "Bajo Piura · La Unión", -80.66, -5.42, 24),
    ("piura", "Piura ciudad", -80.63, -5.19, 24),
    ("catacaos", "Catacaos", -80.68, -5.27, 22),
    ("chulucanas", "Chulucanas", -80.16, -5.09, 24),
    ("tambogrande", "Tambogrande", -80.35, -4.93, 24),
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


def nearest_segment(rivers, lon, lat, min_upland=500.0):
    """Devuelve el segmento de río con área aportante suficiente más cercano."""
    best = None
    for river in rivers:
        if river["upland"] < min_upland:
            continue
        for i in range(len(river["coords"]) - 1):
            (x1, y1), (x2, y2) = river["coords"][i], river["coords"][i + 1]
            d = math.hypot((x1 + x2) / 2 - lon, (y1 + y2) / 2 - lat)
            if best is None or d < best[0]:
                best = (d, (x1, y1), (x2, y2))
    return None if best is None else (best[1], best[2])


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


def clip_to_ring(a, b, ring, steps=400):
    """Recorta el transecto al tramo continuo más largo dentro de la cuenca."""
    inside = []
    for i in range(steps):
        t = i / (steps - 1)
        point = interpolate(a[0], a[1], a, b, t)
        inside.append(point_in_ring(point[0], point[1], ring))

    best_start = best_end = None
    start = None
    for i, ok in enumerate(inside + [False]):
        if ok and start is None:
            start = i
        elif not ok and start is not None:
            if best_start is None or (i - start) > (best_end - best_start):
                best_start, best_end = start, i - 1
            start = None
    if best_start is None:
        return None
    return (
        interpolate(a[0], a[1], a, b, best_start / (steps - 1)),
        interpolate(a[0], a[1], a, b, best_end / (steps - 1)),
    )


def profile(a, b, elev, lon0, lon1, lat0, lat1):
    dist_km, elev_m = [], []
    total = distance_km(a, b)
    for i in range(MUESTRAS):
        t = i / (MUESTRAS - 1)
        lon, lat = interpolate(a[0], a[1], a, b, t)
        value = sample_dem(elev, lon0, lon1, lat0, lat1, lon, lat)
        dist_km.append(round(total * t, 2))
        elev_m.append(None if math.isnan(value) else round(value, 1))
    return dist_km, elev_m


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
    ring = limits["ring"]

    features, perfiles = [], {}
    for ident, nombre, lon, lat, length in ANCLAS:
        segment = nearest_segment(network["rivers"], lon, lat)
        if segment is None:
            print(f"  (sin río cerca de {nombre}; se omite el corte)")
            continue
        perp = perpendicular(segment[0], segment[1], lat)
        raw_a, raw_b = transect(lon, lat, perp, length)
        clipped = clip_to_ring(raw_a, raw_b, ring)
        if clipped is None:
            print(f"  (el transecto de {nombre} no cruza la cuenca; se omite)")
            continue
        a, b = clipped
        dist, values = profile(a, b, elev, lon0, lon1, lat0, lat1)
        clean = [v for v in values if v is not None]
        if len(clean) < 2:
            print(f"  (sin datos de DEM para {nombre}; se omite)")
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
                    "metodo": "transecto perpendicular a la red, recortado a la cuenca; perfil del DEM",
                    "resolucion_fuente_m": 30,
                },
            }
        )
        perfiles[ident] = {
            "nombre": nombre,
            "longitud_km": round(distance_km(a, b), 2),
            "elev_min_m": round(min(clean)),
            "elev_max_m": round(max(clean)),
            "paso_perfil_m": round(distance_km(a, b) * 1000 / (MUESTRAS - 1), 1),
            "dist_km": dist,
            "elev_m": values,
        }

    write_json("cortes.geojson", {"type": "FeatureCollection", "features": features})
    write_json(
        "cortes_perfiles.json",
        {
            "resolucion_fuente_m": 30,
            "resolucion_malla_m": round(111_320 * abs(lon1 - lon0) / GRID_W),
            "nota": (
                "Perfiles de referencia calculados del Copernicus DEM GLO-30. "
                "La malla del visor para cortes dibujados tiene otra resolución. "
                "No sirve para dimensionar obras."
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
    meta = {
        "bbox": [lon0, min(lat0, lat1), lon1, max(lat0, lat1)],
        "width": GRID_W,
        "height": grid_h,
        "dtype": "int16",
        "byte_order": "little",
        "row_order": "north-to-south",
        "resolution_m_aprox": round(111_320 * abs(lon1 - lon0) / GRID_W),
        "fuente": "copernicus-dem-30",
        "metodo": "remuestreo bilineal del DEM de 30 m",
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
