#!/usr/bin/env python3
"""
Test script to load shapefile and apply spatial filtering to PFT data.
This script validates the polygon-based filtering approach before applying
it to all map and analysis scripts.
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import xarray as xr
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# Configuration
base_dir = Path(__file__).parent.parent
shapefile_path = base_dir / 'data' / 'shapefiles' / 'regionmarinamx.shp'
data_file = base_dir / 'data' / 'pft_golfo_california_2000_2024.nc'
output_dir = base_dir / 'data' / 'figures'
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("TESTING SHAPEFILE-BASED SPATIAL FILTERING")
print("=" * 70)

# Step 1: Load and inspect shapefile
print("\n[1] Loading shapefile...")
try:
    gdf = gpd.read_file(str(shapefile_path))
    print(f"✓ Shapefile loaded successfully")
    print(f"  - Features: {len(gdf)}")
    print(f"  - Columns: {list(gdf.columns)}")
    print(f"  - CRS: {gdf.crs}")
    print(f"  - Geometry type: {gdf.geometry.type.unique()}")
    
    # Show bounds
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    print(f"  - Total bounds: lon [{bounds[0]:.2f}, {bounds[2]:.2f}], lat [{bounds[1]:.2f}, {bounds[3]:.2f}]")
    
    # Create merged geometry
    merged_geometry = gdf.unary_union
    print(f"  - Merged geometry type: {merged_geometry.geom_type}")
    
except Exception as e:
    print(f"✗ ERROR loading shapefile: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 2: Load dataset
print("\n[2] Loading PFT dataset...")
try:
    ds = xr.open_dataset(data_file)
    print(f"✓ Dataset loaded")
    print(f"  - Dimensions: {dict(ds.dims)}")
    print(f"  - Variables: {list(ds.data_vars)}")
    print(f"  - Lat range: [{ds.latitude.values.min():.4f}, {ds.latitude.values.max():.4f}]")
    print(f"  - Lon range: [{ds.longitude.values.min():.4f}, {ds.longitude.values.max():.4f}]")
    
except Exception as e:
    print(f"✗ ERROR loading dataset: {e}")
    exit(1)

# Step 3: Create spatial mask using shapefile bounds
print("\n[3] Creating spatial mask from shapefile polygon...")
try:
    # Method 1: Vectorized point-in-polygon check using rasterio
    from shapely.geometry import Point
    
    # Create coordinate arrays
    lons = ds.longitude.values
    lats = ds.latitude.values
    LON_GRID, LAT_GRID = np.meshgrid(lons, lats)
    
    print(f"  - Creating mask for {LON_GRID.size} points...")
    
    # Vectorized point-in-polygon check
    mask = np.zeros(LON_GRID.shape, dtype=bool)
    for i in range(LAT_GRID.shape[0]):
        for j in range(LON_GRID.shape[1]):
            point = Point(LON_GRID[i, j], LAT_GRID[i, j])
            if merged_geometry.contains(point):
                mask[i, j] = True
    
    # Count masked points
    n_masked = mask.sum()
    n_total = mask.size
    pct = 100 * n_masked / n_total
    
    print(f"✓ Mask created successfully")
    print(f"  - Points inside polygon: {n_masked}/{n_total} ({pct:.2f}%)")
    
except Exception as e:
    print(f"✗ ERROR creating mask: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 4: Test filtering on a sample variable
print("\n[4] Testing filter on CHL variable (sample timestep)...")
try:
    # Get first timestep
    chl_sample = ds['CHL'].isel(time=0)
    
    # Apply mask
    chl_filtered = chl_sample.where(mask, drop=False)
    chl_masked_values = chl_filtered.values[mask]
    
    print(f"✓ Filter applied successfully")
    print(f"  - Original array shape: {chl_sample.shape}")
    print(f"  - Masked points: {chl_masked_values.size}")
    print(f"  - Valid (non-NaN) values: {(~np.isnan(chl_masked_values)).sum()}")
    print(f"  - Mean value (in polygon): {np.nanmean(chl_masked_values):.6f}")
    print(f"  - Std value (in polygon): {np.nanstd(chl_masked_values):.6f}")
    
except Exception as e:
    print(f"✗ ERROR filtering data: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 5: Create visualization of the mask
print("\n[5] Creating visualization...")
try:
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Plot 1: Shapefile polygon
    ax = axes[0]
    gdf.plot(ax=ax, alpha=0.5, edgecolor='k', color='blue', linewidth=2)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Shapefile: Gulf of California Region')
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Spatial mask
    ax = axes[1]
    im = ax.imshow(mask, extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                   cmap='RdYlGn', origin='lower', alpha=0.8)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Spatial Mask (Green = Inside Polygon)')
    plt.colorbar(im, ax=ax)
    
    # Plot 3: Masked data
    ax = axes[2]
    chl_display = chl_sample.values.copy()
    chl_display[~mask] = np.nan
    im = ax.imshow(chl_display, extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                   cmap='viridis', origin='lower', vmin=np.nanpercentile(chl_display, 2),
                   vmax=np.nanpercentile(chl_display, 98))
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('CHL Data (First Timestep) - Masked')
    plt.colorbar(im, ax=ax, label='CHL (mg/m³)')
    
    plt.tight_layout()
    output_file = output_dir / 'test_shapefile_filter_visualization.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Visualization saved: {output_file}")
    plt.close()
    
except Exception as e:
    print(f"✗ ERROR creating visualization: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Performance summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✓ Shapefile filtering works correctly!")
print(f"  - Polygon geometry: {merged_geometry.geom_type}")
print(f"  - Coverage: {pct:.2f}% of the grid")
print(f"  - Points to process: {n_masked:,}")
print(f"\nNext steps:")
print(f"  1. Update config_gulf_california.py with shapefile-based filter")
print(f"  2. Apply to all map scripts (plot_pft_*.py)")
print(f"  3. Apply to time series scripts")
print(f"  4. Generate new results with polygon-based spatial filtering")
print("=" * 70)

ds.close()
