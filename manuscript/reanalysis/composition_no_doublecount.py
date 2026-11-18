#!/usr/bin/env python3
"""Composición sin doble conteo: partición de 5 grupos (DIATO, DINO, GREEN, HAPTO, PROKAR),
que cumple MICRO=DIATO+DINO, NANO=HAPTO, PICO=GREEN+PROKAR. PROCHLO se excluye
(es un subconjunto de los procariotas estimado por separado)."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'figures'))
from make_manuscript_figures import plotly_traces, RES
G5 = ['DIATO', 'DINO', 'GREEN', 'HAPTO', 'PROKAR']
J = json.loads((RES / 'tables/reporte_analisis_numerico.json').read_text())['variables']
d = pd.DataFrame(plotly_traces(RES / 'figures/timeseries/plotly_charts/species_composition_timeseries.html')).dropna()
d.columns = ['DIATO', 'DINO', 'GREEN', 'HAPTO', 'PROCHLO', 'PROKAR']
p5 = d[G5].div(d[G5].sum(axis=1), axis=0) * 100           # % mensual, 5 grupos
out = {}
m = {g: J[g]['temporal_statistics']['mean'] for g in G5}
out['ponderada_biomasa_2002_2024'] = {g: round(100 * m[g] / sum(m.values()), 1) for g in G5}
out['media_de_porcentajes_mensuales_2002_2024'] = p5.mean().round(1).to_dict()
for p in ['2000-2004', '2005-2009', '2010-2014', '2015-2019', '2020-2024']:
    q = {g: J[g]['quinquennial_statistics'][p]['mean'] for g in G5}
    out[f'ponderada_biomasa_{p}'] = {g: round(100 * q[g] / sum(q.values()), 1) for g in G5}
for a, b in [('2002-07', '2011-12'), ('2017', '2024')]:
    out[f'media_porcentajes_{a}_{b}'] = p5[a:b].mean().round(1).to_dict()
p5.to_csv(Path(__file__).with_name('composicion_5grupos_mensual.csv'))
print(json.dumps(out, indent=1))
json.dump(out, open(Path(__file__).with_name('composition_no_doublecount_resultados.json'), 'w'), indent=1)
