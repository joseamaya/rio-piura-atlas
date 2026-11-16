# Cómo contribuir

## Regla número uno

**Nada entra al atlas sin fuente.** Si no hay fuente, se escribe «no hay dato
público» y se abre una tarea en `docs/07-solicitudes.md`.

## Antes de agregar una capa

1. Añadir la fuente a `data/sources.yml` con `id`, institución, escala, fecha y
   licencia.
2. Declarar en `docs/03-metodologia.md` cómo se transformó el dato.
3. Registrar la licencia en `LICENSES/DATOS.md`.
4. Verificar el área o la cifra contra la fuente original.

## Estilo

- Español claro, frases cortas.
- Sin adjetivos de marketing.
- Cifras con unidad y fecha.
- Incertidumbre explícita: «aproximado», «sin dato», «interpretación».

## Revisión

Toda capa se revisa por una segunda persona antes de publicarse. La revisión
comprueba:

- que la geometría sea válida y cierre;
- que el área coincida con la declarada por la fuente;
- que la atribución esté visible en pantalla;
- que el texto no prometa más de lo que el dato permite.

## Lo que no se acepta

- Capturas de mapas sin georreferenciar.
- Datos sin licencia clara copiados al repositorio.
- Pronósticos, alertas o recomendaciones de evacuación.
- Rótulos que sugieran precisión inexistente.
