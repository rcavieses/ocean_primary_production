"""
Script para detección de cambios de régimen en series temporales de producción primaria fitoplanctónica
usando Modelos Ocultos de Markov (HMM, Hidden Markov Models).

Requiere: hmmlearn, pandas, numpy, matplotlib, xarray
"""
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from hmmlearn.hmm import GaussianHMM
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DATA_FILE = BASE_DIR / 'data' / 'processed' / 'pft_monthly_statistics.nc'
OUTPUT_DIR = BASE_DIR / 'results' / 'satellite' / 'figures' / 'hmm_regimen_change'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SPECIES_VARS = [
    'DIATO_mean', 'DINO_mean', 'GREEN_mean', 'HAPTO_mean', 'PROCHLO_mean', 'PROKAR_mean'
]
SIZE_VARS = [
    'MICRO_mean', 'NANO_mean', 'PICO_mean'
]

# Función para ajuste y predicción de estados HMM
def hmm_regime_detection(series, n_states=2, n_iter=200):
    # Elimina NaN
    series = series.dropna()
    if len(series) < 24:
        return None, None
    X = series.values.reshape(-1, 1)
    model = GaussianHMM(n_components=n_states, covariance_type="diag", n_iter=n_iter, random_state=42)
    model.fit(X)
    hidden_states = model.predict(X)
    return hidden_states, model

# Gráfico de estados/regímenes
def plot_hmm_states(series, hidden_states, var_name, output_dir):
    plt.figure(figsize=(12,5))
    plt.plot(series.index, series.values, label='Serie', color='#2E86AB')
    for state in np.unique(hidden_states):
        mask = hidden_states == state
        plt.scatter(series.index[mask], series.values[mask], label=f'Regimen {state+1}', s=30)
    plt.title(f'HMM: Cambios de régimen - {var_name}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / f'{var_name}_hmm_regimen.png', dpi=120)
    plt.close()

if __name__ == "__main__":
    ds = xr.open_dataset(DATA_FILE)
    time_index = pd.DatetimeIndex(ds['time'].values)
    for var in SPECIES_VARS + SIZE_VARS:
        if var not in ds:
            continue
        series = pd.Series(ds[var].values, index=time_index)
        hidden_states, model = hmm_regime_detection(series)
        if hidden_states is None:
            continue
        # Guardar estados
        df_states = pd.DataFrame({
            'fecha': series.dropna().index,
            'valor': series.dropna().values,
            'estado': hidden_states
        })
        df_states.to_csv(OUTPUT_DIR / f'{var}_hmm_states.csv', index=False)
        plot_hmm_states(series.dropna(), hidden_states, var, OUTPUT_DIR)
    print('✓ Resultados HMM y gráficos generados en:', OUTPUT_DIR)
