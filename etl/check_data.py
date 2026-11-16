#!/usr/bin/env python3
"""Valida la coherencia entre fuentes, capas y archivos publicados.

Se puede ejecutar sin el DEM y sin conexión. Pensado para CI y para antes de
publicar una versión del atlas.

Uso:
    python3 etl/check_data.py
"""

from __future__ import annotations

import json
import math
import re
import struct
import sys
from pathlib import Path

import yaml
from pyproj import Geod, Transformer
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import transform, unary_union
from shapely.validation import explain_validity, make_valid

try:  # Ejecución como módulo (`python -m etl.check_data`)
    from etl.topology import Tolerances, as_polygonal, audit_partition
except ModuleNotFoundError:  # Ejecución directa (`python etl/check_data.py`)
    from topology import Tolerances, as_polygonal, audit_partition

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources.yml"
RAW = ROOT / "data" / "raw"
WEB_DATA = ROOT / "web" / "public" / "data"
PROCESSED = ROOT / "data" / "processed"
MODEL = ROOT / "web" / "public" / "models" / "piura.glb"
DRACO = ROOT / "web" / "public" / "draco"
DRACO_FILES = ("draco_wasm_wrapper.js", "draco_decoder.wasm")

ESTADOS = {"disponible", "por_solicitar", "por_verificar"}
GRUPOS = {"Límites, relieve y red", "Agua", "Inundaciones y riesgo", "Estudios"}
CERTEZAS = {"medido", "derivado", "documentado", "interpretacion", "por_verificar"}
TIPOS = {"dataset", "documento", "prensa", "elaboracion_propia"}
CAMPOS = [
    "id",
    "titulo",
    "institucion",
    "url",
    "fecha",
    "escala",
    "licencia",
    "estado",
    "metodo",
    "grupo",
    "certeza",
    "tipo",
]

# Áreas y nombres de control. La cuenca se mide con Geod (WGS84); ANA publica
# Shape_Area en EPSG:32718, que no es la zona del polígono.
BASIN_AREA_TOLERANCE = 0.005  # 0,5 %
TOPOLOGY_TOLERANCES = Tolerances()
RIVER_TOLERANCE_DEG = 0.001   # ~100 m; el redondeo a 5 decimales deja <2 m
PROFILE_STEP_TOLERANCE = 0.90
POECHOS = (-80.5036, -4.6686)
CURUMUY = (-80.6302, -5.0283)
FECHA_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])(-\d{2})?$")
CONSULTA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOPOLOGY_SEEN: set[tuple] = set()

GEOD = Geod(ellps="WGS84")
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32717", always_xy=True)

errores: list[str] = []
avisos: list[str] = []


def error(msg: str) -> None:
    errores.append(msg)


def aviso(msg: str) -> None:
    avisos.append(msg)


def add_findings(findings, prefix: str) -> None:
    """Agrega hallazgos sin duplicar los que ya vienen de limits.json."""
    for finding in findings:
        key = (
            finding.kind,
            finding.severity,
            finding.names,
            round(finding.area_km2, 4),
        )
        if key in TOPOLOGY_SEEN:
            continue
        TOPOLOGY_SEEN.add(key)
        message = finding.message(prefix)
        if finding.severity == "error":
            error(message)
        else:
            aviso(message)


def cargar_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        error(f"falta {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        error(f"JSON inválido en {path.relative_to(ROOT)}: {exc}")
    return None


def geom_of(feature: dict):
    return shape(feature["geometry"])


def geodesic_km2(geom) -> float:
    return abs(GEOD.geometry_area_perimeter(make_valid(geom))[0]) / 1e6


def utm_km2(geom) -> float:
    return transform(TO_UTM.transform, make_valid(geom)).area / 1e6


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(h))


