#!/usr/bin/env python3
"""
Script to create interactive Plotly charts for PFT analysis.
Generates HTML-embedded interactive visualizations.
"""

import xarray as xr
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
import json

# Configuration
base_dir = Path(__file__).parent.parent
stats_file = base_dir / 'data' / 'pft_monthly_statistics.nc'
output_dir = base_dir / 'data' / 'plotly_charts'
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

COLORS_SPECIES = {
    'Diatomeas': '#FF6B6B',
    'Dinoflagelados': '#4ECDC4',
    'Algas Verdes': '#45B7D1',
    'Haptófitos': '#FFA07A',
    'Proclorococcus': '#98D8C8',
    'Procariontes': '#F7DC6F'
}

COLORS_SIZE = {
    'Microfitoplancton (>20 μm)': '#3498DB',
    'Nanofitoplancton (2-20 μm)': '#E74C3C',
    'Picofitoplancton (<2 μm)': '#2ECC71'
}

print("=" * 70)
print("GENERATING INTERACTIVE PLOTLY CHARTS")
print("=" * 70)

# Load preprocessed statistics
print("\nLoading monthly statistics...")
if not stats_file.exists():
    print(f"✗ Statistics file not found: {stats_file}")
    print("  Run preprocess_pft_data.py first")
    exit(1)

ds_stats = xr.open_dataset(stats_file)
print(f"✓ Statistics file loaded")

# ============================================================================
# 1. SPECIES COMPOSITION PIE CHART (INTERACTIVE)
# ============================================================================
print("\n1. Creating interactive species composition pie chart...")

species_values = {}
for name, var in SPECIES_VARS.items():
    if var in ds_stats:
        species_values[name] = float(ds_stats[var].mean().values)

fig = go.Figure(data=[go.Pie(
    labels=list(species_values.keys()),
    values=list(species_values.values()),
    marker=dict(colors=[COLORS_SPECIES[k] for k in species_values.keys()]),
    hovertemplate='<b>%{label}</b><br>Valor: %{value:.3f} mg/m³<br>Porcentaje: %{percent}<extra></extra>',
    textposition='inside',
    textinfo='label+percent'
)])

fig.update_layout(
    title='<b>Composición Porcentual de Especies de Fitoplancton</b><br><sub>Promedio 2000-2024</sub>',
    font=dict(size=12),
    height=600,
    hovermode='closest'
)

fig.write_html(output_dir / 'species_composition_pie.html')
print("   ✓ Saved: species_composition_pie.html")

# ============================================================================
# 2. SIZE CLASS COMPOSITION PIE CHART (INTERACTIVE)
# ============================================================================
print("\n2. Creating interactive size class composition pie chart...")

size_values = {}
for name, var in SIZE_VARS.items():
    if var in ds_stats:
        size_values[name] = float(ds_stats[var].mean().values)

fig = go.Figure(data=[go.Pie(
    labels=list(size_values.keys()),
    values=list(size_values.values()),
    marker=dict(colors=[COLORS_SIZE[k] for k in size_values.keys()]),
    hovertemplate='<b>%{label}</b><br>Valor: %{value:.3f} mg/m³<br>Porcentaje: %{percent}<extra></extra>',
    textposition='inside',
    textinfo='label+percent'
)])

fig.update_layout(
    title='<b>Composición Porcentual por Clase de Tamaño</b><br><sub>Promedio 2000-2024</sub>',
    font=dict(size=12),
    height=600,
    hovermode='closest'
)

fig.write_html(output_dir / 'size_composition_pie.html')
print("   ✓ Saved: size_composition_pie.html")

# ============================================================================
# 3. TIME SERIES OF SPECIES COMPOSITION (INTERACTIVE)
# ============================================================================
print("\n3. Creating interactive species composition time series...")

df_species = pd.DataFrame({
    name: ds_stats[var].values for name, var in SPECIES_VARS.items()
}, index=pd.DatetimeIndex(ds_stats.time.values))

df_species_pct = df_species.div(df_species.sum(axis=1), axis=0) * 100

fig = go.Figure()

for column in df_species_pct.columns:
    fig.add_trace(go.Scatter(
        x=df_species_pct.index,
        y=df_species_pct[column],
        mode='lines',
        name=column,
        line=dict(width=2, color=COLORS_SPECIES[column]),
        hovertemplate='<b>' + column + '</b><br>Fecha: %{x|%Y-%m}<br>Porcentaje: %{y:.1f}%<extra></extra>'
    ))

