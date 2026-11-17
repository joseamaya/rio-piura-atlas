# Licencias de código y dependencias

El código propio de este repositorio se publica bajo la licencia MIT del archivo
[`../LICENSE`](../LICENSE). Las dependencias y binarios de terceros conservan su
licencia original.

| Componente | Licencia | Uso en el atlas |
|---|---|---|
| Three.js | MIT | motor de la maqueta 3D |
| Draco decoder (`draco_wasm_wrapper.js`, `draco_decoder.wasm`) | Apache 2.0 | descompresión del GLB de la maqueta |
| Newsreader | SIL Open Font License 1.1 | tipografía editorial |
| Archivo | SIL Open Font License 1.1 | tipografía de interfaz y cartografía |

## Draco

Los archivos de `web/public/draco/` se copian de
`three/examples/jsm/libs/draco/gltf/` (la variante para
`KHR_draco_mesh_compression`). El decodificador forma parte del proyecto
[Draco](https://github.com/google/draco) de Google y se distribuye bajo Apache
License 2.0: <https://github.com/google/draco/blob/master/LICENSE>.

Al actualizar Three.js hay que volver a copiar esos dos archivos desde la misma
versión y comprobar que el GLB sigue cargando. La procedencia y las instrucciones
están en [`../web/README.md`](../web/README.md).

## Tipografías

Newsreader y Archivo se autoalojan en `web/src/fonts/` bajo SIL Open Font License
1.1. Los textos completos y la procedencia están en
[`TIPOGRAFIA.md`](TIPOGRAFIA.md).

## Modelo y datos

El GLB de la maqueta es contenido del atlas (CC BY 4.0) y combina datos de
Copernicus, ANA, HydroRIVERS y OpenStreetMap; sus licencias están en
[`DATOS.md`](DATOS.md).
