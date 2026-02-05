#!/usr/bin/env python3
"""
Demonstration script showing how to use shapefile-based spatial filtering
in existing PFT analysis scripts.

This example shows the before/after approach.
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import warnings
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config_gulf_california import (
    GULF_OF_CALIFORNIA_EXTENT,
    get_gulf_of_california_filter
)

warnings.filterwarnings("ignore")

# Configuration
base_dir = Path(__file__).parent.parent
data_file = base_dir / 'data' / 'pft_golfo_california_2000_2024.nc'
output_dir = base_dir / 'data' / 'figures'
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("DEMONSTRATION: SHAPEFILE-BASED FILTERING IN EXISTING SCRIPTS")
print("=" * 70)

# Load dataset
print("\n[1] Loading dataset...")
ds = xr.open_dataset(data_file)
print(f"✓ Dataset loaded: {dict(ds.dims)}")

# ===== METHOD 1: RECTANGULAR BBOX (Original) =====
print("\n[2] METHOD 1: Rectangular bounding box (original approach)...")
try:
    lat_mask_bbox, lon_mask_bbox = get_gulf_of_california_filter(ds, use_shapefile=False)
    ds_bbox = ds.isel(latitude=lat_mask_bbox, longitude=lon_mask_bbox)
    print(f"✓ Filtered with bbox:")
    print(f"  - New dimensions: {dict(ds_bbox.dims)}")
    print(f"  - Spatial coverage: {(lat_mask_bbox.sum() * lon_mask_bbox.sum()) / (lat_mask_bbox.size * lon_mask_bbox.size) * 100:.2f}%")
except Exception as e:
    print(f"✗ Error: {e}")

# ===== METHOD 2: POLYGON-BASED (New) =====
print("\n[3] METHOD 2: Polygon-based filter from shapefile (new approach)...")
try:
    mask_polygon = get_gulf_of_california_filter(ds, use_shapefile=True)
    print(f"✓ Shapefile filter created")
    print(f"  - Mask shape: {mask_polygon.shape}")
    print(f"  - Points inside polygon: {mask_polygon.sum()} ({100*mask_polygon.sum()/mask_polygon.size:.2f}%)")
    
    # Apply mask to data
    chl_sample = ds['CHL'].isel(time=0)
    chl_masked = chl_sample.where(mask_polygon, drop=False)
    
    # Get valid values inside polygon
    chl_valid = chl_masked.values[mask_polygon]
    chl_valid = chl_valid[~np.isnan(chl_valid)]
    
    print(f"  - Median CHL (in polygon): {np.median(chl_valid):.6f}")
    print(f"  - Mean CHL (in polygon): {np.mean(chl_valid):.6f}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# ===== COMPARISON VISUALIZATION =====
print("\n[4] Creating comparison visualization...")
try:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Get sample CHL data (first timestep)
    chl = ds['CHL'].isel(time=0).values
    lons = ds.longitude.values
    lats = ds.latitude.values
    extent = [lons.min(), lons.max(), lats.min(), lats.max()]
    
    # Plot 1: Full data
    ax = axes[0, 0]
    im = ax.imshow(chl, extent=extent, cmap='viridis', origin='lower',
                   vmin=np.nanpercentile(chl, 2), vmax=np.nanpercentile(chl, 98))
    ax.set_title('Full Dataset (All Points)')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.colorbar(im, ax=ax, label='CHL (mg/m³)')
    
    # Plot 2: Bbox filtered
    ax = axes[0, 1]
    chl_bbox = chl.copy()
    chl_bbox[~(lat_mask_bbox[:, np.newaxis] & lon_mask_bbox[np.newaxis, :])] = np.nan
    im = ax.imshow(chl_bbox, extent=extent, cmap='viridis', origin='lower',
                   vmin=np.nanpercentile(chl, 2), vmax=np.nanpercentile(chl, 98))
    ax.set_title('Method 1: Rectangular Bbox Filter')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.colorbar(im, ax=ax, label='CHL (mg/m³)')
    
    # Plot 3: Polygon filtered
    ax = axes[1, 0]
    chl_poly = chl.copy()
    chl_poly[~mask_polygon] = np.nan
    im = ax.imshow(chl_poly, extent=extent, cmap='viridis', origin='lower',
                   vmin=np.nanpercentile(chl, 2), vmax=np.nanpercentile(chl, 98))
    ax.set_title('Method 2: Shapefile Polygon Filter')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.colorbar(im, ax=ax, label='CHL (mg/m³)')
    
    # Plot 4: Difference/comparison
    ax = axes[1, 1]
    diff_mask = mask_polygon.astype(int) - (lat_mask_bbox[:, np.newaxis] & lon_mask_bbox[np.newaxis, :]).astype(int)
    im = ax.imshow(diff_mask, extent=extent, cmap='RdBu', origin='lower', vmin=-1, vmax=1)
    ax.set_title('Polygon - Bbox (Red: only in polygon, Blue: only in bbox)')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.colorbar(im, ax=ax, label='Difference')
    
    plt.tight_layout()
    fig.savefig(output_dir / 'demo_shapefile_filtering_comparison.png', dpi=150, bbox_inches='tight')
    print(f"✓ Comparison saved to: demo_shapefile_filtering_comparison.png")
    plt.close()
    
except Exception as e:
    print(f"✗ Error creating visualization: {e}")
    import traceback
    traceback.print_exc()

# ===== CODE PATTERN GUIDE =====
print("\n" + "=" * 70)
print("CODE PATTERN FOR UPDATING EXISTING SCRIPTS")
print("=" * 70)
print("""
OLD CODE (rectangular bbox):
    from config_gulf_california import get_gulf_of_california_filter
    lat_mask, lon_mask = get_gulf_of_california_filter(ds)
    ds_filtered = ds.isel(latitude=lat_mask, longitude=lon_mask)

NEW CODE (shapefile polygon):
    from config_gulf_california import get_gulf_of_california_filter
    mask = get_gulf_of_california_filter(ds, use_shapefile=True)
    ds_filtered = ds.where(mask, drop=False)
    
    # Or use with xarray operations:
    data_masked = data.where(mask, drop=False)
    
    # To preserve coordinates:
    data_masked = data.where(mask, drop=True)  # keeps only valid points

IMPORTANT NOTES:
  1. Old code using isel() breaks with 2D mask - must use where()
  2. mask_polygon is 2D (lat, lon), not 1D like lat_mask/lon_mask
  3. use_shapefile=False falls back to bbox automatically
  4. Shapefile must be extracted in data/shapefiles/regionmarinamx.shp
""")
print("=" * 70)

ds.close()
print("\n✓ Demonstration complete. Check output PNG for visual comparison.")
