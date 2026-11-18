#!/usr/bin/env python3
"""
Match-ups satélite-eDNA normalizados por esfuerzo de muestreo (v1, solo detecciones).
(Parte A de la revisión: A1-A4.)

Base: taxonomy_corrected_edna.csv (v1); muestras con Original_ID (excluye el bloque de totales,
que no tiene ID); estrato superficial (columna `Shallow (m)`, 1-26 m); sin ZONE "SOUTH PACIFIC";
fecha >= 2002-07-01. Detección = fila con Abundancia > 0. Grupos (clasificación de
edna_auditoria.classify): Dinoflagelados, Haptofitas, Clorofitas y Productores primarios
(cualquier grupo). Variable satelital por grupo: DINO, HAPTO, GREEN y CHL.

A1  Muestra = Original_ID (los metadatos son constantes dentro de cada ID; sitio x fecha x
    profundidad NO es único: 81 IDs -> 79 combinaciones). Se verifica 81 muestras / 39
    superficiales. Por año-mes: muestras, muestras dentro del polígono del golfo, zonas, sitios y
    latitudes.
A2  Por grupo y año-mes (unidad = año-mes con >= 1 muestra de la base; los meses sin detección
    del grupo cuentan con 0):
      (a) detecciones; (b) detecciones / muestras; (c) frecuencia de ocurrencia = fracción de
      muestras con >= 1 detección del grupo  [VARIABLE PRINCIPAL].
    Referencia adicional "a_ref": (a) solo en meses con >= 1 detección (definición anterior de
    edna_auditoria.py), para enlazar con los valores ya informados.
A3  Valores satelitales:
      (i)   media mensual de la cuenca (pft_monthly_statistics.nc);
      (ii)  media mensual de la banda de latitud (REGIONS de composicion_regional.py) que contiene
            la muestra: DINO/HAPTO/GREEN de salidas/regional_mensual.csv; CHL no está en ese archivo
            y se calcula aquí con el mismo código (máscara del polígono, media temporal del mes y
            luego media espacial); como control se recalculan también DINO/HAPTO/GREEN y se
            comparan con regional_mensual.csv;
      (iii) caja de 3x3 píxeles centrada en el píxel más cercano a la muestra, en el NetCDF diario
            (data/raw/pft_golfo_california_2000_2024.nc): media mensual de cada píxel (días sin
            dato ignorados) y luego media de los píxeles con dato. Se informan píxeles válidos
            (de 9) y píxel-días válidos. Sin ningún dato -> NaN.
    Unidad para (ii) y (iii): la muestra (detecciones por muestra y ocurrencia 0/1). Para
    comparar, también se calcula la unidad muestra con (i).
A4  Por grupo x variable in situ x valor satelital: n, Pearson r (= punto-biserial si la
    variable es 0/1), Spearman rho, p nominales; para 0/1 además regresión logística
    (coeficiente por desviación estándar del valor satelital, p de Wald y de razón de
    verosimilitud). BH por separado para Pearson, Spearman y logística, en dos familias:
    PRINCIPAL = combinaciones de la variable principal [(c) mensual con (i); ocurrencia por
    muestra con (i), (ii), (iii)] y TODAS = todas las combinaciones. Las combinaciones con
    variable in situ constante se marcan "no definido" y no entran en BH. Para cada n se da el
    |r| mínimo para p < 0.05 (bilateral, Pearson): t_{0.975,n-2} / sqrt(t^2 + n - 2).

Uso:  python3 manuscript/reanalysis/edna_normalizado.py \
          --csv data/insitu/taxonomy_corrected_edna.csv --pft data/processed/pft_monthly_statistics.nc \
          --raw data/raw/pft_golfo_california_2000_2024.nc
Salida: manuscript/reanalysis/salidas/edna_normalizado/
"""
import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import xarray as xr
from scipy import stats
from shapely.geometry import Point
from statsmodels.stats.multitest import multipletests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "src" / "pipeline"))
from composicion_regional import REGIONS  # noqa: E402
from edna_auditoria import PACIFIC_PAT, classify, layer_v1, parse_date  # noqa: E402

