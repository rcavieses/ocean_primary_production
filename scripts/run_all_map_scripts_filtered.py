#!/usr/bin/env python3
"""
Master script to run all map-related scripts with spatial filtering by GulfCalifornia shapefile.
Filters all data to only include points within the Gulf of California region.
Optimized for memory efficiency.
"""

import xarray as xr
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import warnings
import subprocess
import sys
from zipfile import ZipFile
import tempfile
import json
import os

warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
SCRIPTS_DIR = BASE_DIR / 'scripts'
SHAPEFILE_ZIP = DATA_DIR / 'shapefiles' / 'GulfCalifornia.zip'
DATA_FILE = DATA_DIR / 'pft_golfo_california_2000_2024.nc'

# Map scripts to run
MAP_SCRIPTS = [
    'plot_pft_maps.py',
    'plot_pft_quinquennial_maps.py',
    'plot_lat_time_optimized.py',
    'plot_pft_seasonal_quinquennial_comparison.py',
    'plot_pft_monthly_with_indices_optimized.py',
    'plot_composition_percentages.py',
]

print("=" * 80)
print("RUNNING ALL MAP SCRIPTS WITH GULF CALIFORNIA SPATIAL FILTERING")
print("=" * 80)

# ============================================================================
# STEP 1: Load and extract shapefile
# ============================================================================

print("\n[STEP 1] Loading Gulf of California shapefile...")

if not SHAPEFILE_ZIP.exists():
    print(f"ERROR: Shapefile zip not found at {SHAPEFILE_ZIP}")
    sys.exit(1)

# Extract shapefile from zip temporarily
with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    with ZipFile(SHAPEFILE_ZIP, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)
    
    # Find the .shp file
    shp_file = list(tmpdir.glob('*.shp'))[0]
    
    # Load shapefile
    gdf = gpd.read_file(shp_file)
    print(f"✓ Shapefile loaded: {shp_file.name}")
    print(f"  Geometry type: {gdf.geometry.type[0]}")
    print(f"  CRS: {gdf.crs}")
    
    # Create a spatial index
    geom = gdf.geometry.unary_union
    bounds = gdf.total_bounds
    print(f"  Bounds: Lon [{bounds[0]:.2f}, {bounds[2]:.2f}], Lat [{bounds[1]:.2f}, {bounds[3]:.2f}]")

# ============================================================================
# STEP 2: Create filter mask (memory efficient)
# ============================================================================

print("\n[STEP 2] Creating spatial filter mask...")

ds = xr.open_dataset(DATA_FILE, chunks={'time': 100})
print(f"  Original dataset shape: {dict(ds.dims)}")

# Extract lat/lon coordinates
lats = ds.latitude.values
lons = ds.longitude.values

# Create a mask for points within the Gulf of California
# Use a more memory-efficient approach
print("  Creating spatial mask (this may take a moment)...")
lat_grid, lon_grid = np.meshgrid(lats, lons, indexing='ij')

