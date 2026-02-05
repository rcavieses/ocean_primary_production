#!/usr/bin/env python3
"""
Script to create latitude-time heatmaps for each PFT variable
from the Gulf of California dataset (2000-2024).

Visualization:
- X-axis: Month (1-12)
- Y-axis: Latitude
- Color intensity: Average measured value for the variable

Generates plots for each plankton type, grouped by species and size classes.
"""

import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURATION
# ============================================================================

base_dir = Path(__file__).parent.parent
data_file = base_dir / 'data' / 'pft_golfo_california_2000_2024.nc'
output_dir = base_dir / 'data' / 'figures' / 'latseries'
output_dir.mkdir(parents=True, exist_ok=True)

# ============================================================================
# VARIABLE GROUPINGS
# ============================================================================

# Variables grouped by species type
SPECIES_GROUPS = {
    'Species_Diatoms': {
        'variables': ['DIATO'],
        'description': 'Diatoms'
    },
    'Species_Dinoflagellates': {
        'variables': ['DINO'],
        'description': 'Dinoflagellates'
    },
    'Species_GreenAlgae': {
        'variables': ['GREEN'],
        'description': 'Green Algae'
    },
    'Species_Haptophytes': {
        'variables': ['HAPTO'],
        'description': 'Haptophytes'
    },
    'Species_Prokaryotes': {
        'variables': ['PROKAR'],
        'description': 'Prokaryotes'
    },
    'Species_Prochlorococcus': {
        'variables': ['PROCHLO'],
        'description': 'Prochlorococcus'
    }
}

# Variables grouped by size class
SIZE_GROUPS = {
    'Size_Microphytoplankton': {
        'variables': ['MICRO'],
        'description': 'Microphytoplankton (>20 μm)'
    },
    'Size_Nanophytoplankton': {
        'variables': ['NANO'],
        'description': 'Nanophytoplankton (2-20 μm)'
    },
    'Size_Picophytoplankton': {
        'variables': ['PICO'],
        'description': 'Picophytoplankton (<2 μm)'
    }
}

# Total chlorophyll-a
TOTAL_GROUPS = {
    'Total_Chlorophyll': {
        'variables': ['CHL'],
        'description': 'Total Chlorophyll-a'
    }
}

