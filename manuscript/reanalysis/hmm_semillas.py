#!/usr/bin/env python3
"""
B1. Robustez del HMM gaussiano de 2 estados de diatomeas (Fig. 5) frente a la semilla.

Serie: DIATO_mean de pft_monthly_statistics.nc, recortada jul-2002..dic-2024 e interpolación solo
de huecos internos (igual que stl_recortado.py). Modelo: hmmlearn GaussianHMM(2, "diag").
  - Configuración de la Fig. 5 actual (stl_recortado.py): random_state=42, n_iter=200, tol por
    defecto (0.01).
  - 20 semillas (0..19) con n_iter=10000 y tol=1e-6, en dos configuraciones:
      A "por defecto": parámetros de hmmlearn por defecto (covars_prior=0.01, covars_weight=1),
        como en stl_recortado.py y en el análisis original;
      B "máxima verosimilitud": covars_prior=0 (sin prior sobre las varianzas).
    Con prior, el paso M maximiza la posterior y la log-verosimilitud monitorizada puede bajar
    (origen del aviso "Model is not converging"). hmmlearn marca converged=True también cuando
    el último cambio es negativo; por eso se informa además una convergencia estricta:
    0 <= delta final < tol y iteraciones < n_iter.
Por ajuste: convergencia (hmmlearn y estricta), delta final e iteraciones, log-verosimilitud, medias de los
estados (mg m-3), % de meses en el régimen alto en jul-2002..2011, 2012..2015 y 2016..2024 y meses en
el régimen alto entre ene-2014 y dic-2017. También se resumen los estados guardados por el
análisis original (results/satellite/figures/hmm_regimen_change/DIATO_mean_hmm_states.csv) si se
indica con --original.
Mejor solución = mayor log-verosimilitud entre los ajustes con convergencia estricta (A y B). Si su secuencia de
estados difiere de la de la Fig. 5 actual, se regenera la figura con ella (mismo código de
dibujo que stl_recortado.py) y se guarda la anterior.

Uso:  python3 manuscript/reanalysis/hmm_semillas.py --pft data/processed/pft_monthly_statistics.nc \
          --original results/satellite/figures/hmm_regimen_change/DIATO_mean_hmm_states.csv
Salida: manuscript/reanalysis/salidas/hmm_semillas/
"""
import argparse
import shutil
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from hmmlearn.hmm import GaussianHMM
from statsmodels.tsa.seasonal import STL

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from stl_recortado import stl_trimmed  # noqa: E402

PERIODS = {"jul2002-2011": ("2002-07", "2011-12"), "2012-2015": ("2012-01", "2015-12"), "2016-2024": ("2016-01", "2024-12")}
MANUSCRITO = {"media_alta": 0.111, "media_baja": 0.034, "pct_alto_jul2002-2011": 54, "pct_alto_2012-2015": 19,
              "pct_alto_2016-2024": 14, "meses_alto_2014-2017": 0}


def summarize(states, means, y, label, extra=None):
    hi = int(np.argmax(means))
    st = pd.Series(states == hi, index=y.index)
    rec = {"ajuste": label, **(extra or {}), "media_alta": float(np.max(means)), "media_baja": float(np.min(means))}
    for k, (a, b) in PERIODS.items():
        rec[f"pct_alto_{k}"] = 100 * float(st[a:b].mean())
    w = st["2014-01":"2017-12"]
    rec["meses_alto_2014-2017"] = int(w.sum())
    rec["meses_alto_2014-2017_lista"] = ", ".join(f"{d:%Y-%m}" for d in w[w].index)
    return rec, st


