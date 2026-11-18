#!/usr/bin/env python3
"""
Granger robusto PFT <- índices climáticos (comentario 4 del manuscrito).

Cambios respecto a src/analysis/granger_causality.py:
  1. Periodo con datos reales de PFT (jul-2002 a dic-2024); sin relleno.
  2. PFT en log10 y desestacionalizados (anomalía respecto a la climatología mensual);
     índices también desestacionalizados.
  3. Pruebas ADF (H0: raíz unitaria) y KPSS (H0: estacionariedad). Si la serie no es
     estacionaria por ambos criterios (ADF p<0.05 y KPSS p>0.05) se diferencia una vez.
  4. Granger (prueba F, ssr_ftest) para desfases 1-6.
       a) Análisis principal: desfase elegido por AIC (VAR, maxlags=6) -> 1 prueba por par;
          corrección Benjamini-Hochberg sobre todos los pares (grupos x índices).
       b) Sensibilidad: las 6 pruebas por par, BH sobre la familia completa.
  5. Sensibilidad para PROCHLO: solo hasta mar-2016 (antes de la discontinuidad detectada).

Uso (en el equipo que tiene los datos, desde la raíz del repositorio):
    python3 manuscript/reanalysis/granger_robusto.py \
        --pft data/processed/pft_monthly_statistics.nc --indices data/raw
Salida: manuscript/reanalysis/salidas/granger_robusto_*.csv y granger_robusto_resumen.md
"""
import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller, grangercausalitytests, kpss

warnings.filterwarnings("ignore")
GROUPS = ["DIATO", "DINO", "GREEN", "HAPTO", "PROKAR", "PROCHLO"]
INDEX_FILES = {"NINO34": "nino34.long.anom.csv", "PDO": "pdo.timeseries.sstens.csv",
               "MEI": "mei.exttimeseries.csv"}
MAXLAG = 6


def load_index(name, path):
    """Mismo formato que src/analysis/granger_causality.py."""
    if name == "MEI":
        rows = []
        for line in open(path):
            p = line.strip().split()
            if not p or not p[0].isdigit() or len(p) < 13:
                continue
            for m, v in enumerate(p[1:13]):
                try:
                    v = float(v)
                except ValueError:
                    continue
                if v > -90:
                    rows.append((pd.Timestamp(int(p[0]), m + 1, 1), v))
        return pd.Series(dict(rows), name=name).sort_index()
    df = pd.read_csv(path, skiprows=1, header=None, names=["Date", name])
    df["Date"] = pd.to_datetime(df["Date"].astype(str).str.strip())
    df[name] = pd.to_numeric(df[name], errors="coerce")
    df = df[df[name] > -90].dropna()
    s = df.set_index("Date")[name]
    s.index = s.index.to_period("M").to_timestamp()
    return s


def deseason(s):
    return s - s.groupby(s.index.month).transform("mean")


def stationarity(s):
    adf_p = adfuller(s.dropna(), autolag="AIC")[1]
    kpss_p = kpss(s.dropna(), regression="c", nlags="auto")[1]
    return adf_p, kpss_p, (adf_p < 0.05) and (kpss_p > 0.05)


def prepare(s):
    """Devuelve la serie estacionaria y un registro de las decisiones."""
    adf_p, kpss_p, ok = stationarity(s)
    rec = {"ADF_p": adf_p, "KPSS_p": kpss_p, "estacionaria": ok, "diferenciada": False}
    if not ok:
        s = s.diff().dropna()
        a2, k2, ok2 = stationarity(s)
        rec.update({"diferenciada": True, "ADF_p_dif": a2, "KPSS_p_dif": k2, "estacionaria_dif": ok2})
    return s, rec


