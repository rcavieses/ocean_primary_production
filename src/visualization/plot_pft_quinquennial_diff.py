#!/usr/bin/env python3
"""
Publication-quality spatial difference maps for quinquennial (5-year) periods.

For each PFT variable, produces two figure types per comparison pair
(2020-2024 vs. each earlier period):

  Fig A – Absolute difference  : Δ = recent − baseline  (mg m⁻³)
  Fig B – Percentage change     : %Δ = (recent − baseline) / baseline × 100

Both use diverging colormaps; Fig B uses a symmetric-log stretch to
exaggerate small but ecologically meaningful differences.

Comparisons shown:
  2020–2024 vs. 2000–2004
  2020–2024 vs. 2005–2009
  2020–2024 vs. 2010–2014
  2020–2024 vs. 2015–2019
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import sys
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import geopandas as gpd

sys.path.insert(0, str(Path(__file__).parent.parent / 'pipeline'))
from config_gulf_california import (GULF_OF_CALIFORNIA_EXTENT,
                                    get_gulf_of_california_filter)

# ── Publication-quality rcParams ──────────────────────────────────────────────
plt.rcParams.update({
    'font.family':       'serif',
    'font.serif':        ['Times New Roman', 'DejaVu Serif'],
    'font.size':         9,
    'axes.titlesize':    9,
    'axes.labelsize':    8,
    'xtick.labelsize':   7,
    'ytick.labelsize':   7,
    'legend.fontsize':   8,
    'figure.dpi':        300,
    'savefig.dpi':       600,
    'axes.linewidth':    0.7,
    'xtick.major.width': 0.7,
    'ytick.major.width': 0.7,
    'pdf.fonttype':      42,
    'ps.fonttype':       42,
})

# ── Paths ─────────────────────────────────────────────────────────────────────
data_file  = (Path(__file__).parent.parent.parent
              / 'data' / 'raw' / 'pft_golfo_california_2000_2024.nc')
output_dir = (Path(__file__).parent.parent.parent
              / 'results' / 'satellite' / 'figures' / 'quinquennial_diff_publication')
output_dir.mkdir(parents=True, exist_ok=True)

# ── Quinquennial periods ──────────────────────────────────────────────────────
periods = [
    ('2000–2004', '2000-01-01', '2004-12-31'),
    ('2005–2009', '2005-01-01', '2009-12-31'),
    ('2010–2014', '2010-01-01', '2014-12-31'),
    ('2015–2019', '2015-01-01', '2019-12-31'),
    ('2020–2024', '2020-01-01', '2024-12-31'),
]

# ── Variables ─────────────────────────────────────────────────────────────────
variables = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO',
             'MICRO', 'NANO', 'PICO', 'PROCHLO', 'PROKAR']

var_descriptions = {
    'CHL':     'Total Chlorophyll-a',
    'DIATO':   'Diatoms',
    'DINO':    'Dinoflagellates',
    'GREEN':   'Green Algae',
    'HAPTO':   'Haptophytes',
    'MICRO':   'Microphytoplankton',
    'NANO':    'Nanophytoplankton',
    'PICO':    'Picophytoplankton',
    'PROCHLO': 'Prochlorococcus',
    'PROKAR':  'Prokaryotes',
}
units = {v: 'mg m⁻³' for v in variables}

# ── Colormaps ─────────────────────────────────────────────────────────────────
CMAP_DIV = 'RdBu_r'   # red = increase, blue = decrease


# ── Helpers ───────────────────────────────────────────────────────────────────
def quinquennial_mean(ds, var, start, end, mask):
    data = ds[var].sel(time=slice(start, end))
    return data.where(mask, drop=False).mean(dim='time')


def symmetric_vmax(arr_list, pct=99):
    """Return a symmetric ±vmax at the given percentile of absolute values."""
    combined = np.concatenate([a.values.ravel() for a in arr_list])
    valid = combined[np.isfinite(combined)]
    if len(valid) == 0:
        return 1.0
    vmax = np.nanpercentile(np.abs(valid), pct)
    return max(vmax, 1e-10)


def _add_map_features(ax, extent, shapefile_gdf=None):
    ax.coastlines(resolution='10m', linewidth=0.5, color='#444444')
    ax.add_feature(cfeature.LAND, facecolor='#d0d0d0', edgecolor='#888888',
                   linewidth=0.4, zorder=2)

    # Add study area boundary from shapefile
    if shapefile_gdf is not None:
        shapefile_gdf.boundary.plot(ax=ax, transform=ccrs.PlateCarree(),
                                     edgecolor='#000000', facecolor='none',
                                     linewidth=1.2, linestyle='-', zorder=10)

    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color='gray',
                      alpha=0.5, linestyle='--')
    gl.top_labels   = False
    gl.right_labels  = False
    gl.xlabel_style  = {'size': 6}
    gl.ylabel_style  = {'size': 6}
    ax.set_extent(extent, crs=ccrs.PlateCarree())


def save_fig(fig, path_stem):
    fig.savefig(str(path_stem) + '.png', dpi=600, bbox_inches='tight')
    fig.savefig(str(path_stem) + '.pdf',           bbox_inches='tight')
    print(f"  → {path_stem.name}.png  |  .pdf")


# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading dataset...")
ds   = xr.open_dataset(data_file)
mask = get_gulf_of_california_filter(ds, use_shapefile=True)

# Load shapefile for study area boundary
shapefile_path = (Path(__file__).parent.parent.parent
                  / 'results' / 'satellite' / 'figures' / 'shapefiles' / 'regionmarinamx.shp')
shapefile_gdf = gpd.read_file(shapefile_path) if shapefile_path.exists() else None
if shapefile_gdf is None:
    print("WARNING: Shapefile not found, study area boundary will not be drawn.")

ref_name, ref_start, ref_end = periods[-1]
comparisons = periods[:-1]   # 4 baseline periods

# ── Main loop ─────────────────────────────────────────────────────────────────
for var in variables:
    if var not in ds:
        print(f"  [SKIP] {var} not found.")
        continue

    print(f"\nProcessing {var}  ({var_descriptions[var]}) ...")

    # Compute quinquennial means
    ref_mean = quinquennial_mean(ds, var, ref_start, ref_end, mask)

    base_means, abs_diffs, pct_diffs, labels = [], [], [], []
    for bname, bstart, bend in comparisons:
        bm   = quinquennial_mean(ds, var, bstart, bend, mask)
        adiff = ref_mean - bm
        pdiff = (ref_mean - bm) / bm * 100.0
        base_means.append(bm)
        abs_diffs.append(adiff)
        pct_diffs.append(pdiff)
        labels.append(f'{ref_name}\n− {bname}')
        print(f"  - Difference computed: {ref_name} vs {bname}")

    n = len(comparisons)   # 4

    # ── Figure A: Absolute differences ───────────────────────────────────────
    vmax_abs = symmetric_vmax(abs_diffs)
    norm_abs = mcolors.TwoSlopeNorm(vmin=-vmax_abs, vcenter=0, vmax=vmax_abs)

    fig_a, axes_a = plt.subplots(
        1, n, figsize=(4.2 * n, 4.2),
        subplot_kw={'projection': ccrs.PlateCarree()})

    for ax, diff, label in zip(axes_a, abs_diffs, labels):
        _add_map_features(ax, GULF_OF_CALIFORNIA_EXTENT, shapefile_gdf)
        im_a = diff.plot(ax=ax, transform=ccrs.PlateCarree(),
                         cmap=CMAP_DIV, norm=norm_abs,
                         add_colorbar=False, zorder=1)
        ax.set_title(label, fontsize=8, fontweight='bold', pad=4,
                     linespacing=1.3)

    # Shared colorbar
    cbar_ax_a = fig_a.add_axes([0.92, 0.18, 0.015, 0.64])
    cb_a = fig_a.colorbar(im_a, cax=cbar_ax_a, extend='both')
    cb_a.set_label(f'Δ Concentration ({units[var]})', fontsize=8)
    cb_a.ax.tick_params(labelsize=7)

    fig_a.suptitle(
        f'{var_descriptions[var]} – Absolute Concentration Change\n'
        f'Reference Period: {ref_name} (Gulf of California)',
        fontsize=9, fontweight='bold', y=1.02)

    plt.subplots_adjust(left=0.03, right=0.90, top=0.88,
                        bottom=0.06, wspace=0.20)
    save_fig(fig_a, output_dir / f'{var}_abs_diff')
    plt.close(fig_a)

    # ── Figure B: Percentage change (symlog stretch) ──────────────────────────
    vmax_pct = symmetric_vmax(pct_diffs, pct=98)

    # Symmetric log threshold: values between ±linthresh rendered linearly
    # (avoids log(0)); everything outside is log-stretched
    linthresh = max(1.0, vmax_pct * 0.01)   # ~1 % linear region
    norm_pct = mcolors.SymLogNorm(
        linthresh=linthresh,
        linscale=0.5,
        vmin=-vmax_pct, vmax=vmax_pct,
        base=10)

    fig_b, axes_b = plt.subplots(
        1, n, figsize=(4.2 * n, 4.2),
        subplot_kw={'projection': ccrs.PlateCarree()})

    for ax, pdiff, label in zip(axes_b, pct_diffs, labels):
        _add_map_features(ax, GULF_OF_CALIFORNIA_EXTENT, shapefile_gdf)
        im_b = pdiff.plot(ax=ax, transform=ccrs.PlateCarree(),
                          cmap=CMAP_DIV, norm=norm_pct,
                          add_colorbar=False, zorder=1)
        ax.set_title(label, fontsize=8, fontweight='bold', pad=4,
                     linespacing=1.3)

    # Colorbar with symlog ticks
    cbar_ax_b = fig_b.add_axes([0.92, 0.18, 0.015, 0.64])
    cb_b = fig_b.colorbar(im_b, cax=cbar_ax_b, extend='both')
    cb_b.set_label('Change (%)', fontsize=8)
    cb_b.ax.tick_params(labelsize=7)

    # Custom symlog tick positions for readability
    decade_ticks = []
    for exp in range(0, int(np.log10(vmax_pct)) + 2):
        for sign in [-1, 1]:
            val = sign * 10**exp
            if -vmax_pct <= val <= vmax_pct:
                decade_ticks.append(val)
    decade_ticks = sorted(set(decade_ticks))
    cb_b.set_ticks(decade_ticks)
    cb_b.set_ticklabels([f'{t:+.0f}%' for t in decade_ticks])

    fig_b.suptitle(
        f'{var_descriptions[var]} – Percentage Concentration Change (log-stretched)\n'
        f'Reference Period: {ref_name} (Gulf of California)',
        fontsize=9, fontweight='bold', y=1.02)

    plt.subplots_adjust(left=0.03, right=0.90, top=0.88,
                        bottom=0.06, wspace=0.20)
    save_fig(fig_b, output_dir / f'{var}_pct_diff')
    plt.close(fig_b)

# ── Done ──────────────────────────────────────────────────────────────────────
ds.close()
print("\nAll publication-quality difference maps generated successfully.")
print(f"Output directory: {output_dir}")
