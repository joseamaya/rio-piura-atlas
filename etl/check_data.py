#!/usr/bin/env python3
"""Valida la coherencia entre fuentes, capas y archivos publicados.

Se puede ejecutar sin el DEM y sin conexión. Pensado para CI y para antes de
publicar una versión del atlas.

Uso:
    python3 etl/check_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources.yml"
WEB_DATA = ROOT / "web" / "public" / "data"
MODEL = ROOT / "web" / "public" / "models" / "piura.glb"
DRACO = ROOT / "web" / "public" / "draco"
DRACO_FILES = ("draco_wasm_wrapper.js", "draco_decoder.wasm")

ESTADOS = {"disponible", "por_solicitar", "por_verificar"}
GRUPOS = {"Límites, relieve y red", "Agua", "Inundaciones y riesgo", "Estudios"}
CAMPOS = ["id", "titulo", "institucion", "url", "fecha", "escala", "licencia", "estado", "metodo", "grupo"]

errores: list[str] = []
avisos: list[str] = []


def error(msg: str) -> None:
    errores.append(msg)


def aviso(msg: str) -> None:
    avisos.append(msg)


def cargar_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        error(f"falta {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        error(f"JSON inválido en {path.relative_to(ROOT)}: {exc}")
    return None


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
        if not fuente.get("licencia"):
            error(f"{fid}: licencia vacía")
        if fuente.get("fecha") is not None and not isinstance(fuente["fecha"], str):
            aviso(f"{fid}: fecha no es texto; YAML puede interpretarla como fecha")

    print(f"fuentes: {len(ids)}")
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
        if len(geom.get("coordinates") or []) != 2:
            error(f"{path.name}: punto sin dos coordenadas")
        return
    if gtype == "LineString":
        if len(geom.get("coordinates") or []) < 2:
            error(f"{path.name}: línea con menos de 2 puntos")
        return
    if gtype == "Polygon":
        polygons = [geom.get("coordinates") or []]
    elif gtype == "MultiPolygon":
        polygons = geom.get("coordinates") or []
    else:
        error(f"{path.name}: geometría no soportada '{gtype}'")
        return
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
            if not feature.get("geometry"):
                error(f"{path.name}: feature sin geometría")
                continue
            check_geometry(path, feature["geometry"])
        print(f"  {path.name}: {len(data.get('features', []))} elementos")


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
        for campo in ("evento", "zona", "aoi", "fecha", "sensores", "area_km2", "fuente", "metodo", "cobertura"):
            if campo not in props:
                error(f"flood_2017.geojson: falta '{campo}' en {props.get('aoi', '?')}")
        if props.get("fuente") != "copernicus-ems-emsr199":
            error(f"flood_2017.geojson: fuente inesperada '{props.get('fuente')}'")
        if props.get("esquematico") is not False:
            error(f"flood_2017.geojson: la mancha no debe marcarse como esquemática")
        area = props.get("area_km2")
        if not isinstance(area, (int, float)) or area <= 0:
            error(f"flood_2017.geojson: área inválida en {props.get('aoi', '?')}")
        else:
            total += float(area)
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
    for feature in features:
        props = feature.get("properties") or {}
        if props.get("fuente") != "obras-esquematicas":
            error("obras.geojson: fuente inesperada; debe ser 'obras-esquematicas'")
        if props.get("esquematico") is not True:
            error("obras.geojson: falta la marca 'esquematico: true'")
        if not props.get("nota"):
            error("obras.geojson: falta la nota de límite")
        tipos.add(props.get("tipo"))
    if tipos != {"represa", "canal"}:
        error(f"obras.geojson: tipos inesperados {sorted(tipos)}")
    print(f"  obras: {len(features)} elementos esquemáticos")


def check_cortes():
    cortes = cargar_json(WEB_DATA / "cortes.geojson")
    perfiles = cargar_json(WEB_DATA / "cortes_perfiles.json")
    if not cortes or not perfiles:
        return
    ids = {f.get("properties", {}).get("id") for f in cortes.get("features", [])}
    perfiles_data = perfiles.get("perfiles") or {}
    for campo in ["resolucion_fuente_m", "resolucion_malla_m"]:
        if not perfiles.get(campo):
            error(f"cortes_perfiles.json: falta '{campo}'")
    faltan = ids - set(perfiles_data)
    sobran = set(perfiles_data) - ids
    if faltan:
        error(f"cortes sin perfil: {sorted(faltan)}")
    if sobran:
        error(f"perfiles sin corte: {sorted(sobran)}")
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
    print(f"  cortes: {len(ids)} · perfiles: {len(perfiles_data)}")


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
    if len(meta.get("bbox") or []) != 4:
        error("dem_grid.meta.json: bbox inválido")
    print(f"  dem_grid: {real / 1e3:.0f} kB")


def check_glb(path: Path) -> None:
    """Comprueba cabecera, versión y extensión Draco del GLB publicado."""
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        error(f"{path.relative_to(ROOT)} no es un GLB válido")
        return
    version = int.from_bytes(data[4:8], "little")
    if version != 2:
        error(f"{path.relative_to(ROOT)}: versión glTF {version}; se esperaba 2")
        return
    chunk_len = int.from_bytes(data[12:16], "little")
    if data[16:20] != b"JSON" or 20 + chunk_len > len(data):
        error(f"{path.relative_to(ROOT)}: bloque JSON inválido")
        return
    try:
        gltf = json.loads(data[20:20 + chunk_len].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        error(f"{path.relative_to(ROOT)}: JSON inválido ({exc})")
        return
    extensiones = set(gltf.get("extensionsUsed") or []) | set(gltf.get("extensionsRequired") or [])
    if "KHR_draco_mesh_compression" not in extensiones:
        aviso(f"{path.name} no declara compresión Draco; el visor seguirá funcionando")


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
    check_citation()
    check_layer_fuentes(ids)
    check_flood()
    check_obras()
    check_cortes()
    check_grid()
    check_model()
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