def granger_pair(y, x):
    df = pd.concat([y, x], axis=1, join="inner").dropna()
    df.columns = ["y", "x"]
    try:  # statsmodels < 0.15 acepta `verbose`; >= 0.15 lo eliminó
        res = grangercausalitytests(df[["y", "x"]], maxlag=MAXLAG, verbose=False)
    except TypeError:
        res = grangercausalitytests(df[["y", "x"]], maxlag=MAXLAG)
    p_by_lag = {lag: res[lag][0]["ssr_ftest"][1] for lag in range(1, MAXLAG + 1)}
    sel = VAR(df.values).select_order(MAXLAG)
    lag_aic = max(1, int(sel.aic))
    return p_by_lag, lag_aic, len(df)


def run(pft_path, idx_dir, out_dir, end=None, groups=GROUPS, tag=""):
    ds = xr.open_dataset(pft_path)
    t = pd.DatetimeIndex(ds["time"].values).to_period("M").to_timestamp()
    stat_rows, pair_rows, lag_rows = [], [], []
    idx = {}
    for name, fn in INDEX_FILES.items():
        s = load_index(name, Path(idx_dir) / fn)
        s = deseason(s["2002-07":"2024-12"])
        s, rec = prepare(s)
        idx[name] = s
        stat_rows.append({"serie": name, **rec})
    for g in groups:
        y = pd.Series(ds[f"{g}_mean"].values, index=t).dropna()
        y = y[y > 0]
        if end:
            y = y[:end]
        y = deseason(np.log10(y))
        y, rec = prepare(y)
        stat_rows.append({"serie": g + tag, **rec})
        for name, x in idx.items():
            p_by_lag, lag_aic, n = granger_pair(y, x)
            pair_rows.append({"grupo": g + tag, "indice": name, "n": n, "desfase_AIC": lag_aic,
                              "p": p_by_lag[lag_aic]})
            for lag, p in p_by_lag.items():
                lag_rows.append({"grupo": g + tag, "indice": name, "desfase": lag, "p": p})
    pairs, lags, stat = pd.DataFrame(pair_rows), pd.DataFrame(lag_rows), pd.DataFrame(stat_rows)
    pairs["q_BH"] = multipletests(pairs["p"], method="fdr_bh")[1]
    lags["q_BH"] = multipletests(lags["p"], method="fdr_bh")[1]
    out_dir.mkdir(parents=True, exist_ok=True)
    stat.to_csv(out_dir / f"granger_robusto_estacionariedad{tag}.csv", index=False)
    pairs.to_csv(out_dir / f"granger_robusto_pares{tag}.csv", index=False)
    lags.to_csv(out_dir / f"granger_robusto_todos_los_desfases{tag}.csv", index=False)
    return stat, pairs, lags


def md(df):
    try:
        return df.to_markdown(index=False)
    except ImportError:  # sin tabulate
        return "```\n" + df.to_string(index=False) + "\n```"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pft", default="data/processed/pft_monthly_statistics.nc")
    ap.add_argument("--indices", default="data/raw")
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas")))
    a = ap.parse_args()
    out = Path(a.out)
    stat, pairs, lags = run(a.pft, a.indices, out)
    _, pairs_pre, _ = run(a.pft, a.indices, out, end="2016-03", groups=["PROCHLO"], tag="_hasta2016-03")
    with open(out / "granger_robusto_resumen.md", "w") as f:
        f.write("# Granger robusto (log10, desestacionalizado, ADF/KPSS, BH)\n\n")
        f.write("## Estacionariedad\n\n" + md(stat.round(4)) + "\n\n")
        f.write("## Principal: desfase por AIC, BH sobre pares\n\n"
                + md(pairs.sort_values("q_BH").round(4)) + "\n\n")
        sig = lags[lags.q_BH < 0.05].sort_values("q_BH")
        f.write("## Sensibilidad: todos los desfases 1-6, BH sobre la familia completa "
                f"({len(lags)} pruebas); significativos q<0.05\n\n"
                + (md(sig.round(4)) if len(sig) else "Ninguno.") + "\n\n")
        f.write("## PROCHLO solo hasta mar-2016\n\n" + md(pairs_pre.round(4)) + "\n")
    print((out / "granger_robusto_resumen.md").read_text())


if __name__ == "__main__":
    main()
