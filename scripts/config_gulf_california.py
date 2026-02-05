#!/usr/bin/env python3
"""
Configuración centralizada para los límites geográficos del Golfo de California.
Todos los scripts de mapas deben usar estas coordenadas.
"""

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

# Función para crear el filtro de datos
def get_gulf_of_california_filter(ds):
    """
    Retorna un filtro booleano para seleccionar datos del Golfo de California.
    Necesita ser una función porque los límites dependen de los datos.
    """
    lat_mask = (ds['latitude'] >= GULF_OF_CALIFORNIA_BOUNDS['lat_min']) & \
               (ds['latitude'] <= GULF_OF_CALIFORNIA_BOUNDS['lat_max'])
    lon_mask = (ds['longitude'] >= GULF_OF_CALIFORNIA_BOUNDS['lon_min']) & \
               (ds['longitude'] <= GULF_OF_CALIFORNIA_BOUNDS['lon_max'])
    return lat_mask.values, lon_mask.values
