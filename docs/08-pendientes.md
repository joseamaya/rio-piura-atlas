# 08 · Pendientes de la fase 2.2

Actualizado: 2026-11-18.

Este documento separa lo que ya está implementado, lo que se puede hacer sin datos
externos y lo que está bloqueado por solicitudes. La regla sigue siendo: **lo que no
tiene fuente, no se dibuja**.

## Implementado

- Capas base: cuenca ANA, 8 subcuencas oficiales + Bajo Piura derivado, red
  HydroRIVERS v1.0 recortada, lagunas y salinas OSM.
- Partición de subcuencas **reconciliada topológicamente**: 0 solapamientos,
  0 superficie fuera y 0 huecos por encima del umbral de 0,01 km². El método y los
  cambios de área están en `data/raw/limits.json → reconciliacion`.
- Mancha oficial de la inundación de marzo de 2017 (Copernicus EMSR199, AOI10 y
  AOI11), con observaciones por fecha, sensor, área original y área simplificada.
- Referencia de Poechos como punto en el dique y del canal Daniel Escobar como recta
  de referencia en el mapa 2D; no se dibujan el vaso, bocatomas ni diques sin geometría.
- Relieve sombreado y maqueta 3D de la cuenca con el desierto y la bahía, exportada con Draco (1,6 MB).
- Cortes transversales de referencia (5) y corte dibujado por el visitante.
- Catálogo de fuentes generado desde `data/sources.yml`, con enlaces por capa.
- **Fase 2:** catálogo ampliado a **49 fuentes**, con `disponibilidad` (7 estados),
  `tipo_evidencia` (10 categorías), periodo, formato, CRS, descarga, limitaciones y
  capas respaldadas.
- **Fase 2:** auditoría individual de las siete fuentes prioritarias y de las
  fuentes complementarias en `docs/11`; catálogo de evidencia en `docs/12`; plan de
  integración en `docs/13`; documento de cuenca baja en `docs/14`.
- **Fase 2:** registro documental de la expedición de 2002, el modelo de Lund de
  2024 y la inspección de 2026 en `/escenarios`, sin geometría nueva.
- **Fase 2:** PISCOp v3.0 catalogado y condicionado a la aclaración de licencia; no
  se publicó ninguna serie derivada.
- **Fase 2.1:** API histórica de SENAMHI catalogada y con ETL reproducible
  (`download_senamhi_historico.py` + `build_senamhi_historico.py`); 20 estaciones
  de Piura. La fase 2.2 verificó 357.524 filas, 0 días faltantes y 0 duplicados,
  pero 7 estaciones sin temperatura y 3 con temperatura parcial. La tabla queda en
  `data/processed/senamhi/` y no se publica hasta confirmar términos.
- **Fase 2.1:** INGEMMET corregido: la Geología Integrada 1:100 000 sí tiene capas
  vectoriales, además de geomorfología, susceptibilidad a inundación y peligros
  geológicos. La fase 2.2 corrigió los conteos: 576 polígonos de geología en 12
  hojas, 573 de geomorfología, 16.341 de susceptibilidad y 230 puntos de peligros;
  los conteos anteriores no se reprodujeron.
- **Fase 2.1:** ZEE Piura catalogada: geología, geomorfología, peligro de
  inundación y vulnerabilidad; 78 y 19 polígonos, respectivamente. La fase 2.2
  localizó la Memoria Final 2012, escala 1:100 000, y documentó que el campo
  `Nivel_Vuln` no permite asignar la semántica sin confirmación del autor.
- **Fase 2.2:** auditoría de SENAMHI con catálogo completo (293 estaciones), 20
  seleccionadas, hashes crudos, cobertura por estación, nulos, huecos, banderas de
  calidad y clasificación geográfica (9 dentro / 11 fuera de la cuenca).
- **Fase 2.2:** auditoría reproducible de INGEMMET y ZEE: metadatos, conteos
  espaciales contra la cuenca, CRS, WFS/WMTS, paginación por OBJECTID, catálogo
  IDEP y licencia de descarga. Se descargó solo el subconjunto de 576 polígonos de
  geología; 1 resultó inválido y no se reparó.
