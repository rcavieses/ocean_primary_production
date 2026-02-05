#!/usr/bin/env python3
"""
Script to create percentage composition plots for PFT groups.
Uses preprocessed monthly statistics to save memory.

Generates:
1. Species composition (% of total chlorophyll-a)
2. Size class composition (% of total chlorophyll-a)
3. Time series of composition evolution
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import json

warnings.filterwarnings("ignore")

# Configuration
base_dir = Path(__file__).parent.parent
stats_file = base_dir / 'data' / 'pft_monthly_statistics.nc'

# Check for filter info (when running from run_all_map_scripts_filtered.py)
filter_info_file = base_dir / 'data' / 'pft_golfo_california_FILTER_INFO.json'
if filter_info_file.exists():
    output_subdir = 'filtered_gulf_california'
else:
    output_subdir = 'composition'

output_dir = base_dir / 'data' / 'figures' / output_subdir
output_dir.mkdir(parents=True, exist_ok=True)

# Variable groupings
SPECIES_VARS = {
    'Diatomeas': 'DIATO_mean',
    'Dinoflagelados': 'DINO_mean',
    'Algas Verdes': 'GREEN_mean',
    'Haptófitos': 'HAPTO_mean',
    'Proclorococcus': 'PROCHLO_mean',
    'Procariontes': 'PROKAR_mean'
}

SIZE_VARS = {
    'Microfitoplancton (>20 μm)': 'MICRO_mean',
    'Nanofitoplancton (2-20 μm)': 'NANO_mean',
    'Picofitoplancton (<2 μm)': 'PICO_mean'
}

print("=" * 70)
print("GENERATING PERCENTAGE COMPOSITION FIGURES")
print("=" * 70)

# Load preprocessed statistics
print("\nLoading monthly statistics...")
if not stats_file.exists():
    print(f"✗ Statistics file not found: {stats_file}")
    print("  Run preprocess_pft_data.py first")
    exit(1)

ds_stats = xr.open_dataset(stats_file)
print(f"✓ Statistics file loaded")
print(f"  Shape: {len(ds_stats.time)} months")
print(f"  Variables: {len(ds_stats.data_vars)}")

# ============================================================================
# 1. SPECIES COMPOSITION PIE CHART
# ============================================================================
print("\n1. Creating species composition pie chart...")

species_values = {}
for name, var in SPECIES_VARS.items():
    if var in ds_stats:
        val = float(ds_stats[var].mean().values)
        if not np.isnan(val) and val > 0:
            species_values[name] = val
    else:
        print(f"   Warning: {var} not found")

# Skip if no valid data
if len(species_values) == 0:
    print("   ✗ No valid data for species composition")
else:
    # Calculate percentages
    total_species = sum(species_values.values())
    if total_species > 0:
        species_percentages = {k: (v / total_species) * 100 for k, v in species_values.items()}

        # Create pie chart
        fig, ax = plt.subplots(figsize=(12, 8))
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']
        wedges, texts, autotexts = ax.pie(
            species_percentages.values(),
            labels=species_percentages.keys(),
            autopct='%1.1f%%',
            startangle=90,
            colors=colors[:len(species_percentages)],
            textprops={'fontsize': 11, 'weight': 'bold'}
        )

        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(12)

        ax.set_title(
            'Composición Porcentual de Especies de Fitoplancton\n(Promedio 2000-2024)',
            fontsize=14, fontweight='bold', pad=20
        )

        plt.tight_layout()
        plt.savefig(output_dir / 'species_composition_pie.png', dpi=300, bbox_inches='tight')
        print("   ✓ Saved: species_composition_pie.png")
plt.close()

# ============================================================================
# 2. SIZE CLASS COMPOSITION PIE CHART
# ============================================================================
print("\n2. Creating size class composition pie chart...")

size_values = {}
for name, var in SIZE_VARS.items():
    if var in ds_stats:
        val = float(ds_stats[var].mean().values)
        if not np.isnan(val) and val > 0:
            size_values[name] = val
    else:
        print(f"   Warning: {var} not found")

# Skip if no valid data
if len(size_values) == 0:
    print("   ✗ No valid data for size composition")
else:
    # Calculate percentages
    total_size = sum(size_values.values())
    if total_size > 0:
        size_percentages = {k: (v / total_size) * 100 for k, v in size_values.items()}

        # Create pie chart
        fig, ax = plt.subplots(figsize=(12, 8))
        colors_size = ['#3498DB', '#E74C3C', '#2ECC71']
        wedges, texts, autotexts = ax.pie(
            size_percentages.values(),
            labels=size_percentages.keys(),
            autopct='%1.1f%%',
            startangle=90,
            colors=colors_size[:len(size_percentages)],
            textprops={'fontsize': 11, 'weight': 'bold'}
        )

        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(12)

        ax.set_title(
            'Composición Porcentual por Clase de Tamaño\n(Promedio 2000-2024)',
            fontsize=14, fontweight='bold', pad=20
        )

        plt.tight_layout()
        plt.savefig(output_dir / 'size_composition_pie.png', dpi=300, bbox_inches='tight')
        print("   ✓ Saved: size_composition_pie.png")
plt.close()

# ============================================================================
# 3. TIME SERIES OF SPECIES COMPOSITION
# ============================================================================
print("\n3. Creating species composition time series...")

# Create DataFrame from statistics
df_species = pd.DataFrame({
    name: ds_stats[var].values for name, var in SPECIES_VARS.items()
}, index=pd.DatetimeIndex(ds_stats.time.values))

# Calculate percentage composition over time
df_species_pct = df_species.div(df_species.sum(axis=1), axis=0) * 100

# Plot
fig, ax = plt.subplots(figsize=(14, 8))

for column in df_species_pct.columns:
    ax.plot(df_species_pct.index, df_species_pct[column], linewidth=2, label=column, marker='o', markersize=3)

ax.set_xlabel('Año', fontsize=12, fontweight='bold')
ax.set_ylabel('Composición Porcentual (%)', fontsize=12, fontweight='bold')
ax.set_title(
    'Evolución Temporal de la Composición de Especies\n(Promedio espacial, 2000-2024)',
    fontsize=14, fontweight='bold', pad=20
)
ax.legend(loc='best', fontsize=10, framealpha=0.95)
ax.grid(True, alpha=0.3)
ax.set_ylim(0, 100)

plt.tight_layout()
plt.savefig(output_dir / 'species_composition_timeseries.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: species_composition_timeseries.png")
plt.close()

# ============================================================================
# 4. TIME SERIES OF SIZE CLASS COMPOSITION
# ============================================================================
print("\n4. Creating size class composition time series...")

# Create DataFrame
df_size = pd.DataFrame({
    name: ds_stats[var].values for name, var in SIZE_VARS.items()
}, index=pd.DatetimeIndex(ds_stats.time.values))

# Calculate percentage composition over time
df_size_pct = df_size.div(df_size.sum(axis=1), axis=0) * 100

# Plot
fig, ax = plt.subplots(figsize=(14, 8))

colors = ['#3498DB', '#E74C3C', '#2ECC71']
for idx, column in enumerate(df_size_pct.columns):
    ax.plot(df_size_pct.index, df_size_pct[column], linewidth=2, label=column, 
            color=colors[idx], marker='o', markersize=3)

ax.set_xlabel('Año', fontsize=12, fontweight='bold')
ax.set_ylabel('Composición Porcentual (%)', fontsize=12, fontweight='bold')
ax.set_title(
    'Evolución Temporal de la Composición por Clase de Tamaño\n(Promedio espacial, 2000-2024)',
    fontsize=14, fontweight='bold', pad=20
)
ax.legend(loc='best', fontsize=11, framealpha=0.95)
ax.grid(True, alpha=0.3)
ax.set_ylim(0, 100)

plt.tight_layout()
plt.savefig(output_dir / 'size_composition_timeseries.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: size_composition_timeseries.png")
plt.close()

# ============================================================================
# 5. STACKED AREA CHART - SPECIES
# ============================================================================
print("\n5. Creating species composition stacked area chart...")

fig, ax = plt.subplots(figsize=(14, 8))
ax.stackplot(
    df_species_pct.index,
    *[df_species_pct[col] for col in df_species_pct.columns],
    labels=df_species_pct.columns,
    colors=colors,
    alpha=0.8
)

ax.set_xlabel('Año', fontsize=12, fontweight='bold')
ax.set_ylabel('Composición Porcentual (%)', fontsize=12, fontweight='bold')
ax.set_title(
    'Composición de Especies - Gráfico de Área Acumulada\n(Promedio espacial, 2000-2024)',
    fontsize=14, fontweight='bold', pad=20
)
ax.legend(loc='upper left', fontsize=10, framealpha=0.95)
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / 'species_composition_stacked.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: species_composition_stacked.png")
plt.close()

# ============================================================================
# 6. STACKED AREA CHART - SIZE CLASSES
# ============================================================================
print("\n6. Creating size class composition stacked area chart...")

fig, ax = plt.subplots(figsize=(14, 8))
ax.stackplot(
    df_size_pct.index,
    *[df_size_pct[col] for col in df_size_pct.columns],
    labels=df_size_pct.columns,
    colors=colors_size,
    alpha=0.8
)

ax.set_xlabel('Año', fontsize=12, fontweight='bold')
ax.set_ylabel('Composición Porcentual (%)', fontsize=12, fontweight='bold')
ax.set_title(
    'Composición por Tamaño - Gráfico de Área Acumulada\n(Promedio espacial, 2000-2024)',
    fontsize=14, fontweight='bold', pad=20
)
ax.legend(loc='upper left', fontsize=11, framealpha=0.95)
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / 'size_composition_stacked.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: size_composition_stacked.png")
plt.close()

print("\n" + "=" * 70)
print("✓ All composition figures generated successfully!")
print(f"  Output directory: {output_dir}")
print("=" * 70)

ds_stats.close()
