"""
Script para identificación de eventos extremos en series temporales de producción primaria fitoplanctónica
usando tres enfoques alternativos:
 3. Umbrales móviles (ventana deslizante)
 4. Outliers robustos (IQR)
 5. Detección de cambios de régimen (rupturas)

Requiere: pandas, numpy, matplotlib, ruptures
"""
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ruptures as rpt
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DATA_FILE = BASE_DIR / 'data' / 'processed' / 'pft_monthly_statistics.nc'
OUTPUT_DIR = BASE_DIR / 'results' / 'satellite' / 'figures' / 'extremos_alternativos'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SPECIES_VARS = [
    'DIATO_mean', 'DINO_mean', 'GREEN_mean', 'HAPTO_mean', 'PROCHLO_mean', 'PROKAR_mean'
]
SIZE_VARS = [
    'MICRO_mean', 'NANO_mean', 'PICO_mean'
]

# 3. Umbral móvil (ventana deslizante)
def rolling_extremes(series, window=24, p_low=10, p_high=90):
    lows, highs = [], []
    for i in range(len(series)):
        win = series[max(0, i-window//2):min(len(series), i+window//2)]
        if win.isnull().all():
            continue
        p10 = np.nanpercentile(win, p_low)
        p90 = np.nanpercentile(win, p_high)
        if series.iloc[i] < p10:
            lows.append((series.index[i], series.iloc[i]))
        if series.iloc[i] > p90:
            highs.append((series.index[i], series.iloc[i]))
    return lows, highs

# 4. Outliers robustos (IQR)
def iqr_outliers(series):
    q1 = np.nanpercentile(series, 25)
    q3 = np.nanpercentile(series, 75)
    iqr = q3 - q1
    low_thr = q1 - 1.5 * iqr
    high_thr = q3 + 1.5 * iqr
    lows = [(series.index[i], v) for i, v in enumerate(series) if v < low_thr]
    highs = [(series.index[i], v) for i, v in enumerate(series) if v > high_thr]
    return lows, highs

# 5. Detección de rupturas (changepoints)
def changepoint_events(series, model="l2", pen=10):
    arr = series.dropna().values
    if len(arr) < 24:
        return []
    algo = rpt.Pelt(model=model).fit(arr)
    result = algo.predict(pen=pen)
    # result son índices de cambio, convertir a fechas
    dates = series.dropna().index
    return [dates[i] for i in result[:-1]]  # quitar el último (fin de serie)

# Gráfico resumen
def plot_events(series, var_name, lows, highs, changepoints, output_dir):
    plt.figure(figsize=(12,5))
    plt.plot(series.index, series.values, label='Serie', color='#2E86AB')
    if lows:
        plt.scatter([d for d,_ in lows], [v for _,v in lows], color='blue', label='Bajo', zorder=5)
    if highs:
        plt.scatter([d for d,_ in highs], [v for _,v in highs], color='red', label='Alto', zorder=5)
    for cp in changepoints:
        plt.axvline(cp, color='orange', linestyle='--', alpha=0.7, label='Ruptura')
    plt.title(f'Eventos extremos y rupturas - {var_name}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / f'{var_name}_extremos_alternativos.png', dpi=120)
    plt.close()

if __name__ == "__main__":
    ds = xr.open_dataset(DATA_FILE)
    time_index = pd.DatetimeIndex(ds['time'].values)
    for var in SPECIES_VARS + SIZE_VARS:
        if var not in ds:
            continue
        series = pd.Series(ds[var].values, index=time_index)
        # 3. Umbral móvil
        lows_roll, highs_roll = rolling_extremes(series)
        # 4. IQR
        lows_iqr, highs_iqr = iqr_outliers(series)
        # 5. Rupturas
        changepoints = changepoint_events(series)
        # Guardar resultados
        pd.DataFrame(lows_roll, columns=['fecha','valor']).to_csv(OUTPUT_DIR / f'{var}_bajos_rolling.csv', index=False)
        pd.DataFrame(highs_roll, columns=['fecha','valor']).to_csv(OUTPUT_DIR / f'{var}_altos_rolling.csv', index=False)
        pd.DataFrame(lows_iqr, columns=['fecha','valor']).to_csv(OUTPUT_DIR / f'{var}_bajos_iqr.csv', index=False)
        pd.DataFrame(highs_iqr, columns=['fecha','valor']).to_csv(OUTPUT_DIR / f'{var}_altos_iqr.csv', index=False)
        pd.DataFrame({'fecha':changepoints}).to_csv(OUTPUT_DIR / f'{var}_rupturas.csv', index=False)
        # Gráfico
        plot_events(series, var, lows_roll, highs_roll, changepoints, OUTPUT_DIR)
    print('✓ Resultados alternativos y gráficos generados en:', OUTPUT_DIR)
