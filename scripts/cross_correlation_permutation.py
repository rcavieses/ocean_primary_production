"""
Script para análisis de correlación cruzada entre anomalías de biomasa fitoplanctónica y
índices climáticos, considerando desfases de 0 a 6 meses y pruebas de permutación.

Referencias:
- Chatfield, C. (2003). The Analysis of Time Series: An Introduction.

Requiere archivos CSV con series temporales de anomalías de biomasa y de índices climáticos.
"""

import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import pearsonr
from pathlib import Path

# Parámetros
LAGS = range(0, 7)  # 0 a 6 meses
N_PERMUTATIONS = 1000
ALPHA = 0.05

# Variables de especies y tamaños
SPECIES_VARS = [
    'DIATO_mean', 'DINO_mean', 'GREEN_mean', 'HAPTO_mean', 'PROCHLO_mean', 'PROKAR_mean'
]
SIZE_VARS = [
    'MICRO_mean', 'NANO_mean', 'PICO_mean'
]

CLIMATE_INDICES = {
    'MEI': {
        'file': 'data/mei.exttimeseries.csv',
        'loader': 'mei'
    },
    'PDO': {
        'file': 'data/pdo.timeseries.sstens.csv',
        'loader': 'pdo'
    },
    'NINO34': {
        'file': 'data/nino34.long.anom.csv',
        'loader': 'nino'
    }
}

# Funciones para cargar índices climáticos
def load_nino34(filepath):
    df = pd.read_csv(filepath, skiprows=1, header=None, names=['Date', 'NINO34'])
    df['Date'] = pd.to_datetime(df['Date'].str.strip())
    df['NINO34'] = pd.to_numeric(df['NINO34'], errors='coerce')
    df = df[df['NINO34'] > -90].dropna()
    return df.set_index('Date')['NINO34']

def load_pdo(filepath):
    df = pd.read_csv(filepath, skiprows=1, header=None, usecols=[0, 1], names=['Date', 'PDO'])
    df['Date'] = pd.to_datetime(df['Date'])
    df['PDO'] = pd.to_numeric(df['PDO'], errors='coerce')
    return df.set_index('Date')['PDO']

def load_mei(filepath):
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

def cross_correlation_permutation(x, y, lags=LAGS, n_permutations=N_PERMUTATIONS, alpha=ALPHA, random_state=None):
    results = []
    rng = np.random.default_rng(random_state)
    x = np.asarray(x)
    y = np.asarray(y)
    for lag in lags:
        if lag > 0:
            x_lag = x[:-lag]
            y_lag = y[lag:]
        else:
            x_lag = x
            y_lag = y
        mask = ~np.isnan(x_lag) & ~np.isnan(y_lag)
        x_valid = x_lag[mask]
        y_valid = y_lag[mask]
        if len(x_valid) < 3:
            results.append({'lag': lag, 'r': np.nan, 'p_perm': np.nan, 'significant': False})
            continue
        r_obs, _ = pearsonr(x_valid, y_valid)
        perm_stats = []
        for _ in range(n_permutations):
            y_perm = rng.permutation(y_valid)
            r_perm, _ = pearsonr(x_valid, y_perm)
            perm_stats.append(r_perm)
        perm_stats = np.array(perm_stats)
        p_perm = np.mean(np.abs(perm_stats) >= np.abs(r_obs))
        significant = p_perm < alpha
        results.append({'lag': lag, 'r': r_obs, 'p_perm': p_perm, 'significant': significant})
    return pd.DataFrame(results)

def main():
    base_dir = Path(__file__).parent.parent
    stats_file = base_dir / 'data' / 'pft_monthly_statistics.nc'
    # Cargar datos de biomasa
    ds = xr.open_dataset(stats_file)
    time_index = pd.DatetimeIndex(ds['time'].values)

    # Cargar índices climáticos
    index_loaders = {
        'MEI': load_mei,
        'PDO': load_pdo,
        'NINO34': load_nino34
    }
    climate_indices = {}
    for idx, meta in CLIMATE_INDICES.items():
        loader = index_loaders[idx]
        series = loader(base_dir / meta['file'])
        # Recortar a rango de datos
        series = series[series.index.isin(time_index)]
        climate_indices[idx] = series

    # Análisis para especies
    for idx_name, idx_series in climate_indices.items():
        for var in SPECIES_VARS:
            if var not in ds:
                continue
            y = ds[var].values
            # Convertir a pandas Series para alinear fechas
            y_series = pd.Series(y, index=time_index)
            # Alinear fechas
            common_idx = y_series.index.intersection(idx_series.index)
            y_aligned = y_series[common_idx].values
            idx_aligned = idx_series[common_idx].values
            result = cross_correlation_permutation(y_aligned, idx_aligned)
            outname = f'crosscorr_{var}_vs_{idx_name}.csv'
            result.to_csv(base_dir / 'data' / outname, index=False)
            print(f'Guardado: {outname}')

    # Análisis para tamaños
    for idx_name, idx_series in climate_indices.items():
        for var in SIZE_VARS:
            if var not in ds:
                continue
            y = ds[var].values
            y_series = pd.Series(y, index=time_index)
            common_idx = y_series.index.intersection(idx_series.index)
            y_aligned = y_series[common_idx].values
            idx_aligned = idx_series[common_idx].values
            result = cross_correlation_permutation(y_aligned, idx_aligned)
            outname = f'crosscorr_{var}_vs_{idx_name}.csv'
            result.to_csv(base_dir / 'data' / outname, index=False)
            print(f'Guardado: {outname}')

if __name__ == "__main__":
    main()
