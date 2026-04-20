#!/usr/bin/env python3
"""
Script to create quinquennial (5-year) average maps for each PFT variable
from the Gulf of California dataset (2000-2024).
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import numpy as np
import sys

# Importar configuración centralizada
sys.path.insert(0, str(Path(__file__).parent))
from config_gulf_california import GULF_OF_CALIFORNIA_BOUNDS, GULF_OF_CALIFORNIA_EXTENT, get_gulf_of_california_filter

# Configuration
base_dir = Path(__file__).parent.parent
data_file = base_dir / 'data' / 'pft_golfo_california_2000_2024.nc'
output_dir = base_dir / 'data' / 'figures'
output_dir.mkdir(parents=True, exist_ok=True)

# Define quinquennial periods
periods = [
    ('2000-2004', '2000-01-01', '2004-12-31'),
    ('2005-2009', '2005-01-01', '2009-12-31'),
    ('2010-2014', '2010-01-01', '2014-12-31'),
    ('2015-2019', '2015-01-01', '2019-12-31'),
    ('2020-2024', '2020-01-01', '2024-12-31')
]

# Load dataset
print("Loading dataset...")
ds = xr.open_dataset(data_file)

# Aplicar filtro espacial con shapefile del Golfo de California
mask = get_gulf_of_california_filter(ds, use_shapefile=True)

# Variables to plot (excluding uncertainty and flags)
variables = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO', 
             'PICO', 'PROCHLO', 'PROKAR']

# Variable descriptions for better titles
var_descriptions = {
    'CHL': 'Total Chlorophyll-a',
    'DIATO': 'Diatoms',
    'DINO': 'Dinoflagellates',
    'GREEN': 'Green Algae',
    'HAPTO': 'Haptophytes',
    'MICRO': 'Microphytoplankton',
    'NANO': 'Nanophytoplankton',
    'PICO': 'Picophytoplankton',
    'PROCHLO': 'Prochlorococcus',
    'PROKAR': 'Prokaryotes'
}

# Units for variables
units = {
    'CHL': 'mg m⁻³',
    'DIATO': 'mg m⁻³',
    'DINO': 'mg m⁻³',
    'GREEN': 'mg m⁻³',
    'HAPTO': 'mg m⁻³',
    'MICRO': 'mg m⁻³',
    'NANO': 'mg m⁻³',
    'PICO': 'mg m⁻³',
    'PROCHLO': 'mg m⁻³',
    'PROKAR': 'mg m⁻³'
}

# Process each variable
for var in variables:
    if var not in ds:
        print(f"Variable {var} not found in dataset, skipping...")
        continue
    
    print(f"\nProcessing {var} ({var_descriptions.get(var, var)})...")
    
    # Calculate vmin and vmax from all periods FIRST, before creating figure
    all_mins = []
    all_maxs = []
    for _, start, end in periods:
        period_data = ds[var].sel(time=slice(start, end), drop=True)
        if len(period_data.time) > 0:  # Only if period has data
            period_mean = period_data.mean(dim='time')
            try:
                min_val = float(period_mean.min().values)
                max_val = float(period_mean.max().values)
                if not np.isnan(min_val) and min_val != np.inf:
                    all_mins.append(min_val)
                if not np.isnan(max_val) and max_val != np.inf:
                    all_maxs.append(max_val)
            except (ValueError, TypeError):
                continue
    
    if len(all_mins) == 0 or len(all_maxs) == 0:
        print(f"  WARNING: No valid data found for {var}")
        continue
    
    vmin = min(all_mins)
    vmax = max(all_maxs)
    
    if np.isnan(vmin) or np.isnan(vmax) or vmin == vmax:
        print(f"  WARNING: Invalid min/max for {var}")
        continue
    
    # Create figure with subplots for each quinquennial period
    fig = plt.figure(figsize=(20, 12))
    
    for idx, (period_name, start_date, end_date) in enumerate(periods, 1):
        print(f"  - Computing average for {period_name}...")
        
        # Select time period
        data_period = ds[var].sel(time=slice(start_date, end_date))
        
        # Apply spatial mask (enmascarar puntos fuera del polígono del Golfo)
        data_period = data_period.where(mask, drop=False)
        
        # Calculate mean
        data_mean = data_period.mean(dim='time')
        
        # Create subplot
        ax = fig.add_subplot(2, 3, idx, projection=ccrs.PlateCarree())
        
        # Add map features
        ax.coastlines(resolution='10m', linewidth=0.8)
        ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='black', linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        
        # Plot data
        im = data_mean.plot(
            ax=ax,
            transform=ccrs.PlateCarree(),
            cmap='viridis',
            vmin=vmin,
            vmax=vmax,
            add_colorbar=False
        )
        
        # Set title
        ax.set_title(f'{period_name}', fontsize=12, fontweight='bold')
        
        # Add gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', 
                         alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        
        # Set extent to full Gulf of California region coordinates
        ax.set_extent(GULF_OF_CALIFORNIA_EXTENT, crs=ccrs.PlateCarree())
    
    # Add a single colorbar for all subplots
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label(f'{units.get(var, "")}', fontsize=12, fontweight='bold')
    
    # Add main title
    fig.suptitle(f'{var_descriptions.get(var, var)} - Quinquennial Averages (2000-2024)',
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Adjust layout
    plt.subplots_adjust(left=0.05, right=0.90, top=0.95, bottom=0.05, 
                       wspace=0.15, hspace=0.15)
    
    # Save figure
    output_file = output_dir / f'{var}_quinquennial_maps.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  - Saved: {output_file}")
    plt.close()

# Close dataset
ds.close()

print("\n✓ All quinquennial maps have been generated successfully!")
print(f"Output directory: {output_dir}")
