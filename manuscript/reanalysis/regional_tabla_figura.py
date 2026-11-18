#!/usr/bin/env python3
"""
Tabla y figura de apoyo para la composición por región (bandas de latitud de composicion_regional.py).

Entrada: salidas/regional_mensual.csv y salidas/regional_composicion.csv (de composicion_regional.py).
Salida (salidas/regional/):
  Tabla_regional_composicion.csv / .md  composición ponderada por biomasa (%) por región y periodo,
                                         biomasa total de los 5 grupos (mg m-3) y n de meses
  Fig_regional_composicion.png           (a) 2002-2024 por región; (b) por quinquenio y región
Uso:  python3 manuscript/reanalysis/regional_tabla_figura.py
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from composicion_regional import G5, PERIODS, REGIONS  # noqa: E402

NAMES = {"DIATO": "Diatomeas", "DINO": "Dinoflagelados", "GREEN": "Clorofitas",
         "HAPTO": "Haptofitas", "PROKAR": "Procariotas"}
# mismos colores que Fig. 2 (make_manuscript_figures.py: CAT[0], CAT[1], CAT[2], CAT[3], CAT[5])
COLORS = {"DIATO": "#2a78d6", "DINO": "#eb6834", "GREEN": "#1baf7a", "HAPTO": "#eda100", "PROKAR": "#008300"}
ORDER = list(REGIONS)  # norte -> sur
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path(__file__).with_name("salidas")))
    a = ap.parse_args()
    d = Path(a.dir); out = d / "regional"; out.mkdir(parents=True, exist_ok=True)
    mon = pd.read_csv(d / "regional_mensual.csv", parse_dates=["mes"])
    comp = pd.read_csv(d / "regional_composicion.csv")

    per = {"2002-2024": ("2002-07", "2024-12"), **PERIODS}
    rows = []
    for r in ORDER:
        g = mon[mon.region == r].set_index("mes").sort_index()
        for p, (a0, a1) in per.items():
            s = g.loc[a0:a1, G5]
            c = comp[(comp.region == r) & (comp.periodo == p) & (comp.tipo == "ponderada_biomasa")].iloc[0]
            cu = comp[(comp.region == r) & (comp.periodo == p) & (comp.tipo == "media_porcentajes")].iloc[0]
            lo, hi = REGIONS[r]
            rows.append({"region": r, "banda_lat_N": f"{lo}–{hi}", "periodo": p, "n_meses": int(s.dropna().shape[0]),
                         "biomasa_5grupos_mg_m3": round(float(s.sum(axis=1).mean()), 4),
                         **{f"{NAMES[k]} (%)": float(c[k]) for k in G5},
                         **{f"{NAMES[k]} (% no ponderado)": float(cu[k]) for k in G5}})
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "Tabla_regional_composicion.csv", index=False)
    show = tab[["region", "banda_lat_N", "periodo", "n_meses", "biomasa_5grupos_mg_m3"] + [f"{NAMES[k]} (%)" for k in G5]]
    with open(out / "Tabla_regional_composicion.md", "w") as f:
        f.write("# Composición de PFT por región (bandas de latitud dentro del polígono del golfo)\n\n"
                "Porcentaje de la biomasa de clorofila de los 5 grupos de la partición sin doble conteo "
                "(media del grupo / suma de las medias de los 5 grupos). Prochlorococcus no se incluye "
                "(subconjunto de procariotas). Columnas no ponderadas en el CSV.\n\n")
        try:
            f.write(show.to_markdown(index=False) + "\n")
        except ImportError:
            f.write(show.to_string(index=False) + "\n")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": INK2,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig = plt.figure(figsize=(6.8, 6.4))
    gs = fig.add_gridspec(2, 5, height_ratios=[1, 1.15], hspace=0.55, wspace=0.12)
    ax = fig.add_subplot(gs[0, :])
    full = tab[tab.periodo == "2002-2024"].set_index("region").loc[ORDER]
    left = np.zeros(len(full))
    for k in G5:
        v = full[f"{NAMES[k]} (%)"].values
        ax.barh(range(len(full)), v, left=left, color=COLORS[k], label=NAMES[k], height=0.7)
        for i, (l, w) in enumerate(zip(left, v)):
            if w >= 6:
                ax.text(l + w / 2, i, f"{w:.0f}", ha="center", va="center", color="white", fontsize=7.5)
        left += v
    ax.set_yticks(range(len(full)))
    ax.set_yticklabels([f"{r}\n({REGIONS[r][0]}–{REGIONS[r][1]}° N)" for r in ORDER], fontsize=7.5)
    ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel("% de la biomasa (clorofila) de los 5 grupos")
    ax.set_title("(a) Jul 2002 – dic 2024", loc="left", fontweight="bold", fontsize=9)
    fig.legend(*ax.get_legend_handles_labels(), ncol=5, fontsize=7.2, frameon=False, loc="lower center",
               bbox_to_anchor=(0.5, 0.905))
    labs = list(PERIODS)
    for j, r in enumerate(ORDER):
        axr = fig.add_subplot(gs[1, j])
        sub = tab[(tab.region == r) & (tab.periodo.isin(labs))].set_index("periodo").loc[labs]
        bottom = np.zeros(len(sub))
        for k in G5:
            v = sub[f"{NAMES[k]} (%)"].values
            axr.bar(range(len(sub)), v, bottom=bottom, color=COLORS[k], width=0.8)
            bottom += v
        axr.set_xticks(range(len(sub))); axr.set_xticklabels([p[2:4] + "–" + p[-2:] for p in labs], rotation=90, fontsize=7)
        axr.set_ylim(0, 100); axr.set_title(r, fontsize=7.8)
        if j:
            axr.set_yticklabels([])
        else:
            axr.set_ylabel("%")
    fig.text(0.125, 0.475, "(b) Por quinquenio (el primero inicia en jul 2002)", fontweight="bold", fontsize=9)
    fig.savefig(out / "Fig_regional_composicion.png", dpi=220, bbox_inches="tight", facecolor="white")
    print(show[show.periodo == "2002-2024"].to_string(index=False))


if __name__ == "__main__":
    main()
