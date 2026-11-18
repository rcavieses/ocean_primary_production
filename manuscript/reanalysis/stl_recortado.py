#!/usr/bin/env python3
"""
STL y HMM recortados al periodo con datos (comentario 3 del manuscrito).

El script original (src/analysis/stl_decomposition_extremes.py) aplica
`interpolate(method='time').ffill().bfill()` sobre ene-2000..dic-2024: los 30 meses
iniciales sin PFT (ene-2000..jun-2002) se rellenan con el valor de jul-2002, es decir,
STL se ajusta con un 10 % de la serie constante y artificial. Aquí la serie se recorta
al primer/último mes válido, solo se interpolan huecos INTERNOS y se informa cuántos.

Uso:  python3 manuscript/reanalysis/stl_recortado.py --pft data/processed/pft_monthly_statistics.nc
Salida: manuscript/reanalysis/salidas/stl_huecos.csv, stl_<VAR>.csv, Fig5_diatomeas_STL_HMM.png
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from hmmlearn.hmm import GaussianHMM
from statsmodels.tsa.seasonal import STL

VARS = ["CHL", "DIATO", "DINO", "GREEN", "HAPTO", "PROKAR", "PROCHLO", "MICRO", "NANO", "PICO"]


def stl_trimmed(s):
    s = s.asfreq("MS")
    first, last = s.first_valid_index(), s.last_valid_index()
    core = s[first:last]
    n_int = int(core.isna().sum())
    filled = core.interpolate(method="time")
    res = STL(filled, period=12, robust=True).fit()
    info = {"primer_mes": first.date(), "ultimo_mes": last.date(), "meses_usados": len(core),
            "huecos_internos_interpolados": n_int,
            "meses_excluidos_al_inicio": int(s[:first].shape[0] - 1),
            "meses_excluidos_al_final": int(s[last:].shape[0] - 1)}
    return res, filled, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pft", default="data/processed/pft_monthly_statistics.nc")
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas")))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(a.pft)
    t = pd.DatetimeIndex(ds["time"].values).to_period("M").to_timestamp()
    rows, diato = [], None
    for v in VARS:
        if f"{v}_mean" not in ds:
            continue
        s = pd.Series(ds[f"{v}_mean"].values, index=t)
        res, filled, info = stl_trimmed(s)
        rows.append({"variable": v, **info,
                     "amplitud_estacional_antes_2012": float(np.ptp(res.seasonal[:"2011"].groupby(res.seasonal[:"2011"].index.month).mean())),
                     "amplitud_estacional_desde_2012": float(np.ptp(res.seasonal["2012":].groupby(res.seasonal["2012":].index.month).mean())),
                     "tendencia_inicio": float(res.trend.iloc[:12].mean()),
                     "tendencia_fin": float(res.trend.iloc[-12:].mean())})
        pd.DataFrame({"serie": filled, "tendencia": res.trend, "estacional": res.seasonal,
                      "residuo": res.resid}).to_csv(out / f"stl_{v}.csv")
        if v == "DIATO":
            diato = (filled, res)
    pd.DataFrame(rows).to_csv(out / "stl_huecos.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))

    if diato is not None:  # Figura 5: STL + HMM de diatomeas
        y, res = diato
        X = y.values.reshape(-1, 1)
        hmm = GaussianHMM(2, covariance_type="diag", n_iter=200, random_state=42).fit(X)
        st = hmm.predict(X)
        hi = int(np.argmax(hmm.means_.ravel()))  # estado de alta biomasa
        fig, ax = plt.subplots(3, 1, figsize=(6.6, 5.6), sharex=True,
                               gridspec_kw={"height_ratios": [1.3, 1, 1]})
        ax[0].plot(y.index, y, color="#a5a4a0", lw=0.8, label="Serie mensual")
        ax[0].plot(y.index, res.trend, color="#2a78d6", lw=2, label="Tendencia (STL)")
        ax[0].scatter(y.index[st == hi], y[st == hi], s=9, color="#eb6834", zorder=3, label="Régimen de alta biomasa (HMM)")
        ax[0].set_ylabel("mg m⁻³"); ax[0].legend(fontsize=7, frameon=False, loc="upper right")
        ax[1].plot(y.index, res.seasonal, color="#2a78d6", lw=1.2); ax[1].set_ylabel("Estacional")
        ax[2].plot(y.index, res.resid, color="#2a78d6", lw=0.9); ax[2].axhline(0, color="#52514e", lw=0.6)
        ax[2].set_ylabel("Residuo"); ax[2].set_xlabel("Año")
        for a_, tg in zip(ax, "abc"):
            a_.spines[["top", "right"]].set_visible(False)
            a_.text(-0.12, 1.0, f"({tg})", transform=a_.transAxes, fontweight="bold")
        fig.tight_layout(); fig.savefig(out / "Fig5_diatomeas_STL_HMM.png", dpi=200)


if __name__ == "__main__":
    main()
