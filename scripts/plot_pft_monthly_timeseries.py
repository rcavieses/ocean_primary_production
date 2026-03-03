#!/usr/bin/env python3
"""
Script to create monthly time series plots for each PFT variable
from the Gulf of California dataset (2000-2024).

Shows the temporal evolution of monthly average concentrations.
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import sys

# Importar configuración centralizada
sys.path.insert(0, str(Path(__file__).parent))
from config_gulf_california import get_gulf_of_california_filter

# Suppress warnings
warnings.filterwarnings("ignore")

# Configuration
base_dir = Path(__file__).parent.parent
data_file = base_dir / 'data' / 'pft_golfo_california_2000_2024.nc'
output_dir = base_dir / 'data' / 'figures'
output_dir.mkdir(parents=True, exist_ok=True)

# Climate Data Files
nino_file = base_dir / 'data' / 'nino34.long.anom.csv'
mei_file = base_dir / 'data' / 'mei.exttimeseries.csv'
pdo_file = base_dir / 'data' / 'pdo.timeseries.sstens.csv'

# --- Data Loading Functions ---

def load_nino34(filepath):
    """Load NINO3.4 data"""
    try:
        # Based on inspection: header in line 1 (index 0), data starts after
        df = pd.read_csv(filepath, skiprows=1, header=None, names=['Date', 'NINO34'])
        df['Date'] = pd.to_datetime(df['Date'].str.strip())
        df['NINO34'] = pd.to_numeric(df['NINO34'], errors='coerce')
        # Filter -99.99
        df = df[df['NINO34'] > -90].dropna()
        return df.set_index('Date')['NINO34']
    except Exception as e:
        print(f"Error loading NINO3.4: {e}")
        return None

def load_pdo(filepath):
    """Load PDO data"""
    try:
        # Based on inspection: skip 1 line (header info), then Date, PDO
        df = pd.read_csv(filepath, skiprows=1, header=None, usecols=[0, 1], names=['Date', 'PDO'])
        df['Date'] = pd.to_datetime(df['Date'])
        df['PDO'] = pd.to_numeric(df['PDO'], errors='coerce')
        return df.set_index('Date')['PDO']
    except Exception as e:
        print(f"Error loading PDO: {e}")
        return None

def load_mei(filepath):
    """Load MEI data"""
    try:
        # Space separated, year + 12 months
        # 1979 0.46 0.29 ...
        chunks = []
        with open(filepath, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts or not parts[0].isdigit() or len(parts) < 13:
                    continue
                year = int(parts[0])
                for month_idx, val in enumerate(parts[1:13]):
                    try:
                         val_float = float(val)
                         if val_float > -90: # Check for nodata
                             date = pd.Timestamp(year=year, month=month_idx+1, day=1)
                             chunks.append({'Date': date, 'MEI': val_float})
                    except:
                        pass
        df = pd.DataFrame(chunks)
        return df.set_index('Date')['MEI']
    except Exception as e:
        print(f"Error loading MEI: {e}")
        return None

print("Loading climate indices...")
nino_series = load_nino34(nino_file)
mei_series = load_mei(mei_file)
pdo_series = load_pdo(pdo_file)

# Load dataset
print("Loading dataset...")
ds = xr.open_dataset(data_file)

# No aplicar filtro espacial (usar todo el dominio)
# Se evita el uso del shapefile para ejecutar sin filtro espacial

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

# Common time range
start_date = '2000-01-01'
end_date = '2024-12-31'

# Crop indices to dataset range
if nino_series is not None:
    nino_series = nino_series[start_date:end_date]
if mei_series is not None:
    mei_series = mei_series[start_date:end_date]
if pdo_series is not None:
    pdo_series = pdo_series[start_date:end_date]

# Process each variable
for var in variables:
    if var not in ds:
        print(f"Variable {var} not found in dataset, skipping...")
        continue
    
    print(f"\nProcessing {var} ({var_descriptions.get(var, var)})...")
    
    # Get the variable data (time-sliced)
    data = ds[var].sel(time=slice(start_date, end_date))

    # Compute spatial mean per time step in a memory-efficient loop
    times = data['time'].values
    values = []
    for i in range(len(times)):
        slice_arr = data.isel(time=i).values
        # compute mean over lat/lon ignoring NaNs
        mean_val = float(np.nanmean(slice_arr))
        values.append(mean_val)

    # Build pandas Series and resample to monthly means
    ts_series = pd.Series(data=values, index=pd.to_datetime(data['time'].values))
    ts_series = ts_series.resample('MS').mean().dropna()
    mean_val = ts_series.mean()
    std_val = ts_series.std()
    
    # Create figure with 2 subplots
    fig, axes = plt.subplots(2, 1, figsize=(16, 12))
    
    # ===== PLOT 1: Time Series + Rolling Mean =====
    ax1 = axes[0]
    ax1.plot(ts_series.index, ts_series.values, 
           linewidth=1.5, color='#2E86AB', alpha=0.8, label='Monthly Mean')
    
    # Add a rolling average (12-month moving average)
    rolling_mean = ts_series.rolling(window=12, center=True).mean()
    ax1.plot(rolling_mean.index, rolling_mean.values, 
           linewidth=2.5, color='#E63946', alpha=0.8, label='12-Month Moving Average')
    
    # Fill between to show variability
    ax1.fill_between(ts_series.index, ts_series.values, 
                   alpha=0.2, color='#2E86AB')
    
    # Add gridlines
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)
    
    # Labels and title
    ax1.set_ylabel(f'{units.get(var, "")}', fontsize=12, fontweight='bold')
    ax1.set_title(f'{var_descriptions.get(var, var)} - Monthly Time Series (2000-2024)',
                fontsize=14, fontweight='bold')
    
    # Add statistics box
    stats_text = f'Min: {ts_series.min():.2f}\nMax: {ts_series.max():.2f}\nMean: {mean_val:.2f}\nStd: {std_val:.2f}'
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes,
           fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', 
           facecolor='wheat', alpha=0.8), family='monospace')
    
    # Add legend
    ax1.legend(fontsize=11, loc='upper left', framealpha=0.95)
    
    # ===== PLOT 2: Anomaly + Climate Indices =====
    ax2 = axes[1]
    anomaly = ts_series - mean_val
    colors = ['#2ca02c' if x >= 0 else '#d62728' for x in anomaly]
    ax2.bar(anomaly.index, anomaly.values, width=25, 
           color=colors, alpha=0.6, edgecolor='black', linewidth=0.5)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    ax2.set_xlabel('Time', fontsize=11, fontweight='bold')
    ax2.set_ylabel(f'Anomaly ({units.get(var, "")})', fontsize=11, fontweight='bold')
    ax2.set_title(f'{var_descriptions.get(var, var)} - Monthly Anomaly (Deviation from Mean)',
                 fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.set_axisbelow(True)
    
    # ===== ADD CLIMATE INDICES ON SECONDARY AXIS =====
    ax2_twin = ax2.twinx()
    
    lines = []
    labels = []
    
    # Add NIÑO 3.4
    if nino_series is not None:
        nino_aligned = nino_series.reindex(ts_series.index, method='nearest')
        line1, = ax2_twin.plot(nino_aligned.index, nino_aligned.values, 
                              color='#FF9500', linewidth=2.5, label='NIÑO 3.4', zorder=5)
        lines.append(line1)
        labels.append('NIÑO 3.4')
    
    # Add MEI
    if mei_series is not None:
        mei_aligned = mei_series.reindex(ts_series.index, method='nearest')
        line2, = ax2_twin.plot(mei_aligned.index, mei_aligned.values, 
                              color='#9B59B6', linewidth=2, linestyle='--', label='MEI', zorder=4)
        lines.append(line2)
        labels.append('MEI')
    
    # Add PDO
    if pdo_series is not None:
        pdo_aligned = pdo_series.reindex(ts_series.index, method='nearest')
        line3, = ax2_twin.plot(pdo_aligned.index, pdo_aligned.values, 
                              color='#34495E', linewidth=2, linestyle=':', label='PDO', zorder=3)
        lines.append(line3)
        labels.append('PDO')
    
    ax2_twin.set_ylabel('Climate Index Value', fontsize=11, fontweight='bold')
    ax2_twin.tick_params(axis='y', labelsize=10)
    
    # Combined legend
    lines_anomaly, labels_anomaly = ax2.get_legend_handles_labels()
    if lines:
        ax2_twin.legend(lines + lines_anomaly, labels + labels_anomaly, 
                       loc='upper left', ncol=4, fontsize=10)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save combined figure
    output_file_combined = output_dir / f'{var}_timeseries_analysis.png'
    plt.savefig(output_file_combined, dpi=150, bbox_inches='tight')
    print(f"  - Saved: {output_file_combined}")
    plt.close()
    


# Close dataset
ds.close()

print("\n✓ All monthly time series plots have been generated successfully!")
print(f"Output directory: {output_dir}")
