# Filtrado Espacial con Shapefile - Guía de Implementación

## Estado: ✅ PROBADO Y FUNCIONAL

El filtrado basado en el shapefile del Golfo de California ha sido implementado y probado exitosamente.

### Branch de desarrollo
- **Rama actual**: `spatial-filter-shapefile`
- **Rama original**: `master`

## Archivos modificados/creados

### 1. **config_gulf_california.py** (ACTUALIZADO)
Ahora incluye dos métodos de filtrado:
- `get_gulf_of_california_filter(ds, use_shapefile=False)` - método nuevo universal
- `get_gulf_of_california_filter_bbox()` - método rectangular (original)
- `get_gulf_of_california_filter_shapefile()` - método con polígono (nuevo)

### 2. **Scripts de demostración**
- `test_shapefile_filter.py` - Valida que el shapefile se carga correctamente
- `demo_shapefile_filtering.py` - Muestra comparación entre métodos

### 3. **Shapefile extraído**
```
data/shapefiles/regionmarinamx.{shp,shx,dbf,prj,xml,html}
```

## Diferencias entre métodos

| Aspecto | Rectangular (Original) | Polígono (Nuevo) |
|---------|------------------------|------------------|
| Cobertura | 83.33% del grid | 8.96% del grid |
| Precisión | Caja | Polígono exacto |
| Puntos procesados | ~108,000 | ~13,900 |
| Velocidad | Rápido | Variable |
| Memoria | Mayor | Menor |

## Cómo apliar a los scripts existentes

### Scripts a actualizar (MAPAS):
1. `plot_pft_maps.py`
2. `plot_pft_quinquennial_maps.py`
3. `plot_pft_quinquennial_diff.py`
4. `plot_lat_time_optimized.py`

### Scripts a actualizar (SERIES DE TIEMPO):
1. `plot_pft_monthly_timeseries.py`
2. `plot_pft_monthly_with_indices_optimized.py`

## Patrón de código para actualización

### ANTES (rectangular):
```python
from config_gulf_california import get_gulf_of_california_filter, GULF_OF_CALIFORNIA_EXTENT

# Aplicar filtro rectangular
lat_mask, lon_mask = get_gulf_of_california_filter(ds)
ds_filtered = ds.isel(latitude=lat_mask, longitude=lon_mask)

# Usar en plots
ax.set_extent(GULF_OF_CALIFORNIA_EXTENT, crs=ccrs.PlateCarree())
```

### DESPUÉS (polígono):
```python
from config_gulf_california import get_gulf_of_california_filter, GULF_OF_CALIFORNIA_EXTENT

# Aplicar filtro con shapefile
mask = get_gulf_of_california_filter(ds, use_shapefile=True)

# Para mapas (evitar eliminar puntos, solo enmascarar):
data_masked = data.where(mask, drop=False)

# Para análisis (eliminar puntos fuera del polígono):
data_masked = data.where(mask, drop=True)

# El extent sigue siendo el mismo
ax.set_extent(GULF_OF_CALIFORNIA_EXTENT, crs=ccrs.PlateCarree())
```

## Impacto en resultados

- **Mapas**: Mostrarán solo el polígono del Golfo de California (más preciso)
- **Series de tiempo**: Usarán solo datos dentro del polígono (valores más concentrados)
- **Estadísticas**: Serán calculadas con menos puntos pero más relevantes

## Próximos pasos

1. ✅ Validar shapefile cargado correctamente
2. ✅ Probar filtrado básico
3. ⏳ Actualizar todos los scripts de mapas
4. ⏳ Actualizar todos los scripts de series de tiempo
5. ⏳ Ejecutar todos los scripts con nuevo filtrado
6. ⏳ Revisar y validar resultados
7. ⏳ Hacer commit a la rama y merge a master

## Ventajas del filtrado por polígono

1. **Mayor precisión**: Sigue exactamente la geometría del Golfo de California
2. **Menos datos innecesarios**: Elimina puntos fuera de la región de interés
3. **Resultados más confiables**: Las estadísticas no incluyen puntos en tierra o océano abierto
4. **Visualizaciones mejoradas**: Los mapas muestran solo la región relevante

## Archivos de salida generados

- `test_shapefile_filter_visualization.png` - Validación del shapefile
- `demo_shapefile_filtering_comparison.png` - Comparación visual de métodos

Puedes revisar estos archivos en `data/figures/` para ver la diferencia entre métodos.
