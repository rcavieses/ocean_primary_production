#!/usr/bin/env python3
"""
Punto 3: ¿depende la Fig. 4 (mapas de diferencias quinquenales) de la máscara?

src/visualization/plot_pft_quinquennial_diff.py calcula, píxel a píxel desde el NetCDF diario,
media(2020-2024) - media(quinquenio previo) con data.where(mask).mean('time'), y fija la escala de
color simétrica en el percentil 99 de |Δ| de todos los píxeles de la máscara (symmetric_vmax). Ese
script no se puede importar (ejecuta todo al cargarse); aquí se replica el cálculo para CHL y DIATO
con las dos máscaras de config_gulf_california (rectángulo y polígono) y se informa:
  - si los valores de Δ dentro del polígono son idénticos con ambas máscaras;
  - el ±vmax de la escala con cada máscara;
  - cuántos píxeles con dato muestra cada mapa.

Uso:  python3 manuscript/reanalysis/fig4_escala.py --raw data/raw/pft_golfo_california_2000_2024.nc
Salida: manuscript/reanalysis/salidas/poligono/fig4/fig4_escala.csv
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "pipeline"))
import config_gulf_california as cg  # noqa: E402

PERIODS = {"2000-2004": ("2000-01-01", "2004-12-31"), "2005-2009": ("2005-01-01", "2009-12-31"),
           "2010-2014": ("2010-01-01", "2014-12-31"), "2015-2019": ("2015-01-01", "2019-12-31")}
REF = ("2020-01-01", "2024-12-31")


def symmetric_vmax(arrs, pct=99):
    """Igual que plot_pft_quinquennial_diff.symmetric_vmax."""
    valid = np.concatenate([a[np.isfinite(a)].ravel() for a in arrs])
    return max(float(np.nanpercentile(np.abs(valid), pct)), 1e-10)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw/pft_golfo_california_2000_2024.nc")
    ap.add_argument("--vars", nargs="+", default=["CHL", "DIATO"])
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas") / "poligono" / "fig4"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(a.raw)
    masks = {"rectangulo": np.asarray(cg.get_gulf_of_california_filter_bbox(ds)),
             "poligono": np.asarray(cg.get_gulf_of_california_filter_shapefile(ds))}
    rows = []
    for v in a.vars:
        ref = ds[v].sel(time=slice(*REF)).mean("time").values
        diffs = {p: ref - ds[v].sel(time=slice(*rng)).mean("time").values for p, rng in PERIODS.items()}
        for k, m in masks.items():
            dm = [np.where(m, d, np.nan) for d in diffs.values()]
            rows.append({"variable": v, "mascara": k, "pixeles_mascara": int(m.sum()),
                         "pixeles_con_dato_min": int(min(np.isfinite(x).sum() for x in dm)),
                         "vmax_abs_p99": symmetric_vmax(dm, 99),
                         **{f"media_delta_{p}": float(np.nanmean(x)) for p, x in zip(diffs, dm)}})
        inside = masks["poligono"]
        same = all(np.array_equal(np.where(inside, d, np.nan), np.where(inside & masks["rectangulo"], d, np.nan), equal_nan=True)
                   for d in diffs.values())
        rows.append({"variable": v, "mascara": "control", "nota": f"Δ dentro del polígono idéntico con ambas máscaras: {same}"})
        print(v, "listo", flush=True)
    T = pd.DataFrame(rows)
    T.to_csv(out / "fig4_escala.csv", index=False)
    print(T.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