def check_sources():
    if not SOURCES.exists():
        error("falta data/sources.yml")
        return {}
    data = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    fuentes = data.get("fuentes") or []
    if not fuentes:
        error("data/sources.yml no tiene fuentes")
        return {}

    ids: dict[str, dict] = {}
    for i, fuente in enumerate(fuentes, start=1):
        if not isinstance(fuente, dict):
            error(f"fuente #{i} no es un objeto")
            continue
        for campo in CAMPOS:
            if campo not in fuente:
                error(f"fuente {fuente.get('id', f'#{i}')}: falta el campo '{campo}'")
        fid = fuente.get("id")
        if not fid:
            error(f"fuente #{i} sin id")
            continue
        if fid in ids:
            error(f"id duplicado en sources.yml: {fid}")
        ids[fid] = fuente
        if fuente.get("estado") not in ESTADOS:
            error(f"{fid}: estado inválido '{fuente.get('estado')}'")
        if fuente.get("grupo") not in GRUPOS:
            error(f"{fid}: grupo inválido '{fuente.get('grupo')}'")
        if not fuente.get("institucion"):
            error(f"{fid}: institución vacía")
        if not fuente.get("licencia"):
            error(f"{fid}: licencia vacía")
        if not fuente.get("metodo"):
            error(f"{fid}: método vacío")

        certeza = fuente.get("certeza")
        if certeza not in CERTEZAS:
            error(f"{fid}: certeza inválida '{certeza}'")
        tipo = fuente.get("tipo")
        if tipo not in TIPOS:
            error(f"{fid}: tipo inválido '{tipo}'")
        if certeza == "medido" and tipo == "elaboracion_propia":
            error(f"{fid}: una geometría propia no puede declararse 'medido'")
        if tipo == "elaboracion_propia" and "Río Piura Atlas" not in str(fuente.get("institucion")):
            error(f"{fid}: una fuente de elaboración propia debe atribuirse al atlas")

        fecha = fuente.get("fecha")
        if fecha is not None:
            if not isinstance(fecha, str):
                error(f"{fid}: fecha no es texto")
            elif not FECHA_RE.match(fecha):
                error(f"{fid}: fecha '{fecha}' no tiene formato YYYY-MM o YYYY-MM-DD")
            elif fecha.endswith("-01-01") and fuente.get("estado") != "disponible":
                aviso(f"{fid}: fecha {fecha} parece un marcador de posición")
        consultado = fuente.get("consultado")
        if consultado is not None:
            if not isinstance(consultado, str) or not CONSULTA_RE.match(consultado):
                error(f"{fid}: 'consultado' debe ser una fecha YYYY-MM-DD")
        if fuente.get("pagina") and not fuente.get("documento"):
            error(f"{fid}: declara página sin documento")

        url = fuente.get("url")
        if url is not None and not isinstance(url, str):
            error(f"{fid}: URL no es texto")
        if fuente.get("estado") == "disponible" and tipo != "elaboracion_propia":
            if not url and not fuente.get("documento"):
                error(f"{fid}: está disponible pero no tiene URL ni documento")
        generic = {
            "https://www.senamhi.gob.pe/",
            "https://enfen.gob.pe/",
            "https://www.openstreetmap.org/",
            "https://sigrid.cenepred.gob.pe/",
        }
        if (
            fuente.get("estado") == "disponible"
            and url in generic
            and not fuente.get("documento")
        ):
            aviso(f"{fid}: enlace genérico; falta el documento concreto")

    disponible = sum(1 for f in ids.values() if f.get("estado") == "disponible")
    print(f"fuentes: {len(ids)} · disponibles: {disponible}")
    return ids


def check_licencias(ids: dict[str, dict]):
    path = ROOT / "LICENSES" / "DATOS.md"
    if not path.exists():
        error("falta LICENSES/DATOS.md")
        return
    text = path.read_text(encoding="utf-8")
    for fid in ids:
        if fid in text:
            continue
        if fid.startswith("senamhi-") and "senamhi-*" in text:
            continue
        error(f"{fid}: falta en LICENSES/DATOS.md")
    print(f"licencias: {len(ids)} fuentes revisadas")


def check_page_sources(ids: dict[str, dict]):
    """Comprueba que los enlaces /fuentes#id de las páginas existan."""
    import re

    for path in sorted((ROOT / "web" / "src" / "pages").glob("*.astro")):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"/fuentes#([a-z0-9-]+)", text):
            fid = match.group(1)
            if fid not in ids:
                error(f"{path.name}: enlace a fuente desconocida '{fid}'")
    print("  páginas: enlaces a fuentes revisados")


def check_citation():
    path = ROOT / "CITATION.cff"
    if not path.exists():
        error("falta CITATION.cff")
        return
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for campo in ["cff-version", "title", "authors", "version", "date-released", "license"]:
        if campo not in data:
            error(f"CITATION.cff: falta '{campo}'")
    package = ROOT / "web" / "package.json"
    if package.exists():
        version = json.loads(package.read_text(encoding="utf-8")).get("version")
        if version and str(data.get("version")) != str(version):
            error(f"CITATION.cff: versión {data.get('version')} no coincide con web/package.json ({version})")
    print(f"citación: versión {data.get('version', '?')}")


