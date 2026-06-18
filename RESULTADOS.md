# Bitácora de Resultados

Registro del estado de cada script: cuándo se ejecutó por última vez, qué produce y si los resultados son válidos.

**Estado:** ✓ Completado | ⚠ Revisar | ✗ Pendiente | ▶ En curso

---

## Preprocesamiento

| Script | Última ejecución | Output | Estado | Notas |
|--------|-----------------|--------|--------|-------|
| `src/pipeline/preprocess_pft_data.py` | — | `data/processed/pft_monthly_statistics.nc` | ✓ | Archivo ya existe |
| `src/pipeline/download_pft_data.py` | — | `data/raw/pft_golfo_california_2000_2024.nc` | ✓ | 81 GB, no re-descargar |

---

## Visualización Satelital

| Script | Última ejecución | Output | Estado | Notas |
|--------|-----------------|--------|--------|-------|
| `src/visualization/plot_pft_maps.py` | — | `results/satellite/figures/maps/` | ✓ | Mapas medias |
| `src/visualization/plot_pft_quinquennial_maps.py` | — | `results/satellite/figures/maps/` | ✓ | Mapas 5 años |
| `src/visualization/plot_pft_quinquennial_diff.py` | — | `results/satellite/figures/maps/` | ✓ | Diferencias entre períodos |
| `src/visualization/plot_pft_seasonal_quinquennial_comparison.py` | — | `results/satellite/figures/maps/seasonal_analysis/` | ✓ | |
| `src/visualization/plot_lat_time_optimized.py` | — | `results/satellite/figures/maps/latseries/` | ✓ | Hovmoller |
| `src/visualization/plot_pft_monthly_timeseries.py` | — | `results/satellite/figures/timeseries/` | ✓ | |
| `src/visualization/plot_pft_monthly_with_indices_optimized.py` | — | `results/satellite/figures/timeseries_indices/` | ✓ | Con índices climáticos |
| `src/visualization/plot_composition_percentages.py` | — | `results/satellite/figures/composition/` | ✓ | |
| `src/visualization/generate_plotly_charts.py` | — | `results/satellite/figures/timeseries/plotly_charts/` | ✓ | Interactivos HTML |

---

## Análisis In-Situ (eDNA) — Comparación entre versiones de taxonomía

> Para ejecutar ambas versiones y comparar:
> ```bash
> ./run_all_analyses.sh --only-insitu --taxonomy v1
> ./run_all_analyses.sh --only-insitu --taxonomy v2
> ```

| Script | Taxonomía | Última ejecución | Output | Estado | Notas |
|--------|-----------|-----------------|--------|--------|-------|
| `src/insitu/analisis_series_tiempo_in_situ_primarios.py` | v1 | 2026-04-21 | `results/insitu/edna_v1/series_tiempo/` | ✓ | 188,325 registros, 6 grupos |
| `src/insitu/analisis_series_tiempo_in_situ_primarios.py` | v2 | 2026-04-21 | `results/insitu/edna_v2/series_tiempo/` | ✓ | 17,015 registros, 6 grupos |
| `src/insitu/analisis_profundidad_abundancia.py` | v1 | 2026-04-21 | `results/insitu/edna_v1/profundidad/` | ✓ | 188,325 registros con profundidad |
| `src/insitu/analisis_profundidad_abundancia.py` | v2 | 2026-04-21 | `results/insitu/edna_v2/profundidad/` | ✓ | 17,015 registros con profundidad |
| `src/insitu/time_series_analysis_species.py` | — | — | `results/insitu/edna_v1/series_tiempo/` | ✓ | Solo usa NetCDF satelital |

### Comparación v1 vs v2

| Métrica | edna_v1 | edna_v2 | Diferencia |
|---------|---------|---------|-----------|
| N registros válidos (2000-2024) | 188,325 | 17,015 | v1 tiene ~11× más registros |
| Grupos identificados | 6 (sin Diatomeas) | 6 (con Diatomeas, sin Otros Eucariotas) | v2 resuelve Bacillariophyta como Diatomeas |
| Período con datos | 2000-2024 | 2000-2024 | Mismo rango |
| Fecha columna | Excel serial (`Collected date year`) | ISO 8601 (`date`) | Formato diferente |
| Profundidad columna | 3 cols: Shallow/Mid-water/Deep | 1 col: `Depth` (metros) | Esquema distinto |
| Abundancia | Conteo de registros | Columna `Abundance` explícita | v2 cuantitativo |

---

## Análisis Estadístico Inferencial

| Script | Última ejecución | Output | Estado | Notas |
|--------|-----------------|--------|--------|-------|
| `src/analysis/stl_decomposition_extremes.py` | — | `results/satellite/figures/stl_decomposition/` | ✓ | |
| `src/analysis/fourier_analysis.py` | — | `results/satellite/figures/fourier_analysis/` | ✓ | |
| `src/analysis/hmm_regimen_change.py` | — | `results/satellite/figures/hmm_regimen_change/` | ✓ | |
| `src/analysis/extremos_alternativos.py` | — | `results/satellite/figures/extremos_alternativos/` | ✓ | |
| `src/analysis/cross_correlation_permutation.py` | — | `results/satellite/tables/correlations/` | ✓ | |
| `src/analysis/granger_causality.py` | — | `results/satellite/figures/granger_causality/` | ✓ | |
| `src/analysis/canonical_correlation.py` | — | `results/satellite/figures/canonical_correlation/` | ✓ | |
| `src/analysis/piecewise_regression.py` | — | `results/satellite/figures/piecewise_regression/` | ✓ | |
| `src/analysis/joint_extremes.py` | — | `results/satellite/figures/joint_extremes/` | ✓ | |

---

## Reporte Final HTML

| Reporte | Taxonomía usada | Fecha generación | Ruta | Estado |
|---------|----------------|-----------------|------|--------|
| Reporte completo (20 secciones) | v1 | — | `results/reports/completo_pft/index.html` | ✓ Referencia histórica |
| **Reporte activo (HTML)** | **v2** | **2026-04-21** | **`results/reports/index.html`** | **✓ Activo** |
| **Reporte activo (Markdown)** | **v2** | **2026-04-21** | **`results/reports/reporte_insitu_v2.md`** | **✓ Activo** |

> Para regenerar: `TAXONOMY_VERSION=v2 python3 src/reports/generate_html_report_complete_v2.py`
> Para markdown:  `TAXONOMY_VERSION=v2 python3 src/reports/generate_markdown_report.py`

---

## Cómo actualizar esta bitácora

Al ejecutar un script, actualiza la columna **Última ejecución** con la fecha `YYYY-MM-DD` y el **Estado** correspondiente. Para la comparación v1/v2, completar la tabla de métricas una vez ejecutados ambos.
