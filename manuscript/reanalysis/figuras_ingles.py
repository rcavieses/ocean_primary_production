#!/usr/bin/env python3
"""
Figures 1-6 of the manuscript in English, publication quality (300 dpi PNG and TIFF + vector PDF).

Same data and design as the Spanish figures inserted in the manuscript (polygon series):
  Fig. 1  Study area, analysis polygon, download box and latitude-band limits (REGIONS).
  Fig. 2  Relative composition: 5 groups and size classes (data/processed/pft_monthly_statistics_poligono.nc);
          Prochlorococcus/prokaryotes ratio with the Pettitt break (salidas/poligono/serie_cuenca/escalones.csv).
  Fig. 3  Regional composition by latitude band (salidas/regional_composicion.csv).
  Fig. 4  Five-year means +- 1 SD (ddof=0) from the polygon series.
  Fig. 5  2020-2024 minus each previous five-year period, per pixel, CHL and DIATO, polygon mask, from the
          daily NetCDF (same calculation as src/visualization/plot_pft_quinquennial_diff.py; colour scale =
          99th percentile of |delta| over the four panels of each variable). Cached in <out>/cache_fig5.npz.
  Fig. 6  Diatoms: STL (stl_recortado.stl_trimmed) and high-biomass HMM regime of the best maximum-likelihood
          solution (salidas/poligono/hmm/estados.csv, column alto_mejor).

Usage:  python3 manuscript/reanalysis/figuras_ingles.py --nc data/processed/pft_monthly_statistics_poligono.nc \
            --raw data/raw/pft_golfo_california_2000_2024.nc [--figs 1 2 3 4 5 6]
Output: manuscript/reanalysis/salidas/figuras_ingles/FigN_*.{png,tif,pdf}
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "src" / "pipeline"))
from composicion_regional import REGIONS  # noqa: E402

MM = 1 / 25.4
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
G5 = ["DIATO", "DINO", "GREEN", "HAPTO", "PROKAR"]
COL = {"DIATO": "#2a78d6", "DINO": "#eb6834", "GREEN": "#1baf7a", "HAPTO": "#eda100", "PROKAR": "#008300"}
NAME = {"DIATO": "Diatoms", "DINO": "Dinoflagellates", "GREEN": "Green algae", "HAPTO": "Haptophytes",
        "PROKAR": "Prokaryotes"}
SIZES = [("MICRO", "Micro (>20 µm)", "#2a78d6"), ("NANO", "Nano (2–20 µm)", "#eda100"), ("PICO", "Pico (<2 µm)", "#1baf7a")]
REG_EN = {"Alto Golfo": "Upper Gulf", "Grandes Islas": "Midriff Islands", "Golfo central": "Central Gulf",
          "Golfo sur": "Southern Gulf", "Entrada": "Entrance"}
UNIT = "mg m$^{-3}$"

plt.rcParams.update({
    "font.family": "Nimbus Sans", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "mathtext.default": "regular",
    "mathtext.fontset": "custom", "mathtext.rm": "Nimbus Sans", "mathtext.it": "Nimbus Sans:italic",
    "mathtext.bf": "Nimbus Sans:bold", "mathtext.sf": "Nimbus Sans",
    "pdf.fonttype": 42, "ps.fonttype": 42, "lines.linewidth": 1.0, "axes.titlelocation": "left",
})


def save(fig, out, name):
    from PIL import Image
    for ext in ("png", "pdf"):
        fig.savefig(out / f"{name}.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.03, facecolor="white")
    plt.close(fig)
    im = Image.open(out / f"{name}.png").convert("RGB")          # sin canal alfa (algunas revistas lo rechazan)
    im.save(out / f"{name}.png", dpi=(300, 300))
    im.save(out / f"{name}.tif", compression="tiff_lzw", dpi=(300, 300))
    print(f"{name}: {im.size[0]}x{im.size[1]} px = {im.size[0] / 300 * 25.4:.0f} x {im.size[1] / 300 * 25.4:.0f} mm at 300 dpi")


def letter(ax, s, x=-0.09, y=1.0):
    ax.text(x, y, f"({s})", transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="right", color=INK)


def load_monthly(nc):
    ds = xr.open_dataset(nc)
    t = pd.DatetimeIndex(ds.time.values).to_period("M").to_timestamp()
    return pd.DataFrame({v[:-5]: ds[v].values for v in ds.data_vars if v.endswith("_mean")}, index=t)


def gulf_rings():
    import shapefile
    sf = shapefile.Reader(str(ROOT / "results" / "satellite" / "figures" / "shapefiles" / "regionmarinamx.shp"))
    shp = sf.shapes()[0]
    parts = list(shp.parts) + [len(shp.points)]
    return [np.array(shp.points[parts[i]:parts[i + 1]]) for i in range(len(parts) - 1)]


# --------------------------------------------------------------------------------------------- Fig. 1
def fig1(out):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
    from shapely.geometry import LineString, Polygon
    pc = ccrs.PlateCarree()
    fig = plt.figure(figsize=(120 * MM, 112 * MM))
    ax = plt.axes(projection=pc)
    ax.set_extent([-118, -101, 17.5, 33.5], crs=pc)
    ax.add_feature(cfeature.LAND.with_scale("10m"), facecolor="#e9e8e4", edgecolor="none")
    ax.add_feature(cfeature.COASTLINE.with_scale("10m"), linewidth=0.4, edgecolor=INK2)
    ax.add_feature(cfeature.BORDERS.with_scale("10m"), linewidth=0.35, edgecolor="#a5a4a0")
    rings = gulf_rings()
    for r in rings:
        ax.fill(r[:, 0], r[:, 1], facecolor="#2a78d6", alpha=0.28, edgecolor="#1c5aa6", linewidth=0.8, transform=pc, zorder=3)
    ax.add_patch(mpatches.Rectangle((-117, 18), 15, 15, fill=False, edgecolor=INK, linestyle="--", linewidth=0.8,
                                    transform=pc, zorder=4))
    ax.text(-116.8, 18.3, "Download box (18°–33° N, 117°–102° W)", fontsize=6.5, color=INK, transform=pc)
    gulf = [Polygon(r).buffer(0) for r in rings]
    for lat in sorted({x for lohi in REGIONS.values() for x in lohi}):
        east = None
        for p in gulf:
            seg = LineString([(-118, lat), (-101, lat)]).intersection(p)
            for g in getattr(seg, "geoms", [seg]):
                if g.is_empty or g.geom_type != "LineString":
                    continue
                xs, ys = g.xy
                ax.plot(xs, ys, color="#a3341b", lw=0.9, ls=(0, (4, 2)), transform=pc, zorder=4)
                east = max(xs) if east is None else max(east, max(xs))
        if east is not None:
            ax.text(east + 0.2, lat, f"{lat:g}° N", fontsize=6, color="#a3341b", va="center", transform=pc, zorder=5,
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8))
    for x, y, t in [(-114.4, 31.2, "Upper Gulf"), (-114.2, 29.25, "Midriff Islands"), (-111.4, 27.0, "Central Gulf"),
                    (-108.9, 24.4, "Southern Gulf"), (-108.9, 21.3, "Entrance")]:
        ax.text(x, y, t, fontsize=6.8, color=INK, transform=pc, zorder=5,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
    for x, y, t, ha in [(-109.9, 22.85, "Cabo San Lucas", "right"), (-105.6, 20.4, "Cabo Corrientes", "left")]:
        ax.plot(x, y, "o", ms=2.5, color=INK, transform=pc, zorder=5)
        ax.text(x + (-0.25 if ha == "right" else 0.25), y - 0.35, t, fontsize=6.3, ha=ha, color=INK2, transform=pc, zorder=5)
    ax.text(-116.5, 24.5, "Pacific\nOcean", fontsize=7, color=INK2, style="italic", transform=pc)
    ax.text(-104.5, 28.6, "MEXICO", fontsize=6.5, color=INK2, transform=pc)
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color=GRID, xlocs=range(-117, -100, 3), ylocs=range(18, 34, 2))
    gl.top_labels = gl.right_labels = False
    gl.xformatter, gl.yformatter = LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    gl.xlabel_style = gl.ylabel_style = {"size": 6.5, "color": INK2}
    handles = [mpatches.Patch(facecolor="#2a78d6", alpha=0.28, edgecolor="#1c5aa6", label="Analysis domain (Gulf polygon)"),
               plt.Line2D([], [], color=INK, linestyle="--", lw=0.8, label="Download box"),
               plt.Line2D([], [], color="#a3341b", lw=0.9, ls=(0, (4, 2)), label="Region limits (latitude bands)")]
    ax.legend(handles=handles, loc="upper right", fontsize=6.5, frameon=True, framealpha=0.95, edgecolor=GRID)
    save(fig, out, "Fig1_study_area")


# --------------------------------------------------------------------------------------------- Fig. 2
def fig2(D, brk, out):
    d = D[G5 + ["PROCHLO"]].dropna()
    p5 = d[G5].div(d[G5].sum(axis=1), axis=0) * 100
    sz = D[[s[0] for s in SIZES]].dropna()
    szp = sz.div(sz.sum(axis=1), axis=0) * 100
    p5s = p5.rolling(12, center=True, min_periods=6).mean()
    szs = szp.rolling(12, center=True, min_periods=6).mean()
    ratio = d.PROCHLO / d.PROKAR
    fig, axes = plt.subplots(3, 1, figsize=(160 * MM, 165 * MM), sharex=True, gridspec_kw={"height_ratios": [1.25, 1, 0.95]})
    ax = axes[0]
    ax.stackplot(p5s.index, p5s[G5].T.values, colors=[COL[g] for g in G5], labels=[NAME[g] for g in G5],
                 edgecolor="white", linewidth=0.4)
    ax.set_title("Taxonomic groups (five-group partition, excluding $\\it{Prochlorococcus}$)")
    ax2 = axes[1]
    ax2.stackplot(szs.index, szs[[s[0] for s in SIZES]].T.values, colors=[s[2] for s in SIZES], labels=[s[1] for s in SIZES],
                  edgecolor="white", linewidth=0.4)
    ax2.set_title("Size classes")
    for a, tg in [(ax, "a"), (ax2, "b")]:
        a.set_ylim(0, 100); a.set_xlim(p5s.index.min(), p5s.index.max())
        a.set_ylabel("Relative contribution (%)")
        a.grid(axis="y", color=GRID, lw=0.4); a.set_axisbelow(True)
        a.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False, reverse=True)
        letter(a, tg)
    a = axes[2]
    a.set_yscale("log")
    a.plot(ratio.index, ratio.values, color="#2a78d6", lw=0.9)
    mus = []
    for a0, a1 in [(ratio.index.min(), brk - pd.Timedelta(days=1)), (brk, ratio.index.max())]:
        mu = ratio[a0:a1].mean(); mus.append(mu)
        a.hlines(mu, a0, a1, color=INK, lw=1.2)
    a.axhline(1, color="#e34948", lw=0.8, linestyle="--")
    a.axvline(brk, color=INK2, lw=0.7, linestyle=":")
    prev = brk - pd.DateOffset(months=1)
    a.legend(handles=[plt.Line2D([], [], color=INK, lw=1.2,
                                 label=f"Period mean: {mus[0]:.2f} (Jul 2002–{prev:%b %Y}), {mus[1]:.2f} ({brk:%b %Y}–Dec 2024)"),
                      plt.Line2D([], [], color="#e34948", lw=0.8, ls="--", label="Physical limit (subset = total)"),
                      plt.Line2D([], [], color=INK2, lw=0.7, ls=":", label=f"Break ({brk:%b %Y}, Pettitt test)")],
             loc="upper left", frameon=False, fontsize=6.3, handlelength=2.2)
    lo, hi = min(0.3, ratio.min() * 0.8), max(14, ratio.max() * 1.6)
    a.set_ylim(lo, hi)
    ticks = [t for t in [0.2, 0.5, 1, 2, 5, 10, 20] if lo <= t <= hi]
    a.set_yticks(ticks, [f"{t:g}" for t in ticks]); a.minorticks_off()
    a.set_ylabel("$\\it{Prochlorococcus}$ /\nprokaryotes")
    a.set_title("Monthly $\\it{Prochlorococcus}$/prokaryotes ratio")
    a.grid(axis="y", color=GRID, lw=0.4); a.set_axisbelow(True)
    a.set_xlabel("Year")
    letter(a, "c")
    fig.align_ylabels(axes)
    save(fig, out, "Fig2_relative_composition")


# --------------------------------------------------------------------------------------------- Fig. 3
def fig3(comp_csv, out):
    from composicion_regional import PERIODS
    comp = pd.read_csv(comp_csv)
    comp = comp[comp.tipo == "ponderada_biomasa"]
    order = list(REGIONS)
    fig = plt.figure(figsize=(174 * MM, 160 * MM))
    gs = fig.add_gridspec(2, 5, height_ratios=[1, 1.15], hspace=0.5, wspace=0.12)
    ax = fig.add_subplot(gs[0, :])
    full = comp[comp.periodo == "2002-2024"].set_index("region").loc[order]
    left = np.zeros(len(full))
    for g in G5:
        v = full[g].values
        ax.barh(range(len(full)), v, left=left, color=COL[g], label=NAME[g], height=0.68, edgecolor="white", linewidth=0.4)
        for i, (l, w) in enumerate(zip(left, v)):
            if w >= 6:
                ax.text(l + w / 2, i, f"{w:.0f}", ha="center", va="center", color="white", fontsize=6.8, fontweight="bold")
        left += v
    ax.set_yticks(range(len(full)))
    ax.set_yticklabels([f"{REG_EN[r]}\n({REGIONS[r][0]:.1f}–{REGIONS[r][1]:.1f}° N)" for r in order], fontsize=6.8)
    ax.invert_yaxis(); ax.set_xlim(0, 100)
    ax.set_xlabel("Share of the chlorophyll-a biomass of the five groups (%)")
    ax.set_title("Jul 2002 – Dec 2024", pad=4)
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    letter(ax, "a", x=-0.02, y=1.0)
    fig.legend(*ax.get_legend_handles_labels(), ncol=5, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.93))
    labs = list(PERIODS)
    axes = []
    for j, r in enumerate(order):
        a = fig.add_subplot(gs[1, j], sharey=axes[0] if axes else None)
        sub = comp[(comp.region == r) & (comp.periodo.isin(labs))].set_index("periodo").loc[labs]
        bottom = np.zeros(len(sub))
        for g in G5:
            a.bar(range(len(sub)), sub[g].values, bottom=bottom, color=COL[g], width=0.78, edgecolor="white", linewidth=0.3)
            bottom += sub[g].values
        a.set_xticks(range(len(sub)), [p[2:4] + "–" + p[-2:] for p in labs], rotation=90, fontsize=6.5)
        a.set_ylim(0, 100); a.set_title(REG_EN[r], fontsize=7.2, loc="center")
        if j:
            plt.setp(a.get_yticklabels(), visible=False)
        else:
            a.set_ylabel("Share (%)")
            letter(a, "b", x=-0.32, y=1.06)
        axes.append(a)
    axes[2].set_xlabel("Five-year period (first period starts Jul 2002)", labelpad=4)
    save(fig, out, "Fig3_regional_composition")


# --------------------------------------------------------------------------------------------- Fig. 4
def fig4(D, out):
    Q = {"2000-2004": ("2000", "2004"), "2005-2009": ("2005", "2009"), "2010-2014": ("2010", "2014"),
         "2015-2019": ("2015", "2019"), "2020-2024": ("2020", "2024")}
    vars_ = [("CHL", "Total chlorophyll-a"), ("DIATO", "Diatoms"), ("MICRO", "Microphytoplankton"),
             ("DINO", "Dinoflagellates"), ("HAPTO", "Haptophytes"), ("GREEN", "Green algae"),
             ("PROCHLO", "$\\it{Prochlorococcus}$"), ("PROKAR", "Prokaryotes"), ("PICO", "Picophytoplankton")]
    xt = ["2000–04*", "2005–09", "2010–14", "2015–19", "2020–24"]
    fig, axes = plt.subplots(3, 3, figsize=(174 * MM, 150 * MM), sharex=True)
    x = np.arange(5)
    for ax, (v, name) in zip(axes.flat, vars_):
        s = [D.loc[a:b, v].dropna() for a, b in Q.values()]
        m = np.array([q.mean() for q in s]); sd = np.array([q.std(ddof=0) for q in s])
        ax.fill_between(x, m - sd, m + sd, color="#2a78d6", alpha=0.15, linewidth=0)
        ax.plot(x, m, "-o", color="#2a78d6", lw=1.4, ms=3.6, mec="white", mew=0.7)
        ax.set_title(name, fontsize=7.5)
        ax.set_ylim(0, (m + sd).max() * 1.15)
        ax.set_xticks(x, xt, rotation=45, ha="right", fontsize=6.5)
        ax.grid(axis="y", color=GRID, lw=0.4); ax.set_axisbelow(True)
        imax, imin = int(np.argmax(m)), int(np.argmin(m))
        below = m[imin] / ax.get_ylim()[1] > 0.12          # hay espacio bajo el punto
        ax.annotate(f"{m[imin]:.3f}", (x[imin], m[imin]), textcoords="offset points",
                    xytext=((7 if imin == 0 else 0) if below else -4, -9 if below else 4),
                    ha="center" if below else "right", fontsize=6, color=INK2)
        ax.annotate(f"{m[imax]:.3f}", (x[imax], m[imax]), textcoords="offset points",
                    xytext=(7 if imax == 0 else 0, 5), ha="center", fontsize=6, color=INK2)
    for ax in axes[:, 0]:
        ax.set_ylabel(f"Concentration ({UNIT})")
    fig.tight_layout(h_pad=0.9, w_pad=1.2)
    save(fig, out, "Fig4_five_year_means")


# --------------------------------------------------------------------------------------------- Fig. 5
PER5 = [("2000–04", "2000-01-01", "2004-12-31"), ("2005–09", "2005-01-01", "2009-12-31"),
        ("2010–14", "2010-01-01", "2014-12-31"), ("2015–19", "2015-01-01", "2019-12-31")]
REF5 = ("2020-01-01", "2024-12-31")


def fig5_data(raw, cache):
    if cache.exists():
        z = np.load(cache)
        return {k: z[k] for k in z.files}
    import config_gulf_california as cg
    ds = xr.open_dataset(raw)
    mask = np.asarray(cg.get_gulf_of_california_filter_shapefile(ds))
    assert int(mask.sum()) == 13928, int(mask.sum())
    out = {"lat": ds.latitude.values, "lon": ds.longitude.values, "mask": mask}
    for v in ["CHL", "DIATO"]:
        ref = ds[v].sel(time=slice(*REF5)).mean("time").values
        for lab, a, b in PER5:
            out[f"{v}_{lab}"] = np.where(mask, ref - ds[v].sel(time=slice(a, b)).mean("time").values, np.nan)
        print(v, "differences computed", flush=True)
    np.savez_compressed(cache, **out)
    return out


def fig5(raw, out):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter
    Z = fig5_data(raw, out / "cache_fig5.npz")
    pc = ccrs.PlateCarree()
    rings = gulf_rings()
    fig = plt.figure(figsize=(174 * MM, 108 * MM))
    gs = fig.add_gridspec(2, 5, width_ratios=[1, 1, 1, 1, 0.055], wspace=0.06, hspace=0.16)
    land = cfeature.LAND.with_scale("10m")
    for i, (v, title) in enumerate([("CHL", "Total chlorophyll-a"), ("DIATO", "Diatoms")]):
        arrs = [Z[f"{v}_{lab}"] for lab, _, _ in PER5]
        vals = np.concatenate([x[np.isfinite(x)] for x in arrs])
        vmax = float(np.nanpercentile(np.abs(vals), 99))
        norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
        for j, ((lab, _, _), arr) in enumerate(zip(PER5, arrs)):
            ax = fig.add_subplot(gs[i, j], projection=pc)
            ax.set_extent([-115.4, -104.6, 20.0, 32.2], crs=pc)
            ax.set_facecolor("white")
            im = ax.pcolormesh(Z["lon"], Z["lat"], arr, cmap="RdBu_r", norm=norm, shading="nearest", transform=pc,
                               rasterized=True, zorder=1)
            ax.add_feature(land, facecolor="#dcdbd7", edgecolor="none", zorder=2, rasterized=True)
            ax.add_feature(cfeature.COASTLINE.with_scale("10m"), linewidth=0.3, edgecolor=INK2, zorder=3, rasterized=True)
            for r in rings:
                ax.plot(r[:, 0], r[:, 1], color=INK, lw=0.5, transform=pc, zorder=4)
            ax.set_xticks([-114, -110, -106], crs=pc); ax.set_yticks([21, 24, 27, 30], crs=pc)
            ax.xaxis.set_major_formatter(LongitudeFormatter()); ax.yaxis.set_major_formatter(LatitudeFormatter())
            ax.tick_params(labelsize=6, length=2, width=0.5)
            if i == 0:
                ax.tick_params(labelbottom=False)
            if j:
                ax.tick_params(labelleft=False)
            for s in ax.spines.values():
                s.set_linewidth(0.5); s.set_edgecolor(INK2)
            ax.set_title(f"2020–24 minus {lab}", fontsize=7, loc="center", pad=3)
            if j == 0:
                ax.text(-0.04, 1.13, f"({'ab'[i]}) {title}", transform=ax.transAxes, fontsize=8, fontweight="bold",
                        ha="left", va="bottom")
        cax = fig.add_subplot(gs[i, 4])
        cb = fig.colorbar(im, cax=cax, extend="both")
        cb.set_label(f"Δ concentration ({UNIT})", fontsize=6.8)
        cb.ax.tick_params(labelsize=6, width=0.5, length=2); cb.outline.set_linewidth(0.5)
    save(fig, out, "Fig5_difference_maps")


# --------------------------------------------------------------------------------------------- Fig. 6
def fig6(D, estados_csv, out):
    from stl_recortado import stl_trimmed
    res, y, _ = stl_trimmed(D["DIATO"])
    st = pd.read_csv(estados_csv, parse_dates=["fecha"]).set_index("fecha")
    assert len(st) == len(y) and np.allclose(st["valor"].values, y.values), "estados.csv no coincide con la serie"
    hi = st["alto_mejor"].values.astype(bool)
    fig, ax = plt.subplots(3, 1, figsize=(174 * MM, 130 * MM), sharex=True, gridspec_kw={"height_ratios": [1.35, 1, 1]})
    ax[0].plot(y.index, y, color="#a5a4a0", lw=0.7, label="Monthly series")
    ax[0].plot(y.index, res.trend, color="#2a78d6", lw=1.6, label="Trend (STL)")
    ax[0].scatter(y.index[hi], y[hi], s=7, color="#eb6834", zorder=3, linewidths=0, label="High-biomass regime (HMM)")
    ax[0].set_ylabel(f"Diatoms ({UNIT})")
    ax[0].legend(frameon=False, loc="upper right")
    ax[1].plot(y.index, res.seasonal, color="#2a78d6", lw=0.9); ax[1].set_ylabel(f"Seasonal ({UNIT})")
    ax[2].plot(y.index, res.resid, color="#2a78d6", lw=0.8); ax[2].axhline(0, color=INK2, lw=0.5)
    ax[2].set_ylabel(f"Residual ({UNIT})"); ax[2].set_xlabel("Year")
    for a, tg in zip(ax, "abc"):
        a.grid(axis="y", color=GRID, lw=0.4); a.set_axisbelow(True)
        letter(a, tg, x=-0.075)
    ax[2].set_xlim(y.index.min() - pd.Timedelta(days=60), y.index.max() + pd.Timedelta(days=60))
    fig.align_ylabels(ax)
    fig.tight_layout(h_pad=0.6)
    save(fig, out, "Fig6_diatoms_STL_HMM")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nc", default="data/processed/pft_monthly_statistics_poligono.nc")
    ap.add_argument("--raw", default="data/raw/pft_golfo_california_2000_2024.nc")
    ap.add_argument("--salidas", default=str(HERE / "salidas"))
    ap.add_argument("--out", default=str(HERE / "salidas" / "figuras_ingles"))
    ap.add_argument("--figs", nargs="+", type=int, default=[1, 2, 3, 4, 5, 6])
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    S = Path(a.salidas)
    D = load_monthly(a.nc)
    esc = pd.read_csv(S / "poligono" / "serie_cuenca" / "escalones.csv").set_index("serie")
    brk = pd.Timestamp(esc.loc["ln(PROCHLO/PROKAR)", "pettitt_fecha"])
    for f in a.figs:
        {1: lambda: fig1(out), 2: lambda: fig2(D, brk, out), 3: lambda: fig3(S / "regional_composicion.csv", out),
         4: lambda: fig4(D, out), 5: lambda: fig5(a.raw, out),
         6: lambda: fig6(D, S / "poligono" / "hmm" / "estados.csv", out)}[f]()


if __name__ == "__main__":
    main()
