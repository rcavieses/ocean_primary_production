#!/bin/bash
# ============================================================
# Ejecuta TODOS los scripts de análisis en secuencia
#
# Uso:
#   ./run_all_analyses.sh              # taxonomía v1 (default)
#   ./run_all_analyses.sh --taxonomy v2  # taxonomía v2
#   ./run_all_analyses.sh --only-insitu  # solo análisis in-situ
#   ./run_all_analyses.sh --only-satellite  # solo análisis satelital
#
# Log: run_all_analyses.log
# ============================================================

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$ROOT_DIR/run_all_analyses.log"

TAXONOMY_VERSION="v1"
RUN_SATELLITE=true
RUN_INSITU=true

for arg in "$@"; do
  case $arg in
    --taxonomy) ;;
    v1|v2) TAXONOMY_VERSION="$arg" ;;
    --only-insitu)    RUN_SATELLITE=false ;;
    --only-satellite) RUN_INSITU=false ;;
  esac
done

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"
}

run_script() {
    local category="$1"
    local script="$2"
    shift 2
    local extra_args="$*"
    local full_path="$ROOT_DIR/src/$category/$script"
    log ">>> $category/$script $extra_args"
    python3 "$full_path" $extra_args >> "$LOG" 2>&1
    local status=$?
    if [ $status -eq 0 ]; then
        log "    OK"
    else
        log "    ERROR ($status) — continuando..."
    fi
}

log "======================================================"
log "INICIO | taxonomía: $TAXONOMY_VERSION"
log "======================================================"

# ---- 1. PREPROCESAMIENTO ----
log ""
log "--- [1/6] PREPROCESAMIENTO ---"
run_script "pipeline" "preprocess_pft_data.py"

# ---- 2. MAPAS Y VISUALIZACIONES SATELITALES ----
if [ "$RUN_SATELLITE" = true ]; then
log ""
log "--- [2/6] MAPAS Y VISUALIZACIONES SATELITALES ---"
run_script "visualization" "plot_pft_maps.py"
run_script "visualization" "plot_pft_quinquennial_maps.py"
run_script "visualization" "plot_pft_quinquennial_diff.py"
run_script "visualization" "plot_pft_seasonal_quinquennial_comparison.py"
run_script "visualization" "plot_lat_time_optimized.py"
run_script "visualization" "plot_pft_monthly_timeseries.py"
run_script "visualization" "plot_pft_monthly_with_indices_optimized.py"
run_script "visualization" "plot_composition_percentages.py"
run_script "visualization" "generate_plotly_charts.py"
fi

# ---- 3. IN-SITU (eDNA) ----
if [ "$RUN_INSITU" = true ]; then
log ""
log "--- [3/6] ANÁLISIS IN-SITU (eDNA) | taxonomía: $TAXONOMY_VERSION ---"
run_script "insitu" "analisis_series_tiempo_in_situ_primarios.py" "--taxonomy $TAXONOMY_VERSION"
run_script "insitu" "analisis_profundidad_abundancia.py"          "--taxonomy $TAXONOMY_VERSION"
run_script "insitu" "time_series_analysis_species.py"
fi

# ---- 4. COMPARACIÓN SATELITAL VS IN-SITU ----
if [ "$RUN_SATELLITE" = true ] && [ "$RUN_INSITU" = true ]; then
log ""
log "--- [4/6] COMPARACIÓN SATELITAL vs IN-SITU ---"
run_script "visualization" "plot_satellite_vs_insitu_timeseries.py"
fi

# ---- 5. ANÁLISIS INFERENCIAL AVANZADO ----
if [ "$RUN_SATELLITE" = true ]; then
log ""
log "--- [5/6] ANÁLISIS INFERENCIAL AVANZADO ---"
run_script "analysis" "stl_decomposition_extremes.py"
run_script "analysis" "fourier_analysis.py"
run_script "analysis" "hmm_regimen_change.py"
run_script "analysis" "extremos_alternativos.py"
run_script "analysis" "cross_correlation_permutation.py"
run_script "analysis" "granger_causality.py"
run_script "analysis" "canonical_correlation.py"
run_script "analysis" "piecewise_regression.py"
run_script "analysis" "joint_extremes.py"
fi

# ---- 6. REPORTE HTML ----
log ""
log "--- [6/6] REPORTE HTML | taxonomía: $TAXONOMY_VERSION ---"
TAXONOMY_VERSION="$TAXONOMY_VERSION" python3 "$ROOT_DIR/src/reports/generate_html_report_complete_v2.py" >> "$LOG" 2>&1 \
  && log "    OK — results/reports/index.html" \
  || log "    ERROR — revisar log"

log ""
log "======================================================"
log "FINALIZADO | resultados en: results/"
log "  Satelital:  results/satellite/"
log "  In-situ:    results/insitu/edna_$TAXONOMY_VERSION/"
log "  Reporte:    results/reports/index.html"
log "======================================================"
