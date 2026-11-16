# Río Piura Atlas — instrucciones para agentes

Atlas **divulgativo** de la cuenca del río Piura. No es un sistema de alerta ni un
modelo hidráulico: no pronostica, no calcula manchas nuevas y no reemplaza a SENAMHI,
ANA, INDECI ni al ENFEN.

## Reglas de trabajo

1. **Nada se publica sin fuente.** Toda capa, cifra y rótulo apunta a un `id` de
   `data/sources.yml`. Si no hay fuente, se escribe «no hay dato público».
2. **Lo interpretado se marca.** Lo reconstruido a mano va como interpretación, con
   estilo propio y nota visible.
3. **No inventar geometría.** Si falta el polígono, no se dibuja una aproximación
   silenciosa.
4. **No prometer precisión que el dato no tiene.** Toda cifra lleva unidad, fecha y
   límite conocido (resolución, escala, método).
5. **Los datos pesados no van a Git.** `data/raw/` y `data/processed/` van ignorados
   salvo los JSON de origen; lo publicado vive en `web/public/data/`.
6. **Commits en imperativo y en español**, un cambio lógico por commit.

## Comandos

```bash
# capas y relieve (necesita el DEM del laboratorio; ver PIURA_DEM)
python3 etl/build_layers.py
python3 etl/build_cortes.py

# validación (lo mismo que corre el CI)
python3 etl/check_data.py
python3 -m unittest discover -s etl/tests -v

# sitio
cd web && npm install && npm run dev     # http://localhost:4321
cd web && npm run build                  # estático en web/dist
```

Variables útiles:

- `PIURA_DEM` — ruta al `dem.npz` (por defecto `../blender/projects/piura/data/dem.npz`).
- `SITE_URL` — dominio al compilar (por defecto `https://example.org`).

## Skills

Las skills se instalan aparte y **no se versionan** (`.agents/skills/` está ignorado).
El entorno se restaura desde `skills-lock.json`:

```bash
npx skills install          # restaura las 4 skills del lock
npx skills list             # verifica
```

Instaladas: `blender-export`, `blender-web-pipeline`, `threejs-webgl`,
`web-design-guidelines`. Para añadir otra:

```bash
DISABLE_TELEMETRY=1 npx skills add <owner/repo> -s <skill> -a opencode -y --copy
```

Las skills de Blender asumen un MCP que aquí está apagado: úsalas como guía de
método, no como herramientas.

## Mapa del repositorio

| Ruta | Qué hay |
|---|---|
| `docs/00`–`08` | alcance, fuentes, metodología, datos, glosario, citación, solicitudes, pendientes |
| `data/sources.yml` | registro maestro; es la fuente de verdad de la trazabilidad |
| `etl/` | descarga, construcción de capas, cortes, validación y pruebas |
| `web/` | Astro + MapLibre + Three.js (sitio estático) |
| `LICENSES/` | licencia por fuente y semáforo de redistribución |

## Criterio de calidad

Antes de dar algo por terminado: `check_data.py` en verde, `npm run build` sin errores
y una captura real de la página afectada. Una compilación correcta no demuestra que se
vea bien.
