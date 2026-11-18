#!/usr/bin/env python3
"""
Análisis de la serie mensual de cuenca leídos directamente de un NetCDF mensual
(pft_monthly_statistics.nc = rectángulo, o pft_monthly_statistics_poligono.nc = polígono):

  (a) Composición de los 5 grupos de la partición sin doble conteo (DIATO, DINO, GREEN, HAPTO,
      PROKAR): ponderada por biomasa (media del grupo / suma de medias) y media de porcentajes
      mensuales, para 2002-07..2024-12, jul-2002..2011, 2017..2024 y quinquenios; clases de tamaño
      (MICRO, NANO, PICO como % de su suma); cociente PROCHLO/PROKAR por periodos y meses con
      PROCHLO > PROKAR por año. Mismo cálculo que composition_no_doublecount.py y
      prochlo_discontinuity.py, que leían las trazas plotly (hechas desde una versión anterior de la
      serie del rectángulo).
  (b) Escalones (escalon.py: Pettitt sobre la serie desestacionalizada + modelo de escalón con
      efectos de mes, p por 500 permutaciones de bloques de 12 meses) en ln(PROCHLO/PROKAR),
      ln(PROCHLO/total5), ln(DIATO/total5) y log10 de PROCHLO, GREEN, DIATO y CHL, jul-2002..dic-2024.
  (c) Medias quinquenales (media y DE con ddof=0 de los meses de cada quinquenio, como
      reporte_analisis_numerico.json) de todas las variables.
  Figuras 2 y 3 con las funciones de manuscript/figures/make_manuscript_figures.py, alimentadas con
  esta serie (sustituyendo la lectura de las trazas plotly y del JSON); la fecha del quiebre de la
  Fig. 2c es la de Pettitt de ln(PROCHLO/PROKAR).

Uso:  python3 manuscript/reanalysis/serie_cuenca.py --nc <NetCDF mensual> --etiqueta poligono
Salida: manuscript/reanalysis/salidas/<etiqueta>/serie_cuenca/
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "figures"))
import escalon  # noqa: E402

G5 = ["DIATO", "DINO", "GREEN", "HAPTO", "PROKAR"]
QUINQ = {"2000-2004": ("2000", "2004"), "2005-2009": ("2005", "2009"), "2010-2014": ("2010", "2014"),
         "2015-2019": ("2015", "2019"), "2020-2024": ("2020", "2024")}
PER = {"2002-2024": ("2002-07", "2024-12"), "jul2002-2011": ("2002-07", "2011-12"), "2017-2024": ("2017-01", "2024-12")}
SP_NAMES = {"Diatomeas": "DIATO", "Dinoflagelados": "DINO", "Algas Verdes": "GREEN", "Haptófitos": "HAPTO",
            "Proclorococcus": "PROCHLO", "Procariontes": "PROKAR"}
SZ_NAMES = {"Microfitoplancton (>20 μm)": "MICRO", "Nanofitoplancton (2-20 μm)": "NANO", "Picofitoplancton (<2 μm)": "PICO"}


def load(nc):
    ds = xr.open_dataset(nc)
    t = pd.DatetimeIndex(ds.time.values).to_period("M").to_timestamp()
    return pd.DataFrame({v[:-5]: ds[v].values for v in ds.data_vars if v.endswith("_mean")}, index=t), ds.attrs


def composition(D):
    out = {}
    p5 = D[G5].dropna(); p5 = p5.div(p5.sum(axis=1), axis=0) * 100
    sz = D[["MICRO", "NANO", "PICO"]].dropna(); szp = sz.div(sz.sum(axis=1), axis=0) * 100
    for k, (a, b) in {**PER, **{f"quinquenio {q}": v for q, v in QUINQ.items()}}.items():
        m = D.loc[a:b, G5].mean()
        out[f"5 grupos ponderada {k}"] = (100 * m / m.sum()).round(2).to_dict()
        if k in PER:
            out[f"5 grupos media de % mensuales {k}"] = p5[a:b].mean().round(2).to_dict()
            ms = D.loc[a:b, ["MICRO", "NANO", "PICO"]].mean()
            out[f"tamaños ponderada {k}"] = (100 * ms / ms.sum()).round(2).to_dict()
            out[f"tamaños media de % mensuales {k}"] = szp[a:b].mean().round(2).to_dict()
    r = (D.PROCHLO / D.PROKAR).dropna()
    out["PROCHLO/PROKAR medias"] = {k: round(float(r[a:b].mean()), 3) for k, (a, b) in
                                    {"2002-07..2015-12": ("2002-07", "2015-12"), "2016": ("2016", "2016"),
                                     "2017..2024": ("2017", "2024")}.items()}
    out["meses PROCHLO>PROKAR por año"] = {str(y): int((r[str(y)] > 1).sum()) for y in range(2002, 2025)}
    return out, p5, szp


def steps(D, n_perm):
    d = D.loc["2002-07":"2024-12"]
    tot = d[G5].sum(axis=1)
    series = {"ln(PROCHLO/PROKAR)": np.log(d.PROCHLO / d.PROKAR), "ln(PROCHLO/total5)": np.log(d.PROCHLO / tot),
              "ln(DIATO/total5)": np.log(d.DIATO / tot), "log10 PROCHLO": np.log10(d.PROCHLO),
              "log10 GREEN": np.log10(d.GREEN), "log10 DIATO": np.log10(d.DIATO), "log10 CHL": np.log10(d.CHL)}
    rows = []
    for k, y in series.items():
        r = escalon.detect(y.dropna(), n_perm=n_perm)
        r["factor"] = float(np.exp(r["escalon_delta"]) if k.startswith("ln") else 10 ** r["escalon_delta"])
        r.pop("escalon_factor_10^delta")
        rows.append({"serie": k, **r})
    return pd.DataFrame(rows)


def quinq(D):
    rows = []
    for v in D.columns:
        for q, (a, b) in QUINQ.items():
            s = D.loc[a:b, v].dropna()
            rows.append({"variable": v, "quinquenio": q, "media": float(s.mean()), "de": float(s.std(ddof=0)), "n": len(s)})
    return pd.DataFrame(rows)


def figures(D, Q, brk, out):
    import make_manuscript_figures as m
    def fake_traces(path):
        name = Path(path).name
        if "species" in name:
            d = D[list(SP_NAMES.values())].dropna(); d = d.div(d.sum(axis=1), axis=0) * 100
            return {k: d[v] for k, v in SP_NAMES.items()}
        d = D[list(SZ_NAMES.values())].dropna(); d = d.div(d.sum(axis=1), axis=0) * 100
        return {k: d[v] for k, v in SZ_NAMES.items()}
    with tempfile.TemporaryDirectory() as td:
        res = Path(td); (res / "tables").mkdir()
        J = {"variables": {v: {"quinquennial_statistics": {r.quinquenio: {"mean": r.media, "std": r.de, "count": r.n}
                                                           for r in Q[Q.variable == v].itertuples()}} for v in Q.variable.unique()}}
        (res / "tables" / "reporte_analisis_numerico.json").write_text(json.dumps(J))
        m.plotly_traces, m.RES, m.OUT, m.QUIEBRE_PROCHLO = fake_traces, res, out, str(brk.date())
        r = (D.PROCHLO / D.PROKAR).dropna()
        lo, hi = min(0.3, r.min() * 0.8), max(14, r.max() * 1.6)   # mismos límites que el original si caben
        m.FIG2C_YLIM = (lo, hi)
        m.FIG2C_YTICKS = [t for t in [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50] if lo <= t <= hi]
        m.FIG2C_ETIQUETA_Y = 9 if hi <= 14 else hi * 0.75
        m.fig_composicion(); m.fig_quinquenios()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nc", required=True)
    ap.add_argument("--etiqueta", required=True)
    ap.add_argument("--n-perm", type=int, default=500)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out or HERE / "salidas" / a.etiqueta / "serie_cuenca"); out.mkdir(parents=True, exist_ok=True)
    D, attrs = load(a.nc)
    comp, p5, szp = composition(D)
    json.dump(comp, open(out / "composicion.json", "w"), indent=1, ensure_ascii=False)
    p5.to_csv(out / "composicion_5grupos_mensual.csv"); szp.to_csv(out / "tamanos_mensual.csv")
    S = steps(D, a.n_perm); S.to_csv(out / "escalones.csv", index=False)
    Q = quinq(D); Q.to_csv(out / "quinquenios.csv", index=False)
    brk = pd.Timestamp(S.set_index("serie").loc["ln(PROCHLO/PROKAR)", "pettitt_fecha"])
    figures(D, Q, brk, out)
    with open(out / "resumen.md", "w") as f:
        f.write(f"# Serie de cuenca: {a.etiqueta}\n\nArchivo: `{a.nc}`; máscara: {attrs.get('filter_coverage', 'sin atributo')}\n\n")
        f.write("## (a) Composición\n\n```\n" + json.dumps(comp, indent=1, ensure_ascii=False) + "\n```\n\n")
        f.write("## (b) Escalones\n\n" + S.round(4).to_markdown(index=False) + "\n\n")
        f.write(f"Quiebre marcado en la Fig. 2c: {brk:%Y-%m}\n\n## (c) Quinquenios\n\n" + Q.round(4).to_markdown(index=False) + "\n")
    print((out / "resumen.md").read_text()[:4000])


if __name__ == "__main__":
    main()