def check_geometry(path: Path, geom: dict):
    gtype = geom.get("type")
    if gtype == "Point":
        coords = geom.get("coordinates") or []
        if len(coords) != 2 or not all(isinstance(v, (int, float)) for v in coords):
            error(f"{path.name}: punto sin dos coordenadas numéricas")
        return
    if gtype == "LineString":
        coords = geom.get("coordinates") or []
        if len(coords) < 2:
            error(f"{path.name}: línea con menos de 2 puntos")
            return
        line = LineString(coords)
        if not line.is_simple:
            error(f"{path.name}: línea autointersectada")
        if line.length == 0:
            error(f"{path.name}: línea de longitud cero")
        return
    if gtype in {"Polygon", "MultiPolygon"}:
        polygons = [geom.get("coordinates") or []] if gtype == "Polygon" else (geom.get("coordinates") or [])
        if not polygons:
            error(f"{path.name}: geometría sin polígonos")
            return
        for polygon in polygons:
            if not polygon:
                error(f"{path.name}: polígono vacío")
                continue
            ring = polygon[0]
            if len(ring) < 4 or ring[0] != ring[-1]:
                error(f"{path.name}: anillo no cerrado o con menos de 4 puntos")
            for hole in polygon[1:]:
                if len(hole) < 4 or hole[0] != hole[-1]:
                    error(f"{path.name}: hueco no cerrado o con menos de 4 puntos")
        geom_obj = shape(geom)
        if not geom_obj.is_valid:
            error(f"{path.name}: geometría inválida: {explain_validity(geom_obj)}")
        if geom_obj.is_empty:
            error(f"{path.name}: geometría vacía")
        return
    if gtype in {"MultiLineString", "GeometryCollection"}:
        for child in geom.get("geometries") or geom.get("coordinates") or []:
            if isinstance(child, dict):
                check_geometry(path, child)
        return
    error(f"{path.name}: geometría no soportada '{gtype}'")


def check_layer_fuentes(ids: dict[str, dict]):
    for path in sorted(WEB_DATA.glob("*.geojson")):
        data = cargar_json(path)
        if not data:
            continue
        for feature in data.get("features", []):
            props = feature.get("properties") or {}
            fuente = props.get("fuente")
            if not fuente:
                error(f"{path.name}: elemento sin 'fuente'")
            elif fuente not in ids:
                error(f"{path.name}: fuente desconocida '{fuente}'")
            elif ids[fuente].get("estado") != "disponible":
                error(f"{path.name}: usa la fuente '{fuente}', que no está disponible")
            if not feature.get("geometry"):
                error(f"{path.name}: feature sin geometría")
                continue
            check_geometry(path, feature["geometry"])
        print(f"  {path.name}: {len(data.get('features', []))} elementos")


def _geometry_from_record(record):
    """Reconstruye Polygon/MultiPolygon desde limits.json o subcuencas.geojson."""
    if not record:
        return None
    polygons = record.get("polygons")
    if polygons:
        parts = [
            Polygon(p["ring"], p.get("holes") or [])
            for p in polygons
            if p.get("ring")
        ]
    elif record.get("ring"):
        parts = [Polygon(record["ring"], record.get("holes") or [])]
    else:
        return None
    parts = [make_valid(p) for p in parts if p is not None]
    parts = [p for p in parts if not p.is_empty]
    if not parts:
        return None
    merged = parts[0] if len(parts) == 1 else unary_union(parts)
    return as_polygonal(merged)


def check_raw_limits():
    data = cargar_json(RAW / "limits.json")
    if not data:
        return None
    if not data.get("metodo"):
        error("limits.json: falta el método de construcción")
    basin = _geometry_from_record(data)
    if basin is None:
        error("limits.json: no se pudo reconstruir la cuenca")
        return data
    if not basin.is_valid:
        error(f"limits.json: cuenca inválida: {explain_validity(basin)}")

    subs = data.get("subbasins") or []
    if len(subs) != 9:
        error(f"limits.json: se esperaban 9 subcuencas; hay {len(subs)}")
    named = []
    for sub in subs:
        name = sub.get("name", "?")
        geom = _geometry_from_record(sub)
        if geom is None:
            error(f"limits.json: no se pudo reconstruir la subcuenca {name}")
            continue
        if not geom.is_valid:
            error(f"limits.json: subcuenca {name} inválida: {explain_validity(geom)}")
        if not sub.get("area_km2"):
            error(f"limits.json: subcuenca {name} sin área")
        named.append((name, geom))

    report = audit_partition(basin, named, TOPOLOGY_TOLERANCES)
    add_findings(report.findings, "limits.json")

    reconciliation = data.get("reconciliacion") or {}
    for field in (
        "crs_metrico",
        "tolerancia_simplificacion_deg",
        "caras",
        "slivers_asignados_km2",
        "solapamientos_eliminados_km2",
        "superficie_fuera_eliminada_km2",
        "metodo",
    ):
        if field not in reconciliation:
            error(f"limits.json: falta 'reconciliacion.{field}'")
    if reconciliation.get("crs_metrico") != "EPSG:32717":
        error("limits.json: la reconciliación debe declarar EPSG:32717")

    print(f"  limits: {report.summary()}")
    return data


