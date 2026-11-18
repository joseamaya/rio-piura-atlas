# 17 · Licencias y reutilización de SENAMHI, INGEMMET y ZEE Piura

Actualizado: 2026-11-18.

Este documento registra evidencia, no dictamina derechos. Distingue **acceso**,
**consulta**, **descarga técnica**, **reutilización**, **redistribución** y
**publicación de derivados**. La ausencia de una licencia explícita se registra
como **no declarada**: no se interpreta como permiso irrestricto ni como
prohibición automática.

## 1. Cómo leer la matriz

- **Acceso:** la página o el servicio se puede abrir sin credenciales.
- **Consulta:** se puede leer el dato en el visor o en la respuesta.
- **Descarga técnica:** se puede obtener una copia (JSON, GeoJSON, PDF, etc.).
- **Reutilización:** se puede usar para un análisis propio.
- **Redistribución:** se puede volver a publicar el dato original.
- **Publicación de derivados:** se puede publicar una tabla, mapa o capa
  producida a partir del dato.
- **Publicación en el atlas:** el atlas puede incluir el dato o un derivado en
  `web/public` con su licencia visible.

## 2. SENAMHI — API histórica por estación

**Evidencia**

- Términos y condiciones:
  `https://www.senamhi.gob.pe/?p=terminos-condiciones` (consultado 2026-11-18).
- La página declara: «La Información y Contenidos a los que el usuario puede
  acceder en la página web son de acceso público y gratuito. El usuario puede
  utilizar la información para realizar acciones con o sin fines de lucro,
  siempre aceptando la obligación de reconocer de manera expresa que el SENAMHI
  es el propietario de la información...».
- También declara: «Queda prohibido que la información a la que se accede pueda
  ser modificada en su contenido para luego ser presentada como información
  oficial emitida por el Servicio Nacional de Meteorología e Hidrología del
  Perú...».
- Y: «El usuario no adquiere ningún derecho de propiedad intelectual por el
  simple uso de los Servicios, Contenidos e Información... y en ningún momento
  dicho uso será considerado como una autorización ni licencia para utilizar los
  Servicios, Contenidos e Información con fines distintos a los que se contemplan
  en los presentes Términos...».
- La API no publica una licencia específica distinta de esos términos.

**Lectura**

- Acceso: sí.
- Consulta: sí.
- Descarga técnica: sí, la API responde sin credenciales.
- Reutilización: el texto permite usar la información con atribución, pero no
  aclara si esa autorización cubre la API y la creación de derivados.
- Redistribución del JSON crudo: **no declarada**.
- Publicación de derivados: **no declarada**; el texto exige no presentar
  información modificada como oficial y no concede una licencia para fines
  distintos.
- Estado en el atlas: **bloqueada**. No hay series de SENAMHI en `web/public`.
  Cualquier publicación requiere confirmación escrita.

**Preguntas para SENAMHI**

1. ¿Los términos de la web se aplican también a la API
   `/api/researchers/historical-download`?
2. ¿Se permite redistribuir el JSON crudo por estación?
3. ¿Se permite publicar una tabla derivada (cobertura, promedios, series
   agregadas) con atribución?
4. ¿Qué leyenda de atribución exacta debe usarse?
5. ¿Se puede publicar una serie derivada bajo CC BY 4.0 o se requiere otra
   licencia?

## 3. INGEMMET — GEOCATMIN

**Evidencia**

- Licencia de descarga:
  `https://geocatminapp.ingemmet.gob.pe/descarga?id=8&str=GEO_INGEEX`
  (consultado 2026-11-18).
