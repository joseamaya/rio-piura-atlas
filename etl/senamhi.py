#!/usr/bin/env python3
"""Utilidades compartidas para las series históricas de SENAMHI.

El módulo no descarga nada: separa la lectura del catálogo, la validación de
esquema, el control de calidad y el cálculo de cobertura para que el download y
el build puedan probarse sin red y sin depender del formato exacto de la API.

Principio: el dato original no se corrige. Los valores negativos, las
temperaturas incoherentes y los extremos se conservan y se marcan; los nulos se
conservan. Un error estructural (fecha inválida, duplicado o campo ausente) se
informa y detiene esa estación, pero no se rellena ni se inventa.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

API = "https://servicios.senamhi.gob.pe/api/researchers/historical-download"
RAW_DEFAULT = Path(__file__).resolve().parents[1] / "data" / "raw" / "senamhi"
OUT_DEFAULT = Path(__file__).resolve().parents[1] / "data" / "processed" / "senamhi"
SELECTION_DEFAULT = Path(__file__).resolve().parent / "senamhi_estaciones_piura.txt"

EXPECTED_FIELDS = (
    "date",
    "precipitation",
    "maximumTemperature",
    "minimumTemperature",
)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

DAILY_COLUMNS = [
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
    "qc_flags",
    "qc_precip_negativa",
    "qc_tmax_menor_tmin",
    "qc_tmax_igual_tmin",
    "qc_precip_extrema",
    "qc_temp_sospechosa",
]

# Compatibilidad con la API pública del ETL anterior.
COLUMNS = DAILY_COLUMNS

CATALOG_COLUMNS = [
    "station_id",
    "station_name",
    "department",
    "province",
    "district",
    "latitude",
    "longitude",
    "altitude_m",
    "seleccionada_piura",
]

INVENTORY_COLUMNS = [
    "station_id",
    "station_name",
    "province",
    "district",
    "latitude",
    "longitude",
    "altitude_m",
    "file",
    "sha256",
    "bytes",
    "http_status",
    "content_type",
    "fetched_at",
    "coordenada_valida",
]

COVERAGE_COLUMNS = [
    "station_id",
    "station_name",
    "province",
    "district",
    "latitude",
    "longitude",
    "altitude_m",
    "archivo",
    "sha256",
    "bytes",
    "estado",
    "error",
    "first_date",
    "last_date",
    "observed_days",
    "expected_days",
    "missing_days",
    "coverage_pct",
    "n_precip",
    "pct_precip_null",
    "n_tmax",
    "pct_tmax_null",
    "n_tmin",
    "pct_tmin_null",
    "first_precip_date",
    "last_precip_date",
    "first_tmax_date",
    "last_tmax_date",
    "first_tmin_date",
    "last_tmin_date",
    "n_precip_negativa",
    "n_tmax_menor_tmin",
    "n_tmax_igual_tmin",
    "n_precip_extrema",
    "n_temp_sospechosa",
    "max_precip_mm",
    "max_precip_date",
    "n_precip_gt_100",
    "n_gaps",
    "longest_gap_days",
    "relacion_cuenca",
    "distancia_borde_km",
    "subcuenca_mas_cercana",
    "clasificacion",
    "nota_geografica",
    "coordenada_valida",
]

GAP_COLUMNS = ["station_id", "gap_start", "gap_end", "days"]


class SchemaError(ValueError):
    """La respuesta no tiene la forma esperada."""


class SeriesQualityError(ValueError):
    """La serie tiene un problema que impide tratarla sin ambigüedad."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"falta {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaError(f"{path}: JSON inválido ({exc})") from exc
    if not isinstance(payload, dict):
        raise SchemaError(f"{path}: la raíz no es un objeto")
    return payload


def read_selection(path: Path = SELECTION_DEFAULT) -> list[str]:
    if not path.exists():
        return []
    ids = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            ids.append(line)
    if len(ids) != len(set(ids)):
        raise SchemaError(f"{path}: IDs duplicados en la selección")
    return ids


def piura_stations(payload: dict) -> list[dict]:
    estaciones = payload.get("data") or []
    if not isinstance(estaciones, list):
        raise SchemaError("el catálogo no trae una lista 'data'")
    return sorted(
        [
            e
            for e in estaciones
            if isinstance(e, dict)
            and str(e.get("departmentName", "")).strip().upper() == "PIURA"
        ],
        key=lambda e: str(e.get("id", "")),
    )


def catalog_rows(payload: dict, selected_ids: Iterable[str] = ()) -> list[dict]:
    estaciones = payload.get("data") or []
    if not isinstance(estaciones, list):
        raise SchemaError("el catálogo no trae una lista 'data'")
    selected = {str(s) for s in selected_ids}
    rows = []
    for e in sorted(estaciones, key=lambda x: str(x.get("id", ""))):
        if not isinstance(e, dict):
            continue
        sid = str(e.get("id", ""))
        rows.append(
            {
                "station_id": sid,
                "station_name": e.get("name") or "",
                "department": e.get("departmentName") or "",
                "province": e.get("provinceName") or "",
                "district": e.get("districtName") or "",
                "latitude": e.get("latitude"),
                "longitude": e.get("longitude"),
                "altitude_m": e.get("altitude"),
                "seleccionada_piura": 1 if sid in selected else 0,
            }
        )
    return rows


def station_qc(station: dict) -> dict:
    """Valida los metadatos de la estación sin descartarla."""
    lat = station.get("latitude")
    lon = station.get("longitude")
    alt = station.get("altitude")
    numbers = all(
        isinstance(v, (int, float)) and not isinstance(v, bool)
        for v in (lat, lon)
    )
    valid = bool(
        numbers
        and -90 <= float(lat) <= 90
        and -180 <= float(lon) <= 180
        and not (float(lat) == 0 and float(lon) == 0)
    )
    if valid and alt is not None:
        if not isinstance(alt, (int, float)) or isinstance(alt, bool):
            valid = False
        elif not -100 <= float(alt) <= 7000:
            valid = False
    return {"coordenada_valida": 1 if valid else 0}


def _number(value: object, field: str, sid: str, fecha: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaError(f"{sid} {fecha}: {field} no es numérico: {value!r}")
    return float(value)


def _qc_flags(
    precipitacion: float | None,
    tmax: float | None,
    tmin: float | None,
) -> list[str]:
    flags: list[str] = []
    if precipitacion is not None and precipitacion < 0:
        flags.append("precip_negativa")
    if tmax is not None and tmin is not None and tmax < tmin:
        flags.append("tmax_menor_tmin")
    if tmax is not None and tmin is not None and tmax == tmin:
        flags.append("tmax_igual_tmin")
    # 100 mm/día es un umbral de lluvia torrencial; no implica error. Se marca
    # para revisión y no se elimina.
    if precipitacion is not None and precipitacion > 100:
        flags.append("precip_extrema")
    if (
        (tmax is not None and (tmax > 50 or tmax < -10))
        or (tmin is not None and (tmin > 40 or tmin < -20))
        or (
            tmax is not None
            and tmin is not None
            and (tmax - tmin) > 30
        )
    ):
        flags.append("temp_sospechosa")
    return flags


def flatten_series(station: dict, payload: dict) -> list[dict]:
    """Aplana una serie y aplica controles de calidad.

    Los nulos se conservan. Los valores negativos, las temperaturas
    incoherentes y los extremos se conservan con banderas. Una fecha inválida,
    un duplicado o un campo ausente se consideran errores estructurales.
    """
    sid = str(station.get("id", ""))
    if payload.get("status") is False:
        raise SchemaError(f"{sid}: la API devolvió status=false")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise SchemaError(f"{sid}: la serie no trae una lista 'data'")

    salida: list[dict] = []
    vistas: set[str] = set()
    for item in rows:
        if not isinstance(item, dict):
            raise SchemaError(f"{sid}: fila de serie inválida")
        faltan = [campo for campo in EXPECTED_FIELDS if campo not in item]
        if faltan:
            raise SchemaError(
                f"{sid}: fila sin los campos {', '.join(faltan)}"
            )
        fecha = item.get("date")
        if not isinstance(fecha, str) or not DATE_RE.match(fecha):
            raise SeriesQualityError(f"{sid}: fecha inválida {fecha!r}")
        try:
            date.fromisoformat(fecha)
        except ValueError as exc:
            raise SeriesQualityError(f"{sid}: fecha inválida {fecha!r}") from exc
        if fecha in vistas:
            raise SeriesQualityError(f"{sid}: fecha duplicada {fecha}")
        vistas.add(fecha)

        precipitacion = _number(
            item.get("precipitation"), "precipitation", sid, fecha
        )
        tmax = _number(
            item.get("maximumTemperature"), "maximumTemperature", sid, fecha
        )
        tmin = _number(
            item.get("minimumTemperature"), "minimumTemperature", sid, fecha
        )
        flags = _qc_flags(precipitacion, tmax, tmin)

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
                "qc_flags": ";".join(flags),
                "qc_precip_negativa": int("precip_negativa" in flags),
                "qc_tmax_menor_tmin": int("tmax_menor_tmin" in flags),
                "qc_tmax_igual_tmin": int("tmax_igual_tmin" in flags),
                "qc_precip_extrema": int("precip_extrema" in flags),
                "qc_temp_sospechosa": int("temp_sospechosa" in flags),
            }
        )
    return sorted(salida, key=lambda r: (r["station_id"], r["date"]))