def check_topology():
    cuenca_data = cargar_json(WEB_DATA / "cuenca.geojson")
    subs_data = cargar_json(WEB_DATA / "subcuencas.geojson")
    if not cuenca_data or not subs_data:
        return
    basin = as_polygonal(geom_of(cuenca_data["features"][0]))
    if basin is None or not basin.is_valid:
        detail = explain_validity(basin) if basin is not None else "geometría vacía"
        error(f"cuenca.geojson: inválida: {detail}")
        return
    declared = (cuenca_data["features"][0].get("properties") or {}).get("area_km2")
    measured = geodesic_km2(basin)
    if not isinstance(declared, (int, float)) or abs(measured - float(declared)) / measured > BASIN_AREA_TOLERANCE:
        error(f"cuenca.geojson: área declarada {declared} vs medida {measured:.2f} km²")

    named = []
    hole_notes: dict[str, str] = {}
    for feature in subs_data.get("features", []):
        geom = as_polygonal(geom_of(feature))
        props = feature.get("properties") or {}
        name = props.get("nombre", "?")
        if geom is None or not geom.is_valid:
            detail = explain_validity(geom) if geom is not None else "geometría vacía"
            error(f"subcuencas.geojson: {name} inválida: {detail}")
            continue
        declared_sub = props.get("area_km2")
        area = geodesic_km2(geom)
        if not isinstance(declared_sub, (int, float)) or abs(area - float(declared_sub)) / area > BASIN_AREA_TOLERANCE:
            error(f"subcuencas.geojson: {name} declara {declared_sub} km²; mide {area:.2f} km²")
        expected = "bajo-piura-derivado" if name == "Bajo Piura" else "ana-subcuencas"
        if props.get("fuente") != expected:
            error(
                f"subcuencas.geojson: {name} usa la fuente '{props.get('fuente')}'; "
                f"se esperaba '{expected}'"
            )
        if props.get("motivo_hueco"):
            hole_notes[name] = str(props["motivo_hueco"])
        named.append((name, geom))

    if not any(name == "Bajo Piura" for name, _ in named):
        error("subcuencas.geojson: falta la subcuenca derivada 'Bajo Piura'")

    report = audit_partition(basin, named, TOPOLOGY_TOLERANCES, hole_notes=hole_notes)
    add_findings(report.findings, "subcuencas.geojson")
    print(f"  topología: {report.summary()}")


def check_rivers():
    cuenca = cargar_json(WEB_DATA / "cuenca.geojson")
    riv = cargar_json(WEB_DATA / "red_hidrica.geojson")
    if not cuenca or not riv:
        return
    basin = make_valid(geom_of(cuenca["features"][0]))
    total = 0.0
    outside = 0.0
    bad = 0
    for feature in riv.get("features", []):
        geom = geom_of(feature)
        if geom.geom_type != "LineString":
            error("red_hidrica.geojson: se esperaban LineString")
            continue
        if not geom.is_valid or not geom.is_simple:
            error("red_hidrica.geojson: línea inválida o autointersectada")
        total += geom.length
        out = geom.difference(basin).length
        outside += out
        if out > RIVER_TOLERANCE_DEG:
            bad += 1
    if bad:
        error(f"red_hidrica.geojson: {bad} líneas fuera de la cuenca")
    share = outside / total if total else 0
    if share > 0.0001:
        error(f"red_hidrica.geojson: {share * 100:.3f} % de la red queda fuera de la cuenca")
    print(f"  red hídrica: {len(riv.get('features', []))} tramos · fuera {outside * 111:.0f} m")


def check_places():
    cuenca = cargar_json(WEB_DATA / "cuenca.geojson")
    lugares = cargar_json(WEB_DATA / "lugares.geojson")
    if not cuenca or not lugares:
        return
    basin = make_valid(geom_of(cuenca["features"][0]))
    for feature in lugares.get("features", []):
        props = feature.get("properties") or {}
        point = geom_of(feature)
        if point.geom_type != "Point":
            error("lugares.geojson: se esperaban puntos")
            continue
        inside = basin.covers(point)
        if not inside and not props.get("fuera_cuenca"):
            error(f"lugares.geojson: {props.get('nombre')} queda fuera de la cuenca sin marca")
    print(f"  lugares: {len(lugares.get('features', []))} puntos")


