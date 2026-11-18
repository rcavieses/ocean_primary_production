#!/usr/bin/env python3
"""
Composición y anomalía de PFT por fase ENSO (El Niño, La Niña, Neutral).

Fases (criterio tipo ONI de NOAA) a partir de data/raw/nino34.long.anom.csv:
  media móvil centrada de 3 meses de la anomalía Niño 3.4; El Niño si >= +0.5 °C y La Niña si
  <= -0.5 °C durante al menos 5 meses consecutivos; el resto, Neutral. (La anomalía viene del
  archivo de NOAA PSL tal cual; no se recalcula con climatologías móviles de 30 años.)

Grupos: los 5 de la partición sin doble conteo (DIATO, DINO, GREEN, HAPTO, PROKAR) + CHL total;
periodo jul-2002..dic-2024. PROCHLO no se usa (discontinuidad de 2016).

Para cada fase:
  1. n de meses.
  2. Composición ponderada por biomasa (%) = media del grupo en la fase / suma de las 5 medias.
  3. Anomalía de composición ajustada por estación (puntos porcentuales): % mensual menos la
     climatología mensual del %, promediada en la fase (las fases ENSO no se reparten igual
     entre meses del año, así que la composición cruda mezcla ENSO y estacionalidad).
  4. Anomalía de biomasa: log10 desestacionalizado, promediado en la fase y expresado como %
     (100*(10^m - 1)).
Prueba: diferencia de cada fase contra Neutral; p por permutación con desplazamiento circular
de la serie de fases (conserva la autocorrelación de ambas series), BH dentro de cada familia
(anomalía de biomasa: 6 series x 2 contrastes; anomalía de composición: 5 x 2).
Sensibilidad: (s1) anomalías tras quitar además la tendencia lineal de cada serie y, en GREEN,
el escalón de 2016 detectado con escalon.py; (s2) fase desfasada 3 meses (ENSO adelantado).

Uso:  python3 manuscript/reanalysis/enso_fases.py --pft data/processed/pft_monthly_statistics.nc --nino data/raw/nino34.long.anom.csv
Salida: manuscript/reanalysis/salidas/enso_fases/
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).parent))
import escalon  # noqa: E402
import granger_robusto as gr  # noqa: E402

G5 = ["DIATO", "DINO", "GREEN", "HAPTO", "PROKAR"]
NAMES = {"DIATO": "Diatomeas", "DINO": "Dinoflagelados", "GREEN": "Clorofitas", "HAPTO": "Haptofitas",
         "PROKAR": "Procariotas", "CHL": "Clorofila total"}
COLORS = {"DIATO": "#2a78d6", "DINO": "#eb6834", "GREEN": "#1baf7a", "HAPTO": "#eda100", "PROKAR": "#008300"}
PHC = {"El Niño": "#c0392b", "Neutral": "#8a8985", "La Niña": "#2a78d6"}
START, END = "2002-07", "2024-12"
PHASES = ["El Niño", "Neutral", "La Niña"]


def oni_phases(nino):
    oni = nino.rolling(3, center=True).mean()
    def runs(mask):
        out = pd.Series(False, index=mask.index)
        grp = (mask != mask.shift()).cumsum()
        for _, idx in mask.groupby(grp):
            if idx.iloc[0] and len(idx) >= 5:
                out[idx.index] = True
        return out
    ph = pd.Series("Neutral", index=oni.index)
    ph[runs(oni >= 0.5)] = "El Niño"
    ph[runs(oni <= -0.5)] = "La Niña"
    ph[oni.isna()] = np.nan
    return ph, oni


def perm_test(values, phases, n_shift_min=12):
    """Diferencia de medias fase - Neutral; p por desplazamiento circular de las fases."""
    v = values.values; ph = phases.values; n = len(v)
    def stat(p):
        neu = v[p == "Neutral"].mean()
        return {f: v[p == f].mean() - neu for f in ("El Niño", "La Niña")}
    obs = stat(ph)
    shifts = range(n_shift_min, n - n_shift_min + 1)
    null = {f: np.array([stat(np.roll(ph, k))[f] for k in shifts]) for f in obs}
    return {f: (obs[f], float((np.sum(np.abs(null[f]) >= abs(obs[f])) + 1) / (len(null[f]) + 1))) for f in obs}


def anomalies(df, detrend=False, green_step=None):
    an = {}
    for v in df.columns:
        a = gr.deseason(np.log10(df[v]))
        if detrend:
            t = np.arange(len(a)); X = [np.ones_like(t, float), t.astype(float)]
            if v == "GREEN" and green_step is not None:
                X.append((a.index >= green_step).astype(float))
            X = np.column_stack(X); b, *_ = np.linalg.lstsq(X, a.values, rcond=None)
            a = a - X @ b + a.mean()
        an[v] = a
    return pd.DataFrame(an)


def analyse(df, ph, label, detrend=False, green_step=None):
    an = anomalies(df, detrend, green_step)
    pct = df[G5].div(df[G5].sum(axis=1), axis=0) * 100
    pct_an = pct - pct.groupby(pct.index.month).transform("mean")
    rows_b, rows_c = [], []
    for v in an.columns:
        res = perm_test(an[v], ph)
        for f in PHASES:
            m = an[v][ph == f].mean()
            rows_b.append({"analisis": label, "variable": v, "fase": f, "n_meses": int((ph == f).sum()),
                           "anomalia_log10": m, "anomalia_pct": 100 * (10 ** m - 1),
                           "dif_vs_Neutral_log10": res[f][0] if f in res else np.nan,
                           "p_perm": res[f][1] if f in res else np.nan})
    for v in G5:
        res = perm_test(pct_an[v], ph)
        for f in PHASES:
            rows_c.append({"analisis": label, "grupo": v, "fase": f, "n_meses": int((ph == f).sum()),
                           "anomalia_composicion_pp": pct_an[v][ph == f].mean(),
                           "p_perm": res[f][1] if f in res else np.nan})
    B, C = pd.DataFrame(rows_b), pd.DataFrame(rows_c)
    for T in (B, C):
        m = T.p_perm.notna()
        T.loc[m, "q_BH"] = multipletests(T.loc[m, "p_perm"], method="fdr_bh")[1]
    return B, C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pft", default="data/processed/pft_monthly_statistics.nc")
    ap.add_argument("--nino", default="data/raw/nino34.long.anom.csv")
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas") / "enso_fases"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    ds = xr.open_dataset(a.pft)
    t = pd.DatetimeIndex(ds["time"].values).to_period("M").to_timestamp()
    df = pd.DataFrame({v: ds[f"{v}_mean"].values for v in G5 + ["CHL"]}, index=t)[START:END]
    assert df.notna().all().all() and (df > 0).all().all()
    nino = gr.load_index("NINO34", a.nino)
    ph_all, oni = oni_phases(nino)
    ph = ph_all.reindex(df.index)
    pd.DataFrame({"nino34_anom": nino.reindex(df.index), "oni_3m": oni.reindex(df.index), "fase": ph}).to_csv(out / "fases_mensuales.csv")
    step = pd.Timestamp(escalon.detect(np.log10(df["GREEN"]), n_perm=200)["escalon_fecha"])

    # Composición cruda ponderada por biomasa
    comp = []
    for f in PHASES:
        m = df.loc[ph == f, G5].mean()
        comp.append({"fase": f, "n_meses": int((ph == f).sum()), **(100 * m / m.sum()).round(2).to_dict(),
                     "CHL_media_mg_m3": round(float(df.loc[ph == f, "CHL"].mean()), 4)})
    m = df[G5].mean()
    comp.append({"fase": "Todo el periodo", "n_meses": len(df), **(100 * m / m.sum()).round(2).to_dict(),
                 "CHL_media_mg_m3": round(float(df["CHL"].mean()), 4)})
    comp = pd.DataFrame(comp)
    comp.to_csv(out / "composicion_por_fase.csv", index=False)
    # Meses por fase y mes del calendario (desbalance estacional)
    pd.crosstab(df.index.month, ph).to_csv(out / "meses_por_fase_y_mes_calendario.csv")

    B0, C0 = analyse(df, ph, "principal (lag 0)")
    B1, C1 = analyse(df, ph, "s1 sin tendencia lineal ni escalón de GREEN", detrend=True, green_step=step)
    ph3 = ph_all.shift(3).reindex(df.index)
    B2, C2 = analyse(df, ph3, "s2 fase adelantada 3 meses")
    B = pd.concat([B0, B1, B2]); C = pd.concat([C0, C1, C2])
    B.to_csv(out / "anomalia_biomasa_por_fase.csv", index=False)
    C.to_csv(out / "anomalia_composicion_por_fase.csv", index=False)

    def md(d):
        try:
            return d.to_markdown(index=False)
        except ImportError:
            return d.to_string(index=False)
    with open(out / "resumen.md", "w") as f:
        f.write("# PFT por fase ENSO (jul-2002..dic-2024)\n\n"
                f"Meses por fase: {ph.value_counts().to_dict()}. Escalón de GREEN usado en s1: {step:%Y-%m}.\n\n"
                "## Composición ponderada por biomasa (%), cruda\n\n" + md(comp) + "\n\n"
                "## Anomalía de biomasa (log10 desestacionalizado; % = 100*(10^m-1)); p y q contra Neutral\n\n"
                + md(B[["analisis", "variable", "fase", "n_meses", "anomalia_pct", "p_perm", "q_BH"]].round(4)) + "\n\n"
                "## Anomalía de composición ajustada por estación (puntos porcentuales)\n\n"
                + md(C[["analisis", "grupo", "fase", "n_meses", "anomalia_composicion_pp", "p_perm", "q_BH"]].round(4)) + "\n")

    # Figura
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.4), gridspec_kw={"width_ratios": [1, 1.6]})
    c3 = comp.set_index("fase").loc[PHASES]
    left = np.zeros(3)
    for g in G5:
        ax[0].bar(range(3), c3[g], bottom=left, color=COLORS[g], label=NAMES[g], width=0.7)
        left += c3[g].values
    ax[0].set_xticks(range(3)); ax[0].set_xticklabels([f"{p}\n(n={c3.loc[p, 'n_meses']})" for p in PHASES])
    ax[0].set_ylabel("% de la biomasa de los 5 grupos"); ax[0].set_ylim(0, 100)
    ax[0].set_title("(a) Composición (cruda)", loc="left", fontweight="bold", fontsize=9)
    ax[0].legend(fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    vs = G5 + ["CHL"]; w = 0.27
    for i, f in enumerate(PHASES):
        sub = B0[B0.fase == f].set_index("variable").loc[vs]
        x = np.arange(len(vs)) + (i - 1) * w
        ax[1].bar(x, sub["anomalia_pct"], width=w, color=PHC[f], label=f)
        for xi, (val, q) in zip(x, zip(sub["anomalia_pct"], sub["q_BH"])):
            if pd.notna(q) and q < 0.05:
                ax[1].text(xi, val + (0.4 if val >= 0 else -0.4), "*", ha="center",
                           va="bottom" if val >= 0 else "top", fontsize=10)
    ax[1].axhline(0, color="#52514e", lw=0.6)
    ax[1].set_xticks(range(len(vs))); ax[1].set_xticklabels([NAMES[v] for v in vs], rotation=30, ha="right")
    ax[1].set_ylabel("Anomalía de biomasa (%)")
    ax[1].set_title("(b) Anomalía (* q<0.05 frente a Neutral)", loc="left", fontweight="bold", fontsize=9)
    lo, hi = ax[1].get_ylim(); ax[1].set_ylim(lo - 1.5, hi + 5)
    ax[1].legend(fontsize=7, frameon=False, ncol=3, loc="upper center")
    fig.tight_layout(); fig.savefig(out / "Fig_enso_fases.png", dpi=220, facecolor="white")
    print((out / "resumen.md").read_text())


if __name__ == "__main__":
    main()
