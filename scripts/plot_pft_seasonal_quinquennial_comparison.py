#!/usr/bin/env python3
"""
Script to compare seasonal averages (Spring, Summer, Autumn, Winter) 
across quinquennial periods for each PFT variable.

Seasons defined as:
- Spring (DJF): December, January, February
- Summer (MAM): March, April, May
- Autumn (JJA): June, July, August
- Winter (SON): September, October, November
"""

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import LogNorm

# Configuration
data_file = Path(__file__).parent.parent / 'data' / 'pft_golfo_california_2000_2024.nc'
output_dir = Path(__file__).parent.parent / 'data' / 'figures' / 'seasonal_analysis'
output_dir.mkdir(parents=True, exist_ok=True)

# Define quinquennial periods
periods = [
    ('2000-2004', '2000-01-01', '2004-12-31'),
    ('2005-2009', '2005-01-01', '2009-12-31'),
    ('2010-2014', '2010-01-01', '2014-12-31'),
    ('2015-2019', '2015-01-01', '2019-12-31'),
    ('2020-2024', '2020-01-01', '2024-12-31')
]

# Define seasons (month numbers)
seasons = {
    'Spring': [3, 4, 5],        # MAM
    'Summer': [6, 7, 8],        # JJA
    'Autumn': [9, 10, 11],      # SON
    'Winter': [12, 1, 2]        # DJF
}

# Load dataset
print("Loading dataset...")
ds = xr.open_dataset(data_file)

# Variables to analyze
variables = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO', 
             'PICO', 'PROCHLO', 'PROKAR']

# Variable descriptions
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

def get_seasonal_mean(data, season_months):
    """Extract seasonal data and compute mean."""
    seasonal_data = data.sel(time=data.time.dt.month.isin(season_months)).mean(dim='time')
    return seasonal_data

def get_spatial_mean(data):
    """Calculate spatial mean (average over all grid points)."""
    return float(data.mean().values)

# Process each variable
for var in variables:
    if var not in ds:
        print(f"Variable {var} not found in dataset, skipping...")
        continue
    
    print(f"\nProcessing {var} ({var_descriptions.get(var, var)})...")
    
    # Dictionary to store seasonal means for each quinquennial period
    seasonal_data = {season: [] for season in seasons.keys()}
    # Dictionary to store seasonal maps for each quinquennial period
    seasonal_maps = {season: [] for season in seasons.keys()}
    
    # Compute seasonal averages for each quinquennial period
    for period_name, start_date, end_date in periods:
        print(f"  - Computing seasonal averages for {period_name}...")
        
        # Select time period
        data_period = ds[var].sel(time=slice(start_date, end_date))
        
        # Compute seasonal means and spatial averages
        for season, months in seasons.items():
            seasonal_mean = get_seasonal_mean(data_period, months)
            spatial_mean = get_spatial_mean(seasonal_mean)
            seasonal_data[season].append(spatial_mean)
            seasonal_maps[season].append(seasonal_mean)
    
    # Create comparison figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    # Define colors for quinquennial periods
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    period_names = [p[0] for p in periods]
    
    # Plot each season
    for season_idx, (season, ax) in enumerate(zip(seasons.keys(), axes)):
        values = seasonal_data[season]
        x_pos = np.arange(len(period_names))
        
        bars = ax.bar(x_pos, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_xlabel('Quinquennial Period', fontsize=11, fontweight='bold')
        ax.set_ylabel(f'{units.get(var, "")}', fontsize=11, fontweight='bold')
        ax.set_title(f'{season}', fontsize=12, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(period_names, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
    
    # Add main title
    fig.suptitle(f'{var_descriptions.get(var, var)} - Seasonal Averages by Quinquennial Period (2000-2024)',
                 fontsize=14, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    # Save figure
    output_file = output_dir / f'{var}_seasonal_quinquennial_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  - Saved: {output_file}")
    plt.close()
    
    # Create a combined line plot for better trend visualization
    fig, ax = plt.subplots(figsize=(12, 7))
    
    season_colors = {'Spring': '#2ecc71', 'Summer': '#e74c3c', 
                    'Autumn': '#f39c12', 'Winter': '#3498db'}
    
    for season, values in seasonal_data.items():
        ax.plot(period_names, values, marker='o', linewidth=2.5, markersize=8,
               label=season, color=season_colors[season], alpha=0.8)
    
    ax.set_xlabel('Quinquennial Period', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'{units.get(var, "")}', fontsize=12, fontweight='bold')
    ax.set_title(f'{var_descriptions.get(var, var)} - Seasonal Trends (2000-2024)',
                fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save line plot
    output_file_line = output_dir / f'{var}_seasonal_trends.png'
    plt.savefig(output_file_line, dpi=300, bbox_inches='tight')
    print(f"  - Saved: {output_file_line}")
    plt.close()

    # Generate comparison maps (Log Scale)
    print(f"  - Generating comparison maps for {var}...")
    maps_output_dir = output_dir / 'maps'
    maps_output_dir.mkdir(exist_ok=True)

    for season in seasons.keys():
        # Create figure with 1 row, 5 columns (one for each period)
        fig, axes = plt.subplots(1, 5, figsize=(20, 5), subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Determine global min/max for the colorbar across all periods for this season
        # To ensure consistent color scale
        # Use log scale, so min must be > 0.
        
        # Collect all data to find min/max
        all_data = np.concatenate([m.values.flatten() for m in seasonal_maps[season]])
        all_data = all_data[~np.isnan(all_data)]
        all_data = all_data[all_data > 0] # Filter for log scale
        
        if len(all_data) == 0:
             # Handle empty data case
             vmin, vmax = 0.001, 1
        else:
             vmin, vmax = all_data.min(), all_data.max()
        
        for idx, (period_name, ax) in enumerate(zip(period_names, axes)):
            data_map = seasonal_maps[season][idx]
            
            ax.coastlines()
            ax.add_feature(cfeature.LAND, facecolor='lightgray')
            
            # Plot
            im = data_map.plot(
                ax=ax,
                transform=ccrs.PlateCarree(),
                cmap='viridis',
                norm=LogNorm(vmin=vmin, vmax=vmax),
                add_colorbar=False 
            )
            ax.set_title(f'{period_name}')
        
        # Add common colorbar
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
        fig.colorbar(im, cax=cbar_ax, label=f'{units.get(var, "")} (Log Scale)')
        
        fig.suptitle(f'{var_descriptions.get(var, var)} - {season} Comparison (Log Scale)', fontsize=16)
        
        output_map_file = maps_output_dir / f'{var}_{season}_comparison_map_log.png'
        plt.savefig(output_map_file, dpi=300, bbox_inches='tight')
        print(f"  - Saved: {output_map_file}")
        plt.close()

# Close dataset
ds.close()

print("\n✓ All seasonal comparison plots have been generated successfully!")
print(f"Output directory: {output_dir}")