- **Fase 2.2:** licencias documentadas en `docs/17`: SENAMHI sin licencia abierta;
  INGEMMET con licencia no comercial incompatible con CC BY 4.0; ZEE sin licencia
  declarada. Las fuentes afectadas llevan `publicacion: bloqueada` y
  `check_data.py` impide que una capa publicada las use.
- **Fase 2.2:** 136 pruebas de Python, 3 de integración en vivo opt-in
  (`RUN_LIVE_TESTS=1`); no se ejecutan en CI.
- **Fase 2.1:** mapas históricos de Sullana y Cura Mori catalogados como evidencia
  documental; no hay shapefiles y no se digitalizan.
- Escenarios históricos documentados; la mancha de 2017 usa un vector oficial y
  1983/1998 siguen como texto. Sin manchas inventadas.
- ETL reproducible para capas y cortes.
- Scripts de descarga para ANA, HydroRIVERS, cuerpos de agua OSM y Copernicus
  EMSR199.
- Validación de datos (`etl/check_data.py`) con auditoría por par de subcuencas,
  superficie fuera por subcuenca, huecos por componente, agujeros interiores,
  validación antes de reparar y fidelidad (IoU, diferencia simétrica, Hausdorff,
  media y p95); 136 pruebas de Python (3 de integración en vivo opt-in) y pruebas
  Playwright de mapa, móvil, fallo de red y maqueta.
- Catálogo de fuentes con `certeza` y `tipo`: distingue dato medido, derivado,
  documentado, interpretación y pendiente de verificación.
- CI que compila el sitio y valida datos en cada push.
- Accesibilidad: enlace de salto, foco visible, texto alternativo del mapa y la
  maqueta, movimiento reducido y auditoría automática WCAG A/AA con axe en CI
  (`npm run check:a11y`), sin violaciones en las cinco páginas y el 404.
- Comprobación automática de tipos (`astro check`) y de enlaces/anclas internas en CI.
- Página 404, `robots.txt` y metadatos Open Graph/Twitter.
- `CITATION.cff` con los metadatos de la versión 0.3.0.
- Sitio publicado en GitHub Pages (`https://joseamaya.github.io/rio-piura-atlas/`)
  con despliegue automático desde `main` y comprobaciones previas de tipos, enlaces
  y accesibilidad.

## Desbloqueado

1. **Dominio propio (opcional).** Sustituir `joseamaya.github.io` por un dominio
   definitivo y actualizar `SITE_URL`.
2. **DOI Zenodo.** El release `v0.3.0` se publica sobre esta versión. Falta
   depositarlo en Zenodo y añadir el DOI a `CITATION.cff` y
   `docs/06-como-citar.md`. El tag `v0.2.3` es la versión anterior; `v0.2.2` y
   anteriores corresponden a la fase 1.
3. **Prueba de accesibilidad con personas.** La auditoría automática está limpia;
   falta teclado real, lector de pantalla y prueba con los tres públicos.
4. **Rendimiento futuro.** Migrar a PMTiles/COG si crecen las capas vectoriales.

## Bloqueado por solicitudes

| Dato | Entidad | Uso |
|---|---|---|
| Caudales y niveles diarios | SENAMHI | hidrogramas, duración y fecha exacta de 1998 |
| Licencia de PISCOp v3.0 | SENAMHI | publicar o no una serie derivada |
| Confirmación de términos de la API histórica | SENAMHI | redistribución del crudo y publicación de derivados |
| Cartografía de inundación 1983/1998 | ANA / INDECI | manchas históricas vectoriales |
| Bocatomas, diques y ejes de canales | ANA / PECHP | capa de obras completa |
| Operación de Poechos | PECHP | trasvase y regulación |
| Escenarios de riesgo | CENEPRED / SIGRID | exposición |
| Informe hidrológico de La Niña 2023 | SENAMHI / ANA | área y volumen del evento |
| Informe ENFEN concreto | ENFEN | edición exacta de 1982-83, 1997-98 o 2017 |
| Topobatimetría 2026 | PECHP | secciones y capacidad del cauce |
| Licencia aplicable a WFS/WMTS y compatibilidad con CC BY 4.0 | INGEMMET | publicar geología/geomorfología vectorial |
| Registro ISO 19115 del servicio `SERV_GEOLOGIA_100K_INTEGRADA` | INGEMMET | trazabilidad del servicio |
| Semántica de `Nivel_Vuln` y relación con la Memoria 2012 | Gobierno Regional de Piura / MINAM | publicar o no el peligro/vulnerabilidad ZEE |
| Licencia de la Memoria 2012 y de las capas ZEE | Gobierno Regional de Piura / MINAM | reutilización y derivados |
| Ordenanza Regional de aprobación de la ZEE | Gobierno Regional de Piura | estatus legal del estudio |
| Leyenda completa de susceptibilidad (4 clases) | INGEMMET | publicar o no la susceptibilidad |
| Coordenadas de la inspección 2026 | PECHP / ANA | georreferenciar el registro documental |
| Series diarias 2017 y 2023 | SENAMHI | comparar con PISCO y notas de prensa |

