"""
Script para análisis de eventos extremos conjuntos entre biomasa fitoplanctónica e índices ambientales.
Requiere: pandas, numpy, xarray
"""
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DATA_FILE = BASE_DIR / 'data' / 'processed' / 'pft_monthly_statistics.nc'
INDICES = {
    'MEI': BASE_DIR / 'data' / 'raw' / 'mei.exttimeseries.csv',
    'PDO': BASE_DIR / 'data' / 'raw' / 'pdo.timeseries.sstens.csv',
    'NINO34': BASE_DIR / 'data' / 'raw' / 'nino34.long.anom.csv'
}
OUTPUT_DIR = BASE_DIR / 'results' / 'satellite' / 'figures' / 'joint_extremes'
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
            # Definir extremos (percentil 10 y 90)
            y_low, y_high = np.nanpercentile(y, 10), np.nanpercentile(y, 90)
            x_low, x_high = np.nanpercentile(x, 10), np.nanpercentile(x, 90)
            # Eventos conjuntos
            joint_high = ((y > y_high) & (x > x_high))
            joint_low = ((y < y_low) & (x < x_low))
            df = pd.DataFrame({
                'fecha': y.index,
                'biomasa': y.values,
                'indice': x.values,
                'joint_high': joint_high.values,
                'joint_low': joint_low.values
            })
            df[df['joint_high'] | df['joint_low']].to_csv(OUTPUT_DIR / f'{var}_joint_extremes_{idx_name}.csv', index=False)
    print('✓ Análisis de eventos extremos conjuntos generado en:', OUTPUT_DIR)
