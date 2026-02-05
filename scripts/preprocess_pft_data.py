#!/usr/bin/env python3
"""
Script to process the full PFT dataset with low memory footprint.
Processes data month by month and saves only spatial statistics.
"""

import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from collections import OrderedDict

warnings.filterwarnings("ignore")

# Configuration
base_dir = Path(__file__).parent.parent
data_file = base_dir / 'data' / 'pft_golfo_california_2000_2024.nc'
output_file = base_dir / 'data' / 'pft_monthly_statistics.nc'

# Variables to process
VARIABLES = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO', 
             'PICO', 'PROCHLO', 'PROKAR']

TIME_RANGE = ('2000-01-01', '2024-12-31')

print("=" * 70)
print("PROCESSING PFT DATA - LOW MEMORY MODE")
print("=" * 70)

print("\nLoading dataset...")
ds = xr.open_dataset(data_file)

# Filter by time range
ds_period = ds.sel(time=slice(TIME_RANGE[0], TIME_RANGE[1]))

print(f"Dataset loaded")
print(f"Time range: {ds_period.time.values[0]} to {ds_period.time.values[-1]}")
print(f"Total timepoints: {len(ds_period.time)}")

# Get unique year-months
times = pd.DatetimeIndex(ds_period.time.values)
year_months = times.to_period('M').unique()
print(f"Unique months: {len(year_months)}")

# Dictionaries to store monthly statistics
monthly_stats = OrderedDict()

print("\n" + "=" * 70)
print("CALCULATING MONTHLY STATISTICS")
print("=" * 70)

# Process month by month
for idx, ym in enumerate(year_months):
    year = ym.year
    month = ym.month
    
    # Select data for this month
    mask = (times.year == year) & (times.month == month)
    indices = np.where(mask)[0]
    
    if len(indices) == 0:
        continue
    
    if idx % 12 == 0:
        print(f"\nProcessing year {year}...")
    
    # Get timestamps for this month
    month_times = times[mask]
    month_key = f"{year:04d}-{month:02d}"
    
    # Extract and process each variable
    stats_dict = {'time': np.datetime64(f'{year:04d}-{month:02d}-01')}
    
    for var in VARIABLES:
        if var not in ds_period:
            continue
        
        # Load only this month's data for this variable
        da_month = ds_period[var].isel(time=indices)
        
        # Calculate spatial statistics (mean over all days in month, then over space)
        da_time_mean = da_month.mean(dim='time')
        stats_dict[f'{var}_mean'] = float(da_time_mean.mean(dim=['latitude', 'longitude']).values)
        stats_dict[f'{var}_std'] = float(da_time_mean.std(dim=['latitude', 'longitude']).values)
        stats_dict[f'{var}_min'] = float(da_time_mean.min(dim=['latitude', 'longitude']).values)
        stats_dict[f'{var}_max'] = float(da_time_mean.max(dim=['latitude', 'longitude']).values)
    
    monthly_stats[month_key] = stats_dict

print(f"\nProcessed {len(monthly_stats)} months")

# Convert to DataFrame
print("\nConverting to DataFrame...")
df_stats = pd.DataFrame.from_dict(monthly_stats, orient='index')
df_stats['time'] = pd.to_datetime(df_stats['time'])
df_stats = df_stats.set_index('time')
df_stats = df_stats.sort_index()

print(f"DataFrame shape: {df_stats.shape}")

# Convert to xarray Dataset
print("Converting to xarray Dataset...")
ds_stats = xr.Dataset({
    col: (['time'], df_stats[col].values) for col in df_stats.columns
}, coords={'time': df_stats.index})

# Add metadata
ds_stats.attrs['description'] = 'Monthly statistics for PFT variables (Gulf of California 2000-2024)'
ds_stats.attrs['processed_date'] = pd.Timestamp.now().isoformat()
ds_stats.attrs['original_file'] = str(data_file)
ds_stats.attrs['statistics'] = 'mean, std, min, max (calculated across latitude and longitude)'

# Save to file
print(f"\nSaving to {output_file}...")
ds_stats.to_netcdf(output_file, mode='w', engine='netcdf4')

print(f"\n✓ File saved successfully!")
print(f"  Output file: {output_file}")
print(f"  File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Original file size: {data_file.stat().st_size / 1024 / 1024:.2f} MB")
print(f"Statistics file size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
compression_ratio = (1 - output_file.stat().st_size / data_file.stat().st_size) * 100
print(f"Compression ratio: {compression_ratio:.1f}%")

print("\nDataset dimensions:", dict(ds_stats.dims))
print("Variables stored:")
for var in sorted(ds_stats.data_vars):
    print(f"  - {var}")

print("\n" + "=" * 70)

ds.close()
ds_stats.close()
