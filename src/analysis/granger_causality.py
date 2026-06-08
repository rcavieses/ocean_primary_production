"""
Script para análisis de causalidad de Granger entre biomasa fitoplanctónica e índices ambientales.
Requiere: pandas, numpy, xarray, statsmodels
"""
import xarray as xr
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import grangercausalitytests
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DATA_FILE = BASE_DIR / 'data' / 'processed' / 'pft_monthly_statistics.nc'
INDICES = {
    'MEI': BASE_DIR / 'data' / 'raw' / 'mei.exttimeseries.csv',
    'PDO': BASE_DIR / 'data' / 'raw' / 'pdo.timeseries.sstens.csv',
    'NINO34': BASE_DIR / 'data' / 'raw' / 'nino34.long.anom.csv'
}
OUTPUT_DIR = BASE_DIR / 'results' / 'satellite' / 'figures' / 'granger_causality'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SPECIES_VARS = [
    'DIATO_mean', 'DINO_mean', 'GREEN_mean', 'HAPTO_mean', 'PROCHLO_mean', 'PROKAR_mean'
]

# Función para cargar índices

def load_index(name, path):
    if name == 'MEI':
        chunks = []
        with open(path, 'r') as f:
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
    else:
        df = pd.read_csv(path, skiprows=1, header=None, names=['Date', name])
        df['Date'] = pd.to_datetime(df['Date'].str.strip())
        df[name] = pd.to_numeric(df[name], errors='coerce')
        df = df[df[name] > -90].dropna()
        return df.set_index('Date')[name]

if __name__ == "__main__":
    ds = xr.open_dataset(DATA_FILE)
    time_index = pd.DatetimeIndex(ds['time'].values)
    for idx_name, idx_path in INDICES.items():
        idx_series = load_index(idx_name, idx_path)
        for var in SPECIES_VARS:
            if var not in ds:
                continue
            y = pd.Series(ds[var].values, index=time_index)
            # Alinear fechas
            common_idx = y.index.intersection(idx_series.index)
            y = y[common_idx]
            x = idx_series[common_idx]
            if len(x.dropna()) < 24:
                continue
            # DataFrame para Granger
            df = pd.DataFrame({var: y, idx_name: x}).dropna()
            # Prueba de causalidad de Granger (lags 1 a 6)
            result = grangercausalitytests(df[[var, idx_name]], maxlag=6, verbose=False)
            # Guardar p-valores
            pvals = {f'lag_{lag}': result[lag][0]['ssr_ftest'][1] for lag in range(1,7)}
            pd.DataFrame([pvals]).to_csv(OUTPUT_DIR / f'{var}_causality_{idx_name}.csv', index=False)
    print('✓ Análisis de causalidad de Granger generado en:', OUTPUT_DIR)
