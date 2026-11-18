#!/usr/bin/env python3
"""Detección de un escalón (cambio de nivel) en una serie mensual.

Mismo método que prochlo_discontinuity.py (que no se puede importar porque ejecuta
su análisis al cargarse):
  - Pettitt sobre la serie desestacionalizada.
  - Modelo y ~ efectos de mes + escalón(t >= tau); tau se busca entre el 20 % y el 80 %
    del registro minimizando la SCR; prueba F frente al modelo sin escalón, con valor p
    por permutación de bloques de 12 meses (la búsqueda de tau infla la F nominal).
"""
import numpy as np
import pandas as pd


def deseason(y):
    return y - y.groupby(y.index.month).transform("mean")


def pettitt(x):
    x = np.asarray(x); n = len(x)
    U = np.array([np.sign(x[:t, None] - x[None, t:]).sum() for t in range(1, n)])
    k = int(np.argmax(np.abs(U))); K = abs(U[k])
    p = 2 * np.exp(-6 * K ** 2 / (n ** 3 + n ** 2))
    return k + 1, int(K), float(min(p, 1.0))


def _ssr(X, y):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    return float(r @ r), b


def step_search(y, n_perm=500, seed=0):
    """Devuelve (fecha_tau, delta, F, p_perm) para y (pd.Series mensual sin huecos)."""
    n = len(y); v = y.values
    M = pd.get_dummies(y.index.month).values.astype(float)
    ssr0, _ = _ssr(M, v)
    best = None
    for tau in range(int(.2 * n), int(.8 * n)):
        s, b = _ssr(np.hstack([M, (np.arange(n) >= tau).astype(float)[:, None]]), v)
        if best is None or s < best[0]:
            best = (s, tau, b[-1])
    s1, tau, delta = best
    F = (ssr0 - s1) / (s1 / (n - 13))
    rng = np.random.default_rng(seed)
    blocks = [v[i:i + 12] for i in range(0, n, 12)]
    Fs = []
    for _ in range(n_perm):
        vp = np.concatenate([blocks[i] for i in rng.permutation(len(blocks))])[:n]
        s0p, _ = _ssr(M, vp)
        sb = min(_ssr(np.hstack([M, (np.arange(n) >= t).astype(float)[:, None]]), vp)[0]
                 for t in range(int(.2 * n), int(.8 * n), 3))
        Fs.append((s0p - sb) / (sb / (n - 13)))
    p_perm = (np.sum(np.array(Fs) >= F) + 1) / (len(Fs) + 1)
    return y.index[tau], float(delta), float(F), float(p_perm)


def detect(y, n_perm=500):
    """Pettitt + modelo de escalón. y en la escala en que se quiere medir el salto (p. ej. log10)."""
    k, K, p = pettitt(deseason(y).values)
    tau, delta, F, pp = step_search(y, n_perm=n_perm)
    return {"pettitt_fecha": str(y.index[k].date()), "pettitt_K": K, "pettitt_p": p,
            "escalon_fecha": str(tau.date()), "escalon_delta": delta, "escalon_factor_10^delta": float(10 ** delta),
            "F": F, "p_permutacion_bloques": pp}
