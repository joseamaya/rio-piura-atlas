#!/usr/bin/env python3
"""Aplana y audita las series históricas de SENAMHI.

Entrada:  data/raw/senamhi/stations.json, manifest.json y series/*.json
Salida:   data/processed/senamhi/
          ├── estaciones_piura.csv      tabla diaria con banderas de calidad
          ├── catalogo_estaciones.csv   catálogo completo de la API
          ├── inventario_estaciones.csv 20 estaciones seleccionadas
          ├── cobertura_estaciones.csv  cobertura y nulos por estación
          ├── huecos_estaciones.csv     intervalos de fechas faltantes
          ├── metadata.json
          └── hashes.sha256

No publica en web/public: la licencia de reutilización no está confirmada.
Conserva los nulos: no interpola, no rellena y no suaviza.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from etl.senamhi import (
        CATALOG_COLUMNS,
        COVERAGE_COLUMNS,
        DAILY_COLUMNS,
        GAP_COLUMNS,
        INVENTORY_COLUMNS,
        SchemaError,
        SeriesQualityError,
        catalog_rows,
        coverage_stats,
        flatten_series,
        load_json,
        piura_stations,
        sha256_file,
        station_qc,
        write_csv,
        write_daily_csv,
    )
    from etl.senamhi_geo import classify_station
except ModuleNotFoundError:  # ejecución directa
    from senamhi import (  # type: ignore
        CATALOG_COLUMNS,
        COVERAGE_COLUMNS,
        DAILY_COLUMNS,
        GAP_COLUMNS,
        INVENTORY_COLUMNS,
        SchemaError,
        SeriesQualityError,
        catalog_rows,
        coverage_stats,
        flatten_series,
        load_json,
        piura_stations,
        sha256_file,
        station_qc,
        write_csv,
        write_daily_csv,
    )
    from senamhi_geo import classify_station  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
RAW_DEFAULT = ROOT / "data" / "raw" / "senamhi"
OUT_DEFAULT = ROOT / "data" / "processed" / "senamhi"
PUBLIC = ROOT / "web" / "public"

# Compatibilidad con la API pública del ETL anterior.
COLUMNS = DAILY_COLUMNS


def ensure_not_public(path: Path) -> None:
    resolved = path.resolve()
    if resolved == PUBLIC or PUBLIC in resolved.parents:
        raise SystemExit(
            f"destino no permitido: {path}. Las series de SENAMHI no se publican "
            "hasta confirmar los términos."
        )


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _empty_coverage(station: dict, status: str, error: str = "") -> dict:
    qc = station_qc(station)
    return {
        "station_id": str(station.get("id", "")),
        "station_name": station.get("name") or "",
        "province": station.get("provinceName") or "",
        "district": station.get("districtName") or "",
        "latitude": station.get("latitude"),
        "longitude": station.get("longitude"),
        "altitude_m": station.get("altitude"),
        "archivo": "",
        "sha256": "",
        "bytes": "",
        "estado": status,
        "error": error,
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
        "relacion_cuenca": "",
        "distancia_borde_km": None,
        "subcuenca_mas_cercana": "",
        "clasificacion": "",
        "nota_geografica": "no se clasifica sin serie",
        "coordenada_valida": qc["coordenada_valida"],
    }


def build(raw_dir: Path, out_dir: Path) -> dict:
    ensure_not_public(out_dir)
    stations_payload = load_json(raw_dir / "stations.json")
    todas = piura_stations(stations_payload)
    if not todas:
        raise SystemExit("el catálogo no contiene estaciones de Piura")
    total_piura = len(todas)
    total_catalogo = len(stations_payload.get("data") or [])

    manifest_path = raw_dir / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seleccionadas_ids = [
        str(e.get("id"))
        for e in manifest.get("estaciones", [])
        if e.get("id") is not None
    ]
    if not seleccionadas_ids:
        # Compatibilidad con corridas antiguas sin manifiesto: se usan todas
        # las estaciones de Piura del catálogo. La lista fija se aplica en el
        # downloader y queda registrada en el manifiesto.
        estaciones = list(todas)
    else:
        catalogo = {str(e.get("id")): e for e in todas}
        faltan = [sid for sid in seleccionadas_ids if sid not in catalogo]
        if faltan:
            raise SystemExit(
                "la selección contiene IDs que no están en el catálogo de Piura: "
                + ", ".join(faltan)
            )
        estaciones = [catalogo[sid] for sid in seleccionadas_ids]

    files_manifest = manifest.get("archivos") or {}
    rows: list[dict] = []
    inventario: list[dict] = []
    cobertura: list[dict] = []
    huecos: list[dict] = []
    errores: list[str] = []
    sin_serie: list[str] = []
    sin_datos: list[str] = []
    con_datos = 0

    for estacion in estaciones:
        sid = str(estacion.get("id", ""))
        serie_path = raw_dir / "series" / f"{sid}.json"
        rel = f"series/{sid}.json"
        qc = station_qc(estacion)
        if not serie_path.exists():
            sin_serie.append(sid)
            errores.append(f"{sid}: falta {serie_path}")
            cobertura.append(_empty_coverage(estacion, "sin_serie", "archivo ausente"))
            continue

        content = serie_path.read_bytes()
        digest = sha256_file(serie_path)
        esperado = (files_manifest.get(rel) or {}).get("sha256")
        if esperado and esperado != digest:
            msg = f"{sid}: SHA-256 no coincide con el manifiesto"
            errores.append(msg)
            cobertura.append(_empty_coverage(estacion, "error", msg))
            continue

        try:
            serie = json.loads(content.decode("utf-8"))
            if not isinstance(serie, dict):
                raise SchemaError(f"{sid}: la raíz de la serie no es un objeto")
            estacion_rows = flatten_series(estacion, serie)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            msg = f"{sid}: JSON inválido ({exc})"
            errores.append(msg)
            cobertura.append(_empty_coverage(estacion, "error", msg))
            continue
        except (SchemaError, SeriesQualityError) as exc:
            msg = str(exc)
            errores.append(msg)
            estado = "sin_datos" if "no trae una lista 'data'" in msg else "error"
            if estado == "sin_datos":
                sin_datos.append(sid)
            cobertura.append(_empty_coverage(estacion, estado, msg))
            continue

        if not estacion_rows:
            sin_datos.append(sid)
            errores.append(f"{sid}: la serie no tiene filas")
            cobertura.append(_empty_coverage(estacion, "sin_datos", "serie vacía"))
            continue

        con_datos += 1
        rows.extend(estacion_rows)
        stats = coverage_stats(estacion_rows)
        geo = classify_station(
            estacion.get("longitude"),
            estacion.get("latitude"),
            str(estacion.get("departmentName") or ""),
        )
        cov = {
            "station_id": sid,
            "station_name": estacion.get("name") or "",
            "province": estacion.get("provinceName") or "",
            "district": estacion.get("districtName") or "",
            "latitude": estacion.get("latitude"),
            "longitude": estacion.get("longitude"),
            "altitude_m": estacion.get("altitude"),
            "archivo": rel,
            "sha256": digest,
            "bytes": len(content),
            "estado": stats["estado"],
            "error": "",
            **{k: v for k, v in stats.items() if k != "gaps"},
            **geo,
            "coordenada_valida": qc["coordenada_valida"],
        }
        cobertura.append(cov)
        for start, end, days in stats["gaps"]:
            huecos.append(
                {"station_id": sid, "gap_start": start, "gap_end": end, "days": days}
            )
        meta_file = files_manifest.get(rel) or {}
        inventario.append(
            {
                "station_id": sid,
                "station_name": estacion.get("name") or "",
                "province": estacion.get("provinceName") or "",
                "district": estacion.get("districtName") or "",
                "latitude": estacion.get("latitude"),
                "longitude": estacion.get("longitude"),
                "altitude_m": estacion.get("altitude"),
                "file": rel,
                "sha256": digest,
                "bytes": len(content),
                "http_status": meta_file.get("http_status"),
                "content_type": meta_file.get("content_type"),
                "fetched_at": meta_file.get("fetched_at"),
                "coordenada_valida": qc["coordenada_valida"],
            }
        )

    if not rows:
        faltan = ", ".join(sin_serie) if sin_serie else "sin filas"
        raise SystemExit(f"no hay filas para escribir ({faltan})")

    rows.sort(key=lambda r: (r["station_id"], r["date"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    daily_path = out_dir / "estaciones_piura.csv"
    write_daily_csv(rows, daily_path)
    write_csv(
        catalog_rows(stations_payload, seleccionadas_ids),
        out_dir / "catalogo_estaciones.csv",
        CATALOG_COLUMNS,
    )
    write_csv(
        sorted(inventario, key=lambda r: r["station_id"]),
        out_dir / "inventario_estaciones.csv",
        INVENTORY_COLUMNS,
    )
    write_csv(
        sorted(cobertura, key=lambda r: r["station_id"]),
        out_dir / "cobertura_estaciones.csv",
        COVERAGE_COLUMNS,
    )
    write_csv(
        sorted(huecos, key=lambda r: (r["station_id"], r["gap_start"])),
        out_dir / "huecos_estaciones.csv",
        GAP_COLUMNS,
    )

    fechas = [r["date"] for r in rows]
    periodo = {"desde": min(fechas), "hasta": max(fechas)}
    periodo_por_estacion = {
        cov["station_id"]: {
            "desde": cov["first_date"],
            "hasta": cov["last_date"],
            "filas": cov["observed_days"],
            "estado": cov["estado"],
        }
        for cov in cobertura
        if cov["observed_days"]
    }
    flags = {
        "precip_negativa": sum(r["qc_precip_negativa"] for r in rows),
        "tmax_menor_tmin": sum(r["qc_tmax_menor_tmin"] for r in rows),
        "tmax_igual_tmin": sum(r["qc_tmax_igual_tmin"] for r in rows),
        "precip_extrema": sum(r["qc_precip_extrema"] for r in rows),
        "temp_sospechosa": sum(r["qc_temp_sospechosa"] for r in rows),
    }
    catalog_hash = sha256_file(raw_dir / "stations.json")
    metadata = {
        "fuente": "senamhi-historico-estaciones",
        "url": f"https://servicios.senamhi.gob.pe/api/researchers/historical-download/stations",
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "consultado": manifest.get("consultado"),
        "estaciones_catalogo_total": total_piura,
        "estaciones_catalogo_completo": total_catalogo,
        "estaciones_seleccionadas": len(estaciones),
        "estaciones_con_datos": con_datos,
        "estaciones_sin_datos": sorted(sin_datos),
        "estaciones_sin_serie": sorted(sin_serie),
        "estaciones_con_error": len(errores) - len(sin_serie) - len(sin_datos),
        "errores": errores,
        "filas": len(rows),
        "periodo": periodo,
        "periodo_por_estacion": periodo_por_estacion,
        "variables": {
            "precipitation_mm": "precipitación diaria (mm)",
            "temperature_max_c": "temperatura máxima diaria (°C)",
            "temperature_min_c": "temperatura mínima diaria (°C)",
        },
        "calidad": {
            "filas_con_bandera": sum(1 for r in rows if r["qc_flags"]),
            "conteo_por_bandera": flags,
            "duplicados": 0,
            "fechas_invalidas": 0,
            "esquema_estable": True,
            "unidades": "asumidas según documentación de SENAMHI; la API no las declara en el JSON",
        },
        "metodo": (
            "descarga JSON cruda por estación; tabla plana sin interpolación ni "
            "relleno; banderas de calidad sin eliminación automática"
        ),
        "licencia": (
            "dato público; uso con atribución según términos de SENAMHI; "
            "sin licencia abierta; redistribución y derivados por confirmar"
        ),
        "publicado": False,
        "limitaciones": [
            "No incluye caudales.",
            "No cubre 2017 ni 2023: la cobertura termina en 2015-10-31.",
            "La envolvente 1961–2015 no implica cobertura completa por estación.",
            "Ocho estaciones no tienen temperatura; dos tienen temperatura parcial.",
            "Los nulos se conservan; no se imputan.",
            "No se publica en web/public hasta confirmar términos.",
        ],
        "manifiesto_crudo": str(manifest_path),
        "catalogo_sha256": catalog_hash,
        "seleccion": manifest.get("seleccion")
        or {
            "departamento": "PIURA",
            "regla": "lista fija o todas las de Piura",
            "ids": seleccionadas_ids,
        },
        "hashes_crudos": {
            rel: (files_manifest.get(rel) or {}).get("sha256")
            for rel in sorted(files_manifest)
        },
    }
    metadata_path = out_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    hashes = []
    for path in [raw_dir / "stations.json", raw_dir / "manifest.json"]:
        if path.exists():
            hashes.append((sha256_file(path), _relative(path, raw_dir)))
    for item in sorted(inventario, key=lambda r: r["station_id"]):
        hashes.append((item["sha256"], item["file"]))
    for name in (
        "estaciones_piura.csv",
        "catalogo_estaciones.csv",
        "inventario_estaciones.csv",
        "cobertura_estaciones.csv",
        "huecos_estaciones.csv",
        "metadata.json",
    ):
        path = out_dir / name
        if path.exists():
            hashes.append((sha256_file(path), name))
    (out_dir / "hashes.sha256").write_text(
        "".join(f"{digest}  {name}\n" for digest, name in hashes),
        encoding="utf-8",
    )

    print(
        f"listo: {len(rows)} filas, {con_datos} estaciones con datos, "
        f"{periodo['desde']}–{periodo['hasta']}"
    )
    print(f"  {daily_path}")
    print(f"  {out_dir / 'cobertura_estaciones.csv'}")
    print(f"  {metadata_path}")
    if errores:
        print(f"  {len(errores)} error(es) registrados")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DEFAULT)
    parser.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    print("SENAMHI · tabla plana y auditoría de estaciones de Piura")
    metadata = build(args.raw_dir, args.out_dir)
    return 1 if metadata.get("errores") else 0


if __name__ == "__main__":
    sys.exit(main())
