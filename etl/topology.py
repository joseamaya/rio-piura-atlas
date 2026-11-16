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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
from pyproj import Geod, Transformer
from shapely import set_precision, transform as shapely_transform
from shapely.geometry import MultiPolygon, Polygon
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
    """

    error_km2: float = 0.01
    warn_km2: float = 0.001
    total_share_error: float = 0.0001
    area_declared_tolerance: float = 0.005


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
        if self.kind == "area":
            return f"{head}{self.detail}"
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


def polygonal_parts(geom) -> list[Polygon]:
    """Extrae todas las componentes poligonales de una geometría."""
    if geom is None or geom.is_empty:
        return []
    geom = make_valid(geom)
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    parts: list[Polygon] = []
    if hasattr(geom, "geoms"):
        for child in geom.geoms:
            parts.extend(polygonal_parts(child))
    return parts


def as_polygonal(geom):
    """Devuelve Polygon/MultiPolygon o None, sin líneas ni puntos."""
    parts = polygonal_parts(geom)
    if not parts:
        return None
    return parts[0] if len(parts) == 1 else MultiPolygon(parts)


def _project(geom):
    def project_coords(coords):
        x, y = TO_METRIC.transform(coords[:, 0], coords[:, 1])
        return np.column_stack([x, y])

    return shapely_transform(make_valid(geom), project_coords)


def metric_area_km2(geom) -> float:
    """Área en la proyección métrica de trabajo, en km²."""
    projected = _project(geom)
    if projected.is_empty:
        return 0.0
    return abs(projected.area) / 1e6


def geodesic_area_km2(geom) -> float:
    """Área geodésica (WGS84), para comparar con las áreas publicadas."""
    clean = make_valid(geom)
    return abs(GEOD.geometry_area_perimeter(clean)[0]) / 1e6


def _clean_named(named_geoms: Iterable[tuple[str, object]]) -> list[tuple[str, object]]:
    cleaned = []
    for name, geom in named_geoms:
        clean = make_valid(geom)
        if clean is None or clean.is_empty:
            continue
        cleaned.append((name, clean))
    return cleaned


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
    gap = make_valid(basin.difference(union))
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
    reportable = sum(
        1 for part in parts if metric_area_km2(part) >= tol.warn_km2
    )
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
    """Audita una partición sin usar la suma de áreas como indicador principal."""
    tol = tolerances or Tolerances()
    basin = make_valid(basin)
    named = _clean_named(named_geoms)
    report = AuditReport(
        basin_area_km2=geodesic_area_km2(basin),
        sub_area_km2=sum(geodesic_area_km2(geom) for _, geom in named),
    )

    for name, geom in named:
        if not geom.is_valid:
            report.findings.append(
                Finding(
                    kind="invalid",
                    severity=FINDING_ERROR,
                    area_km2=0.0,
                    names=(name,),
                    detail=explain_validity(geom),
                )
            )

    overlap_findings, overlap_total, overlap_pairs, overlap_max = _pairwise(named, tol)
    outside_findings, outside_total, outside_max = _outside(named, basin, tol)
    gap_findings, gap_total, gap_components, gap_max = _gaps(basin, named, tol)
    hole_findings = _holes(basin, named, tol, hole_notes)

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


def reconcile_partition(
    basin,
    named_geoms: Iterable[tuple[str, object]],
    precision: float = 1e-6,
) -> ReconciliationResult:
    """Construye una partición limpia a partir de geometrías simplificadas.

    No crea superficie nueva: reparte las caras del grafo de límites entre las
    subcuencas existentes. Cada cara se asigna a la subcuenca con la que más se
    solapa; si no se solapa con ninguna, a la más cercana. La unión resultante
    es exactamente la cuenca de entrada.

    ``precision`` fija una rejilla común (1e-6° ≈ 0,11 m) para que la cuenca y
    las subcuencas se serialicen con los mismos vértices y el redondeo no abra
    slivers en el borde.

    Si una subcuenca trae agujeros interiores, la función se detiene: un agujero
    puede ser un cuerpo de agua o un enclave real, y rellenarlo en silencio sería
    inventar geometría. Esos casos requieren una decisión manual documentada.
    """
    basin = make_valid(set_precision(make_valid(basin), precision))
    named = [
        (name, make_valid(set_precision(geom, precision)))
        for name, geom in _clean_named(named_geoms)
    ]
    if not named:
        raise ValueError("no hay subcuencas para reconciliar")

    with_holes = [name for name, geom in named if _has_holes(geom)]
    if with_holes:
        raise ValueError(
            "subcuencas con agujeros interiores: "
            + ", ".join(with_holes)
            + ". La reconciliación automática no rellena agujeros; revisa el caso."
        )

    union_before = unary_union([geom for _, geom in named])
    gap_before = metric_area_km2(basin.difference(union_before))
    outside_before = metric_area_km2(union_before.difference(basin))
    overlap_before = 0.0
    for i in range(len(named)):
        for j in range(i + 1, len(named)):
            overlap_before += metric_area_km2(named[i][1].intersection(named[j][1]))

    lines = unary_union([basin.boundary] + [geom.boundary for _, geom in named])
    faces = list(polygonize(lines))
    groups: dict[str, list[Polygon]] = {name: [] for name, _ in named}
    gap_faces = 0

    for face in faces:
        clipped = make_valid(face.intersection(basin))
        for part in polygonal_parts(clipped):
            if part.area <= 0:
                continue
            best_name = None
            best_area = 0.0
            for name, geom in named:
                area = part.intersection(geom).area
                if area > best_area:
                    best_area = area
                    best_name = name
            if best_name is None or best_area <= 1e-12:
                best_name = min(named, key=lambda item: item[1].distance(part))[0]
                gap_faces += 1
            groups[best_name].append(part)

    reconciled: list[tuple[str, object]] = []
    area_changes: dict[str, float] = {}
    for name, original in named:
        parts = groups.get(name) or []
        if not parts:
            raise ValueError(f"{name}: la reconciliación no le asignó ninguna cara")
        merged = as_polygonal(unary_union(parts))
        if merged is None or merged.is_empty:
            raise ValueError(f"{name}: la reconciliación produjo una geometría vacía")
        reconciled.append((name, merged))
        area_changes[name] = round(
            metric_area_km2(merged) - metric_area_km2(original), 4
        )

    union_after = unary_union([geom for _, geom in reconciled])
    gap_after = metric_area_km2(basin.difference(union_after))
    outside_after = metric_area_km2(union_after.difference(basin))
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
        basin=basin,
        basin_area_km2=metric_area_km2(basin),
        gap_before_km2=gap_before,
        overlap_before_km2=overlap_before,
        outside_before_km2=outside_before,
        face_count=len(faces),
        gap_face_count=gap_faces,
        area_changes_km2=area_changes,
    )
