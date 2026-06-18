#!/usr/bin/env python3
"""
Comparación de Series de Tiempo: Producción Primaria Satelital vs eDNA In Situ
==============================================================================

Genera gráficas de series de tiempo combinadas para cada grupo funcional
de fitoplancton, mostrando:
  - Eje principal: concentración satelital (mg m⁻³) con media móvil
  - Eje secundario: frecuencia de ocurrencia eDNA in situ (registros mensuales)
  - Panel inferior: índices climáticos (NIÑO 3.4, MEI, PDO)

Datos:
  - Satelital: pft_monthly_statistics.nc (Copernicus, 2000-2024)
  - In situ:   taxonomy_corrected_edna_2.csv (eDNA, Golfo de California)
  - Climáticos: nino34, mei, pdo

Autor: Script generado para análisis de producción primaria oceánica
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from datetime import datetime
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# =============================================================================
# CONFIGURACIÓN DE RUTAS
# =============================================================================
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'results' / 'insitu' / 'edna_v2' / 'series_tiempo' / 'comparacion_satelital_insitu'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Archivos de datos
SATELLITE_FILE = DATA_DIR / 'processed' / 'pft_monthly_statistics.nc'
TAXONOMY_FILE = DATA_DIR / 'insitu' / 'taxonomy_corrected_edna_2.csv'
NINO_FILE = DATA_DIR / 'raw' / 'nino34.long.anom.csv'
MEI_FILE = DATA_DIR / 'raw' / 'mei.exttimeseries.csv'
PDO_FILE = DATA_DIR / 'raw' / 'pdo.timeseries.sstens.csv'

# Rango temporal
START_DATE = '2000-01-01'
END_DATE = '2024-12-31'

# =============================================================================
# MAPEO SATELITAL <-> IN SITU
# =============================================================================
# Cada entrada: (nombre_display, variable_satelital, grupos_insitu_phyla)
SPECIES_MAPPING = [
    {
        'name': 'Dinoflagelados',
        'name_en': 'Dinoflagellates',
        'sat_var': 'DINO_mean',
        'insitu_phyla': ['Dinophyta', 'Dinophyceae', 'Myzozoa'],
        'insitu_classes': ['Dinophyceae'],
        'insitu_kingdoms': [],
        'color_sat': '#2E86AB',
        'color_insitu': '#E63946',
    },
    {
        'name': 'Diatomeas',
        'name_en': 'Diatoms',
        'sat_var': 'DIATO_mean',
        'insitu_phyla': ['Bacillariophyta'],
        'insitu_classes': ['Diatomophyceae', 'Fragilariophyceae', 'Bacillariophyceae'],
        'insitu_kingdoms': [],
        'color_sat': '#1B9E77',
        'color_insitu': '#D95F02',
    },
    {
        'name': 'Clorofitas (Algas Verdes)',
        'name_en': 'Green Algae (Chlorophyta)',
        'sat_var': 'GREEN_mean',
        'insitu_phyla': ['Chlorophyta'],
        'insitu_classes': ['Chlorophyceae', 'Ulvophyceae'],
        'insitu_kingdoms': [],
        'color_sat': '#66A61E',
        'color_insitu': '#E6AB02',
    },
    {
        'name': 'Haptofitas',
        'name_en': 'Haptophytes',
        'sat_var': 'HAPTO_mean',
        'insitu_phyla': ['Haptophyta'],
        'insitu_classes': ['Prymnesiophyceae', 'Coccolithophyceae'],
        'insitu_kingdoms': [],
        'color_sat': '#7570B3',
        'color_insitu': '#A6761D',
    },
    {
        'name': 'Cianobacterias (Procariontes)',
        'name_en': 'Cyanobacteria (Prokaryotes)',
        'sat_var': 'PROKAR_mean',
        'insitu_phyla': ['Cyanobacteria'],
        'insitu_classes': ['Oxyphotobacteria'],
        'insitu_kingdoms': ['Bacteria'],
        'color_sat': '#E7298A',
        'color_insitu': '#666666',
    },
    {
        'name': 'Clorofila Total vs Todos los Grupos',
        'name_en': 'Total Chlorophyll vs All Groups',
        'sat_var': 'CHL_mean',
        'insitu_phyla': '__ALL__',  # Señal especial para usar todos los registros clasificados
        'insitu_classes': [],
        'insitu_kingdoms': [],
        'color_sat': '#1F77B4',
        'color_insitu': '#FF7F0E',
    },
]

# =============================================================================
# CLASIFICACIÓN DE PRODUCTORES PRIMARIOS (consistente con script in situ)
# =============================================================================
PRIMARY_PRODUCERS = {
    'Diatomeas': ['Bacillariophyta', 'Diatomophyceae', 'Fragilariophyceae', 'Bacillariophyceae'],
    'Dinoflagelados': ['Dinophyta', 'Dinophyceae', 'Myzozoa'],
    'Clorofitas': ['Chlorophyta', 'Chlorophyceae', 'Ulvophyceae'],
    'Cianobacterias': ['Cyanobacteria', 'Oxyphotobacteria'],
    'Haptofitas': ['Haptophyta', 'Prymnesiophyceae', 'Coccolithophyceae'],
    'Otros Eucariotas': ['Eukaryota'],
    'Protozoa': ['Protozoa', 'Discosea', 'Amoebozoa'],
}


# =============================================================================
# FUNCIONES PARA CARGAR DATOS
# =============================================================================

def excel_date_to_datetime(excel_date):
    """Convierte número serial de Excel o texto DD/MM/YYYY a datetime."""
    if pd.isna(excel_date) or excel_date == '':
        return pd.NaT
    try:
        if isinstance(excel_date, str):
            if '/' in excel_date:
                return pd.to_datetime(excel_date, format='%d/%m/%Y', errors='coerce')
            else:
                excel_date = float(excel_date)
        excel_epoch = datetime(1899, 12, 30)
        return excel_epoch + pd.Timedelta(days=int(excel_date))
    except (ValueError, OverflowError):
        return pd.NaT


def load_satellite_data():
    """Carga datos satelitales mensuales pre-procesados."""
    print("  Cargando datos satelitales (pft_monthly_statistics.nc)...")
    ds = xr.open_dataset(SATELLITE_FILE)
    
    # Convertir a DataFrame con índice temporal
    df_sat = pd.DataFrame(index=pd.to_datetime(ds.time.values))
    for var in ds.data_vars:
        df_sat[var] = ds[var].values
    
    ds.close()
    
    # Filtrar rango temporal
    df_sat = df_sat[START_DATE:END_DATE]
    print(f"    → {len(df_sat)} meses, {len(df_sat.columns)} variables")
    return df_sat


def load_insitu_data():
    """Carga y clasifica datos eDNA in situ."""
    print("  Cargando datos eDNA in situ (taxonomy_corrected_edna_2.csv)...")
    df = pd.read_csv(TAXONOMY_FILE)
    
    # Convertir fechas
    df['date'] = df['Collected date year'].apply(excel_date_to_datetime)
    df = df.dropna(subset=['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    # Filtrar rango 2000-2024
    df = df[(df['year'] >= 2000) & (df['year'] <= 2024)].copy()
    
    # Clasificar en grupos de productores primarios
    def classify_producer(row):
        phylum = str(row.get('phylum', '')).strip() if pd.notna(row.get('phylum')) else ''
        class_tax = str(row.get('class', '')).strip() if pd.notna(row.get('class')) else ''
        kingdom = str(row.get('kingdom', '')).strip() if pd.notna(row.get('kingdom')) else ''
        
        for group, values in PRIMARY_PRODUCERS.items():
            if phylum in values or class_tax in values or kingdom in values:
                return group
        
        if kingdom == 'Protozoa' or phylum == 'Amoebozoa':
            return 'Protozoa'
        return 'Otros'
    
    df['grupo_primario'] = df.apply(classify_producer, axis=1)
    
    print(f"    → {len(df)} registros válidos (2000-2024)")
    print("    Grupos clasificados:")
    for g in sorted(df['grupo_primario'].unique()):
        print(f"      {g}: {len(df[df['grupo_primario'] == g])}")
    
    return df


def build_insitu_monthly_series(df_insitu, mapping_entry):
    """
    Construye serie de tiempo mensual de frecuencia de ocurrencia para un grupo.
    Retorna pd.Series con índice DatetimeIndex mensual y valores = conteo de registros.
    """
    if mapping_entry['insitu_phyla'] == '__ALL__':
        # Todos los productores primarios (excluyendo 'Otros' no clasificados)
        df_group = df_insitu[df_insitu['grupo_primario'] != 'Otros'].copy()
    else:
        # Filtrar por phylum, class o kingdom
        phyla = mapping_entry['insitu_phyla']
        classes = mapping_entry['insitu_classes']
        kingdoms = mapping_entry['insitu_kingdoms']
        
        mask = (
            df_insitu['phylum'].isin(phyla) |
            df_insitu['class'].isin(classes) |
            df_insitu['kingdom'].isin(kingdoms)
        )
        df_group = df_insitu[mask].copy()
    
    if len(df_group) == 0:
        return pd.Series(dtype=float)
    
    # Agrupar por año-mes y contar registros
    df_group['year_month'] = pd.to_datetime(
        df_group['year'].astype(str) + '-' + df_group['month'].astype(str).str.zfill(2) + '-01'
    )
    monthly_counts = df_group.groupby('year_month').size()
    monthly_counts.index = pd.DatetimeIndex(monthly_counts.index)
    monthly_counts = monthly_counts.sort_index()
    
    return monthly_counts


def load_nino34():
    """Carga índice NIÑO 3.4."""
    try:
        df = pd.read_csv(NINO_FILE, skiprows=1, header=None, names=['Date', 'NINO34'])
        df['Date'] = pd.to_datetime(df['Date'].str.strip())
        df['NINO34'] = pd.to_numeric(df['NINO34'], errors='coerce')
        df = df[df['NINO34'] > -90].dropna()
        series = df.set_index('Date')['NINO34']
        return series[START_DATE:END_DATE]
    except Exception as e:
        print(f"    ⚠ Error cargando NIÑO 3.4: {e}")
        return None


def load_mei():
    """Carga índice MEI (Multivariate ENSO Index)."""
    try:
        chunks = []
        with open(MEI_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts or not parts[0].isdigit() or len(parts) < 13:
                    continue
                year = int(parts[0])
                for month_idx, val in enumerate(parts[1:13]):
                    try:
                        val_float = float(val)
                        if val_float > -90:
                            date = pd.Timestamp(year=year, month=month_idx + 1, day=1)
                            chunks.append({'Date': date, 'MEI': val_float})
                    except ValueError:
                        pass
        df = pd.DataFrame(chunks)
        series = df.set_index('Date')['MEI']
        return series[START_DATE:END_DATE]
    except Exception as e:
        print(f"    ⚠ Error cargando MEI: {e}")
        return None


def load_pdo():
    """Carga índice PDO (Pacific Decadal Oscillation)."""
    try:
        df = pd.read_csv(PDO_FILE, skiprows=1, header=None, usecols=[0, 1], names=['Date', 'PDO'])
        df['Date'] = pd.to_datetime(df['Date'])
        df['PDO'] = pd.to_numeric(df['PDO'], errors='coerce')
        df = df.dropna()
        series = df.set_index('Date')['PDO']
        return series[START_DATE:END_DATE]
    except Exception as e:
        print(f"    ⚠ Error cargando PDO: {e}")
        return None


# =============================================================================
# FUNCIÓN PRINCIPAL DE GRAFICADO
# =============================================================================

def plot_combined_timeseries(df_sat, df_insitu, mapping, nino, mei, pdo):
    """
    Genera una figura por cada grupo funcional con:
      - Panel superior: serie de tiempo satelital + in situ (eje secundario)
      - Panel inferior: índices climáticos
    """
    sat_var = mapping['sat_var']
    group_name = mapping['name']
    group_name_en = mapping['name_en']
    color_sat = mapping['color_sat']
    color_insitu = mapping['color_insitu']
    
    # Verificar que la variable satelital existe
    if sat_var not in df_sat.columns:
        print(f"  ⚠ Variable satelital '{sat_var}' no encontrada, saltando {group_name}")
        return
    
    # Serie satelital
    sat_series = df_sat[sat_var].dropna()
    
    # Variable de dispersión (std) si existe
    sat_std_var = sat_var.replace('_mean', '_std')
    sat_std = df_sat[sat_std_var] if sat_std_var in df_sat.columns else None
    
    # Serie in situ
    insitu_series = build_insitu_monthly_series(df_insitu, mapping)
    
    if len(insitu_series) == 0:
        print(f"  ⚠ Sin datos in situ para {group_name}, generando solo satelital")
    
    # Media móvil de 12 meses para satelital
    sat_rolling = sat_series.rolling(window=12, center=True).mean()
    
    # =========================================================================
    # CREAR FIGURA
    # =========================================================================
    fig = plt.figure(figsize=(18, 14))
    
    # Grid: 3 filas con proporciones [4, 4, 2]
    gs = fig.add_gridspec(3, 1, height_ratios=[4, 4, 2.5], hspace=0.3)
    
    # ----- PANEL 1: Series de tiempo satelital + in situ -----
    ax1 = fig.add_subplot(gs[0])
    
    # Satelital en eje principal
    ax1.plot(sat_series.index, sat_series.values,
             linewidth=1.2, color=color_sat, alpha=0.6, label='Satelital (mensual)')
    ax1.plot(sat_rolling.index, sat_rolling.values,
             linewidth=2.5, color=color_sat, alpha=0.9, label='Satelital (media móvil 12 meses)')
    
    # Banda de variabilidad satelital (±1 std)
    if sat_std is not None:
        sat_std_aligned = sat_std.reindex(sat_series.index)
        ax1.fill_between(sat_series.index,
                         (sat_series - sat_std_aligned).values,
                         (sat_series + sat_std_aligned).values,
                         alpha=0.15, color=color_sat, label='±1 σ espacial')
    
    ax1.set_ylabel(f'Concentración Satelital (mg m⁻³)', fontsize=12, fontweight='bold',
                    color=color_sat)
    ax1.tick_params(axis='y', labelcolor=color_sat, labelsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)
    
    # Estadísticas satelitales
    stats_sat = (f'Satelital: min={sat_series.min():.4f}, max={sat_series.max():.4f}, '
                 f'media={sat_series.mean():.4f} mg m⁻³')
    
    # In situ en eje secundario
    if len(insitu_series) > 0:
        ax1_twin = ax1.twinx()
        
        # Barras para frecuencia de ocurrencia
        bar_width = 20  # días
        ax1_twin.bar(insitu_series.index, insitu_series.values,
                     width=bar_width, alpha=0.5, color=color_insitu,
                     edgecolor=color_insitu, linewidth=0.5,
                     label='eDNA in situ (frecuencia)')
        
        # Línea conectando puntos in situ
        ax1_twin.plot(insitu_series.index, insitu_series.values,
                      marker='o', markersize=4, linewidth=1.2,
                      color=color_insitu, alpha=0.7, linestyle='--',
                      label='eDNA in situ (tendencia)')
        
        ax1_twin.set_ylabel('Frecuencia de Ocurrencia eDNA\n(registros mensuales)',
                            fontsize=11, fontweight='bold', color=color_insitu)
        ax1_twin.tick_params(axis='y', labelcolor=color_insitu, labelsize=10)
        
        stats_insitu = (f'In situ: total={int(insitu_series.sum())}, '
                        f'meses con datos={len(insitu_series)}, '
                        f'max mensual={int(insitu_series.max())}')
        
        # Leyenda combinada
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1_twin.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2,
                   loc='upper right', fontsize=9, framealpha=0.9, ncol=2)
    else:
        stats_insitu = 'In situ: sin datos'
        ax1.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
    ax1.set_title(f'{group_name} ({group_name_en})\n'
                  f'Producción Primaria Satelital vs Frecuencia eDNA In Situ (2000-2024)',
                  fontsize=14, fontweight='bold')
    
    # Box de estadísticas
    ax1.text(0.02, 0.98, f'{stats_sat}\n{stats_insitu}',
             transform=ax1.transAxes, fontsize=8.5, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
             family='monospace')
    
    # ----- PANEL 2: Anomalías satelitales + índices climáticos -----
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    
    # Anomalía satelital
    sat_mean = sat_series.mean()
    anomaly = sat_series - sat_mean
    colors_anom = ['#2ca02c' if x >= 0 else '#d62728' for x in anomaly]
    ax2.bar(anomaly.index, anomaly.values, width=25,
            color=colors_anom, alpha=0.6, edgecolor='none', linewidth=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.set_ylabel(f'Anomalía Satelital\n(mg m⁻³)', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.set_axisbelow(True)
    ax2.set_title(f'Anomalía de Concentración Satelital + Índices Climáticos',
                  fontsize=12, fontweight='bold')
    
    # Índices climáticos en eje secundario
    ax2_twin = ax2.twinx()
    
    climate_lines = []
    climate_labels = []
    
    if nino is not None:
        nino_aligned = nino.reindex(sat_series.index, method='nearest')
        l1, = ax2_twin.plot(nino_aligned.index, nino_aligned.values,
                            color='#FF9500', linewidth=2, label='NIÑO 3.4', zorder=5)
        climate_lines.append(l1)
        climate_labels.append('NIÑO 3.4')
    
    if mei is not None:
        mei_aligned = mei.reindex(sat_series.index, method='nearest')
        l2, = ax2_twin.plot(mei_aligned.index, mei_aligned.values,
                            color='#9B59B6', linewidth=1.8, linestyle='--',
                            label='MEI', zorder=4)
        climate_lines.append(l2)
        climate_labels.append('MEI')
    
    if pdo is not None:
        pdo_aligned = pdo.reindex(sat_series.index, method='nearest')
        l3, = ax2_twin.plot(pdo_aligned.index, pdo_aligned.values,
                            color='#34495E', linewidth=1.8, linestyle=':',
                            label='PDO', zorder=3)
        climate_lines.append(l3)
        climate_labels.append('PDO')
    
    ax2_twin.set_ylabel('Valor del Índice Climático', fontsize=11, fontweight='bold')
    ax2_twin.tick_params(axis='y', labelsize=10)
    
    # Leyenda combinada del panel 2
    anom_patch = plt.Rectangle((0, 0), 1, 1, fc='#2ca02c', alpha=0.6, label='Anomalía (+)')
    anom_patch_neg = plt.Rectangle((0, 0), 1, 1, fc='#d62728', alpha=0.6, label='Anomalía (-)')
    custom_handles = [anom_patch, anom_patch_neg] + climate_lines
    custom_labels = ['Anomalía (+)', 'Anomalía (-)'] + climate_labels
    ax2_twin.legend(custom_handles, custom_labels, loc='upper right',
                    fontsize=9, framealpha=0.9, ncol=3)
    
    # ----- PANEL 3: Correlación temporal (si hay datos in situ) -----
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    
    if len(insitu_series) > 0:
        # Normalizar ambas series para comparación directa
        sat_norm = (sat_series - sat_series.mean()) / sat_series.std()
        
        # Reindexar in situ al mismo eje temporal que satelital
        insitu_reindexed = insitu_series.reindex(sat_series.index).fillna(0)
        insitu_norm = (insitu_reindexed - insitu_reindexed.mean()) / (insitu_reindexed.std() + 1e-10)
        
        ax3.plot(sat_norm.index, sat_norm.values,
                 linewidth=1.5, color=color_sat, alpha=0.7, label='Satelital (normalizada)')
        ax3.plot(insitu_norm.index, insitu_norm.values,
                 linewidth=1.5, color=color_insitu, alpha=0.7, label='eDNA in situ (normalizada)')
        ax3.fill_between(sat_norm.index, sat_norm.values, alpha=0.1, color=color_sat)
        ax3.fill_between(insitu_norm.index, insitu_norm.values, alpha=0.1, color=color_insitu)
        
        ax3.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax3.set_ylabel('Valores Normalizados\n(z-score)', fontsize=11, fontweight='bold')
        ax3.set_title('Comparación Normalizada: Satelital vs In Situ', fontsize=12, fontweight='bold')
        
        # Calcular correlación solo en meses donde hay datos in situ
        common_idx = sat_series.index.intersection(insitu_series.index)
        if len(common_idx) >= 3:
            corr = np.corrcoef(
                sat_series.reindex(common_idx).values,
                insitu_series.reindex(common_idx).values
            )[0, 1]
            ax3.text(0.02, 0.95, f'r = {corr:.3f} (n={len(common_idx)} meses comunes)',
                     transform=ax3.transAxes, fontsize=10, verticalalignment='top',
                     bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9),
                     fontweight='bold')
        
        ax3.legend(loc='upper right', fontsize=9, framealpha=0.9)
    else:
        # Sin datos in situ: mostrar solo climatología satelital
        sat_monthly_clim = sat_series.groupby(sat_series.index.month).mean()
        months_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                         'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        ax3.bar(range(1, 13), sat_monthly_clim.values, color=color_sat, alpha=0.7)
        ax3.set_xticks(range(1, 13))
        ax3.set_xticklabels(months_labels)
        ax3.set_ylabel('Concentración Media\n(mg m⁻³)', fontsize=11, fontweight='bold')
        ax3.set_title('Climatología Mensual Satelital (sin datos in situ)', fontsize=12)
    
    ax3.grid(True, alpha=0.3, linestyle='--')
    ax3.set_axisbelow(True)
    
    # Formato del eje X
    ax3.set_xlabel('Año', fontsize=12, fontweight='bold')
    ax3.xaxis.set_major_locator(mdates.YearLocator(2))
    ax3.xaxis.set_minor_locator(mdates.YearLocator(1))
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Guardar
    safe_name = group_name.lower().replace(' ', '_').replace('(', '').replace(')', '')
    safe_name = safe_name.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o')
    filename = f'comparacion_sat_insitu_{safe_name}.png'
    filepath = OUTPUT_DIR / filename
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"  ✓ Guardado: {filepath}")
    plt.close()


def plot_overview_all_groups(df_sat, df_insitu, nino, mei, pdo):
    """
    Genera una figura resumen con todos los grupos funcionales en paneles.
    Cada panel muestra satelital (eje izquierdo) + in situ (eje derecho).
    """
    n_groups = len(SPECIES_MAPPING)
    fig, axes = plt.subplots(n_groups + 1, 1, figsize=(20, 4 * (n_groups + 1)),
                              sharex=True)
    
    for idx, mapping in enumerate(SPECIES_MAPPING):
        ax = axes[idx]
        sat_var = mapping['sat_var']
        
        if sat_var not in df_sat.columns:
            ax.text(0.5, 0.5, f'{mapping["name"]}: sin datos satelitales',
                    transform=ax.transAxes, ha='center', fontsize=12)
            continue
        
        sat_series = df_sat[sat_var].dropna()
        sat_rolling = sat_series.rolling(window=12, center=True).mean()
        insitu_series = build_insitu_monthly_series(df_insitu, mapping)
        
        # Satelital
        ax.plot(sat_series.index, sat_series.values,
                linewidth=1, color=mapping['color_sat'], alpha=0.4)
        ax.plot(sat_rolling.index, sat_rolling.values,
                linewidth=2.5, color=mapping['color_sat'], alpha=0.9,
                label=f'{mapping["name"]} - Satelital')
        ax.fill_between(sat_series.index, sat_series.values,
                        alpha=0.1, color=mapping['color_sat'])
        
        ax.set_ylabel('mg m⁻³', fontsize=10, color=mapping['color_sat'], fontweight='bold')
        ax.tick_params(axis='y', labelcolor=mapping['color_sat'], labelsize=9)
        
        # In situ en eje secundario
        if len(insitu_series) > 0:
            ax_twin = ax.twinx()
            ax_twin.bar(insitu_series.index, insitu_series.values,
                        width=20, alpha=0.4, color=mapping['color_insitu'],
                        edgecolor=mapping['color_insitu'], linewidth=0.3,
                        label=f'{mapping["name"]} - eDNA')
            ax_twin.set_ylabel('Registros\neDNA', fontsize=9,
                              color=mapping['color_insitu'], fontweight='bold')
            ax_twin.tick_params(axis='y', labelcolor=mapping['color_insitu'], labelsize=9)
            
            # Leyenda combinada
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax_twin.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2,
                      loc='upper right', fontsize=8, framealpha=0.9, ncol=2)
        else:
            ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
        
        ax.set_title(f'{mapping["name"]} ({mapping["name_en"]})',
                      fontsize=11, fontweight='bold', loc='left')
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.set_axisbelow(True)
    
    # Panel inferior: índices climáticos
    ax_climate = axes[-1]
    
    if nino is not None:
        ax_climate.plot(nino.index, nino.values,
                        color='#FF9500', linewidth=2, label='NIÑO 3.4')
        ax_climate.fill_between(nino.index, 0, nino.values,
                                where=nino.values > 0, alpha=0.2, color='red',
                                label='El Niño')
        ax_climate.fill_between(nino.index, 0, nino.values,
                                where=nino.values < 0, alpha=0.2, color='blue',
                                label='La Niña')
    
    if mei is not None:
        ax_climate.plot(mei.index, mei.values,
                        color='#9B59B6', linewidth=1.5, linestyle='--', label='MEI')
    
    if pdo is not None:
        ax_climate.plot(pdo.index, pdo.values,
                        color='#34495E', linewidth=1.5, linestyle=':', label='PDO')
    
    ax_climate.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax_climate.set_ylabel('Valor del Índice', fontsize=11, fontweight='bold')
    ax_climate.set_title('Índices Climáticos', fontsize=11, fontweight='bold', loc='left')
    ax_climate.legend(loc='upper right', fontsize=9, framealpha=0.9, ncol=5)
    ax_climate.grid(True, alpha=0.3, linestyle='--')
    ax_climate.set_axisbelow(True)
    
    ax_climate.set_xlabel('Año', fontsize=12, fontweight='bold')
    ax_climate.xaxis.set_major_locator(mdates.YearLocator(2))
    ax_climate.xaxis.set_minor_locator(mdates.YearLocator(1))
    ax_climate.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax_climate.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    fig.suptitle('Comparación Global: Producción Primaria Satelital vs eDNA In Situ\n'
                 'Golfo de California (2000-2024)',
                 fontsize=16, fontweight='bold', y=1.01)
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / 'resumen_todos_grupos_sat_vs_insitu.png'
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"  ✓ Guardado resumen: {filepath}")
    plt.close()


def plot_seasonal_comparison(df_sat, df_insitu):
    """
    Comparación estacional: climatología mensual satelital vs in situ por grupo.
    """
    months_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                     'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    n_groups = len(SPECIES_MAPPING) - 1  # Excluir CHL total
    ncols = 3
    nrows = int(np.ceil(n_groups / ncols))
    
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 5 * nrows))
    axes_flat = axes.flatten()
    
    for idx, mapping in enumerate([m for m in SPECIES_MAPPING if m['sat_var'] != 'CHL_mean']):
        ax = axes_flat[idx]
        sat_var = mapping['sat_var']
        
        if sat_var not in df_sat.columns:
            continue
        
        sat_series = df_sat[sat_var].dropna()
        insitu_series = build_insitu_monthly_series(df_insitu, mapping)
        
        # Climatología mensual satelital
        sat_clim = sat_series.groupby(sat_series.index.month).mean()
        sat_clim_std = sat_series.groupby(sat_series.index.month).std()
        
        x = np.arange(1, 13)
        width = 0.35
        
        # Barras satelitales
        bars1 = ax.bar(x - width / 2, sat_clim.values, width,
                        color=mapping['color_sat'], alpha=0.7, label='Satelital',
                        yerr=sat_clim_std.values, capsize=3, ecolor='gray')
        ax.set_ylabel('mg m⁻³', fontsize=10, color=mapping['color_sat'])
        ax.tick_params(axis='y', labelcolor=mapping['color_sat'])
        
        # In situ en eje secundario
        if len(insitu_series) > 0:
            ax_twin = ax.twinx()
            insitu_clim = insitu_series.groupby(insitu_series.index.month).mean()
            # Rellenar meses sin datos
            insitu_clim_full = pd.Series(0.0, index=range(1, 13))
            for m in insitu_clim.index:
                insitu_clim_full[m] = insitu_clim[m]
            
            bars2 = ax_twin.bar(x + width / 2, insitu_clim_full.values, width,
                                 color=mapping['color_insitu'], alpha=0.6,
                                 label='eDNA in situ')
            ax_twin.set_ylabel('Registros\npromedio', fontsize=9,
                              color=mapping['color_insitu'])
            ax_twin.tick_params(axis='y', labelcolor=mapping['color_insitu'])
            
            # Leyenda combinada
            ax.legend([bars1, bars2], ['Satelital', 'eDNA in situ'],
                      loc='upper right', fontsize=8)
        
        ax.set_xticks(x)
        ax.set_xticklabels(months_labels, fontsize=8, rotation=45)
        ax.set_title(mapping['name'], fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.2, axis='y')
    
    # Ocultar ejes vacíos
    for idx in range(n_groups, len(axes_flat)):
        axes_flat[idx].set_visible(False)
    
    fig.suptitle('Climatología Mensual: Satelital vs eDNA In Situ\n'
                 'Golfo de California (2000-2024)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    filepath = OUTPUT_DIR / 'climatologia_mensual_sat_vs_insitu.png'
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
    print(f"  ✓ Guardado climatología: {filepath}")
    plt.close()


# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

def main():
    print("=" * 70)
    print(" COMPARACIÓN: Producción Primaria Satelital vs eDNA In Situ")
    print(" Golfo de California (2000-2024)")
    print("=" * 70)
    
    # 1. Cargar datos
    print("\n[1/4] Cargando datos...")
    df_sat = load_satellite_data()
    df_insitu = load_insitu_data()
    
    print("\n  Cargando índices climáticos...")
    nino = load_nino34()
    mei = load_mei()
    pdo = load_pdo()
    
    print(f"    NIÑO 3.4: {'✓' if nino is not None else '✗'} "
          f"({len(nino) if nino is not None else 0} meses)")
    print(f"    MEI:      {'✓' if mei is not None else '✗'} "
          f"({len(mei) if mei is not None else 0} meses)")
    print(f"    PDO:      {'✓' if pdo is not None else '✗'} "
          f"({len(pdo) if pdo is not None else 0} meses)")
    
    # 2. Gráficas individuales por grupo
    print(f"\n[2/4] Generando gráficas individuales ({len(SPECIES_MAPPING)} grupos)...")
    for mapping in SPECIES_MAPPING:
        print(f"\n  → {mapping['name']}:")
        plot_combined_timeseries(df_sat, df_insitu, mapping, nino, mei, pdo)
    
    # 3. Gráfica resumen con todos los grupos
    print(f"\n[3/4] Generando gráfica resumen...")
    plot_overview_all_groups(df_sat, df_insitu, nino, mei, pdo)
    
    # 4. Comparación estacional
    print(f"\n[4/4] Generando comparación estacional...")
    plot_seasonal_comparison(df_sat, df_insitu)
    
    print("\n" + "=" * 70)
    print(f" ✓ Todas las gráficas generadas en:")
    print(f"   {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == '__main__':
    main()
