#!/usr/bin/env python3
"""
Configuración centralizada para los límites geográficos del Golfo de California.
Incluye:
  - Límites de caja rectangular (fallback)
  - Filtrado por polígono (shapefile)

Todos los scripts de mapas y análisis espacial deben usar estas funciones.
"""

import numpy as np
import xarray as xr
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
SHAPEFILE_PATH = Path(__file__).parent.parent.parent / 'data' / 'shapefiles' / 'regionmarinamx.shp'
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
    Retorna un filtro 2D rectangular para seleccionar datos del Golfo de California.
    Este es el método fallback cuando no se puede usar shapefile.
    
    Returns:
        numpy array: máscara 2D (lat, lon) con True para puntos dentro del bbox
    """
    lat_mask = (ds['latitude'] >= GULF_OF_CALIFORNIA_BOUNDS['lat_min']) & \
               (ds['latitude'] <= GULF_OF_CALIFORNIA_BOUNDS['lat_max'])
    lon_mask = (ds['longitude'] >= GULF_OF_CALIFORNIA_BOUNDS['lon_min']) & \
               (ds['longitude'] <= GULF_OF_CALIFORNIA_BOUNDS['lon_max'])
    
    # Crear máscara 2D usando broadcasting
    lat_values = lat_mask.values
    lon_values = lon_mask.values
    
    # Broadcasting: (lat_size, 1) & (1, lon_size) -> (lat_size, lon_size)
    mask_2d = lat_values[:, np.newaxis] & lon_values[np.newaxis, :]
    return mask_2d

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
        mask_2d = get_gulf_of_california_filter_bbox(ds)
        return mask_2d

def get_gulf_of_california_filter(ds, use_shapefile=True):
    """
    Retorna un filtro boolean DataArray para seleccionar datos del Golfo de California.
    
    Args:
        ds: xarray Dataset
        use_shapefile: bool, si True usa polígono del shapefile, si False usa bbox
    
    Returns:
        xarray.DataArray: máscara 2D (lat, lon) compatible con .where()
    """
    if use_shapefile:
        mask_2d = get_gulf_of_california_filter_shapefile(ds)
    else:
        mask_2d = get_gulf_of_california_filter_bbox(ds)
    
    # Convertir a xarray DataArray para compatibilidad con .where()
    mask_da = xr.DataArray(
        mask_2d,
        coords={'latitude': ds['latitude'], 'longitude': ds['longitude']},
        dims=['latitude', 'longitude'],
        name='spatial_mask'
    )
    return mask_da