def check_flood():
    path = WEB_DATA / "flood_2017.geojson"
    data = cargar_json(path)
    if not data:
        return
    features = data.get("features") or []
    if not features:
        error("flood_2017.geojson: no tiene elementos")
        return
    total = 0.0
    for feature in features:
        props = feature.get("properties") or {}
        for campo in (
            "evento",
            "zona",
            "aoi",
            "fecha",
            "fecha_texto",
            "sensores",
            "observaciones",
            "clase",
            "area_km2",
            "area_original_km2",
            "fuente",
            "metodo",
            "cobertura",
            "esquematico",
            "advertencia",
        ):
            if campo not in props:
                error(f"flood_2017.geojson: falta '{campo}' en {props.get('aoi', '?')}")
        if props.get("fuente") != "copernicus-ems-emsr199":
            error(f"flood_2017.geojson: fuente inesperada '{props.get('fuente')}'")
        if props.get("clase") != "Flooded Area":
            error("flood_2017.geojson: la capa publicada debe ser solo 'Flooded Area'")
        if props.get("esquematico") is not False:
            error("flood_2017.geojson: la mancha no debe marcarse como esquemática")
        if "no es una mancha simultánea" not in str(props.get("metodo", "")):
            error("flood_2017.geojson: el método debe declarar que es una unión de fechas")
        if not props.get("advertencia"):
            error("flood_2017.geojson: falta la advertencia de metadatos del producto")

        observations = props.get("observaciones")
        if not isinstance(observations, list) or not observations:
            error(f"flood_2017.geojson: {props.get('aoi', '?')} no tiene observaciones por fecha")
            observations = []
        obs_areas = []
        obs_dates = []
        for obs in observations:
            if not isinstance(obs, dict):
                error("flood_2017.geojson: observación con formato inválido")
                continue
            for field in ("fecha", "sensor", "area_original_km2", "partes"):
                if field not in obs:
                    error(f"flood_2017.geojson: observación sin '{field}' en {props.get('aoi', '?')}")
            fecha = obs.get("fecha")
            if isinstance(fecha, str) and FECHA_RE.match(fecha):
                obs_dates.append(fecha)
            else:
                error(f"flood_2017.geojson: fecha de observación inválida '{fecha}'")
            area_obs = obs.get("area_original_km2")
            if not isinstance(area_obs, (int, float)) or area_obs <= 0:
                error("flood_2017.geojson: área de observación inválida")
            else:
                obs_areas.append(float(area_obs))
            if not isinstance(obs.get("partes"), int) or obs["partes"] <= 0:
                error("flood_2017.geojson: número de partes inválido")

        if obs_dates:
            expected = obs_dates[0] if len(obs_dates) == 1 else f"{min(obs_dates)}/{max(obs_dates)}"
            if props.get("fecha") != expected:
                error(
                    f"flood_2017.geojson: fecha '{props.get('fecha')}' no coincide con "
                    f"las observaciones ({expected})"
                )
        if obs_areas:
            area_original = props.get("area_original_km2")
            if not isinstance(area_original, (int, float)):
                error("flood_2017.geojson: falta el área original")
            elif not (max(obs_areas) - 0.5 <= float(area_original) <= sum(obs_areas) + 0.5):
                error(
                    "flood_2017.geojson: el área original no está entre la mayor "
                    "observación y la suma de observaciones"
                )

        area = props.get("area_km2")
        geom = geom_of(feature)
        if not geom.is_valid:
            error(f"flood_2017.geojson: geometría inválida en {props.get('aoi')}")
        measured = utm_km2(geom)
        if not isinstance(area, (int, float)) or area <= 0:
            error(f"flood_2017.geojson: área inválida en {props.get('aoi', '?')}")
        elif abs(measured - float(area)) / float(area) > 0.01:
            error(f"flood_2017.geojson: área declarada {area} vs medida {measured:.1f} km²")
        else:
            total += float(area)
        if obs_areas and isinstance(area, (int, float)):
            reference = props.get("area_original_km2")
            if isinstance(reference, (int, float)) and reference > 0:
                if abs(float(area) - float(reference)) / float(reference) > 0.02:
                    error(
                        "flood_2017.geojson: el área publicada difiere más de 2 % "
                        "del vector original"
                    )
            if float(area) < max(obs_areas) * 0.98:
                error(
                    "flood_2017.geojson: el área publicada es menor que la mayor "
                    "observación por más del 2 %"
                )
    if not 500 <= total <= 600:
        error(f"flood_2017.geojson: área total {total:.1f} km² fuera del rango esperado (500–600)")
    size = path.stat().st_size
    if size > 1_500_000:
        error(f"flood_2017.geojson: {size / 1e6:.2f} MB; conviene simplificar más")
    print(f"  flood_2017: {len(features)} zonas · {total:.1f} km² · {size / 1e3:.0f} kB")


