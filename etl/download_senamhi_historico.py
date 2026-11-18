#!/usr/bin/env python3
"""Descarga las series históricas diarias de las estaciones de Piura.

Fuente: API del Observatorio de SENAMHI.
- Catálogo: /api/researchers/historical-download/stations
- Serie:   /api/researchers/historical-download/stations/{id}/series

Guarda los bytes crudos de cada respuesta en `data/raw/senamhi/` (ignorado por
Git), con un manifiesto de SHA-256. No publica el dato: la licencia de
reutilización no está confirmada. `build_senamhi_historico.py` genera las tablas
de revisión en `data/processed/senamhi/`.

Uso:
    python3 etl/download_senamhi_historico.py
    python3 etl/download_senamhi_historico.py --force
    python3 etl/download_senamhi_historico.py --limit 2 --raw-dir /tmp/senamhi
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
API = "https://servicios.senamhi.gob.pe/api/researchers/historical-download"
RAW_DEFAULT = ROOT / "data" / "raw" / "senamhi"
PUBLIC = ROOT / "web" / "public"
USER_AGENT = "rio-piura-atlas/0.4 (atlas documentado; uso manual)"
SELECTION_DEFAULT = ROOT / "etl" / "senamhi_estaciones_piura.txt"


def sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_not_public(path: Path) -> None:
    resolved = path.resolve()
    if resolved == PUBLIC or PUBLIC in resolved.parents:
        raise SystemExit(
            f"destino no permitido: {path}. Los datos de SENAMHI no se publican "
            "en web/public hasta confirmar los términos."
        )


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(path)


def parse_payload(content: bytes, url: str) -> dict:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"respuesta no JSON en {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"respuesta no es un objeto JSON en {url}")
    if payload.get("status") is not True:
        raise RuntimeError(
            f"la API devolvió status={payload.get('status')} para {url}: "
            f"{payload.get('message')}"
        )
    if not isinstance(payload.get("data"), list):
        raise RuntimeError(f"la API no devolvió una lista 'data' para {url}")
    return payload


def fetch(
    session: requests.Session,
    url: str,
    timeout: int,
    retries: int,
) -> tuple[bytes, dict]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code >= 500:
                raise RuntimeError(f"HTTP {response.status_code} en {url}")
            response.raise_for_status()
            parse_payload(response.content, url)
            return response.content, {
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        except (requests.RequestException, RuntimeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2 ** (attempt - 1))
    raise RuntimeError(f"no se pudo descargar {url}: {last_error}")


def piura_stations(payload: dict) -> list[dict]:
    return sorted(
        [
            e
            for e in payload.get("data") or []
            if isinstance(e, dict)
            and str(e.get("departmentName", "")).strip().upper() == "PIURA"
        ],
        key=lambda e: str(e.get("id", "")),
    )


def read_ids(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []
    ids = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            ids.append(line)
    if len(ids) != len(set(ids)):
        raise SystemExit(f"{path}: IDs duplicados")
    return ids


def choose_stations(
    stations: list[dict],
    ids: list[str],
    all_piura: bool,
    limit: int | None,
) -> tuple[list[dict], str]:
    if ids and not all_piura:
        catalogo = {str(e.get("id")): e for e in stations}
        faltan = [sid for sid in ids if sid not in catalogo]
        if faltan:
            raise SystemExit(
                "la selección fija contiene IDs que no están en el catálogo de "
                f"Piura: {', '.join(faltan)}"
            )
        seleccionadas = [catalogo[sid] for sid in ids]
        regla = "lista fija de IDs (etl/senamhi_estaciones_piura.txt)"
    else:
        seleccionadas = list(stations)
        regla = "todas las estaciones del departamento de Piura"
    if limit is not None:
        seleccionadas = seleccionadas[:limit]
        regla += f"; limitadas a {limit}"
    return seleccionadas, regla


def download(raw_dir: Path, force: bool, limit: int | None, args) -> int:
    ensure_not_public(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(
        {"User-Agent": USER_AGENT, "Accept": "application/json"}
    )

    stations_path = raw_dir / "stations.json"
    files: dict[str, dict] = {}
    errores: list[dict] = []

    if stations_path.exists() and not (force or args.refresh_catalog):
        content = stations_path.read_bytes()
        catalog = parse_payload(content, str(stations_path))
        files["stations.json"] = {
            "sha256": sha256_bytes(content),
            "bytes": len(content),
            "http_status": None,
            "content_type": "application/json",
            "fetched_at": None,
            "origen": "caché local",
        }
        print(f"  usando catálogo existente {stations_path}")
    else:
        print("  descargando catálogo de estaciones…")
        try:
            content, meta = fetch(
                session, f"{API}/stations", args.timeout, args.retries
            )
            catalog = parse_payload(content, f"{API}/stations")
            atomic_write(stations_path, content)
            files["stations.json"] = {
                "sha256": sha256_bytes(content),
                "bytes": len(content),
                **meta,
            }
            print(f"  guardado {stations_path}")
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc

    stations = piura_stations(catalog)
    if not stations:
        raise SystemExit("no se encontraron estaciones de Piura en el catálogo")
    ids = read_ids(args.ids_file)
    seleccionadas, regla = choose_stations(
        stations, ids, args.all_piura, limit
    )

    series_dir = raw_dir / "series"
    series_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "fuente": "senamhi-historico-estaciones",
        "api": API,
        "consultado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seleccion": {
            "departamento": "PIURA",
            "regla": regla,
            "archivo": str(args.ids_file) if args.ids_file and args.ids_file.exists() else None,
            "ids": [str(e["id"]) for e in seleccionadas],
            "estaciones_piura_en_catalogo": len(stations),
        },
        "estaciones": [],
        "archivos": files,
        "errores": errores,
        "licencia": (
            "dato público; uso con atribución según términos de SENAMHI; "
            "sin licencia abierta; redistribución y derivados por confirmar"
        ),
        "publicado": False,
    }

    for i, estacion in enumerate(seleccionadas, start=1):
        sid = str(estacion["id"])
        destino = series_dir / f"{sid}.json"
        rel = f"series/{sid}.json"
        meta = {
            "http_status": None,
            "content_type": "application/json",
            "fetched_at": None,
            "origen": "caché local",
        }
        try:
            if destino.exists() and not force:
                content = destino.read_bytes()
                parse_payload(content, str(destino))
                print(f"  {i:02d}/{len(seleccionadas)} {sid} {estacion.get('name')}: ya existe")
            else:
                print(f"  {i:02d}/{len(seleccionadas)} {sid} {estacion.get('name')}: descargando…")
                content, meta = fetch(
                    session,
                    f"{API}/stations/{sid}/series",
                    args.timeout,
                    args.retries,
                )
                atomic_write(destino, content)
                print(f"    {destino.name} ({len(content) / 1e6:.1f} MB)")
        except RuntimeError as exc:
            errores.append({"id": sid, "error": str(exc)})
            print(f"    ERROR: {exc}")
            if destino.exists():
                content = destino.read_bytes()
                meta["origen"] = "caché local conservada tras error"
            else:
                continue

        item = {
            "id": sid,
            "name": estacion.get("name"),
            "provinceName": estacion.get("provinceName"),
            "districtName": estacion.get("districtName"),
            "latitude": estacion.get("latitude"),
            "longitude": estacion.get("longitude"),
            "altitude": estacion.get("altitude"),
            "file": rel,
            "sha256": sha256_bytes(content),
            "bytes": len(content),
            **meta,
            "id_en_respuesta": False,
        }
        manifest["estaciones"].append(item)
        files[rel] = {
            "sha256": item["sha256"],
            "bytes": item["bytes"],
            "http_status": meta.get("http_status"),
            "content_type": meta.get("content_type"),
            "fetched_at": meta.get("fetched_at"),
            "origen": meta.get("origen"),
        }
        if args.delay:
            time.sleep(args.delay)

    manifest_path = raw_dir / "manifest.json"
    atomic_write(
        manifest_path,
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    print(f"\nlisto: {len(manifest['estaciones'])} estaciones en {raw_dir}")
    if errores:
        print(f"  {len(errores)} error(es); ver {manifest_path}")
        return 1
    print("siguiente: python3 etl/build_senamhi_historico.py")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="volver a descargar")
    parser.add_argument(
        "--refresh-catalog", action="store_true", help="volver a descargar el catálogo"
    )
    parser.add_argument("--limit", type=int, default=None, help="descargar solo N estaciones")
    parser.add_argument(
        "--ids-file",
        type=Path,
        default=SELECTION_DEFAULT,
        help="lista fija de IDs (por defecto etl/senamhi_estaciones_piura.txt)",
    )
    parser.add_argument(
        "--all-piura",
        action="store_true",
        help="ignorar la lista fija y usar todas las estaciones de Piura",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DEFAULT,
        help="directorio de salida (por defecto data/raw/senamhi)",
    )
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.3)
    args = parser.parse_args()
    print("SENAMHI · series históricas por estación")
    return download(args.raw_dir, args.force, args.limit, args)


if __name__ == "__main__":
    sys.exit(main())