Mientras no lleguen, esas capas se muestran como «sin dato público» y no se dibujan.

## Contradicciones y límites conocidos

- **Área de la cuenca.** La geometría mide **10 938,4 km²** (geodésica). ANA publica
  11 021,8 km² en `Shape_Area`, pero ese campo está calculado en **EPSG:32718 (UTM 18S)**,
  fuera de la zona 17S del polígono; la diferencia no es redondeo. El atlas muestra la
  cifra medida y conserva la oficial como referencia.
- **Bajo Piura.** La capa oficial de subcuencas no publica «Bajo Piura» como polígono
  independiente. El atlas lo calcula como el resto de la cuenca **antes** de simplificar
  y lo atribuye a `bajo-piura-derivado`, no a ANA. Su área medida es **4 752,9 km²**.
  La reconciliación topológica eliminó 0,7828 km² de solapamientos, 1,4725 km² de
  huecos y 0,6747 km² de superficie fuera de la cuenca; no se crea superficie nueva.
  El método, las 374 caras y los cambios de área por subcuenca están en
  `data/raw/limits.json → reconciliacion`. El resultado tiene 0 solapamientos,
  0 superficie fuera y 0 huecos por encima de 0,01 km². La fidelidad también se
  publica: ocho subcuencas cambian más de 0,01 km² entre la fuente y la geometría
  reconciliada, y 1,4725 km² se asignan por proximidad; son **avisos declarados**,
  no errores ocultos. La mayor diferencia de área total es San Francisco
  (−0,2583 km², −0,056 %).
- **Red hídrica.** HydroRIVERS v1.0 incluye tramos que sobresalen de la ventana y de la
  cuenca. `build_layers.py` usa intersección geométrica exacta con el polígono ANA;
  ningún tramo publicado queda fuera (solo el redondeo de 6 decimales, <0,2 m).
- **Poechos y canal Daniel Escobar.** Poechos se publica como **punto en el dique**
  (4°40′07″S, 80°30′13″W, PECHP), no como vaso inventado. El canal es una **recta de
  referencia** Poechos–Curumuy, no su eje oficial; el PECHP documenta 54 km y 70 m³/s.
  No hay geometría oficial publicada del vaso ni del eje: no se dibujan como si lo fueran.
- **Inundación de 2017.** La mancha es el vector oficial de Copernicus EMSR199
  (AOI10 + AOI11), no una reconstrucción propia. Los atributos del vector declaran
  Radarsat Ultra-Fine Beam (26/03) y Cosmo-SkyMed (30/03) para AOI10, y Radarsat
  (26/03) para AOI11. En AOI10, la suma de observaciones es 80,785 + 73,040 =
  153,825 km²; 56,772 km² se observaron en ambas fechas; la unión original es
  97,053 km² y la unión simplificada publicada, 96,507 km². En AOI11, 457,408 km²
  originales y 458,970 km² publicados. Total: 555,477 km² en EPSG:32717. La suma de
  fechas no es una superficie. La ficha del PDF v2 declara Sentinel-1A y el DBF
  declara Radarsat/Cosmo; el atlas usa el DBF y deja la discrepancia visible,
  pendiente de reabrir el PDF. Cubre la llanura baja y el desierto adyacente, no toda la cuenca; el
  total no es una estimación hidráulica ni una extensión simultánea. No se publica una
  clase potencial porque el vector no la trae. El AOI12 Piura North se descartó por
  falta de fecha y sensor en sus registros. Un polígono de AOI10 venía con
  autointersección de anillo; se reparó con `make_valid` y se registró en
  `reparaciones` del GeoJSON, sin descartar componentes.
