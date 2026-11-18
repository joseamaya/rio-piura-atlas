# 12 · Catálogo de evidencia territorial

Actualizado: 2026-11-17.

Este documento explica cómo se clasifica la evidencia del atlas, cómo se relaciona
con las capas y cómo se registran las incertidumbres. La fuente de verdad operativa
es `data/sources.yml`; este texto es su lectura humana.

## 1. Por qué separar disponibilidad, certeza y tipo de evidencia

Una fuente puede ser oficial y, a la vez, no tener geometría publicable. O puede
ser académica, estar disponible y no ser una medición. Mezclar esas dimensiones
produce dos errores frecuentes:

- llamar «dato» a una interpretación porque viene en un PDF institucional;
- llamar «capa» a un mapa que solo existe como imagen.

El atlas usa tres ejes independientes:

| Eje | Pregunta | Valores |
|---|---|---|
| **Disponibilidad** | ¿Se puede usar o publicar el dato? | `localizada`, `descargable`, `procesada`, `validada`, `documental`, `pendiente`, `descartada` |
| **Certeza** | ¿Qué tan sólido es el dato? | `medido`, `derivado`, `documentado`, `interpretacion`, `por_verificar` |
| **Tipo de evidencia** | ¿Qué clase de registro es? | oficial, académica, científica, histórica, observación satelital, dato medido, reconstrucción cartográfica, modelamiento, prensa/documentación secundaria, colaborativa |

La disponibilidad no es una jerarquía de calidad. Un documento `documental` puede
ser más valioso que una capa `validada` de baja resolución.

## 2. Estados de disponibilidad

| Estado | Significado | Ejemplo |
|---|---|---|
| `localizada` | Se identificó la referencia, pero no se recuperó el archivo o no se verificó su cobertura. | Carta Geológica 1:100 000 de INGEMMET |
| `descargable` | El archivo original está disponible y se puede descargar, pero aún no se procesó. | Reportes diarios del PECHP |
| `procesada` | El archivo pasó por un ETL reproducible, pero aún no completó la validación. | Una serie PISCO por subcuenca, si se autoriza |
| `validada` | Se verificaron cobertura, metadatos, geometría y método; la capa puede publicarse. | Cuenca ANA, mancha 2017, DEM |
| `documental` | La fuente sirve para contextualizar, pero no tiene geometría incorporable o su licencia no permite derivados. | Estudio ANA 2014, INDECI 2009, tesis de Lund |
| `pendiente` | Falta un dato, una licencia, una solicitud o una confirmación. | PISCO v3.0, series SENAMHI, topobatimetría PECHP |
| `descartada` | Se evaluó y no es adecuada para el atlas; se justifica. | Capas de susceptibilidad de otra región |

### Reglas de uso

1. Una capa publicada solo puede referenciar fuentes `validada` o `procesada`.
2. Una fuente `documental` puede sostener texto, una ficha o un registro, pero no
   una geometría publicada.
3. Una fuente `pendiente` no se dibuja; se declara.
4. `descartada` no se usa ni se enlaza como si estuviera disponible.
5. El campo heredado `estado` (`disponible`, `por_solicitar`, `por_verificar`) se
   conserva por compatibilidad; el campo nuevo es `disponibilidad`.

## 3. Tipos de evidencia

