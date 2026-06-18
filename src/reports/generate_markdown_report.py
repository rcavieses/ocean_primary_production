#!/usr/bin/env python3
"""
Genera un reporte en Markdown con los resultados consolidados del análisis
de producción primaria fitoplanctónica del Golfo de California.

Incluye estadísticas numéricas, tablas de resultados y referencias a figuras.
Taxonomy: taxonomy_corrected_edna_2.csv (v2) por defecto.

Uso:
    python3 generate_markdown_report.py
    TAXONOMY_VERSION=v1 python3 generate_markdown_report.py
"""

import os
import csv
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    import xarray as xr
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
BASE_DIR = Path(__file__).parent.parent.parent
TAXONOMY_VERSION = os.environ.get('TAXONOMY_VERSION', 'v2')
TAXONOMY_FILENAME = ('taxonomy_corrected_edna.csv' if TAXONOMY_VERSION == 'v1'
                     else 'taxonomy_corrected_edna_2.csv')

RESULTS_SAT    = BASE_DIR / 'results' / 'satellite'
RESULTS_INSITU = BASE_DIR / 'results' / 'insitu' / f'edna_{TAXONOMY_VERSION}'
RESULTS_FIGS   = RESULTS_SAT / 'figures'
REPORT_DIR     = BASE_DIR / 'results' / 'reports'
REPORT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE    = REPORT_DIR / f'reporte_insitu_{TAXONOMY_VERSION}.md'

DATA_DIR       = BASE_DIR / 'data'
NETCDF_FILE    = DATA_DIR / 'processed' / 'pft_monthly_statistics.nc'

VAR_NAMES = {
    'CHL': 'Clorofila-a Total', 'DIATO': 'Diatomeas', 'DINO': 'Dinoflagelados',
    'GREEN': 'Algas Verdes',    'HAPTO': 'Haptófitos', 'MICRO': 'Microfitoplancton',
    'NANO': 'Nanofitoplancton', 'PICO': 'Picofitoplancton',
    'PROCHLO': 'Proclorococcus','PROKAR': 'Procariontes',
}

# ============================================================================
# HELPERS
# ============================================================================
def read_csv_safe(path):
    if not path.exists():
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def rel_to_report(fig_path):
    """Ruta relativa desde el directorio del reporte (results/reports/) a la figura."""
    return os.path.relpath(fig_path, OUTPUT_FILE.parent)

def find_pngs(directory, pattern='*.png'):
    if not directory or not directory.exists():
        return []
    return sorted(directory.glob(pattern))

def fmt(val, decimals=4):
    try:
        return f"{float(val):.{decimals}f}"
    except (ValueError, TypeError):
        return str(val)

# ============================================================================
# CARGA DE DATOS
# ============================================================================
def load_satellite_stats():
    """Lee el NetCDF procesado y devuelve estadísticas básicas por variable."""
    if not HAS_PANDAS or not NETCDF_FILE.exists():
        return {}
    ds = xr.open_dataset(NETCDF_FILE)
    stats = {}
    for var in VAR_NAMES:
        key = f'{var}_mean'
        if key not in ds:
            continue
        series = ds[key].values
        series = series[~np.isnan(series)]
        if len(series) == 0:
            continue
        stats[var] = {
            'media':  float(np.mean(series)),
            'std':    float(np.std(series)),
            'min':    float(np.min(series)),
            'max':    float(np.max(series)),
            'n_meses': len(series),
        }
    ds.close()
    return stats

def load_insitu_summary():
    """Lee los CSV de series de tiempo in-situ y resume por grupo."""
    series_dir = RESULTS_INSITU / 'series_tiempo'
    grupos = {}
    if not series_dir.exists():
        return grupos
    for csv_path in sorted(series_dir.glob('*_in_situ_timeseries.csv')):
        grupo = csv_path.stem.replace('_in_situ_timeseries', '').replace('_', ' ').title()
        rows = read_csv_safe(csv_path)
        if not rows:
            continue
        # Contar celdas con datos (no vacías)
        total = sum(
            1 for row in rows
            for v in list(row.values())[1:]  # skip mes column
            if v.strip() not in ('', 'nan', 'NaN')
        )
        grupos[grupo] = {'meses_con_datos': total}
    return grupos

