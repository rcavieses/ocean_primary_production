#!/usr/bin/env python3

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

# Get base directory
base_dir = Path(__file__).parent.parent
data_file = base_dir / 'data' / 'pft_golfo_california_2000_2024.nc'
output_dir = base_dir / 'data' / 'figures'
output_dir.mkdir(parents=True, exist_ok=True)

ds = xr.open_dataset(data_file)

# Aplicar filtrado del Golfo de California por default
lat_mask, lon_mask = get_gulf_of_california_filter(ds)
ds = ds.isel(latitude=lat_mask, longitude=lon_mask)

variables = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO', 
             'PICO', 'PROCHLO', 'PROKAR']

for var in variables:
    if var not in ds:
        print(f"Variable {var} not found, skipping...")
        continue
    
    print(f"Creating map for {var}...")
    
    try:
        data_mean = ds[var].mean(dim='time')
        
        # Check if data is valid
        if np.isnan(float(data_mean.min().values)) or np.isnan(float(data_mean.max().values)):
            print(f"  WARNING: Invalid data for {var}, skipping...")
            continue
        
        fig = plt.figure(figsize=(10, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.coastlines()
        ax.add_feature(cfeature.LAND, facecolor='lightgray')
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        
        im = data_mean.plot(
            ax=ax,
            transform=ccrs.PlateCarree(),
            cmap='viridis',
            add_colorbar=True,
            cbar_kwargs={'label': f'{var} mean'}
        )
        
        ax.set_title(f'{var} - Time Average (2000-2024)')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        
        plt.tight_layout()
        plt.savefig(output_dir / f'{var}_mean_map.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {var}_mean_map.png")
    except Exception as e:
        print(f"  ERROR processing {var}: {str(e)}")

ds.close()