| Tipo | Qué es | Cómo se trata | Ejemplos |
|---|---|---|---|
| **Oficial** | Documento o dato de una entidad pública con competencia. | Se cita; no se convierte en capa sin metadatos. | ANA, INDECI, INGEMMET, PECHP, SENAMHI |
| **Académica** | Tesis, artículo o informe universitario. | Se cita; se separan resultados de opiniones. | Lund 2024, PUCP, UDEP |
| **Científica** | Producto de investigación con método explícito. | Se cita con limitaciones y versión. | IMARPE, PISCO, HydroRIVERS |
| **Histórica** | Documento que describe hechos del pasado. | Se distingue hecho, interpretación y vacío. | SIAR, expedición de 2002 |
| **Observación satelital** | Imagen o vector derivado de sensores remotos. | Se declara sensor, fecha, resolución y clase. | Copernicus EMSR199, Landsat, Sentinel-1 |
| **Dato medido** | Serie, aforo o levantamiento. | Se declara estación, unidad, periodo y calidad. | Caudales de Puente Sánchez Cerro |
| **Reconstrucción cartográfica** | Geometría elaborada por el atlas o derivada de otra fuente. | Estilo propio y aviso visible. | Bajo Piura derivado, obras esquemáticas |
| **Modelamiento** | Resultado de un modelo hidráulico o hidrológico. | No es observación ni decisión oficial. | Lund HEC-RAS, PUCP HEC-HMS |
| **Prensa / documentación secundaria** | Nota, crónica o comunicación institucional. | Se usa como registro fechado, no como medición. | Andina 2023, nota PECHP 2026 |
| **Colaborativa** | Dato generado por una comunidad abierta. | Se declara la fuente y su licencia. | OpenStreetMap |

## 4. Relación fuente–capa

| Capa publicada | Fuente principal | Disponibilidad | Qué se declara |
|---|---|---|---|
| `cuenca.geojson` | `ana-subcuencas` | `validada` | Polígono ANA 1:100 000; área medida 10 938,4 km² |
| `subcuencas.geojson` | `ana-subcuencas` + `bajo-piura-derivado` | `validada` | Ocho subcuencas oficiales + Bajo Piura derivado |
| `red_hidrica.geojson` | `hydrorivers` | `validada` | Red derivada ~500 m, recortada a la cuenca |
| `agua.geojson` | `osm-agua` | `validada` | Lagunas y salinas OSM; intermitencia declarada |
| `lugares.geojson` | `osm-lugares` | `validada` | Nodos de localidad, no centroides |
| `relieve.jpg` / `dem_grid` | `copernicus-dem-30` | `validada` | DEM 30 m remuestreado a ~143 m |
| `cortes.geojson` | `copernicus-dem-30` | `validada` | Perfiles de referencia a resolución efectiva |
| `flood_2017.geojson` | `copernicus-ems-emsr199` | `validada` | Unión de observaciones, no mancha simultánea |
| `obras.geojson` | `obras-esquematicas` | `validada` | Punto en el dique y recta de referencia; interpretación |

## 5. Registro de incertidumbres

| Tema | Incertidumbre | Cómo se muestra |
|---|---|---|
| Área de la cuenca | ANA publica 11 021,8 km² en EPSG:32718; la geometría mide 10 938,4 km² en EPSG:32717 | Se muestra la cifra medida y se conserva la oficial como referencia |
| Bajo Piura | No es una subcuenca oficial; se calcula como resto | Se atribuye al atlas, no a ANA; método en `limits.json` |
| DEM | 30 m de producto, malla de trabajo ~143 m | Se declara en la ficha y en los cortes |
| Inundación 2017 | Unión de dos fechas; sensores discrepan entre PDF y DBF | Se publica la unión y se advierte la discrepancia |
| Poechos y canal | No hay geometría oficial del vaso ni del eje | Punto en el dique y recta de referencia; interpretación |
| 1983/1998 | No hay manchas vectoriales oficiales; fecha de 1998 en disputa | Se cuenta con texto y fuente; no se dibuja |
| La Niña | Áreas estimadas con MODIS 500 m; 2023 sin volumen | Se cita la estimación y se declara el vacío |
| PISCO | 0,1° (~10 km), licencia en disputa | No se publica serie; se declara la limitación |
| INGEMMET | Sí hay vector de susceptibilidad a inundaciones para Piura; su leyenda 2018 tiene cuatro clases y la capa vectorial solo tres | No se integra; no se usa como probabilidad |
| ZEE Piura | `Nivel_Vuln` no tiene semántica confirmada; la capa «Peligro Inundación» no usa un campo de peligro | No se integra; queda como referencia documental |
| Inspección 2026 | Sin coordenadas ni mapas; caudales puntuales | Registro documental, no geometría |
| Expedición 2002 | Track GPS de estiaje, no eje oficial | Documento; reconstrucción solo con método explícito |

