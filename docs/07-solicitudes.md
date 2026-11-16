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

Actualizar esta tabla al enviar y al recibir cada respuesta.
