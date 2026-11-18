#!/usr/bin/env python3
"""
Tablas "rectángulo -> polígono" de todos los análisis que usan la serie mensual de cuenca, a partir
de las salidas en salidas/rectangulo/ y salidas/poligono/ (mismos scripts y parámetros).

Cada fila: análisis, cifra, valor del manuscrito si se conoce por los archivos de resultados que
lo alimentaron (composition_no_doublecount_resultados.json, prochlo_discontinuity_resultados.json,
reporte_analisis_numerico.json y los valores del HMM citados en el manuscrito), rectángulo,
polígono y cambio:
  "signo"          la estimación cambia de signo;
  "significancia"  la q (o la p si no hay q) cruza 0.05;
  "fecha"          cambia una fecha (escalón, quiebre, meses del HMM);
  "definición"     pasa de definido a no definido o al revés.
Uso:  python3 manuscript/reanalysis/comparar_rect_poligono.py
Salida: salidas/poligono/comparacion/rect_vs_poligono.csv, cambios.csv, tablas.md
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROWS = []


def add(analisis, cifra, rect, pol, tipo="valor", manus=None, q_rect=None, q_pol=None):
    ROWS.append({"analisis": analisis, "cifra": cifra, "manuscrito": manus, "rectangulo": rect, "poligono": pol,
                 "tipo": tipo, "q_rect": q_rect, "q_pol": q_pol})


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def cambio(r):
    out = []
    a, b = num(r.rectangulo), num(r.poligono)
    if r.tipo == "estimacion" and np.isfinite(a) and np.isfinite(b) and np.sign(a) != np.sign(b) and a != 0 and b != 0:
        out.append("signo")
    if r.tipo == "estimacion" and (np.isfinite(a) != np.isfinite(b)):
        out.append("definición")
    qa, qb = num(r.q_rect), num(r.q_pol)
    if np.isfinite(qa) and np.isfinite(qb) and (qa < 0.05) != (qb < 0.05):
        out.append("significancia")
    if r.tipo == "fecha" and str(r.rectangulo) != str(r.poligono):
        out.append("fecha")
    return ", ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(HERE / "salidas"))
    ap.add_argument("--json-original", default=None, help="reporte_analisis_numerico.json (valores de los quinquenios del manuscrito)")
    a = ap.parse_args()
    d = Path(a.dir); R, P = d / "rectangulo", d / "poligono"
    out = P / "comparacion"; out.mkdir(parents=True, exist_ok=True)

    # (a) composición
    cr, cp = (json.load(open(x / "serie_cuenca" / "composicion.json")) for x in (R, P))
    man_c = json.load(open(HERE / "composition_no_doublecount_resultados.json"))
    man_p = json.load(open(HERE / "prochlo_discontinuity_resultados.json"))
    mkey = {"5 grupos ponderada 2002-2024": "ponderada_biomasa_2002_2024",
            "5 grupos media de % mensuales 2002-2024": "media_de_porcentajes_mensuales_2002_2024",
            "5 grupos media de % mensuales jul2002-2011": "media_porcentajes_2002-07_2011-12",
            "5 grupos media de % mensuales 2017-2024": "media_porcentajes_2017_2024"}
    for k in cr:
        if k.startswith(("5 grupos", "tamaños")):
            for g in cr[k]:
                mk = mkey.get(k) or ("ponderada_biomasa_" + k.split("quinquenio ")[1] if "quinquenio" in k else None)
                add("a) composición", f"{k}: {g} (%)", cr[k][g], cp[k][g], manus=man_c.get(mk, {}).get(g) if mk else None)
    for k in cr["PROCHLO/PROKAR medias"]:
        add("a) composición", f"PROCHLO/PROKAR media {k}", cr["PROCHLO/PROKAR medias"][k], cp["PROCHLO/PROKAR medias"][k],
            manus=man_p["PROCHLO/PROKAR"].get(k))
    for per in [("2002", "2015"), ("2016", "2016"), ("2017", "2024")]:
        f = lambda c: sum(v for y, v in c["meses PROCHLO>PROKAR por año"].items() if per[0] <= y <= per[1])
        add("a) composición", f"meses con PROCHLO>PROKAR {per[0]}-{per[1]}", f(cr), f(cp),
            manus=sum(v for y, v in man_p["meses_con_PROCHLO_mayor_que_PROKAR"].items() if per[0] <= y <= per[1]))
    # (b) escalones
    er, ep = (pd.read_csv(x / "serie_cuenca" / "escalones.csv").set_index("serie") for x in (R, P))
    mp = {"ln(PROCHLO/PROKAR)": "log(PROCHLO/PROKAR)", "ln(PROCHLO/total5)": "log(PROCHLO/total5)", "ln(DIATO/total5)": "log(DIATO/total5)"}
    for s in er.index:
        m = man_p.get(mp.get(s, ""), {})
        add("b) escalones", f"{s}: fecha Pettitt", er.loc[s, "pettitt_fecha"][:7], ep.loc[s, "pettitt_fecha"][:7], "fecha",
            manus=m.get("pettitt_fecha", "")[:7] or None)
        add("b) escalones", f"{s}: fecha del escalón", er.loc[s, "escalon_fecha"][:7], ep.loc[s, "escalon_fecha"][:7], "fecha",
            manus=m.get("escalon_fecha", "")[:7] or None)
        add("b) escalones", f"{s}: factor del escalón", round(er.loc[s, "factor"], 3), round(ep.loc[s, "factor"], 3),
            manus=round(m["escalon_factor"], 3) if "escalon_factor" in m else None)
        add("b) escalones", f"{s}: F (p perm.)", f"{er.loc[s, 'F']:.1f} ({er.loc[s, 'p_permutacion_bloques']:.3f})",
            f"{ep.loc[s, 'F']:.1f} ({ep.loc[s, 'p_permutacion_bloques']:.3f})", q_rect=er.loc[s, "p_permutacion_bloques"],
            q_pol=ep.loc[s, "p_permutacion_bloques"])
    # (c) quinquenios
    qr, qp = (pd.read_csv(x / "serie_cuenca" / "quinquenios.csv").set_index(["variable", "quinquenio"]) for x in (R, P))
    J = json.load(open(a.json_original))["variables"] if a.json_original else {}
    for (v, q) in qr.index:
        add("c) quinquenios", f"{v} {q}: media (mg m-3)", round(qr.loc[(v, q), "media"], 4), round(qp.loc[(v, q), "media"], 4),
            manus=round(J[v]["quinquennial_statistics"][q]["mean"], 4) if v in J else None)
    for v in qr.index.get_level_values(0).unique():
        for x, lab in [(qr, "rect"), (qp, "pol")]:
            pass
        r0, r1 = qr.loc[(v, "2020-2024"), "media"], qr.loc[(v, "2005-2009"), "media"]
        p0, p1 = qp.loc[(v, "2020-2024"), "media"], qp.loc[(v, "2005-2009"), "media"]
        add("c) quinquenios", f"{v}: cambio 2020-2024 vs 2005-2009 (%)", round(100 * (r0 / r1 - 1), 1), round(100 * (p0 / p1 - 1), 1), "estimacion")
        imr = qr.loc[v, "media"].idxmax(); imp = qp.loc[v, "media"].idxmax()
        add("c) quinquenios", f"{v}: quinquenio con la media más alta", imr, imp, "fecha")
    # (d) STL y HMM
    sr, sp = (pd.read_csv(x / "stl" / "stl_huecos.csv").set_index("variable") for x in (R, P))
    for v in sr.index:
        for c in ["amplitud_estacional_antes_2012", "amplitud_estacional_desde_2012", "tendencia_inicio", "tendencia_fin"]:
            add("d) STL", f"{v}: {c}", round(sr.loc[v, c], 4), round(sp.loc[v, c], 4))
        add("d) STL", f"{v}: amplitud desde 2012 / antes", round(sr.loc[v, c.replace(c, 'amplitud_estacional_desde_2012')] / sr.loc[v, 'amplitud_estacional_antes_2012'], 3),
            round(sp.loc[v, 'amplitud_estacional_desde_2012'] / sp.loc[v, 'amplitud_estacional_antes_2012'], 3))
        add("d) STL", f"{v}: tendencia fin - inicio", round(sr.loc[v, 'tendencia_fin'] - sr.loc[v, 'tendencia_inicio'], 4),
            round(sp.loc[v, 'tendencia_fin'] - sp.loc[v, 'tendencia_inicio'], 4), "estimacion")
    hr, hp = (pd.read_csv(x / "hmm" / "hmm_semillas.csv") for x in (R, P))
    br, bp = hr[hr.mejor].iloc[0], hp[hp.mejor].iloc[0]
    man_h = {"media_alta": 0.111, "media_baja": 0.034, "pct_alto_jul2002-2011": 54, "pct_alto_2012-2015": 19, "pct_alto_2016-2024": 14,
             "meses_alto_2014-2017": 0}
    for c in man_h:
        add("d) HMM (máx. verosimilitud)", c, round(br[c], 4), round(bp[c], 4), manus=man_h[c])
    add("d) HMM (máx. verosimilitud)", "meses altos 2014-2017", br["meses_alto_2014-2017_lista"] if isinstance(br["meses_alto_2014-2017_lista"], str) else "ninguno",
        bp["meses_alto_2014-2017_lista"] if isinstance(bp["meses_alto_2014-2017_lista"], str) else "ninguno", "fecha", manus="ninguno")
    for lab, h in [("rect", hr), ("pol", hp)]:
        pass
    add("d) HMM (máx. verosimilitud)", "soluciones distintas en 20 semillas / convergencias estrictas",
        f"{hr[hr.ajuste.str.startswith('B ')].solucion_id.nunique()} / {int(hr.convergio_estricto.fillna(False).astype(bool).sum())}",
        f"{hp[hp.ajuste.str.startswith('B ')].solucion_id.nunique()} / {int(hp.convergio_estricto.fillna(False).astype(bool).sum())}")
    # (e) Granger
    gr_, gp_ = (pd.read_csv(x / "granger" / "tabla_suplementaria_granger.csv") for x in (R, P))
    for (_, r), (_, p) in zip(gr_.iterrows(), gp_.iterrows()):
        assert (r.familia, r.grupo, r.indice) == (p.familia, p.grupo, p.indice)
        key = f"{r.familia}: {r.grupo} <- {r.indice}"
        add("e) Granger", key + " p (desfase AIC)", f"{r.p:.4f} ({r.desfase_AIC})", f"{p.p:.4f} ({p.desfase_AIC})", q_rect=r.q_BH, q_pol=p.q_BH)
        add("e) Granger", key + " q BH", round(r.q_BH, 4), round(p.q_BH, 4), q_rect=r.q_BH, q_pol=p.q_BH)
    # (f) tendencias
    tr, tp = (pd.read_csv(x / "tendencias" / "tendencias_GREEN_escalon.csv") for x in (R, P))
    for (_, r), (_, p) in zip(tr.iterrows(), tp.iterrows()):
        m = r.modelo.split(" ")[0]
        add("f) tendencias GREEN", f"{m} periodo", r.periodo, p.periodo, "fecha")
        add("f) tendencias GREEN", f"{m} pendiente (mg m-3/año) [IC95]", round(r.pendiente_mg_m3_por_anio, 5), round(p.pendiente_mg_m3_por_anio, 5),
            "estimacion", q_rect=r.p_HAC_NW12, q_pol=p.p_HAC_NW12)
        add("f) tendencias GREEN", f"{m} IC95", f"[{r.IC95_inf_por_anio:.5f}, {r.IC95_sup_por_anio:.5f}]", f"[{p.IC95_inf_por_anio:.5f}, {p.IC95_sup_por_anio:.5f}]")
        add("f) tendencias GREEN", f"{m} p HAC", round(r.p_HAC_NW12, 4), round(p.p_HAC_NW12, 4), q_rect=r.p_HAC_NW12, q_pol=p.p_HAC_NW12)
        add("f) tendencias GREEN", f"{m} % de la media por década", round(r.pct_media_por_decada, 1), round(p.pct_media_por_decada, 1), "estimacion")
    # (g) ENSO
    er_, ep_ = (pd.read_csv(x / "enso" / "composicion_por_fase.csv").set_index("fase") for x in (R, P))
    for f_ in er_.index:
        for c in ["DIATO", "DINO", "GREEN", "HAPTO", "PROKAR", "CHL_media_mg_m3"]:
            add("g) ENSO composición", f"{f_}: {c}", er_.loc[f_, c], ep_.loc[f_, c])
    for fn, val in [("anomalia_biomasa_por_fase.csv", "anomalia_pct"), ("anomalia_composicion_por_fase.csv", "anomalia_composicion_pp")]:
        ar, apl = (pd.read_csv(x / "enso" / fn) for x in (R, P))
        ar, apl = ar[ar.fase != "Neutral"], apl[apl.fase != "Neutral"]
        vc = "variable" if "variable" in ar else "grupo"
        for (_, r), (_, p) in zip(ar.iterrows(), apl.iterrows()):
            add("g) ENSO " + ("anomalía biomasa (%)" if "biomasa" in fn else "anomalía composición (pp)"),
                f"{r.analisis.split(' ')[0]} {r[vc]} {r.fase}", round(r[val], 2), round(p[val], 2), "estimacion", q_rect=r.q_BH, q_pol=p.q_BH)
    # (h) eDNA
    xr_, xp_ = (pd.read_csv(x / "edna_normalizado" / "correlaciones.csv") for x in (R, P))
    for (_, r), (_, p) in zip(xr_.iterrows(), xp_.iterrows()):
        if "(i)" not in r.satelite:
            continue
        lab = f"{r.grupo}, {r.unidad}, {r.variable_in_situ}"
        q1, q2 = (r.q_principal_pearson, p.q_principal_pearson) if r.variable_principal else (r.q_todas_pearson, p.q_todas_pearson)
        add("h) eDNA (i) cuenca", lab + " r Pearson (p)", round(r.pearson_r, 3), round(p.pearson_r, 3), "estimacion", q_rect=q1, q_pol=q2)
        if r.variable_principal and np.isfinite(num(r.logit_p_LR)):
            add("h) eDNA (i) cuenca", lab + " logística p LR (q)", round(r.logit_p_LR, 4), round(p.logit_p_LR, 4),
                q_rect=r.q_principal_logit, q_pol=p.q_principal_logit)

    T = pd.DataFrame(ROWS)
    T["cambio"] = T.apply(cambio, axis=1)
    T.to_csv(out / "rect_vs_poligono.csv", index=False)
    C = T[T.cambio != ""]
    C.to_csv(out / "cambios.csv", index=False)
    with open(out / "tablas.md", "w") as f:
        for an, g in T.groupby("analisis", sort=False):
            f.write(f"## {an}\n\n" + g.drop(columns=["analisis", "tipo"]).to_markdown(index=False) + "\n\n")
    print(f"{len(T)} cifras; {len(C)} con cambio de signo/significancia/fecha/definición")
    print(C.groupby(["analisis", "cambio"]).size().to_string())


if __name__ == "__main__":
    main()
