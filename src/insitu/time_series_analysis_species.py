"""
Análisis de Series de Tiempo de Grupos Funcionales de Fitoplancton
Golfo de California (2000-2024)

Autor: Análisis Oceanográfico
Fecha: 2026

Descripción:
Este script realiza un análisis exhaustivo de las series de tiempo mensuales
de cada grupo de especie (productor primario) para el Golfo de California.
Genera tablas con frequencia de registros y visualizaciones de series de tiempo.
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Rutas
BASE_DIR    = Path(__file__).parent.parent.parent
DATA_DIR    = BASE_DIR / 'data'
NETCDF_FILE = DATA_DIR / 'processed' / 'pft_monthly_statistics.nc'
OUTPUT_DIR  = BASE_DIR / 'results' / 'insitu' / 'edna_v1' / 'series_tiempo'

# Crear directorio de salida
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Definición de productores primarios (Phytoplankton Functional Types)
PRIMARY_PRODUCERS = {
    'DIATO': 'Diatomeas',
    'DINO': 'Dinoflagelados',
    'GREEN': 'Algas Verdes',
    'HAPTO': 'Haptofitas (Coccolitóforos)',
    'PROCHLO': 'Prochlorococcus',
    'PROKAR': 'Procariotas (Cianobacterias)',
    'CRYPTO': 'Criptofitas',
    'PICO': 'Picofitoplancton',
    'NANO': 'Nanofitoplancton',
    'MICRO': 'Microfitoplancton',
    'CHL': 'Clorofila-a Total'
}

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def load_netcdf_data():
    """
    Carga datos NetCDF de fitoplancton del Golfo de California.
    
    Returns:
        xarray.Dataset: Dataset con variables PFT
    """
    print(f"Cargando datos desde: {NETCDF_FILE}")
    ds = xr.open_dataset(NETCDF_FILE)
    print(f"✓ Dataset cargado exitosamente")
    print(f"  Dimensiones: {dict(ds.dims)}")
    print(f"  Variables disponibles: {list(ds.data_vars)}")
    return ds

def create_monthly_series(ds, species_code):
    """
    Crea una serie de tiempo mensual para una especie/variable.
    
    Args:
        ds (xarray.Dataset): Dataset con datos
        species_code (str): Código de la especie (ej: 'DIATO')
    
    Returns:
        pd.DataFrame: Serie de tiempo con columnas Date, Value, Source
    """
    # Intentar obtener datos de mean
    if f'{species_code}_mean' in ds.data_vars:
        var_name = f'{species_code}_mean'
    elif species_code in ds.data_vars:
        var_name = species_code
    else:
        return None
    
    # Extraer datos
    data = ds[var_name].values.flatten()
    
    # Crear índice de tiempo (2000-01 a 2024-12)
    dates = pd.date_range(start='2000-01-01', end='2024-12-01', freq='MS')
    
    # Crear dataframe
    df = pd.DataFrame({
        'Date': dates,
        'Year': dates.year,
        'Month': dates.month,
        'YearMonth': dates.strftime('%Y-%m'),
        'Value': data,
        'Species': PRIMARY_PRODUCERS.get(species_code, species_code),
        'Species_Code': species_code
    })
    
    return df

def calculate_monthly_frequencies(df):
    """
    Calcula frecuencia de registros (non-NaN) por mes.
    
    Args:
        df (pd.DataFrame): Dataframe con series de tiempo
    
    Returns:
        pd.DataFrame: Tabla con frecuencias por mes
    """
    # Contar registros válidos por mes
    monthly_freq = df.groupby('Month').apply(
        lambda x: {
            'month': x['Month'].iloc[0],
            'month_name': pd.Timestamp(year=2000, month=x['Month'].iloc[0], day=1).strftime('%B'),
            'valid_records': x['Value'].notna().sum(),
            'total_records': len(x),
            'missing_records': x['Value'].isna().sum(),
            'mean_value': x['Value'].mean(),
            'std_value': x['Value'].std(),
            'min_value': x['Value'].min(),
            'max_value': x['Value'].max()
        },
        include_groups=False
    )
    
    return monthly_freq

def create_time_series_table(df):
    """
    Crea una tabla completa de series de tiempo (2000-2024).
    Deja espacios en blanco para meses sin datos.
    
    Args:
        df (pd.DataFrame): Dataframe con series de tiempo
    
    Returns:
        pd.DataFrame: Tabla pivotada por año y mes
    """
    # Crear tabla pivotada
    pivot_table = df.pivot_table(
        index='Month',
        columns='Year',
        values='Value',
        fill_value=np.nan
    )
    
    # Renombrar índice con nombres de meses
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    pivot_table.index = [month_names[i-1] for i in pivot_table.index]
    
    return pivot_table

# ============================================================================
# ANÁLISIS PRINCIPAL
# ============================================================================

def main():
    """
    Función principal de análisis.
    """
    print("="*80)
    print("ANÁLISIS DE SERIES DE TIEMPO - PRODUCTORES PRIMARIOS")
    print("Golfo de California (2000-2024)")
    print("="*80)
    print()
    
    # 1. Cargar datos
    ds = load_netcdf_data()
    print()
    
    # 2. Procesar cada especie
    all_results = {}
    all_data_combined = []
    
    print("Procesando datos de cada grupo funcional...")
    print("-" * 80)
    
    for species_code, species_name in PRIMARY_PRODUCERS.items():
        print(f"  Procesando: {species_code:10s} ({species_name})")
        
        # Crear serie de tiempo
        df = create_monthly_series(ds, species_code)
        
        if df is not None:
            # Almacenar resultados
            all_results[species_code] = {
                'dataframe': df,
                'name': species_name
            }
            
            # Agregar a datos combinados
            all_data_combined.append(df)
        else:
            print(f"    ⚠ Advertencia: Variable '{species_code}' no encontrada en dataset")
    
    print()
    print("✓ Procesamiento completado\n")
    
    # 3. Crear DataFrame combinado
    combined_df = pd.concat(all_data_combined, ignore_index=True)
    
    # 4. Generar tablas y estadísticas
    print("="*80)
    print("ESTADÍSTICAS Y TABLAS DE SERIES DE TIEMPO")
    print("="*80)
    print()
    
    for species_code, species_data in all_results.items():
        species_name = species_data['name']
        df = species_data['dataframe']
        
        print(f"\n{species_code}: {species_name}")
        print("-" * 80)
        
        # Estadísticas generales
        print(f"  Período: 2000-01 a 2024-12 (300 meses)")
        print(f"  Registros válidos: {df['Value'].notna().sum()} / {len(df)}")
        print(f"  Cobertura: {(df['Value'].notna().sum() / len(df) * 100):.1f}%")
        print(f"  Media: {df['Value'].mean():.4f}")
        print(f"  Desv. Estándar: {df['Value'].std():.4f}")
        print(f"  Rango: [{df['Value'].min():.4f}, {df['Value'].max():.4f}]")
        
        # Estadísticas mensuales
        print(f"\n  Frecuencia de registros por mes:")
        monthly_freq = df.groupby('Month').agg({
            'Value': ['count', 'mean', 'std', 'min', 'max']
        }).round(4)
        monthly_freq.columns = ['Count', 'Mean', 'Std', 'Min', 'Max']
        print(monthly_freq)
        
        # Guardar tabla pivotada (serie de tiempo)
        pivot_table = create_time_series_table(df)
        csv_path = OUTPUT_DIR / f'{species_code}_timeseries.csv'
        pivot_table.to_csv(csv_path)
        print(f"\n  ✓ Tabla de serie de tiempo guardada: {csv_path.name}")
        
        # Guardar estadísticas mensuales
        stats_path = OUTPUT_DIR / f'{species_code}_monthly_stats.csv'
        monthly_freq.to_csv(stats_path)
        print(f"  ✓ Estadísticas mensuales guardadas: {stats_path.name}")
    
    # 5. Crear visualizaciones
    print("\n" + "="*80)
    print("GENERANDO GRÁFICAS DE SERIES DE TIEMPO")
    print("="*80)
    print()
    
    # 5.1 Gráfica individual por especie (completa)
    for species_code, species_data in all_results.items():
        species_name = species_data['name']
        df = species_data['dataframe']
        
        fig, ax = plt.subplots(figsize=(16, 6))
        
        # Plotear serie de tiempo
        ax.plot(df['Date'], df['Value'], linewidth=2, color='#2E86AB', alpha=0.8)
        ax.scatter(df[df['Value'].notna()]['Date'], 
                  df[df['Value'].notna()]['Value'],
                  s=20, color='#A23B72', alpha=0.5)
        
        # Dejar espacios en blanco para datos sin registros
        missing_dates = df[df['Value'].isna()]['Date']
        if len(missing_dates) > 0:
            ax.axvspan(missing_dates.iloc[0], missing_dates.iloc[-1], 
                       alpha=0.1, color='gray', label='Sin datos')
        
        # Formato
        ax.set_title(f'Serie de Tiempo: {species_code} - {species_name}\nGolfo de California (2000-2024)',
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Año', fontsize=12)
        ax.set_ylabel('Concentración (mg m⁻³)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10)
        
        # Guardar figura
        fig_path = OUTPUT_DIR / f'{species_code}_timeseries.png'
        plt.tight_layout()
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ {species_code:10s} guardada: {fig_path.name}")
    
    # 5.2 Gráfica comparativa de todas las especies (normalizado)
    print("\n  Generando gráfica comparativa...")
    fig, axes = plt.subplots(3, 4, figsize=(20, 14))
    axes = axes.flatten()
    
    for idx, (species_code, species_data) in enumerate(all_results.items()):
        ax = axes[idx]
        df = species_data['dataframe']
        species_name = species_data['name']
        
        # Normalizar para comparación
        values = df['Value'].values
        values_norm = (values - np.nanmin(values)) / (np.nanmax(values) - np.nanmin(values))
        
        ax.plot(df['Date'], values_norm, linewidth=2, color='#2E86AB', alpha=0.8)
        ax.fill_between(df['Date'], values_norm, alpha=0.3, color='#2E86AB')
        
        ax.set_title(f'{species_code}: {species_name}', fontsize=11, fontweight='bold')
        ax.set_xlabel('Año', fontsize=9)
        ax.set_ylabel('Normalizado', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=8)
    
    # Ocultar último subplot vacío
    axes[-1].set_visible(False)
    
    plt.suptitle('Comparación de Series de Tiempo Normalizadas - Productores Primarios\nGolfo de California (2000-2024)',
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    comp_path = OUTPUT_DIR / 'todas_especies_comparacion.png'
    plt.savefig(comp_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Gráfica comparativa guardada: {comp_path.name}")
    
    # 5.3 Heatmap de anomalías mensuales
    print("\n  Generando heatmap de anomalías mensuales...")
    
    fig, axes = plt.subplots(4, 3, figsize=(16, 14))
    axes = axes.flatten()
    
    for idx, (species_code, species_data) in enumerate(all_results.items()):
        ax = axes[idx]
        df = species_data['dataframe']
        species_name = species_data['name']
        
        # Crear tabla para heatmap
        pivot = df.pivot_table(index='Month', columns='Year', values='Value')
        
        # Calcular anomalías (resta de la media climática)
        clim_mean = df.groupby('Month')['Value'].mean()
        anomalies = pivot.sub(clim_mean, axis=0)
        
        # Plotear heatmap
        sns.heatmap(anomalies, cmap='RdBu_r', center=0, ax=ax,
                   cbar_kws={'label': 'Anomalía'}, vmin=-1, vmax=1)
        
        ax.set_title(f'{species_code}: {species_name}', fontsize=10, fontweight='bold')
        ax.set_xlabel('')
        ax.set_ylabel('Mes', fontsize=9)
    
    axes[-1].set_visible(False)
    
    plt.suptitle('Heatmap de Anomalías Mensuales - Productores Primarios\nGolfo de California (2000-2024)',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    heat_path = OUTPUT_DIR / 'anomalias_mensuales_heatmap.png'
    plt.savefig(heat_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Heatmap de anomalías guardado: {heat_path.name}")
    
    # 6. Resumen final
    print("\n" + "="*80)
    print("RESUMEN DE ARCHIVOS GENERADOS")
    print("="*80)
    print(f"\nDirectorio de salida: {OUTPUT_DIR}")
    print("\nArchivos generados:")
    
    output_files = sorted(OUTPUT_DIR.glob('*'))
    for i, file in enumerate(output_files, 1):
        size_kb = file.stat().st_size / 1024
        print(f"  {i:2d}. {file.name:50s} ({size_kb:>8.1f} KB)")
    
    print("\n" + "="*80)
    print("✓ ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("="*80)

if __name__ == '__main__':
    main()
