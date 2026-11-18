#!/usr/bin/env python3
"""
Match-ups satélite-eDNA del panel espacial (origen de r = 0.27 y r = -0.46 del manuscrito),
recalculados con todas las filas (como el original) y solo con detecciones.

Replica sin modificarlo el cálculo de src/visualization/plot_satellite_vs_insitu_spatial_panel.py:
  - eDNA: taxonomy_corrected_edna_2.csv (v2), columnas en minúsculas, fecha con
    pd.to_datetime(errors='coerce'), años 2000-2016.
  - Grupo: `phylum` en PRIMARY_PRODUCERS del script; "Total Chlorophyll" = TODAS las filas
    (todos los taxones, no solo productores primarios).
  - Unidad de n: año-mes con >= 1 fila del grupo; valor in situ = número de filas en ese mes;
    valor satelital = media mensual de la cuenca (pft_monthly_statistics.nc, 2000-2016).
  - Pearson (y Spearman) entre ambos.
Variantes: "todas las filas" (original) y "solo detecciones" (Abundance > 0). La v2 no tiene
bloque de totales. Se informa también cuántas muestras distintas (TableID, sitio, fecha,
profundidad) hay en cada mes, porque el conteo de filas crece con el esfuerzo de muestreo.

Uso:  python3 manuscript/reanalysis/edna_panel_detecciones.py --csv data/insitu/taxonomy_corrected_edna_2.csv \
          --pft data/processed/pft_monthly_statistics.nc
Salida: manuscript/reanalysis/salidas/edna_detecciones/panel_espacial_{resumen,detalle}.csv
"""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parents[2]


def load_panel_constants():
    """Lee PRIMARY_PRODUCERS, SPECIES_MAPPING y el rango de fechas del script original sin ejecutarlo."""
    src = (ROOT / "src/visualization/plot_satellite_vs_insitu_spatial_panel.py").read_text()
    start = src.index("# Time range"); end = src.index("# =", src.index("SPECIES_MAPPING = ["))
    ns = {}
    exec(src[start:end], ns)  # solo asignaciones de constantes (sin imports ni efectos)
    return ns["START_DATE"], ns["END_DATE"], ns["PRIMARY_PRODUCERS"], ns["SPECIES_MAPPING"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/insitu/taxonomy_corrected_edna_2.csv")
    ap.add_argument("--pft", default="data/processed/pft_monthly_statistics.nc")
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas") / "edna_detecciones"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    START, END, PP, MAPPING = load_panel_constants()

    ds = xr.open_dataset(a.pft).sel(time=slice(START, END))
    sat = pd.DataFrame({v: ds[v].values for v in ds.data_vars}, index=pd.to_datetime(ds.time.values))
    sat_m = sat.groupby(sat.index.to_period("M")).mean()

    df = pd.read_csv(a.csv)
    df.columns = df.columns.str.lower()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df[(df.date.dt.year >= 2000) & (df.date.dt.year <= 2016)].copy()
    df["year_month"] = df.date.dt.to_period("M")
    df["muestra"] = df[["tableid", "site_name", "date", "depth"]].astype(str).agg("|".join, axis=1)

    rows, detail = [], []
    for variant, d in [("todas las filas (original)", df), ("solo detecciones (Abundance > 0)", df[df.abundance > 0])]:
        for sp in MAPPING:
            g = sp["insitu_group"]
            sub = d if g == "All" else d[d["phylum"].astype(str).str.strip().isin(PP.get(g, []))]
            cnt = sub.groupby("year_month").size()
            comp = pd.DataFrame({"insitu_count": cnt})
            comp["sat_value"] = comp.index.map(sat_m[sp["sat_var"]])
            comp = comp.dropna()
            rec = {"variante": variant, "panel": sp["name_en"], "grupo_in_situ": g, "variable_satelital": sp["sat_var"],
                   "filas_usadas": len(sub), "filas_con_abundancia_0": int((sub.abundance == 0).sum()),
                   "n_meses": len(comp)}
            if len(comp) >= 3:
                rec["pearson_r"], rec["pearson_p"] = pearsonr(comp.sat_value, comp.insitu_count)
                rec["spearman_rho"], rec["spearman_p"] = spearmanr(comp.sat_value, comp.insitu_count)
            rows.append(rec)
            ms = sub.groupby("year_month")["muestra"].nunique()
            for ym, r in comp.iterrows():
                detail.append({"variante": variant, "panel": sp["name_en"], "mes": str(ym),
                               "filas": int(r.insitu_count), "muestras_distintas": int(ms.get(ym, 0)),
                               "satelite": float(r.sat_value)})
    res = pd.DataFrame(rows)
    res.to_csv(out / "panel_espacial_resumen.csv", index=False)
    pd.DataFrame(detail).to_csv(out / "panel_espacial_detalle.csv", index=False)
    print(res.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
