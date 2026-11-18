#!/usr/bin/env python3
"""Prueba de discontinuidad en Prochlorococcus (2016-2017) con series SIN escala
derivadas de la composición porcentual mensual (filtrada al Golfo):
  R1 = PROCHLO / PROKAR      (un subconjunto no puede exceder al total)
  R2 = PROCHLO / (DIATO+DINO+GREEN+HAPTO+PROKAR)
Pruebas: Pettitt sobre log-cociente desestacionalizado y modelo de escalón con
efectos mensuales (búsqueda del punto de quiebre que minimiza la SCR + prueba F).
"""
import sys, json
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'figures'))
from make_manuscript_figures import plotly_traces, RES

sp = plotly_traces(RES / 'figures/timeseries/plotly_charts/species_composition_timeseries.html')
d = pd.DataFrame(sp).dropna()
d.columns = ['DIATO', 'DINO', 'GREEN', 'HAPTO', 'PROCHLO', 'PROKAR']
s5 = d[['DIATO', 'DINO', 'GREEN', 'HAPTO', 'PROKAR']].sum(axis=1)
series = {'log(PROCHLO/PROKAR)': np.log(d.PROCHLO / d.PROKAR),
          'log(PROCHLO/total5)': np.log(d.PROCHLO / s5),
          'log(DIATO/total5)': np.log(d.DIATO / s5)}

def deseason(y):
    return y - y.groupby(y.index.month).transform('mean')

def pettitt(x):
    x = np.asarray(x); n = len(x)
    U = np.array([np.sign(x[:t, None] - x[None, t:]).sum() for t in range(1, n)])
    k = int(np.argmax(np.abs(U))); K = abs(U[k])
    p = 2 * np.exp(-6 * K**2 / (n**3 + n**2))
    return k + 1, K, min(p, 1.0)

def step_model(y):
    """y ~ mes + escalón(t>=tau); busca tau (20%-80% del registro)."""
    n = len(y); M = pd.get_dummies(y.index.month).values.astype(float)
    def ssr(X):
        b, *_ = np.linalg.lstsq(X, y.values, rcond=None); r = y.values - X @ b
        return r @ r, b
    ssr0, _ = ssr(M)
    best = None
    for tau in range(int(.2 * n), int(.8 * n)):
        step = (np.arange(n) >= tau).astype(float)[:, None]
        s, b = ssr(np.hstack([M, step]))
        if best is None or s < best[0]: best = (s, tau, b[-1])
    s1, tau, delta = best
    F = (ssr0 - s1) / (s1 / (n - 13))
    # el punto de quiebre se eligió por búsqueda: valor p de Andrews (aprox.) con
    # permutación por bloques de 12 meses para no sobreestimar la significancia
    rng = np.random.default_rng(0); blocks = [y.values[i:i+12] for i in range(0, n, 12)]
    Fs = []
    for _ in range(500):
        yp = pd.Series(np.concatenate([blocks[i] for i in rng.permutation(len(blocks))])[:n], index=y.index)
        s0p, _ = ssr_of(M, yp)
        sb = min(ssr_of(np.hstack([M, (np.arange(n) >= t).astype(float)[:, None]]), yp)[0]
                 for t in range(int(.2 * n), int(.8 * n), 3))
        Fs.append((s0p - sb) / (sb / (n - 13)))
    p_perm = (np.sum(np.array(Fs) >= F) + 1) / (len(Fs) + 1)
    return y.index[tau], delta, F, p_perm

def ssr_of(X, y):
    b, *_ = np.linalg.lstsq(X, y.values, rcond=None); r = y.values - X @ b
    return r @ r, b

out = {}
for name, y in series.items():
    k, K, p = pettitt(deseason(y).values)
    tau, delta, F, pp = step_model(y)
    pre, post = y[:tau].iloc[-24:], y[tau:].iloc[:24]
    out[name] = dict(pettitt_fecha=str(y.index[k].date()), pettitt_K=int(K), pettitt_p=float(p),
                     escalon_fecha=str(tau.date()), escalon_delta_log=float(delta),
                     escalon_factor=float(np.exp(delta)), F=float(F), p_permutacion_bloques=float(pp))
ratio = d.PROCHLO / d.PROKAR
out['PROCHLO/PROKAR'] = {p: float(ratio[a:b].mean()) for p, (a, b) in
                         {'2002-07..2015-12': ('2002-07', '2015-12'), '2016': ('2016', '2016'),
                          '2017..2024': ('2017', '2024')}.items()}
out['meses_con_PROCHLO_mayor_que_PROKAR'] = {str(yr): int((ratio[str(yr)] > 1).sum()) for yr in range(2002, 2025)}
print(json.dumps(out, indent=1, ensure_ascii=False))
json.dump(out, open(__file__.replace('.py', '_resultados.json'), 'w'), indent=1, ensure_ascii=False)
