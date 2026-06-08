# Reporte Organizado (Canónico)

Esta carpeta concentra una salida limpia y mantenible del reporte integrado.

## Estructura

- `index.html`: reporte final unificado.
- `assets/satellite/`: figuras provenientes de `results/satellite/figures` (prioridad por nombre de archivo).
- `assets/insitu/`: insumos no disponibles en satélite (principalmente profundidad/in-situ).
- `assets/comparaciones/`: paneles de comparación satelital vs in-situ.
- `assets_manifest.json`: trazabilidad archivo-a-archivo (origen -> destino).

## Criterios aplicados

1. Se eliminaron rutas mezcladas (`figuras_v1/` y `figuras_reciente/`) y se unificó el reporte con rutas relativas canónicas.
2. Se priorizaron imágenes existentes en `results/satellite/figures` para mapas y análisis.
3. Se mantuvieron en `assets/insitu/` únicamente los archivos no disponibles en satélite.
4. Se agregó contenido real en la sección de comparaciones (panel espacial) con 6 figuras.
5. Se deshabilitó la edición/comentarios en el HTML final.

## Recomendación operativa

Mantener este folder como referencia de publicación y tratar los demás reportes como fuentes de trabajo/intermedios.
