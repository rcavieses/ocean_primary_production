"""
Script para regresión segmentada (piecewise) entre biomasa fitoplanctónica e índices ambientales.
Requiere: numpy, pandas, matplotlib, xarray, pwlf
"""
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pwlf
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DATA_FILE = BASE_DIR / 'data' / 'processed' / 'pft_monthly_statistics.nc'
INDICES = {
    'MEI': BASE_DIR / 'data' / 'raw' / 'mei.exttimeseries.csv',
    'PDO': BASE_DIR / 'data' / 'raw' / 'pdo.timeseries.sstens.csv',
    'NINO34': BASE_DIR / 'data' / 'raw' / 'nino34.long.anom.csv'
}
OUTPUT_DIR = BASE_DIR / 'results' / 'satellite' / 'figures' / 'piecewise_regression'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SPECIES_VARS = [
    'DIATO_mean', 'DINO_mean', 'GREEN_mean', 'HAPTO_mean', 'PROCHLO_mean', 'PROKAR_mean'
]

# Función para cargar índices

def load_index(name, path):
    if name == 'MEI':
        # MEI: espacio separado, año + 12 meses
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
            # Eliminar NaN e Inf
            valid = (~y.isna()) & (~x.isna()) & np.isfinite(y.values) & np.isfinite(x.values)
            x_valid = x[valid]
            y_valid = y[valid]
            if len(x_valid) < 24:
                continue
            try:
                my_pwlf = pwlf.PiecewiseLinFit(x_valid.values, y_valid.values)
                breaks = my_pwlf.fit(2)
                y_hat = my_pwlf.predict(x_valid.values)
                # Gráfico
                plt.figure(figsize=(8,5))
                plt.scatter(x_valid, y_valid, alpha=0.5, label='Datos')
                plt.plot(x_valid, y_hat, color='red', label='Piecewise fit')
                for b in breaks[1:-1]:
                    plt.axvline(b, color='orange', linestyle='--', label='Cambio de segmento')
                plt.xlabel(idx_name)
                plt.ylabel(var)
                plt.title(f'Regresión segmentada: {var} vs {idx_name}')
                plt.legend()
                plt.tight_layout()
                plt.savefig(OUTPUT_DIR / f'{var}_vs_{idx_name}_piecewise.png', dpi=120)
                plt.close()
            except Exception as e:
                print(f"Error en {var} vs {idx_name}: {e}")
    print('✓ Regresión segmentada generada en:', OUTPUT_DIR)
