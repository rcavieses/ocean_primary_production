"""
Script para descomposición STL de series temporales de producción primaria fitoplanctónica
por grupo funcional (especie y tamaño), identificación de eventos extremos y generación de gráficos.

Referencias:
- Cleveland et al., 1990. STL: A Seasonal-Trend Decomposition Procedure Based on Loess.

Requiere: statsmodels, matplotlib, pandas, xarray
"""
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import STL
from pathlib import Path

# Configuración
BASE_DIR = Path(__file__).parent.parent.parent
DATA_FILE = BASE_DIR / 'data' / 'processed' / 'pft_monthly_statistics.nc'
OUTPUT_DIR = BASE_DIR / 'results' / 'satellite' / 'figures' / 'stl_decomposition'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SPECIES_VARS = [
    'DIATO_mean', 'DINO_mean', 'GREEN_mean', 'HAPTO_mean', 'PROCHLO_mean', 'PROKAR_mean'
]
SIZE_VARS = [
    'MICRO_mean', 'NANO_mean', 'PICO_mean'
]

# Función para análisis STL y eventos extremos
def analyze_stl_and_extremes(series, var_name, output_dir):
    # STL requiere frecuencia regular y sin NaN
    series = series.asfreq('MS')
    # Si la serie tiene menos de 24 datos válidos, omitir análisis
    if series.dropna().shape[0] < 24:
        print(f"{var_name}: Serie insuficiente para STL/descomposición.")
        pd.DataFrame({'fecha_bajo': [], 'anomalia_bajo': []}).to_csv(output_dir / f'{var_name}_eventos_bajos.csv', index=False)
        pd.DataFrame({'fecha_alto': [], 'anomalia_alto': []}).to_csv(output_dir / f'{var_name}_eventos_altos.csv', index=False)
        return
    # STL no acepta NaN: interpolar huecos temporales antes de ajustar
    series_stl = series.interpolate(method='time').ffill().bfill()
    nan_mask = series.isna()
    stl = STL(series_stl, period=12, robust=True)
    res = stl.fit()
    # Convertir a Series con el índice original
    idx = series_stl.index
    trend    = pd.Series(res.trend,    index=idx)
    seasonal = pd.Series(res.seasonal, index=idx)
    resid    = pd.Series(res.resid,    index=idx)
    # Enmascarar huecos originales en el residual (no contar como extremos meses interpolados)
    anomaly = resid.copy()
    anomaly[nan_mask] = np.nan
    # Eventos extremos (solo sobre datos reales)
    valid_anom = anomaly.dropna()
    if len(valid_anom) < 6:
        eventos_bajos = pd.Series([], dtype='float64')
        eventos_altos = pd.Series([], dtype='float64')
    else:
        p10 = np.nanpercentile(valid_anom, 10)
        p90 = np.nanpercentile(valid_anom, 90)
        eventos_bajos = anomaly[anomaly < p10].dropna()
        eventos_altos = anomaly[anomaly > p90].dropna()
    # Gráfico
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    axes[0].plot(series.index, series.values, label='Serie original', color='#2E86AB', linewidth=1.2)
    if nan_mask.any():
        axes[0].plot(series_stl.index, series_stl.where(nan_mask).values,
                     color='gray', linewidth=1, linestyle='--', label='Interpolado', alpha=0.6)
    axes[0].set_title(f'{var_name} — Serie original', fontweight='bold')
    axes[0].legend(fontsize=8)
    axes[1].plot(trend.index, trend.values, label='Tendencia', color='#E63946', linewidth=1.5)
    axes[1].set_title('Tendencia', fontweight='bold')
    axes[2].plot(seasonal.index, seasonal.values, label='Estacionalidad', color='#06A77D', linewidth=1.2)
    axes[2].axhline(0, color='black', linewidth=0.5, linestyle='--', alpha=0.4)
    axes[2].set_title('Componente estacional', fontweight='bold')
    axes[3].plot(anomaly.index, anomaly.values, label='Anomalía (residual)', color='#A23B72', linewidth=1.2)
    axes[3].axhline(0, color='black', linewidth=0.5, linestyle='--', alpha=0.4)
    if not eventos_bajos.empty:
        axes[3].scatter(eventos_bajos.index, eventos_bajos.values,
                        color='#1565C0', s=40, label=f'Evento bajo (p10, n={len(eventos_bajos)})', zorder=5)
    if not eventos_altos.empty:
        axes[3].scatter(eventos_altos.index, eventos_altos.values,
                        color='#C62828', s=40, label=f'Evento alto (p90, n={len(eventos_altos)})', zorder=5)
    axes[3].set_title('Anomalía y eventos extremos', fontweight='bold')
    axes[3].legend(fontsize=8)
    for ax in axes:
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / f'{var_name}_stl_decomposition.png', dpi=120)
    plt.close()
    # Guardar eventos extremos
    if not eventos_bajos.empty:
        eventos_df = pd.DataFrame({
            'fecha_bajo': eventos_bajos.index,
            'anomalia_bajo': eventos_bajos.values
        })
    else:
        eventos_df = pd.DataFrame({'fecha_bajo': ['Sin eventos'], 'anomalia_bajo': [np.nan]})
    if not eventos_altos.empty:
        eventos_df2 = pd.DataFrame({
            'fecha_alto': eventos_altos.index,
            'anomalia_alto': eventos_altos.values
        })
    else:
        eventos_df2 = pd.DataFrame({'fecha_alto': ['Sin eventos'], 'anomalia_alto': [np.nan]})
    eventos_df.to_csv(output_dir / f'{var_name}_eventos_bajos.csv', index=False)
    eventos_df2.to_csv(output_dir / f'{var_name}_eventos_altos.csv', index=False)

if __name__ == "__main__":
    ds = xr.open_dataset(DATA_FILE)
    time_index = pd.DatetimeIndex(ds['time'].values)
    # Especies
    for var in SPECIES_VARS:
        if var not in ds:
            continue
        series = pd.Series(ds[var].values, index=time_index)
        analyze_stl_and_extremes(series, var, OUTPUT_DIR)
    # Tamaños
    for var in SIZE_VARS:
        if var not in ds:
            continue
        series = pd.Series(ds[var].values, index=time_index)
        analyze_stl_and_extremes(series, var, OUTPUT_DIR)
    print('✓ STL, eventos extremos y gráficos generados en:', OUTPUT_DIR)
