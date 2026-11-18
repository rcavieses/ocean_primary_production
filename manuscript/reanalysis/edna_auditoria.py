#!/usr/bin/env python3
"""
Auditoría de eDNA y de los match-ups satélite-eDNA (comentarios 1, 5, 11 y 12).

  (6) Cuenta los registros exactos que quedan después de cada filtro.
  (7) Indica si entran registros de "Pacífico Sur" (u otras zonas) en los match-ups.
  (8) Define qué es cada unidad de n (año-mes con >=1 registro del grupo) y reporta
      Pearson y Spearman por separado, para dos configuraciones:
        - ORIGINAL: réplica de src/visualization/plot_satellite_vs_insitu_timeseries.py
          (todas las zonas y profundidades, 2000-2024, conteo de registros por año-mes,
          valor satelital = media mensual de toda la cuenca).
        - CORREGIDA: solo estrato superficial (1-26 m), sin "Pacífico Sur",
          solo meses con PFT satelital (desde jul-2002).

Acepta el CSV combinado (v1: 'Collected date year', 'Shallow (m)', 'Mid-water (m)',
'Deep (m)') y el v2 ('date', 'Depth'). Las columnas se detectan sin distinguir
mayúsculas; el script imprime cuáles usó para que se verifiquen.

Uso:
    python3 manuscript/reanalysis/edna_auditoria.py --csv ADN_merged_data_20251001_161630.csv \
        [--pft data/processed/pft_monthly_statistics.nc]
Salida: manuscript/reanalysis/salidas/edna_*.csv y edna_auditoria_resumen.md
"""
import argparse
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

# Grupos (sección 3.4 del manuscrito + scripts existentes)
GROUPS = {
    "Diatomeas": ["Bacillariophyta", "Bacillariophyceae", "Fragilariophyceae", "Diatomophyceae"],
    "Dinoflagelados": ["Dinophyta", "Dinophyceae", "Myzozoa", "Dino NA"],
    "Clorofitas": ["Chlorophyta", "Chlorophyceae", "Ulvophyceae"],
    "Cianobacterias": ["Cyanobacteria", "Oxyphotobacteria"],
    "Haptofitas": ["Haptophyta", "Prymnesiophyceae", "Coccolithophyceae", "Haptista"],
}
# Emparejamiento usado en el manuscrito (4.5) y en el script original
MATCH = {"Diatomeas": ("DIATO_mean", ["Bacillariophyta"]),
         "Dinoflagelados": ("DINO_mean", ["Dinophyta", "Dinophyceae", "Myzozoa"]),
         "Clorofitas": ("GREEN_mean", ["Chlorophyta"]),
         "Haptofitas": ("HAPTO_mean", ["Haptophyta"]),
         "Cianobacterias": ("PROKAR_mean", ["Cyanobacteria"]),
         "Clorofila total": ("CHL_mean", "__ALL_CLASSIFIED__")}
PACIFIC_PAT = re.compile(r"pac[ií]f", re.I)


def find_col(df, *cands, pattern=None):
    low = {c.lower().strip(): c for c in df.columns}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    if pattern:
        for c in df.columns:
            if re.search(pattern, c, re.I):
                return c
    return None


def parse_date(v):
    if pd.isna(v) or v == "":
        return pd.NaT
    s = str(v).strip()
    try:
        f = float(s)
        if 20000 < f < 80000:  # número serial de Excel
            return datetime(1899, 12, 30) + pd.Timedelta(days=int(f))
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y"):
        try:
            return pd.to_datetime(s, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.to_datetime(s, errors="coerce", dayfirst=True)


def layer_v1(row, cs, cm, cd):
    if cs and pd.notna(row[cs]):
        return "Superficial"
    if cm and pd.notna(row[cm]):
        return "Intermedia"
    if cd and pd.notna(row[cd]):
        return "Profunda"
    return np.nan


def layer_from_depth(v):
    if pd.isna(v):
        return np.nan
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(v))]
    if not nums:
        return np.nan
    d = max(nums)  # para rangos como "1-26" usa el extremo inferior de la capa
    d = min(nums) if len(nums) > 1 else d
    if d <= 26:
        return "Superficial"
    if d <= 140:
        return "Intermedia"
    return "Profunda"


