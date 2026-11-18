#!/usr/bin/env python3
"""
Descarga SST (temperatura superficial del mar) desde Copernicus Marine y la
remuestrea a la rejilla del NetCDF de PFT.

Producto: SST_GLO_SST_L4_REP_OBSERVATIONS_010_011 (OSTIA reprocesado, L4, 0.05°, diario)
Dataset:  METOFFICE-GLO-SST-L4-REP-OBS-SST
Variable: analysed_sst (K -> °C)

Salidas (data/raw y data/processed):
    sst_golfo_california_2000_2025.nc          SST diaria original (0.05°)
    sst_monthly_pft_grid_2000_2025.nc          SST mensual interpolada a la rejilla PFT

Uso:
    python download_sst_data.py            # descarga + remuestreo
    python download_sst_data.py --skip-download
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

import copernicusmarine
import xarray as xr

ROOT = Path(__file__).parent.parent.parent
PFT_FILE = ROOT / 'data' / 'raw' / 'pft_golfo_california_2000_2024.nc'
SST_RAW = ROOT / 'data' / 'raw' / 'sst_golfo_california_2000_2025.nc'
SST_MONTHLY = ROOT / 'data' / 'processed' / 'sst_monthly_pft_grid_2000_2025.nc'

DATASET_ID = 'METOFFICE-GLO-SST-L4-REP-OBS-SST'
START, END = '2000-01-01', '2025-12-31'
MARGIN = 0.1  # grados extra para que la interpolación no tenga bordes vacíos


def download_sst(grid):
    """Subset remoto (lazy) y escritura con netcdf4 (el writer h5netcdf de
    copernicusmarine.subset falla en este entorno)."""
    SST_RAW.parent.mkdir(parents=True, exist_ok=True)
    ds = copernicusmarine.open_dataset(
        dataset_id=DATASET_ID,
        variables=['analysed_sst'],
        minimum_longitude=float(grid.longitude.min()) - MARGIN,
        maximum_longitude=float(grid.longitude.max()) + MARGIN,
        minimum_latitude=float(grid.latitude.min()) - MARGIN,
        maximum_latitude=float(grid.latitude.max()) + MARGIN,
        start_datetime=START,
        end_datetime=END,
    )
    print(f'Descargando {dict(ds.sizes)} ...')
    ds.to_netcdf(SST_RAW, engine='netcdf4')


def regrid_monthly(grid):
    """Media mensual a 0.05° y luego interpolación bilineal a la rejilla PFT."""
    sst = xr.open_dataset(SST_RAW, engine='netcdf4', chunks={'time': 366})['analysed_sst'] - 273.15
    sst.attrs.update(units='degree_Celsius', long_name='Sea surface temperature (OSTIA L4)')
    monthly = sst.resample(time='1MS').mean(skipna=True)
    out = monthly.interp(latitude=grid.latitude, longitude=grid.longitude, method='linear')
    out = out.rename('SST').astype('float32')
    out['time'].attrs = {'standard_name': 'time', 'long_name': 'Time', 'axis': 'T'}
    out.attrs.update(
        units='degree_Celsius',
        long_name='Monthly mean sea surface temperature (OSTIA L4), regridded to the PFT grid',
        standard_name='sea_surface_temperature',
        source_variable='analysed_sst (kelvin, converted to degree_Celsius)',
        cell_methods='time: mean (calendar month)',
    )
    SST_MONTHLY.parent.mkdir(parents=True, exist_ok=True)
    ds = out.to_dataset()
    ds.attrs = {
        'title': 'Monthly sea surface temperature, Gulf of California, 2000-2025, on the PFT grid',
        'summary': ('Monthly means computed from the daily gap-free L4 OSTIA reprocessed SST '
                    '(0.05 deg) and bilinearly interpolated to the 1/24 deg grid of the CMEMS '
                    'plankton (PFT) product so both fields match point to point.'),
        'source': 'Copernicus Marine Service (CMEMS), product SST_GLO_SST_L4_REP_OBSERVATIONS_010_011, '
                  f'dataset {DATASET_ID}, version 202003, variable analysed_sst',
        'source_provider': 'UK Met Office (OSTIA reprocessed)',
        'source_resolution': 'daily, 0.05 deg x 0.05 deg, L4 (gap-free)',
        'processing_step_1': 'Daily analysed_sst converted from K to degC (K - 273.15).',
        'processing_step_2': ('Monthly mean per calendar month at 0.05 deg using all daily values '
                              '(xarray resample 1MS, mean, skipna=True); time stamp = first day of month.'),
        'processing_step_3': ('Bilinear interpolation (xarray interp, method=linear) from the 0.05 deg grid to '
                              'the latitude/longitude of the PFT product '
                              'cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D (432 x 360).'),
        'time_coverage_start': str(out.time.values[0])[:10],
        'time_coverage_end': str(out.time.values[-1])[:10],
        'note': 'L4 SST has no cloud gaps; mask with PFT coverage before comparing. NaN = land / no data.',
        'history': f'Created {datetime.now(timezone.utc):%Y-%m-%d} by src/pipeline/download_sst_data.py',
    }
    ds.to_netcdf(SST_MONTHLY)
    print(f'Guardado: {SST_MONTHLY}  dims={dict(out.sizes)}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-download', action='store_true')
    args = ap.parse_args()
    grid = xr.open_dataset(PFT_FILE, engine='netcdf4')[['latitude', 'longitude']]
    if not args.skip_download:
        download_sst(grid)
    regrid_monthly(grid)
