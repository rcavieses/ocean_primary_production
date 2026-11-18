#!/usr/bin/env python3
"""
Controles de data/processed/pft_monthly_statistics_poligono.nc.

  1. Atributos (número real de píxeles de la máscara).
  2. Medias de los meses de prueba frente a salidas/procedencia/procedencia_mensual.csv
     (columna media_poligono, calculada por procedencia_mensual.py).
  3. Media ponderada por píxeles de las 5 bandas de REGIONS (salidas/regional_mensual.csv) frente
     a la serie del polígono, para DIATO, DINO, GREEN, HAPTO, PROKAR y PROCHLO, jul-2002..dic-2024:
       (a) pesos = píxeles de la máscara en cada banda (constantes);
       (b) pesos = píxeles CON DATO de cada banda en cada mes (exacto: así promedia
           composicion_regional.py), solo para los meses de prueba, contados desde el NetCDF diario.
  4. Diferencias rectángulo -> polígono de toda la serie (resumen por variable).

Uso:  python3 manuscript/reanalysis/control_poligono.py --nc data/processed/pft_monthly_statistics_poligono.nc \
          --rect data/processed/pft_monthly_statistics.nc --raw data/raw/pft_golfo_california_2000_2024.nc
Salida: manuscript/reanalysis/salidas/poligono/controles/
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1] / "src" / "pipeline"))
from composicion_regional import REGIONS  # noqa: E402

G6 = ["DIATO", "DINO", "GREEN", "HAPTO", "PROKAR", "PROCHLO"]


def md(d):
    try:
        return d.to_markdown(index=False, floatfmt=".6g")
    except ImportError:
        return d.to_string(index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nc", default="data/processed/pft_monthly_statistics_poligono.nc")
    ap.add_argument("--rect", default="data/processed/pft_monthly_statistics.nc")
    ap.add_argument("--raw", default="data/raw/pft_golfo_california_2000_2024.nc")
    ap.add_argument("--procedencia", default=str(HERE / "salidas" / "procedencia" / "procedencia_mensual.csv"))
    ap.add_argument("--regional", default=str(HERE / "salidas" / "regional_mensual.csv"))
    ap.add_argument("--out", default=str(HERE / "salidas" / "poligono" / "controles"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    nc = xr.open_dataset(a.nc); t = pd.DatetimeIndex(nc.time.values)
    P = pd.DataFrame({v[:-5]: nc[v].values for v in nc.data_vars if v.endswith("_mean")}, index=t)

    # 2. meses de prueba
    pr = pd.read_csv(a.procedencia)
    pr["poligono_nc"] = [P.loc[pd.Timestamp(m + "-01"), v] for m, v in zip(pr.mes, pr.variable)]
    pr["dif_abs"] = (pr.poligono_nc - pr.media_poligono).abs()
    c2 = pr[["mes", "variable", "media_poligono", "poligono_nc", "dif_abs"]]
    c2.to_csv(out / "control_meses_prueba.csv", index=False)

    # 3a. bandas ponderadas por píxeles de la máscara
    import config_gulf_california as cg
    ds = xr.open_dataset(a.raw)
    gulf = cg.get_gulf_of_california_filter(ds, use_shapefile=True)
    lat2d = xr.broadcast(ds.latitude, ds.longitude)[0]
    masks = {r: (gulf & (lat2d >= lo) & (lat2d < hi)) for r, (lo, hi) in REGIONS.items()}
    npix = {r: int(m.sum()) for r, m in masks.items()}
    reg = pd.read_csv(a.regional, parse_dates=["mes"])
    rows = []
    for v in G6:
        w = reg.pivot(index="mes", columns="region", values=v)
        wm = sum(w[r] * npix[r] for r in npix) / sum(npix.values())
        d = (wm - P[v].reindex(wm.index))
        rows.append({"variable": v, "meses": len(d), "max_dif_abs": float(d.abs().max()),
                     "max_dif_rel_pct": float((100 * d / P[v].reindex(wm.index)).abs().max()),
                     "media_dif_rel_pct": float((100 * d / P[v].reindex(wm.index)).mean())})
    c3a = pd.DataFrame(rows)
    c3a.to_csv(out / "control_bandas_pesos_mascara.csv", index=False)

    # 3b. exacto con píxeles con dato, meses de prueba
    times = pd.DatetimeIndex(ds.time.values)
    rows = []
    for mes in sorted(pr.mes.unique()):
        p = pd.Period(mes, "M"); idx = np.where((times.year == p.year) & (times.month == p.month))[0]
        for v in ["DIATO", "GREEN"]:
            f = ds[v].isel(time=idx).mean("time")
            num = den = 0.0
            for r, m in masks.items():
                fv = f.where(m)
                nval = int(fv.notnull().sum()); num += float(fv.mean()) * nval; den += nval
            rows.append({"mes": mes, "variable": v, "bandas_pond_pixeles_con_dato": num / den,
                         "poligono_nc": float(P.loc[pd.Timestamp(mes + "-01"), v]),
                         "pixeles_con_dato": int(den), "pixeles_mascara": int(sum(npix.values()))})
    c3b = pd.DataFrame(rows); c3b["dif_abs"] = (c3b.bandas_pond_pixeles_con_dato - c3b.poligono_nc).abs()
    c3b.to_csv(out / "control_bandas_pesos_con_dato.csv", index=False)

    # 4. rectángulo -> polígono
    rc = xr.open_dataset(a.rect)
    R = pd.DataFrame({v[:-5]: rc[v].values for v in rc.data_vars if v.endswith("_mean")}, index=pd.DatetimeIndex(rc.time.values))
    rows = []
    for v in P.columns:
        x, y = R[v].dropna(), P[v].dropna()
        rows.append({"variable": v, "meses_rect": len(x), "meses_pol": len(y), "media_rect": x.mean(), "media_pol": y.mean(),
                     "cambio_pct": 100 * (y.mean() / x.mean() - 1), "r_mensual": float(np.corrcoef(x.align(y, join="inner")[0], x.align(y, join="inner")[1])[0, 1])})
    c4 = pd.DataFrame(rows)
    c4.to_csv(out / "rectangulo_vs_poligono_series.csv", index=False)

    with open(out / "resumen.md", "w") as f:
        f.write("# Controles del NetCDF mensual con el polígono\n\n## Atributos\n\n")
        for k, v in nc.attrs.items():
            f.write(f"- `{k}`: {v}\n")
        f.write(f"\nPíxeles por banda (máscara): {npix} (total {sum(npix.values())})\n\n")
        f.write("## 1. Meses de prueba frente a procedencia_mensual.py\n\n" + md(c2) + "\n\n")
        f.write("## 2a. Bandas ponderadas por píxeles de la máscara frente al polígono (jul-2002..dic-2024)\n\n" + md(c3a) + "\n\n")
        f.write("## 2b. Bandas ponderadas por píxeles con dato (meses de prueba)\n\n" + md(c3b) + "\n\n")
        f.write("## 3. Serie mensual: rectángulo -> polígono\n\n" + md(c4) + "\n")
    print((out / "resumen.md").read_text())


if __name__ == "__main__":
    main()
