#!/usr/bin/env python3
"""
Composición de PFT por región del golfo, ponderada por biomasa (comentario 8).

Lee el NetCDF diario original mes por mes (como src/pipeline/preprocess_pft_data.py),
aplica la máscara del polígono del golfo y separa cinco regiones por bandas de
latitud (editables en REGIONS). Para cada región y mes guarda la media espacial de
los 5 grupos de la partición sin doble conteo (DIATO, DINO, GREEN, HAPTO, PROKAR) y
de PROCHLO (solo informativo). Luego calcula, por región y quinquenio:
  - composición ponderada por biomasa = media(grupo) / suma de medias de los 5 grupos
  - composición media de porcentajes mensuales (no ponderada)

Uso (desde la raíz del repositorio, en el equipo con el NetCDF de 81 GB):
    python3 manuscript/reanalysis/composicion_regional.py \
        --raw data/raw/pft_golfo_california_2000_2024.nc
Salida: manuscript/reanalysis/salidas/regional_mensual.csv, regional_composicion.csv
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "pipeline"))

G5 = ["DIATO", "DINO", "GREEN", "HAPTO", "PROKAR"]
EXTRA = ["PROCHLO"]
# Bandas de latitud (°N) aproximadas a las regiones del texto; ajústalas si usas
# la regionalización de Marín-Enríquez et al. (2024) u otra.
REGIONS = {"Alto Golfo": (30.0, 32.5), "Grandes Islas": (28.0, 30.0),
           "Golfo central": (25.5, 28.0), "Golfo sur": (23.0, 25.5), "Entrada": (19.0, 23.0)}
PERIODS = {"2002-2004": ("2002-07", "2004-12"), "2005-2009": ("2005", "2009"),
           "2010-2014": ("2010", "2014"), "2015-2019": ("2015", "2019"), "2020-2024": ("2020", "2024")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw/pft_golfo_california_2000_2024.nc")
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas")))
    ap.add_argument("--mask-npy", default=None, help="máscara booleana (lat,lon) precalculada, opcional")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    ds = xr.open_dataset(a.raw).sel(time=slice("2002-07-01", "2024-12-31"))
    if a.mask_npy:
        gulf = xr.DataArray(np.load(a.mask_npy), dims=["latitude", "longitude"],
                            coords={"latitude": ds.latitude, "longitude": ds.longitude})
    else:
        from config_gulf_california import get_gulf_of_california_filter
        gulf = get_gulf_of_california_filter(ds, use_shapefile=True)
    lat2d = xr.broadcast(ds.latitude, ds.longitude)[0]
    masks = {r: gulf & (lat2d >= lo) & (lat2d < hi) for r, (lo, hi) in REGIONS.items()}
    for r, m in masks.items():
        print(f"{r}: {int(m.sum())} píxeles")

    times = pd.DatetimeIndex(ds.time.values)
    rows = []
    for ym in times.to_period("M").unique():
        sel = ds.isel(time=np.where((times.year == ym.year) & (times.month == ym.month))[0])
        clim = {v: sel[v].mean("time") for v in G5 + EXTRA if v in sel}
        for r, m in masks.items():
            row = {"mes": ym.to_timestamp(), "region": r}
            for v, f in clim.items():
                row[v] = float(f.where(m).mean())
            rows.append(row)
        print(ym, end=" ", flush=True)
    mon = pd.DataFrame(rows)
    mon.to_csv(out / "regional_mensual.csv", index=False)

    comp = []
    for r, g in mon.groupby("region"):
        g = g.set_index("mes").sort_index()
        pct = g[G5].div(g[G5].sum(axis=1), axis=0) * 100
        for p, (a0, a1) in {"2002-2024": ("2002-07", "2024-12"), **PERIODS}.items():
            mean = g.loc[a0:a1, G5].mean()
            comp.append({"region": r, "periodo": p, "tipo": "ponderada_biomasa",
                         **(100 * mean / mean.sum()).round(1).to_dict()})
            comp.append({"region": r, "periodo": p, "tipo": "media_porcentajes",
                         **pct.loc[a0:a1].mean().round(1).to_dict()})
    comp = pd.DataFrame(comp)
    comp.to_csv(out / "regional_composicion.csv", index=False)
    print("\n", comp[comp.periodo == "2002-2024"].to_string(index=False))


if __name__ == "__main__":
    main()
