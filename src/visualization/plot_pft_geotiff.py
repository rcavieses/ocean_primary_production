#!/usr/bin/env python3

import os
os.environ['MPLBACKEND'] = 'Agg'

import xarray as xr
from pathlib import Path
import numpy as np
import sys
import rasterio
from rasterio.transform import from_bounds
import geopandas as gpd
from shapely.geometry import Point
import cartopy.io.shapereader as shpreader

# Importar configuración centralizada
sys.path.insert(0, str(Path(__file__).parent.parent / 'pipeline'))
from config_gulf_california import GULF_OF_CALIFORNIA_BOUNDS, get_gulf_of_california_filter

# Get base directory
base_dir = Path(__file__).parent.parent.parent
data_file = base_dir / 'data' / 'raw' / 'pft_golfo_california_2000_2024.nc'
output_dir = base_dir / 'results' / 'satellite' / 'figures' / 'maps' / 'geotiff_2020_2025'
output_dir.mkdir(parents=True, exist_ok=True)

ds = xr.open_dataset(data_file)

# Filtrar datos a 2020-2025
ds_filtered = ds.sel(time=slice('2020-01-01', '2025-12-31'))
print(f"Filtered data: {len(ds_filtered.time)} timesteps (2020-2025)")

# Aplicar filtro espacial con shapefile del Golfo de California
mask = get_gulf_of_california_filter(ds_filtered, use_shapefile=True)

# Cargar shapefile para visualización
shapefile_path = base_dir / 'results' / 'satellite' / 'figures' / 'shapefiles' / 'regionmarinamx.shp'
gdf = gpd.read_file(str(shapefile_path))
study_area_polygon = gdf.unary_union

# Cargar máscaras de tierra desde Natural Earth shapefiles
try:
    land_shp = shpreader.natural_earth(resolution='50m', category='physical', name='land')
    land_gdf = gpd.read_file(land_shp)
    print(f"Loaded land mask with {len(land_gdf)} polygons")
except Exception as e:
    print(f"Warning: Could not load land mask ({e})")
    land_gdf = None

variables = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO',
             'PICO', 'PROCHLO', 'PROKAR']

for var in variables:
    if var not in ds_filtered:
        print(f"Variable {var} not found, skipping...")
        continue

    print(f"Creating GeoTiff for {var}...")

    try:
        # Compute time mean
        time_len = ds_filtered.dims.get('time', len(ds_filtered['time']))
        sum_arr = None
        count_arr = None

        for t in range(time_len):
            arr = ds_filtered[var].isel(time=t).values
            if sum_arr is None:
                sum_arr = np.zeros_like(arr, dtype=float)
                count_arr = np.zeros_like(arr, dtype=int)
            valid = ~np.isnan(arr)
            sum_arr[valid] += arr[valid]
            count_arr[valid] += 1

        # Avoid division by zero
        with np.errstate(invalid='ignore', divide='ignore'):
            mean_arr = np.where(count_arr > 0, sum_arr / count_arr, np.nan)

        # Wrap back into an xarray DataArray
        data_mean = xr.DataArray(mean_arr, coords=[ds_filtered['latitude'], ds_filtered['longitude']], dims=['latitude', 'longitude'])

        # Create land mask using spatial join (optimized)
        lons = ds_filtered.longitude.values
        lats = ds_filtered.latitude.values

        # Check if latitude is in ascending order (S to N) and flip if needed for proper GeoTIFF georeferencing
        if lats[1] > lats[0]:
            lats = np.flip(lats)
            mean_arr = np.flipud(mean_arr)
            data_mean = xr.DataArray(np.flipud(data_mean.values), coords=[lats, lons], dims=['latitude', 'longitude'])
        LON_GRID, LAT_GRID = np.meshgrid(lons, lats)

        land_mask = np.zeros(LON_GRID.shape, dtype=bool)
        if land_gdf is not None:
            # Use spatial indexing for efficiency
            points = [Point(LON_GRID[i, j], LAT_GRID[i, j])
                     for i in range(LAT_GRID.shape[0])
                     for j in range(LON_GRID.shape[1])]

            points_gdf = gpd.GeoDataFrame({'geometry': points})
            joined = gpd.sjoin(points_gdf, land_gdf, how='inner', predicate='within')

            # Mark land points
            land_indices = joined.index.unique()
            for idx in land_indices:
                i = idx // LON_GRID.shape[1]
                j = idx % LON_GRID.shape[1]
                if i < land_mask.shape[0] and j < land_mask.shape[1]:
                    land_mask[i, j] = True

        # Flip land mask to match flipped data (if latitude was inverted)
        if ds_filtered.latitude.values[1] > ds_filtered.latitude.values[0]:
            land_mask = np.flipud(land_mask)

        # Apply land mask: set land pixels to NaN
        data_mean_no_land = data_mean.copy()
        data_mean_no_land.values[land_mask] = np.nan

        # Calculate scale using only data inside study area and not on land
        mask_array = mask.values.astype(bool)
        valid_data = data_mean_no_land.values
        valid_values_in_region = valid_data[mask_array & ~land_mask]
        valid_values_in_region = valid_values_in_region[~np.isnan(valid_values_in_region)]
        valid_values_in_region = valid_values_in_region[valid_values_in_region > 0]

        if len(valid_values_in_region) == 0:
            print(f"  WARNING: No valid data for {var} within study area, skipping...")
            continue

        vmin = float(np.min(valid_values_in_region))
        vmax = float(np.max(valid_values_in_region))

        # Create GeoTiff with rasterio
        output_file = output_dir / f'{var}_mean_map.tif'

        # Get coordinate info (note: after flip, lats should be in descending order N to S)
        lon_min = float(lons.min())
        lon_max = float(lons.max())
        lat_min = float(lats.min())
        lat_max = float(lats.max())

        # Create transform: from_bounds expects (left, bottom, right, top, width, height)
        # After flip, data is in (N to S, W to E) order, so lats goes from max (north) to min (south)
        transform = from_bounds(lon_min, lat_min, lon_max, lat_max, len(lons), len(lats))

        # Write GeoTiff
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
            # Write data, converting NaN to nodata
            data_to_write = data_mean_no_land.values.astype(np.float32)
            data_to_write[np.isnan(data_to_write)] = -9999
            dst.write(data_to_write, 1)
            # Add metadata with units
            dst.update_tags(1,
                           long_name=f'{var} Mean Primary Production (2020-2025)',
                           units='mg C m^-2 day^-1',
                           scale='logarithmic',
                           scale_range=f'{vmin:.2f} - {vmax:.2f}',
                           nodata_value='-9999')
            # Also add global metadata
            dst.update_tags(
                title='Primary Production Mean Maps (2020-2025)',
                description='Phytoplankton Functional Type mean production maps',
                source='MODIS satellite data',
                time_period='2020-2025',
                study_area='Gulf of California',
                land_masked='yes',
                crs='WGS84 (EPSG:4326)'
            )

        print(f"  ✓ GeoTiff: {output_file.name} (log scale: {vmin:.2f} - {vmax:.2f})")
    except Exception as e:
        print(f"  ERROR processing {var}: {str(e)}")
        import traceback
        traceback.print_exc()

ds.close()
print(f"\n✓ GeoTiff files saved to: {output_dir}")
