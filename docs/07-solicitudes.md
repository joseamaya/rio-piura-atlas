# 07 · Solicitudes de información

## Base legal

En Perú, la **Ley N.° 27806 (Transparencia y Acceso a la Información Pública)** obliga
a las entidades del Estado a responder solicitudes de información pública en **diez
días hábiles**, prorrogables por cinco más de forma excepcional. Cualquier persona
puede solicitarla, sin necesidad de justificar el motivo.

Canales: mesa de partes de la entidad, portal `gob.pe` o la Plataforma de Atención al
Ciudadano. Conviene registrar la solicitud con número de expediente.

## Reglas para que funcionen

1. Pedir **datos**, no «información sobre el río».
2. Nombrar el **formato** (CSV, Excel, shapefile, GeoPackage).
3. Delimitar **periodo** y **estaciones**.
4. Pedir **diccionario de campos** y metadatos.
5. Indicar correo para notificaciones.
6. Anotar número de expediente y fecha en la tabla de seguimiento.

## Plantilla · datos hidrológicos (SENAMHI / ANA)

> **Asunto:** Solicitud de acceso a información pública — datos hidrológicos de la
> cuenca del río Piura
>
> Yo, [NOMBRE], identificado con DNI [NÚMERO], con domicilio en [DIRECCIÓN], solicito
> en virtud de la Ley N.° 27806:
>
> 1. Series de caudales medios diarios y niveles de agua de las estaciones
>    [ESTACIÓN 1], [ESTACIÓN 2], [ESTACIÓN 3], para el periodo [AÑO INICIO]–[AÑO FIN],
>    en formato CSV o Excel.
> 2. Diccionario de variables y metadatos de las series (datum, unidad, estado de
>    calidad de cada registro).
> 3. Documento técnico de máximas avenidas vigente para la cuenca, con anexos.
>
> Señalo como domicilio electrónico [CORREO] para las notificaciones.

## Plantilla · cartografía y obras (ANA / PECHP)

> **Asunto:** Solicitud de acceso a información pública — cartografía de la cuenca
> del río Piura
>
> Yo, [NOMBRE], con DNI [NÚMERO], solicito:
>
> 1. Cartografía de inundaciones históricas de 1983 y 1998 en formato shapefile o
>    GeoPackage, con metadatos. (La de 2017 se trabaja con el vector público de
>    Copernicus EMSR199.)
> 2. Inventario de infraestructura hidráulica (diques, bocatomas, canal Daniel
>    Escobar, represa de Poechos) con coordenadas y año de construcción.
> 3. Estudios de batimetría del cauce disponibles, con fecha de levantamiento.
> 4. Informes de operación de la represa de Poechos del periodo 2010–2025.
>
> Domicilio electrónico: [CORREO].

## Pedidos específicos de la auditoría v0.2.1

Estos son los datos que aún no están en el catálogo. No se envían automáticamente:
requieren firma, datos personales y registro de expediente.

| Dato | Entidad | Pedido concreto | Uso |
|---|---|---|---|
| Fecha exacta del pico de 1998 | SENAMHI | Serie de caudales medios diarios y niveles de Puente Sánchez Cerro, 01/01/1998–31/12/1998, con hora del máximo instantáneo | Resolver la discrepancia 12 vs 16 de marzo |
| Duración del episodio de 1983 | SENAMHI | Serie diaria de caudales y niveles, 01/01/1983–31/12/1983 | Documentar duración y volumen |
| La Niña 2023 | SENAMHI / ANA | Informe hidrológico, área y volumen, fechas de formación y desborde | Sustituir la nota de prensa por una medición |
| Vaso de Poechos y eje del canal Daniel Escobar | PECHP / ANA | Shapefile o GeoPackage con metadatos, escala y fecha de levantamiento | Dejar de usar punto y recta de referencia |
| Manchas de 1983 y 1998 | ANA / INDECI | Cartografía vectorial con metadatos y método | Publicar geometrías históricas |
| Informe ENFEN concreto | ENFEN | Edición exacta de los informes 1982-83, 1997-98 y 2017, con páginas | Sustituir la ficha genérica |
| Documento UDEP exacto | Universidad de Piura | Tesis o informe que sustente los picos de 3 200 y 4 424 m³/s | Dejar de usar un handle genérico |

