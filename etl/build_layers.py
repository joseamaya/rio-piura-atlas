#!/usr/bin/env python3
"""Construye las capas web del atlas a partir de los datos crudos.

Entrada:  data/raw/{limits,network,water}.json  y el DEM del laboratorio de modelos
Salida:   data/processed/*.geojson  y  web/public/data/*

Uso:
    python3 etl/build_layers.py
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
WEB = ROOT / "web" / "public" / "data"
DEM_PATH = Path(os.environ.get("PIURA_DEM", ROOT.parent / "blender/projects/piura/data/dem.npz"))

RELIEF_W = 3072


def round_ring(ring, nd=5):
    return [[round(x, nd), round(y, nd)] for x, y in ring]


def rdp(points, tol):
    """Ramer–Douglas–Peucker; conserva el cierre si el anillo viene cerrado."""
    closed = len(points) > 2 and points[0] == points[-1]
    if closed:
        points = points[:-1]
    if len(points) < 3:
        return points + [points[0]] if closed else points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        x1, y1 = points[i]
        x2, y2 = points[j]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1e-12
        best, idx = -1.0, i
        for k in range(i + 1, j):
            d = abs(dy * (points[k][0] - x1) - dx * (points[k][1] - y1)) / n
            if d > best:
                best, idx = d, k
        if best > tol:
            keep[idx] = True
            stack += [(i, idx), (idx, j)]
    out = [p for p, k in zip(points, keep) if k]
    return out + [out[0]] if closed else out


def write(name, obj):
    for base in (OUT, WEB):
        base.mkdir(parents=True, exist_ok=True)
        path = base / name
        path.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
    size = (OUT / name).stat().st_size / 1e3
    print(f"  {name:24s} {size:7.0f} kB")


def feature(geom, props):
    return {"type": "Feature", "geometry": geom, "properties": props}


def build_limits():
    data = json.loads((RAW / "limits.json").read_text(encoding="utf-8"))
    cuenca = feature(
        {"type": "Polygon", "coordinates": [round_ring(rdp(data["ring"], 0.0006))]},
        {
            "nombre": "Cuenca del río Piura",
            "area_km2": data["area_km2"],
            "fuente": "ana-subcuencas",
            "escala": "1:100 000",
            "codigo": data.get("code"),
        },
    )
    subs = []
    for s in data["subbasins"]:
        subs.append(
            feature(
                {"type": "Polygon", "coordinates": [round_ring(rdp(s["ring"], 0.0006))]},
                {"nombre": s["name"], "area_km2": s["area_km2"], "fuente": "ana-subcuencas"},
            )
        )
    write("cuenca.geojson", feature_collection([cuenca]))
    write("subcuencas.geojson", feature_collection(subs))
    return data["ring"]


def feature_collection(features):
    return {"type": "FeatureCollection", "features": features}


def point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i - 1]
        x2, y2 = ring[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


def build_rivers():
    net = json.loads((RAW / "network.json").read_text(encoding="utf-8"))
    limits = json.loads((RAW / "limits.json").read_text(encoding="utf-8"))
    ring = limits["ring"]
    feats = []
    for seg in net["rivers"]:
        if seg["upland"] < 150 or len(seg["coords"]) < 2:
            continue
        mid = seg["coords"][len(seg["coords"]) // 2]
        if not point_in_ring(mid[0], mid[1], ring) and seg["upland"] < 4000:
            continue  # fuera de la cuenca: el atlas no dibuja cuencas vecinas
        coords = [[round(x, 5), round(y, 5)] for x, y in seg["coords"]]
        if len(coords) > 4:
            coords = rdp(coords, 0.0004)
        feats.append(
            feature(
                {"type": "LineString", "coordinates": coords},
                {"aporte_km2": seg["upland"], "orden": seg["order"], "fuente": "hydrorivers"},
            )
        )
    write("red_hidrica.geojson", feature_collection(feats))


def build_water():
    data = json.loads((RAW / "water.json").read_text(encoding="utf-8"))
    feats = []
    for b in data["bodies"]:
        if b.get("manual"):
            continue
        feats.append(
            feature(
                {"type": "Polygon", "coordinates": [round_ring(rdp(b["ring"], 0.0005))]},
                {
                    "nombre": b["name"] or "Cuerpo de agua sin nombre",
                    "area_km2": b["area_km2"],
                    "intermitente": b["intermittent"],
                    "fuente": "osm-agua",
                },
            )
        )
    write("agua.geojson", feature_collection(feats))


LUGARES = [
    ("Piura", -80.63, -5.19, "ciudad", 1),
    ("Castilla", -80.69, -5.11, "ciudad", 2),
    ("Catacaos", -80.68, -5.27, "ciudad", 2),
    ("Chulucanas", -80.16, -5.09, "ciudad", 1),
    ("Tambogrande", -80.35, -4.93, "ciudad", 2),
    ("Morropón", -79.97, -5.19, "ciudad", 2),
    ("Sechura", -80.82, -5.55, "ciudad", 2),
    ("Paita", -81.06, -5.08, "ciudad", 2),
    ("La Unión", -80.66, -5.42, "ciudad", 3),
    ("Cura Mori", -80.72, -5.38, "ciudad", 3),
    ("Huarmaca", -79.85, -5.75, "ciudad", 3),
    ("Salitral", -79.79, -5.42, "ciudad", 3),
    ("Canchaque", -79.62, -5.40, "ciudad", 3),
]


def build_places():
    feats = [
        feature(
            {"type": "Point", "coordinates": [lo, la]},
            {"nombre": n, "tipo": t, "jerarquia": j, "fuente": "osm-agua"},
        )
        for n, lo, la, t, j in LUGARES
    ]
    write("lugares.geojson", feature_collection(feats))


def build_relief():
    if not DEM_PATH.exists():
        print(f"  (sin DEM en {DEM_PATH}; se omite el relieve)")
        return
    dem = np.load(DEM_PATH)
    elev = dem["elev"]
    lon, lat = dem["lon"], dem["lat"]

    h, w = elev.shape
    W = RELIEF_W
    H = int(round(W * h / w))
    big = np.asarray(Image.fromarray(elev).resize((W, H), Image.BICUBIC), dtype=np.float32)

    stops = [
        (0, (206, 188, 150)), (120, (208, 191, 152)), (400, (196, 184, 141)),
        (800, (172, 172, 120)), (1300, (139, 155, 97)), (1900, (110, 137, 84)),
        (2500, (101, 126, 80)), (3100, (150, 138, 112)), (3700, (198, 189, 175)),
        (4100, (234, 233, 228)),
    ]
    xs = np.array([s[0] for s in stops], dtype=np.float32)
    color = np.empty((H, W, 3), dtype=np.float32)
    for c in range(3):
        color[:, :, c] = np.interp(big, xs, np.array([s[1][c] for s in stops], dtype=np.float32))

    dx = 111_320 * abs(lon[1] - lon[0]) / w
    dy = 110_540 * abs(lat[0] - lat[1]) / h
    gy, gx = np.gradient(elev, dy, dx)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    hs = np.zeros_like(elev)
    for az, alt, wgt in ((315, 42, 0.6), (45, 38, 0.25), (225, 30, 0.15)):
        a, e = math.radians(az), math.radians(alt)
        hs += wgt * np.clip(np.sin(e) * np.cos(slope) + np.cos(e) * np.sin(slope) * np.cos(a - aspect), 0, 1)
    hs_big = np.asarray(Image.fromarray((hs * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
                        dtype=np.float32) / 255.0

    from scipy.ndimage import label

    rough = big <= 0.5
    tags, _ = label(rough)
    border = set(np.unique(np.concatenate([tags[0, :], tags[-1, :], tags[:, 0], tags[:, -1]])))
    border.discard(0)
    sea = np.isin(tags, list(border)) if border else np.zeros_like(rough)
    color[sea] = (56, 104, 132)
    color *= (0.70 + 0.55 * (hs_big - 0.5)).clip(0.5, 1.18)[:, :, None]

    img = Image.fromarray(np.clip(color, 0, 255).astype(np.uint8))
    path = WEB / "relieve.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=86, optimize=True)
    (OUT / "relieve_info.json").write_text(
        json.dumps({"bbox": [float(lon[0]), float(lat[0]), float(lon[1]), float(lat[1])],
                    "size": [W, H]})
    )
    print(f"  {'relieve.jpg':24s} {path.stat().st_size / 1e3:7.0f} kB")


def main() -> None:
    print("capas:")
    build_limits()
    build_rivers()
    build_water()
    build_places()
    build_relief()
    print("listo")


if __name__ == "__main__":
    main()