# All variable descriptions
VAR_DESCRIPTIONS = {
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

UNITS = {k: 'mg m⁻³' for k in VAR_DESCRIPTIONS.keys()}

# Time range
START_DATE = '2000-01-01'
END_DATE = '2024-12-31'

# Colormap and figure parameters
CMAP = 'YlOrRd'
DPI = 300

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def compute_latitude_time_matrix(da, latitude_bins=None):
    """
    Compute a latitude-time matrix with monthly averages.
    Optimized for low memory usage.
    
    Parameters:
    -----------
    da : xr.DataArray
        Data array with dimensions (time, latitude, longitude)
    latitude_bins : int or None
        Number of latitude bins to use. If None, uses original latitude resolution.
    
    Returns:
    --------
    matrix : np.ndarray
        2D array (latitude x month) with monthly averages
    lat_values : np.ndarray
        Latitude values for rows
    """
    
    # Average across longitude to get (time, latitude)
    da_lat_time = da.mean(dim='longitude').load()
    
    # Resample to monthly first to reduce time points
    da_monthly = da_lat_time.resample(time='MS').mean(dim='time')
    
    # Convert to pandas DataFrame
    df = da_monthly.to_pandas()  # Shape: (time, latitude)
    
    # Add month column
    df['month'] = df.index.month
    df['year'] = df.index.year
    
    # Group by month across all years and calculate mean
    monthly_avg = df.groupby('month')[df.columns[:-2]].mean()  # Shape: (12, latitude)
    
    # Transpose to get latitude x month
    matrix = monthly_avg.T.values  # Shape: (latitude, 12)
    lat_values = monthly_avg.T.index.values
    
    del da_lat_time, da_monthly, df  # Free memory
    
    return matrix, lat_values


def create_latitude_time_heatmap(variable, var_group_name, var_group_desc, 
                                 da, output_dir, cmap=CMAP, dpi=DPI):
    """
    Create and save a latitude-time heatmap for a single variable.
    
    Parameters:
    -----------
    variable : str
        Variable name (e.g., 'CHL', 'DIATO')
    var_group_name : str
        Group identifier (e.g., 'Species_Diatoms')
    var_group_desc : str
        Human-readable description
    da : xr.DataArray
        The data array for this variable (already filtered by time)
    output_dir : Path
        Output directory for figures
    cmap : str
        Colormap name
    dpi : int
        Figure resolution
    """
    
    print(f"    Processing {variable} ({var_group_desc})...")
    
    # Compute latitude-time matrix
    matrix, lat_values = compute_latitude_time_matrix(da)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Create heatmap
    im = ax.imshow(
        matrix,
        aspect='auto',
        cmap=cmap,
        interpolation='bilinear',
        origin='lower'
    )
    
    # Set axes
    ax.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitude (°N)', fontsize=12, fontweight='bold')
    ax.set_title(
        f'{VAR_DESCRIPTIONS[variable]} - Latitude-Time Pattern\n'
        f'Average monthly concentration (2000-2024)',
        fontsize=14, fontweight='bold', pad=20
    )
    
    # Set x-axis ticks (months)
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    ax.set_xticks(np.arange(12))
    ax.set_xticklabels(month_labels, fontsize=10)
    
    # Set y-axis ticks (latitude) - show every nth latitude
    lat_tick_step = max(1, len(lat_values) // 10)  # Show ~10 latitude ticks
    lat_indices = np.arange(0, len(lat_values), lat_tick_step)
    ax.set_yticks(lat_indices)
    ax.set_yticklabels([f'{lat_values[i]:.2f}' for i in lat_indices], fontsize=9)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, label=UNITS[variable], pad=0.02)
    cbar.ax.tick_params(labelsize=9)
    
    # Add grid for better readability
    ax.set_xticks(np.arange(-0.5, 12, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(lat_values), lat_tick_step), minor=True)
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.1, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    output_file = output_dir / f'{var_group_name}_{variable}_latseries.png'
    plt.savefig(output_file, dpi=dpi, bbox_inches='tight')
    print(f"      ✓ Saved: {output_file.name}")
    plt.close()


# ============================================================================
# MAIN PROCESSING
# ============================================================================

print("=" * 70)
print("LATITUDE-TIME HEATMAP GENERATION")
print("=" * 70)

print("\nLoading dataset...")
ds = xr.open_dataset(data_file)

# Process by species group
print("\n" + "=" * 70)
print("PROCESSING BY SPECIES GROUP")
print("=" * 70)

for group_key, group_info in SPECIES_GROUPS.items():
    print(f"\n{group_info['description']} Group:")
    for var in group_info['variables']:
        if var in ds:
            print(f"  Creating heatmap for {var}...")
            # Load only this variable
            da = ds[var].sel(time=slice(START_DATE, END_DATE))
            create_latitude_time_heatmap(
                var, group_key, group_info['description'], da, output_dir
            )
            del da  # Free memory immediately
        else:
            print(f"  ✗ Variable {var} not found in dataset")

# Process by size group
print("\n" + "=" * 70)
print("PROCESSING BY SIZE CLASS")
print("=" * 70)

for group_key, group_info in SIZE_GROUPS.items():
    print(f"\n{group_info['description']} Group:")
    for var in group_info['variables']:
        if var in ds:
            print(f"  Creating heatmap for {var}...")
            # Load only this variable
            da = ds[var].sel(time=slice(START_DATE, END_DATE))
            create_latitude_time_heatmap(
                var, group_key, group_info['description'], da, output_dir
            )
            del da  # Free memory immediately
        else:
            print(f"  ✗ Variable {var} not found in dataset")

# Process total chlorophyll
print("\n" + "=" * 70)
print("PROCESSING TOTAL CHLOROPHYLL")
print("=" * 70)

for group_key, group_info in TOTAL_GROUPS.items():
    print(f"\n{group_info['description']} Group:")
    for var in group_info['variables']:
        if var in ds:
            print(f"  Creating heatmap for {var}...")
            # Load only this variable
            da = ds[var].sel(time=slice(START_DATE, END_DATE))
            create_latitude_time_heatmap(
                var, group_key, group_info['description'], da, output_dir
            )
            del da  # Free memory immediately
        else:
            print(f"  ✗ Variable {var} not found in dataset")

print("\n" + "=" * 70)
print(f"✓ All latitude-time heatmaps generated successfully!")
print(f"  Output directory: {output_dir}")
print("=" * 70)

ds.close()