## Pedidos específicos de las fases 2 y 2.1

Estos pedidos nacen de la auditoría de fuentes de 2026. No se han enviado: faltan
firma, datos personales y registro de expediente.

| Dato | Entidad | Pedido concreto | Uso |
|---|---|---|---|
| Licencia de PISCOp v3.0 | SENAMHI | Confirmación escrita de la licencia de los NetCDF de PISCOp v3.0 (Figshare declara GPL 3.0+; el artículo aclara que el código es GPL y los datos CC BY) | Publicar o no una serie derivada por subcuenca |
| Términos de la API histórica | SENAMHI | Condiciones de reutilización de las series diarias por estación y del reporte PDF | Publicar o no la tabla de estaciones |
| Metadatos de INGEMMET | INGEMMET | Escala, fecha, licencia y metodología de las capas vectoriales de geología, geomorfología y susceptibilidad | Evaluar capas candidatas |
| Metadatos de la ZEE Piura | ANA / MINAM | Estudio ZEE Piura, fecha, escala, método y licencia de la capa Peligro Inundación | Evaluar la capa candidata |
| Topobatimetría 2026 | PECHP | Archivo, método, fecha, cobertura y secciones del levantamiento topobatimétrico del río Piura | Superponer batimetría al DEM y documentar capacidad |
| Carta Geológica de Piura | INGEMMET | Shapefiles de las hojas 1:100 000 que cubren la cuenca, con metadatos, CRS y licencia | Geología superficial y geomorfología |
| Ejes de canales y diques | ANA / PECHP | Geometrías oficiales de canal Daniel Escobar, Chutuque, drenes, diques y bocatomas, con año y estado | Dejar de usar rectas de referencia |
| Coordenadas de la inspección 2026 | PECHP / ANA | Puntos, mapas y fichas técnicas de Tapa de Cuy, La Niña, Virrilá, puente de Bayóvar y Chutuque | Georreferenciar el registro documental |
| Serie diaria 2017 y 2023 | SENAMHI | Caudales y niveles diarios de Puente Sánchez Cerro y estaciones del Bajo Piura | Comparar con PISCO y con las notas de prensa |
| Serie diaria 1983 y 1998 | SENAMHI | Caudales y niveles diarios, con hora del máximo instantáneo | Resolver la fecha de 1998 y la duración de 1983 |
| Cartografía vectorial 1983/1998 | ANA / INDECI | Manchas oficiales en shapefile o GeoPackage, con metadatos y método | Publicar geometrías históricas |

## Seguimiento

| # | Entidad | Pedido | Fecha | Expediente | Estado | Respuesta |
|---|---|---|---|---|---|---|
| 1 | SENAMHI | caudales diarios 1983/1998 | — | — | pendiente | — |
| 2 | ANA | cartografía de inundación 1983/1998 | — | — | pendiente | — |
| 3 | PECHP | operación y geometría de Poechos/canal | — | — | pendiente | — |
| 4 | CENEPRED | escenarios de riesgo | — | — | pendiente | — |
| 5 | ANA | informe hidrológico La Niña 2023 | — | — | pendiente | — |
| 6 | ENFEN | informe técnico concreto | — | — | pendiente | — |
| 7 | UDEP | documento exacto de contraste | — | — | pendiente | — |
| 8 | SENAMHI | licencia de PISCOp v3.0 | — | — | pendiente | — |
| 9 | PECHP | topobatimetría 2026 | — | — | pendiente | — |
| 10 | INGEMMET | shapefiles de la Carta Geológica de Piura | — | — | pendiente | — |
| 11 | ANA / PECHP | ejes de canales, diques y bocatomas | — | — | pendiente | — |
| 12 | PECHP / ANA | coordenadas de la inspección de 2026 | — | — | pendiente | — |
| 13 | SENAMHI | series diarias 2017 y 2023 | — | — | pendiente | — |
| 14 | SENAMHI | términos de la API histórica por estación | — | — | pendiente | — |
| 15 | INGEMMET | metadatos y licencia de las capas vectoriales | — | — | pendiente | — |
| 16 | ANA / MINAM | metadatos y licencia de la ZEE Piura | — | — | pendiente | — |

Actualizar esta tabla al enviar y al recibir cada respuesta.