- **Color del terreno.** La maqueta usa una rampa hipsométrica: el verde indica
  altitud, no cobertura vegetal. La rampa del GLB es más verde que la tinta de
  papel de la lámina 2D. UI-02 no reexportó el modelo ni aplicó un tinte runtime
  para no desajustar los pósteres y los renders; la propuesta de reexportación
  coordinada está en `docs/ui/08-coherencia-3d.md`.
- **Lagunas.** Los polígonos son de OSM; Ramón y Las Salinas figuran como
  intermitentes. La maqueta las pinta como agua permanente por el relato y las sitúa
  a una cota simbólica (+25 m), no a un nivel medido.
- **Rótulos del GLB.** El rótulo de cota «Naciente ~2 700 m» fue retirado del GLB
  regenerado: el DEM en esa posición mide ~1 935 m y el máximo de la ventana es
  3 019 m. «Reserva Nacional Illescas» se conserva como referencia de lugar, no como
  límite oficial; el área protegida no está dibujada. Poechos se rotula en el dique
  real y el canal en su punto medio de referencia.
- **1998: fecha del pico.** SIAR 200 consigna el 12 de marzo en la introducción (p. 1)
  y el 16 de marzo en el análisis de niveles (p. 15). El atlas mantiene la cifra de
  4 424 m³/s y marca la fecha como discrepancia; no elige una sin una fuente adicional.
- **1983: duración.** El pico de 3 200 m³/s del 21 de abril está documentado (SIAR 200
  p. 15; SIAR 204 p. 49), pero no se localizó una duración diaria del episodio.
- **1891: mecanismo.** SIAR registra el cambio de embocadura (p. 5 y 7) y describe el
  mecanismo general de avulsión (p. 9). La tesis de la PUCP quedó como referencia
  secundaria: el repositorio no permitió abrirla en esta auditoría, así que no se usa
  para una afirmación específica. El detalle se marca como interpretación histórica.
- **1998: 161 días.** SIAR 200 consigna un período de 161 días, pero no se verificó con
  una serie diaria; el texto no afirma que el evento durara exactamente 161 días.
- **2023: La Niña.** Andina documenta el desborde y 120 m de carretera destruidos;
  NASA documenta la laguna con Landsat 9. No hay informe hidrológico de SENAMHI/ANA en
  el catálogo; no se publica área ni volumen para 2023. No se localizó una fuente que
  documente un cambio de desembocadura; no se afirma que lo haya habido ni que no lo
  haya.
- **ENFEN, Sentinel-1 y UNOSAT.** ENFEN se usa solo como contexto: falta identificar la
  edición concreta de sus informes. Sentinel-1 no es la fuente del vector publicado; el
  vector EMSR199 se basa en Radarsat/Cosmo según sus atributos. UNOSAT se usa como
  contraste, no como geometría. Las manchas de 1983 y 1998 siguen sin geometría pública
  localizada.

### Límites añadidos en la fase 2

- **PISCOp v3.0.** Es 0,1° (~10 km), 1981–2025, no 5 km ni 1981–2016. El artículo
  es CC BY 4.0, pero el conjunto de datos en Figshare declara GPL 3.0+; no se
  publica una serie derivada hasta aclarar la licencia.
- **Expedición de 2002.** Describe una salida principal por San Pedro, Virrilá como
  segunda salida y Reventazón como tercera salida excepcional. No prueba que las
  tres estuvieran activas a la vez ni que sigan activas. Es una navegación de
  estiaje, no un eje oficial.
- **Inspección de 2026.** La nota titula «libre desembocadura al mar», pero el
  cuerpo verifica el paso del agua en Tapa de Cuy, Virrilá, el puente de Bayóvar y
  Chutuque. No publica coordenadas ni mapas; no se infiere una conexión permanente.
- **INDECI 2009.** El título exacto es *Estudio Mapa de peligros de la ciudad de
  Piura*; Castilla aparece en el capítulo III y en los planos. El estudio separado
  de Castilla de 2001 no se fusiona.
- **INGEMMET.** La Geología Integrada 1:100 000 sí tiene capas vectoriales; la
  Carta Geológica sigue en PDF/JPG. La fase 2.2 verificó 576 polígonos en la
  cuenca, en 12 hojas (10b, 10c, 10d, 11a, 11b, 11c, 11d, 11e, 12b, 12c, 12d y
  12e); la descripción oficial enumera 27 hojas y no coincide con la capa. La
  licencia de descarga es no comercial. No se integra como capa.
