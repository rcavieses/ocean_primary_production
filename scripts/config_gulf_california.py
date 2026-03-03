#!/usr/bin/env python3
"""
Configuración centralizada para los límites geográficos del Golfo de California.
Incluye:
  - Límites de caja rectangular (fallback)
  - Filtrado por polígono (shapefile)

Todos los scripts de mapas y análisis espacial deben usar estas funciones.
"""

import numpy as np
from pathlib import Path
import warnings

# Coordenadas objetivo del Golfo de California
# Basadas en download_pft_data.py
GULF_OF_CALIFORNIA_BOUNDS = {
    'lon_min': -117.0,
    'lon_max': -102.0,
    'lat_min': 18.0,
    'lat_max': 33.0
}

# Para uso en cartopy set_extent (oeste, este, sur, norte)
# Usar los límites objetivo para que los mapas muestren exactamente eso
GULF_OF_CALIFORNIA_EXTENT = [
    GULF_OF_CALIFORNIA_BOUNDS['lon_min'],
    GULF_OF_CALIFORNIA_BOUNDS['lon_max'],
    GULF_OF_CALIFORNIA_BOUNDS['lat_min'],
    GULF_OF_CALIFORNIA_BOUNDS['lat_max']
]

# Ruta al shapefile del polígono
SHAPEFILE_PATH = Path(__file__).parent.parent / 'data' / 'shapefiles' / 'regionmarinamx.shp'
_SHAPEFILE_CACHE = None
_SHAPEFILE_POLYGON_CACHE = None

def _load_shapefile_polygon():
    """
    Carga el shapefile y retorna el polígono unificado (cached).
    """
    global _SHAPEFILE_CACHE, _SHAPEFILE_POLYGON_CACHE
    
    if _SHAPEFILE_POLYGON_CACHE is not None:
        return _SHAPEFILE_POLYGON_CACHE
    
    try:
        import geopandas as gpd
        gdf = gpd.read_file(str(SHAPEFILE_PATH))
        _SHAPEFILE_POLYGON_CACHE = gdf.unary_union
        return _SHAPEFILE_POLYGON_CACHE
    except Exception as e:
        warnings.warn(f"Could not load shapefile: {e}. Using rectangular bounds.")
        return None

def get_gulf_of_california_filter_bbox(ds):
    """
    Retorna un filtro booleano rectangular para seleccionar datos del Golfo de California.
    Este es el método fallback cuando no se puede usar shapefile.
    """
    lat_mask = (ds['latitude'] >= GULF_OF_CALIFORNIA_BOUNDS['lat_min']) & \
               (ds['latitude'] <= GULF_OF_CALIFORNIA_BOUNDS['lat_max'])
    lon_mask = (ds['longitude'] >= GULF_OF_CALIFORNIA_BOUNDS['lon_min']) & \
               (ds['longitude'] <= GULF_OF_CALIFORNIA_BOUNDS['lon_max'])
    return lat_mask.values, lon_mask.values

def get_gulf_of_california_filter_shapefile(ds):
    """
    Retorna un filtro 2D basado en el shapefile del Golfo de California.
    Usa point-in-polygon para mayor precisión.
    
    Returns:
        numpy array: máscara 2D (lat, lon) con True para puntos dentro del polígono
    """
    from shapely.geometry import Point
    
    try:
        polygon = _load_shapefile_polygon()
        if polygon is None:
            raise RuntimeError("Could not load polygon")
        
        # Create coordinate grids
        lons = ds.longitude.values
        lats = ds.latitude.values
        LON_GRID, LAT_GRID = np.meshgrid(lons, lats)
        
        # Vectorized point-in-polygon check
        mask = np.zeros(LON_GRID.shape, dtype=bool)
        
        # Use prepared geometry for faster checks (if available)
        try:
            from shapely.prepared import prep
            prepared_polygon = prep(polygon)
            for i in range(LAT_GRID.shape[0]):
                for j in range(LON_GRID.shape[1]):
                    point = Point(LON_GRID[i, j], LAT_GRID[i, j])
                    if prepared_polygon.contains(point):
                        mask[i, j] = True
        except (ImportError, AttributeError):
            # Fallback to regular contains check
            for i in range(LAT_GRID.shape[0]):
                for j in range(LON_GRID.shape[1]):
                    point = Point(LON_GRID[i, j], LAT_GRID[i, j])
                    if polygon.contains(point):
                        mask[i, j] = True
        
        return mask
    
    except Exception as e:
        warnings.warn(f"Shapefile filtering failed ({e}). Falling back to bbox.")
        lat_mask, lon_mask = get_gulf_of_california_filter_bbox(ds)
        return lat_mask & lon_mask

def get_gulf_of_california_filter(ds, use_shapefile=True):
    """
    Retorna un filtro booleano para seleccionar datos del Golfo de California.
    
    Args:
        ds: xarray Dataset
        use_shapefile: bool, si True usa polígono del shapefile, si False usa bbox
    
    Returns:
        tuple (lat_mask, lon_mask): máscaras 1D para uso con isel()
            Nota: estas son máscaras booleanas para las dimensiones lat/lon,
                  resultando en una selección rectangular pero precisa dentro del polígono
    """
    if use_shapefile:
        mask_2d = get_gulf_of_california_filter_shapefile(ds)
        # Convertir máscara 2D a máscaras 1D: un punto está "dentro" si hay al menos
        # un punto válido en su fila/columna
        lat_mask = mask_2d.any(axis=1)  # True si algún punto en esa fila está dentro
        lon_mask = mask_2d.any(axis=0)  # True si algún punto en esa columna está dentro
        return lat_mask, lon_mask
    else:
        return get_gulf_of_california_filter_bbox(ds)