def check_obras():
    path = WEB_DATA / "obras.geojson"
    data = cargar_json(path)
    if not data:
        return
    features = data.get("features") or []
    if len(features) != 2:
        error(f"obras.geojson: se esperaban 2 elementos; hay {len(features)}")
        return
    tipos = set()
    poechos = None
    canal = None
    for feature in features:
        props = feature.get("properties") or {}
        if props.get("fuente") != "obras-esquematicas":
            error("obras.geojson: fuente inesperada; debe ser 'obras-esquematicas'")
        if props.get("esquematico") is not True:
            error("obras.geojson: falta la marca 'esquematico: true'")
        if not props.get("nota"):
            error("obras.geojson: falta la nota de límite")
        tipos.add(props.get("tipo"))
        geom = geom_of(feature)
        if props.get("tipo") == "represa":
            if geom.geom_type != "Point":
                error("obras.geojson: Poechos debe ser un punto de referencia")
            else:
                poechos = (geom.x, geom.y)
        if props.get("tipo") == "canal":
            if geom.geom_type != "LineString":
                error("obras.geojson: el canal debe ser una línea esquemática")
            else:
                canal = geom
    if tipos != {"represa", "canal"}:
        error(f"obras.geojson: tipos inesperados {sorted(tipos)}")
    if poechos and haversine_km(poechos, POECHOS) > 2:
        error("obras.geojson: Poechos está a más de 2 km del dique documentado")
    if canal:
        ends = [canal.coords[0], canal.coords[-1]]
        if haversine_km(tuple(ends[0]), POECHOS) > 2 or haversine_km(tuple(ends[-1]), CURUMUY) > 3:
            error("obras.geojson: el canal esquemático no empieza en Poechos y termina en Curumuy")
    print(f"  obras: {len(features)} referencias esquemáticas")


def check_cortes():
    cortes = cargar_json(WEB_DATA / "cortes.geojson")
    perfiles = cargar_json(WEB_DATA / "cortes_perfiles.json")
    cuenca = cargar_json(WEB_DATA / "cuenca.geojson")
    network = cargar_json(RAW / "network.json")
    if not cortes or not perfiles:
        return
    basin = make_valid(geom_of(cuenca["features"][0])) if cuenca else None
    ids = {f.get("properties", {}).get("id") for f in cortes.get("features", [])}
    perfiles_data = perfiles.get("perfiles") or {}
    for campo in ["resolucion_fuente_m", "resolucion_efectiva_m", "resolucion_malla_m"]:
        if not perfiles.get(campo):
            error(f"cortes_perfiles.json: falta '{campo}'")
    faltan = ids - set(perfiles_data)
    sobran = set(perfiles_data) - ids
    if faltan:
        error(f"cortes sin perfil: {sorted(faltan)}")
    if sobran:
        error(f"perfiles sin corte: {sorted(sobran)}")

    rivers = network.get("rivers", []) if network else []
    effective = float(perfiles.get("resolucion_efectiva_m") or 0)
    for feature in cortes.get("features", []):
        props = feature.get("properties") or {}
        geom = geom_of(feature)
        if basin is not None and not basin.covers(geom):
            error(f"corte {props.get('id')}: no está dentro de la cuenca")
        if not any(
            LineString(r["coords"]).intersects(geom)
            for r in rivers
            if r.get("upland", 0) >= 500 and len(r.get("coords", [])) >= 2
        ):
            error(f"corte {props.get('id')}: no cruza la red hídrica")
        coords = list(geom.coords)
        measured = haversine_km(coords[0], coords[-1])
        if abs(float(props.get("longitud_km", 0)) - measured) > 1:
            error(f"corte {props.get('id')}: longitud declarada {props.get('longitud_km')} vs {measured:.1f} km")

    for fid, perfil in perfiles_data.items():
        dist = perfil.get("dist_km") or []
        elev = perfil.get("elev_m") or []
        if len(dist) != len(elev) or len(dist) < 2:
            error(f"perfil {fid}: dist_km y elev_m no coinciden o son muy cortos")
            continue
        if any(b < a for a, b in zip(dist, dist[1:])):
            error(f"perfil {fid}: distancias no monótonas")
        if any(v is None for v in elev):
            aviso(f"perfil {fid}: contiene elevaciones nulas")
        paso = (dist[-1] - dist[0]) * 1000 / (len(dist) - 1)
        declarado = perfil.get("paso_perfil_m")
        if declarado is None:
            error(f"perfil {fid}: falta paso_perfil_m")
        elif abs(paso - float(declarado)) > max(1.0, paso * 0.02):
            error(f"perfil {fid}: paso declarado {declarado} m; real {paso:.1f} m")
        if effective and paso < effective * PROFILE_STEP_TOLERANCE:
            error(f"perfil {fid}: paso {paso:.1f} m < resolución efectiva {effective:.0f} m")
        declared_len = perfil.get("longitud_km")
        if declared_len is not None and abs(float(declared_len) - dist[-1]) > 0.05:
            error(f"perfil {fid}: longitud declarada {declared_len} vs perfil {dist[-1]}")
        if perfil.get("elev_min_m") is None or perfil.get("elev_max_m") is None:
            error(f"perfil {fid}: faltan cotas")
    print(f"  cortes: {len(ids)} · perfiles: {len(perfiles_data)} · resolución efectiva {effective:.0f} m")


