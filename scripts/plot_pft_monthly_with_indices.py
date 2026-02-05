#!/usr/bin/env python3
"""
Script to create monthly time series plots for each PFT variable
from the Gulf of California dataset (2000-2024), INCLUDING CLIMATE INDICES (MEI, PDO, NINO3.4).

Shows:
1. Temporal evolution (Mean + Rolling Mean)
2. Anomalies vs Climate Indices
"""

import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Configuration
base_dir = Path(__file__).parent.parent
data_file = base_dir / 'data' / 'pft_golfo_california_2000_2024.nc'
output_dir = base_dir / 'data' / 'figures' / 'timeseries_indices'
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

# --- Main Processing ---

print("Loading dataset...")
ds = xr.open_dataset(data_file)

# Variables to analyze
variables = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO', 
             'PICO', 'PROCHLO', 'PROKAR']

var_descriptions = {
    'CHL': 'Total Chlorophyll-a', 'DIATO': 'Diatoms', 'DINO': 'Dinoflagellates',
    'GREEN': 'Green Algae', 'HAPTO': 'Haptophytes', 'MICRO': 'Microphytoplankton',
    'NANO': 'Nanophytoplankton', 'PICO': 'Picophytoplankton',
    'PROCHLO': 'Prochlorococcus', 'PROKAR': 'Prokaryotes'
}

units = {k: 'mg m⁻³' for k in variables}

# Common time range
start_date = '2000-01-01'
end_date = '2024-12-31'

# Crop indices to dataset range
if nino_series is not None: nino_series = nino_series[start_date:end_date]
if mei_series is not None: mei_series = mei_series[start_date:end_date]
if pdo_series is not None: pdo_series = pdo_series[start_date:end_date]

for var in variables:
    if var not in ds:
        continue
    
    print(f"Processing {var}...")
    
    # 1. Calculate Monthly Means & Anomalies
    da = ds[var].sel(time=slice(start_date, end_date))
    temporal_mean = da.mean(dim=['latitude', 'longitude']).load() # Load into memory
    
    # Convert to pandas series for easy plotting
    ts_series = temporal_mean.to_pandas()
    
    # Calculate Anomaly
    climatology_mean = ts_series.mean()
    anomaly_series = ts_series - climatology_mean
    
    colors = ['#2ca02c' if x >= 0 else '#d62728' for x in anomaly_series]
    
    # --- Plot: Anomaly vs Indices ---
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [1, 1]})
    
    # Plot 1: Standard Time Series
    ax1 = axes[0]
    ax1.plot(ts_series.index, ts_series.values, color='#2E86AB', alpha=0.8, label='Monthly Mean')
    rolling = ts_series.rolling(window=12, center=True).mean()
    ax1.plot(rolling.index, rolling.values, color='#E63946', linewidth=2, label='12-Month Mean')
    ax1.set_ylabel(f'{units[var]}')
    ax1.set_title(f'{var_descriptions[var]} ({var}) - 2000-2024')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Anomaly vs Indices
    ax2 = axes[1]
    # Bar plot for Anomaly (Primary Axis)
    ax2.bar(anomaly_series.index, anomaly_series.values, color=colors, width=25, alpha=0.5, label=f'{var} Anomaly')
    ax2.set_ylabel(f'{var} Anomaly ({units[var]})', fontsize=12, fontweight='bold')
    ax2.set_title(f'Anomalies vs Climate Indices', fontsize=12)
    
    # Lines for Indices (Secondary Axis)
    ax3 = ax2.twinx()
    
    if nino_series is not None:
        idx_aligned = nino_series.reindex(ts_series.index, method='nearest')
        ax3.plot(idx_aligned.index, idx_aligned.values, color='#FF9500', linewidth=2, label='NIÑO 3.4')
        
    if mei_series is not None:
        idx_aligned = mei_series.reindex(ts_series.index, method='nearest')
        ax3.plot(idx_aligned.index, idx_aligned.values, color='#9B59B6', linewidth=1.5, linestyle='--', label='MEI')
        
    if pdo_series is not None:
        idx_aligned = pdo_series.reindex(ts_series.index, method='nearest')
        ax3.plot(idx_aligned.index, idx_aligned.values, color='#34495E', linewidth=1.5, linestyle=':', label='PDO')
    
    ax3.set_ylabel('Climate Index Value', fontsize=12, fontweight='bold')
    
    # Legends
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper left', ncol=4, fontsize=10)
    
    # Grid
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / f'{var}_timeseries_analysis.png', dpi=100)
    plt.close()
    
    print(f"Saved {var}_timeseries_analysis.png")

print("Done processing all variables.")
