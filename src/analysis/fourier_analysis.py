"""
Script para análisis de descomposición de frecuencias de Fourier en series temporales de producción primaria fitoplanctónica.
Permite identificar tendencias (baja frecuencia) y ciclos (frecuencias dominantes).

Requiere: numpy, pandas, matplotlib, xarray
"""
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DATA_FILE = BASE_DIR / 'data' / 'processed' / 'pft_monthly_statistics.nc'
OUTPUT_DIR = BASE_DIR / 'results' / 'satellite' / 'figures' / 'fourier_analysis'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SPECIES_VARS = [
    'DIATO_mean', 'DINO_mean', 'GREEN_mean', 'HAPTO_mean', 'PROCHLO_mean', 'PROKAR_mean'
]
SIZE_VARS = [
    'MICRO_mean', 'NANO_mean', 'PICO_mean'
]

# Análisis de Fourier y gráfico
def fourier_decomposition(series, var_name, output_dir):
    series = series.dropna()
    n = len(series)
    t = np.arange(n)
    y = series.values
    # Transformada de Fourier
    yf = np.fft.fft(y - np.mean(y))
    xf = np.fft.fftfreq(n, d=1)  # d=1 mes
    # Potencia (densidad espectral)
    power = (np.abs(yf)**2)[:n//2]
    freq = xf[:n//2]
    # Periodo en meses
    period = 1 / freq
    # Gráfico: espectro de potencia
    plt.figure(figsize=(10,5))
    plt.plot(period, power, color='#2E86AB', lw=2, label='Densidad espectral de potencia')
    # Resaltar picos dominantes
    dom_idx = np.argsort(power)[-3:][::-1]
    plt.scatter(period[dom_idx], power[dom_idx], color='red', zorder=5, label='Ciclos dominantes')
    for i in dom_idx:
        plt.text(period[i], power[i], f'{period[i]:.1f}m', color='red', fontsize=9, ha='center', va='bottom')
    plt.xlabel('Periodo (meses)')
    plt.ylabel('Potencia')
    plt.title(f'Espectro de Potencia de Fourier - {var_name}')
    plt.xscale('log')
    plt.grid(True, which='both', ls='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / f'{var_name}_fourier_spectrum.png', dpi=120)
    plt.close()
    # Guardar frecuencias dominantes
    dom_periods = period[dom_idx]
    dom_powers = power[dom_idx]
    df = pd.DataFrame({'periodo_meses': dom_periods, 'potencia': dom_powers})
    df.to_csv(output_dir / f'{var_name}_frecuencias_dominantes.csv', index=False)

if __name__ == "__main__":
    ds = xr.open_dataset(DATA_FILE)
    time_index = pd.DatetimeIndex(ds['time'].values)
    for var in SPECIES_VARS + SIZE_VARS:
        if var not in ds:
            continue
        series = pd.Series(ds[var].values, index=time_index)
        fourier_decomposition(series, var, OUTPUT_DIR)
    print('✓ Análisis de Fourier y gráficos generados en:', OUTPUT_DIR)
