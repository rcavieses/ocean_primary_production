#!/usr/bin/env python3
"""
Figuras del manuscrito "Tipos funcionales de fitoplancton en el Golfo de California".

Usa SOLO salidas del flujo filtrado al polígono del Golfo (shapefile regionmarinamx):
  - results/satellite/tables/reporte_analisis_numerico.json  (estadísticas quinquenales)
  - results/satellite/figures/timeseries/plotly_charts/*_composition_timeseries.html
    (composición porcentual mensual, embebida en los gráficos plotly)
  - results/satellite/figures/quinquennial_diff_publication/*_abs_diff.pdf (mapas)
  - results/satellite/figures/shapefiles/regionmarinamx.shp (dominio de análisis)

Uso:  python3 manuscript/figures/make_manuscript_figures.py
Requiere: matplotlib, numpy, pandas, cartopy, pyshp, poppler-utils (pdftoppm)
"""
import base64
import json
import re
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import shapefile  # pyshp

BASE = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RES = BASE / "results" / "satellite"

# Paleta categórica (orden fijo, validada para pares adyacentes en modo claro)
# Fecha del quiebre de Prochlorococcus que se marca en la Fig. 2c (se puede cambiar al importar el módulo)
QUIEBRE_PROCHLO = "2016-04-01"
# Eje y de la Fig. 2c (cociente en escala log) y altura de la etiqueta del quiebre
FIG2C_YLIM = (0.3, 14)
FIG2C_YTICKS = [0.5, 1, 2, 5, 10]
FIG2C_ETIQUETA_Y = 9

CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5,
    "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white",
})


# ---------------------------------------------------------------- utilidades
def plotly_traces(path):
    """Devuelve {nombre: pd.Series} de un HTML generado con plotly (Python)."""
    s = path.read_text(encoding="utf-8")
    m = re.search(r'Plotly\.newPlot\(\s*"[^"]*",\s*(\[.*?\])\s*,\s*\{', s, re.S)
    out = {}
    for tr in json.loads(m.group(1)):
        def dec(v):
            if isinstance(v, dict) and "bdata" in v:
                return np.frombuffer(base64.b64decode(v["bdata"]), dtype=np.dtype(v["dtype"]))
            return v
        out[tr["name"]] = pd.Series(np.asarray(dec(tr["y"]), float),
                                    index=pd.to_datetime(dec(tr["x"])))
    return out


def gulf_polygon():
    sf = shapefile.Reader(str(RES / "figures" / "shapefiles" / "regionmarinamx.shp"))
    shp = sf.shapes()[0]
    parts = list(shp.parts) + [len(shp.points)]
    return [np.array(shp.points[parts[i]:parts[i + 1]]) for i in range(len(parts) - 1)]


