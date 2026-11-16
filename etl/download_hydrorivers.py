#!/usr/bin/env python3
"""Descarga HydroRIVERS v10 y construye data/raw/network.json.

Recorta la red a la ventana del atlas (con un pequeño margen para no cortar
tramos en el borde) y conserva los campos que usa build_layers.py.

El ZIP de Sudamérica pesa ~95 MB y se guarda en data/raw/hydrorivers/ (ignorado
por Git). La descarga se conserva para no repetirla en cada ejecución.

Uso:
    python3 etl/download_hydrorivers.py
    python3 etl/download_hydrorivers.py --out data/raw/network.json --force
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import requests
import shapefile

ROOT = Path(__file__).resolve().parents[1]
URL = "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_sa_shp.zip"
BBOX = (-81.45, -6.25, -79.30, -4.55)
BUFFER = 0.05


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"  usando {dest}")
        return
    print(f"  descargando {url}")
    with requests.get(url, stream=True, timeout=300) as response:
        response.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with tmp.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=1 << 20):
                if chunk:
                    fh.write(chunk)
        tmp.replace(dest)
    print(f"  guardado en {dest} ({dest.stat().st_size / 1e6:.0f} MB)")


def extract(zip_path: Path, dest: Path) -> Path:
    shp = dest / "HydroRIVERS_v10_sa_shp" / "HydroRIVERS_v10_sa.shp"
    if shp.exists():
        return shp
    print("  extrayendo shapefile…")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    if not shp.exists():
        raise SystemExit(f"no se encontró {shp} dentro del ZIP")
    return shp


def intersects(bbox, west, south, east, north) -> bool:
    return not (bbox[2] < west or bbox[0] > east or bbox[3] < south or bbox[1] > north)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "raw" / "network.json")
    parser.add_argument("--cache", type=Path, default=ROOT / "data" / "raw" / "hydrorivers")
    parser.add_argument("--force", action="store_true", help="sobrescribir la salida si ya existe")
    parser.add_argument("--buffer", type=float, default=BUFFER, help="margen en grados alrededor del atlas")
    args = parser.parse_args()

    if args.out.exists() and not args.force:
        raise SystemExit(f"{args.out} ya existe. Usa --force para reemplazarlo.")

    zip_path = args.cache / "HydroRIVERS_v10_sa_shp.zip"
    download(URL, zip_path)
    shp_path = extract(zip_path, args.cache)

    west, south, east, north = (
        BBOX[0] - args.buffer,
        BBOX[1] - args.buffer,
        BBOX[2] + args.buffer,
        BBOX[3] + args.buffer,
    )

    print("  filtrando la red…")
    reader = shapefile.Reader(str(shp_path))
    rios = []
    for record, shape_rec in zip(reader.iterRecords(), reader.iterShapes()):
        if not intersects(shape_rec.bbox, west, south, east, north):
            continue
        coords = [[round(float(x), 5), round(float(y), 5)] for x, y in shape_rec.points]
        if len(coords) < 2:
            continue
        rios.append(
            {
                "id": int(record["HYRIV_ID"]),
                "order": int(record["ORD_STRA"]),
                "upland": round(float(record["UPLAND_SKM"]), 1),
                "next": int(record["NEXT_DOWN"]),
                "length_km": round(float(record["LENGTH_KM"]), 2),
                "coords": coords,
            }
        )

    rios.sort(key=lambda r: r["id"])
    output = {
        "basins": [],
        "rivers": rios,
        "bounds": list(BBOX),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, separators=(",", ":")), encoding="utf-8")
    print(f"  {args.out}: {len(rios)} tramos · {args.out.stat().st_size / 1e3:.0f} kB")
    print("  (basins queda vacío: build_layers.py no lo usa y no se descarga HydroBASINS)")


if __name__ == "__main__":
    main()
