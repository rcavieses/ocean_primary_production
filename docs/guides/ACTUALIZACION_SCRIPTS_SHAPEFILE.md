# Actualización de Scripts con Filtrado Shapefile - COMPLETADO ✅

**Fecha**: 3 Marzo 2026
**Estado**: Todos los scripts actualizados correctamente

## Resumen de cambios

Se han actualizado todos los 6 scripts principales para aplicar el filtrado espacial usando el polígono del shapefile del Golfo de California. Esto mejora la precisión espacial al excluir puntos fuera de la región de estudio.

## Scripts actualizados (6 Total)

### 1. **Scripts de MAPAS** (con `drop=False` - enmascarar datos)

#### ✅ [plot_pft_maps.py](scripts/plot_pft_maps.py)
- **Cambio**: Agregó `mask = get_gulf_of_california_filter(ds, use_shapefile=True)`
- **Filtrado**: `data_mean = data_mean.where(mask, drop=False)`
- **Efecto**: Los mapas muestran solo el polígono del Golfo de California

#### ✅ [plot_pft_quinquennial_maps.py](scripts/plot_pft_quinquennial_maps.py)
- **Cambio**: Agregó creación del mask y aplicación por período quinquenal
- **Filtrado**: `data_period = data_period.where(mask, drop=False)` 
- **Efecto**: Mapas de 5 períodos muestran solo la región del Golfo

#### ✅ [plot_pft_quinquennial_diff.py](scripts/plot_pft_quinquennial_diff.py)
- **Cambio**: Modificó función `compute_quinquennial_mean()` para aceptar parámetro `mask`
- **Filtrado**: `data_period = data_period.where(mask, drop=False)`
- **Efecto**: Diferencias calculadas solo sobre puntos dentro del polígono

### 2. **Scripts de SERIES DE TIEMPO** (con `drop=True` - eliminar datos)

#### ✅ [plot_pft_monthly_timeseries.py](scripts/plot_pft_monthly_timeseries.py)
- **Cambio**: Agregó `mask = get_gulf_of_california_filter(ds, use_shapefile=True)`
- **Filtrado**: `data = data.where(mask, drop=True)`
- **Efecto**: Series de tiempo usan solo datos dentro del polígono del Golfo

### 3. **Scripts con ESTADÍSTICAS PRE-COMPUTADAS** (datos ya filtrados)

#### ✅ [plot_pft_monthly_with_indices_optimized.py](scripts/plot_pft_monthly_with_indices_optimized.py)
- **Cambio**: Agregó nota explicativa sobre filtrado previo
- **Nota**: Los datos en `pft_monthly_statistics.nc` ya fueron filtrados durante preprocesamiento
- **Efecto**: Script produce resultados con datos filtrados automáticamente

#### ✅ [plot_lat_time_optimized.py](scripts/plot_lat_time_optimized.py)
- **Cambio**: Agregó nota explicativa sobre filtrado previo
- **Nota**: Los datos en `pft_monthly_statistics.nc` ya fueron filtrados durante preprocesamiento
- **Efecto**: Heatmaps de latitud-tiempo muestran datos del Golfo de California

## Diferencias de metodología

| Aspecto | MAPAS (drop=False) | SERIES (drop=True) |
|---------|-------------------|-------------------|
| Puntos mostrados | Enmascarados (NaN) | Eliminados |
| Visualización | Solo región del Golfo | Solo región del Golfo |
| Media espacial | Excluye puntos enmascarados | Excluye puntos eliminados |
| Memoria | Mayor (conserva grid) | Menor (elimina puntos) |

## ✅ Verificación

Todos los scripts han sido verificados y contienen:

1. **Scripts de mapas**: 
   - ✅ Importan `get_gulf_of_california_filter`
   - ✅ Crean mask con `use_shapefile=True`
   - ✅ Aplican mask con `where(mask, drop=False)`

2. **Scripts de series**:
   - ✅ Importan `get_gulf_of_california_filter`
   - ✅ Crean mask con `use_shapefile=True`
   - ✅ Aplican mask con `where(mask, drop=True)`

3. **Scripts de estadísticas**:
   - ✅ Incluyen notas sobre datos pre-filtrados
   - ✅ Usan archivo `pft_monthly_statistics.nc` (ya filtrado)

## Próximos pasos

1. ✅ COMPLETADO: Actualizar scripts para usar shapefile polygon filter
2. ⏳ **SIGUIENTE**: Ejecutar scripts para generar mapas, series y análisis con nuevos filtrados
3. ⏳ Validar que outputs muestren únicamente la región del Golfo de California
4. ⏳ Revisar cambios en estadísticas vs versión anterior (si aplica)
5. ⏳ Commit a rama `spatial-filter-shapefile` y merge a `master`

## Beneficios de estos cambios

✓ **Mayor precisión espacial**: Solo datos dentro del Golfo de California  
✓ **Resultados más confiables**: Excluye puntos en tierra o océano abierto  
✓ **Visualizaciones mejoradas**: Mapas muestran límite exacto del polígono  
✓ **Análisis más robusto**: Series de tiempo usan solo datos relevantes  

## Archivos de configuración

Todos los scripts dependen de:
- `config_gulf_california.py` - Función `get_gulf_of_california_filter(ds, use_shapefile=True)`
- `data/shapefiles/regionmarinamx.shp` y archivos asociados

Verificar que estos archivos estén presentes y correctamente configurados.
