#!/usr/bin/env python3
"""
A5. Fechas crudas de la v2 (Mac_loughlin y Valdivia): formatos y dos lecturas posibles.

No se usa la v2 para match-ups. Para cada TableID y formato de la cadena `date`:
  F1 "AAAA-xx-yy" con xx <= 12 (ambiguo), F2 "AAAA-xx-yy" con xx > 12, F3 "AA-xx-yy" (año de 2 dígitos).
Lecturas: AAAA-MM-DD y AAAA-DD-MM (en F3 el año se lee como 20AA). Para cada lectura: filas
válidas, rango, fechas distintas, año-meses distintos y muestras distintas (TableID x sitio x
profundidad x fecha).

Además, si se dan las tablas de sitios de las fuentes (`--fuentes`, archivos .xlsx con columna de
fecha), se cruzan por sitio con la v2 y se muestra cómo está guardada la fecha en la fuente
(texto o fecha de Excel). Requiere openpyxl para leer .xlsx.

Uso:  python3 manuscript/reanalysis/edna_v2_fechas.py --csv data/insitu/taxonomy_corrected_edna_2.csv \
          --fuentes <ruta>/Table_SITES_MacLoughin_2024.xlsx <ruta>/Tabla_Valdivia_2021.xlsx
Salida: manuscript/reanalysis/salidas/edna_normalizado/v2_fechas_*.csv, v2_fechas.md
"""
import argparse
import re
from pathlib import Path

import pandas as pd


def fmt(s):
    s = str(s).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return "F1 AAAA-xx-yy (xx<=12)" if int(s[5:7]) <= 12 else "F2 AAAA-xx-yy (xx>12)"
    if re.fullmatch(r"\d{2}-\d{2}-\d{2}", s):
        return "F3 AA-xx-yy"
    return "otro"


def read(s, order):
    s = str(s).strip()
    p = s.split("-")
    if len(p) != 3:
        return pd.NaT
    y = int(p[0]) + (2000 if len(p[0]) == 2 else 0)
    a, b = int(p[1]), int(p[2])
    m, d = (a, b) if order == "MD" else (b, a)
    try:
        return pd.Timestamp(year=y, month=m, day=d)
    except ValueError:
        return pd.NaT


def md(d):
    try:
        return d.to_markdown(index=False)
    except ImportError:
        return d.to_string(index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/insitu/taxonomy_corrected_edna_2.csv")
    ap.add_argument("--fuentes", nargs="*", default=[])
    ap.add_argument("--out", default=str(Path(__file__).with_name("salidas") / "edna_normalizado"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    v = pd.read_csv(a.csv)
    v = v[v.TableID.isin(["Mac_loughlin", "Valdivia"])].copy()
    v["formato"] = v.date.map(fmt)
    v["lect_MD"] = v.date.map(lambda s: read(s, "MD"))
    v["lect_DM"] = v.date.map(lambda s: read(s, "DM"))

    rows = []
    for (t, f), g in list(v.groupby(["TableID", "formato"])) + [((t, "TODOS"), g) for t, g in v.groupby("TableID")]:
        rec = {"TableID": t, "formato": f, "filas": len(g), "cadenas_distintas": g.date.nunique(),
               "ejemplos": ", ".join(sorted(g.date.unique())[:6])}
        for k, lab in [("lect_MD", "AAAA-MM-DD"), ("lect_DM", "AAAA-DD-MM")]:
            ok = g[g[k].notna()]
            rec.update({f"{lab}: válidas": len(ok),
                        f"{lab}: rango": f"{ok[k].min():%Y-%m-%d} a {ok[k].max():%Y-%m-%d}" if len(ok) else "—",
                        f"{lab}: fechas distintas": ok[k].nunique(),
                        f"{lab}: año-meses distintos": ok[k].dt.to_period("M").nunique(),
                        f"{lab}: muestras distintas": ok[["TableID", "Site_Name", "Depth", k]].astype(str).drop_duplicates().shape[0]})
        rows.append(rec)
    T = pd.DataFrame(rows).sort_values(["TableID", "formato"])
    T.to_csv(out / "v2_fechas_formatos.csv", index=False)

    sites = (v.groupby(["TableID", "Site_Name", "date"]).agg(lat=("Latitude", "first"), filas=("date", "size"))
             .reset_index())
    sites["lectura_AAAA-MM-DD"] = sites.date.map(lambda s: read(s, "MD"))
    sites["lectura_AAAA-DD-MM"] = sites.date.map(lambda s: read(s, "DM"))

    src_rows = []
    for f in a.fuentes:
        import openpyxl
        wb = openpyxl.load_workbook(f, read_only=True, data_only=False)
        ws = wb.worksheets[0]
        r = list(ws.iter_rows(values_only=True)); h = [str(x).strip() if x else "" for x in r[0]]
        dc = next(i for i, x in enumerate(h) if "date" in x.lower() or "fecha" in x.lower())
        nc = next((i for i, x in enumerate(h) if x.lower() in ("site name", "site_id")), 0)
        lc = next((i for i, x in enumerate(h) if x.lower() in ("lat", "latitude")), None)
        for row in r[1:]:
            val = row[dc]
            src_rows.append({"fuente": Path(f).name, "sitio_fuente": row[nc], "lat_fuente": row[lc] if lc is not None else None,
                             "fecha_en_fuente": val.strftime("%Y-%m-%d") if hasattr(val, "strftime") else str(val),
                             "tipo_en_fuente": "fecha de Excel" if hasattr(val, "strftime") else "texto"})
    S = pd.DataFrame(src_rows)
    if len(S):
        S.to_csv(out / "v2_fechas_fuentes.csv", index=False)
    sites.astype(str).to_csv(out / "v2_fechas_por_sitio.csv", index=False)
    with open(out / "v2_fechas.md", "w") as fh:
        fh.write("# v2: fechas crudas de Mac_loughlin y Valdivia\n\n" + md(T) + "\n\n## Por sitio (v2)\n\n"
                 + md(sites.sort_values(["TableID", "lectura_AAAA-DD-MM"]).astype(str)) + "\n")
        if len(S):
            fh.write("\n## Tablas de sitios de las fuentes\n\n" + md(S) + "\n")
    print((out / "v2_fechas.md").read_text())


if __name__ == "__main__":
    main()
