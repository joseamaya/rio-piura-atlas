# UI-01 · Propuesta visual

Documentación de la auditoría y la propuesta de rediseño del Atlas del río Piura, versión 0.2.3.

| Documento | Contenido |
|---|---|
| [01-auditoria-visual.md](01-auditoria-visual.md) | Hallazgos, evidencia, impacto y prioridad |
| [02-direccion-de-arte.md](02-direccion-de-arte.md) | Concepto, paleta, tipografía, componentes y accesibilidad |
| [03-propuesta-redisenio.md](03-propuesta-redisenio.md) | Propuesta página por página |
| [04-plan-implementacion.md](04-plan-implementacion.md) | Fases, riesgos y criterios de aceptación |
| [06-estabilizacion-accesibilidad.md](06-estabilizacion-accesibilidad.md) | Foco, teclado, panel móvil y semántica del mapa (UI-02) |
| [07-qa-responsive.md](07-qa-responsive.md) | Cinco resoluciones, canvas, orientación y rendimiento (UI-02) |
| [08-coherencia-3d.md](08-coherencia-3d.md) | Paleta del GLB y propuesta de reexportación (UI-02) |
| [evidencia/](evidencia/) | Capturas del estado actual, de la QA `ui02-*`, de la fase 2 (`fase2-*`) y de la fase 2.1 (`fase2-1-*`) |

**Prototipos:** [`../../design-proposal/index.html`](../../design-proposal/index.html)

**Cómo revisar:**

```bash
python3 -m http.server 4330
# http://127.0.0.1:4330/design-proposal/index.html
```

**Estado:** rediseño aplicado en producción local: fundamentos, portada, mapa, Escenarios, Fuentes y maqueta 3D. UI-02 estabilizó el foco, el panel móvil, la semántica del mapa y el QA responsive; la coherencia cromática del GLB queda documentada y pendiente de una reexportación aprobada. Las decisiones pendientes están en el §10 del documento 03, en el §10 del documento 04 y en el documento 08.

La propuesta no modifica datos ni geometrías. Los mockups de `design-proposal/` siguen siendo la referencia visual de la fase completa.