warnings.filterwarnings("ignore")
GROUPS = {"Dinoflagelados": "DINO", "Haptofitas": "HAPTO", "Clorofitas": "GREEN", "Productores primarios": "CHL"}
SAT_LABEL = {"i": "(i) cuenca", "ii": "(ii) banda regional", "iii": "(iii) caja 3x3"}


def load_samples(csv):
    v = pd.read_csv(csv, low_memory=False)
    v = v[v["Original_ID"].notna()].copy()                      # excluye el bloque de totales
    meta = ["ZONE", "SITE NAME", "Shallow (m)", "Mid-water (m)", "Deep (m)", "Latitude", "Longitude",
            "Collected date year"]
    assert v.groupby("Original_ID")[meta].nunique(dropna=False).max().max() == 1, "metadatos no constantes por ID"
    s = v.drop_duplicates("Original_ID")[["Original_ID"] + meta].copy()
    s["fecha"] = s["Collected date year"].map(parse_date)
    s["capa"] = s.apply(lambda r: layer_v1(r, "Shallow (m)", "Mid-water (m)", "Deep (m)"), axis=1)
    checks = {"muestras_total": len(s), "muestras_superficiales": int((s.capa == "Superficial").sum()),
              "combinaciones_sitio_fecha_prof": int(s[["SITE NAME", "fecha", "Shallow (m)", "Mid-water (m)", "Deep (m)"]]
                                                    .astype(str).agg("|".join, axis=1).nunique())}
    det = v[pd.to_numeric(v["Abundancia"], errors="coerce") > 0].copy()
    det["grupo"] = classify(det, "phylum", "class", "kingdom")
    return s, det, checks


def band_of(lat):
    return next((r for r, (lo, hi) in REGIONS.items() if lo <= lat < hi), None)


def raw_values(raw_path, base, months, out_checks):
    """(ii) CHL por banda y control de DINO/HAPTO/GREEN; (iii) caja 3x3 por muestra."""
    import config_gulf_california as cg
    ds = xr.open_dataset(raw_path)
    times = pd.DatetimeIndex(ds.time.values)
    lat, lon = ds.latitude.values, ds.longitude.values
    gulf = cg.get_gulf_of_california_filter(ds, use_shapefile=True)
    lat2d = xr.broadcast(ds.latitude, ds.longitude)[0]
    masks = {r: gulf & (lat2d >= lo) & (lat2d < hi) for r, (lo, hi) in REGIONS.items()}
    band_rows = []
    for ym in months:
        idx = np.where((times.year == ym.year) & (times.month == ym.month))[0]
        sel = ds.isel(time=idx)
        for v in GROUPS.values():
            f = sel[v].mean("time")
            for r, m in masks.items():
                band_rows.append({"mes": ym.to_timestamp(), "region": r, "var": v, "valor": float(f.where(m).mean())})
    band = pd.DataFrame(band_rows)
    box_rows = []
    for _, s in base.iterrows():
        ym = s.fecha.to_period("M")
        idx = np.where((times.year == ym.year) & (times.month == ym.month))[0]
        i, j = int(np.abs(lat - s.Latitude).argmin()), int(np.abs(lon - s.Longitude).argmin())
        i0, i1, j0, j1 = max(i - 1, 0), min(i + 2, len(lat)), max(j - 1, 0), min(j + 2, len(lon))
        row = {"Original_ID": s.Original_ID, "pixel_lat": float(lat[i]), "pixel_lon": float(lon[j]),
               "dist_pixel_km": float(np.hypot((lat[i] - s.Latitude) * 111.0,
                                               (lon[j] - s.Longitude) * 111.0 * np.cos(np.radians(s.Latitude)))),
               "pixeles_caja": (i1 - i0) * (j1 - j0), "dias_mes": len(idx)}
        for v in GROUPS.values():
            a = ds[v].isel(time=idx, latitude=slice(i0, i1), longitude=slice(j0, j1)).values.astype(float)
            pix_mean = np.nanmean(a, axis=0) if np.isfinite(a).any() else np.full(a.shape[1:], np.nan)
            row[f"{v}_iii"] = float(np.nanmean(pix_mean)) if np.isfinite(pix_mean).any() else np.nan
            row[f"{v}_pix_validos"] = int(np.isfinite(pix_mean).sum())
            row[f"{v}_pixdias_validos"] = int(np.isfinite(a).sum())
        box_rows.append(row)
    return band, pd.DataFrame(box_rows)


