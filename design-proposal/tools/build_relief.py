#!/usr/bin/env python3
"""Genera el relieve de la propuesta visual a partir del mismo DEM del ETL.

No cambia geometría ni datos: solo reclasifica el color y el sombreado para
evaluar la dirección de arte «Lámina y margen». El archivo de salida vive en
design-proposal/assets/ y no se publica en el sitio.

Uso:
    python3 design-proposal/tools/build_relief.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parents[2]
DEM = ROOT.parent / "blender" / "projects" / "piura" / "data" / "dem.npz"
OUT = ROOT / "design-proposal" / "assets" / "relieve-propuesta.jpg"
W = 2400

# Rampa hipsométrica: arena -> ocre -> oliva -> gris de roca.
# El color indica altitud, no vegetación (misma regla que el ETL).
STOPS = [
    (0, (216, 199, 166)),
    (120, (214, 196, 161)),
    (400, (201, 183, 145)),
    (800, (184, 166, 128)),
    (1300, (161, 149, 116)),
    (1900, (137, 137, 111)),
    (2500, (116, 121, 103)),
    (3100, (102, 108, 98)),
    (3700, (125, 124, 116)),
    (4200, (196, 193, 184)),
]
SEA = (170, 197, 200)


def main() -> None:
    data = np.load(DEM)
    elev = data["elev"]
    lon, lat = data["lon"], data["lat"]

    h, w = elev.shape
    height = int(round(W * h / w))
    big = np.asarray(Image.fromarray(elev).resize((W, height), Image.BICUBIC), dtype=np.float32)

    xs = np.array([s[0] for s in STOPS], dtype=np.float32)
    color = np.empty((height, W, 3), dtype=np.float32)
    for c in range(3):
        color[:, :, c] = np.interp(big, xs, np.array([s[1][c] for s in STOPS], dtype=np.float32))

    dx = 111_320 * abs(lon[1] - lon[0]) / w
    dy = 110_540 * abs(lat[0] - lat[1]) / h
    gy, gx = np.gradient(elev, dy, dx)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    hs = np.zeros_like(elev)
    for az, alt, weight in ((315, 42, 0.6), (45, 38, 0.25), (225, 30, 0.15)):
        a, e = math.radians(az), math.radians(alt)
        hs += weight * np.clip(
            np.sin(e) * np.cos(slope) + np.cos(e) * np.sin(slope) * np.cos(a - aspect),
            0,
            1,
        )
    hs_big = np.asarray(
        Image.fromarray((hs * 255).astype(np.uint8)).resize((W, height), Image.BILINEAR),
        dtype=np.float32,
    ) / 255.0

    # Solo el océano (el componente de cota cero más grande) se pinta como mar.
    # Las lagunas interiores quedan en color de terreno y las dibuja la capa OSM.
    rough = big <= 0.5
    tags, count = label(rough)
    sizes = np.bincount(tags.ravel())
    sizes[0] = 0
    sea = tags == int(np.argmax(sizes)) if count else np.zeros_like(rough)
    color[sea] = SEA

    # Sombreado suave: la propuesta evita el aspecto de satélite saturado.
    shade = (0.78 + 0.38 * (hs_big - 0.5)).clip(0.62, 1.10)
    color *= shade[:, :, None]

    # Un velo de papel muy leve para integrar el ráster con la página.
    paper = np.array((245, 241, 230), dtype=np.float32)
    color = color * 0.94 + paper * 0.06

    img = Image.fromarray(np.clip(color, 0, 255).astype(np.uint8))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, quality=84, optimize=True, progressive=True)
    print(f"{OUT.relative_to(ROOT)}  {OUT.stat().st_size / 1024:.0f} kB  {img.size[0]}x{img.size[1]}")


if __name__ == "__main__":
    main()
