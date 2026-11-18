#!/usr/bin/env python3
"""
Sensibilidad de las tendencias de clorofitas (GREEN) al escalón de 2016.

Tendencia lineal del reporte original (results/satellite/tables/reporte_analisis_numerico.json,
`linear_trend`): MCO de GREEN_mean (mg m-3) contra el índice del mes (0..n-1) sobre los meses
válidos. Se reproduce y se repite:
  T0. Original: jul-2002..dic-2024, y ~ t
  T1. Con indicadora del escalón: y ~ t + D, D = 1{t >= fecha del escalón}
  T2. Solo antes del escalón: jul-2002..mes anterior, y ~ t
  (T3. Solo después del escalón, informativo)
Para cada una: pendiente por año y por década (mg m-3 y % de la media del periodo), IC 95 % y p
con errores HAC de Newey-West (12 desfases, por autocorrelación), p de MCO clásico, pendiente de
Theil-Sen y Mann-Kendall (p sin corregir por autocorrelación). Además la tendencia STL (como
stl_recortado.py) al inicio y al final de cada ventana.

Uso:  python3 manuscript/reanalysis/tendencias_escalon_green.py --pft data/processed/pft_monthly_statistics.nc
Salida: manuscript/reanalysis/salidas/granger_revision/tendencias_GREEN_escalon.csv / .md
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import xarray as xr
from scipy import stats
from statsmodels.tsa.seasonal import STL

sys.path.insert(0, str(Path(__file__).parent))
import escalon  # noqa: E402

START, END = "2002-07", "2024-12"


def mk_p(y):
    """Mann-Kendall (sin empates relevantes), p bilateral normal."""
    y = np.asarray(y); n = len(y)
    s = sum(np.sign(y[j] - y[i]) for i in range(n - 1) for j in range(i + 1, n))
    var = n * (n - 1) * (2 * n + 5) / 18
    z = (s - np.sign(s)) / np.sqrt(var) if s != 0 else 0.0
    return float(2 * stats.norm.sf(abs(z)))


def fit(y, label, D=None):
    t = np.arange(len(y), dtype=float)
    X = pd.DataFrame({"const": 1.0, "t": t}, index=y.index)
    if D is not None:
        X["D"] = D.values
    ols = sm.OLS(y.values, X.values).fit()
    hac = sm.OLS(y.values, X.values).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
    b, se = hac.params[1], hac.bse[1]
    ts = stats.theilslopes(y.values if D is None else y.values - ols.params[2] * D.values, t)
    stl = STL(y, period=12, robust=True).fit().trend
    m = y.mean()
    row = {"modelo": label, "periodo": f"{y.index[0]:%Y-%m}..{y.index[-1]:%Y-%m}", "n_meses": len(y),
           "pendiente_mg_m3_por_anio": b * 12, "IC95_inf_por_anio": (b - 1.96 * se) * 12,
           "IC95_sup_por_anio": (b + 1.96 * se) * 12, "p_HAC_NW12": float(hac.pvalues[1]),
           "p_MCO_clasico": float(ols.pvalues[1]), "pct_media_por_decada": 100 * b * 120 / m,
           "TheilSen_por_anio": ts.slope * 12, "MannKendall_p": mk_p(y.values if D is None else y.values - ols.params[2] * D.values),
           "intercepto": float(ols.params[0]), "media_periodo": float(m),
           "STL_tendencia_inicio": float(stl.iloc[:12].mean()), "STL_tendencia_fin": float(stl.iloc[-12:].mean())}
    if D is not None:
        row.update({"escalon_mg_m3": float(hac.params[2]), "escalon_p_HAC": float(hac.pvalues[2])})
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pft", default="data/processed/pft_monthly_statistics.nc")
    ap.add_argument("--json-original", default=None,
                    help="reporte_analisis_numerico.json para comprobar que T0 reproduce la tendencia original")
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas") / "granger_revision"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(a.pft)
    t = pd.DatetimeIndex(ds["time"].values).to_period("M").to_timestamp()
    y = pd.Series(ds["GREEN_mean"].values, index=t)[START:END].dropna()
    info = escalon.detect(np.log10(y))
    step = pd.Timestamp(info["escalon_fecha"])
    D = pd.Series((y.index >= step).astype(float), index=y.index)
    rows = [fit(y, "T0 original (y ~ t)"),
            fit(y, "T1 con indicadora del escalón (y ~ t + D)", D),
            fit(y[:step - pd.DateOffset(months=1)], "T2 solo antes del escalón (y ~ t)"),
            fit(y[step:], "T3 solo después del escalón (y ~ t), informativo")]
    df = pd.DataFrame(rows)
    chk = ""
    if a.json_original:
        lt = json.load(open(a.json_original))["variables"]["GREEN"]["linear_trend"]
        chk = (f"Comprobación T0 vs JSON original: pendiente/año {df.loc[0, 'pendiente_mg_m3_por_anio']:.6f} vs "
               f"{lt['slope_per_year']:.6f}; intercepto {df.loc[0, 'intercepto']:.6f} vs {lt['intercept']:.6f}")
    df.to_csv(out / "tendencias_GREEN_escalon.csv", index=False)
    with open(out / "tendencias_GREEN_escalon.md", "w") as f:
        f.write(f"# Tendencias de GREEN y escalón de {step:%Y-%m}\n\nEscalón (log10): `{json.dumps(info)}`\n\n{chk}\n\n")
        try:
            f.write(df.round(5).to_markdown(index=False) + "\n")
        except ImportError:
            f.write(df.round(5).to_string(index=False) + "\n")
    print((out / "tendencias_GREEN_escalon.md").read_text())


if __name__ == "__main__":
    main()