def corr(x, y, binary):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    rec = {"n": len(d)}
    if len(d) >= 3:
        t = stats.t.ppf(0.975, len(d) - 2)
        rec["r_min_p05"] = float(t / np.sqrt(t ** 2 + len(d) - 2))
    if len(d) < 3:
        rec["nota"] = "n < 3"; return rec
    if d.y.nunique() < 2:
        rec["nota"] = f"no definido: in situ constante (= {d.y.iloc[0]:g})"; return rec
    if d.x.nunique() < 2:
        rec["nota"] = "no definido: satélite constante"; return rec
    rec["pearson_r"], rec["pearson_p"] = (float(v) for v in stats.pearsonr(d.x, d.y))
    rec["spearman_rho"], rec["spearman_p"] = (float(v) for v in stats.spearmanr(d.x, d.y))
    if binary:
        rec["eventos_1"] = int(d.y.sum())
        z = (d.x - d.x.mean()) / d.x.std()
        try:
            m = sm.Logit(d.y.astype(float), sm.add_constant(z)).fit(disp=0, maxiter=200)
            rec.update({"logit_coef_por_DE": float(m.params.iloc[1]), "logit_p_wald": float(m.pvalues.iloc[1]),
                        "logit_p_LR": float(m.llr_pvalue)})
        except Exception as e:  # separación perfecta u otros
            rec["nota"] = f"logística no estimable: {type(e).__name__}"
    return rec


def bh(df, mask, col):
    q = pd.Series(np.nan, index=df.index)
    m = mask & df[col].notna()
    if m.any():
        q[m] = multipletests(df.loc[m, col], method="fdr_bh")[1]
    return q


