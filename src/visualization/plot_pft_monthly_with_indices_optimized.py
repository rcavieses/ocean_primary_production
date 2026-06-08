#!/usr/bin/env python3
"""
Script to create monthly time series plots with climate indices
using the compressed monthly statistics file (efficient, low-memory).

Shows:
1. Temporal evolution (Mean + Rolling Mean)
2. Anomalies vs Climate Indices (MEI, PDO, NINO3.4) on secondary axis

Uses: pft_monthly_statistics.nc instead of full dataset

NOTA IMPORTANTE SOBRE FILTRADO ESPACIAL:
Este script usa datos pre-computados que ya han sido filtrados espacialmente
al Golfo de California usando shapefile polygon filter. Todos los resultados
muestran ÚNICAMENTE datos dentro del Golfo de California.
"""

import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'pipeline'))
from config_gulf_california import get_gulf_of_california_filter

# Suppress warnings
warnings.filterwarnings("ignore")

# Configuration
base_dir = Path(__file__).parent.parent.parent
stats_file = base_dir / 'data' / 'processed' / 'pft_monthly_statistics.nc'
output_dir = base_dir / 'results' / 'satellite' / 'figures' / 'timeseries_indices'
output_dir.mkdir(parents=True, exist_ok=True)

# Climate Data Files
nino_file = base_dir / 'data' / 'raw' / 'nino34.long.anom.csv'
mei_file = base_dir / 'data' / 'raw' / 'mei.exttimeseries.csv'
pdo_file = base_dir / 'data' / 'raw' / 'pdo.timeseries.sstens.csv'

# --- Data Loading Functions ---

def load_nino34(filepath):
    """Load NINO3.4 data"""
    try:
        df = pd.read_csv(filepath, skiprows=1, header=None, names=['Date', 'NINO34'])
        df['Date'] = pd.to_datetime(df['Date'].str.strip())
        df['NINO34'] = pd.to_numeric(df['NINO34'], errors='coerce')
        df = df[df['NINO34'] > -90].dropna()
        return df.set_index('Date')['NINO34']
    except Exception as e:
        print(f"Error loading NINO3.4: {e}")
        return None

def load_pdo(filepath):
    """Load PDO data"""
    try:
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
                         if val_float > -90:
                             date = pd.Timestamp(year=year, month=month_idx+1, day=1)
                             chunks.append({'Date': date, 'MEI': val_float})
                    except:
                        pass
        df = pd.DataFrame(chunks)
        return df.set_index('Date')['MEI']
    except Exception as e:
        print(f"Error loading MEI: {e}")
        return None

print("=" * 70)
print("GENERATING TIME SERIES WITH CLIMATE INDICES")
print("=" * 70)

print("\nLoading climate indices...")
nino_series = load_nino34(nino_file)
mei_series = load_mei(mei_file)
pdo_series = load_pdo(pdo_file)

print("Loading statistics file...")
if not stats_file.exists():
    print(f"ERROR: Statistics file not found: {stats_file}")
    print("Run preprocess_pft_data.py first.")
    exit(1)

ds = xr.open_dataset(stats_file)

# Nota: Los datos en el archivo de estadísticas ya han sido filtrados
# usando el polígono del shapefile del Golfo de California durante
# la fase de preprocesamiento (preprocess_pft_data.py)

# Variables to analyze
variables = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO', 
             'PICO', 'PROCHLO', 'PROKAR']

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

units = {k: 'mg m⁻³' for k in variables}

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

# --- Main Processing ---