# Process in chunks to avoid memory issues
mask = np.zeros(lat_grid.shape, dtype=bool)
for i in range(0, len(lats), 100):  # Process 100 latitudes at a time
    for j in range(0, len(lons), 100):  # Process 100 longitudes at a time
        i_end = min(i + 100, len(lats))
        j_end = min(j + 100, len(lons))
        
        lat_chunk = lat_grid[i:i_end, j:j_end]
        lon_chunk = lon_grid[i:i_end, j:j_end]
        
        points_chunk = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(lon_chunk.ravel(), lat_chunk.ravel()),
            crs='EPSG:4326'
        )
        mask_chunk = points_chunk.geometry.within(geom).values.reshape(lat_chunk.shape)
        mask[i:i_end, j:j_end] = mask_chunk
    
    if (i // 100) % 2 == 0:
        print(f"  Processing... {min(i + 100, len(lats))}/{len(lats)} latitudes")

print(f"  Points inside Gulf of California: {mask.sum()} out of {mask.size} ({100*mask.sum()/mask.size:.1f}%)")

# Select only lat/lon indices that have at least one True value
lat_indices = np.where(mask.any(axis=1))[0]
lon_indices = np.where(mask.any(axis=0))[0]

print(f"  Filtered coverage: {len(lat_indices)} latitudes × {len(lon_indices)} longitudes")

# Create mask for the filtered domain
mask_refined = mask[np.ix_(lat_indices, lon_indices)]

# Get filtered bounds
lon_min = float(ds.longitude.values[lon_indices[0]])
lon_max = float(ds.longitude.values[lon_indices[-1]])
lat_min = float(ds.latitude.values[lat_indices[-1]])
lat_max = float(ds.latitude.values[lat_indices[0]])

print(f"  Spatial coverage: Lon [{lon_min:.2f}, {lon_max:.2f}]")
print(f"                   Lat [{lat_min:.2f}, {lat_max:.2f}]")

# ============================================================================
# STEP 3: Save filter information
# ============================================================================

print("\n[STEP 3] Saving filter information...")

# Save filter bounds as JSON
filter_info = {
    'region': 'Gulf of California',
    'bounds': {
        'lon_min': lon_min,
        'lon_max': lon_max,
        'lat_min': lat_min,
        'lat_max': lat_max
    },
    'indices': {
        'lat_start': int(lat_indices[0]),
        'lat_end': int(lat_indices[-1]),
        'lon_start': int(lon_indices[0]),
        'lon_end': int(lon_indices[-1])
    },
    'n_points_inside': int(mask_refined.sum()),
    'n_lat': int(len(lat_indices)),
    'n_lon': int(len(lon_indices))
}

filter_info_file = DATA_DIR / 'pft_golfo_california_FILTER_INFO.json'
with open(filter_info_file, 'w') as f:
    json.dump(filter_info, f, indent=2)
print(f"✓ Filter info saved: {filter_info_file.name}")

# ============================================================================
# STEP 4: Create output directory for filtered maps
# ============================================================================

print("\n[STEP 4] Setting up output directories...")

filtered_output_dir = DATA_DIR / 'figures' / 'filtered_gulf_california'
filtered_output_dir.mkdir(parents=True, exist_ok=True)
print(f"✓ Output directory: {filtered_output_dir}")

# ============================================================================
# STEP 5: Create a visualization of the filter mask
# ============================================================================

print("\n[STEP 5] Creating spatial coverage visualization...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), subplot_kw={'projection': ccrs.PlateCarree()})

# Plot original dataset coverage
lats_orig = ds.latitude.values
lons_orig = ds.longitude.values
# Create mesh grid for scatter plot
lon_grid_all, lat_grid_all = np.meshgrid(lons_orig, lats_orig)
ax1.scatter(lon_grid_all.ravel(), lat_grid_all.ravel(), s=1, alpha=0.3, c='blue', 
            transform=ccrs.PlateCarree(), label='Original coverage')
ax1.add_feature(cfeature.COASTLINE)
ax1.add_feature(cfeature.LAND, facecolor='lightgray')
gpd.GeoSeries([geom], crs='EPSG:4326').plot(ax=ax1, facecolor='none', edgecolor='red', linewidth=2, label='Gulf of California')
ax1.set_title('Original Dataset Coverage')
ax1.legend(loc='upper right')
ax1.gridlines(draw_labels=True)

# Plot filtered dataset coverage - use the original lat_grid and lon_grid with mask
lons_filt = lon_grid[np.ix_(lat_indices, lon_indices)].ravel()
lats_filt = lat_grid[np.ix_(lat_indices, lon_indices)].ravel()
ax2.scatter(lons_filt, lats_filt, s=1, alpha=0.5, c='green', 
            transform=ccrs.PlateCarree(), label='Filtered coverage')
ax2.add_feature(cfeature.COASTLINE)
ax2.add_feature(cfeature.LAND, facecolor='lightgray')
gpd.GeoSeries([geom], crs='EPSG:4326').plot(ax=ax2, facecolor='none', edgecolor='red', linewidth=2, label='Gulf of California')
ax2.set_title('Filtered Dataset Coverage (Gulf of California Only)')
ax2.legend(loc='upper right')
ax2.gridlines(draw_labels=True)

plt.tight_layout()
coverage_plot = filtered_output_dir / 'spatial_coverage_comparison.png'
plt.savefig(coverage_plot, dpi=300, bbox_inches='tight')
plt.close(fig)
plt.close()
print(f"✓ Coverage comparison saved: {coverage_plot.name}")

# ============================================================================
# STEP 6: Run map scripts with filtered data
# ============================================================================

print("\n[STEP 6] Running map scripts with filtered data...")
print("=" * 80)

successful_scripts = []
failed_scripts = []

for script_name in MAP_SCRIPTS:
    script_path = SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        print(f"\n⚠ SKIPPED: {script_name} (not found)")
        failed_scripts.append((script_name, "Script not found"))
        continue
    
    print(f"\n▶ Running: {script_name}")
    print("-" * 80)
    
    # Create environment with filtered data info
    env = os.environ.copy()
    env['PFT_FILTER_INFO_FILE'] = str(filter_info_file)
    env['PFT_OUTPUT_DIR'] = str(filtered_output_dir)
    env['PFT_IS_FILTERED'] = 'true'
    env['PFT_FILTER_REGION'] = 'GulfCalifornia'
    
    try:
        # Run script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=SCRIPTS_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            print(f"✓ COMPLETED: {script_name}")
            successful_scripts.append(script_name)
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines[-3:]:  # Show last 3 lines
                    if line.strip():
                        print(f"  {line}")
        else:
            print(f"✗ FAILED: {script_name}")
            if result.stderr:
                error_preview = result.stderr[:300]
                print(f"  Error: {error_preview}")
            failed_scripts.append((script_name, result.stderr[:200] if result.stderr else "Unknown error"))
    
    except subprocess.TimeoutExpired:
        print(f"✗ TIMEOUT: {script_name} (exceeded 600 seconds)")
        failed_scripts.append((script_name, "Timeout"))
    except Exception as e:
        print(f"✗ ERROR: {script_name} - {str(e)}")
        failed_scripts.append((script_name, str(e)))

# ============================================================================
# STEP 7: Summary report
# ============================================================================

print("\n" + "=" * 80)
print("EXECUTION SUMMARY")
print("=" * 80)

print(f"\n✓ Successful scripts ({len(successful_scripts)}):")
for script in successful_scripts:
    print(f"  ✓ {script}")

if failed_scripts:
    print(f"\n✗ Failed scripts ({len(failed_scripts)}):")
    for script, error in failed_scripts:
        print(f"  ✗ {script}")
        if error and error != "Script not found":
            print(f"    → {error[:80]}")

print(f"\n📊 Filter Information:")
print(f"  Region: Gulf of California")
print(f"  Bounds: Lon [{lon_min:.2f}, {lon_max:.2f}], Lat [{lat_min:.2f}, {lat_max:.2f}]")
print(f"  Grid points inside: {mask_refined.sum():,} / {mask.size:,} ({100*mask.sum()/mask.size:.1f}%)")
print(f"  Filtered dimensions: {len(lat_indices)} latitudes × {len(lon_indices)} longitudes")

print(f"\n📁 Output directory:")
print(f"  Location: {filtered_output_dir}")
print(f"  Total files generated: {len(list(filtered_output_dir.rglob('*')))}")

print(f"\n📋 Configuration files:")
print(f"  {filter_info_file.name}")

print("\n" + "=" * 80)
print("✓ ALL DONE!")
print("=" * 80)

ds.close()