- Título: **«Licencia para Uso No Comercial»**.
- Texto de datos: «Datos.- La utilización, traducción y creación de obras
  derivadas del sistema y datos, están autorizadas, a condición de que se “CITE
  AL INGEMMET” como fuente original, ya sea de información contenida en medio
  físico o virtual (GEOCATMIN - http://geocatmin.ingemmet.gob.pe)».
- Texto de software: «Software.- Se prohíbe la reproducción, modificación,
  adaptación, mantenimiento, corrección de errores, cesión, venta, arriendo,
  préstamo, cesión de uso ni parcial ni total, transmisión del derecho de uso;
  salvo autorización expresa del INGEMMET».
- El WFS declara `Fees=1` y `AccessConstraints=referencial`; no es una licencia.
- El catálogo IDEP no contiene un registro del servicio
  `SERV_GEOLOGIA_100K_INTEGRADA`; el registro más cercano
  (`0cc58287-29e0-415c-bf19-63bb1f51c59a`) no enlaza WFS/WMTS.

**Lectura**

- Acceso: sí.
- Consulta: sí.
- Descarga técnica: sí para el visor/descarga; la extracción por ArcGIS REST es
  técnicamente posible.
- Reutilización: autorizada para los datos, con cita, pero bajo una licencia
  **no comercial**.
- Redistribución: el texto autoriza la creación de obras derivadas con cita; no
  autoriza expresamente la redistribución del dato original ni el uso comercial.
- Publicación de derivados: autorizada con cita, pero **no comercial**.
- Estado en el atlas: **bloqueada**. El atlas es CC BY 4.0, que permite uso
  comercial. Publicar una capa derivada de INGEMMET bajo esa licencia sería
  incompatible sin una decisión separada.

**Preguntas para INGEMMET**

1. ¿La «Licencia para Uso No Comercial» se aplica a los servicios WFS/WMTS o
   solo a las descargas del portal?
2. ¿El atlas divulgativo sin venta directa califica como uso no comercial?
3. ¿Se puede publicar una capa derivada bajo CC BY-NC 4.0 o se requiere
   autorización expresa?
4. ¿Qué formato de cita exige la licencia?
5. ¿Se puede obtener el registro ISO 19115 del servicio y su licencia?
6. ¿Qué significa `Fees=1` en el WFS?

## 4. ANA — servicios de cuenca

La capa de cuenca y subcuencas de ANA ya está publicada en el atlas con
atribución. Su ficha (`ana-subcuencas`) declara «dato público; verificar términos
de reutilización». En esta auditoría **no se localizó una página de términos
específica del Geoservidor de ANA**; la licencia sigue **no declarada**. No se
cambia el uso actual ni se crea un derivado nuevo. Si se reutiliza una capa nueva
de ANA, se aplica la misma compuerta: confirmar licencia, escala, fecha y método.

## 5. ZEE Piura — Gobierno Regional de Piura / MINAM

**Evidencia**

- Memoria Final 2012:
  `https://sinia.minam.gob.pe/metadatos/295867` y
  `https://sinia.minam.gob.pe/sites/default/files/sinia/archivos/public/docs/estudio_de_la_propuesta_de_zee_7.pdf`.
- La Memoria no declara licencia de reutilización.
- El servicio del Geoservidor no declara `serviceDescription`,
  `copyrightText`, fecha, escala, método ni licencia.
- La capa `Peligro Inundación` usa el campo `Nivel_Vuln`; la capa
  `Vulnerabilidad frente a Inundaciones` también. La semántica no está resuelta.

**Lectura**

- Acceso: sí.
- Consulta: sí.
- Descarga técnica: la Memoria es descargable; las capas se pueden consultar.
- Reutilización: **no declarada**.
- Redistribución: **no declarada**.
- Publicación de derivados: **no declarada**.
- Estado en el atlas: **bloqueada**. No se usa como peligro ni probabilidad.

**Preguntas para el Gobierno Regional de Piura / MINAM**

1. ¿Qué licencia se aplica a la Memoria Final 2012 y a las capas del
   Geoservidor?
2. ¿Qué representa exactamente `Nivel_Vuln` en la capa «Peligro Inundación»?
3. ¿La capa de 78 polígonos corresponde al submodelo de peligro o al de
   vulnerabilidad?
4. ¿La capa de 19 polígonos es la vulnerabilidad por exposición?
5. ¿La ZEE fue aprobada por Ordenanza Regional? ¿Cuál?
6. ¿Se puede publicar una capa derivada con atribución al Gobierno Regional de
   Piura y al MINAM?

## 6. Matriz resumida

| Fuente | Acceso | Consulta | Descarga | Reutilización | Redistribución | Derivados | Estado atlas |
|---|---|---|---|---|---|---|---|
| SENAMHI histórico | sí | sí | sí | con atribución, alcance por confirmar | no declarada | no declarada | **bloqueada** |
| INGEMMET GEOCATMIN | sí | sí | sí | sí, no comercial y con cita | no declarada | sí, no comercial y con cita | **bloqueada** |
| ZEE Piura | sí | sí | Memoria sí; capas por servicio | no declarada | no declarada | no declarada | **bloqueada** |
| ANA cuenca (contexto) | sí | sí | sí | uso actual con atribución | no declarada | capas actuales ya publicadas | se mantiene como está |
| Copernicus EMSR199 | sí | sí | sí | sí, con atribución | sí, con atribución | sí, con atribución | ya publicada, no se toca |

## 7. Decisión de la fase 2.2

1. No se publica ninguna serie de SENAMHI.
2. No se publica ninguna capa de INGEMMET.
3. No se publica ninguna capa de la ZEE Piura.
4. `data/sources.yml` marca estas fuentes con `publicacion: bloqueada`, y
   `etl/check_data.py` impide que una capa publicada use una fuente bloqueada.
5. La decisión se revisa solo con una respuesta institucional o una decisión
   explícita de licencia del proyecto.

## 8. Nota

Esta ficha no es asesoría legal. Cita la evidencia disponible y formula las
preguntas que necesitan confirmación. Si una institución confirma una licencia,
se actualizan `data/sources.yml`, `LICENSES/DATOS.md` y este documento en el
mismo cambio.
