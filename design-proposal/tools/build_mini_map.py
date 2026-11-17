#!/usr/bin/env python3
"""Miniatura cartográfica del atlas para la portada de la propuesta.

Usa exactamente las geometrías publicadas (cuenca, subcuencas, red, agua).
No generaliza ni inventa formas: solo proyecta y colorea para una figura
editorial. Salida: design-proposal/assets/mini-cuenca.svg
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "web" / "public" / "data"
OUT = ROOT / "design-proposal" / "assets" / "mini-cuenca.svg"

W, H = 1200, 900
PAD = 36

SUBCUENCA_COLORS = [
    "#e4d7bd", "#d9c9a8", "#cdbb94", "#bfae88", "#b3a37f",
    "#a99a78", "#9e9274", "#948a70", "#89816b",
]


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def collect(geom):
    """Devuelve listas de anillos (polígonos) y líneas."""
    polys, lines = [], []
    if geom["type"] == "Polygon":
        polys.append(geom["coordinates"])
    elif geom["type"] == "MultiPolygon":
        polys.extend(geom["coordinates"])
    elif geom["type"] == "LineString":
        lines.append(geom["coordinates"])
    elif geom["type"] == "MultiLineString":
        lines.extend(geom["coordinates"])
    return polys, lines


def bounds(features):
    xs, ys = [], []
    for f in features:
        polys, lines = collect(f["geometry"])
        for poly in polys:
            for ring in poly:
                for x, y in ring:
                    xs.append(x); ys.append(y)
        for line in lines:
            for x, y in line:
                xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def main() -> None:
    cuenca = load("cuenca.geojson")
    subcuencas = load("subcuencas.geojson")
    rios = load("red_hidrica.geojson")
    agua = load("agua.geojson")

    west, south, east, north = bounds(cuenca["features"])
    lat_mid = (south + north) / 2
    kx = math.cos(math.radians(lat_mid))
    span_x = (east - west) * kx
    span_y = north - south
    scale = min((W - 2 * PAD) / span_x, (H - 2 * PAD) / span_y)
    off_x = (W - span_x * scale) / 2
    off_y = (H - span_y * scale) / 2

    def project(lon, lat):
        x = off_x + (lon - west) * kx * scale
        y = off_y + (north - lat) * scale
        return round(x, 2), round(y, 2)

    def ring_path(ring):
        pts = [project(x, y) for x, y in ring]
        if not pts:
            return ""
        d = f"M {pts[0][0]} {pts[0][1]}"
        d += "".join(f" L {x} {y}" for x, y in pts[1:])
        return d + " Z"

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'role="img" aria-labelledby="mini-title mini-desc">'
    )
    parts.append("<title id=\"mini-title\">La cuenca del río Piura y sus subcuencas</title>")
    parts.append(
        "<desc id=\"mini-desc\">Figura editorial de la cuenca ANA, ocho subcuencas oficiales, "
        "Bajo Piura derivado, red hídrica y cuerpos de agua. Sin rótulos; la leyenda está en el texto.</desc>"
    )
    parts.append(f'<rect width="{W}" height="{H}" fill="#f5f1e6"/>')

    # Cuenca como fondo.
    for f in cuenca["features"]:
        polys, _ = collect(f["geometry"])
        for poly in polys:
            parts.append(f'<path d="{ring_path(poly[0])}" fill="#eee5d2" stroke="none"/>')

    # Subcuencas.
    for i, f in enumerate(subcuencas["features"]):
        color = SUBCUENCA_COLORS[i % len(SUBCUENCA_COLORS)]
        polys, _ = collect(f["geometry"])
        for poly in polys:
            parts.append(
                f'<path d="{ring_path(poly[0])}" fill="{color}" fill-opacity="0.92" '
                f'stroke="#8b806c" stroke-width="1.1" stroke-linejoin="round"/>'
            )

    # Cuerpos de agua.
    for f in agua["features"]:
        polys, _ = collect(f["geometry"])
        for poly in polys:
            parts.append(f'<path d="{ring_path(poly[0])}" fill="#1d6a86" fill-opacity="0.86"/>')

    # Red hídrica.
    for f in rios["features"]:
        _, lines = collect(f["geometry"])
        for line in lines:
            pts = [project(x, y) for x, y in line]
            if len(pts) < 2:
                continue
            d = f"M {pts[0][0]} {pts[0][1]}" + "".join(f" L {x} {y}" for x, y in pts[1:])
            parts.append(f'<path d="{d}" fill="none" stroke="#1d6a86" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round"/>')

    # Límite de cuenca.
    for f in cuenca["features"]:
        polys, _ = collect(f["geometry"])
        for poly in polys:
            parts.append(
                f'<path d="{ring_path(poly[0])}" fill="none" stroke="#7a3a2b" '
                f'stroke-width="3" stroke-linejoin="round"/>'
            )

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}  {OUT.stat().st_size / 1024:.0f} kB")


if __name__ == "__main__":
    main()
