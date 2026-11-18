#!/usr/bin/env python3
"""
Tablas comparativas eDNA: todas las filas (análisis original) frente a solo detecciones.

Entradas (de edna_auditoria.py y edna_panel_detecciones.py):
  salidas/edna_<v1|v2|merged>/                      modo original (cuenta filas)
  salidas/edna_detecciones/<v1|v2|merged>/          con --solo-detecciones
  salidas/edna_detecciones/panel_espacial_resumen.csv
Salida (salidas/edna_detecciones/):
  tabla_cascada_comparada.csv, tabla_matchups_comparada.csv, tabla_panel_espacial.csv, tablas.md
Uso:  python3 manuscript/reanalysis/edna_detecciones_tablas.py
"""
import argparse
import re
from pathlib import Path

import pandas as pd

BASES = {"v1": "taxonomy_corrected_edna.csv", "v2": "taxonomy_corrected_edna_2.csv",
         "merged": "ADN_merged_data_20251001_161630.csv"}


def md(d):
    try:
        return d.to_markdown(index=False)
    except ImportError:
        return d.to_string(index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path(__file__).with_name("salidas")))
    a = ap.parse_args()
    d = Path(a.dir); out = d / "edna_detecciones"

    casc = []
    for b, fn in BASES.items():
        o = pd.read_csv(d / f"edna_{b}" / "edna_cascada_filtros.csv")
        n = pd.read_csv(out / b / "edna_cascada_filtros.csv")
        pre = n[n.filtro.str.match(r"0[abc]\.")]
        for _, r in pre.iterrows():
            casc.append({"base": b, "archivo": fn, "filtro": r.filtro, "filas_original": None, "solo_detecciones": r.registros})
        for _, r in o.iterrows():
            k = r.filtro.split(".")[0]
            m = n[n.filtro.str.startswith(k + ".") & ~n.filtro.str.match(r"0[abc]\.")]
            casc.append({"base": b, "archivo": fn, "filtro": re.sub(r"^0\. Registros en el archivo", "0. Registros analizados", r.filtro),
                         "filas_original": r.registros, "solo_detecciones": int(m.registros.iloc[0]) if len(m) else None})
    C = pd.DataFrame(casc)
    C.to_csv(out / "tabla_cascada_comparada.csv", index=False)

    mu = []
    for b in BASES:
        o = pd.read_csv(d / f"edna_{b}" / "edna_matchups_resumen.csv")
        n = pd.read_csv(out / b / "edna_matchups_resumen.csv")
        m = o.merge(n, on=["configuracion", "grupo"], suffixes=("_filas", "_det"))
        m.insert(0, "base", b)
        mu.append(m[["base", "configuracion", "grupo", "variable_satelital_filas", "registros_filas", "registros_det",
                      "n_meses_match_filas", "n_meses_match_det", "pearson_r_filas", "pearson_r_det", "pearson_p_det",
                      "spearman_rho_filas", "spearman_rho_det", "spearman_p_det"]]
                  .rename(columns={"variable_satelital_filas": "variable_satelital"}))
    M = pd.concat(mu, ignore_index=True)
    M.to_csv(out / "tabla_matchups_comparada.csv", index=False)

    P = pd.read_csv(out / "panel_espacial_resumen.csv")
    Pw = P.pivot_table(index=["panel", "variable_satelital"], columns="variante",
                       values=["filas_usadas", "n_meses", "pearson_r", "pearson_p", "spearman_rho"], aggfunc="first")
    Pw.columns = [f"{v}__{k.split(' (')[0].replace(' ', '_')}" for v, k in Pw.columns]
    Pw = Pw.reset_index()
    Pw.to_csv(out / "tabla_panel_espacial.csv", index=False)

    with open(out / "tablas.md", "w") as f:
        f.write("# eDNA: todas las filas frente a solo detecciones\n\n## Cascada de filtros\n\n" + md(C) + "\n\n"
                "## Match-ups de edna_auditoria.py\n\n" + md(M.round(3)) + "\n\n"
                "## Panel espacial (origen de r = 0.27 / -0.46)\n\n" + md(Pw.round(4)) + "\n")
    print((out / "tablas.md").read_text()[:3000])


if __name__ == "__main__":
    main()