def load_insitu_stats():
    """Lee los CSV de estadísticas mensuales in-situ."""
    series_dir = RESULTS_INSITU / 'series_tiempo'
    result = {}
    if not series_dir.exists():
        return result
    for csv_path in sorted(series_dir.glob('*_in_situ_monthly_stats.csv')):
        grupo = csv_path.stem.replace('_in_situ_monthly_stats', '').replace('_', ' ').title()
        rows = read_csv_safe(csv_path)
        if not rows:
            continue
        total = sum(int(r.get('Total_Registros', 0)) for r in rows)
        prom   = sum(float(r.get('Promedio_por_Año', 0)) for r in rows)
        result[grupo] = {'total_registros': total, 'prom_anual': prom / 12}
    return result

def load_depth_summary():
    """Lee el CSV de resumen de profundidad."""
    path = RESULTS_INSITU / 'profundidad' / 'resumen_estadistico_profundidad.csv'
    return read_csv_safe(path)

def load_crosscorr_summary():
    """Lee los CSVs de cross-correlación y extrae la correlación máxima por variable-índice."""
    corr_dir = RESULTS_SAT / 'tables' / 'correlations'
    result = []
    if not corr_dir.exists():
        return result
    for csv_path in sorted(corr_dir.glob('crosscorr_*_vs_*.csv')):
        parts = csv_path.stem.split('_vs_')
        if len(parts) < 2:
            continue
        var_raw = parts[0].replace('crosscorr_', '')
        idx = parts[1]
        var = var_raw.replace('_mean', '')
        rows = read_csv_safe(csv_path)
        if not rows:
            continue
        best = max(rows, key=lambda r: abs(float(r.get('correlation', 0) or 0)),
                   default=None)
        if best:
            result.append({
                'Variable': VAR_NAMES.get(var, var),
                'Índice': idx,
                'Correlación': fmt(best.get('correlation', ''), 3),
                'Lag (meses)': best.get('lag', ''),
                'p-valor': fmt(best.get('p_value', ''), 3),
            })
    return result

def load_hmm_summary():
    """Cuenta transiciones de régimen por variable."""
    hmm_dir = RESULTS_FIGS / 'hmm_regimen_change'
    result = []
    if not hmm_dir.exists():
        return result
    for csv_path in sorted(hmm_dir.glob('*_hmm_states.csv')):
        var_raw = csv_path.stem.replace('_hmm_states', '').split('_')[0]
        rows = read_csv_safe(csv_path)
        if not rows:
            continue
        states = [int(r.get('state', -1)) for r in rows if r.get('state', '').strip()]
        transitions = sum(1 for i in range(1, len(states)) if states[i] != states[i-1])
        result.append({
            'Variable': VAR_NAMES.get(var_raw, var_raw),
            'N transiciones': transitions,
            'Meses estado alto': states.count(1),
            'Meses estado bajo': states.count(0),
        })
    return result

# ============================================================================
# SECCIONES DEL REPORTE
# ============================================================================
lines = []

def h(level, text):
    lines.append(f"\n{'#' * level} {text}\n")

def p(text):
    lines.append(f"{text}\n")

def table(headers, rows):
    if not rows:
        lines.append("*Sin datos disponibles.*\n")
        return
    lines.append('| ' + ' | '.join(headers) + ' |')
    lines.append('|' + '|'.join([' --- '] * len(headers)) + '|')
    for row in rows:
        if isinstance(row, dict):
            vals = [str(row.get(h, '')) for h in headers]
        else:
            vals = [str(v) for v in row]
        lines.append('| ' + ' | '.join(vals) + ' |')
    lines.append('')


