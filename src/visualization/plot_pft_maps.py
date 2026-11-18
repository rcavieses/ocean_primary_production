#!/usr/bin/env python3

import os
os.environ['MPLBACKEND'] = 'Agg'

import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import numpy as np
import sys
import geopandas as gpd
from shapely.geometry import Point

# Importar configuración centralizada
sys.path.insert(0, str(Path(__file__).parent.parent / 'pipeline'))
from config_gulf_california import GULF_OF_CALIFORNIA_BOUNDS, GULF_OF_CALIFORNIA_EXTENT, get_gulf_of_california_filter

# Get base directory
base_dir = Path(__file__).parent.parent.parent
data_file = base_dir / 'data' / 'raw' / 'pft_golfo_california_2000_2024.nc'
output_dir = base_dir / 'results' / 'satellite' / 'figures' / 'maps'
output_dir.mkdir(parents=True, exist_ok=True)

ds = xr.open_dataset(data_file)

# Filtrar datos a 2016-2024
ds_filtered = ds.sel(time=slice('2016-01-01', '2024-12-31'))
print(f"Filtered data: {len(ds_filtered.time)} timesteps (2016-2024)")

# Aplicar filtro espacial con shapefile del Golfo de California
mask = get_gulf_of_california_filter(ds_filtered, use_shapefile=True)

# Cargar shapefile para visualización
shapefile_path = base_dir / 'results' / 'satellite' / 'figures' / 'shapefiles' / 'regionmarinamx.shp'
gdf = gpd.read_file(str(shapefile_path))
study_area_polygon = gdf.unary_union

# Cargar máscaras de tierra desde Natural Earth shapefiles
import cartopy.io.shapereader as shpreader

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

    print(f"Creating map for {var}...")

    try:
        # Compute time mean in a memory-friendly loop
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

        # Wrap back into an xarray DataArray with latitude/longitude coords
        data_mean = xr.DataArray(mean_arr, coords=[ds_filtered['latitude'], ds_filtered['longitude']], dims=['latitude', 'longitude'])

        # Create land mask: mark points that are on land (optimized)
        lons = ds_filtered.longitude.values
        lats = ds_filtered.latitude.values
        LON_GRID, LAT_GRID = np.meshgrid(lons, lats)

        land_mask = np.zeros(LON_GRID.shape, dtype=bool)
        if land_gdf is not None:
            # Use spatial indexing for efficiency
            from geopandas.sindex import spatial_index

            # Create GeoDataFrame from points
            points = [Point(LON_GRID[i, j], LAT_GRID[i, j])
                     for i in range(LAT_GRID.shape[0])
                     for j in range(LON_GRID.shape[1])]

            points_gdf = gpd.GeoDataFrame({'geometry': points})

            # Use spatial join to find points within land polygons
            joined = gpd.sjoin(points_gdf, land_gdf, how='inner', predicate='within')

            # Mark land points
            land_indices = joined.index.unique()
            for idx in land_indices:
                i = idx // LON_GRID.shape[1]
                j = idx % LON_GRID.shape[1]
                if i < land_mask.shape[0] and j < land_mask.shape[1]:
                    land_mask[i, j] = True

        # Apply land mask: set land pixels to NaN
        data_mean_no_land = data_mean.copy()
        data_mean_no_land.values[land_mask] = np.nan

        # Calculate colorbar range using ONLY data inside the study area AND not on land
        mask_array = mask.values.astype(bool)
        valid_data = data_mean_no_land.values
        valid_values_in_region = valid_data[mask_array & ~land_mask]
        valid_values_in_region = valid_values_in_region[~np.isnan(valid_values_in_region)]
        valid_values_in_region = valid_values_in_region[valid_values_in_region > 0]  # Remove zeros for log scale

        if len(valid_values_in_region) == 0:
            print(f"  WARNING: No valid data for {var} within study area, skipping...")
            continue

        vmin = float(np.min(valid_values_in_region))
        vmax = float(np.max(valid_values_in_region))

        fig = plt.figure(figsize=(10, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.coastlines()
        ax.add_feature(cfeature.LAND, facecolor='lightgray')
        ax.add_feature(cfeature.BORDERS, linestyle=':')

        # Use logarithmic normalization
        norm = mcolors.LogNorm(vmin=vmin, vmax=vmax)

        im = data_mean_no_land.plot(
            ax=ax,
            transform=ccrs.PlateCarree(),
            cmap='viridis',
            add_colorbar=True,
            cbar_kwargs={'label': f'{var} mean (log scale)'},
            norm=norm
        )

        # Draw study area boundary
        from matplotlib.patches import Polygon as mplPolygon
        if hasattr(study_area_polygon, 'exterior'):
            coords = np.array(study_area_polygon.exterior.coords)
            polygon_patch = mplPolygon(coords, fill=False, edgecolor='red', linewidth=2,
                                      transform=ccrs.PlateCarree(), label='Study Area')
            ax.add_patch(polygon_patch)
        elif hasattr(study_area_polygon, 'geoms'):
            # MultiPolygon
            for poly in study_area_polygon.geoms:
                coords = np.array(poly.exterior.coords)
                polygon_patch = mplPolygon(coords, fill=False, edgecolor='red', linewidth=2,
                                          transform=ccrs.PlateCarree())
                ax.add_patch(polygon_patch)

        ax.set_title(f'{var} - Time Average (2016-2024)')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.legend(loc='upper left')

        plt.tight_layout()
        plt.savefig(output_dir / f'{var}_mean_map.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {var}_mean_map.png (log scale: {vmin:.2f} - {vmax:.2f})")
    except Exception as e:
        print(f"  ERROR processing {var}: {str(e)}")

ds.close()