def check_grid():
    meta_path = WEB_DATA / "dem_grid.meta.json"
    bin_path = WEB_DATA / "dem_grid.bin"
    meta = cargar_json(meta_path)
    if not meta or not bin_path.exists():
        return
    esperado = meta.get("width", 0) * meta.get("height", 0) * 2
    real = bin_path.stat().st_size
    if esperado != real:
        error(f"dem_grid.bin: {real} bytes; se esperaban {esperado} para {meta.get('width')}×{meta.get('height')} Int16")
    bbox = meta.get("bbox") or []
    if len(bbox) != 4:
        error("dem_grid.meta.json: bbox inválido")
    else:
        west, south, east, north = bbox
        lon_res = 111_320 * abs(east - west) * math.cos(math.radians((south + north) / 2)) / max(meta.get("width", 1), 1)
        lat_res = 110_540 * abs(north - south) / max(meta.get("height", 1), 1)
        declared = meta.get("resolution_m_aprox")
        if not declared or abs(float(declared) - max(lon_res, lat_res)) / max(lon_res, lat_res) > 0.10:
            error(f"dem_grid.meta.json: resolución declarada {declared} vs calculada {max(lon_res, lat_res):.0f} m")
        if meta.get("row_order") != "north-to-south":
            error("dem_grid.meta.json: row_order debe ser north-to-south")
        if meta.get("dtype") != "int16" or meta.get("byte_order") != "little":
            error("dem_grid.meta.json: dtype/byte_order inesperados")
    print(f"  dem_grid: {real / 1e3:.0f} kB · {meta.get('width')}×{meta.get('height')}")


