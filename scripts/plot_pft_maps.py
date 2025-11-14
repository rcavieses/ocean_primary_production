#!/usr/bin/env python3

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path

data_file = Path('/data/pft_golfo_california_2000_2024.nc')
output_dir = Path('/data/figures')
output_dir.mkdir(parents=True, exist_ok=True)

ds = xr.open_dataset(data_file)

variables = ['DIATO', 'DINO', 'HAPTO', 'GREEN', 'PROKAR', 'CRYPTO', 'CHL']

for var in variables:
    if var not in ds:
        continue
    
    data_mean = ds[var].mean(dim='time')
    
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

ds.close()
