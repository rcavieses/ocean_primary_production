#!/usr/bin/env python3
"""
Prepara la producción primaria (grupos funcionales de fitoplancton, PFT) del
Golfo de California como covariable ambiental para GLOSSA.

Entrada:  data/raw/pft_golfo_california_2000_2024.nc
          (diario, 2000-2024, 432x360, GlobColour/Copernicus
          cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D)
Salida:   data/processed/glossa_primary_production_monthly_golfo_california.nc
          (mensual, mismo grid espacial (time, latitude, longitude),
          recortado al polígono del Golfo de California, sin variables de
          incertidumbre ni flags)

Nota: el producto GlobColour PFT reporta concentración de clorofila-a por
grupo funcional (mg m-3), no producción primaria neta en unidades de carbono
(mg C m-2 día-1). Se usa como proxy estándar de productividad/biomasa
fitoplanctónica para modelos de distribución de especies (SDM).

Uso:
    python prepare_glossa_environmental_data.py
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent))
from config_gulf_california import get_gulf_of_california_filter

BASE_DIR = Path(__file__).parent.parent.parent
RAW_FILE = BASE_DIR / "data" / "raw" / "pft_golfo_california_2000_2024.nc"
OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "glossa_primary_production_monthly_golfo_california.nc"
)

VARIABLES = [
    "CHL",
    "DIATO",
    "DINO",
    "GREEN",
    "HAPTO",
    "MICRO",
    "NANO",
    "PICO",
    "PROCHLO",
    "PROKAR",
]

TIME_CHUNK = 30  # días por chunk dask, mantiene el uso de memoria bajo


def main():
    print("=" * 70)
    print("PREPARANDO PRODUCCIÓN PRIMARIA (PFT) PARA GLOSSA")
    print("=" * 70)

    print(f"\nAbriendo {RAW_FILE} (dask, chunk time={TIME_CHUNK})...")
    ds = xr.open_dataset(RAW_FILE, chunks={"time": TIME_CHUNK})
    ds = ds[VARIABLES]

    print("Aplicando máscara del polígono del Golfo de California...")
    mask = get_gulf_of_california_filter(ds, use_shapefile=True)
    ds = ds.where(mask)

    print("Recalculando promedios mensuales (esto puede tardar varios minutos)...")
    ds_monthly = ds.resample(time="1MS").mean(skipna=True)
    ds_monthly = ds_monthly.astype("float32")

    # Metadatos CF + contexto GLOSSA
    for var in VARIABLES:
        ds_monthly[var].attrs.update(
            {
                "units": "mg m-3",
                "long_name": ds[var].attrs.get("long_name", var),
                "cell_methods": "time: mean (daily obs aggregated to monthly)",
            }
        )

    ds_monthly.attrs.update(
        {
            "title": "Producción primaria (PFT) mensual - Golfo de California",
            "description": (
                "Concentración de clorofila-a por grupo funcional de "
                "fitoplancton (proxy de producción primaria), agregada "
                "mensualmente y recortada al polígono del Golfo de "
                "California. Preparado como covariable ambiental para "
                "modelos de distribución de especies (GLOSSA)."
            ),
            "spatial_filter": "Shapefile polygon filter (Golfo de California)",
            "source_dataset": "cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D",
            "source_file": str(RAW_FILE),
            "variables": ", ".join(VARIABLES),
            "grid": "regular lat/lon, ~4km, CRS EPSG:4326",
            "temporal_resolution": "monthly (1MS)",
            "temporal_coverage": "2000-01 to 2024-12",
            "processed_date": pd.Timestamp.now().isoformat(),
            "conventions": "CF-1.8",
        }
    )

    encoding = {
        var: {"zlib": True, "complevel": 4, "_FillValue": np.float32(np.nan)}
        for var in VARIABLES
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nEscribiendo {OUTPUT_FILE} ...")
    ds_monthly.to_netcdf(OUTPUT_FILE, mode="w", engine="netcdf4", encoding=encoding)

    print("\n" + "=" * 70)
    print("COMPLETADO")
    print("=" * 70)
    print(f"Archivo de salida: {OUTPUT_FILE}")
    print(f"Tamaño: {OUTPUT_FILE.stat().st_size / (1024 ** 2):.1f} MB")
    print(f"Dimensiones: {dict(ds_monthly.sizes)}")

    ds.close()
    ds_monthly.close()


if __name__ == "__main__":
    main()
