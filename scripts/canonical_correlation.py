"""
Script para análisis de correlación canónica entre grupos de fitoplancton e índices ambientales.
Requiere: pandas, numpy, xarray, sklearn
"""
import xarray as xr
import pandas as pd
import numpy as np
from sklearn.cross_decomposition import CCA
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / 'data' / 'pft_monthly_statistics.nc'
INDICES = {
    'MEI': BASE_DIR / 'data' / 'mei.exttimeseries.csv',
    'PDO': BASE_DIR / 'data' / 'pdo.timeseries.sstens.csv',
    'NINO34': BASE_DIR / 'data' / 'nino34.long.anom.csv'
}
OUTPUT_DIR = BASE_DIR / 'data' / 'figures' / 'canonical_correlation'
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
    # Matriz de fitoplancton
    X = []
    for var in SPECIES_VARS:
        if var in ds:
            X.append(pd.Series(ds[var].values, index=time_index))
    X = pd.concat(X, axis=1, keys=SPECIES_VARS)
    # Matriz de índices
    Y = []
    for idx_name, idx_path in INDICES.items():
        idx_series = load_index(idx_name, idx_path)
        Y.append(idx_series)
    Y = pd.concat(Y, axis=1, keys=INDICES.keys())
    # Intersección de fechas
    common_idx = X.index.intersection(Y.index)
    X = X.loc[common_idx].dropna()
    Y = Y.loc[common_idx].dropna()
    X, Y = X.align(Y, join='inner', axis=0)
    if len(X) < 24:
        print('No hay suficientes datos para CCA.')
    else:
        cca = CCA(n_components=2)
        cca.fit(X, Y)
        X_c, Y_c = cca.transform(X, Y)
        # Correlaciones canónicas
        corrs = [np.corrcoef(X_c[:,i], Y_c[:,i])[0,1] for i in range(2)]
        pd.DataFrame({'canonica': [1,2], 'correlacion': corrs}).to_csv(OUTPUT_DIR / 'correlacion_canonica.csv', index=False)
    print('✓ Análisis de correlación canónica generado en:', OUTPUT_DIR)
