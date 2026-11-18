#!/usr/bin/env python3
"""
B2. Procedencia de data/processed/pft_monthly_statistics.nc: ¿polígono del shapefile o rectángulo?

Recalcula la media mensual de meses de prueba desde el NetCDF diario con el MISMO cálculo que
src/pipeline/preprocess_pft_data.py (da.where(mask, drop=True).mean('time') y luego media en
latitud y longitud), con dos máscaras de src/pipeline/config_gulf_california.py:
  - polígono:   get_gulf_of_california_filter_shapefile (regionmarinamx.shp)
  - rectángulo: get_gulf_of_california_filter_bbox (GULF_OF_CALIFORNIA_BOUNDS)
y compara ambos con el valor guardado en el .nc. Informa también los atributos del .nc.

Uso:  python3 manuscript/reanalysis/procedencia_mensual.py --raw data/raw/pft_golfo_california_2000_2024.nc \
          --nc data/processed/pft_monthly_statistics.nc --meses 2010-06 2003-01 2020-08
Salida: manuscript/reanalysis/salidas/procedencia/procedencia_mensual.csv y resumen.md
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

VARS = ["CHL", "DIATO", "GREEN"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw/pft_golfo_california_2000_2024.nc")
    ap.add_argument("--nc", default="data/processed/pft_monthly_statistics.nc")
    ap.add_argument("--meses", nargs="+", default=["2010-06"])
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas") / "procedencia"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(a.raw)
    nc = xr.open_dataset(a.nc)
    tnc = pd.DatetimeIndex(nc.time.values).to_period("M")
    masks = {"poligono": np.asarray(cg.get_gulf_of_california_filter_shapefile(ds)),
             "rectangulo": np.asarray(cg.get_gulf_of_california_filter_bbox(ds))}
    masks = {k: xr.DataArray(m, dims=["latitude", "longitude"], coords={"latitude": ds.latitude, "longitude": ds.longitude})
             for k, m in masks.items()}
    npix = {k: int(m.sum()) for k, m in masks.items()}
    times = pd.DatetimeIndex(ds.time.values)
    rows = []
    for mes in a.meses:
        p = pd.Period(mes, "M")
        idx = np.where((times.year == p.year) & (times.month == p.month))[0]
        for v in VARS:
            da = ds[v].isel(time=idx)
            rec = {"mes": mes, "variable": v, "valor_nc": float(nc[f"{v}_mean"].values[list(tnc).index(p)])}
            for k, m in masks.items():
                rec[f"media_{k}"] = float(da.where(m, drop=True).mean("time").mean(["latitude", "longitude"]).values)
                rec[f"dif_{k}"] = rec[f"media_{k}"] - rec["valor_nc"]
                rec[f"dif_rel_{k}_pct"] = 100 * rec[f"dif_{k}"] / rec["valor_nc"]
            rows.append(rec)
    T = pd.DataFrame(rows)
    T.to_csv(out / "procedencia_mensual.csv", index=False)
    with open(out / "resumen.md", "w") as f:
        f.write("# Procedencia de pft_monthly_statistics.nc\n\n## Atributos del .nc\n\n")
        for k, v in nc.attrs.items():
            f.write(f"- `{k}`: {v}\n")
        f.write(f"\n## Máscaras\n\n- polígono (`{cg.SHAPEFILE_PATH.name}`): {npix['poligono']} píxeles\n"
                f"- rectángulo (`GULF_OF_CALIFORNIA_BOUNDS` = {cg.GULF_OF_CALIFORNIA_BOUNDS}): {npix['rectangulo']} píxeles\n"
                f"- malla completa: {ds.sizes['latitude'] * ds.sizes['longitude']} píxeles\n\n## Comparación\n\n")
        try:
            f.write(T.to_markdown(index=False, floatfmt=".6g") + "\n")
        except ImportError:
            f.write(T.to_string(index=False) + "\n")
    print((out / "resumen.md").read_text())


if __name__ == "__main__":
    main()