def section_portada():
    h(1, 'Reporte de Análisis — Producción Primaria Fitoplanctónica')
    h(2, 'Golfo de California (2000–2024)')
    p(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
    p(f"**Taxonomía in-situ:** `{TAXONOMY_FILENAME}` (versión {TAXONOMY_VERSION})  ")
    p(f"**Fuente satelital:** MODIS Aqua Level-3, 4 km, mensual  ")
    p(f"**Período:** Enero 2000 – Diciembre 2024 (300 meses)  ")
    p("---")


def section_satellite_stats(stats):
    h(2, '1. Estadísticas Satelitales por Variable (2000–2024)')
    p("Concentraciones mensuales promediadas espacialmente sobre el Golfo de California (mg m⁻³).")
    headers = ['Variable', 'Nombre', 'Media', 'Desv. Est.', 'Mínimo', 'Máximo']
    rows = []
    for var, s in stats.items():
        rows.append({
            'Variable': var,
            'Nombre': VAR_NAMES.get(var, var),
            'Media': fmt(s['media']),
            'Desv. Est.': fmt(s['std']),
            'Mínimo': fmt(s['min']),
            'Máximo': fmt(s['max']),
        })
    table(headers, rows)


def section_insitu_summary(monthly_stats):
    h(2, '2. Datos In-Situ eDNA — Resumen por Grupo Taxonómico')
    p(f"Archivo: `{TAXONOMY_FILENAME}` · Período válido: 2000–2024")

    headers = ['Grupo', 'Total Registros', 'Promedio Mensual/Año']
    rows = []
    total_global = 0
    for grupo, s in sorted(monthly_stats.items()):
        total_global += s['total_registros']
        rows.append({
            'Grupo': grupo,
            'Total Registros': f"{s['total_registros']:,}",
            'Promedio Mensual/Año': fmt(s['prom_anual'], 1),
        })
    rows.append({'Grupo': '**TOTAL**', 'Total Registros': f"**{total_global:,}**",
                 'Promedio Mensual/Año': ''})
    table(headers, rows)


def section_depth(depth_rows):
    h(2, '3. Análisis por Profundidad')
    p("Distribución de abundancia eDNA por capa de profundidad: "
      "Superficial (1–26 m), Intermedia (35–140 m), Profunda (220–1000 m).")
    if depth_rows:
        headers = list(depth_rows[0].keys())
        table(headers, depth_rows)
    else:
        p("*Sin datos de profundidad disponibles.*")

    # Figuras de profundidad
    figs = find_pngs(RESULTS_INSITU / 'profundidad')
    if figs:
        h(3, 'Figuras — Análisis de Profundidad')
        for f in figs:
            rel = rel_to_report(f)
            p(f"**{f.stem}**  ")
            p(f"![{f.stem}]({rel})  ")
            p("")


def section_insitu_figures():
    h(2, '4. Series Temporales In-Situ (Figuras)')
    figs_dir = RESULTS_INSITU / 'series_tiempo' / 'figuras_primarios'
    figs = find_pngs(figs_dir)
    if not figs:
        p("*Sin figuras generadas.*")
        return
    for f in figs:
        rel = rel_to_report(f)
        p(f"**{f.stem}**  ")
        p(f"![{f.stem}]({rel})  ")
        p("")


def section_crosscorr(corr_rows):
    h(2, '5. Correlación Cruzada con Índices Climáticos')
    p("Correlación de Pearson con desfases 0–6 meses entre anomalías de biomasa "
      "e índices MEI, NIÑO3.4, PDO. Significancia por 1,000 permutaciones.")
    if corr_rows:
        headers = ['Variable', 'Índice', 'Correlación', 'Lag (meses)', 'p-valor']
        table(headers, corr_rows)
    else:
        p("*Resultados no disponibles — ejecutar `cross_correlation_permutation.py`.*")


def section_hmm(hmm_rows):
    h(2, '6. Cambios de Régimen (HMM)')
    p("Modelos Ocultos de Markov (2 estados) para detectar transiciones entre regímenes "
      "productivos alto y bajo.")
    if hmm_rows:
        headers = ['Variable', 'N transiciones', 'Meses estado alto', 'Meses estado bajo']
        table(headers, hmm_rows)
    else:
        p("*Resultados no disponibles — ejecutar `hmm_regimen_change.py`.*")


def section_satellite_figures():
    h(2, '7. Figuras Satelitales')

    sections_figs = [
        ('Mapas de Concentración Media', RESULTS_FIGS / 'maps', '*_mean_map.png'),
        ('Series Temporales con Índices Climáticos', RESULTS_FIGS / 'timeseries' / 'timeseries_indices', '*.png'),
        ('Descomposición STL', RESULTS_FIGS / 'stl_decomposition', '*_stl_decomposition.png'),
        ('Análisis Fourier', RESULTS_FIGS / 'fourier_analysis', '*_fourier_spectrum.png'),
        ('Cambios de Régimen HMM', RESULTS_FIGS / 'hmm_regimen_change', '*_hmm_regimen.png'),
        ('Correlación Canónica (CCA)', RESULTS_FIGS / 'canonical_correlation', '*.png'),
        ('Extremos Alternativos (PELT)', RESULTS_FIGS / 'extremos_alternativos', '*.png'),
        ('Regresión Segmentada', RESULTS_FIGS / 'piecewise_regression', '*.png'),
        ('Extremos Conjuntos', RESULTS_FIGS / 'joint_extremes', '*.png'),
        ('Causalidad de Granger', RESULTS_FIGS / 'granger_causality', '*.png'),
    ]

    for titulo, directory, pattern in sections_figs:
        figs = find_pngs(directory, pattern)
        if not figs:
            continue
        h(3, titulo)
        for f in figs[:5]:  # máx 5 por sección para mantener el reporte manejable
            rel = rel_to_report(f)
            p(f"**{f.stem}**  ")
            p(f"![{f.stem}]({rel})  ")
            p("")
        if len(figs) > 5:
            p(f"*... y {len(figs) - 5} figuras más en `{directory.relative_to(BASE_DIR)}/`*\n")


def section_metodologia():
    h(2, '8. Metodología Resumida')
    p("| Análisis | Método | Software |")
    p("| --- | --- | --- |")
    p("| Datos satelitales | MODIS Aqua L3, 4 km, mensual (Copernicus Marine) | `xarray`, `netCDF4` |")
    p("| Índices climáticos | MEI, NIÑO3.4, PDO (NOAA) | `pandas` |")
    p("| Datos in-situ | eDNA — Golfo de California | `pandas` |")
    p("| Descomposición temporal | STL (Loess) | `statsmodels` |")
    p("| Cambios de régimen | HMM 2 estados | `hmmlearn` |")
    p("| Causalidad | Granger F-test, lags 1–6 | `statsmodels` |")
    p("| Correlación cruzada | Pearson + 1,000 permutaciones | `numpy`, `scipy` |")
    p("| Correlación canónica | CCA | `sklearn` |")
    p("| Regresión segmentada | Piecewise breakpoint | `pwlf` |")
    p("| Extremos conjuntos | Percentiles p10/p90 co-ocurrencia | `pandas` |")
    p("")


def section_estructura():
    h(2, '9. Estructura de Resultados')
    p("```")
    p("results/")
    p("├── satellite/")
    p("│   ├── figures/         ← Mapas, series temporales, análisis estadísticos")
    p("│   └── tables/          ← CSVs de correlaciones, regresiones, extremos")
    p("├── insitu/")
    p(f"│   ├── edna_v1/         ← taxonomy_corrected_edna.csv (188,325 registros)")
    p(f"│   │   ├── series_tiempo/")
    p(f"│   │   └── profundidad/")
    p(f"│   └── edna_v2/         ← taxonomy_corrected_edna_2.csv (17,015 registros) ← ACTIVO")
    p(f"│       ├── series_tiempo/")
    p(f"│       └── profundidad/")
    p("└── reports/")
    p("    ├── index.html        ← Reporte HTML interactivo (20 secciones)")
    p(f"    └── reporte_insitu_{TAXONOMY_VERSION}.md  ← Este archivo")
    p("```")


def section_comparacion():
    h(2, '10. Comparación v1 vs v2')
    p("| Métrica | edna_v1 | edna_v2 (activo) |")
    p("| --- | --- | --- |")
    p("| Registros válidos 2000–2024 | 188,325 | 17,015 |")
    p("| Grupos taxonómicos | 6 (sin Diatomeas) | 6 (con Diatomeas) |")
    p("| Diatomeas (Bacillariophyta) | Clasificadas como *Otros* | Grupo separado ✓ |")
    p("| Formato fecha | Serial Excel | ISO 8601 |")
    p("| Columna profundidad | 3 cols (Shallow/Mid/Deep) | 1 col `Depth` (m) |")
    p("| Abundancia | Conteo registros | `Abundance` explícita |")
    p("")


# ============================================================================
# EJECUCIÓN
# ============================================================================
def main():
    print(f"Generando reporte Markdown (taxonomía {TAXONOMY_VERSION})...")

    sat_stats   = load_satellite_stats()
    insitu_stats = load_insitu_stats()
    depth_rows  = load_depth_summary()
    corr_rows   = load_crosscorr_summary()
    hmm_rows    = load_hmm_summary()

    section_portada()
    section_satellite_stats(sat_stats)
    section_insitu_summary(insitu_stats)
    section_depth(depth_rows)
    section_insitu_figures()
    section_crosscorr(corr_rows)
    section_hmm(hmm_rows)
    section_satellite_figures()
    section_metodologia()
    section_estructura()
    section_comparacion()

    h(2, 'Notas')
    p("- Reporte generado automáticamente por `src/reports/generate_markdown_report.py`.")
    p("- Para cambiar la versión de taxonomía: `TAXONOMY_VERSION=v1 python3 generate_markdown_report.py`")
    p("- Reporte HTML completo con figuras interactivas: `results/reports/index.html`")

    content = '\n'.join(lines)
    OUTPUT_FILE.write_text(content, encoding='utf-8')
    size_kb = OUTPUT_FILE.stat().st_size / 1024
    print(f"  ✓ {OUTPUT_FILE}  ({size_kb:.1f} KB)")


if __name__ == '__main__':
    main()