def classify(df, cph, ccl, cki):
    out = pd.Series("No productor primario", index=df.index)
    for g, names in GROUPS.items():
        m = pd.Series(False, index=df.index)
        for c in (cph, ccl, cki):
            if c:
                m |= df[c].astype(str).str.strip().isin(names)
        out[m & (out == "No productor primario")] = g
    return out


def matchups(df, sat, label, out_dir):
    rows, detail = [], []
    for g, (svar, phyla) in MATCH.items():
        if phyla == "__ALL_CLASSIFIED__":
            sub = df[df["grupo"] != "No productor primario"]
        else:
            sub = df[df["_phylum"].isin(phyla) | df["_class"].isin(phyla)]
        cnt = sub.groupby("year_month").size()
        zones = sub.groupby("year_month")["_zone"].agg(lambda z: ";".join(sorted(set(map(str, z)))))
        pac = sub.groupby("year_month")["_zone"].agg(lambda z: int(z.astype(str).str.contains(PACIFIC_PAT).sum()))
        rec = {"configuracion": label, "grupo": g, "variable_satelital": svar,
               "registros": len(sub), "meses_con_registros": len(cnt),
               "registros_PacificoSur": int(sub["_zone"].astype(str).str.contains(PACIFIC_PAT).sum())}
        if sat is not None and svar in sat:
            s = sat[svar].dropna()
            common = cnt.index.intersection(s.index)
            rec["n_meses_match"] = len(common)
            rec["meses_match_con_PacificoSur"] = int((pac.reindex(common) > 0).sum())
            if len(common) >= 3:
                x, y = s.reindex(common).values, cnt.reindex(common).values
                rec["pearson_r"], rec["pearson_p"] = pearsonr(x, y)
                rec["spearman_rho"], rec["spearman_p"] = spearmanr(x, y)
            for m in common:
                detail.append({"configuracion": label, "grupo": g, "mes": m.date(),
                               "registros": int(cnt[m]), "satelite": float(s[m]),
                               "zonas": zones[m], "registros_PacificoSur": int(pac[m])})
        rows.append(rec)
    pd.DataFrame(detail).to_csv(out_dir / f"edna_matchups_detalle_{label}.csv", index=False)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--pft", default=None, help="pft_monthly_statistics.nc (opcional, para correlaciones)")
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas")))
    ap.add_argument("--solo-detecciones", action="store_true",
                    help="excluye el bloque de totales (filas sin ID de muestra) y las filas con abundancia = 0 "
                         "(ausencias); sin esta opción el comportamiento es el original (cuenta filas)")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(a.csv, low_memory=False)
    pre_steps = []
    if a.solo_detecciones:
        cid = find_col(df, "Original_ID", "sample_id", "muestra")
        cab = find_col(df, "Abundancia", "Abundance", "abundancia")
        print("Solo detecciones: ID de muestra =", cid, "| abundancia =", cab)
        pre_steps.append(("0a. Filas en el archivo", len(df)))
        if cid:  # v1: el bloque sin ID es la fila de totales (suma de las muestras por taxón)
            df = df[df[cid].notna()]
            pre_steps.append((f"0b. Sin bloque de totales ('{cid}' vacío)", len(df)))
        else:
            pre_steps.append(("0b. Sin bloque de totales (no hay columna de ID de muestra: no aplica)", len(df)))
        if cab:
            df = df[pd.to_numeric(df[cab], errors="coerce") > 0]
            pre_steps.append((f"0c. Solo detecciones ('{cab}' > 0)", len(df)))
        else:
            pre_steps.append(("0c. Solo detecciones: NO APLICABLE, el archivo no tiene columna de abundancia", len(df)))
        df = df.copy()
    cdate = find_col(df, "Collected date year", "date", "fecha", pattern=r"date|fecha")
    cph, ccl, cki = find_col(df, "phylum", "filo"), find_col(df, "class", "clase"), find_col(df, "kingdom", "reino")
    czone = find_col(df, "zone", "zona", "region", "región", pattern=r"zon|region|área|area")
    cs, cm, cd = find_col(df, "Shallow (m)"), find_col(df, "Mid-water (m)"), find_col(df, "Deep (m)")
    cdep = find_col(df, "Depth", "profundidad", pattern=r"^depth$|profund")
    used = {"fecha": cdate, "filo": cph, "clase": ccl, "reino": cki, "zona": czone,
            "Shallow": cs, "Mid-water": cm, "Deep": cd, "Depth": cdep}
    print("Columnas detectadas:", used)

    steps = pre_steps + [("0. Registros en el análisis" if a.solo_detecciones else "0. Registros en el archivo", len(df))]
    df["date"] = df[cdate].map(parse_date)
    steps.append(("1. Con fecha válida", int(df["date"].notna().sum())))
    df = df[df["date"].notna()].copy()
    df = df[(df.date.dt.year >= 2000) & (df.date.dt.year <= 2024)]
    steps.append(("2. Fecha entre 2000 y 2024", len(df)))
    df["_phylum"] = df[cph].astype(str).str.strip() if cph else ""
    df["_class"] = df[ccl].astype(str).str.strip() if ccl else ""
    df["_zone"] = df[czone] if czone else "sin_columna_zona"
    df["grupo"] = classify(df, cph, ccl, cki)
    steps.append(("3. Asignados a un grupo de productores primarios", int((df.grupo != "No productor primario").sum())))
    if cs or cm or cd:
        df["capa"] = df.apply(lambda r: layer_v1(r, cs, cm, cd), axis=1)
    else:
        df["capa"] = df[cdep].map(layer_from_depth) if cdep else np.nan
    prim = df[df.grupo != "No productor primario"]
    steps.append(("4. ... y en estrato superficial (1-26 m)", int((prim.capa == "Superficial").sum())))
    surf = prim[prim.capa == "Superficial"]
    no_pac = surf[~surf["_zone"].astype(str).str.contains(PACIFIC_PAT)]
    steps.append(("5. ... y fuera de 'Pacífico Sur'", len(no_pac)))
    ov = no_pac[no_pac.date >= "2002-07-01"]
    steps.append(("6. ... y en meses con PFT satelital (jul-2002 a dic-2024)", len(ov)))
    cascade = pd.DataFrame(steps, columns=["filtro", "registros"])
    cascade.to_csv(out / "edna_cascada_filtros.csv", index=False)

    df["year_month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    tab_zone = pd.crosstab(df["_zone"], df["grupo"], margins=True)
    tab_layer = pd.crosstab(df["capa"].fillna("sin capa"), df["grupo"], margins=True)
    tab_year = pd.crosstab(df["date"].dt.year, df["_zone"], margins=True)
    for n_, t in [("zona_x_grupo", tab_zone), ("capa_x_grupo", tab_layer), ("anio_x_zona", tab_year)]:
        t.to_csv(out / f"edna_{n_}.csv")

    sat = None
    if a.pft:
        import xarray as xr
        ds = xr.open_dataset(a.pft)
        t = pd.DatetimeIndex(ds.time.values).to_period("M").to_timestamp()
        sat = pd.DataFrame({v: ds[v].values for v in ds.data_vars if v.endswith("_mean")}, index=t)
    orig = matchups(df, sat, "original", out)
    corr = df[(df.capa == "Superficial") & (~df["_zone"].astype(str).str.contains(PACIFIC_PAT))
              & (df.date >= "2002-07-01")]
    corr_res = matchups(corr, sat, "corregida", out)
    res = pd.concat([orig, corr_res])
    res.to_csv(out / "edna_matchups_resumen.csv", index=False)

    with open(out / "edna_auditoria_resumen.md", "w") as f:
        f.write(f"# Auditoría eDNA — {Path(a.csv).name}\n\nColumnas usadas: `{used}`\n\n"
                f"Modo: {'SOLO DETECCIONES (sin totales, abundancia > 0)' if a.solo_detecciones else 'todas las filas (original)'}\n\n")
        f.write("## Cascada de filtros\n\n```\n" + cascade.to_string(index=False) + "\n```\n\n")
        f.write("## Registros por zona y grupo\n\n```\n" + tab_zone.to_string() + "\n```\n\n")
        f.write("## Registros por capa y grupo\n\n```\n" + tab_layer.to_string() + "\n```\n\n")
        f.write("## Match-ups (n = número de año-mes con >=1 registro del grupo que coinciden con un mes satelital)\n\n```\n"
                + res.round(4).to_string(index=False) + "\n```\n")
    print((out / "edna_auditoria_resumen.md").read_text())


if __name__ == "__main__":
    main()
