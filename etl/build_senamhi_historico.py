#!/usr/bin/env python3
"""Aplana las series históricas de SENAMHI en una tabla revisable.

Entrada:  data/raw/senamhi/stations.json y data/raw/senamhi/series/*.json
Salida:   data/processed/senamhi/estaciones_piura.csv
          data/processed/senamhi/metadata.json

No publica en web/public: la licencia de reutilización no está confirmada.
Conserva los nulos: no interpola, no rellena y no suaviza.

Uso:
    python3 etl/build_senamhi_historico.py
    python3 etl/build_senamhi_historico.py --raw-dir /tmp/senamhi --out-dir /tmp/out
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DEFAULT = ROOT / "data" / "raw" / "senamhi"
OUT_DEFAULT = ROOT / "data" / "processed" / "senamhi"

COLUMNS = [
    "station_id",
    "station_name",
    "province",
    "district",
    "latitude",
    "longitude",
    "altitude_m",
    "date",
    "precipitation_mm",
    "temperature_max_c",
    "temperature_min_c",
]


def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"falta {path}; ejecuta primero download_senamhi_historico.py")
    return json.loads(path.read_text(encoding="utf-8"))


def piura_stations(payload: dict) -> list[dict]:
    estaciones = payload.get("data") or []
    return sorted(
        [
            e
            for e in estaciones
            if str(e.get("departmentName", "")).strip().upper() == "PIURA"
        ],
        key=lambda e: str(e.get("id", "")),
    )


def _number(value: object, field: str, sid: str, fecha: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{sid} {fecha}: {field} no es numérico: {value!r}")
    return float(value)


def flatten_series(station: dict, payload: dict) -> list[dict]:
    sid = str(station.get("id", ""))
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError(f"{sid}: la serie no trae una lista 'data'")

    salida: list[dict] = []
    vistas: set[str] = set()
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError(f"{sid}: fila de serie inválida")
        fecha = item.get("date")
        if not isinstance(fecha, str):
            raise ValueError(f"{sid}: fila sin fecha")
        try:
            date.fromisoformat(fecha)
        except ValueError as exc:
            raise ValueError(f"{sid}: fecha inválida {fecha!r}") from exc
        if fecha in vistas:
            raise ValueError(f"{sid}: fecha duplicada {fecha}")
        vistas.add(fecha)

        precipitacion = _number(item.get("precipitation"), "precipitation", sid, fecha)
        if precipitacion is not None and precipitacion < 0:
            raise ValueError(f"{sid} {fecha}: precipitación negativa {precipitacion}")
        tmax = _number(item.get("maximumTemperature"), "maximumTemperature", sid, fecha)
        tmin = _number(item.get("minimumTemperature"), "minimumTemperature", sid, fecha)

        salida.append(
            {
                "station_id": sid,
                "station_name": station.get("name") or "",
                "province": station.get("provinceName") or "",
                "district": station.get("districtName") or "",
                "latitude": station.get("latitude"),
                "longitude": station.get("longitude"),
                "altitude_m": station.get("altitude"),
                "date": fecha,
                "precipitation_mm": precipitacion,
                "temperature_max_c": tmax,
                "temperature_min_c": tmin,
            }
        )
    return sorted(salida, key=lambda r: (r["station_id"], r["date"]))


def _fmt(value: object, decimals: int = 3) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.{decimals}f}".rstrip("0").rstrip(".")
    return str(value)


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "station_id": row["station_id"],
                    "station_name": row["station_name"],
                    "province": row["province"],
                    "district": row["district"],
                    "latitude": _fmt(row["latitude"], 6),
                    "longitude": _fmt(row["longitude"], 6),
                    "altitude_m": _fmt(row["altitude_m"], 1),
                    "date": row["date"],
                    "precipitation_mm": _fmt(row["precipitation_mm"]),
                    "temperature_max_c": _fmt(row["temperature_max_c"]),
                    "temperature_min_c": _fmt(row["temperature_min_c"]),
                }
            )


def build(raw_dir: Path, out_dir: Path) -> dict:
    stations_payload = load_json(raw_dir / "stations.json")
    estaciones = piura_stations(stations_payload)
    if not estaciones:
        raise SystemExit("el catálogo no contiene estaciones de Piura")

    # Si existe un manifiesto de descarga, se respeta: permite ejecutar el
    # download con --limit y construir solo esas estaciones.
    manifest_path = raw_dir / "manifest.json"
    seleccionadas: set[str] | None = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        seleccionadas = {str(e["id"]) for e in manifest.get("estaciones", [])}
        estaciones = [e for e in estaciones if str(e.get("id")) in seleccionadas]

    rows: list[dict] = []
    con_datos = 0
    sin_datos: list[str] = []
    sin_serie: list[str] = []
    for estacion in estaciones:
        sid = str(estacion.get("id", ""))
        serie_path = raw_dir / "series" / f"{sid}.json"
        if not serie_path.exists():
            sin_serie.append(sid)
            continue
        serie = load_json(serie_path)
        estacion_rows = flatten_series(estacion, serie)
        if estacion_rows:
            con_datos += 1
            rows.extend(estacion_rows)
        else:
            sin_datos.append(sid)

    if not rows:
        faltan = ", ".join(sin_serie) if sin_serie else "sin filas"
        raise SystemExit(f"no hay filas para escribir ({faltan})")
    rows.sort(key=lambda r: (r["station_id"], r["date"]))

    csv_path = out_dir / "estaciones_piura.csv"
    write_csv(rows, csv_path)
    fechas = [r["date"] for r in rows]
    metadata = {
        "fuente": "senamhi-historico-estaciones",
        "url": "https://servicios.senamhi.gob.pe/api/researchers/historical-download/stations",
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "estaciones_catalogo": len(estaciones),
        "estaciones_con_datos": con_datos,
        "estaciones_sin_datos": sin_datos,
        "estaciones_sin_serie": sin_serie,
        "filas": len(rows),
        "periodo": {"desde": min(fechas), "hasta": max(fechas)},
        "variables": {
            "precipitation_mm": "precipitación diaria (mm)",
            "temperature_max_c": "temperatura máxima diaria (°C)",
            "temperature_min_c": "temperatura mínima diaria (°C)",
        },
        "metodo": "descarga JSON por estación; tabla plana sin interpolación ni relleno",
        "licencia": "dato público; términos de reutilización por confirmar",
        "publicado": False,
        "limitaciones": [
            "No incluye caudales.",
            "No cubre 2017 ni 2023: la cobertura termina en 2014/2015.",
            "Los nulos se conservan; no se imputan.",
            "No se publica en web/public hasta confirmar términos.",
        ],
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"listo: {len(rows)} filas, {con_datos} estaciones con datos, "
        f"{metadata['periodo']['desde']}–{metadata['periodo']['hasta']}"
    )
    print(f"  {csv_path}")
    print(f"  {out_dir / 'metadata.json'}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DEFAULT)
    parser.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    print("SENAMHI · tabla plana de estaciones de Piura")
    build(args.raw_dir, args.out_dir)


if __name__ == "__main__":
    main()