def check_glb(path: Path) -> None:
    """Valida cabecera, chunks, bufferViews, accessors, meshes y extensiones."""
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        error(f"{path.relative_to(ROOT)} no es un GLB válido")
        return
    version = int.from_bytes(data[4:8], "little")
    if version != 2:
        error(f"{path.relative_to(ROOT)}: versión glTF {version}; se esperaba 2")
        return
    total = int.from_bytes(data[8:12], "little")
    if total != len(data):
        error(f"{path.relative_to(ROOT)}: longitud de cabecera {total} != {len(data)}")
    off = 12
    chunks = []
    while off + 8 <= len(data):
        length, kind = struct.unpack_from("<II", data, off)
        off += 8
        if off + length > len(data):
            error(f"{path.relative_to(ROOT)}: chunk fuera de límites")
            return
        chunks.append((kind, data[off:off + length]))
        off += length
    if off != len(data):
        error(f"{path.relative_to(ROOT)}: bytes sobrantes tras los chunks")
    json_chunk = next((c[1] for c in chunks if c[0] == 0x4E4F534A), None)
    bin_chunk = next((c[1] for c in chunks if c[0] == 0x004E4942), None)
    if json_chunk is None:
        error(f"{path.relative_to(ROOT)}: falta el chunk JSON")
        return
    try:
        gltf = json.loads(json_chunk.decode("utf-8").rstrip(" \x00"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        error(f"{path.relative_to(ROOT)}: JSON inválido ({exc})")
        return

    buffers = gltf.get("buffers") or []
    if buffers and bin_chunk is not None and int(buffers[0].get("byteLength", 0)) > len(bin_chunk):
        error(f"{path.name}: buffer mayor que el chunk BIN")
    views = gltf.get("bufferViews") or []
    for i, view in enumerate(views):
        if view.get("buffer", 0) != 0:
            error(f"{path.name}: bufferView {i} apunta a otro buffer")
        if int(view.get("byteOffset", 0)) + int(view.get("byteLength", 0)) > len(bin_chunk or b""):
            error(f"{path.name}: bufferView {i} fuera del BIN")
    components = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
    types = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
    for i, accessor in enumerate(gltf.get("accessors") or []):
        view_index = accessor.get("bufferView")
        if view_index is not None and not 0 <= int(view_index) < len(views):
            error(f"{path.name}: accessor {i} con bufferView inexistente")
            continue
        size = int(accessor.get("count", 0)) * components.get(accessor.get("componentType"), 0) * types.get(accessor.get("type"), 0)
        if view_index is not None and size:
            view = views[int(view_index)]
            if int(accessor.get("byteOffset", 0)) + size > int(view.get("byteLength", 0)):
                error(f"{path.name}: accessor {i} fuera del bufferView")
    for i, mesh in enumerate(gltf.get("meshes") or []):
        for primitive in mesh.get("primitives") or []:
            for accessor in (primitive.get("attributes") or {}).values():
                if not 0 <= int(accessor) < len(gltf.get("accessors") or []):
                    error(f"{path.name}: mesh {i} con accessor inexistente")
            draco = (primitive.get("extensions") or {}).get("KHR_draco_mesh_compression")
            if draco and not 0 <= int(draco.get("bufferView", -1)) < len(views):
                error(f"{path.name}: Draco con bufferView inexistente")
    extensiones = set(gltf.get("extensionsUsed") or []) | set(gltf.get("extensionsRequired") or [])
    if "KHR_draco_mesh_compression" not in extensiones:
        aviso(f"{path.name} no declara compresión Draco; el visor seguirá funcionando")
    names = [str(node.get("name", "")) for node in gltf.get("nodes") or []]
    if any("Naciente" in name for name in names):
        aviso(
            "piura.glb todavía contiene el rótulo «Naciente ~2 700 m»; "
            "el visor lo oculta, pero debe retirarse en la próxima exportación"
        )
    print(f"  GLB: {len(gltf.get('nodes', []))} nodos · {len(views)} bufferViews · {len(gltf.get('meshes', []))} mallas")


def check_model():
    if not MODEL.exists():
        error("falta web/public/models/piura.glb")
        return
    for name in DRACO_FILES:
        if not (DRACO / name).exists():
            error(f"falta web/public/draco/{name}")
    check_glb(MODEL)
    mb = MODEL.stat().st_size / 1e6
    if mb > 4:
        aviso(f"piura.glb pesa {mb:.1f} MB; conviene optimizarlo (Draco o malla más ligera)")
    print(f"  modelo: {mb:.1f} MB")


def check_sync():
    # Estas imágenes se generan solo para la web; relieve_info.json es metadata
    # interna del ETL y no se publica.
    web_only = {"flood_2017.jpg", "relieve.jpg", "relieve_info.json"}
    for path in sorted(WEB_DATA.glob("*")):
        if path.name in web_only:
            continue
        twin = PROCESSED / path.name
        if not twin.exists():
            aviso(f"{path.name}: no existe la copia en data/processed")
        elif twin.read_bytes() != path.read_bytes():
            error(f"{path.name}: data/processed y web/public/data difieren")


def check_presupuesto():
    pesos = [p.stat().st_size for p in WEB_DATA.glob("*") if p.name not in {"dem_grid.bin"}]
    total = sum(pesos)
    print(f"  datos publicados: {total / 1e3:.0f} kB")
    if total > 2_000_000:
        aviso(f"los datos publicados superan 2 MB ({total / 1e6:.2f} MB)")


def main() -> int:
    print("validando datos del atlas")
    ids = check_sources()
    check_licencias(ids)
    check_page_sources(ids)
    check_citation()
    check_raw_limits()
    check_layer_fuentes(ids)
    check_topology()
    check_rivers()
    check_places()
    check_flood()
    check_obras()
    check_cortes()
    check_grid()
    check_model()
    check_sync()
    check_presupuesto()

    if avisos:
        print("\navisos:")
        for msg in avisos:
            print(f"  - {msg}")
    if errores:
        print("\nerrores:")
        for msg in errores:
            print(f"  - {msg}")
        return 1
    print("\ntodo en orden")
    return 0


if __name__ == "__main__":
    sys.exit(main())
