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
import shapefile
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer
from shapely import set_precision
from shapely.geometry import MultiPolygon, mapping, shape
from shapely.ops import transform, unary_union
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
WEB = ROOT / "web" / "public" / "data"
DEM_PATH = Path(os.environ.get("PIURA_DEM", ROOT.parent / "blender/projects/piura/data/dem.npz"))

RELIEF_W = 3072
EMSR = RAW / "emsr199"
FLOOD_MIN_AREA_M2 = 5_000
FLOOD_SIMPLIFY_M = 25

# Mismo eje que usa la maqueta 3D (`build_scene.py`). Es una interpretación
# aproximada: no es el eje oficial del canal ni un levantamiento.
CANAL_DANIEL_ESCOBAR = [
    (-80.500, -4.884),
    (-80.474, -4.918),
    (-80.448, -4.952),
    (-80.420, -4.985),
]

FLOOD_AOIS = [
    {
        "id": "AOI10",
        "carpeta": "aoi10_piura",
        "zona": "Piura, Catacaos y La Unión",
        "fecha": "2017-03-26/2017-03-30",
        "fecha_texto": "26–30 de marzo de 2017",
        "sensores": "Radarsat-2 (26/03) y Cosmo-SkyMed (30/03)",
    },
    {
        "id": "AOI11",
        "carpeta": "aoi11_parachique",
        "zona": "Parachique y llanura baja",
        "fecha": "2017-03-26",
        "fecha_texto": "26 de marzo de 2017",
        "sensores": "Radarsat-2 (26/03)",
    },
]

FIG_BBOX = (-81.18, -6.12, -80.30, -5.06)


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
        if not point_in_ring(mid[0], mid[1], ring):
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
            {"nombre": n, "tipo": t, "jerarquia": j, "fuente": "osm-lugares"},
        )
        for n, lo, la, t, j in LUGARES
    ]
    write("lugares.geojson", feature_collection(feats))


def _polygonal(geom):
    """Devuelve solo la parte poligonal de una geometría validada."""
    if geom is None:
        return None
    if geom.geom_type in {"Polygon", "MultiPolygon"}:
        return geom
    if geom.geom_type == "GeometryCollection":
        parts = [g for g in geom.geoms if g.geom_type in {"Polygon", "MultiPolygon"}]
        if not parts:
            return None
        return unary_union(parts)
    return None


def _flood_polygons(shp_path: Path):
    """Lee la capa `crisis_information_poly` y conserva solo `Flooded Area`."""
    reader = shapefile.Reader(str(shp_path), encoding="latin1")
    fields = [f[0] for f in reader.fields[1:]]
    geoms = []
    for sr in reader.iterShapeRecords():
        props = dict(zip(fields, sr.record))
        if props.get("interpret") != "Flooded Area":
            continue
        geom = shape(sr.shape.__geo_interface__)
        if not geom.is_valid:
            geom = make_valid(geom)
        if geom.geom_type == "Polygon":
            geoms.append(geom)
        elif geom.geom_type == "MultiPolygon":
            geoms.extend(geom.geoms)
        elif geom.geom_type == "GeometryCollection":
            geoms.extend(g for g in geom.geoms if g.geom_type == "Polygon")
    return geoms


def _keep_parts(geom, min_area_m2: float):
    parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    parts = [p for p in parts if p.area >= min_area_m2]
    if not parts:
        return None
    return parts[0] if len(parts) == 1 else MultiPolygon(parts)


def build_flood():
    """Publica la mancha oficial de 2017 (Copernicus EMSR199, AOI10 + AOI11)."""
    if not EMSR.exists():
        print("  (sin EMSR199 en data/raw; se omite flood_2017.geojson)")
        return

    transformer = Transformer.from_crs("EPSG:32717", "EPSG:4326", always_xy=True)
    feats = []
    for aoi in FLOOD_AOIS:
        shp_files = list((EMSR / aoi["carpeta"]).glob("*crisis_information_poly.shp"))
        if not shp_files:
            print(f"  (sin shapefile para {aoi['id']}; se omite)")
            continue
        raw = _flood_polygons(shp_files[0])
        if not raw:
            print(f"  ({aoi['id']} sin polígonos 'Flooded Area'; se omite)")
            continue

        merged = unary_union(raw)
        kept = _keep_parts(merged, FLOOD_MIN_AREA_M2)
        if kept is None:
            print(f"  ({aoi['id']} sin partes por encima del área mínima; se omite)")
            continue
        simplified = kept.simplify(FLOOD_SIMPLIFY_M, preserve_topology=True)
        simplified = _polygonal(make_valid(simplified))
        if simplified is None:
            print(f"  ({aoi['id']} no quedó geometría válida; se omite)")
            continue

        area_km2 = simplified.area / 1e6
        wgs = transform(transformer.transform, simplified)
        wgs = _polygonal(make_valid(set_precision(wgs, 1e-5)))
        if wgs is None:
            print(f"  ({aoi['id']} no se pudo reproyectar; se omite)")
            continue

        feats.append(
            feature(
                mapping(wgs),
                {
                    "evento": "Inundación de marzo de 2017",
                    "zona": aoi["zona"],
                    "aoi": f"EMSR199_{aoi['id']}",
                    "fecha": aoi["fecha"],
                    "fecha_texto": aoi["fecha_texto"],
                    "sensores": aoi["sensores"],
                    "area_km2": round(area_km2, 1),
                    "fuente": "copernicus-ems-emsr199",
                    "metodo": "vector oficial EMSR199; disuelto, filtrado y simplificado",
                    "esquematico": False,
                    "cobertura": "Cubre la llanura baja y el desierto adyacente; no toda la cuenca",
                },
            )
        )
        print(f"  {aoi['id']}: {len(raw)} polígonos → {area_km2:.1f} km²")

    if feats:
        write("flood_2017.geojson", feature_collection(feats))


