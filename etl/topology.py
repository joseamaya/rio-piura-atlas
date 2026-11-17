#!/usr/bin/env python3
"""Auditoría y reconciliación topológica de las subcuencas del atlas.

La cuenca del río Piura se mide en EPSG:32717 (UTM 17S), que es el sistema de
trabajo del geoservidor de ANA. No se usa EPSG:32718: ese es el sistema en el que
ANA calculó su campo ``Shape_Area``, no el de la geometría publicada.

Las tolerancias no esconden errores: a escala 1:100 000, 1 mm en el papel son
100 m y 1 mm² son 0,01 km². Un solapamiento, hueco o superficie fuera de la
cuenca mayor que 0,01 km² no se puede atribuir solo a la precisión cartográfica.
Por debajo de 0,001 km² (0,1 mm² en el papel) se considera un sliver de
simplificación y se reporta como aviso.

Desde v0.2.2 la validez se comprueba **antes** de reparar. Una geometría inválida
nunca se convierte en válida sin dejar un hallazgo con su motivo, su tipo original
y el resultado de la reparación.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
from pyproj import Geod, Transformer
from shapely import segmentize, set_precision, transform as shapely_transform
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import polygonize, unary_union
from shapely.validation import explain_validity, make_valid

METRIC_CRS = "EPSG:32717"
TO_METRIC = Transformer.from_crs("EPSG:4326", METRIC_CRS, always_xy=True)
GEOD = Geod(ellps="WGS84")

FINDING_ERROR = "error"
FINDING_WARNING = "warning"


@dataclass(frozen=True)
class Tolerances:
    """Umbrales en km² y en proporción de la cuenca.

    ``error_km2``: 1 mm² a 1:100 000. Un valor mayor es una inconsistencia real.
    ``warn_km2``: 0,1 mm² a 1:100 000. Por debajo se ignora como ruido numérico.
    ``total_share_error``: un conjunto de slivers que supera esta fracción de la
    cuenca es un problema sistemático aunque cada fragmento sea pequeño.
    ``area_declared_tolerance``: tolerancia de la comprobación secundaria de área.
    ``simplification_deg``: tolerancia de simplificación usada por el ETL
    (0,0006° ≈ 66 m). No es un umbral de error; sirve para interpretar el
    desplazamiento de límites.
    """

    error_km2: float = 0.01
    warn_km2: float = 0.001
    total_share_error: float = 0.0001
    area_declared_tolerance: float = 0.005
    simplification_deg: float = 0.0006
    boundary_warn_factor: float = 3.0

    @property
    def boundary_warn_m(self) -> float:
        """Desplazamiento p95 que se considera fuera de lo esperado.

        Se deriva de la tolerancia de simplificación: 3 × 0,0006° ≈ 200 m.
        No es un estándar externo; es una regla de revisión documentada.
        """
        return self.simplification_deg * 111_320.0 * self.boundary_warn_factor


@dataclass
class GeometryAudit:
    """Estado de una geometría antes y después de una reparación explícita."""

    name: str
    valid: bool
    empty: bool
    geom_type: str
    reason: str | None = None
    repaired: bool = False
    repaired_type: str | None = None
    repaired_valid: bool | None = None
    polygonal_parts: int = 0
    discarded_parts: int = 0
    discarded_length_m: float = 0.0
    discarded_types: tuple[str, ...] = ()
    note: str | None = None

    def as_dict(self) -> dict:
        return {
            "nombre": self.name,
            "valida": self.valid,
            "vacia": self.empty,
            "tipo": self.geom_type,
            "motivo": self.reason,
            "reparada": self.repaired,
            "tipo_reparado": self.repaired_type,
            "reparada_valida": self.repaired_valid,
            "partes_poligonales": self.polygonal_parts,
            "partes_descartadas": self.discarded_parts,
            "longitud_descartada_m": round(self.discarded_length_m, 2),
            "tipos_descartados": list(self.discarded_types),
            "nota": self.note,
        }


@dataclass
class Finding:
    kind: str
    severity: str
    area_km2: float
    names: tuple[str, ...]
    detail: str
    components: int = 1
    max_component_km2: float | None = None

    def message(self, prefix: str = "") -> str:
        head = f"{prefix}: " if prefix else ""
        if self.kind == "overlap":
            return (
                f"{head}solapamiento de {self.area_km2:.4f} km² entre "
                f"{' y '.join(self.names)}"
            )
        if self.kind == "outside":
            return f"{head}{self.names[0]} sobresale {self.area_km2:.4f} km² de la cuenca"
        if self.kind == "gap":
            if self.components > 1:
                return (
                    f"{head}hueco total de {self.area_km2:.4f} km² en "
                    f"{self.components} fragmentos (mayor: {self.max_component_km2:.4f} km²); "
                    f"afecta a {', '.join(self.names) or 'varias subcuencas'}"
                )
            return (
                f"{head}hueco de {self.area_km2:.4f} km² entre "
                f"{', '.join(self.names) or 'varias subcuencas'}"
            )
        if self.kind == "hole":
            return f"{head}hueco interior no justificado en {self.names[0]}: {self.area_km2:.4f} km²"
        if self.kind == "invalid":
            return f"{head}geometría inválida en {self.names[0]}: {self.detail}"
        if self.kind == "empty":
            return f"{head}geometría vacía en {self.names[0]}: {self.detail}"
        if self.kind == "repair":
            return f"{head}reparación de {self.names[0]}: {self.detail}"
        if self.kind == "area":
            return f"{head}{self.detail}"
        if self.kind == "fidelity":
            return f"{head}fidelidad de {self.names[0]}: {self.detail}"
        return f"{head}{self.detail}"


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)
    basin_area_km2: float = 0.0
    sub_area_km2: float = 0.0
    overlap_total_km2: float = 0.0
    overlap_pairs: int = 0
    overlap_max_km2: float = 0.0
    outside_total_km2: float = 0.0
    outside_max_km2: float = 0.0
    gap_total_km2: float = 0.0
    gap_components: int = 0
    gap_max_km2: float = 0.0
    hole_count: int = 0
    basin_audit: GeometryAudit | None = None
    repairs: list[GeometryAudit] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == FINDING_ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == FINDING_WARNING]

    def summary(self) -> str:
        return (
            f"cuenca {self.basin_area_km2:.1f} km² · subcuencas {self.sub_area_km2:.1f} km² · "
            f"solapamientos {self.overlap_pairs} ({self.overlap_total_km2:.4f} km²) · "
            f"fuera {self.outside_total_km2:.4f} km² · "
            f"huecos {self.gap_components} ({self.gap_total_km2:.4f} km²)"
        )


@dataclass
class FidelityMetrics:
    """Comparación geométrica entre una fuente y su versión transformada."""

    area_source_km2: float
    area_target_km2: float
    delta_area_km2: float
    delta_area_pct: float
    iou: float
    symmetric_difference_km2: float
    hausdorff_m: float
    boundary_mean_m: float
    boundary_p95_m: float
    components_source: int
    components_target: int

    def as_dict(self) -> dict:
        return {
            "area_fuente_km2": round(self.area_source_km2, 4),
            "area_objetivo_km2": round(self.area_target_km2, 4),
            "delta_area_km2": round(self.delta_area_km2, 4),
            "delta_area_pct": round(self.delta_area_pct, 6),
            "iou": round(self.iou, 6),
            "diferencia_simetrica_km2": round(self.symmetric_difference_km2, 4),
            "hausdorff_m": round(self.hausdorff_m, 1),
            "distancia_media_limite_m": round(self.boundary_mean_m, 1),
            "distancia_p95_limite_m": round(self.boundary_p95_m, 1),
            "componentes_fuente": self.components_source,
            "componentes_objetivo": self.components_target,
        }


@dataclass
class ReconciliationResult:
    geoms: list[tuple[str, object]]
    basin: object
    basin_area_km2: float
    gap_before_km2: float
    overlap_before_km2: float
    outside_before_km2: float
    face_count: int
    gap_face_count: int
    area_changes_km2: dict[str, float]
    area_changes_pct: dict[str, float]
    area_before_km2: dict[str, float]
    area_after_km2: dict[str, float]
    proximity_area_km2: float
    proximity_faces: int
    proximity_max_distance_m: float
    proximity_mean_distance_m: float
    overlap_assigned_km2: float
    fidelity: dict[str, FidelityMetrics]
    repairs: list[GeometryAudit] = field(default_factory=list)


def inspect_geometry(geom, name: str = "") -> GeometryAudit:
    """Inspecciona una geometría sin repararla ni modificarla."""
    if geom is None:
        return GeometryAudit(
            name=name,
            valid=False,
            empty=True,
            geom_type="None",
            reason="geometría ausente",
        )
    empty = bool(geom.is_empty)
    valid = bool(geom.is_valid)
    reason = None if valid else explain_validity(geom)
    return GeometryAudit(
        name=name,
        valid=valid,
        empty=empty,
        geom_type=geom.geom_type,
        reason=reason,
    )


def _extract_polygonal_parts(geom) -> list[Polygon]:
    """Extrae componentes poligonales sin reparar la geometría."""
    if geom is None or geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    parts: list[Polygon] = []
    if hasattr(geom, "geoms"):
        for child in geom.geoms:
            parts.extend(_extract_polygonal_parts(child))
    return parts


def _discarded_summary(geom) -> tuple[int, float, tuple[str, ...]]:
    """Cuenta líneas y puntos que no se conservan al extraer polígonos."""
    count = 0
    length = 0.0
    types: set[str] = set()

    def walk(item) -> None:
        nonlocal count, length
        if item is None or item.is_empty:
            return
        if isinstance(item, (Polygon, MultiPolygon)):
            return
        if hasattr(item, "geoms"):
            for child in item.geoms:
                walk(child)
            return
        count += 1
        types.add(item.geom_type)
        if item.geom_type in {"LineString", "LinearRing"}:
            length += metric_length_m(item)

    walk(geom)
    return count, length, tuple(sorted(types))


def repair_to_polygonal(
    geom,
    name: str = "",
    allow_repair: bool = False,
) -> tuple[object | None, GeometryAudit]:
    """Repara o normaliza una geometría y devuelve el registro de lo ocurrido.

    - Si es un Polygon/MultiPolygon válido, lo devuelve sin tocar.
    - Si es inválida y ``allow_repair`` es False, devuelve ``None`` y explica por qué.
    - Si se permite reparar, aplica ``make_valid``, conserva todas las componentes
      poligonales y registra las líneas/puntos descartados.
    """
    audit = inspect_geometry(geom, name)
    if geom is None or geom.is_empty:
        return None, audit

    if audit.valid and geom.geom_type in {"Polygon", "MultiPolygon"}:
        audit.polygonal_parts = len(_extract_polygonal_parts(geom))
        return geom, audit

    if audit.valid and geom.geom_type == "GeometryCollection":
        if not allow_repair:
            audit.note = (
                "geometría compuesta: contiene polígonos y otros tipos; "
                "requiere extracción explícita"
            )
            return None, audit
        repaired = geom
    else:
        if not allow_repair:
            audit.note = "geometría inválida: requiere reparación explícita"
            return None, audit
        repaired = make_valid(geom)

    if repaired is None or repaired.is_empty:
        audit.note = "la reparación produjo una geometría vacía"
        return None, audit

    parts = _extract_polygonal_parts(repaired)
    if not parts:
        audit.note = "la geometría no contiene polígonos después de reparar"
        return None, audit

    result = parts[0] if len(parts) == 1 else MultiPolygon(parts)
    if not result.is_valid or result.is_empty:
        audit.repaired = True
        audit.repaired_type = result.geom_type
        audit.repaired_valid = False
        audit.polygonal_parts = len(parts)
        audit.note = (
            "la reparación produjo una geometría inválida: "
            f"{explain_validity(result) if not result.is_empty else 'vacía'}"
        )
        return None, audit
    discarded, discarded_length, discarded_types = _discarded_summary(repaired)
    audit.repaired = True
    audit.repaired_type = result.geom_type
    audit.repaired_valid = True
    audit.polygonal_parts = len(parts)
    audit.discarded_parts = discarded
    audit.discarded_length_m = discarded_length
    audit.discarded_types = discarded_types
    if audit.reason:
        audit.note = f"make_valid: {audit.reason}; resultado {result.geom_type}"
    else:
        audit.note = f"normalización a {result.geom_type}"
    if discarded:
        audit.note += (
            f"; {discarded} componente(s) no poligonal(es) descartada(s)"
        )
    return result, audit


def polygonal_parts(geom) -> list[Polygon]:
    """Extrae componentes poligonales de una geometría ya validada.

    No repara: si la geometría es inválida, falla. Para reparar explícitamente,
    usa ``repair_to_polygonal``.
    """
    if geom is None or geom.is_empty:
        return []
    if not geom.is_valid:
        raise ValueError(f"geometría inválida: {explain_validity(geom)}")
    return _extract_polygonal_parts(geom)


def as_polygonal(geom):
    """Devuelve Polygon/MultiPolygon o None, sin reparar.

    Una GeometryCollection no se acepta silenciosamente: puede contener líneas o
    puntos que se perderían. Usa ``repair_to_polygonal`` para normalizarla y
    registrar lo descartado.
    """
    if geom is None or geom.is_empty:
        return None
    if not geom.is_valid:
        raise ValueError(f"geometría inválida: {explain_validity(geom)}")
    if geom.geom_type in {"Polygon", "MultiPolygon"}:
        return geom
    raise ValueError(
        f"se esperaba Polygon/MultiPolygon; llegó {geom.geom_type}. "
        "Normaliza con repair_to_polygonal()."
    )


def _project(geom):
    if geom is None or geom.is_empty:
        return geom
    if not geom.is_valid:
        raise ValueError(f"geometría inválida: {explain_validity(geom)}")

    def project_coords(coords):
        x, y = TO_METRIC.transform(coords[:, 0], coords[:, 1])
        return np.column_stack([x, y])

    return shapely_transform(geom, project_coords)


def metric_area_km2(geom) -> float:
    """Área en la proyección métrica de trabajo, en km²."""
    if geom is None or geom.is_empty:
        return 0.0
    projected = _project(geom)
    area = abs(projected.area) / 1e6
    return area if math.isfinite(area) else 0.0


def geodesic_area_km2(geom) -> float:
    """Área geodésica (WGS84), para comparar con las áreas publicadas."""
    if geom is None or geom.is_empty:
        return 0.0
    if not geom.is_valid:
        raise ValueError(f"geometría inválida: {explain_validity(geom)}")
    area = abs(GEOD.geometry_area_perimeter(geom)[0]) / 1e6
    return area if math.isfinite(area) else 0.0


def metric_length_m(geom) -> float:
    """Longitud en EPSG:32717, en metros."""
    if geom is None or geom.is_empty:
        return 0.0
    projected = _project(geom)
    length = projected.length
    return length if math.isfinite(length) else 0.0


def metric_distance_m(a, b) -> float:
    """Distancia mínima entre dos geometrías, en metros."""
    if a is None or b is None or a.is_empty or b.is_empty:
        return 0.0
    return _project(a).distance(_project(b))


def _append_geometry_findings(
    report: AuditReport,
    audit: GeometryAudit,
    names: tuple[str, ...],
) -> None:
    if audit.empty:
        report.findings.append(
            Finding(
                kind="empty",
                severity=FINDING_ERROR,
                area_km2=0.0,
                names=names,
                detail=audit.reason or "geometría vacía",
            )
        )
    elif not audit.valid:
        report.findings.append(
            Finding(
                kind="invalid",
                severity=FINDING_ERROR,
                area_km2=0.0,
                names=names,
                detail=audit.reason or "geometría inválida",
            )
        )

    if audit.repaired:
        detail = audit.note or f"reparada a {audit.repaired_type}"
        if audit.discarded_parts:
            detail += (
                f"; {audit.discarded_parts} componente(s) descartada(s)"
                f" de tipos {', '.join(audit.discarded_types)}"
            )
        report.findings.append(
            Finding(
                kind="repair",
                severity=FINDING_WARNING,
                area_km2=0.0,
                names=names,
                detail=detail,
            )
        )


def _shared_names(geoms: list[tuple[str, object]], target) -> tuple[str, ...]:
    touching = [name for name, geom in geoms if geom.distance(target) < 1e-9]
    if touching:
        return tuple(touching)
    nearest = sorted(
        ((geom.distance(target), name) for name, geom in geoms),
        key=lambda item: item[0],
    )
    return tuple(name for _, name in nearest[:2])


def _pairwise(named: list[tuple[str, object]], tol: Tolerances) -> tuple[list[Finding], float, int, float]:
    findings: list[Finding] = []
    total = 0.0
    count = 0
    maximum = 0.0
    for i in range(len(named)):
        for j in range(i + 1, len(named)):
            name_a, geom_a = named[i]
            name_b, geom_b = named[j]
            area = metric_area_km2(geom_a.intersection(geom_b))
            if area < tol.warn_km2:
                continue
            total += area
            count += 1
            maximum = max(maximum, area)
            severity = FINDING_ERROR if area >= tol.error_km2 else FINDING_WARNING
            findings.append(
                Finding(
                    kind="overlap",
                    severity=severity,
                    area_km2=area,
                    names=(name_a, name_b),
                    detail=f"intersección de {area:.4f} km²",
                )
            )
    return findings, total, count, maximum


def _outside(named: list[tuple[str, object]], basin, tol: Tolerances) -> tuple[list[Finding], float, float]:
    findings: list[Finding] = []
    total = 0.0
    maximum = 0.0
    for name, geom in named:
        area = metric_area_km2(geom.difference(basin))
        if area < tol.warn_km2:
            continue
        total += area
        maximum = max(maximum, area)
        severity = FINDING_ERROR if area >= tol.error_km2 else FINDING_WARNING
        findings.append(
            Finding(
                kind="outside",
                severity=severity,
                area_km2=area,
                names=(name,),
                detail=f"{area:.4f} km² fuera de la cuenca",
            )
        )
    return findings, total, maximum


def _gaps(basin, named: list[tuple[str, object]], tol: Tolerances) -> tuple[list[Finding], float, int, float]:
    union = unary_union([geom for _, geom in named])
    gap = basin.difference(union)
    if not gap.is_valid:
        # Geometría derivada, no fuente: se repara para poder medir el hueco.
        gap = make_valid(gap)
    parts = polygonal_parts(gap)
    findings: list[Finding] = []
    total = 0.0
    maximum = 0.0
    large_total = 0.0
    large_count = 0
    large_max = 0.0
    large_names: set[str] = set()
    small_total = 0.0
    small_count = 0
    small_max = 0.0
    small_names: set[str] = set()
    for part in parts:
        area = metric_area_km2(part)
        if area < tol.warn_km2:
            continue
        total += area
        maximum = max(maximum, area)
        names = _shared_names(named, part)
        if area >= tol.error_km2:
            large_total += area
            large_count += 1
            large_max = max(large_max, area)
            large_names.update(names)
        else:
            small_total += area
            small_count += 1
            small_max = max(small_max, area)
            small_names.update(names)

    # Un error agregado es más útil que 60 líneas casi idénticas. El detalle
    # conserva el número de fragmentos, el mayor y las subcuencas afectadas.
    if large_count:
        findings.append(
            Finding(
                kind="gap",
                severity=FINDING_ERROR,
                area_km2=large_total,
                names=tuple(sorted(large_names)),
                detail=f"{large_count} huecos mayores de {tol.error_km2:.3f} km²",
                components=large_count,
                max_component_km2=large_max,
            )
        )
    if small_count:
        findings.append(
            Finding(
                kind="gap",
                severity=FINDING_WARNING,
                area_km2=small_total,
                names=tuple(sorted(small_names)),
                detail=f"{small_count} slivers de simplificación",
                components=small_count,
                max_component_km2=small_max,
            )
        )
    basin_area = metric_area_km2(basin)
    if basin_area and total / basin_area > tol.total_share_error:
        already_error = any(f.kind == "gap" and f.severity == FINDING_ERROR for f in findings)
        if not already_error:
            findings.append(
                Finding(
                    kind="gap",
                    severity=FINDING_ERROR,
                    area_km2=total,
                    names=tuple(sorted(large_names | small_names)),
                    detail=f"hueco total de {total:.4f} km²",
                )
            )
    reportable = sum(1 for part in parts if metric_area_km2(part) >= tol.warn_km2)
    return findings, total, reportable, maximum


def _holes(
    basin,
    named: list[tuple[str, object]],
    tol: Tolerances,
    hole_notes: dict[str, str] | None,
) -> list[Finding]:
    notes = hole_notes or {}
    findings: list[Finding] = []
    for name, geom in named:
        for part in polygonal_parts(geom):
            for interior in part.interiors:
                hole = Polygon(interior)
                # Un agujero del propio límite de la cuenca no es un hueco interno:
                # está fuera del territorio que el atlas publica.
                if not basin.covers(hole):
                    continue
                if any(other.covers(hole) for other_name, other in named if other_name != name):
                    continue
                area = metric_area_km2(hole)
                if area < tol.warn_km2:
                    continue
                note = notes.get(name)
                findings.append(
                    Finding(
                        kind="hole",
                        severity=FINDING_WARNING if note else FINDING_ERROR,
                        area_km2=area,
                        names=(name,),
                        detail=note or f"hueco interior de {area:.4f} km² sin justificación",
                    )
                )
    return findings


def audit_partition(
    basin,
    named_geoms: Iterable[tuple[str, object]],
    tolerances: Tolerances | None = None,
    hole_notes: dict[str, str] | None = None,
) -> AuditReport:
    """Audita una partición sin usar la suma de áreas como indicador principal.

    La validez de la cuenca y de cada subcuenca se comprueba antes de reparar.
    Si una geometría inválida se puede reparar, el reporte conserva el error
    original y añade un aviso con el tipo reparado y los componentes descartados.
    """
    tol = tolerances or Tolerances()
    report = AuditReport()
    basin_fixed, basin_audit = repair_to_polygonal(basin, "cuenca", allow_repair=True)
    report.basin_audit = basin_audit
    _append_geometry_findings(report, basin_audit, ("cuenca",))
    if basin_fixed is None:
        if not basin_audit.empty and basin_audit.valid:
            report.findings.append(
                Finding(
                    kind="repair",
                    severity=FINDING_ERROR,
                    area_km2=0.0,
                    names=("cuenca",),
                    detail=basin_audit.note or "no contiene polígonos",
                )
            )
        return report

    named: list[tuple[str, object]] = []
    for name, geom in named_geoms:
        fixed, audit = repair_to_polygonal(geom, name, allow_repair=True)
        _append_geometry_findings(report, audit, (name,))
        if audit.repaired:
            report.repairs.append(audit)
        if fixed is None:
            if not audit.empty and audit.valid:
                report.findings.append(
                    Finding(
                        kind="repair",
                        severity=FINDING_ERROR,
                        area_km2=0.0,
                        names=(name,),
                        detail=audit.note or "no contiene polígonos",
                    )
                )
            continue
        named.append((name, fixed))

    if not named:
        return report

    report.basin_area_km2 = geodesic_area_km2(basin_fixed)
    report.sub_area_km2 = sum(geodesic_area_km2(geom) for _, geom in named)

    overlap_findings, overlap_total, overlap_pairs, overlap_max = _pairwise(named, tol)
    outside_findings, outside_total, outside_max = _outside(named, basin_fixed, tol)
    gap_findings, gap_total, gap_components, gap_max = _gaps(basin_fixed, named, tol)
    hole_findings = _holes(basin_fixed, named, tol, hole_notes)

    report.findings.extend(overlap_findings)
    report.findings.extend(outside_findings)
    report.findings.extend(gap_findings)
    report.findings.extend(hole_findings)
    report.overlap_total_km2 = overlap_total
    report.overlap_pairs = overlap_pairs
    report.overlap_max_km2 = overlap_max
    report.outside_total_km2 = outside_total
    report.outside_max_km2 = outside_max
    report.gap_total_km2 = gap_total
    report.gap_components = gap_components
    report.gap_max_km2 = gap_max
    report.hole_count = len(hole_findings)

    if report.basin_area_km2:
        relative = abs(report.sub_area_km2 - report.basin_area_km2) / report.basin_area_km2
        if relative > tol.area_declared_tolerance:
            report.findings.append(
                Finding(
                    kind="area",
                    severity=FINDING_ERROR,
                    area_km2=abs(report.sub_area_km2 - report.basin_area_km2),
                    names=(),
                    detail=(
                        f"suma de subcuencas {report.sub_area_km2:.2f} km² vs "
                        f"cuenca {report.basin_area_km2:.2f} km² ({relative * 100:.3f} %)"
                    ),
                )
            )
    return report


def _has_holes(geom) -> bool:
    return any(part.interiors for part in polygonal_parts(geom))


def _prepare_for_reconcile(
    geom,
    name: str,
    allow_repair: bool,
    repairs: list[GeometryAudit],
) -> object:
    audit = inspect_geometry(geom, name)
    if audit.empty:
        raise ValueError(f"{name}: geometría vacía")
    if not audit.valid:
        if not allow_repair:
            raise ValueError(f"{name}: geometría inválida: {audit.reason}")
    fixed, repair_audit = repair_to_polygonal(geom, name, allow_repair=allow_repair)
    if fixed is None:
        raise ValueError(f"{name}: {repair_audit.note or 'no se pudo normalizar'}")
    if repair_audit.repaired:
        repairs.append(repair_audit)
        if not allow_repair:
            raise ValueError(
                f"{name}: requiere normalización ({repair_audit.note}) y "
                "no se permitió reparar"
            )
    return fixed


def _snap_geometry(
    geom,
    name: str,
    precision: float,
    allow_repair: bool,
    repairs: list[GeometryAudit],
) -> object:
    snapped = set_precision(geom, precision)
    audit = inspect_geometry(snapped, name)
    if audit.valid and snapped.geom_type in {"Polygon", "MultiPolygon"}:
        if snapped.geom_type != geom.geom_type:
            audit.repaired = True
            audit.repaired_type = snapped.geom_type
            audit.repaired_valid = bool(snapped.is_valid)
            audit.note = f"la rejilla {precision:g}° cambió el tipo a {snapped.geom_type}"
            repairs.append(audit)
        return snapped
    if not allow_repair:
        raise ValueError(
            f"{name}: la rejilla {precision:g}° produjo una geometría "
            f"{audit.geom_type} inválida o no poligonal: {audit.reason or audit.note or 'sin detalle'}"
        )
    fixed, repair_audit = repair_to_polygonal(snapped, name, allow_repair=True)
    if fixed is None:
        raise ValueError(f"{name}: no se pudo normalizar tras la rejilla")
    repairs.append(repair_audit)
    return fixed


def _boundary_points(boundary, step_m: float = 50.0) -> list[tuple[float, float]]:
    if boundary is None or boundary.is_empty:
        return []
    dense = segmentize(boundary, step_m)
    lines = list(dense.geoms) if hasattr(dense, "geoms") else [dense]
    points: list[tuple[float, float]] = []
    for line in lines:
        if line.is_empty:
            continue
        points.extend((float(x), float(y)) for x, y in line.coords)
    return points


def _boundary_stats(source, target) -> tuple[float, float, float]:
    """Distancia media, p95 y máxima muestreada entre dos límites, en metros."""
    source_boundary = source.boundary
    target_boundary = target.boundary
    if source_boundary.is_empty or target_boundary.is_empty:
        return 0.0, 0.0, 0.0

    source_points = _boundary_points(source_boundary)
    target_points = _boundary_points(target_boundary)
    distances: list[float] = []
    for x, y in source_points:
        distances.append(target_boundary.distance(Point(x, y)))
    for x, y in target_points:
        distances.append(source_boundary.distance(Point(x, y)))
    if not distances:
        return 0.0, 0.0, 0.0
    distances.sort()
    mean = sum(distances) / len(distances)
    p95 = distances[int(len(distances) * 0.95)]
    maximum = distances[-1]
    return mean, p95, maximum


def _component_count(geom) -> int:
    return len(_extract_polygonal_parts(geom))


def fidelity_metrics(source, target) -> FidelityMetrics:
    """Compara dos geometrías poligonales en EPSG:32717.

    IoU y diferencia simétrica se miden en área. Hausdorff es el máximo exacto
    entre límites; la distancia media y el p95 se calculan muestreando ambos
    límites cada 50 m. Hausdorff es muy sensible a un vértice aislado: se publica
    como diagnóstico, no como único criterio.
    """
    source_poly = as_polygonal(source)
    target_poly = as_polygonal(target)
    if source_poly is None or target_poly is None:
        raise ValueError("fidelity_metrics necesita dos geometrías poligonales no vacías")

    source_metric = _project(source_poly)
    target_metric = _project(target_poly)
    area_source = abs(source_metric.area) / 1e6
    area_target = abs(target_metric.area) / 1e6
    delta = area_target - area_source
    delta_pct = (delta / area_source * 100.0) if area_source else 0.0

    intersection = source_metric.intersection(target_metric).area
    union = source_metric.union(target_metric).area
    iou = intersection / union if union else 1.0
    symmetric = abs(source_metric.symmetric_difference(target_metric).area) / 1e6
    hausdorff = source_metric.boundary.hausdorff_distance(target_metric.boundary)
    mean, p95, _ = _boundary_stats(source_metric, target_metric)

    return FidelityMetrics(
        area_source_km2=area_source,
        area_target_km2=area_target,
        delta_area_km2=delta,
        delta_area_pct=delta_pct,
        iou=iou,
        symmetric_difference_km2=symmetric,
        hausdorff_m=hausdorff,
        boundary_mean_m=mean,
        boundary_p95_m=p95,
        components_source=_component_count(source_poly),
        components_target=_component_count(target_poly),
    )


def reconcile_partition(
    basin,
    named_geoms: Iterable[tuple[str, object]],
    precision: float = 1e-6,
    allow_repair: bool = False,
) -> ReconciliationResult:
    """Construye una partición limpia a partir de geometrías simplificadas.

    No crea superficie nueva: reparte las caras del grafo de límites entre las
    subcuencas existentes. Cada cara se asigna a la subcuenca con la que más se
    solapa; si no se solapa con ninguna, a la más cercana. La unión resultante
    es exactamente la cuenca de entrada.

    ``allow_repair`` es False por defecto: una geometría inválida o compuesta
    detiene el proceso con un mensaje explícito. Si se activa, la reparación se
    registra en ``repairs`` y en el resultado.

    ``precision`` fija una rejilla común (1e-6° ≈ 0,11 m) para que la cuenca y
    las subcuencas se serialicen con los mismos vértices y el redondeo no abra
    slivers en el borde.

    Si una subcuenca trae agujeros interiores, la función se detiene: un agujero
    puede ser un cuerpo de agua o un enclave real, y rellenarlo en silencio sería
    inventar geometría. Esos casos requieren una decisión manual documentada.
    """
    repairs: list[GeometryAudit] = []
    basin_fixed = _prepare_for_reconcile(basin, "cuenca", allow_repair, repairs)
    named_fixed: list[tuple[str, object]] = []
    for name, geom in named_geoms:
        named_fixed.append(
            (name, _prepare_for_reconcile(geom, name, allow_repair, repairs))
        )
    if not named_fixed:
        raise ValueError("no hay subcuencas para reconciliar")

    basin_snapped = _snap_geometry(
        basin_fixed, "cuenca", precision, allow_repair, repairs
    )
    named: list[tuple[str, object]] = []
    for name, geom in named_fixed:
        named.append(
            (
                name,
                _snap_geometry(geom, name, precision, allow_repair, repairs),
            )
        )

    with_holes = [name for name, geom in named if _has_holes(geom)]
    if with_holes:
        raise ValueError(
            "subcuencas con agujeros interiores: "
            + ", ".join(with_holes)
            + ". La reconciliación automática no rellena agujeros; revisa el caso."
        )

    union_before = unary_union([geom for _, geom in named])
    gap_before = metric_area_km2(basin_snapped.difference(union_before))
    outside_before = metric_area_km2(union_before.difference(basin_snapped))
    overlap_before = 0.0
    for i in range(len(named)):
        for j in range(i + 1, len(named)):
            overlap_before += metric_area_km2(named[i][1].intersection(named[j][1]))

    lines = unary_union([basin_snapped.boundary] + [geom.boundary for _, geom in named])
    faces = list(polygonize(lines))
    groups: dict[str, list[Polygon]] = {name: [] for name, _ in named}
    gap_faces = 0
    proximity_faces = 0
    proximity_area = 0.0
    proximity_distances: list[float] = []
    overlap_assigned = 0.0

    for face in faces:
        clipped = face.intersection(basin_snapped)
        if not clipped.is_valid:
            clipped = make_valid(clipped)
        for part in polygonal_parts(clipped):
            if part.area <= 0:
                continue
            best_name = None
            best_area = 0.0
            best_geom = None
            for name, geom in named:
                area = part.intersection(geom).area
                if area > best_area:
                    best_area = area
                    best_name = name
                    best_geom = geom
            if best_name is None or best_geom is None or best_area <= 1e-12:
                best_name = min(named, key=lambda item: item[1].distance(part))[0]
                best_geom = dict(named)[best_name]
                distance_m = metric_distance_m(part, best_geom)
                proximity_faces += 1
                proximity_area += metric_area_km2(part)
                proximity_distances.append(distance_m)
                gap_faces += 1
            else:
                overlap_assigned += metric_area_km2(part.intersection(best_geom))
            groups[best_name].append(part)

    reconciled: list[tuple[str, object]] = []
    area_changes: dict[str, float] = {}
    area_changes_pct: dict[str, float] = {}
    area_before: dict[str, float] = {}
    area_after: dict[str, float] = {}
    fidelity: dict[str, FidelityMetrics] = {}
    for name, original in named:
        parts = groups.get(name) or []
        if not parts:
            raise ValueError(f"{name}: la reconciliación no le asignó ninguna cara")
        # La intersección de caras puede reintroducir vértices con más
        # precisión que la rejilla. Se vuelve a fijar la rejilla de salida para
        # que el GeoJSON no cree una autointersección al redondear. Si la
        # operación produjera una geometría inválida, se repara con registro.
        merged = _snap_geometry(
            unary_union(parts),
            f"{name} (salida)",
            precision,
            True,
            repairs,
        )
        merged = as_polygonal(merged)
        if merged is None or merged.is_empty:
            raise ValueError(f"{name}: la reconciliación produjo una geometría vacía")
        reconciled.append((name, merged))
        before = metric_area_km2(original)
        after = metric_area_km2(merged)
        area_before[name] = round(before, 4)
        area_after[name] = round(after, 4)
        area_changes[name] = round(after - before, 4)
        area_changes_pct[name] = round(
            ((after - before) / before * 100.0) if before else 0.0, 6
        )
        fidelity[name] = fidelity_metrics(original, merged)

    union_after = unary_union([geom for _, geom in reconciled])
    gap_after = metric_area_km2(basin_snapped.difference(union_after))
    outside_after = metric_area_km2(union_after.difference(basin_snapped))
    overlap_after = 0.0
    for i in range(len(reconciled)):
        for j in range(i + 1, len(reconciled)):
            overlap_after += metric_area_km2(reconciled[i][1].intersection(reconciled[j][1]))

    if gap_after > 1e-4 or outside_after > 1e-4 or overlap_after > 1e-4:
        raise ValueError(
            "la reconciliación no quedó limpia: "
            f"hueco {gap_after:.6f} km², fuera {outside_after:.6f} km², "
            f"solapamiento {overlap_after:.6f} km²"
        )

    return ReconciliationResult(
        geoms=reconciled,
        basin=basin_snapped,
        basin_area_km2=metric_area_km2(basin_snapped),
        gap_before_km2=gap_before,
        overlap_before_km2=overlap_before,
        outside_before_km2=outside_before,
        face_count=len(faces),
        gap_face_count=gap_faces,
        area_changes_km2=area_changes,
        area_changes_pct=area_changes_pct,
        area_before_km2=area_before,
        area_after_km2=area_after,
        proximity_area_km2=proximity_area,
        proximity_faces=proximity_faces,
        proximity_max_distance_m=max(proximity_distances) if proximity_distances else 0.0,
        proximity_mean_distance_m=(
            sum(proximity_distances) / len(proximity_distances)
            if proximity_distances
            else 0.0
        ),
        overlap_assigned_km2=overlap_assigned,
        fidelity=fidelity,
        repairs=repairs,
    )