def md(d):
    try:
        return d.to_markdown(index=False)
    except ImportError:
        return d.to_string(index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/insitu/taxonomy_corrected_edna.csv")
    ap.add_argument("--pft", default="data/processed/pft_monthly_statistics.nc")
    ap.add_argument("--raw", default="data/raw/pft_golfo_california_2000_2024.nc")
    ap.add_argument("--regional", default=str(HERE / "salidas" / "regional_mensual.csv"))
    ap.add_argument("--out", default=str(HERE / "salidas" / "edna_normalizado"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    # ---------------- A1
    s, det, checks = load_samples(a.csv)
    print("Verificación de muestras:", checks)
    assert checks["muestras_total"] == 81 and checks["muestras_superficiales"] == 39
    base = s[(s.capa == "Superficial") & ~s["ZONE"].astype(str).str.contains(PACIFIC_PAT)
             & (s.fecha >= "2002-07-01")].copy()
    import config_gulf_california as cg
    poly = cg._load_shapefile_polygon()
    base["en_golfo"] = [bool(poly.contains(Point(x, y))) for x, y in zip(base.Longitude, base.Latitude)]
    base["banda"] = base.Latitude.map(band_of)
    base["mes"] = base.fecha.dt.to_period("M")
    d = det[det.Original_ID.isin(base.Original_ID)]
    for g in GROUPS:
        sub = d if g == "Productores primarios" else d[d.grupo == g]
        if g == "Productores primarios":
            sub = d[d.grupo != "No productor primario"]
        cnt = sub.groupby("Original_ID").size()
        base[f"det_{g}"] = base.Original_ID.map(cnt).fillna(0).astype(int)
        base[f"occ_{g}"] = (base[f"det_{g}"] > 0).astype(int)
    months = sorted(base.mes.unique())
    mon = base.groupby("mes").agg(muestras=("Original_ID", "size"), muestras_en_golfo=("en_golfo", "sum"),
                                  zonas=("ZONE", lambda z: "; ".join(sorted(set(map(str, z))))),
                                  sitios=("SITE NAME", lambda z: "; ".join(sorted(set(map(str, z))))),
                                  latitudes=("Latitude", lambda z: "; ".join(f"{x:.3f}" for x in sorted(z))),
                                  bandas=("banda", lambda z: "; ".join(sorted(set(map(str, z))))))
    for g in GROUPS:
        gg = base.groupby("mes")
        mon[f"a_det_{g}"] = gg[f"det_{g}"].sum()
        mon[f"b_det_por_muestra_{g}"] = mon[f"a_det_{g}"] / mon["muestras"]
        mon[f"c_ocurrencia_{g}"] = gg[f"occ_{g}"].mean()

    # ---------------- A3 satélite
    ds = xr.open_dataset(a.pft)
    tm = pd.DatetimeIndex(ds.time.values).to_period("M")
    basin = pd.DataFrame({v: ds[f"{v}_mean"].values for v in GROUPS.values()}, index=tm)
    for v in GROUPS.values():
        mon[f"{v}_i"] = mon.index.map(basin[v])
        base[f"{v}_i"] = base.mes.map(basin[v])
    band, box = raw_values(a.raw, base, months, checks)
    reg = pd.read_csv(a.regional, parse_dates=["mes"])
    ctrl = band[band["var"] != "CHL"].merge(reg.melt(id_vars=["mes", "region"], var_name="var", value_name="regional_mensual"),
                                           on=["mes", "region", "var"])
    ctrl["dif_abs"] = (ctrl.valor - ctrl.regional_mensual).abs()
    ctrl.to_csv(out / "control_bandas_vs_regional_mensual.csv", index=False)
    base["mes_ts"] = base.mes.dt.to_timestamp()
    for v in GROUPS.values():
        src = (band[band["var"] == "CHL"].rename(columns={"valor": "x"}) if v == "CHL" else
               reg[["mes", "region", v]].rename(columns={v: "x"}))
        base[f"{v}_ii"] = base.merge(src[["mes", "region", "x"]], left_on=["mes_ts", "banda"],
                                     right_on=["mes", "region"], how="left")["x"].values
    base = base.merge(box, on="Original_ID", how="left")
    base.drop(columns=["mes_ts"]).to_csv(out / "muestras.csv", index=False)
    mon.reset_index().astype({"mes": str}).to_csv(out / "meses.csv", index=False)

    # ---------------- A4 correlaciones
    rows = []
    for g, v in GROUPS.items():
        # unidad mes, satélite (i)
        for var, col, binary in [("(a) detecciones", f"a_det_{g}", False),
                                 ("(b) detecciones/muestra", f"b_det_por_muestra_{g}", False),
                                 ("(c) frecuencia de ocurrencia", f"c_ocurrencia_{g}", False)]:
            rows.append({"grupo": g, "unidad": "año-mes (todos los meses muestreados)", "variable_in_situ": var,
                         "satelite": SAT_LABEL["i"], "principal": var.startswith("(c)"),
                         **corr(mon[f"{v}_i"], mon[col], binary)})
        ref = mon[mon[f"a_det_{g}"] > 0]
        rows.append({"grupo": g, "unidad": "año-mes con >=1 detección (definición anterior)", "variable_in_situ": "(a) detecciones [a_ref]",
                     "satelite": SAT_LABEL["i"], "principal": False, **corr(ref[f"{v}_i"], ref[f"a_det_{g}"], False)})
        # unidad muestra
        for sat in ("i", "ii", "iii"):
            for var, col, binary in [("detecciones por muestra", f"det_{g}", False),
                                     ("ocurrencia por muestra (0/1)", f"occ_{g}", True)]:
                rows.append({"grupo": g, "unidad": "muestra", "variable_in_situ": var, "satelite": SAT_LABEL[sat],
                             "principal": binary, **corr(base[f"{v}_{sat}"], base[col], binary)})
    R = pd.DataFrame(rows)
    for c in ("pearson_p", "spearman_p", "logit_p_LR"):
        if c not in R:
            R[c] = np.nan
        k = c.split("_")[0]
        R[f"q_principal_{k}"] = bh(R, R.principal, c)
        R[f"q_todas_{k}"] = bh(R, pd.Series(True, index=R.index), c)
    R["variable_principal"] = R.principal
    R = R.sort_values(["variable_principal", "grupo"], ascending=[False, True], kind="stable")
    cols = ["grupo", "unidad", "variable_in_situ", "satelite", "variable_principal", "n", "eventos_1", "r_min_p05",
            "pearson_r", "pearson_p", "q_principal_pearson", "q_todas_pearson",
            "spearman_rho", "spearman_p", "q_principal_spearman", "q_todas_spearman",
            "logit_coef_por_DE", "logit_p_wald", "logit_p_LR", "q_principal_logit", "q_todas_logit", "nota"]
    R = R.reindex(columns=cols)
    R.to_csv(out / "correlaciones.csv", index=False)

    # ---------------- resumen
    iii_nan = {v: int(base[f"{v}_iii"].isna().sum()) for v in GROUPS.values()}
    pv = {v: base[f"{v}_pix_validos"].describe()[["min", "50%", "max"]].to_dict() for v in GROUPS.values()}
    with open(out / "resumen.md", "w") as f:
        f.write("# eDNA (v1) normalizada por esfuerzo de muestreo\n\n")
        f.write(f"Verificación: {checks}. Muestra = Original_ID.\n\n"
                f"Base (superficie, sin SOUTH PACIFIC, desde jul-2002): {len(base)} muestras, {len(months)} meses, "
                f"{int(base.en_golfo.sum())} dentro del polígono del golfo.\n\n")
        f.write("## A1. Muestras por año-mes\n\n" + md(mon.reset_index()[["mes", "muestras", "muestras_en_golfo", "zonas", "sitios", "latitudes", "bandas"]].astype({"mes": str})) + "\n\n")
        f.write("## A2. Variables in situ por año-mes\n\n" + md(mon.reset_index()[["mes", "muestras"] + [c for c in mon.columns if c.startswith(("a_det", "b_det", "c_oc"))]].astype({"mes": str}).round(3)) + "\n\n")
        f.write("## A3. Satélite\n\n"
                f"(ii) control: máx |dif| entre bandas recalculadas y regional_mensual.csv = {ctrl.dif_abs.max():.2e} ({len(ctrl)} valores).\n\n"
                f"(iii) muestras sin dato en la caja 3x3: {iii_nan}; píxeles válidos (de 9) min/mediana/máx: {pv}; "
                f"distancia muestra-centro de píxel: máx {base.dist_pixel_km.max():.2f} km.\n\n")
        f.write("## A4. Correlaciones (variable principal primero)\n\n" + md(R.round(4)) + "\n\n"
                f"Pruebas en BH (Pearson/Spearman): familia principal {int(R[R.variable_principal].pearson_p.notna().sum())}, "
                f"todas {int(R.pearson_p.notna().sum())}; logística: {int(R.logit_p_LR.notna().sum())} "
                "(solo ocurrencia por muestra). No definidas: "
                f"{int(R.nota.astype(str).str.startswith('no definido').sum())}.\n")
    print((out / "resumen.md").read_text())


if __name__ == "__main__":
    main()
