#!/usr/bin/env python3
"""Descarga las series históricas diarias de las estaciones de Piura.

Fuente: API del Observatorio de SENAMHI.
- Catálogo: /api/researchers/historical-download/stations
- Serie:   /api/researchers/historical-download/stations/{id}/series

Guarda JSON crudo en `data/raw/senamhi/` (ignorado por Git). No publica el dato:
la licencia de reutilización no está confirmada. `build_senamhi_historico.py`
genera una tabla plana en `data/processed/senamhi/` para revisión local.

Uso:
    python3 etl/download_senamhi_historico.py
    python3 etl/download_senamhi_historico.py --force
    python3 etl/download_senamhi_historico.py --limit 2 --raw-dir /tmp/senamhi
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
API = "https://servicios.senamhi.gob.pe/api/researchers/historical-download"
RAW_DEFAULT = ROOT / "data" / "raw" / "senamhi"
USER_AGENT = "rio-piura-atlas/0.3 (atlas documentado; uso manual)"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_json(url: str) -> dict:
    response = requests.get(
        url,
        timeout=120,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("status"):
        raise RuntimeError(f"la API devolvió status={payload.get('status')} para {url}")
    return payload


def piura_stations(payload: dict) -> list[dict]:
    estaciones = payload.get("data") or []
    piura = [
        e
        for e in estaciones
        if str(e.get("departmentName", "")).strip().upper() == "PIURA"
    ]
    return sorted(piura, key=lambda e: str(e.get("id", "")))


def download(raw_dir: Path, force: bool, limit: int | None) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    stations_path = raw_dir / "stations.json"

    if stations_path.exists() and not force:
        print(f"  usando catálogo existente {stations_path}")
        payload = json.loads(stations_path.read_text(encoding="utf-8"))
    else:
        print("  descargando catálogo de estaciones…")
        payload = fetch_json(f"{API}/stations")
        stations_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"  guardado {stations_path}")

    estaciones = piura_stations(payload)
    if limit is not None:
        estaciones = estaciones[:limit]
    if not estaciones:
        raise SystemExit("no se encontraron estaciones de Piura en el catálogo")

    series_dir = raw_dir / "series"
    series_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "fuente": "senamhi-historico-estaciones",
        "api": API,
        "consultado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "estaciones": [],
        "licencia": "dato público; términos de reutilización por confirmar",
        "publicado": False,
    }

    for estacion in estaciones:
        sid = str(estacion["id"])
        destino = series_dir / f"{sid}.json"
        if destino.exists() and not force:
            print(f"  {sid} {estacion.get('name')}: ya existe")
        else:
            print(f"  {sid} {estacion.get('name')}: descargando…")
            serie = fetch_json(f"{API}/stations/{sid}/series")
            destino.write_text(
                json.dumps(serie, ensure_ascii=False, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            print(f"    {destino.name} ({destino.stat().st_size / 1e6:.1f} MB)")
        manifest["estaciones"].append(
            {
                "id": sid,
                "name": estacion.get("name"),
                "provinceName": estacion.get("provinceName"),
                "districtName": estacion.get("districtName"),
                "latitude": estacion.get("latitude"),
                "longitude": estacion.get("longitude"),
                "altitude": estacion.get("altitude"),
                "file": f"series/{sid}.json",
                "sha256": sha256(destino),
                "bytes": destino.stat().st_size,
            }
        )

    (raw_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nlisto: {len(estaciones)} estaciones en {raw_dir}")
    print("siguiente: python3 etl/build_senamhi_historico.py")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="volver a descargar")
    parser.add_argument("--limit", type=int, default=None, help="descargar solo N estaciones")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DEFAULT,
        help="directorio de salida (por defecto data/raw/senamhi)",
    )
    args = parser.parse_args()
    print("SENAMHI · series históricas por estación")
    download(args.raw_dir, args.force, args.limit)


if __name__ == "__main__":
    main()
