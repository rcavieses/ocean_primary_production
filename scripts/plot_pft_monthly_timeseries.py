#!/usr/bin/env python3
"""
Script to create monthly time series plots for each PFT variable
from the Gulf of California dataset (2000-2024).

Shows the temporal evolution of monthly average concentrations.
"""

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuration
data_file = Path(__file__).parent.parent / 'data' / 'pft_golfo_california_2000_2024.nc'
output_dir = Path(__file__).parent.parent / 'data' / 'figures' / 'timeseries'
output_dir.mkdir(parents=True, exist_ok=True)

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

# Process each variable
for var in variables:
    if var not in ds:
        print(f"Variable {var} not found in dataset, skipping...")
        continue
    
    print(f"\nProcessing {var} ({var_descriptions.get(var, var)})...")
    
    # Get the variable data
    data = ds[var]
    
    # Calculate spatial mean (average over all grid points) for each time step
    temporal_mean = data.mean(dim=['lat', 'lon'])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 7))
    
    # Plot time series
    ax.plot(temporal_mean.time.values, temporal_mean.values, 
           linewidth=1.5, color='#2E86AB', alpha=0.8, label='Monthly Mean')
    
    # Add a rolling average (12-month moving average)
    rolling_mean = temporal_mean.rolling(time=12, center=True).mean()
    ax.plot(rolling_mean.time.values, rolling_mean.values, 
           linewidth=2.5, color='#E63946', alpha=0.8, label='12-Month Moving Average')
    
    # Fill between to show variability
    ax.fill_between(temporal_mean.time.values, temporal_mean.values, 
                   alpha=0.2, color='#2E86AB')
    
    # Add gridlines
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Labels and title
    ax.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'{units.get(var, "")}', fontsize=12, fontweight='bold')
    ax.set_title(f'{var_descriptions.get(var, var)} - Monthly Time Series (2000-2024)',
                fontsize=14, fontweight='bold')
    
    # Format x-axis
    ax.tick_params(axis='both', which='major', labelsize=10)
    plt.xticks(rotation=45, ha='right')
    
    # Add legend
    ax.legend(fontsize=11, loc='best', framealpha=0.95)
    
    # Add statistics box
    min_val = temporal_mean.min().values
    max_val = temporal_mean.max().values
    mean_val = temporal_mean.mean().values
    std_val = temporal_mean.std().values
    
    stats_text = f'Min: {min_val:.2f}\nMax: {max_val:.2f}\nMean: {mean_val:.2f}\nStd: {std_val:.2f}'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', 
           facecolor='wheat', alpha=0.8), family='monospace')
    
    plt.tight_layout()
    
    # Save figure
    output_file = output_dir / f'{var}_monthly_timeseries.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  - Saved: {output_file}")
    plt.close()
    
    # Create an additional figure with subplots for better visualization
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    
    # Plot 1: Time series with confidence interval
    ax1 = axes[0]
    ax1.plot(temporal_mean.time.values, temporal_mean.values, 
            linewidth=1.5, color='#2E86AB', alpha=0.8, label='Monthly Mean')
    ax1.fill_between(temporal_mean.time.values, temporal_mean.values, 
                    alpha=0.2, color='#2E86AB')
    ax1.set_ylabel(f'{units.get(var, "")}', fontsize=11, fontweight='bold')
    ax1.set_title(f'{var_descriptions.get(var, var)} - Monthly Average with 12-Month Moving Average',
                 fontsize=12, fontweight='bold')
    ax1.plot(rolling_mean.time.values, rolling_mean.values, 
            linewidth=2.5, color='#E63946', alpha=0.8, label='12-Month Moving Average')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)
    ax1.legend(fontsize=10, loc='best', framealpha=0.95)
    
    # Plot 2: Monthly anomaly (deviation from mean)
    ax2 = axes[1]
    anomaly = temporal_mean - mean_val
    ax2.bar(temporal_mean.time.values, anomaly.values, width=20, 
           color=np.where(anomaly.values >= 0, '#2ca02c', '#d62728'), 
           alpha=0.7, edgecolor='black', linewidth=0.5)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    ax2.set_xlabel('Time', fontsize=11, fontweight='bold')
    ax2.set_ylabel(f'Anomaly ({units.get(var, "")})', fontsize=11, fontweight='bold')
    ax2.set_title(f'{var_descriptions.get(var, var)} - Monthly Anomaly (Deviation from Mean)',
                 fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.set_axisbelow(True)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save combined figure
    output_file_combined = output_dir / f'{var}_timeseries_analysis.png'
    plt.savefig(output_file_combined, dpi=300, bbox_inches='tight')
    print(f"  - Saved: {output_file_combined}")
    plt.close()

# Close dataset
ds.close()

print("\n✓ All monthly time series plots have been generated successfully!")
print(f"Output directory: {output_dir}")
