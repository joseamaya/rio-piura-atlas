# 00 · Plan de fase 0

**Objetivo:** decidir qué se puede afirmar, con qué datos y con qué esfuerzo, antes de
escribir una línea de la aplicación.

**Duración estimada:** 3–4 semanas. **Entregable:** este repositorio documentado y una
lista de fuentes con estado real.

## Semana 1 · Alcance y audiencia

- [x] Cerrar las preguntas que responde el atlas (`01-alcance.md`).
- [ ] Definir los tres públicos y una prueba de lectura con una persona de cada uno.
- [x] Acordar qué **no** se hará (alerta, modelamiento propio).
- [x] Fijar criterios de éxito medibles.

## Semana 2 · Auditoría de fuentes

- [x] Completar `data/sources.yml` con todas las fuentes candidatas.
- [x] Verificar cuáles son descargables, con qué licencia y a qué escala.
- [x] Separar lo que existe de lo que hay que pedir.
- [ ] Enviar las solicitudes (`07-solicitudes.md`) y registrar expedientes.
- [x] Anotar contradicciones entre fuentes (áreas, longitudes, cotas).

## Semana 3 · Prototipo de datos

- [x] Integrar en `data/processed/` las capas ya disponibles: cuenca, subcuencas,
      red, relieve y cortes.
- [ ] Integrar las obras conocidas (pendiente del inventario de ANA / PECHP).
- [x] Medir el peso y la viabilidad técnica (COG, PMTiles).
- [x] Probar un corte transversal sobre el DEM y documentar sus límites.
- [ ] Reconstruir la mancha de 2017 con Sentinel-1/2, si el resultado es defendible.

## Semana 4 · Decisión y publicación

- [ ] Revisar el prototipo con alguien externo (docente, periodista o técnico).
- [ ] Decidir si se pasa a fase 1 y con qué alcance.
- [ ] Publicar `v0.1.0` del repositorio (solo documentación y datos de prueba).
- [x] Escribir la lista de pendientes para la fase 1 (`08-pendientes.md`).

## Puertas de decisión

| Pregunta | Si la respuesta es no… |
|---|---|
| ¿Hay fuentes suficientes para responder las cinco preguntas? | reducir alcance a tres |
| ¿Alguna fuente clave está restringida? | declarar el límite en el atlas |
| ¿Se puede reconstruir 2017 con datos libres? | mostrar solo mapas oficiales citados |
| ¿Hay socio institucional? | mantener el tono divulgativo y no entrar en hidráulica |

## Riesgos de la fase

1. **Dependencia de solicitudes**: pueden tardar meses. Mitigación: avanzar con datos
   libres y dejar la capa «pendiente» visible.
2. **Sobreventa**: que el resultado se lea como alerta. Mitigación: avisos permanentes.
3. **Dispersión**: querer cubrir toda la cuenca con detalle urbano. Mitigación: escalas
   declaradas en `01-alcance.md`.