def build_obras():
    """Publica Poechos y el canal Daniel Escobar como geometría esquemática."""
    data = json.loads((RAW / "water.json").read_text(encoding="utf-8"))
    poechos = next(
        (b for b in data.get("bodies", []) if b.get("manual") and "Poechos" in b.get("name", "")),
        None,
    )
    if poechos is None:
        raise SystemExit("water.json no contiene la represa manual de Poechos")

    ring = [[round(x, 5), round(y, 5)] for x, y in poechos["ring"]]
    if ring[0] != ring[-1]:
        ring.append(ring[0])

    feats = [
        feature(
            {"type": "Polygon", "coordinates": [ring]},
            {
                "nombre": "Represa de Poechos",
                "tipo": "represa",
                "esquematico": True,
                "fuente": "obras-esquematicas",
                "nota": "Contorno aproximado de 9 puntos; no es un levantamiento.",
            },
        ),
        feature(
            {
                "type": "LineString",
                "coordinates": [[round(x, 5), round(y, 5)] for x, y in CANAL_DANIEL_ESCOBAR],
            },
            {
                "nombre": "Canal Daniel Escobar",
                "tipo": "canal",
                "esquematico": True,
                "fuente": "obras-esquematicas",
                "nota": "Trazo aproximado de 4 puntos; no es el eje oficial del canal.",
            },
        ),
    ]
    write("obras.geojson", feature_collection(feats))


def _px(lon: float, lat: float, bbox, size) -> tuple[float, float]:
    west, south, east, north = bbox
    width, height = size
    return (
        (lon - west) / (east - west) * width,
        (north - lat) / (north - south) * height,
    )