- **Gobierno Regional de Piura / MINAM — ZEE Piura.** Tiene geología,
  geomorfología, peligro de inundación y vulnerabilidad vectoriales. La Memoria
  Final 2012 está localizada (255 pp., escala 1:100 000), pero el servicio no
  declara fecha, escala, método ni licencia y el campo `Nivel_Vuln` no permite
  asignar la semántica. No se integra como capa.
- **SENAMHI histórico.** La API por estación cubre 1961–2015 como envolvente; no
  todas las estaciones tienen el mismo intervalo. Siete no tienen temperatura y
  tres la tienen parcial. No incluye caudales ni cubre 2017/2023. No se publica
  el crudo hasta confirmar términos.
- **Susceptibilidad INGEMMET.** La capa vectorial tiene tres clases (2/3/4) y la
  leyenda oficial 2018 tiene cuatro; falta «Muy bajo o nulo». No se publica como
  probabilidad ni como leyenda completa.
- **Conteos INGEMMET.** Los conteos 2.608 / 2.281 / 59.152 / 1.729 de la fase
  2.1 no se reprodujeron con el servicio actual. Los conteos de la cuenca son
  576 / 573 / 16.341 / 230. Los primeros correspondían a otra área o a otra
  fecha; no se usan como cifras de la cuenca.
- **Ruta 2002.** Los 178 puntos GPS están en PSAD56 y son un track de navegación.
  Una reconstrucción exigiría documentar la transformación, el orden y la
  incertidumbre; no se dibuja en esta fase.
- **Mapas 1983/1998.** Existen mapas PDF/JPG de Sullana, Cura Mori y Piura; no hay
  una cobertura vectorial de toda la cuenca. No se digitalizan sin
  georreferenciación, escala y método.

## Criterios para cerrar la fase 1

- Una persona sin formación técnica entiende, en menos de 10 minutos, por qué el río
  no llega al mar.
- Toda capa visible tiene fuente consultable en dos clics.
- La mancha de 2017 declara fuente, fecha, sensores, cobertura y método; las obras
  esquemáticas están marcadas como interpretación.
- El sitio funciona en móvil y con conexión lenta: portada y páginas de texto
  por debajo de 1 MB; `/maqueta` es la excepción declarada por el GLB y la mancha de
  2017 se carga a demanda en `/mapa`.
- Existe una versión etiquetada y citable.

## Criterios de cierre de la fase 2

- Las siete fuentes prioritarias tienen ficha individual y estado de disponibilidad.
- Los documentos descargables están recuperados o se explica por qué no.
- Se revisaron índices, capítulos, tablas y anexos; no solo resúmenes.
- El catálogo no duplica fuentes y distingue disponibilidad, certeza y tipo de
  evidencia.
- PISCO no se publica como serie hasta aclarar su licencia.
- No se agregaron capas geométricas sin escala, licencia y metadatos.
- La ruta de 2002 y la inspección de 2026 quedan como registro documental, no como
  geometría.
- `check_data.py`, las pruebas Python y `npm run verify` pasan.
- La dirección visual «Lámina y margen» no cambia.

## Criterios de cierre de la fase 2.2

- La API histórica de SENAMHI tiene ficha de fuente, ETL, cobertura, calidad y
  hashes.
- La tabla de estaciones queda en `data/processed/`, no en `web/public/`, hasta
  confirmar términos.
- Las capas vectoriales de INGEMMET y ZEE Piura quedan auditadas con conteos de
  la cuenca, escala, fecha, CRS y límites de licencia.
- Los conteos antiguos de INGEMMET quedan corregidos y no se reutilizan.
- La licencia no comercial de INGEMMET y la ausencia de licencia de la ZEE quedan
  documentadas con preguntas institucionales.
- Los mapas de Sullana y Cura Mori quedan como evidencia documental, sin
  digitalización.
- Los pendientes de caudales, batimetría, ejes de infraestructura, vector
  1983/1998 e informe 2023 siguen declarados.
- `check_data.py`, las pruebas Python y `npm run verify` pasan.
- No se agregaron capas al mapa ni se cambió la dirección visual.
