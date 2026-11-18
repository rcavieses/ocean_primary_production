#!/usr/bin/env python3
"""
Granger revisado: familias separadas, sensibilidad al escalón de clorofitas y tabla suplementaria.

Misma preparación que granger_robusto.py (log10, desestacionalizado, ADF/KPSS -> diferenciar
una vez si no es estacionaria, Granger F ssr, desfase por AIC de un VAR con maxlags=6), pero:

  A. PRINCIPAL: solo los 5 grupos de la partición sin doble conteo
     (DIATO, DINO, GREEN, HAPTO, PROKAR) x 3 índices = 15 pares, jul-2002..dic-2024.
     Benjamini-Hochberg (BH) sobre esos 15 pares. Sensibilidad: 6 desfases x 15 = 90 pruebas, BH.
  B. PROCHLO SOLO HASTA MAR-2016 (antes de la discontinuidad): 3 pares con su propia BH.
     Los índices se desestacionalizan y se prueban (ADF/KPSS) en la misma ventana.
     B2 (variante): índices preparados en 2002-2024, como hace granger_robusto.py.
  C. SENSIBILIDAD AL ESCALÓN DE GREEN (detectado con escalon.py sobre log10 GREEN):
     C1. Serie completa con una variable indicadora D_t = 1{t >= fecha del escalón} como
         regresor exógeno en los modelos restringido y no restringido (y en el VAR que elige
         el desfase). La estacionariedad se evalúa sobre la serie sin el salto; si se
         diferencia, D se diferencia también (queda un pulso).
     C2. Solo jul-2002 .. mes anterior al escalón.
     Cada variante: BH sobre sus 3 pares, y q recalculada dentro de la familia de 15
     sustituyendo las 3 filas de GREEN.

Uso:  python3 manuscript/reanalysis/granger_revision.py --pft data/processed/pft_monthly_statistics.nc --indices data/raw
Salida (manuscript/reanalysis/salidas/granger_revision/):
  tabla_suplementaria_granger.csv / .md   (p, q, desfase, ADF/KPSS de cada par y familia)
  granger_todos_los_desfases.csv, escalon_GREEN.json, resumen.md, validacion.csv
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import xarray as xr
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.api import VAR

sys.path.insert(0, str(Path(__file__).parent))
import escalon  # noqa: E402
import granger_robusto as gr  # noqa: E402  (load_index, deseason, stationarity, prepare)

warnings.filterwarnings("ignore")
G5 = ["DIATO", "DINO", "GREEN", "HAPTO", "PROKAR"]
START, END = "2002-07", "2024-12"
PROCHLO_END = "2016-03"
MAXLAG = gr.MAXLAG


def load_pft(path, var):
    ds = xr.open_dataset(path)
    t = pd.DatetimeIndex(ds["time"].values).to_period("M").to_timestamp()
    y = pd.Series(ds[f"{var}_mean"].values, index=t).dropna()
    return y[y > 0]


def prep_indices(idx_dir, start, end):
    out, recs = {}, {}
    for name, fn in gr.INDEX_FILES.items():
        s = gr.deseason(gr.load_index(name, Path(idx_dir) / fn)[start:end])
        s, rec = gr.prepare(s)
        out[name], recs[name] = s, rec
    return out, recs


def prep_bio(y_raw, start, end, step_date=None):
    """log10 + desestacionalizar + ADF/KPSS (+ diferenciar). Devuelve (y, D, registro)."""
    y = gr.deseason(np.log10(y_raw[start:end]))
    if step_date is None:
        y, rec = gr.prepare(y)
        return y, None, rec
    D = pd.Series((y.index >= pd.Timestamp(step_date)).astype(float), index=y.index, name="D")
    b = sm.OLS(y, sm.add_constant(D)).fit().params["D"]
    adf_p, kpss_p, ok = gr.stationarity(y - b * D)
    rec = {"ADF_p": adf_p, "KPSS_p": kpss_p, "estacionaria": ok, "diferenciada": False,
           "nota": f"ADF/KPSS sobre la serie sin el escalón (delta={b:.4f} en log10)"}
    if not ok:
        y, D = y.diff().dropna(), D.diff().dropna()
        a2, k2, ok2 = gr.stationarity(y - sm.OLS(y, sm.add_constant(D)).fit().params["D"] * D)
        rec.update({"diferenciada": True, "ADF_p_dif": a2, "KPSS_p_dif": k2, "estacionaria_dif": ok2})
    return y, D, rec


def granger_F(d, p, with_D):
    """F de Granger (x -> y) con desfase p; d tiene columnas y, x[, D]."""
    Y = d["y"].iloc[p:]
    ly = pd.concat({f"y{l}": d["y"].shift(l) for l in range(1, p + 1)}, axis=1).iloc[p:]
    lx = pd.concat({f"x{l}": d["x"].shift(l) for l in range(1, p + 1)}, axis=1).iloc[p:]
    Xr = pd.concat([pd.Series(1.0, index=Y.index, name="const"), ly]
                   + ([d["D"].iloc[p:]] if with_D else []), axis=1)
    Xu = pd.concat([Xr, lx], axis=1)
    r, u = sm.OLS(Y, Xr).fit(), sm.OLS(Y, Xu).fit()
    F = ((r.ssr - u.ssr) / p) / (u.ssr / u.df_resid)
    return float(F), float(stats.f.sf(F, p, u.df_resid)), int(u.df_resid)


def pair(y, x, D=None):
    cols = [y.rename("y"), x.rename("x")] + ([D.rename("D")] if D is not None else [])
    d = pd.concat(cols, axis=1, join="inner").dropna()
    if D is not None and d["D"].std() == 0:
        D = None; d = d.drop(columns="D")
    exog = d[["D"]].values if D is not None else None
    sel = VAR(d[["y", "x"]].values, exog=exog).select_order(MAXLAG)
    lag = max(1, int(sel.aic))
    res = {l: granger_F(d, l, D is not None) for l in range(1, MAXLAG + 1)}
    return lag, res, len(d)


def run_family(name, groups, pft, idx_dir, start, end, step=None, step_group=None, idx_window=None):
    idx, idx_rec = prep_indices(idx_dir, *(idx_window or (start, end)))
    rows, lag_rows = [], []
    for g in groups:
        sd = step if (step and g == step_group) else None
        y, D, rec = prep_bio(load_pft(pft, g), start, end, sd)
        for iname, x in idx.items():
            lag, res, n = pair(y, x, D)
            F, p, dfr = res[lag]
            xr_ = idx_rec[iname]
            rows.append({
                "familia": name, "grupo": g, "indice": iname, "periodo": f"{start}..{end}",
                "indicadora_escalon": sd or "", "n": n, "desfase_AIC": lag, "F": F, "gl": f"{lag},{dfr}", "p": p,
                "ADF_p_grupo": rec["ADF_p"], "KPSS_p_grupo": rec["KPSS_p"], "grupo_diferenciado": rec["diferenciada"],
                "ADF_p_grupo_dif": rec.get("ADF_p_dif", np.nan), "KPSS_p_grupo_dif": rec.get("KPSS_p_dif", np.nan),
                "ADF_p_indice": xr_["ADF_p"], "KPSS_p_indice": xr_["KPSS_p"], "indice_diferenciado": xr_["diferenciada"],
                "ADF_p_indice_dif": xr_.get("ADF_p_dif", np.nan), "KPSS_p_indice_dif": xr_.get("KPSS_p_dif", np.nan),
                **{f"p_desfase{l}": res[l][1] for l in range(1, MAXLAG + 1)}})
            for l, (Fl, pl, _) in res.items():
                lag_rows.append({"familia": name, "grupo": g, "indice": iname, "desfase": l, "F": Fl, "p": pl})
    df, lags = pd.DataFrame(rows), pd.DataFrame(lag_rows)
    df["q_BH"] = multipletests(df["p"], method="fdr_bh")[1]
    df["n_pruebas_familia"] = len(df)
    lags["q_BH_todos_desfases"] = multipletests(lags["p"], method="fdr_bh")[1]
    return df, lags


def md(df):
    try:
        return df.to_markdown(index=False)
    except ImportError:
        return "```\n" + df.to_string(index=False) + "\n```"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pft", default="data/processed/pft_monthly_statistics.nc")
    ap.add_argument("--indices", default="data/raw")
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas") / "granger_revision"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    # Escalón de GREEN
    gl = np.log10(load_pft(a.pft, "GREEN")[START:END])
    step_info = escalon.detect(gl)
    step = step_info["escalon_fecha"]
    pre_end = str((pd.Timestamp(step) - pd.DateOffset(months=1)).date())[:7]
    step_info["ventana_previa"] = f"{START}..{pre_end}"
    json.dump(step_info, open(out / "escalon_GREEN.json", "w"), indent=1)

    A, A_l = run_family("A_principal_5grupos", G5, a.pft, a.indices, START, END)
    B, B_l = run_family("B_PROCHLO_hasta_2016-03", ["PROCHLO"], a.pft, a.indices, START, PROCHLO_END)
    # Variante de B como en granger_robusto.py: índices preparados en jul-2002..dic-2024
    Bb, Bb_l = run_family("B2_PROCHLO_hasta_2016-03_indices_2002-2024", ["PROCHLO"], a.pft, a.indices,
                          START, PROCHLO_END, idx_window=(START, END))
    C1, C1_l = run_family("C1_GREEN_con_indicadora", ["GREEN"], a.pft, a.indices, START, END,
                          step=step, step_group="GREEN")
    C2, C2_l = run_family("C2_GREEN_antes_del_escalon", ["GREEN"], a.pft, a.indices, START, pre_end)
    for C in (C1, C2):  # q dentro de la familia de 15 sustituyendo GREEN
        mix = pd.concat([A[A.grupo != "GREEN"], C])
        C["q_BH_en_familia_15"] = multipletests(mix["p"], method="fdr_bh")[1][-len(C):]
    sup = pd.concat([A, B, Bb, C1, C2], ignore_index=True)
    sup.to_csv(out / "tabla_suplementaria_granger.csv", index=False)
    lags = pd.concat([A_l, B_l, Bb_l, C1_l, C2_l], ignore_index=True)
    lags.to_csv(out / "granger_todos_los_desfases.csv", index=False)

    # Validación: la familia A sin indicadora debe reproducir granger_robusto (mismas p)
    val = None
    ref = Path(__file__).with_name("salidas") / "granger_robusto_pares.csv"
    if ref.exists():
        r = pd.read_csv(ref)
        val = A.merge(r, on=["grupo", "indice"], suffixes=("", "_granger_robusto"))[
            ["grupo", "indice", "desfase_AIC", "desfase_AIC_granger_robusto", "p", "p_granger_robusto"]]
        val["dif_abs_p"] = (val["p"] - val["p_granger_robusto"]).abs()
        val.to_csv(out / "validacion.csv", index=False)

    short = ["familia", "grupo", "indice", "n", "desfase_AIC", "F", "p", "q_BH"]
    with open(out / "resumen.md", "w") as f:
        f.write("# Granger revisado\n\n")
        f.write(f"Escalón de GREEN (log10): `{json.dumps(step_info)}`\n\n")
        f.write("## A. Principal: 5 grupos x 3 índices (BH sobre 15)\n\n" + md(A[short].sort_values("q_BH").round(4)) + "\n\n")
        sigA = A_l[A_l.q_BH_todos_desfases < 0.05]
        f.write(f"Sensibilidad A, todos los desfases (90 pruebas, BH): {len(sigA)} con q<0.05\n\n"
                + (md(sigA.round(4)) if len(sigA) else "") + "\n\n")
        f.write("## B. PROCHLO jul-2002..mar-2016 (BH sobre 3)\n\n" + md(B[short].round(4)) + "\n\n")
        f.write("B2 (variante de granger_robusto.py: índices desestacionalizados y probados en 2002-2024):\n\n"
                + md(Bb[short].round(4)) + "\n\n")
        f.write("## C. Sensibilidad de GREEN al escalón\n\n")
        cmp_ = pd.concat([A[A.grupo == "GREEN"].assign(q_BH_en_familia_15=A[A.grupo == "GREEN"]["q_BH"]), C1, C2])
        f.write(md(cmp_[["familia", "indice", "periodo", "n", "desfase_AIC", "p", "q_BH", "q_BH_en_familia_15",
                         "grupo_diferenciado"]].round(4)) + "\n\n")
        f.write("En la fila de la familia A, `q_BH` y `q_BH_en_familia_15` son la misma (BH sobre 15).\n\n")
        if val is not None:
            f.write(f"Validación contra granger_robusto_pares.csv: máx |Δp| = {val.dif_abs_p.max():.2e}; "
                    f"desfases iguales: {bool((val.desfase_AIC == val.desfase_AIC_granger_robusto).all())}\n")
    with open(out / "tabla_suplementaria_granger.md", "w") as f:
        cols = ["familia", "grupo", "indice", "periodo", "n", "desfase_AIC", "F", "gl", "p", "q_BH",
                "ADF_p_grupo", "KPSS_p_grupo", "grupo_diferenciado", "ADF_p_indice", "KPSS_p_indice",
                "indice_diferenciado"]
        f.write("# Tabla suplementaria: prueba de causalidad de Granger (índice climático -> grupo)\n\n"
                "log10 y anomalía respecto a la climatología mensual; ADF (H0: raíz unitaria) y KPSS "
                "(H0: estacionariedad); se diferencia una vez si no se cumple ADF p<0.05 y KPSS p>0.05. "
                "Desfase elegido por AIC (VAR, máx. 6 meses). q = Benjamini-Hochberg dentro de cada familia. "
                "Las p de KPSS están acotadas a [0.01, 0.10] por la tabla de statsmodels (0.01 = ≤0.01; 0.10 = ≥0.10). "
                "Las p por desfase 1-6 y las pruebas de la serie diferenciada están en el CSV.\n\n"
                + md(sup[cols].round(4)) + "\n")
    print((out / "resumen.md").read_text())


if __name__ == "__main__":
    main()