def fig5(y, res, st, path):
    """Mismo dibujo que stl_recortado.py (Figura 5)."""
    fig, ax = plt.subplots(3, 1, figsize=(6.6, 5.6), sharex=True, gridspec_kw={"height_ratios": [1.3, 1, 1]})
    ax[0].plot(y.index, y, color="#a5a4a0", lw=0.8, label="Serie mensual")
    ax[0].plot(y.index, res.trend, color="#2a78d6", lw=2, label="Tendencia (STL)")
    ax[0].scatter(y.index[st.values], y[st.values], s=9, color="#eb6834", zorder=3, label="Régimen de alta biomasa (HMM)")
    ax[0].set_ylabel("mg m⁻³"); ax[0].legend(fontsize=7, frameon=False, loc="upper right")
    ax[1].plot(y.index, res.seasonal, color="#2a78d6", lw=1.2); ax[1].set_ylabel("Estacional")
    ax[2].plot(y.index, res.resid, color="#2a78d6", lw=0.9); ax[2].axhline(0, color="#52514e", lw=0.6)
    ax[2].set_ylabel("Residuo"); ax[2].set_xlabel("Año")
    for a_, tg in zip(ax, "abc"):
        a_.spines[["top", "right"]].set_visible(False)
        a_.text(-0.12, 1.0, f"({tg})", transform=a_.transAxes, fontweight="bold")
    fig.tight_layout(); fig.savefig(path, dpi=200)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pft", default="data/processed/pft_monthly_statistics.nc")
    ap.add_argument("--original", default=None)
    ap.add_argument("--fig-actual", default=str(HERE / "salidas" / "Fig5_diatomeas_STL_HMM.png"))
    ap.add_argument("--n-iter", type=int, default=10000)
    ap.add_argument("--tol", type=float, default=1e-6)
    ap.add_argument("--configuraciones", default="AB", help="A, B o AB (B = máxima verosimilitud, covars_prior=0)")
    ap.add_argument("--forzar-figura", action="store_true", help="dibuja la Fig. 5 con la mejor solución aunque coincida con la actual")
    ap.add_argument("--out", default=str(HERE / "salidas" / "hmm_semillas"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(a.pft)
    t = pd.DatetimeIndex(ds["time"].values).to_period("M").to_timestamp()
    res, y, info = stl_trimmed(pd.Series(ds["DIATO_mean"].values, index=t))
    X = y.values.reshape(-1, 1)

    rows, seqs = [], {}
    def info_fit(m, seed, n_iter, tol, conf):
        h = list(m.monitor_.history); d = h[-1] - h[-2] if len(h) > 1 else np.nan
        return {"configuracion": conf, "semilla": seed, "n_iter_max": n_iter, "tol": tol,
                "covars_prior": m.covars_prior, "convergio_hmmlearn": bool(m.monitor_.converged),
                "delta_final": float(d), "convergio_estricto": bool(0 <= d < tol and m.monitor_.iter < n_iter),
                "iteraciones": int(m.monitor_.iter), "loglik": float(m.score(X)),
                "var_alta": float(m.covars_.ravel()[int(np.argmax(m.means_))]),
                "var_baja": float(m.covars_.ravel()[int(np.argmin(m.means_))])}

    m0 = GaussianHMM(2, covariance_type="diag", n_iter=200, random_state=42).fit(X)
    r0, s0 = summarize(m0.predict(X), m0.means_.ravel(), y, "Fig. 5 actual (seed 42, n_iter=200, tol=0.01)",
                       info_fit(m0, 42, 200, m0.tol, "Fig. 5 actual"))
    rows.append(r0); seqs["actual"] = s0
    for conf, kw in [c for c in [("A por defecto", {}), ("B máxima verosimilitud", {"covars_prior": 0.0})] if c[0][0] in a.configuraciones]:
        for seed in range(20):
            m = GaussianHMM(2, covariance_type="diag", n_iter=a.n_iter, tol=a.tol, random_state=seed, **kw).fit(X)
            r, s = summarize(m.predict(X), m.means_.ravel(), y, f"{conf[0]} semilla {seed}",
                             info_fit(m, seed, a.n_iter, a.tol, conf))
            rows.append(r); seqs[(conf[0], seed)] = s
    if a.original:
        o = pd.read_csv(a.original, parse_dates=["fecha"]).set_index("fecha")
        means = o.groupby("estado")["valor"].mean()
        # estado alto = el de mayor media empírica (el CSV no guarda las medias del modelo)
        so = o["estado"].values
        ro, _ = summarize(np.where(so == means.idxmax(), 1, 0), np.array([0.0, 1.0]), o["valor"], "análisis original (CSV de estados)")
        ro.update({"media_alta": float(means.max()), "media_baja": float(means.min()),
                   "nota": "medias = promedio de la serie en cada estado (el CSV no guarda las medias del modelo)"})
        rows.append(ro)
    rows.append({"ajuste": "valores del manuscrito", **MANUSCRITO})
    T = pd.DataFrame(rows)
    is_seed = T.ajuste.str.contains(" semilla ")
    conv = T[is_seed & T.convergio_estricto.fillna(False).astype(bool)]
    bi = conv.loglik.idxmax() if len(conv) else None
    best = (T.loc[bi, "ajuste"][0], int(T.loc[bi, "semilla"])) if bi is not None else None
    T["mejor"] = T.index == bi
    # soluciones distintas (por secuencia de estados alto/bajo), numeradas por configuración
    keys = {k: "".join("1" if v else "0" for v in s.values) for k, s in seqs.items()}
    sol = {kk: i for i, kk in enumerate(dict.fromkeys(keys[k] for k in seqs if k != "actual"))}
    T["solucion_id"] = [sol.get(keys.get((aj[0], int(s))), np.nan) if str(aj).find(" semilla ") > 0 else
                        (sol.get(keys["actual"], np.nan) if aj.startswith("Fig. 5") else np.nan)
                        for s, aj in zip(T.semilla.fillna(-1), T.ajuste)]
    n_sol = {c: len(set(keys[(c, k)] for k in range(20))) for c in a.configuraciones}
    T.to_csv(out / "hmm_semillas.csv", index=False)
    differs = best is not None and keys[best] != keys["actual"]
    n_diff = int(sum(a_ != b_ for a_, b_ in zip(keys[best], keys["actual"]))) if best is not None else None
    note = ""
    if differs or (a.forzar_figura and best is not None):
        fa = Path(a.fig_actual)
        if fa.exists():
            shutil.copy(fa, out / "Fig5_diatomeas_STL_HMM_version_anterior.png")
        fig5(y, res, seqs[best], out / "Fig5_diatomeas_STL_HMM.png")
        note = (f"La mejor solución ({best}) difiere de la Fig. 5 actual en {n_diff} meses: se regeneró la "
                "figura y se guardó la anterior.")
    else:
        note = "La mejor solución coincide mes a mes con la de la Fig. 5 actual: no se regeneró la figura."
    pd.DataFrame({"fecha": y.index, "valor": y.values, "alto_fig5_actual": seqs["actual"].values.astype(int),
                  **({"alto_mejor": seqs[best].values.astype(int)} if best is not None else {})}).to_csv(out / "estados.csv", index=False)
    cols = ["ajuste", "convergio_hmmlearn", "convergio_estricto", "delta_final", "iteraciones", "loglik", "media_alta", "media_baja", "pct_alto_jul2002-2011",
            "pct_alto_2012-2015", "pct_alto_2016-2024", "meses_alto_2014-2017", "meses_alto_2014-2017_lista", "solucion_id", "mejor"]
    with open(out / "resumen.md", "w") as f:
        f.write(f"# HMM de diatomeas: 20 semillas (n_iter={a.n_iter}, tol={a.tol})\n\nSerie: {info}\n\n")
        try:
            f.write(T[cols].round(4).to_markdown(index=False))
        except ImportError:
            f.write(T[cols].round(4).to_string(index=False))
        f.write(f"\n\nSoluciones distintas entre las 20 semillas: {n_sol}. "
                f"Ajustes con convergencia estricta: A = {int(conv.configuracion.eq('A por defecto').sum())}, "
                f"B = {int(conv.configuracion.eq('B máxima verosimilitud').sum())}. Mejor ajuste: {best}. {note}\n")
    print((out / "resumen.md").read_text())


if __name__ == "__main__":
    main()
