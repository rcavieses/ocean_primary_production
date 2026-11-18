#!/usr/bin/env python3
"""
Export PFT production data to GeoTIFF format (2020-2025)
Exports only raw data without map base or visualization artifacts.
"""

import xarray as xr
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from pathlib import Path
import sys
import geopandas as gpd
from shapely.geometry import Point
import cartopy.io.shapereader as shpreader

# Importar configuración centralizada
sys.path.insert(0, str(Path(__file__).parent.parent / 'pipeline'))
from config_gulf_california import get_gulf_of_california_filter

# Configuración
base_dir = Path(__file__).parent.parent.parent
data_file = base_dir / 'data' / 'raw' / 'pft_golfo_california_2000_2024.nc'
output_dir = base_dir / 'results' / 'satellite' / 'figures' / 'maps' / 'geotiff_2020_2025'
output_dir.mkdir(parents=True, exist_ok=True)

# Variables a exportar
VARIABLES = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO',
             'PICO', 'PROCHLO', 'PROKAR']

# Cargar datos
print("Cargando datos...")
ds = xr.open_dataset(data_file)

# Filtrar a 2020-2025
ds_filtered = ds.sel(time=slice('2020-01-01', '2025-12-31'))
print(f"✓ Datos filtrados: {len(ds_filtered.time)} timesteps (2020-2025)")

# Obtener coordenadas
lons = ds_filtered.longitude.values
lats = ds_filtered.latitude.values
print(f"✓ Dominio: Lon {lons[0]:.2f}° to {lons[-1]:.2f}°, Lat {lats[0]:.2f}° to {lats[-1]:.2f}°")

# Cargar máscara de tierra
try:
    land_shp = shpreader.natural_earth(resolution='50m', category='physical', name='land')
    land_gdf = gpd.read_file(land_shp)
    print(f"✓ Máscara de tierra cargada: {len(land_gdf)} polígonos")
except Exception as e:
    print(f"⚠ Advertencia: No se pudo cargar máscara de tierra ({e})")
    land_gdf = None

# Obtener máscara espacial del Golfo de California
mask_spatial = get_gulf_of_california_filter(ds_filtered, use_shapefile=True)
print("✓ Máscara espacial del Golfo de California aplicada")

# Procesar cada variable
for var in VARIABLES:
    if var not in ds_filtered:
        print(f"⚠ Variable {var} no encontrada, saltando...")
        continue

    print(f"\nProcesando {var}...")

    try:
        # Calcular promedio temporal
        time_len = len(ds_filtered.time)
        sum_arr = None
        count_arr = None

        for t in range(time_len):
            arr = ds_filtered[var].isel(time=t).values
            if sum_arr is None:
                sum_arr = np.zeros_like(arr, dtype=np.float32)
                count_arr = np.zeros_like(arr, dtype=np.int32)

            valid = ~np.isnan(arr)
            sum_arr[valid] += arr[valid]
            count_arr[valid] += 1

        # Evitar división por cero
        with np.errstate(invalid='ignore', divide='ignore'):
            mean_data = np.where(count_arr > 0, sum_arr / count_arr, np.nan)

        # Crear máscara de tierra
        LON_GRID, LAT_GRID = np.meshgrid(lons, lats)
        land_mask = np.zeros(LON_GRID.shape, dtype=bool)

        if land_gdf is not None:
            points = [Point(LON_GRID[i, j], LAT_GRID[i, j])
                     for i in range(LAT_GRID.shape[0])
                     for j in range(LON_GRID.shape[1])]

            points_gdf = gpd.GeoDataFrame({'geometry': points})
            joined = gpd.sjoin(points_gdf, land_gdf, how='inner', predicate='within')

            land_indices = joined.index.unique()
            for idx in land_indices:
                i = idx // LON_GRID.shape[1]
                j = idx % LON_GRID.shape[1]
                if i < land_mask.shape[0] and j < land_mask.shape[1]:
                    land_mask[i, j] = True

        # Aplicar máscaras: tierra + área de estudio
        mask_spatial_arr = mask_spatial.values.astype(bool)
        data_masked = mean_data.copy()
        data_masked[land_mask] = np.nan
        data_masked[~mask_spatial_arr] = np.nan

        # Obtener rango de valores válidos
        valid_data = data_masked[~np.isnan(data_masked)]
        if len(valid_data) == 0:
            print(f"  ⚠ Sin datos válidos en área de estudio, saltando...")
            continue

        vmin, vmax = float(np.min(valid_data)), float(np.max(valid_data))

        # CLAVE: Invertir datos para que estén en orden norte→sur (requerido por GeoTIFF)
        # Los datos originales están en orden sur→norte, rasterio espera norte→sur
        data_for_geotiff = np.flipud(data_masked)
        lats_inverted = np.flip(lats)

        # Crear transform para GeoTIFF
        # from_bounds espera: (left, bottom, right, top, width, height)
        lon_min, lon_max = float(lons.min()), float(lons.max())
        lat_min, lat_max = float(lats_inverted.min()), float(lats_inverted.max())

        transform = from_bounds(lon_min, lat_min, lon_max, lat_max, len(lons), len(lats))

        # Escribir GeoTIFF
        output_file = output_dir / f'{var}_mean_map.tif'

        with rasterio.open(
            output_file,
            'w',
            driver='GTiff',
            height=len(lats),
            width=len(lons),
            count=1,
            dtype=rasterio.float32,
            crs='EPSG:4326',
            transform=transform,
        ) as dst:
            # Convertir NaN a nodata
            data_write = data_for_geotiff.astype(np.float32)
            data_write[np.isnan(data_write)] = -9999
            dst.write(data_write, 1)

            # Metadatos
            dst.update_tags(1,
                           long_name=f'{var} Mean Primary Production (2020-2025)',
                           units='mg C m^-2 day^-1',
                           nodata_value='-9999',
                           data_range=f'{vmin:.2f} - {vmax:.2f}')

            dst.update_tags(
                title='Primary Production Mean Maps (2020-2025)',
                description='Phytoplankton Functional Type mean production data',
                source='MODIS satellite data',
                time_period='2020-2025',
                study_area='Gulf of California',
                land_masked='yes',
                crs='WGS84 (EPSG:4326)',
                projection_note='Data inverted to north-south order for correct GeoTIFF georeferencing'
            )

        print(f"  ✓ {output_file.name} (datos: {vmin:.2f} - {vmax:.2f})")

    except Exception as e:
        print(f"  ✗ Error procesando {var}: {str(e)}")
        import traceback
        traceback.print_exc()

ds.close()
print(f"\n✅ Archivos GeoTIFF exportados a: {output_dir}")
print("   Solo datos sin mapa base, con proyección WGS84 correcta")
