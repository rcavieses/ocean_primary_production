#!/usr/bin/env python3
"""
Publication-quality figures for quinquennial (5-year) comparison of phytoplankton
functional type (PFT) concentration variables across seasons.

Seasons defined as:
- Spring (MAM): March, April, May
- Summer (JJA): June, July, August
- Autumn (SON): September, October, November
- Winter (DJF): December, January, February

Logarithmic scale is used to highlight relative differences between periods.
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import os
os.environ['MPLBACKEND'] = 'Agg'

import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import LogNorm
import numpy as np
from pathlib import Path
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd

# ── Publication-quality rcParams ─────────────────────────────────────────────
plt.rcParams.update({
    'font.family':        'serif',
    'font.serif':         ['Times New Roman', 'DejaVu Serif'],
    'font.size':          10,
    'axes.titlesize':     11,
    'axes.labelsize':     10,
    'xtick.labelsize':    9,
    'ytick.labelsize':    9,
    'legend.fontsize':    9,
    'figure.dpi':         300,
    'savefig.dpi':        600,
    'axes.linewidth':     0.8,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'xtick.direction':    'out',
    'ytick.direction':    'out',
    'xtick.major.width':  0.8,
    'ytick.major.width':  0.8,
    'lines.linewidth':    1.5,
    'patch.linewidth':    0.8,
    'pdf.fonttype':       42,   # embeds fonts in PDF (journal requirement)
    'ps.fonttype':        42,
})

# ── Paths ─────────────────────────────────────────────────────────────────────
data_file  = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'pft_golfo_california_2000_2024.nc'
output_dir = Path(__file__).parent.parent.parent / 'results' / 'satellite' / 'figures' / 'seasonal_analysis_publication'
output_dir.mkdir(parents=True, exist_ok=True)
maps_output_dir = output_dir / 'maps'
maps_output_dir.mkdir(exist_ok=True)

# ── Quinquennial periods ──────────────────────────────────────────────────────
periods = [
    ('2000–2004', '2000-01-01', '2004-12-31'),
    ('2005–2009', '2005-01-01', '2009-12-31'),
    ('2010–2014', '2010-01-01', '2014-12-31'),
    ('2015–2019', '2015-01-01', '2019-12-31'),
    ('2020–2024', '2020-01-01', '2024-12-31'),
]

# ── Seasons (month numbers) ────────────────────────────────────────────────────
seasons = {
    'Spring (MAM)': [3, 4, 5],
    'Summer (JJA)': [6, 7, 8],
    'Autumn (SON)': [9, 10, 11],
    'Winter (DJF)': [12, 1, 2],
}

# ── Variables ─────────────────────────────────────────────────────────────────
variables = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO',
             'PICO', 'PROCHLO', 'PROKAR']

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

# ── Color palettes ─────────────────────────────────────────────────────────────
# Colorblind-friendly palette for quinquennial periods
PERIOD_COLORS  = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7']
SEASON_COLORS  = {
    'Spring (MAM)': '#4CAF50',
    'Summer (JJA)': '#F44336',
    'Autumn (SON)': '#FF9800',
    'Winter (DJF)': '#2196F3',
}
SEASON_MARKERS = {
    'Spring (MAM)': 'o',
    'Summer (JJA)': 's',
    'Autumn (SON)': '^',
    'Winter (DJF)': 'D',
}

# ── Helper functions ──────────────────────────────────────────────────────────
def get_seasonal_mean(data, season_months):
    return data.sel(time=data.time.dt.month.isin(season_months)).mean(dim='time')

def get_spatial_mean(data):
    return float(data.mean().values)

def _log_formatter(x, pos):
    """Compact scientific notation for log-scale tick labels."""
    if x <= 0:
        return ''
    exp = int(np.floor(np.log10(x)))
    coeff = x / 10**exp
    if abs(coeff - 1.0) < 1e-9:
        return r'$10^{%d}$' % exp
    return r'$%.1f{\times}10^{%d}$' % (coeff, exp)

def apply_log_scale(ax, values_list):
    """Set log y-scale, hide minor grid noise, add major grid."""
    all_vals = [v for v in np.concatenate(values_list) if v > 0]
    if not all_vals:
        return
    ax.set_yscale('log')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(_log_formatter))
    ax.yaxis.set_minor_formatter(ticker.NullFormatter())
    ax.grid(axis='y', which='major', alpha=0.25, linestyle='--', linewidth=0.6)
    ax.grid(axis='y', which='minor', alpha=0.0)
    ax.set_axisbelow(True)

# ── Load dataset and shapefile ────────────────────────────────────────────────
print("Loading dataset...")
ds = xr.open_dataset(data_file)
period_names = [p[0] for p in periods]

# Load shapefile for study area boundary
shapefile_path = Path(__file__).parent.parent.parent / 'results' / 'satellite' / 'figures' / 'shapefiles' / 'regionmarinamx.shp'
shapefile_gdf = gpd.read_file(shapefile_path) if shapefile_path.exists() else None
if shapefile_gdf is None:
    print("WARNING: Shapefile not found, study area boundary will not be drawn.")

# ── Main loop ─────────────────────────────────────────────────────────────────
for var in variables:
    if var not in ds:
        print(f"  [SKIP] {var} not found in dataset.")
        continue

    print(f"\nProcessing {var} ({var_descriptions[var]})...")

    seasonal_data = {s: [] for s in seasons}
    seasonal_maps  = {s: [] for s in seasons}

    for period_name, start_date, end_date in periods:
        print(f"  - {period_name} ...", end=' ', flush=True)
        data_period = ds[var].sel(time=slice(start_date, end_date))
        for season, months in seasons.items():
            smap  = get_seasonal_mean(data_period, months)
            smean = get_spatial_mean(smap)
            seasonal_data[season].append(smean)
            seasonal_maps[season].append(smap)
        print("done")

    # ── Figure 1: Bar chart (2×2, one panel per season) ──────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.5))   # ~double-column width
    axes = axes.flatten()
    x_pos = np.arange(len(period_names))

    for ax, (season, values) in zip(axes, seasonal_data.items()):
        bars = ax.bar(x_pos, values, color=PERIOD_COLORS, alpha=0.85,
                      edgecolor='white', linewidth=0.6, width=0.65)

        # Value labels above each bar
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2.,
                    v * 1.04,           # 4 % above bar top in log space
                    f'{v:.3f}',
                    ha='center', va='bottom', fontsize=6.5, color='#333333')

        apply_log_scale(ax, [values])

        ax.set_title(season, fontsize=10, fontweight='bold', pad=4)
        ax.set_ylabel(f'Concentration ({units[var]})', fontsize=9)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(period_names, rotation=40, ha='right', fontsize=8)

    # Legend proxy for periods
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=c, edgecolor='white', label=n)
               for c, n in zip(PERIOD_COLORS, period_names)]
    fig.legend(handles=handles, title='Period', title_fontsize=8,
               fontsize=8, loc='lower center', ncol=5,
               bbox_to_anchor=(0.5, -0.04), frameon=False)

    fig.suptitle(
        f'{var_descriptions[var]}\n'
        'Seasonal Mean Concentration by Quinquennial Period (Gulf of California, 2000–2024)',
        fontsize=10, fontweight='bold', y=1.01)

    plt.tight_layout(rect=[0, 0.05, 1, 1])

    out_png = output_dir / f'{var}_seasonal_quinquennial_comparison.png'
    out_pdf = output_dir / f'{var}_seasonal_quinquennial_comparison.pdf'
    plt.savefig(out_png, dpi=600, bbox_inches='tight')
    plt.savefig(out_pdf, bbox_inches='tight')
    print(f"  - Saved: {out_png.name}  |  {out_pdf.name}")
    plt.close()

    # ── Figure 2: Line plot (all seasons on one axes) ─────────────────────────
    fig, ax = plt.subplots(figsize=(5.5, 3.8))

    for season, values in seasonal_data.items():
        ax.plot(period_names, values,
                marker=SEASON_MARKERS[season], linewidth=1.5, markersize=5,
                label=season, color=SEASON_COLORS[season], alpha=0.9)

    apply_log_scale(ax, list(seasonal_data.values()))

    ax.set_xlabel('Quinquennial Period', fontsize=10)
    ax.set_ylabel(f'Concentration ({units[var]})', fontsize=10)
    ax.set_title(f'{var_descriptions[var]} – Seasonal Trends (Gulf of California, 2000–2024)',
                 fontsize=10, fontweight='bold', pad=6)
    ax.legend(fontsize=8, loc='best', framealpha=0.85, edgecolor='#cccccc')
    plt.xticks(rotation=35, ha='right', fontsize=9)
    plt.tight_layout()

    out_png2 = output_dir / f'{var}_seasonal_trends.png'
    out_pdf2 = output_dir / f'{var}_seasonal_trends.pdf'
    plt.savefig(out_png2, dpi=600, bbox_inches='tight')
    plt.savefig(out_pdf2, bbox_inches='tight')
    print(f"  - Saved: {out_png2.name}  |  {out_pdf2.name}")
    plt.close()

    # ── Figure 3: Spatial maps per season (log scale) ─────────────────────────
    print(f"  - Generating spatial comparison maps for {var}...")

    for season in seasons:
        fig, axes_map = plt.subplots(
            1, 5, figsize=(16, 3.8),
            subplot_kw={'projection': ccrs.PlateCarree()})

        all_data = np.concatenate([m.values.flatten() for m in seasonal_maps[season]])
        all_data = all_data[~np.isnan(all_data) & (all_data > 0)]
        vmin, vmax = (all_data.min(), all_data.max()) if len(all_data) else (1e-4, 1)

        for ax_m, period_name, data_map in zip(axes_map, period_names, seasonal_maps[season]):
            ax_m.coastlines(resolution='10m', linewidth=0.5)
            ax_m.add_feature(cfeature.LAND, facecolor='#d5d5d5', edgecolor='#888888',
                             linewidth=0.4)
            im = data_map.plot(
                ax=ax_m,
                transform=ccrs.PlateCarree(),
                cmap='viridis',
                norm=LogNorm(vmin=vmin, vmax=vmax),
                add_colorbar=False)

            # Add study area boundary from shapefile
            if shapefile_gdf is not None:
                shapefile_gdf.boundary.plot(ax=ax_m, transform=ccrs.PlateCarree(),
                                             edgecolor='#000000', facecolor='none',
                                             linewidth=1.0, linestyle='-', zorder=10)

            ax_m.set_title(period_name, fontsize=8, fontweight='bold', pad=3)

        cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.70])
        cb = fig.colorbar(im, cax=cbar_ax)
        cb.set_label(f'{units[var]} (log scale)', fontsize=8)
        cb.ax.tick_params(labelsize=7)

        season_label = season.split(' ')[0]   # e.g. "Spring"
        fig.suptitle(
            f'{var_descriptions[var]} – {season}\n'
            'Quinquennial Period Comparison (Gulf of California)',
            fontsize=9, fontweight='bold', y=1.02)

        plt.subplots_adjust(left=0.02, right=0.90, top=0.88, bottom=0.05, wspace=0.20)

        out_map = maps_output_dir / f'{var}_{season_label}_comparison_map_log.png'
        plt.savefig(out_map, dpi=600, bbox_inches='tight')
        print(f"  - Saved: {out_map.name}")
        plt.close()

# ── Close dataset ─────────────────────────────────────────────────────────────
ds.close()

print("\nAll publication-quality figures have been generated successfully.")
print(f"Output directory: {output_dir}")