## 6. Cómo se cita

- Cada afirmación publicada debe apuntar a un `id` de `data/sources.yml`.
- Si la fuente tiene página, se cita la página. Si no, se cita la sección o el
  documento completo.
- Las cifras llevan unidad, fecha y límite conocido.
- Las fuentes que discrepan se muestran; no se promedian.
- Las figuras y mapas de terceros no se reutilizan sin permiso. Se enlazan.
- Las reconstrucciones propias se marcan como `interpretacion` o
  `reconstruccion_cartografica` y llevan aviso visible.

## 7. Cómo se añade una fuente

1. Verificar que no exista una ficha duplicada.
2. Completar los campos obligatorios de `data/sources.yml`.
3. Añadir `disponibilidad` y `tipo_evidencia`.
4. Declarar `periodo`, `formato`, `crs`, `descarga` y `limitaciones` cuando
   correspondan.
5. Registrar la licencia en `LICENSES/DATOS.md`.
6. Si la fuente sostiene una capa, añadir su `id` en `capas` y verificar que la
   capa la referencie.
7. Ejecutar `python3 etl/check_data.py` y las pruebas.
8. Actualizar `docs/11` si la fuente es nueva o cambió de estado.

## 8. Lo que este catálogo no hace

- No convierte un PDF en una capa.
- No digitaliza mapas sin escala, georreferenciación y método.
- No usa una fuente `pendiente` para rellenar un vacío.
- No confunde una propuesta con una obra ejecutada.
- No confunde susceptibilidad geológica con probabilidad hidrológica.
- No presenta un modelo académico como decisión oficial.

## 9. Fuentes de la segunda ronda (fase 2.1)

La búsqueda agresiva de 2026-11-17 añadió fuentes que no estaban en la primera
fase. Ninguna se publicó como capa.

| Fuente | Tipo de evidencia | Disponibilidad | Uso |
|---|---|---|---|
| `senamhi-historico-estaciones` | oficial + dato medido | `descargable` | Precipitación/temperatura diaria por estación; envolvente 1961–2015; 7 sin temperatura; no caudales; publicación bloqueada |
| `ingemmet-geologia-integrada-100k` | oficial + científica | `descargable` | Geología vectorial 1:100 000; 576 polígonos en la cuenca; licencia no comercial |
| `ingemmet-geomorfologia-vector` | oficial + científica | `descargable` | Geomorfología vectorial; 573 polígonos en la cuenca; escala contradictoria |
| `ingemmet-susceptibilidad-inundacion-vector` | oficial + científica | `descargable` | Susceptibilidad a inundación; 16.341 polígonos; leyenda incompleta; 1:1 000 000 |
| `ana-zee-piura` | oficial | `descargable` | Geología, geomorfología, peligro (78) y vulnerabilidad (19); `Nivel_Vuln` ambiguo |
| `zee-piura-memoria-2012` | oficial + científica | `documental` | Memoria Final 2012, 255 pp., escala 1:100 000 |
| `sigrid-sullana-inundacion-1983-1998` | oficial + histórica | `documental` | Mapas PDF de Sullana 1983/1998 |
| `sigrid-cura-mori-riesgo-1998` | oficial + histórica | `documental` | 34 mapas JPG de Cura Mori 1998 |
| `sigrid-piura-peligros-inundacion` | oficial + histórica | `documental` | Mapas PDF de peligros urbanos |
| `pechp-batimetria-poechos` | oficial | `pendiente` | Batimetría del reservorio, no del cauce |

La regla sigue siendo la misma: una fuente `documental` no se convierte en capa; una
fuente `localizada` no se publica hasta confirmar licencia, escala y fecha; una
fuente `pendiente` no se dibuja.
