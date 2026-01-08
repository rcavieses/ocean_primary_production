#!/usr/bin/env python3
"""
Script to create quinquennial (5-year) difference maps for each PFT variable
from the Gulf of California dataset (2000-2024).

Shows the difference between the reference period (2020-2024) and all previous periods:
- 2020-2024 minus 2000-2004
- 2020-2024 minus 2005-2009
- 2020-2024 minus 2010-2014
- 2020-2024 minus 2015-2019
"""

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import numpy as np

# Configuration
data_file = Path(__file__).parent.parent / 'data' / 'pft_golfo_california_2000_2024.nc'
output_dir = Path(__file__).parent.parent / 'data' / 'figures' / 'quinquennial_diff'
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


def compute_quinquennial_mean(ds, var, start_date, end_date):
    """Compute the mean for a variable over a quinquennial period."""
    data_period = ds[var].sel(time=slice(start_date, end_date))
    return data_period.mean(dim='time')


# Process each variable
for var in variables:
    if var not in ds:
        print(f"Variable {var} not found in dataset, skipping...")
        continue
    
    print(f"\nProcessing {var} ({var_descriptions.get(var, var)})...")
    
    # Compute means for all periods first
    period_means = {}
    for period_name, start_date, end_date in periods:
        print(f"  - Computing average for {period_name}...")
        period_means[period_name] = compute_quinquennial_mean(ds, var, start_date, end_date)
    
    # Reference period is the last one (2020-2024)
    reference_period = periods[-1][0]
    
    # Calculate differences: reference period minus all previous periods
    differences = []
    for i in range(len(periods) - 1):
        comparison_period = periods[i][0]
        diff = period_means[reference_period] - period_means[comparison_period]
        diff_label = f'{reference_period}\nminus\n{comparison_period}'
        differences.append((diff_label, diff))
        print(f"  - Computing difference: {reference_period} - {comparison_period}")
    
    # Create figure with subplots for each difference (2x2 grid for 4 differences)
    fig = plt.figure(figsize=(16, 12))
    
    # Calculate symmetric vmin and vmax for diverging colormap
    all_diffs = [d[1] for d in differences]
    max_abs = max([np.nanmax(np.abs(d.values)) for d in all_diffs])
    vmin = -max_abs
    vmax = max_abs
    
    for idx, (diff_label, diff_data) in enumerate(differences, 1):
        # Create subplot
        ax = fig.add_subplot(2, 2, idx, projection=ccrs.PlateCarree())
        
        # Add map features
        ax.coastlines(resolution='10m', linewidth=0.8)
        ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='black', linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        
        # Plot data with diverging colormap (red-white-blue)
        im = diff_data.plot(
            ax=ax,
            transform=ccrs.PlateCarree(),
            cmap='RdBu_r',  # Red for positive (increase), Blue for negative (decrease)
            vmin=vmin,
            vmax=vmax,
            add_colorbar=False
        )
        
        # Set title
        ax.set_title(diff_label, fontsize=11, fontweight='bold')
        
        # Add gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', 
                         alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        
        # Set extent to full Gulf of California region coordinates
        ax.set_extent([-115.0, -102.0, 18.0, 36.0], crs=ccrs.PlateCarree())
    
    # Add a single colorbar for all subplots
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label(f'Difference ({units.get(var, "")})', fontsize=12, fontweight='bold')
    
    # Add main title
    fig.suptitle(f'{var_descriptions.get(var, var)} - Differences vs Reference Period (2020-2024)\n'
                 'Red: Increase | Blue: Decrease',
                 fontsize=14, fontweight='bold', y=0.98)
    
    # Adjust layout
    plt.subplots_adjust(left=0.05, right=0.90, top=0.90, bottom=0.05, 
                       wspace=0.20, hspace=0.25)
    
    # Save figure
    output_file = output_dir / f'{var}_quinquennial_diff_maps.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  - Saved: {output_file}")
    plt.close()

# Close dataset
ds.close()

print("\n✓ All quinquennial difference maps have been generated successfully!")
print(f"Output directory: {output_dir}")