fig.update_layout(
    title='<b>Evolución Temporal de la Composición de Especies</b><br><sub>Promedio espacial, 2000-2024</sub>',
    xaxis_title='Año',
    yaxis_title='Composición Porcentual (%)',
    hovermode='x unified',
    height=600,
    template='plotly_white',
    yaxis=dict(range=[0, 100])
)

fig.write_html(output_dir / 'species_composition_timeseries.html')
print("   ✓ Saved: species_composition_timeseries.html")

# ============================================================================
# 4. TIME SERIES OF SIZE CLASS COMPOSITION (INTERACTIVE)
# ============================================================================
print("\n4. Creating interactive size class composition time series...")

df_size = pd.DataFrame({
    name: ds_stats[var].values for name, var in SIZE_VARS.items()
}, index=pd.DatetimeIndex(ds_stats.time.values))

df_size_pct = df_size.div(df_size.sum(axis=1), axis=0) * 100

fig = go.Figure()

for column in df_size_pct.columns:
    fig.add_trace(go.Scatter(
        x=df_size_pct.index,
        y=df_size_pct[column],
        mode='lines',
        name=column,
        line=dict(width=2, color=COLORS_SIZE[column]),
        hovertemplate='<b>' + column + '</b><br>Fecha: %{x|%Y-%m}<br>Porcentaje: %{y:.1f}%<extra></extra>'
    ))

fig.update_layout(
    title='<b>Evolución Temporal de la Composición por Clase de Tamaño</b><br><sub>Promedio espacial, 2000-2024</sub>',
    xaxis_title='Año',
    yaxis_title='Composición Porcentual (%)',
    hovermode='x unified',
    height=600,
    template='plotly_white',
    yaxis=dict(range=[0, 100])
)

fig.write_html(output_dir / 'size_composition_timeseries.html')
print("   ✓ Saved: size_composition_timeseries.html")

# ============================================================================
# 5. STACKED AREA CHART - SPECIES (INTERACTIVE)
# ============================================================================
print("\n5. Creating interactive species composition stacked area chart...")

fig = go.Figure()

for column in df_species_pct.columns:
    fig.add_trace(go.Scatter(
        x=df_species_pct.index,
        y=df_species_pct[column],
        mode='lines',
        name=column,
        line=dict(width=0.5, color=COLORS_SPECIES[column]),
        fillcolor=COLORS_SPECIES[column],
        stackgroup='one',
        hovertemplate='<b>' + column + '</b><br>Fecha: %{x|%Y-%m}<br>Porcentaje: %{y:.1f}%<extra></extra>'
    ))

fig.update_layout(
    title='<b>Composición de Especies - Área Acumulada</b><br><sub>Promedio espacial, 2000-2024</sub>',
    xaxis_title='Año',
    yaxis_title='Composición Porcentual (%)',
    hovermode='x unified',
    height=600,
    template='plotly_white',
    yaxis=dict(range=[0, 100])
)

fig.write_html(output_dir / 'species_composition_stacked.html')
print("   ✓ Saved: species_composition_stacked.html")

# ============================================================================
# 6. STACKED AREA CHART - SIZE CLASSES (INTERACTIVE)
# ============================================================================
print("\n6. Creating interactive size class composition stacked area chart...")

fig = go.Figure()

for column in df_size_pct.columns:
    fig.add_trace(go.Scatter(
        x=df_size_pct.index,
        y=df_size_pct[column],
        mode='lines',
        name=column,
        line=dict(width=0.5, color=COLORS_SIZE[column]),
        fillcolor=COLORS_SIZE[column],
        stackgroup='one',
        hovertemplate='<b>' + column + '</b><br>Fecha: %{x|%Y-%m}<br>Porcentaje: %{y:.1f}%<extra></extra>'
    ))

fig.update_layout(
    title='<b>Composición por Tamaño - Área Acumulada</b><br><sub>Promedio espacial, 2000-2024</sub>',
    xaxis_title='Año',
    yaxis_title='Composición Porcentual (%)',
    hovermode='x unified',
    height=600,
    template='plotly_white',
    yaxis=dict(range=[0, 100])
)

fig.write_html(output_dir / 'size_composition_stacked.html')
print("   ✓ Saved: size_composition_stacked.html")

print("\n" + "=" * 70)
print("✓ All interactive charts generated successfully!")
print(f"  Output directory: {output_dir}")
print("=" * 70)

ds_stats.close()