# ---------------------------------------------------------------- Figura 1
def fig_area_estudio():
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    fig = plt.figure(figsize=(6.3, 5.6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-118, -101, 17.5, 33.5], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND.with_scale("10m"), facecolor="#e9e8e4", edgecolor="none")
    ax.add_feature(cfeature.COASTLINE.with_scale("10m"), linewidth=0.5, edgecolor=INK2)
    ax.add_feature(cfeature.BORDERS.with_scale("10m"), linewidth=0.4, edgecolor="#a5a4a0")

    for ring in gulf_polygon():
        ax.fill(ring[:, 0], ring[:, 1], facecolor="#2a78d6", alpha=0.28,
                edgecolor="#1c5aa6", linewidth=1.0, transform=ccrs.PlateCarree(), zorder=3)
    # Recuadro de descarga
    ax.add_patch(mpatches.Rectangle((-117, 18), 15, 15, fill=False, edgecolor=INK,
                                    linestyle="--", linewidth=0.9, transform=ccrs.PlateCarree(), zorder=4))
    ax.text(-116.8, 18.35, "Recuadro de descarga (18°–33° N, 117°–102° O)", fontsize=7.5,
            color=INK, transform=ccrs.PlateCarree())

    # Límites de las bandas de latitud usadas en la composición por región
    # (mismas que manuscript/reanalysis/composicion_regional.py: REGIONS)
    import sys
    from shapely.geometry import LineString, Polygon
    sys.path.insert(0, str(BASE / "manuscript" / "reanalysis"))
    from composicion_regional import REGIONS
    gulf = [Polygon(r) for r in gulf_polygon()]
    edges = sorted({lat for lo_hi in REGIONS.values() for lat in lo_hi})
    for lat in edges:
        line = LineString([(-118, lat), (-101, lat)])
        segs = [line.intersection(p.buffer(0)) for p in gulf]
        east = None
        for seg in segs:
            for g in getattr(seg, "geoms", [seg]):
                if g.is_empty or g.geom_type != "LineString":
                    continue
                xs, ys = g.xy
                ax.plot(xs, ys, color="#a3341b", lw=1.0, ls=(0, (4, 2)), transform=ccrs.PlateCarree(), zorder=4)
                east = max(xs) if east is None else max(east, max(xs))
        if east is not None:  # etiqueta junto al extremo oriental del límite
            ax.text(east + 0.2, lat, f"{lat:g}° N", fontsize=6.5, color="#a3341b", va="center",
                    transform=ccrs.PlateCarree(), zorder=5,
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8))

    labels = [(-114.3, 31.2, "Alto Golfo"), (-113.6, 29.3, "Grandes Islas"),
              (-111.4, 27.0, "Golfo central"), (-108.7, 24.4, "Golfo sur"),
              (-108.9, 21.3, "Entrada")]
    for x, y, t in labels:
        ax.text(x, y, t, fontsize=7.5, color=INK, transform=ccrs.PlateCarree(), zorder=5,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
    for x, y, t, ha in [(-109.9, 22.85, "Cabo San Lucas", "right"), (-105.6, 20.4, "Cabo Corrientes", "left")]:
        ax.plot(x, y, "o", ms=3, color=INK, transform=ccrs.PlateCarree(), zorder=5)
        ax.text(x + (-0.25 if ha == "right" else 0.25), y - 0.35, t, fontsize=7, ha=ha,
                color=INK2, transform=ccrs.PlateCarree(), zorder=5)
    ax.text(-116.5, 24.5, "Océano\nPacífico", fontsize=8, color=INK2, style="italic",
            transform=ccrs.PlateCarree())
    gl = ax.gridlines(draw_labels=True, linewidth=0.4, color=GRID, linestyle="-")
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": 7.5, "color": INK2}
    handles = [mpatches.Patch(facecolor="#2a78d6", alpha=0.28, edgecolor="#1c5aa6",
                              label="Dominio de análisis (polígono del Golfo)"),
               plt.Line2D([], [], color=INK, linestyle="--", label="Recuadro de descarga"),
               plt.Line2D([], [], color="#a3341b", lw=1.0, ls=(0, (4, 2)),
                          label="Límites de las regiones (bandas de latitud)")]
    ax.legend(handles=handles, loc="upper right", fontsize=7.5, frameon=True, framealpha=0.9)
    fig.savefig(OUT / "Fig1_area_estudio.png")
    plt.close(fig)


# ---------------------------------------------------------------- Figura 2
def fig_composicion():
    sp = plotly_traces(RES / "figures/timeseries/plotly_charts/species_composition_timeseries.html")
    sz = plotly_traces(RES / "figures/timeseries/plotly_charts/size_composition_timeseries.html")
    rename = {"Diatomeas": "Diatomeas", "Dinoflagelados": "Dinoflagelados",
              "Algas Verdes": "Clorofitas", "Haptófitos": "Haptofitas",
              "Proclorococcus": "Prochlorococcus", "Procariontes": "Procariotas"}
    dsp = pd.DataFrame({rename[k]: v for k, v in sp.items()}).dropna()
    # Partición sin doble conteo (5 grupos): cumple MICRO=DIATO+DINO, NANO=HAPTO,
    # PICO=GREEN+PROKAR. Prochlorococcus (subconjunto de procariotas) se excluye.
    ratio = dsp["Prochlorococcus"] / dsp["Procariotas"]
    g5 = ["Diatomeas", "Dinoflagelados", "Clorofitas", "Haptofitas", "Procariotas"]
    dsp = dsp[g5].div(dsp[g5].sum(axis=1), axis=0) * 100
    dsz = pd.DataFrame(sz).dropna()
    dsz.columns = ["Micro (>20 µm)", "Nano (2–20 µm)", "Pico (<2 µm)"]
    # suavizado de 12 meses SOLO para la visualización
    dsp_s = dsp.rolling(12, center=True, min_periods=6).mean()
    dsz_s = dsz.rolling(12, center=True, min_periods=6).mean()

    fig, axes = plt.subplots(3, 1, figsize=(6.5, 7.4), sharex=True,
                             gridspec_kw={"height_ratios": [1.3, 1, 0.9]})
    cols5 = [CAT[0], CAT[1], CAT[2], CAT[3], CAT[5]]
    for ax, d, cols, tag in [(axes[0], dsp_s, cols5, "a"), (axes[1], dsz_s, [CAT[0], CAT[3], CAT[2]], "b")]:
        ax.stackplot(d.index, d.T.values, colors=cols, labels=d.columns,
                     edgecolor="white", linewidth=0.6)
        ax.set_ylim(0, 100); ax.set_xlim(d.index.min(), d.index.max())
        ax.set_ylabel("Contribución relativa (%)")
        ax.grid(axis="x", visible=False)
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=7.5, frameon=False,
                  reverse=True)
        ax.text(-0.11, 1.02, f"({tag})", transform=ax.transAxes, fontsize=10, fontweight="bold")
    axes[0].set_title("Grupos taxonómicos (partición de 5 grupos, sin Prochlorococcus)", fontsize=9, loc="left", color=INK)
    axes[1].set_title("Clases de tamaño", fontsize=9, loc="left", color=INK)
    # (c) cociente Prochlorococcus / procariotas: un subconjunto no puede superar 1
    ax = axes[2]
    brk = pd.Timestamp(QUIEBRE_PROCHLO)
    ax.set_yscale("log")
    ax.plot(ratio.index, ratio.values, color="#2a78d6", lw=1.2)
    for a0, a1, dy in [(ratio.index.min(), brk - pd.Timedelta(days=1), 0.62), (brk, ratio.index.max(), 1.35)]:
        mu = ratio[a0:a1].mean()
        ax.hlines(mu, a0, a1, color=INK, lw=1.4)
        ax.text(a0 + (a1 - a0) / 2, mu * dy, f"media {mu:.2f}", ha="center", fontsize=7, color=INK,
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
    ax.axhline(1, color="#e34948", lw=1, linestyle="--")
    ax.text(ratio.index.max(), 0.82, "límite físico: subconjunto = total ", ha="right", fontsize=7, color="#b8302f",
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
    ax.axvline(brk, color=INK2, lw=0.8, linestyle=":")
    ax.text(brk, FIG2C_ETIQUETA_Y, " quiebre " + ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"][brk.month - 1] + f"-{brk.year}", fontsize=7, color=INK2)
    ax.set_ylim(*FIG2C_YLIM)
    ax.set_yticks(FIG2C_YTICKS, [f"{t:g}" for t in FIG2C_YTICKS])
    ax.minorticks_off()
    ax.set_ylabel("Prochlorococcus /\nprocariotas")
    ax.set_title("Cociente mensual Prochlorococcus/procariotas", fontsize=9, loc="left", color=INK)
    ax.grid(axis="x", visible=False)
    ax.text(-0.11, 1.02, "(c)", transform=ax.transAxes, fontsize=10, fontweight="bold")
    axes[2].set_xlabel("Año")
    fig.savefig(OUT / "Fig2_composicion_relativa.png")
    plt.close(fig)


# ---------------------------------------------------------------- Figura 3
def fig_quinquenios():
    J = json.loads((RES / "tables/reporte_analisis_numerico.json").read_text())["variables"]
    vars_ = [("CHL", "Clorofila-a total"), ("DIATO", "Diatomeas"), ("MICRO", "Microfitoplancton"),
             ("DINO", "Dinoflagelados"), ("HAPTO", "Haptofitas"), ("GREEN", "Clorofitas"),
             ("PROCHLO", "Prochlorococcus"), ("PROKAR", "Procariotas"), ("PICO", "Picofitoplancton")]
    periods = ["2000-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2024"]
    xt = ["2000–04*", "2005–09", "2010–14", "2015–19", "2020–24"]
    fig, axes = plt.subplots(3, 3, figsize=(6.7, 6.2), sharex=True)
    for ax, (v, name) in zip(axes.flat, vars_):
        q = J[v]["quinquennial_statistics"]
        m = np.array([q[p]["mean"] for p in periods]); s = np.array([q[p]["std"] for p in periods])
        x = np.arange(5)
        ax.fill_between(x, m - s, m + s, color="#2a78d6", alpha=0.15, linewidth=0)
        ax.plot(x, m, "-o", color="#2a78d6", lw=2, ms=5, mec="white", mew=1)
        ax.set_title(name, fontsize=8.5, loc="left", color=INK)
        ax.set_ylim(0, (m + s).max() * 1.12)
        ax.set_xticks(x, xt, rotation=45, ha="right", fontsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.grid(axis="x", visible=False)
        imax = int(np.argmax(m)); imin = int(np.argmin(m))
        ax.annotate(f"{m[imin]:.3f}", (x[imin], m[imin]), textcoords="offset points",
                    xytext=(9 if imin == 0 else 0, -11), ha="center", fontsize=6.5, color=INK2)
        ax.annotate(f"{m[imax]:.3f}", (x[imax], m[imax]), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=6.5, color=INK2)
    for ax in axes[:, 0]:
        ax.set_ylabel("mg m⁻³", fontsize=8)
    fig.tight_layout(h_pad=1.0)
    fig.savefig(OUT / "Fig3_medias_quinquenales.png")
    plt.close(fig)


# ---------------------------------------------------------------- Figura 4
def fig_mapas_diferencias():
    pdfdir = RES / "figures" / "quinquennial_diff_publication"
    with tempfile.TemporaryDirectory() as td:
        imgs = []
        for v in ["CHL", "DIATO"]:
            stem = Path(td) / v
            subprocess.run(["pdftoppm", "-png", "-r", "170", "-singlefile",
                            str(pdfdir / f"{v}_abs_diff.pdf"), str(stem)], check=True)
            imgs.append(plt.imread(str(stem) + ".png"))
    # recorta el título general en inglés (franja superior) de cada mapa
    crops = []
    for im in imgs:
        h = im.shape[0]
        crops.append(im[int(0.126 * h):, :, :3])
    w = max(c.shape[1] for c in crops)
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.4))
    for ax, im, tag, t in zip(axes, crops, "ab", ["Clorofila-a total", "Diatomeas"]):
        ax.imshow(im); ax.axis("off")
        ax.set_title(f"({tag}) {t}: 2020–2024 menos cada quinquenio previo (mg m⁻³)",
                     fontsize=8.5, loc="left", color=INK)
    fig.tight_layout(h_pad=0.6)
    fig.savefig(OUT / "Fig4_mapas_diferencias.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    fig_area_estudio()
    fig_composicion()
    fig_quinquenios()
    fig_mapas_diferencias()
    print("Figuras guardadas en", OUT)
