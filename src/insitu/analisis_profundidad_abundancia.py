#!/usr/bin/env python3
"""
Análisis de Profundidad y Abundancia: PP In Situ (eDNA) vs Satelital
=====================================================================

Análisis profundo de la producción primaria in situ por capa de profundidad,
comparando la abundancia eDNA con las concentraciones satelitales.

Capas de muestreo:
  - Superficial: 1-26 m  (Shallow)
  - Intermedia:  35-140 m (Mid-water)
  - Profunda:    220-1000 m (Deep)

Gráficas generadas:
  1. Series de tiempo por profundidad vs satelital (por grupo)
  2. Perfil vertical de abundancia por grupo
  3. Comparación estacional por profundidad
  4. Abundancia acumulada por capa y grupo (barras)
  5. Correlación abundancia in situ vs concentración satelital
  6. Heatmaps de abundancia por profundidad × mes
  7. Panel resumen multi-grupo con índices climáticos
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import argparse
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
from datetime import datetime
from pathlib import Path
import warnings
import seaborn as sns

warnings.filterwarnings("ignore")

# =============================================================================
# ARGUMENTOS
# =============================================================================
parser = argparse.ArgumentParser(description='Análisis de profundidad y abundancia in situ vs satelital')
parser.add_argument('--taxonomy', choices=['v1', 'v2'], default='v2',
                    help='Versión del archivo de taxonomía: v1=taxonomy_corrected_edna.csv, v2=taxonomy_corrected_edna_2.csv')
args = parser.parse_args()

TAXONOMY_VERSION = args.taxonomy
TAXONOMY_FILENAME = 'taxonomy_corrected_edna.csv' if TAXONOMY_VERSION == 'v1' else 'taxonomy_corrected_edna_2.csv'

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'results' / 'insitu' / f'edna_{TAXONOMY_VERSION}' / 'profundidad'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SATELLITE_FILE = DATA_DIR / 'processed' / 'pft_monthly_statistics.nc'
TAXONOMY_FILE  = DATA_DIR / 'insitu' / TAXONOMY_FILENAME
NINO_FILE = DATA_DIR / 'raw' / 'nino34.long.anom.csv'
MEI_FILE  = DATA_DIR / 'raw' / 'mei.exttimeseries.csv'
PDO_FILE  = DATA_DIR / 'raw' / 'pdo.timeseries.sstens.csv'

print(f"[analisis_profundidad] Taxonomía: {TAXONOMY_FILENAME}")
print(f"[analisis_profundidad] Output:    {OUTPUT_DIR}")

START_DATE = '2000-01-01'
END_DATE = '2024-12-31'

# Colores para capas de profundidad
LAYER_COLORS = {
    'Superficial': '#3498DB',   # azul claro
    'Intermedia':  '#2ECC71',   # verde
    'Profunda':    '#E74C3C',   # rojo
}

LAYER_DEPTHS_LABEL = {
    'Superficial': '1-26 m',
    'Intermedia':  '35-140 m',
    'Profunda':    '220-1000 m',
}

# Mapeo grupo in situ → variable satelital
GROUP_SAT_MAP = {
    'Dinoflagelados':   {'sat': 'DINO_mean',   'sat_std': 'DINO_std',   'color': '#1F77B4'},
    'Diatomeas':        {'sat': 'DIATO_mean',  'sat_std': 'DIATO_std',  'color': '#FF7F0E'},
    'Clorofitas':       {'sat': 'GREEN_mean',  'sat_std': 'GREEN_std',  'color': '#2CA02C'},
    'Haptofitas':       {'sat': 'HAPTO_mean',  'sat_std': 'HAPTO_std',  'color': '#9467BD'},
    'Cianobacterias':   {'sat': 'PROKAR_mean', 'sat_std': 'PROKAR_std', 'color': '#D62728'},
    'Otros Eucariotas': {'sat': 'CHL_mean',    'sat_std': 'CHL_std',    'color': '#8C564B'},
    'Protozoa':         {'sat': 'CHL_mean',    'sat_std': 'CHL_std',    'color': '#E377C2'},
}

# Clasificación taxonómica
PRIMARY_PRODUCERS = {
    'Diatomeas': ['Bacillariophyta', 'Diatomophyceae', 'Fragilariophyceae', 'Bacillariophyceae'],
    'Dinoflagelados': ['Dinophyta', 'Dinophyceae', 'Myzozoa'],
    'Clorofitas': ['Chlorophyta', 'Chlorophyceae', 'Ulvophyceae'],
    'Cianobacterias': ['Cyanobacteria', 'Oxyphotobacteria'],
    'Haptofitas': ['Haptophyta', 'Prymnesiophyceae', 'Coccolithophyceae'],
    'Otros Eucariotas': ['Eukaryota'],
    'Protozoa': ['Protozoa', 'Discosea', 'Amoebozoa'],
}

MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
         'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

MONTHS_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

GROUP_NAMES_EN = {
    'Dinoflagelados':   'Dinoflagellates',
    'Diatomeas':        'Diatoms',
    'Clorofitas':       'Chlorophytes',
    'Haptofitas':       'Haptophytes',
    'Cianobacterias':   'Cyanobacteria',
    'Otros Eucariotas': 'Other Eukaryotes',
    'Protozoa':         'Protozoa',
}


# =============================================================================
# CARGA DE DATOS
# =============================================================================

def excel_date_to_datetime(excel_date):
    if pd.isna(excel_date) or excel_date == '':
        return pd.NaT
    try:
        if isinstance(excel_date, str):
            if '/' in excel_date:
                return pd.to_datetime(excel_date, format='%d/%m/%Y', errors='coerce')
            else:
                excel_date = float(excel_date)
        return datetime(1899, 12, 30) + pd.Timedelta(days=int(excel_date))
    except (ValueError, OverflowError):
        return pd.NaT


def classify_producer(row):
    ph = str(row.get('phylum', '')).strip() if pd.notna(row.get('phylum')) else ''
    cl = str(row.get('class', '')).strip() if pd.notna(row.get('class')) else ''
    kg = str(row.get('kingdom', '')).strip() if pd.notna(row.get('kingdom')) else ''
    for group, values in PRIMARY_PRODUCERS.items():
        if ph in values or cl in values or kg in values:
            return group
    if kg == 'Protozoa' or ph == 'Amoebozoa':
        return 'Protozoa'
    return 'Otros'


def depth_to_layer(depth_m):
    """Asigna capa de profundidad a partir de un valor numérico o rango (ej. '150-500') en metros."""
    if pd.isna(depth_m):
        return None
    s = str(depth_m).strip()
    try:
        if '-' in s and not s.startswith('-'):
            parts = s.split('-')
            d = (float(parts[0]) + float(parts[1])) / 2.0
        else:
            d = float(s)
    except (ValueError, TypeError):
        return None
    if 1 <= d <= 26:
        return 'Superficial'
    elif 35 <= d <= 140:
        return 'Intermedia'
    elif 220 <= d <= 1000:
        return 'Profunda'
    return None


def get_depth_layer(row):
    # v1: columnas separadas por capa
    if 'Shallow (m)' in row.index:
        if pd.notna(row['Shallow (m)']):
            return 'Superficial'
        elif pd.notna(row['Mid-water (m)']):
            return 'Intermedia'
        elif pd.notna(row['Deep (m)']):
            return 'Profunda'
        return None
    # v2: columna única Depth
    return depth_to_layer(row.get('Depth'))


def get_sample_depth(row):
    """Retorna la profundidad numérica de muestreo en metros."""
    if 'Shallow (m)' in row.index:
        if pd.notna(row['Shallow (m)']):
            return row['Shallow (m)']
        elif pd.notna(row['Mid-water (m)']):
            return row['Mid-water (m)']
        elif pd.notna(row['Deep (m)']):
            return row['Deep (m)']
        return np.nan
    # v2
    s = str(row.get('Depth', '')).strip()
    try:
        if '-' in s and not s.startswith('-'):
            parts = s.split('-')
            return (float(parts[0]) + float(parts[1])) / 2.0
        return float(s)
    except (ValueError, TypeError):
        return np.nan


def normalize_schema(df, version):
    """Normaliza columnas al esquema común independientemente de la versión del archivo."""
    if version == 'v1':
        df['date'] = df['Collected date year'].apply(excel_date_to_datetime)
        if 'Abundancia' in df.columns:
            df['Abundancia'] = pd.to_numeric(df['Abundancia'], errors='coerce').fillna(1)
        else:
            df['Abundancia'] = 1
    else:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        # v2 tiene columna Abundance → renombrar para compatibilidad
        if 'Abundance' in df.columns:
            df['Abundancia'] = pd.to_numeric(df['Abundance'], errors='coerce').fillna(1)
        else:
            df['Abundancia'] = 1
    return df


def load_insitu():
    print("  Cargando eDNA in situ...")
    df = pd.read_csv(TAXONOMY_FILE, low_memory=False)
    df = normalize_schema(df, TAXONOMY_VERSION)
    df = df.dropna(subset=['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df = df[(df['year'] >= 2000) & (df['year'] <= 2024)].copy()

    df['grupo'] = df.apply(classify_producer, axis=1)
    df['depth_layer'] = df.apply(get_depth_layer, axis=1)
    df['sample_depth'] = df.apply(get_sample_depth, axis=1)

    # Crear fecha mensual
    df['year_month'] = pd.to_datetime(
        df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2) + '-01'
    )

    df = df.dropna(subset=['depth_layer'])
    print(f"    → {len(df)} registros con capa de profundidad asignada")
    return df


def load_satellite():
    print("  Cargando datos satelitales...")
    ds = xr.open_dataset(SATELLITE_FILE)
    df_sat = pd.DataFrame(index=pd.to_datetime(ds.time.values))
    for var in ds.data_vars:
        df_sat[var] = ds[var].values
    ds.close()
    df_sat = df_sat[START_DATE:END_DATE]
    print(f"    → {len(df_sat)} meses")
    return df_sat


def load_nino34():
    try:
        df = pd.read_csv(NINO_FILE, skiprows=1, header=None, names=['Date', 'NINO34'])
        df['Date'] = pd.to_datetime(df['Date'].str.strip())
        df['NINO34'] = pd.to_numeric(df['NINO34'], errors='coerce')
        df = df[df['NINO34'] > -90].dropna()
        return df.set_index('Date')['NINO34'][START_DATE:END_DATE]
    except Exception:
        return None


def load_mei():
    try:
        chunks = []
        with open(MEI_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts or not parts[0].isdigit() or len(parts) < 13:
                    continue
                year = int(parts[0])
                for mi, val in enumerate(parts[1:13]):
                    try:
                        vf = float(val)
                        if vf > -90:
                            chunks.append({'Date': pd.Timestamp(year, mi + 1, 1), 'MEI': vf})
                    except ValueError:
                        pass
        return pd.DataFrame(chunks).set_index('Date')['MEI'][START_DATE:END_DATE]
    except Exception:
        return None


def load_pdo():
    try:
        df = pd.read_csv(PDO_FILE, skiprows=1, header=None, usecols=[0, 1], names=['Date', 'PDO'])
        df['Date'] = pd.to_datetime(df['Date'])
        df['PDO'] = pd.to_numeric(df['PDO'], errors='coerce')
        df = df.dropna()
        return df.set_index('Date')['PDO'][START_DATE:END_DATE]
    except Exception:
        return None


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def monthly_abundance_by_layer(df_insitu, grupo, layer):
    """Serie temporal mensual de abundancia total para un grupo y capa."""
    mask = (df_insitu['grupo'] == grupo) & (df_insitu['depth_layer'] == layer)
    sub = df_insitu[mask]
    if len(sub) == 0:
        return pd.Series(dtype=float)
    return sub.groupby('year_month')['Abundancia'].sum().sort_index()


def monthly_frequency_by_layer(df_insitu, grupo, layer):
    """Serie temporal mensual de frecuencia (conteo) para un grupo y capa."""
    mask = (df_insitu['grupo'] == grupo) & (df_insitu['depth_layer'] == layer)
    sub = df_insitu[mask]
    if len(sub) == 0:
        return pd.Series(dtype=float)
    return sub.groupby('year_month').size().sort_index()


# =============================================================================
# GRÁFICAS
# =============================================================================

def plot_01_timeseries_by_depth(df_insitu, df_sat, grupo, sat_info):
    """
    Para cada grupo: serie de tiempo satelital + abundancia in situ por capa.
    3 paneles: uno por capa, cada uno con satelital (izq) + abundancia (der).
    """
    sat_var = sat_info['sat']
    if sat_var not in df_sat.columns:
        return

    sat_series = df_sat[sat_var].dropna()
    sat_rolling = sat_series.rolling(12, center=True).mean()

    layers = ['Superficial', 'Intermedia', 'Profunda']

    fig, axes = plt.subplots(3, 1, figsize=(18, 14), sharex=True)

    for i, layer in enumerate(layers):
        ax = axes[i]
        abund_series = monthly_abundance_by_layer(df_insitu, grupo, layer)
        freq_series = monthly_frequency_by_layer(df_insitu, grupo, layer)

        # Satelital
        ax.plot(sat_series.index, sat_series.values,
                linewidth=0.8, color=sat_info['color'], alpha=0.3)
        ax.plot(sat_rolling.index, sat_rolling.values,
                linewidth=2.5, color=sat_info['color'], alpha=0.9,
                label=f'Satelital ({sat_var.replace("_mean","")})')
        ax.set_ylabel('Concentración\n(mg m⁻³)', fontsize=10,
                      color=sat_info['color'], fontweight='bold')
        ax.tick_params(axis='y', labelcolor=sat_info['color'])

        # Abundancia in situ
        if len(abund_series) > 0:
            ax_twin = ax.twinx()
            ax_twin.bar(abund_series.index, abund_series.values,
                        width=20, alpha=0.5, color=LAYER_COLORS[layer],
                        edgecolor=LAYER_COLORS[layer], linewidth=0.5)

            # Mostrar también frecuencia como línea
            if len(freq_series) > 0:
                ax_twin.plot(freq_series.index, freq_series.values,
                             marker='s', markersize=3, linewidth=1,
                             color='black', alpha=0.5, linestyle='--',
                             label='Frecuencia (n registros)')

            ax_twin.set_ylabel(f'Abundancia eDNA\n({LAYER_DEPTHS_LABEL[layer]})',
                              fontsize=10, color=LAYER_COLORS[layer], fontweight='bold')
            ax_twin.tick_params(axis='y', labelcolor=LAYER_COLORS[layer])

            n_records = len(df_insitu[(df_insitu['grupo'] == grupo) &
                                      (df_insitu['depth_layer'] == layer)])
            n_pos = len(df_insitu[(df_insitu['grupo'] == grupo) &
                                   (df_insitu['depth_layer'] == layer) &
                                   (df_insitu['Abundancia'] > 0)])
            stats = f'n={n_records} | con abundancia>0: {n_pos} | Σ abund={int(abund_series.sum())}'
            ax.text(0.02, 0.95, stats, transform=ax.transAxes, fontsize=8.5,
                    va='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                    family='monospace')

            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax_twin.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2,
                      loc='upper right', fontsize=8, framealpha=0.9)
        else:
            ax.legend(loc='upper right', fontsize=9)
            ax.text(0.5, 0.5, 'Sin datos in situ en esta capa',
                    transform=ax.transAxes, ha='center', fontsize=12,
                    color='gray', alpha=0.5)

        ax.set_title(f'Capa {layer} ({LAYER_DEPTHS_LABEL[layer]})',
                      fontsize=12, fontweight='bold', loc='left',
                      color=LAYER_COLORS[layer])
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.set_axisbelow(True)

    axes[-1].set_xlabel('Año', fontsize=12, fontweight='bold')
    axes[-1].xaxis.set_major_locator(mdates.YearLocator(2))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45, ha='right')

    fig.suptitle(f'{grupo}\nAbundancia In Situ por Capa de Profundidad vs Concentración Satelital (2000-2024)',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    safe = grupo.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e')
    safe = safe.replace('í', 'i').replace('ó', 'o')
    filepath = OUTPUT_DIR / f'01_timeseries_depth_{safe}.png'
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"    ✓ {filepath.name}")
    plt.close()


def plot_02_vertical_profile(df_insitu):
    """
    Perfil vertical de abundancia media por grupo.
    Muestra la distribución vertical de la abundancia para cada grupo funcional.
    """
    grupos = [g for g in GROUP_SAT_MAP.keys()
              if len(df_insitu[df_insitu['grupo'] == g]) > 0]

    fig, axes = plt.subplots(1, len(grupos), figsize=(4 * len(grupos), 8),
                              sharey=True)
    if len(grupos) == 1:
        axes = [axes]

    for idx, grupo in enumerate(grupos):
        ax = axes[idx]
        sub = df_insitu[(df_insitu['grupo'] == grupo) & (df_insitu['Abundancia'] > 0)]

        if len(sub) == 0:
            ax.text(0.5, 0.5, 'Sin abundancia>0', transform=ax.transAxes,
                    ha='center', fontsize=10)
            ax.set_title(grupo, fontsize=11, fontweight='bold')
            continue

        for layer in ['Superficial', 'Intermedia', 'Profunda']:
            layer_data = sub[sub['depth_layer'] == layer]
            if len(layer_data) == 0:
                continue

            depths = layer_data['sample_depth'].values
            abunds = layer_data['Abundancia'].values

            ax.scatter(abunds, -depths, alpha=0.4, s=20,
                       color=LAYER_COLORS[layer], label=f'{layer} (n={len(layer_data)})')

            # Media por capa
            mean_depth = -np.mean(depths)
            mean_abund = np.mean(abunds)
            ax.plot(mean_abund, mean_depth, 'D', markersize=10,
                    color=LAYER_COLORS[layer], markeredgecolor='black',
                    markeredgewidth=1.5, zorder=5)

        ax.set_xlabel('Abundancia eDNA', fontsize=10)
        if idx == 0:
            ax.set_ylabel('Profundidad (m)', fontsize=11, fontweight='bold')
        ax.set_title(grupo, fontsize=11, fontweight='bold',
                      color=GROUP_SAT_MAP[grupo]['color'])
        ax.legend(fontsize=7, loc='lower right')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

    fig.suptitle('Perfil Vertical de Abundancia eDNA por Grupo Funcional\n'
                 '(◆ = media por capa)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    filepath = OUTPUT_DIR / '02_perfil_vertical_abundancia.png'
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"    ✓ {filepath.name}")
    plt.close()


def plot_03_seasonal_by_depth(df_insitu, df_sat):
    """
    Climatología estacional por capa de profundidad vs satelital.
    """
    grupos_con_datos = [g for g in GROUP_SAT_MAP.keys()
                        if len(df_insitu[(df_insitu['grupo'] == g) & (df_insitu['Abundancia'] > 0)]) > 5]

    if not grupos_con_datos:
        print("    ⚠ Insuficientes datos para climatología estacional")
        return

    ncols = 3
    nrows = int(np.ceil(len(grupos_con_datos) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 5 * nrows))
    axes_flat = axes.flatten() if nrows > 1 else (axes if isinstance(axes, np.ndarray) else [axes])

    x = np.arange(1, 13)
    width = 0.22

    for idx, grupo in enumerate(grupos_con_datos):
        ax = axes_flat[idx]
        sat_var = GROUP_SAT_MAP[grupo]['sat']

        # Climatología satelital
        if sat_var in df_sat.columns:
            sat_series = df_sat[sat_var].dropna()
            sat_clim = sat_series.groupby(sat_series.index.month).mean()
            ax.plot(x, sat_clim.values, 'o-', linewidth=2.5,
                    color=GROUP_SAT_MAP[grupo]['color'], markersize=6, zorder=5,
                    label=f'Satelital ({sat_var.replace("_mean","")})')
            ax.set_ylabel('mg m⁻³', fontsize=9, color=GROUP_SAT_MAP[grupo]['color'])
            ax.tick_params(axis='y', labelcolor=GROUP_SAT_MAP[grupo]['color'])

        # Abundancia in situ por capa
        ax_twin = ax.twinx()
        offsets = {'Superficial': -width, 'Intermedia': 0, 'Profunda': width}

        for layer in ['Superficial', 'Intermedia', 'Profunda']:
            sub = df_insitu[(df_insitu['grupo'] == grupo) &
                            (df_insitu['depth_layer'] == layer) &
                            (df_insitu['Abundancia'] > 0)]
            if len(sub) == 0:
                continue

            clim = sub.groupby('month')['Abundancia'].mean()
            vals = [clim.get(m, 0) for m in range(1, 13)]

            ax_twin.bar(x + offsets[layer], vals, width,
                        color=LAYER_COLORS[layer], alpha=0.6,
                        label=f'{layer} ({LAYER_DEPTHS_LABEL[layer]})',
                        edgecolor=LAYER_COLORS[layer])

        ax_twin.set_ylabel('Abundancia\nmedia eDNA', fontsize=9)

        ax.set_xticks(x)
        ax.set_xticklabels(MESES, fontsize=8, rotation=45)
        ax.set_title(grupo, fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.2, axis='y')

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax_twin.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2,
                  loc='upper right', fontsize=7, framealpha=0.9)

    for idx in range(len(grupos_con_datos), len(axes_flat)):
        axes_flat[idx].set_visible(False)

    fig.suptitle('Climatología Mensual: Abundancia In Situ por Capa vs Satelital\n'
                 'Golfo de California (2000-2024)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    filepath = OUTPUT_DIR / '03_estacionalidad_por_profundidad.png'
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"    ✓ {filepath.name}")
    plt.close()


def plot_04_stacked_abundance(df_insitu):
    """
    Barras: abundancia acumulada por capa y grupo.
    """
    grupos = [g for g in GROUP_SAT_MAP.keys()
              if len(df_insitu[(df_insitu['grupo'] == g) & (df_insitu['Abundancia'] > 0)]) > 0]

    data = {}
    for grupo in grupos:
        data[grupo] = {}
        for layer in ['Superficial', 'Intermedia', 'Profunda']:
            sub = df_insitu[(df_insitu['grupo'] == grupo) & (df_insitu['depth_layer'] == layer)]
            data[grupo][layer] = sub['Abundancia'].sum()

    df_bars = pd.DataFrame(data).T

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

    # Panel izquierdo: valores absolutos
    df_bars.plot(kind='barh', stacked=True, ax=ax1,
                 color=[LAYER_COLORS[l] for l in df_bars.columns])
    ax1.set_xlabel('Abundancia Total eDNA', fontsize=12, fontweight='bold')
    ax1.set_title('Abundancia Total por Capa', fontsize=13, fontweight='bold')
    ax1.legend(title='Capa de Profundidad', fontsize=10)
    ax1.grid(True, alpha=0.3, axis='x')

    # Panel derecho: porcentaje
    df_pct = df_bars.div(df_bars.sum(axis=1), axis=0) * 100
    df_pct.plot(kind='barh', stacked=True, ax=ax2,
                color=[LAYER_COLORS[l] for l in df_pct.columns])
    ax2.set_xlabel('Porcentaje (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Distribución Porcentual por Capa', fontsize=13, fontweight='bold')
    ax2.legend(title='Capa de Profundidad', fontsize=10)
    ax2.set_xlim(0, 100)
    ax2.grid(True, alpha=0.3, axis='x')

    # Anotar valores en barras de porcentaje
    for i, grupo in enumerate(df_pct.index):
        cumsum = 0
        for layer in df_pct.columns:
            val = df_pct.loc[grupo, layer]
            if val > 5:
                ax2.text(cumsum + val / 2, i, f'{val:.0f}%',
                         ha='center', va='center', fontsize=9, fontweight='bold')
            cumsum += val

    fig.suptitle('Distribución Vertical de Abundancia eDNA por Grupo Funcional',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    filepath = OUTPUT_DIR / '04_abundancia_por_capa_grupo.png'
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"    ✓ {filepath.name}")
    plt.close()


def plot_05_correlation_sat_insitu(df_insitu, df_sat):
    """
    Scatter plots: abundancia mensual in situ (por capa) vs concentración satelital.
    """
    grupos_con_datos = [g for g in GROUP_SAT_MAP.keys()
                        if (len(df_insitu[(df_insitu['grupo'] == g) & (df_insitu['Abundancia'] > 0)]) > 5
                            and GROUP_SAT_MAP[g]['sat'] in df_sat.columns)]

    if not grupos_con_datos:
        return

    ncols = 3
    nrows = int(np.ceil(len(grupos_con_datos) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows))
    axes_flat = axes.flatten() if nrows > 1 else (axes if isinstance(axes, np.ndarray) else [axes])

    for idx, grupo in enumerate(grupos_con_datos):
        ax = axes_flat[idx]
        sat_var = GROUP_SAT_MAP[grupo]['sat']
        sat_series = df_sat[sat_var].dropna()

        for layer in ['Superficial', 'Intermedia', 'Profunda']:
            abund = monthly_abundance_by_layer(df_insitu, grupo, layer)
            if len(abund) == 0:
                continue

            # Alinear con satelital
            common_idx = sat_series.index.intersection(abund.index)
            if len(common_idx) < 3:
                continue

            sat_vals = sat_series.reindex(common_idx).values
            insitu_vals = abund.reindex(common_idx).values

            ax.scatter(sat_vals, insitu_vals, alpha=0.6, s=40,
                       color=LAYER_COLORS[layer],
                       label=f'{layer} (n={len(common_idx)})', edgecolors='gray',
                       linewidth=0.5)

            # Línea de tendencia
            if len(common_idx) >= 5:
                z = np.polyfit(sat_vals, insitu_vals, 1)
                p = np.poly1d(z)
                x_line = np.linspace(sat_vals.min(), sat_vals.max(), 50)
                ax.plot(x_line, p(x_line), '--', color=LAYER_COLORS[layer],
                        linewidth=1.5, alpha=0.7)

                r = np.corrcoef(sat_vals, insitu_vals)[0, 1]
                ax.text(0.02, 0.98 - 0.12 * list(LAYER_COLORS.keys()).index(layer),
                        f'{layer}: r={r:.2f}', transform=ax.transAxes,
                        fontsize=8, va='top', color=LAYER_COLORS[layer],
                        fontweight='bold')

        ax.set_xlabel(f'Satelital ({sat_var.replace("_mean","")}, mg m⁻³)', fontsize=10)
        ax.set_ylabel('Abundancia eDNA', fontsize=10)
        ax.set_title(grupo, fontsize=11, fontweight='bold',
                      color=GROUP_SAT_MAP[grupo]['color'])
        ax.legend(fontsize=8, loc='lower right')
        ax.grid(True, alpha=0.3)

    for idx in range(len(grupos_con_datos), len(axes_flat)):
        axes_flat[idx].set_visible(False)

    fig.suptitle('Correlación: Concentración Satelital vs Abundancia In Situ por Capa\n'
                 '(datos mensuales agregados, 2000-2024)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    filepath = OUTPUT_DIR / '05_correlacion_sat_vs_insitu_por_capa.png'
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"    ✓ {filepath.name}")
    plt.close()


def plot_06_heatmap_depth(df_insitu):
    """
    Heatmaps de abundancia: mes × año, uno por capa, para los grupos principales.
    """
    grupos_principales = ['Dinoflagelados', 'Otros Eucariotas', 'Protozoa']
    grupos_con_datos = [g for g in grupos_principales
                        if len(df_insitu[(df_insitu['grupo'] == g) & (df_insitu['Abundancia'] > 0)]) > 5]

    if not grupos_con_datos:
        return

    for grupo in grupos_con_datos:
        fig, axes = plt.subplots(1, 3, figsize=(22, 7))

        for i, layer in enumerate(['Superficial', 'Intermedia', 'Profunda']):
            ax = axes[i]
            sub = df_insitu[(df_insitu['grupo'] == grupo) &
                            (df_insitu['depth_layer'] == layer)]

            # Crear matriz mes × año de abundancia sumada
            years = list(range(2000, 2025))
            matriz = pd.DataFrame(np.nan, index=MESES, columns=years)

            for year in years:
                for month in range(1, 13):
                    vals = sub[(sub['year'] == year) & (sub['month'] == month)]['Abundancia']
                    if len(vals) > 0:
                        total = vals.sum()
                        if total > 0:
                            matriz.loc[MESES[month - 1], year] = total

            sns.heatmap(matriz, annot=True, fmt='.0f', cmap='YlOrRd',
                        ax=ax, linewidths=0.5, linecolor='gray',
                        cbar_kws={'label': 'Abundancia', 'shrink': 0.8})
            ax.set_title(f'{layer}\n({LAYER_DEPTHS_LABEL[layer]})',
                          fontsize=12, fontweight='bold', color=LAYER_COLORS[layer])
            ax.set_xlabel('Año', fontsize=10)
            if i == 0:
                ax.set_ylabel('Mes', fontsize=10)

        fig.suptitle(f'{grupo}: Abundancia eDNA por Mes y Año según Capa de Profundidad',
                     fontsize=14, fontweight='bold')
        plt.tight_layout()

        safe = grupo.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e')
        filepath = OUTPUT_DIR / f'06_heatmap_profundidad_{safe}.png'
        plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
        print(f"    ✓ {filepath.name}")
        plt.close()


def plot_07_resumen_multipanel(df_insitu, df_sat, nino, mei, pdo):
    """
    Panel resumen: todos los grupos, 3 capas, + índices climáticos.
    Cada grupo en un panel con barras apiladas por capa + satelital superpuesto.
    """
    grupos_con_datos = [g for g in GROUP_SAT_MAP.keys()
                        if len(df_insitu[(df_insitu['grupo'] == g) & (df_insitu['Abundancia'] > 0)]) > 0]

    n_panels = len(grupos_con_datos) + 1  # +1 para clima
    fig, axes = plt.subplots(n_panels, 1, figsize=(20, 3.5 * n_panels), sharex=True)

    for idx, grupo in enumerate(grupos_con_datos):
        ax = axes[idx]
        sat_var = GROUP_SAT_MAP[grupo]['sat']

        # Satelital
        if sat_var in df_sat.columns:
            sat_series = df_sat[sat_var].dropna()
            sat_rolling = sat_series.rolling(12, center=True).mean()
            ax.plot(sat_rolling.index, sat_rolling.values,
                    linewidth=2.5, color=GROUP_SAT_MAP[grupo]['color'],
                    alpha=0.9, label=f'Satelital (media móvil)')
            ax.fill_between(sat_series.index, sat_series.values,
                            alpha=0.08, color=GROUP_SAT_MAP[grupo]['color'])
            ax.set_ylabel('mg m⁻³', fontsize=9, color=GROUP_SAT_MAP[grupo]['color'])
            ax.tick_params(axis='y', labelcolor=GROUP_SAT_MAP[grupo]['color'])

        # Abundancia por capa en eje secundario
        ax_twin = ax.twinx()
        bottom = None

        for layer in ['Superficial', 'Intermedia', 'Profunda']:
            abund = monthly_abundance_by_layer(df_insitu, grupo, layer)
            if len(abund) == 0:
                continue

            if bottom is None:
                ax_twin.bar(abund.index, abund.values, width=20,
                            alpha=0.5, color=LAYER_COLORS[layer],
                            label=f'{layer}')
                # Guardar para acumular
                all_idx = abund.index
                bottom_vals = abund
            else:
                # Alinear con bottom
                combined_idx = bottom_vals.index.union(abund.index)
                bv = bottom_vals.reindex(combined_idx, fill_value=0)
                av = abund.reindex(combined_idx, fill_value=0)
                ax_twin.bar(combined_idx, av.values, width=20,
                            bottom=bv.values, alpha=0.5,
                            color=LAYER_COLORS[layer], label=f'{layer}')
                bottom_vals = bv + av

        ax_twin.set_ylabel('Abundancia\neDNA', fontsize=9)

        ax.set_title(f'{grupo}', fontsize=11, fontweight='bold', loc='left',
                      color=GROUP_SAT_MAP[grupo]['color'])
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.set_axisbelow(True)

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax_twin.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2,
                  loc='upper right', fontsize=7, framealpha=0.9, ncol=4)

    # Panel climático
    ax_clim = axes[-1]
    if nino is not None:
        ax_clim.fill_between(nino.index, 0, nino.values,
                             where=nino.values > 0, alpha=0.3, color='red', label='El Niño')
        ax_clim.fill_between(nino.index, 0, nino.values,
                             where=nino.values < 0, alpha=0.3, color='blue', label='La Niña')
        ax_clim.plot(nino.index, nino.values, color='#FF9500', linewidth=1.5, label='NIÑO 3.4')
    if mei is not None:
        ax_clim.plot(mei.index, mei.values, color='#9B59B6', linewidth=1.2,
                     linestyle='--', label='MEI')
    if pdo is not None:
        ax_clim.plot(pdo.index, pdo.values, color='#34495E', linewidth=1.2,
                     linestyle=':', label='PDO')
    ax_clim.axhline(0, color='black', linewidth=0.8)
    ax_clim.set_ylabel('Índice', fontsize=10, fontweight='bold')
    ax_clim.set_title('Índices Climáticos', fontsize=11, fontweight='bold', loc='left')
    ax_clim.legend(loc='upper right', fontsize=8, ncol=5, framealpha=0.9)
    ax_clim.grid(True, alpha=0.3, linestyle='--')

    ax_clim.set_xlabel('Año', fontsize=12, fontweight='bold')
    ax_clim.xaxis.set_major_locator(mdates.YearLocator(2))
    ax_clim.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax_clim.xaxis.get_majorticklabels(), rotation=45, ha='right')

    fig.suptitle('Resumen: Abundancia eDNA por Profundidad vs PP Satelital + Índices Climáticos\n'
                 'Golfo de California (2000-2024)', fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    filepath = OUTPUT_DIR / '07_resumen_multipanel_profundidad.png'
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"    ✓ {filepath.name}")
    plt.close()


def plot_08_boxplot_depth_abundance(df_insitu):
    """
    Boxplots de abundancia por capa de profundidad para cada grupo.
    """
    grupos_con_datos = [g for g in GROUP_SAT_MAP.keys()
                        if len(df_insitu[(df_insitu['grupo'] == g) & (df_insitu['Abundancia'] > 0)]) > 5]

    if not grupos_con_datos:
        return

    ncols = 3
    nrows = int(np.ceil(len(grupos_con_datos) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows))
    axes_flat = axes.flatten() if nrows > 1 else (axes if isinstance(axes, np.ndarray) else [axes])

    for idx, grupo in enumerate(grupos_con_datos):
        ax = axes_flat[idx]
        sub = df_insitu[(df_insitu['grupo'] == grupo) & (df_insitu['Abundancia'] > 0)]

        plot_data = []
        layer_labels = []
        colors = []

        for layer in ['Superficial', 'Intermedia', 'Profunda']:
            layer_data = sub[sub['depth_layer'] == layer]['Abundancia']
            if len(layer_data) > 0:
                plot_data.append(layer_data.values)
                layer_labels.append(f'{layer}\n({LAYER_DEPTHS_LABEL[layer]})\nn={len(layer_data)}')
                colors.append(LAYER_COLORS[layer])

        if plot_data:
            bp = ax.boxplot(plot_data, labels=layer_labels, patch_artist=True,
                            showfliers=True, flierprops=dict(marker='.', markersize=3, alpha=0.3))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.5)

        ax.set_ylabel('Abundancia eDNA', fontsize=10)
        ax.set_title(grupo, fontsize=11, fontweight='bold',
                      color=GROUP_SAT_MAP[grupo]['color'])
        ax.grid(True, alpha=0.3, axis='y')

    for idx in range(len(grupos_con_datos), len(axes_flat)):
        axes_flat[idx].set_visible(False)

    fig.suptitle('Distribución de Abundancia eDNA por Capa de Profundidad',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    filepath = OUTPUT_DIR / '08_boxplot_abundancia_por_capa.png'
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"    ✓ {filepath.name}")
    plt.close()


def generate_summary_csv(df_insitu, df_sat):
    """Genera CSV con resumen estadístico por grupo y capa."""
    rows = []
    for grupo in GROUP_SAT_MAP.keys():
        sat_var = GROUP_SAT_MAP[grupo]['sat']
        sat_mean = df_sat[sat_var].mean() if sat_var in df_sat.columns else np.nan

        for layer in ['Superficial', 'Intermedia', 'Profunda']:
            sub = df_insitu[(df_insitu['grupo'] == grupo) & (df_insitu['depth_layer'] == layer)]
            sub_pos = sub[sub['Abundancia'] > 0]
            rows.append({
                'Grupo': grupo,
                'Capa': layer,
                'Profundidad': LAYER_DEPTHS_LABEL[layer],
                'N_registros': len(sub),
                'N_con_abundancia': len(sub_pos),
                'Abundancia_total': sub['Abundancia'].sum(),
                'Abundancia_media': sub_pos['Abundancia'].mean() if len(sub_pos) > 0 else 0,
                'Abundancia_max': sub_pos['Abundancia'].max() if len(sub_pos) > 0 else 0,
                'Abundancia_mediana': sub_pos['Abundancia'].median() if len(sub_pos) > 0 else 0,
                'Satelital_media_mgm3': sat_mean,
                'Variable_satelital': sat_var,
            })

    df_out = pd.DataFrame(rows)
    filepath = OUTPUT_DIR / 'resumen_estadistico_profundidad.csv'
    df_out.to_csv(filepath, index=False)
    print(f"    ✓ {filepath.name}")


def plot_09_panel_groups_comparison(df_insitu, df_sat):
    """
    Publication-quality multi-panel figure comparing all plankton groups.
    Each panel: satellite proxy (line, left axis) + eDNA abundance (bars, right axis).
    Focuses on the Superficial layer (1–26 m), which contains the bulk of in situ records.
    """
    layer = 'Superficial'
    grupos_con_datos = [
        g for g in GROUP_SAT_MAP.keys()
        if len(df_insitu[(df_insitu['grupo'] == g) &
                         (df_insitu['depth_layer'] == layer) &
                         (df_insitu['Abundancia'] > 0)]) > 0
    ]

    if not grupos_con_datos:
        print("    ⚠ No data available for panel comparison")
        return

    n = len(grupos_con_datos)
    ncols = 2
    nrows = int(np.ceil(n / ncols))

    plt.rcParams.update({
        'font.size': 10,
        'axes.titlesize': 11,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 8,
        'font.family': 'sans-serif',
    })

    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(14, 3.8 * nrows),
        sharex=True,
        constrained_layout=False,
    )
    axes_flat = axes.flatten() if nrows > 1 else np.array(axes).flatten()

    panel_labels = list('abcdefghij')
    bar_color    = '#5DADE2'   # consistent blue for eDNA bars
    mean_color   = '#1A5276'   # darker blue for rolling mean line

    for idx, grupo in enumerate(grupos_con_datos):
        ax_sat = axes_flat[idx]
        sat_info   = GROUP_SAT_MAP[grupo]
        sat_var    = sat_info['sat']
        grp_color  = sat_info['color']
        grp_name   = GROUP_NAMES_EN.get(grupo, grupo)

        # --- Satellite (left axis) ---
        if sat_var in df_sat.columns:
            sat_series  = df_sat[sat_var].dropna()
            sat_rolling = sat_series.rolling(12, center=True, min_periods=6).mean()

            ax_sat.fill_between(sat_series.index, sat_series.values,
                                alpha=0.10, color=grp_color)
            ax_sat.plot(sat_rolling.index, sat_rolling.values,
                        linewidth=2.0, color=grp_color, alpha=0.92,
                        label=f'Satellite {sat_var.replace("_mean", "")} (12-mo mean)')
            ax_sat.set_ylabel('Concentration\n(mg m⁻³)', fontsize=9,
                              color=grp_color, fontweight='bold')
            ax_sat.tick_params(axis='y', labelcolor=grp_color, labelsize=8,
                               length=3, width=0.8)
            ax_sat.spines['left'].set_color(grp_color)

        # --- eDNA Abundance (right axis) ---
        abund = monthly_abundance_by_layer(df_insitu, grupo, layer)

        if len(abund) > 0:
            ax_edna = ax_sat.twinx()
            ax_edna.bar(abund.index, abund.values, width=25,
                        alpha=0.40, color=bar_color, edgecolor='none',
                        label='eDNA abundance (monthly sum)')

            if len(abund) >= 3:
                abund_roll = abund.rolling(6, center=True, min_periods=2).mean()
                ax_edna.plot(abund_roll.index, abund_roll.values,
                             linewidth=1.8, color=mean_color, alpha=0.88,
                             linestyle='-', label='eDNA (6-mo mean)')

            ax_edna.set_ylabel('eDNA Abundance\n(reads per month)', fontsize=9,
                               color=mean_color, fontweight='bold')
            ax_edna.tick_params(axis='y', labelcolor=mean_color, labelsize=8,
                                length=3, width=0.8)
            ax_edna.spines['right'].set_color(mean_color)
            ax_edna.set_ylim(bottom=0)

            n_recs = len(df_insitu[(df_insitu['grupo'] == grupo) &
                                   (df_insitu['depth_layer'] == layer)])
            n_months = len(abund)
            stats_txt = f'n = {n_recs:,} records  |  {n_months} sampling months'
            ax_sat.text(0.98, 0.97, stats_txt, transform=ax_sat.transAxes,
                        fontsize=7.5, va='top', ha='right',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                  edgecolor='#CCCCCC', alpha=0.85))

            lines1, labels1 = ax_sat.get_legend_handles_labels()
            lines2, labels2 = ax_edna.get_legend_handles_labels()
            ax_sat.legend(lines1 + lines2, labels1 + labels2,
                          loc='upper left', fontsize=7.5, framealpha=0.88,
                          handlelength=1.5, handletextpad=0.5,
                          borderpad=0.4, labelspacing=0.3)

        # Panel label + group name
        ax_sat.text(0.012, 0.97, f'({panel_labels[idx]})',
                    transform=ax_sat.transAxes,
                    fontsize=11, fontweight='bold', va='top')
        ax_sat.set_title(grp_name, fontsize=11, fontweight='bold',
                         color=grp_color, loc='left', pad=4)

        ax_sat.grid(True, alpha=0.18, linestyle='--', linewidth=0.7)
        ax_sat.set_axisbelow(True)
        for spine in ['top']:
            ax_sat.spines[spine].set_visible(False)

    # X-axis formatting for bottom row panels
    for col in range(ncols):
        bottom_idx = (nrows - 1) * ncols + col
        if bottom_idx < n:
            ax = axes_flat[bottom_idx]
            ax.xaxis.set_major_locator(mdates.YearLocator(2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
            ax.set_xlabel('Year', fontsize=10, fontweight='bold')
        elif bottom_idx == n and n % ncols != 0:
            # Last row has only one panel — format both bottom axes
            axes_flat[bottom_idx - 1].xaxis.set_major_locator(mdates.YearLocator(2))
            axes_flat[bottom_idx - 1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            plt.setp(axes_flat[bottom_idx - 1].xaxis.get_majorticklabels(),
                     rotation=45, ha='right', fontsize=9)
            axes_flat[bottom_idx - 1].set_xlabel('Year', fontsize=10, fontweight='bold')

    # Hide unused panels
    for idx in range(n, len(axes_flat)):
        axes_flat[idx].set_visible(False)

    fig.suptitle(
        'In Situ eDNA Abundance vs. Satellite-Derived Proxy by Plankton Functional Group\n'
        'Gulf of California — Shallow Layer (1–26 m), 2000–2024',
        fontsize=13, fontweight='bold', y=1.02,
    )

    plt.tight_layout(h_pad=0.6, w_pad=1.2)
    filepath = OUTPUT_DIR / '09_panel_grupos_comparativa.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"    ✓ {filepath.name}")
    plt.close()

    plt.rcParams.update(plt.rcParamsDefault)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print(" ANÁLISIS DE PROFUNDIDAD Y ABUNDANCIA")
    print(" PP In Situ (eDNA) vs Satelital — Golfo de California")
    print("=" * 70)

    print("\n[1/10] Cargando datos...")
    df_insitu = load_insitu()
    df_sat = load_satellite()

    print("\n  Cargando índices climáticos...")
    nino = load_nino34()
    mei = load_mei()
    pdo = load_pdo()

    print(f"\n[2/10] Series de tiempo por profundidad (por grupo)...")
    for grupo, sat_info in GROUP_SAT_MAP.items():
        if len(df_insitu[df_insitu['grupo'] == grupo]) > 0:
            plot_01_timeseries_by_depth(df_insitu, df_sat, grupo, sat_info)

    print(f"\n[3/10] Perfil vertical de abundancia...")
    plot_02_vertical_profile(df_insitu)

    print(f"\n[4/10] Climatología estacional por profundidad...")
    plot_03_seasonal_by_depth(df_insitu, df_sat)

    print(f"\n[5/10] Abundancia acumulada por capa...")
    plot_04_stacked_abundance(df_insitu)

    print(f"\n[6/10] Correlación satelital vs in situ...")
    plot_05_correlation_sat_insitu(df_insitu, df_sat)

    print(f"\n[7/10] Heatmaps por profundidad...")
    plot_06_heatmap_depth(df_insitu)

    print(f"\n[8/10] Panel resumen multipanel...")
    plot_07_resumen_multipanel(df_insitu, df_sat, nino, mei, pdo)

    print(f"\n[9/10] Boxplots y resumen CSV...")
    plot_08_boxplot_depth_abundance(df_insitu)
    generate_summary_csv(df_insitu, df_sat)

    print(f"\n[10/10] Panel comparativo por grupo (publicación)...")
    plot_09_panel_groups_comparison(df_insitu, df_sat)

    print("\n" + "=" * 70)
    print(f" ✓ Análisis completo. Resultados en:")
    print(f"   {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == '__main__':
    main()