def _font(size: int):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _font_bold(size: int):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def build_flood_figure():
    """Genera una figura estática de la mancha para /escenarios."""
    flood_path = WEB / "flood_2017.geojson"
    relief_path = WEB / "relieve.jpg"
    if not flood_path.exists() or not relief_path.exists():
        print("  (sin mancha o relieve; se omite flood_2017.jpg)")
        return

    flood = json.loads(flood_path.read_text(encoding="utf-8"))
    if not flood.get("features"):
        print("  (la mancha no tiene elementos; se omite la figura)")
        return

    relief = Image.open(relief_path).convert("RGB")
    info_path = OUT / "relieve_info.json"
    if info_path.exists():
        info = json.loads(info_path.read_text(encoding="utf-8"))
        # relieve_info.json guarda [oeste, norte, este, sur].
        full_bbox = [info["bbox"][0], info["bbox"][3], info["bbox"][2], info["bbox"][1]]
    else:
        full_bbox = [-81.45, -6.25, -79.30, -4.55]

    west, south, east, north = FIG_BBOX
    left, top = _px(west, north, full_bbox, relief.size)
    right, bottom = _px(east, south, full_bbox, relief.size)
    crop = relief.crop(
        (
            max(0, int(left)),
            max(0, int(top)),
            min(relief.width, int(right)),
            min(relief.height, int(bottom)),
        )
    )
    fig_w = 900
    fig_h = max(1, round(crop.height * fig_w / crop.width))
    crop = crop.resize((fig_w, fig_h), Image.LANCZOS)

    mask = Image.new("L", (fig_w, fig_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    polygons = []
    for feat in flood["features"]:
        geom = feat.get("geometry") or {}
        pieces = geom.get("coordinates") or []
        if geom.get("type") == "Polygon":
            pieces = [pieces]
        for piece in pieces:
            if not piece:
                continue
            exterior = [_px(x, y, FIG_BBOX, (fig_w, fig_h)) for x, y in piece[0]]
            if len(exterior) >= 3:
                mask_draw.polygon(exterior, fill=155)
                for hole in piece[1:]:
                    if hole:
                        mask_draw.polygon(
                            [_px(x, y, FIG_BBOX, (fig_w, fig_h)) for x, y in hole],
                            fill=0,
                        )
                polygons.append(piece)

    blue = Image.new("RGB", (fig_w, fig_h), (0, 105, 160))
    crop = Image.composite(blue, crop, mask)

    draw = ImageDraw.Draw(crop)
    for piece in polygons:
        exterior = [_px(x, y, FIG_BBOX, (fig_w, fig_h)) for x, y in piece[0]]
        if len(exterior) >= 2:
            draw.line(exterior, fill=(0, 66, 100), width=1)

    cuenca_path = WEB / "cuenca.geojson"
    if cuenca_path.exists():
        cuenca = json.loads(cuenca_path.read_text(encoding="utf-8"))
        for feat in cuenca.get("features", []):
            ring = ((feat.get("geometry") or {}).get("coordinates") or [[]])[0]
            if len(ring) >= 2:
                draw.line(
                    [_px(x, y, FIG_BBOX, (fig_w, fig_h)) for x, y in ring],
                    fill=(107, 46, 38),
                    width=3,
                )

    lugares_path = WEB / "lugares.geojson"
    if lugares_path.exists():
        lugares = json.loads(lugares_path.read_text(encoding="utf-8"))
        for feat in lugares.get("features", []):
            props = feat.get("properties") or {}
            lon, lat = (feat.get("geometry") or {}).get("coordinates") or (None, None)
            if lon is None or lat is None:
                continue
            if not (west <= lon <= east and south <= lat <= north):
                continue
            x, y = _px(lon, lat, FIG_BBOX, (fig_w, fig_h))
            jerarquia = int(props.get("jerarquia") or 3)
            size = 22 if jerarquia == 1 else 18 if jerarquia == 2 else 16
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(26, 34, 44))
            draw.text(
                (x + 7, y - size * 0.7),
                str(props.get("nombre") or ""),
                font=_font_bold(size) if jerarquia <= 2 else _font(size),
                fill=(26, 34, 44),
                stroke_width=2,
                stroke_fill=(247, 244, 234),
            )

    # Leyenda
    legend = (14, fig_h - 96, min(fig_w - 14, 390), fig_h - 14)
    draw.rounded_rectangle(legend, radius=6, fill=(247, 244, 234), outline=(217, 210, 191))
    ly = legend[1] + 12
    draw.rectangle((legend[0] + 12, ly, legend[0] + 30, ly + 14), fill=(0, 105, 160))
    draw.text(
        (legend[0] + 38, ly - 3),
        "Inundación de marzo de 2017",
        font=_font(16),
        fill=(26, 34, 44),
    )
    ly += 24
    draw.line((legend[0] + 12, ly + 7, legend[0] + 30, ly + 7), fill=(107, 46, 38), width=3)
    draw.text(
        (legend[0] + 38, ly - 3),
        "Límite de cuenca (ANA)",
        font=_font(16),
        fill=(26, 34, 44),
    )
    draw.text(
        (legend[0] + 12, legend[3] - 22),
        "Copernicus EMSR199 · 26–30 mar 2017",
        font=_font(13),
        fill=(76, 88, 102),
    )

    # Norte
    nx, ny = fig_w - 42, 28
    draw.text((nx - 5, ny - 22), "N", font=_font_bold(18), fill=(26, 34, 44),
              stroke_width=2, stroke_fill=(247, 244, 234))
    draw.polygon([(nx, ny - 4), (nx - 9, ny + 20), (nx, ny + 14), (nx + 9, ny + 20)],
                 fill=(26, 34, 44), outline=(247, 244, 234))

    # Escala de 20 km
    km_lon = 111.32 * math.cos(math.radians((south + north) / 2))
    bar = 20 / ((east - west) * km_lon) * fig_w
    bx, by = fig_w - 42 - bar, fig_h - 34
    draw.line((bx, by, bx + bar, by), fill=(26, 34, 44), width=3)
    draw.line((bx, by - 5, bx, by + 5), fill=(26, 34, 44), width=2)
    draw.line((bx + bar, by - 5, bx + bar, by + 5), fill=(26, 34, 44), width=2)
    draw.text((bx + bar / 2 - 16, by - 24), "20 km", font=_font(14), fill=(26, 34, 44),
              stroke_width=2, stroke_fill=(247, 244, 234))

    path = WEB / "flood_2017.jpg"
    crop.save(path, quality=86, optimize=True)
    print(f"  {'flood_2017.jpg':24s} {path.stat().st_size / 1e3:7.0f} kB")


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
    build_obras()
    build_flood()
    build_relief()
    build_flood_figure()
    print("listo")


if __name__ == "__main__":
    main()