for i, var in enumerate(variables, 1):
    var_mean = f'{var}_mean'
    
    if var_mean not in ds:
        print(f"  ⚠ {var} not found in statistics file")
        continue
    
    print(f"\n{i}. Processing {var}...")
    
    # Extract time series from statistics
    ts_series = ds[var_mean].to_pandas()
    
    # Ensure datetime index
    if not isinstance(ts_series.index, pd.DatetimeIndex):
        ts_series.index = pd.to_datetime(ts_series.index)
    
    # Calculate Anomaly
    climatology_mean = ts_series.mean()
    anomaly_series = ts_series - climatology_mean
    
    colors = ['#2ca02c' if x >= 0 else '#d62728' for x in anomaly_series]
    
    # --- Create Figure ---
    fig, axes = plt.subplots(2, 1, figsize=(15, 11), gridspec_kw={'height_ratios': [1, 1]})
    
    # Plot 1: Standard Time Series with Rolling Mean
    ax1 = axes[0]
    ax1.plot(ts_series.index, ts_series.values, color='#2E86AB', alpha=0.7, linewidth=1.5, label='Monthly Mean')
    
    # Rolling mean (12 months)
    rolling = ts_series.rolling(window=12, center=True).mean()
    ax1.plot(rolling.index, rolling.values, color='#E63946', linewidth=2.5, label='12-Month Rolling Mean')
    
    ax1.set_ylabel(f'{var_descriptions[var]} ({units[var]})', fontsize=11, fontweight='bold')
    ax1.set_title(f'{var_descriptions[var]} ({var}) - Monthly Time Series (2000-2024)', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xlim(ts_series.index.min(), ts_series.index.max())
    
    # Plot 2: Anomaly vs Climate Indices
    ax2 = axes[1]
    
    # Bar plot for Anomaly (Primary Axis)
    ax2.bar(anomaly_series.index, anomaly_series.values, 
            color=colors, width=20, alpha=0.6, label=f'{var} Anomaly')
    ax2.set_ylabel(f'{var} Anomaly ({units[var]})', fontsize=11, fontweight='bold')
    ax2.set_title(f'{var_descriptions[var]} - Anomalies vs Climate Indices', fontsize=12, fontweight='bold')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    
    # Create secondary axis for climate indices
    ax3 = ax2.twinx()
    
    # Plot climate indices
    line_styles = {
        'nino': ('-', '#FF9500', 2.0, 'NIÑO 3.4'),
        'mei': ('--', '#9B59B6', 1.8, 'MEI'),
        'pdo': (':', '#34495E', 1.8, 'PDO')
    }
    
    lines_list = []
    labels_list = []
    
    if nino_series is not None and len(nino_series) > 0:
        idx_aligned = nino_series.reindex(ts_series.index, method='nearest')
        line, = ax3.plot(idx_aligned.index, idx_aligned.values, 
                        linestyle=line_styles['nino'][0], 
                        color=line_styles['nino'][1], 
                        linewidth=line_styles['nino'][2], 
                        label=line_styles['nino'][3], alpha=0.8)
        lines_list.append(line)
        labels_list.append(line_styles['nino'][3])
        
    if mei_series is not None and len(mei_series) > 0:
        idx_aligned = mei_series.reindex(ts_series.index, method='nearest')
        line, = ax3.plot(idx_aligned.index, idx_aligned.values, 
                        linestyle=line_styles['mei'][0], 
                        color=line_styles['mei'][1], 
                        linewidth=line_styles['mei'][2], 
                        label=line_styles['mei'][3], alpha=0.8)
        lines_list.append(line)
        labels_list.append(line_styles['mei'][3])
        
    if pdo_series is not None and len(pdo_series) > 0:
        idx_aligned = pdo_series.reindex(ts_series.index, method='nearest')
        line, = ax3.plot(idx_aligned.index, idx_aligned.values, 
                        linestyle=line_styles['pdo'][0], 
                        color=line_styles['pdo'][1], 
                        linewidth=line_styles['pdo'][2], 
                        label=line_styles['pdo'][3], alpha=0.8)
        lines_list.append(line)
        labels_list.append(line_styles['pdo'][3])
    
    ax3.set_ylabel('Climate Index Value', fontsize=11, fontweight='bold')
    ax3.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.3)
    
    # Combined legend
    bars = ax2.patches[:1] if ax2.patches else []
    if bars:
        all_handles = bars + lines_list
        all_labels = [f'{var} Anomaly'] + labels_list
    else:
        all_handles = lines_list
        all_labels = labels_list
    
    ax3.legend(all_handles, all_labels, loc='upper left', ncol=4, fontsize=10, framealpha=0.95)
    
    # Grid
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xlim(ts_series.index.min(), ts_series.index.max())
    
    plt.tight_layout()
    output_file = output_dir / f'{var}_timeseries_with_indices.png'
    plt.savefig(output_file, dpi=100, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file.name}")

print("\n" + "=" * 70)
print("✓ All time series with climate indices generated successfully!")
print("=" * 70)