def _pct(part: int, total: int) -> float:
    return round(100.0 * part / total, 2) if total else 0.0


def coverage_stats(rows: list[dict]) -> dict:
    """Calcula cobertura temporal, nulos, extremos y huecos contiguos."""
    if not rows:
        return {
            "first_date": "",
            "last_date": "",
            "observed_days": 0,
            "expected_days": 0,
            "missing_days": 0,
            "coverage_pct": 0.0,
            "n_precip": 0,
            "pct_precip_null": 0.0,
            "n_tmax": 0,
            "pct_tmax_null": 0.0,
            "n_tmin": 0,
            "pct_tmin_null": 0.0,
            "first_precip_date": "",
            "last_precip_date": "",
            "first_tmax_date": "",
            "last_tmax_date": "",
            "first_tmin_date": "",
            "last_tmin_date": "",
            "n_precip_negativa": 0,
            "n_tmax_menor_tmin": 0,
            "n_tmax_igual_tmin": 0,
            "n_precip_extrema": 0,
            "n_temp_sospechosa": 0,
            "max_precip_mm": None,
            "max_precip_date": "",
            "n_precip_gt_100": 0,
            "n_gaps": 0,
            "longest_gap_days": 0,
            "gaps": [],
            "estado": "sin_datos",
        }

    fechas = [date.fromisoformat(r["date"]) for r in rows]
    first, last = min(fechas), max(fechas)
    expected = (last - first).days + 1
    observed = len(rows)
    presentes = set(fechas)
    gaps: list[tuple[str, str, int]] = []
    cursor: date | None = None
    for offset in range(expected):
        dia = first + timedelta(days=offset)
        if dia not in presentes:
            if cursor is None:
                cursor = dia
            end = dia
        else:
            if cursor is not None:
                gaps.append(
                    (cursor.isoformat(), end.isoformat(), (end - cursor).days + 1)
                )
                cursor = None
    if cursor is not None:
        gaps.append((cursor.isoformat(), end.isoformat(), (end - cursor).days + 1))

    def nonnull(field: str) -> list[dict]:
        return [r for r in rows if r.get(field) is not None]

    precip = nonnull("precipitation_mm")
    tmax = nonnull("temperature_max_c")
    tmin = nonnull("temperature_min_c")
    max_row = max(
        precip,
        key=lambda r: r["precipitation_mm"],
        default=None,
    )
    n_tmax = len(tmax)
    n_tmin = len(tmin)
    if n_tmax == 0 and n_tmin == 0:
        estado = "sin_temperatura"
    elif (
        n_tmax / observed < 0.5
        or n_tmin / observed < 0.5
    ):
        estado = "temperatura_parcial"
    else:
        estado = "ok"

    return {
        "first_date": first.isoformat(),
        "last_date": last.isoformat(),
        "observed_days": observed,
        "expected_days": expected,
        "missing_days": expected - observed,
        "coverage_pct": round(100.0 * observed / expected, 2) if expected else 0.0,
        "n_precip": len(precip),
        "pct_precip_null": _pct(observed - len(precip), observed),
        "n_tmax": n_tmax,
        "pct_tmax_null": _pct(observed - n_tmax, observed),
        "n_tmin": n_tmin,
        "pct_tmin_null": _pct(observed - n_tmin, observed),
        "first_precip_date": precip[0]["date"] if precip else "",
        "last_precip_date": precip[-1]["date"] if precip else "",
        "first_tmax_date": tmax[0]["date"] if tmax else "",
        "last_tmax_date": tmax[-1]["date"] if tmax else "",
        "first_tmin_date": tmin[0]["date"] if tmin else "",
        "last_tmin_date": tmin[-1]["date"] if tmin else "",
        "n_precip_negativa": sum(r["qc_precip_negativa"] for r in rows),
        "n_tmax_menor_tmin": sum(r["qc_tmax_menor_tmin"] for r in rows),
        "n_tmax_igual_tmin": sum(r["qc_tmax_igual_tmin"] for r in rows),
        "n_precip_extrema": sum(r["qc_precip_extrema"] for r in rows),
        "n_temp_sospechosa": sum(r["qc_temp_sospechosa"] for r in rows),
        "max_precip_mm": max_row["precipitation_mm"] if max_row else None,
        "max_precip_date": max_row["date"] if max_row else "",
        "n_precip_gt_100": sum(
            1 for r in rows if r.get("precipitation_mm") is not None
            and r["precipitation_mm"] > 100
        ),
        "n_gaps": len(gaps),
        "longest_gap_days": max((g[2] for g in gaps), default=0),
        "gaps": gaps,
        "estado": estado,
    }


DECIMALS = {
    "latitude": 6,
    "longitude": 6,
    "altitude_m": 1,
    "precipitation_mm": 3,
    "temperature_max_c": 3,
    "temperature_min_c": 3,
    "max_precip_mm": 3,
    "distancia_borde_km": 2,
    "coverage_pct": 2,
    "pct_precip_null": 2,
    "pct_tmax_null": 2,
    "pct_tmin_null": 2,
}


def _fmt_value(key: str, value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        decimals = DECIMALS.get(key, 3)
        return f"{value:.{decimals}f}".rstrip("0").rstrip(".")
    return str(value)


def write_csv(
    rows: Iterable[dict],
    path: Path,
    fieldnames: list[str] | None = None,
) -> None:
    fieldnames = fieldnames or DAILY_COLUMNS
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {key: _fmt_value(key, row.get(key)) for key in fieldnames}
            )


def write_daily_csv(rows: list[dict], path: Path) -> None:
    write_csv(rows, path, DAILY_COLUMNS)
