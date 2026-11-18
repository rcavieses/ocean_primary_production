#!/usr/bin/env python3
"""
Composición de productores primarios por grupo y estrato de profundidad en la eDNA (v1).

Solo taxonomy_corrected_edna.csv (v1) tiene los tres estratos (`Shallow (m)` 1-26 m,
`Mid-water (m)` 35-140 m, `Deep (m)` 220-1000 m). La v2 está en 3-21 m salvo 51 registros de
Cerrillo con fecha inválida (1905) y ADN_merged no tiene profundidad.

IMPORTANTE: la v1 es una matriz completa muestra x taxón: 82 muestras (`Original_ID`) x 2325 filas;
solo las filas con `Abundancia` > 0 son detecciones. Aquí se usan SOLO detecciones. (Para
comparar, se informa también el conteo de filas sin filtrar, que es lo que contaban los scripts
anteriores.)

Grupos y asignación de estrato: los mismos de edna_auditoria.py (GROUPS buscados en kingdom,
class y phylum, que en la v1 tienen el contenido de class y phylum invertido; capa = la columna
de profundidad que no está vacía).

Métricas por estrato y grupo:
  detecciones (filas con Abundancia>0), % de las detecciones de productores primarios,
  taxones distintos (old_species), muestras con >=1 detección del grupo y % de muestras,
  suma de Abundancia y su % (unidad no documentada en el archivo; tratar con cautela).
Variantes: todas las zonas / sin "SOUTH PACIFIC".

Uso:  python3 manuscript/reanalysis/edna_estratos.py --csv data/insitu/taxonomy_corrected_edna.csv
Salida: manuscript/reanalysis/salidas/edna_estratos/
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
from edna_auditoria import GROUPS, PACIFIC_PAT, classify, layer_v1  # noqa: E402

LAYERS = ["Superficial", "Intermedia", "Profunda"]
RANGE = {"Superficial": "1–26 m", "Intermedia": "35–140 m", "Profunda": "220–1000 m"}
COLORS = {"Diatomeas": "#2a78d6", "Dinoflagelados": "#eb6834", "Clorofitas": "#1baf7a",
          "Haptofitas": "#eda100", "Cianobacterias": "#008300"}


def table(df, label):
    prim = df[df.grupo != "No productor primario"]
    rows = []
    for L in LAYERS:
        dl = df[df.capa == L]; pl = prim[prim.capa == L]
        n_samp = dl["Original_ID"].nunique()
        for g in GROUPS:
            s = pl[pl.grupo == g]
            rows.append({"variante": label, "estrato": L, "rango": RANGE[L], "grupo": g,
                         "muestras_estrato": n_samp, "detecciones": len(s),
                         "pct_detecciones_productores": 100 * len(s) / len(pl) if len(pl) else np.nan,
                         "taxones_distintos": s["old_species"].nunique(),
                         "muestras_con_grupo": s["Original_ID"].nunique(),
                         "pct_muestras_con_grupo": 100 * s["Original_ID"].nunique() / n_samp if n_samp else np.nan,
                         "suma_Abundancia": float(s["Abundancia"].sum()),
                         "pct_Abundancia_productores": 100 * s["Abundancia"].sum() / pl["Abundancia"].sum()
                         if pl["Abundancia"].sum() else np.nan})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/insitu/taxonomy_corrected_edna.csv")
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas") / "edna_estratos"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(a.csv, low_memory=False)
    cs, cm, cd = "Shallow (m)", "Mid-water (m)", "Deep (m)"
    n_layers = raw[[cs, cm, cd]].notna().sum(axis=1)
    raw["capa"] = raw.apply(lambda r: layer_v1(r, cs, cm, cd), axis=1)
    raw["grupo"] = classify(raw, "phylum", "class", "kingdom")
    det = raw[raw["Abundancia"] > 0].copy()
    no_pac = det[~det["ZONE"].astype(str).str.contains(PACIFIC_PAT)]

    T = pd.concat([table(det, "todas las zonas"), table(no_pac, "sin SOUTH PACIFIC")], ignore_index=True)
    T.to_csv(out / "edna_composicion_grupo_estrato.csv", index=False)

    # Resumen por estrato y comparación con el conteo sin filtrar (incluye ausencias)
    summ = []
    for L in LAYERS:
        summ.append({"estrato": L, "rango": RANGE[L],
                     "muestras": raw.loc[raw.capa == L, "Original_ID"].nunique(),
                     "filas_archivo": int((raw.capa == L).sum()),
                     "filas_productores_sin_filtrar": int(((raw.capa == L) & (raw.grupo != "No productor primario")).sum()),
                     "detecciones_totales": int((det.capa == L).sum()),
                     "detecciones_productores": int(((det.capa == L) & (det.grupo != "No productor primario")).sum()),
                     "detecciones_productores_sin_SOUTH_PACIFIC": int(((no_pac.capa == L) & (no_pac.grupo != "No productor primario")).sum())})
    summ.append({"estrato": "sin estrato (bloque de totales: suma de las 81 muestras, sin fecha)", "rango": "", "muestras": raw.loc[raw.capa.isna(), "Original_ID"].nunique(),
                 "filas_archivo": int(raw.capa.isna().sum()),
                 "filas_productores_sin_filtrar": int((raw.capa.isna() & (raw.grupo != "No productor primario")).sum()),
                 "detecciones_totales": int(det.capa.isna().sum()),
                 "detecciones_productores": int((det.capa.isna() & (det.grupo != "No productor primario")).sum()),
                 "detecciones_productores_sin_SOUTH_PACIFIC": int((no_pac.capa.isna() & (no_pac.grupo != "No productor primario")).sum())})
    S = pd.DataFrame(summ)
    S.to_csv(out / "edna_resumen_estratos.csv", index=False)
    zones = pd.crosstab(raw.drop_duplicates("Original_ID")["capa"].fillna("sin estrato"),
                        raw.drop_duplicates("Original_ID")["ZONE"].fillna("NaN"))
    zones.to_csv(out / "edna_muestras_estrato_x_zona.csv")

    def md(d):
        try:
            return d.to_markdown(index=False)
        except ImportError:
            return d.to_string(index=False)
    show = ["estrato", "grupo", "muestras_estrato", "detecciones", "pct_detecciones_productores",
            "taxones_distintos", "muestras_con_grupo", "pct_muestras_con_grupo", "pct_Abundancia_productores"]
    with open(out / "resumen.md", "w") as f:
        f.write("# eDNA (v1): productores primarios por grupo y estrato (solo detecciones, Abundancia>0)\n\n"
                f"Filas con más de una columna de profundidad llena: {int((n_layers > 1).sum())}; sin ninguna: "
                f"{int((n_layers == 0).sum())}. Filas con Abundancia>0: {len(det)} de {len(raw)}.\n\n"
                "## Resumen por estrato\n\n" + md(S) + "\n\n## Muestras por estrato y zona\n\n"
                + md(zones.reset_index()) + "\n\n")
        for v in T.variante.unique():
            f.write(f"## Composición por grupo y estrato — {v}\n\n" + md(T[T.variante == v][show].round(2)) + "\n\n")

    # Figura: % de detecciones de productores por estrato (todas las zonas) + n de muestras
    sub = T[T.variante == "todas las zonas"]
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    left = np.zeros(len(LAYERS))
    for g in GROUPS:
        v = sub[sub.grupo == g].set_index("estrato").loc[LAYERS, "pct_detecciones_productores"].fillna(0).values
        if v.sum() == 0:
            continue
        ax.barh(range(len(LAYERS)), v, left=left, color=COLORS[g], label=g, height=0.65)
        for i, (l, w) in enumerate(zip(left, v)):
            if w >= 7:
                ax.text(l + w / 2, i, f"{w:.0f}", ha="center", va="center", color="white", fontsize=7.5)
        left += v
    ns = S.set_index("estrato")
    ax.set_yticks(range(len(LAYERS)))
    ax.set_yticklabels([f"{L} ({RANGE[L]})\n{ns.loc[L, 'muestras']} muestras, {ns.loc[L, 'detecciones_productores']} det."
                        for L in LAYERS], fontsize=7.5)
    ax.invert_yaxis(); ax.set_xlim(0, 100)
    ax.set_xlabel("% de las detecciones de productores primarios")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.25))
    fig.tight_layout(); fig.savefig(out / "Fig_edna_estratos.png", dpi=220, facecolor="white")
    print((out / "resumen.md").read_text())


if __name__ == "__main__":
    main()
