#!/usr/bin/env python3
"""Descarga los vectores oficiales de la inundación de marzo de 2017 (Copernicus EMSR199).

Se usan dos áreas de interés de la activación EMSR199:

- AOI10 PIURA: Piura, Catacaos y La Unión.
- AOI11 PARACHIQUE: llanura baja y desierto adyacente.

Los ZIP se guardan en `data/raw/emsr199/` (ignorado por Git) y se extraen en
subdirectorios. `build_layers.py` lee los shapefiles y publica una versión
simplificada en `web/public/data/flood_2017.geojson`.

Fuente: Copernicus Emergency Management Service — Rapid Mapping, activación
EMSR199 (22/03/2017). Datos públicos, reutilizables con atribución.
DOI de la activación: https://doi.org/10.2905/JRC.GKDVN10

Uso:
    python3 etl/download_emsr199.py
    python3 etl/download_emsr199.py --force
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "emsr199"
BASE_URL = "https://cems-mapping-website.s3.eu-west-1.amazonaws.com/static/activations/EMSR199"
USER_AGENT = "rio-piura-atlas/0.2 (atlas documentado; uso manual)"

AOIS = [
    {
        "id": "AOI10",
        "carpeta": "aoi10_piura",
        "producto": "EMSR199_10PIURA_DELINEATION_OVERVIEW_v2_vector.zip",
        "zona": "Piura, Catacaos y La Unión",
    },
    {
        "id": "AOI11",
        "carpeta": "aoi11_parachique",
        "producto": "EMSR199_11PARACHIQUE_DELINEATION_OVERVIEW_v1_vector.zip",
        "zona": "Parachique y llanura baja",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def descargar(url: str, destino: Path, force: bool) -> None:
    if destino.exists() and not force:
        print(f"  ya existe {destino.relative_to(ROOT)} ({destino.stat().st_size / 1e6:.1f} MB)")
        return

    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(destino.suffix + ".part")
    print(f"  descargando {url.rsplit('/', 1)[-1]}…")
    try:
        with requests.get(
            url,
            stream=True,
            timeout=180,
            headers={"User-Agent": USER_AGENT},
        ) as response:
            response.raise_for_status()
            with temporal.open("wb") as fh:
                for block in response.iter_content(chunk_size=1024 * 1024):
                    if block:
                        fh.write(block)
        temporal.replace(destino)
    finally:
        if temporal.exists():
            temporal.unlink()
    print(f"  guardado {destino.relative_to(ROOT)} ({destino.stat().st_size / 1e6:.1f} MB)")


def extraer(zip_path: Path, destino: Path, force: bool) -> None:
    if destino.exists() and not force:
        if list(destino.glob("*crisis_information_poly.shp")):
            print(f"  ya extraído {destino.relative_to(ROOT)}")
            return
        raise SystemExit(f"{destino} existe pero no contiene la capa de inundación; usa --force")

    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(destino)
    if not list(destino.glob("*crisis_information_poly.shp")):
        raise SystemExit(f"{zip_path.name} no contiene *crisis_information_poly.shp")
    print(f"  extraído {destino.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="volver a descargar y extraer")
    args = parser.parse_args()

    print("Copernicus EMSR199 · inundación de marzo de 2017")
    RAW.mkdir(parents=True, exist_ok=True)
    for aoi in AOIS:
        print(f"\n{aoi['id']} · {aoi['zona']}")
        zip_path = RAW / aoi["producto"]
        destino = RAW / aoi["carpeta"]
        descargar(f"{BASE_URL}/{aoi['producto']}", zip_path, args.force)
        print(f"  sha256 {sha256(zip_path)}")
        extraer(zip_path, destino, args.force)

    print("\nlisto. Ahora ejecuta: python3 etl/build_layers.py")


if __name__ == "__main__":
    main()
