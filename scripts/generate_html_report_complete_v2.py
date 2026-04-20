#!/usr/bin/env python3
"""
Script para generar un reporte HTML completo e integrado con TODOS los resultados
de análisis de producción primaria fitoplanctónica del Golfo de California.

Incluye:
 1. Composición de Fitoplancton (Plotly interactivos)
 2. Mapas de Concentración Media
 3. Diferencias Quinquenales
 4. Mapas Quinquenales
 5. Análisis Estacional
 6. Series Temporales con Índices Climáticos
 7. Patrones Latitud-Tiempo
 8. Estadísticas Cuantitativas (tablas desde JSON)
 9. Descomposición STL y Eventos Extremos
10. Análisis de Frecuencias Fourier
11. Cambios de Régimen (HMM)
12. Extremos Alternativos
13. Correlación Cruzada con Permutación
14. Causalidad de Granger
15. Correlación Canónica (CCA)
16. Regresión Segmentada (Piecewise)
17. Eventos Extremos Conjuntos
18. Análisis In-Situ por Profundidad
19. Comparación Satelital vs In-Situ
20. Series Temporales In-Situ Primarios
"""

import os
import json
import shutil
import glob
import csv
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
FIGURES_BASE = BASE_DIR / 'data' / 'figures'
PLOTLY_BASE = FIGURES_BASE / 'plotly_charts'

# Report output
REPORT_DIR = BASE_DIR / 'reporte_analisis'
REPORT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = REPORT_DIR / 'index.html'
FIGURES_DIR = REPORT_DIR / 'figuras'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# In-situ results
DEPTH_RESULTS = BASE_DIR / 'resultados_analisis_profundidad'
TIMESERIES_RESULTS = BASE_DIR / 'resultados_series_tiempo'

# Quantitative JSON
JSON_REPORT = FIGURES_BASE / 'reporte_analisis_numerico.json'

# Variable descriptions
VAR_DESCRIPTIONS = {
    'CHL': 'Clorofila-a Total',
    'DIATO': 'Diatomeas',
    'DINO': 'Dinoflagelados',
    'GREEN': 'Algas Verdes',
    'HAPTO': 'Haptófitos',
    'MICRO': 'Microfitoplancton',
    'NANO': 'Nanofitoplancton',
    'PICO': 'Picofitoplancton',
    'PROCHLO': 'Proclorococcus',
    'PROKAR': 'Procariontes'
}

VAR_ORDER = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO', 'PICO', 'PROCHLO', 'PROKAR']

# ============================================================================
# ALL SECTIONS CONFIGURATION
# ============================================================================

SECTIONS = [
    {
        'id': 'composicion',
        'num': '1',
        'titulo': 'Composición de Fitoplancton',
        'descripcion': 'Análisis de la composición porcentual de especies y clases de tamaño mediante gráficos interactivos.',
        'tipo': 'plotly',
        'icono': 'fa-pie-chart',
        'color': '#2E86AB',
    },
    {
        'id': 'mean_maps',
        'num': '2',
        'titulo': 'Mapas de Concentración Media (2000-2024)',
        'descripcion': 'Distribución espacial promedio de cada tipo funcional de fitoplancton en el Golfo de California.',
        'tipo': 'carousel',
        'icono': 'fa-map',
        'color': '#06A77D',
        'directorio': FIGURES_BASE,
        'patron': '*_mean_map.png',
    },
    {
        'id': 'quinquennial_diff',
        'num': '3',
        'titulo': 'Diferencias Quinquenales',
        'descripcion': 'Anomalías de concentración del período 2020-2024 respecto a períodos anteriores.',
        'tipo': 'carousel',
        'icono': 'fa-exchange-alt',
        'color': '#E63946',
        'directorio': FIGURES_BASE / 'quinquennial_diff',
        'patron': '*.png',
    },
    {
        'id': 'quinquennial',
        'num': '4',
        'titulo': 'Mapas Quinquenales',
        'descripcion': 'Concentraciones promedio para cada período quinquenal (2000-2004, 2005-2009, 2010-2014, 2015-2019, 2020-2024).',
        'tipo': 'carousel',
        'icono': 'fa-th-large',
        'color': '#F77F00',
        'directorio': FIGURES_BASE / 'quinquennial',
        'patron': '*.png',
    },
    {
        'id': 'seasonal_analysis',
        'num': '5',
        'titulo': 'Análisis Estacional',
        'descripcion': 'Patrones de variación estacional y comparaciones quinquenales para cada variable.',
        'tipo': 'carousel',
        'icono': 'fa-snowflake',
        'color': '#A23B72',
        'directorio': FIGURES_BASE / 'seasonal_analysis',
        'patron': '*.png',
    },
    {
        'id': 'timeseries_indices',
        'num': '6',
        'titulo': 'Series Temporales con Índices Climáticos',
        'descripcion': 'Evolución mensual de fitoplancton (2000-2024) con superposición de índices NIÑO3.4, MEI y PDO.',
        'tipo': 'carousel',
        'icono': 'fa-chart-line',
        'color': '#2E86AB',
        'directorio': FIGURES_BASE / 'timeseries_indices',
        'patron': '*.png',
    },
    {
        'id': 'latseries',
        'num': '7',
        'titulo': 'Patrones Latitud-Tiempo',
        'descripcion': 'Heatmaps mostrando la evolución temporal por banda de latitud para cada tipo de fitoplancton.',
        'tipo': 'carousel',
        'icono': 'fa-align-left',
        'color': '#06A77D',
        'directorio': FIGURES_BASE / 'latseries',
        'patron': '*.png',
    },
    {
        'id': 'estadisticas',
        'num': '8',
        'titulo': 'Estadísticas Cuantitativas',
        'descripcion': 'Resumen estadístico por variable y período quinquenal: media, desviación estándar, tendencia lineal y correlaciones climáticas.',
        'tipo': 'tablas',
        'icono': 'fa-table',
        'color': '#E63946',
    },
    {
        'id': 'stl',
        'num': '9',
        'titulo': 'Descomposición STL y Eventos Extremos',
        'descripcion': 'Separación de tendencia, estacionalidad y residuales (Cleveland et al., 1990). Detección de eventos extremos en percentiles 10 y 90.',
        'tipo': 'carousel',
        'icono': 'fa-wave-square',
        'color': '#F77F00',
        'directorio': FIGURES_BASE / 'stl_decomposition',
        'patron': '*_stl_decomposition.png',
    },
    {
        'id': 'fourier',
        'num': '10',
        'titulo': 'Análisis de Frecuencias (Fourier)',
        'descripcion': 'Espectro de potencia FFT para identificar periodicidades dominantes (ciclos anuales, interanuales) en cada serie temporal.',
        'tipo': 'carousel',
        'icono': 'fa-signal',
        'color': '#A23B72',
        'directorio': FIGURES_BASE / 'fourier_analysis',
        'patron': '*_fourier_spectrum.png',
    },
    {
        'id': 'hmm',
        'num': '11',
        'titulo': 'Cambios de Régimen (HMM)',
        'descripcion': 'Modelos Ocultos de Markov (2 estados) para detectar transiciones entre regímenes productivos alto y bajo.',
        'tipo': 'carousel',
        'icono': 'fa-random',
        'color': '#2E86AB',
        'directorio': FIGURES_BASE / 'hmm_regimen_change',
        'patron': '*_hmm_regimen.png',
    },
    {
        'id': 'extremos',
        'num': '12',
        'titulo': 'Extremos Alternativos',
        'descripcion': 'Detección de eventos extremos mediante tres métodos complementarios: umbral móvil, IQR robusto y detección de rupturas.',
        'tipo': 'carousel',
        'icono': 'fa-exclamation-triangle',
        'color': '#E63946',
        'directorio': FIGURES_BASE / 'extremos_alternativos',
        'patron': '*_extremos_alternativos.png',
    },
    {
        'id': 'crosscorr',
        'num': '13',
        'titulo': 'Correlación Cruzada con Permutación',
        'descripcion': 'Correlaciones de Pearson con desfases de 0-6 meses entre anomalías de biomasa e índices climáticos. Significancia por 1000 permutaciones.',
        'tipo': 'tabla_crosscorr',
        'icono': 'fa-project-diagram',
        'color': '#06A77D',
    },
    {
        'id': 'granger',
        'num': '14',
        'titulo': 'Causalidad de Granger',
        'descripcion': 'Prueba F para evaluar si los valores pasados de índices climáticos mejoran la predicción de biomasa (lags 1-6 meses).',
        'tipo': 'tabla_granger',
        'icono': 'fa-arrow-right',
        'color': '#F77F00',
    },
    {
        'id': 'cca',
        'num': '15',
        'titulo': 'Correlación Canónica (CCA)',
        'descripcion': 'Combinaciones lineales de variables PFT que correlacionan máximamente con los índices climáticos.',
        'tipo': 'tabla_cca',
        'icono': 'fa-compress-arrows-alt',
        'color': '#A23B72',
    },
    {
        'id': 'piecewise',
        'num': '16',
        'titulo': 'Regresión Segmentada (Piecewise)',
        'descripcion': 'Relaciones lineales por tramos entre biomasa e índices climáticos para detectar umbrales y no-linealidades.',
        'tipo': 'carousel',
        'icono': 'fa-bezier-curve',
        'color': '#2E86AB',
        'directorio': FIGURES_BASE / 'piecewise_regression',
        'patron': '*.png',
    },
    {
        'id': 'joint',
        'num': '17',
        'titulo': 'Eventos Extremos Conjuntos',
        'descripcion': 'Co-ocurrencia de extremos simultáneos de biomasa (>p90/<p10) e índices climáticos.',
        'tipo': 'tabla_joint',
        'icono': 'fa-bolt',
        'color': '#E63946',
    },
    {
        'id': 'profundidad',
        'num': '18',
        'titulo': 'Análisis In-Situ por Profundidad (eDNA)',
        'descripcion': 'Distribución de abundancia de grupos taxonómicos por capa de profundidad (Somera: 1-26m, Media: 35-140m, Profunda: 220-1000m).',
        'tipo': 'carousel',
        'icono': 'fa-water',
        'color': '#06A77D',
        'directorio': DEPTH_RESULTS,
        'patron': '*.png',
    },
    {
        'id': 'sat_insitu',
        'num': '19',
        'titulo': 'Comparación Satelital vs In-Situ',
        'descripcion': 'Validación cruzada entre estimaciones satelitales y datos in-situ de eDNA por grupo taxonómico.',
        'tipo': 'carousel',
        'icono': 'fa-satellite',
        'color': '#F77F00',
        'directorio': TIMESERIES_RESULTS / 'comparacion_satelital_insitu',
        'patron': '*.png',
    },
    {
        'id': 'insitu_primarios',
        'num': '20',
        'titulo': 'Series Temporales In-Situ Primarios',
        'descripcion': 'Distribución temporal, heatmaps y composición de productores primarios in-situ (Diatomeas, Dinoflagelados, Clorofitas, Cianobacterias, Haptófitos, Protozoa).',
        'tipo': 'carousel',
        'icono': 'fa-dna',
        'color': '#A23B72',
        'directorio': TIMESERIES_RESULTS / 'figuras_primarios',
        'patron': '*.png',
    },
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_images(directory, pattern):
    if not directory or not directory.exists():
        return []
    matches = glob.glob(str(directory / pattern))
    return sorted([Path(m) for m in matches])

def extract_var_name(filename):
    name = filename.split('_')[0]
    return VAR_DESCRIPTIONS.get(name, name)

def copy_all_figures():
    """Copy all figures to the report directory."""
    print("Copiando todas las figuras al directorio del reporte...")
    copied = 0

    # Subdirectories to copy from
    source_dirs = [
        FIGURES_BASE / 'composition',
        FIGURES_BASE / 'quinquennial_diff',
        FIGURES_BASE / 'quinquennial',
        FIGURES_BASE / 'seasonal_analysis',
        FIGURES_BASE / 'timeseries_indices',
        FIGURES_BASE / 'latseries',
        FIGURES_BASE / 'stl_decomposition',
        FIGURES_BASE / 'fourier_analysis',
        FIGURES_BASE / 'hmm_regimen_change',
        FIGURES_BASE / 'extremos_alternativos',
        FIGURES_BASE / 'piecewise_regression',
        DEPTH_RESULTS,
        TIMESERIES_RESULTS / 'comparacion_satelital_insitu',
        TIMESERIES_RESULTS / 'figuras_primarios',
    ]

    # Copy mean maps from root figures
    for f in FIGURES_BASE.glob('*_mean_map.png'):
        try:
            shutil.copy2(f, FIGURES_DIR / f.name)
            copied += 1
        except Exception:
            pass

    # Copy from subdirectories
    for src_dir in source_dirs:
        if src_dir and src_dir.exists():
            for f in sorted(src_dir.glob('*.png')):
                try:
                    shutil.copy2(f, FIGURES_DIR / f.name)
                    copied += 1
                except Exception:
                    pass

    # Copy Plotly HTML charts
    if PLOTLY_BASE and PLOTLY_BASE.exists():
        for f in sorted(PLOTLY_BASE.glob('*.html')):
            try:
                shutil.copy2(f, FIGURES_DIR / f.name)
                copied += 1
            except Exception:
                pass

    # Copy CSV data files for tables
    csv_dirs = [
        FIGURES_BASE / 'stl_decomposition',
        FIGURES_BASE / 'fourier_analysis',
        FIGURES_BASE / 'hmm_regimen_change',
        FIGURES_BASE / 'extremos_alternativos',
        FIGURES_BASE / 'granger_causality',
        FIGURES_BASE / 'canonical_correlation',
        FIGURES_BASE / 'joint_extremes',
        FIGURES_BASE / 'analisis_estadistico_filt',
    ]
    for src_dir in csv_dirs:
        if src_dir and src_dir.exists():
            for f in sorted(src_dir.glob('*.csv')):
                try:
                    shutil.copy2(f, FIGURES_DIR / f.name)
                    copied += 1
                except Exception:
                    pass

    print(f"  Total copiados: {copied}")
    return copied


def load_json_report():
    """Load quantitative JSON report."""
    if JSON_REPORT.exists():
        with open(JSON_REPORT, 'r') as f:
            return json.load(f)
    return None

def load_csv_data(filepath):
    """Load CSV file as list of dicts."""
    if not filepath.exists():
        return []
    rows = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# ============================================================================
# HTML GENERATION
# ============================================================================

def generate_css():
    return """
    <style>
        :root {
            --primary: #2E86AB;
            --secondary: #A23B72;
            --success: #06A77D;
            --danger: #E63946;
            --warning: #F77F00;
            --light-bg: #F5F5F5;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--light-bg);
            color: #333;
            line-height: 1.6;
        }

        .navbar {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .report-header {
            background: linear-gradient(135deg, #1a5276 0%, var(--primary) 30%, var(--secondary) 70%, #6c3483 100%);
            color: white;
            padding: 50px 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }

        .report-title { font-size: 2.6rem; font-weight: bold; margin-bottom: 15px; }
        .report-subtitle { font-size: 1.3rem; opacity: 0.95; margin-bottom: 10px; }
        .report-meta { font-size: 0.95rem; opacity: 0.85; }

        .container-main { max-width: 1400px; margin: 0 auto; padding: 20px; }

        .section-header {
            background: white;
            padding: 25px;
            margin-top: 40px;
            margin-bottom: 25px;
            border-left: 5px solid var(--primary);
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .section-title { font-size: 1.8rem; font-weight: bold; color: var(--primary); margin-bottom: 10px; }
        .section-description { font-size: 1.05rem; color: #666; margin: 0; }

        .toc {
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .toc-title { font-size: 1.6rem; font-weight: bold; color: var(--primary); margin-bottom: 20px; }

        .toc-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 12px;
        }

        .toc-item {
            display: flex;
            align-items: center;
            padding: 10px 14px;
            border-radius: 6px;
            text-decoration: none;
            color: #333;
            background: #f8f9fa;
            border-left: 3px solid var(--primary);
            transition: all 0.3s;
        }

        .toc-item:hover {
            background: #e9ecef;
            transform: translateX(4px);
            text-decoration: none;
            color: var(--primary);
        }

        .toc-item .toc-num {
            background: var(--primary);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: bold;
            margin-right: 12px;
            flex-shrink: 0;
        }

        .toc-item .toc-label { font-weight: 500; font-size: 0.92rem; }

        .figure-group {
            background: white;
            padding: 30px;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-top: 3px solid var(--primary);
        }

        .figure-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--light-bg);
        }

        .figure-image {
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.12);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .figure-image:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }

        .nav-bullet {
            background: none;
            border: none;
            padding: 8px 14px;
            cursor: pointer;
            color: var(--primary);
            font-weight: 500;
            border-radius: 4px;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
            font-size: 0.9rem;
        }

        .nav-bullet:hover {
            background-color: rgba(46, 134, 171, 0.05);
            border-bottom-color: rgba(46, 134, 171, 0.3);
        }

        .nav-bullet.active {
            background-color: rgba(46, 134, 171, 0.1);
            border-bottom: 3px solid var(--primary);
            font-weight: 600;
        }

        .carousel-btn {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s;
        }

        .carousel-btn:hover { background-color: var(--secondary); }
        .carousel-btn:active { transform: scale(0.95); }

        .figure-display { animation: fadeIn 0.3s ease-in-out; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .observation-box {
            background: linear-gradient(135deg, #f0f4ff 0%, #fff0f5 100%);
            border-left: 4px solid var(--secondary);
            padding: 25px;
            margin-top: 30px;
            border-radius: 6px;
        }

        .observation-title { font-weight: bold; color: var(--secondary); font-size: 1.1rem; margin-bottom: 15px; }

        .observation-content {
            background: white;
            padding: 20px;
            border-radius: 4px;
            border: 2px dashed #ccc;
            min-height: 100px;
            cursor: text;
            transition: border-color 0.3s, background 0.3s;
        }

        .observation-content:hover { border-color: var(--secondary); background: #fafafa; }
        .observation-content.editing { border-color: var(--secondary); background: #fffbf0; }

        .bullet-list { list-style: none; padding-left: 20px; }
        .bullet-list li { margin-bottom: 8px; position: relative; padding-left: 20px; }
        .bullet-list li:before { content: "▸"; color: var(--secondary); font-size: 1.1rem; position: absolute; left: 0; font-weight: bold; }

        .method-box {
            background: #f0f7ff;
            border-left: 4px solid var(--primary);
            padding: 15px 20px;
            margin: 15px 0;
            border-radius: 4px;
        }

        .interpretation-box {
            background: #f0fff4;
            border-left: 4px solid var(--success);
            padding: 15px 20px;
            margin: 15px 0;
            border-radius: 4px;
        }

        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 0.9rem;
        }

        .stats-table th {
            background: var(--primary);
            color: white;
            padding: 10px 12px;
            text-align: left;
            font-weight: 600;
            white-space: nowrap;
        }

        .stats-table td {
            padding: 8px 12px;
            border-bottom: 1px solid #eee;
        }

        .stats-table tr:nth-child(even) { background: #f8f9fa; }
        .stats-table tr:hover { background: #e9ecef; }

        .stat-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
            border-left: 4px solid var(--primary);
        }

        .stat-card h5 {
            color: var(--primary);
            margin-bottom: 12px;
        }

        .badge-sig {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .badge-sig.sig { background: #d4edda; color: #155724; }
        .badge-sig.nosig { background: #f8d7da; color: #721c24; }

        .section-divider {
            margin: 60px 0 10px;
            text-align: center;
            position: relative;
        }

        .section-divider .divider-title {
            background: var(--light-bg);
            padding: 0 20px;
            font-size: 1.4rem;
            font-weight: bold;
            color: var(--secondary);
            position: relative;
            display: inline-block;
        }

        .section-divider::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--secondary), transparent);
        }

        footer {
            background: #2c3e50;
            color: white;
            padding: 30px 20px;
            margin-top: 50px;
            text-align: center;
        }

        footer a { color: #85c1e9; }

        @media (max-width: 768px) {
            .toc-grid { grid-template-columns: 1fr; }
            .report-title { font-size: 1.8rem; }
            .nav-bullet { padding: 6px 10px; font-size: 0.85rem; }
        }
    </style>
"""


def generate_header():
    now = datetime.now()
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Completo - Producción Primaria Golfo de California</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    {generate_css()}
</head>
<body>
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
        <div class="container-fluid">
            <a class="navbar-brand" href="#top">
                <i class="fas fa-microscope"></i> Análisis PFT - Golfo de California
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="#contenidos">Contenidos</a></li>
                    <li class="nav-item"><a class="nav-link" href="#estadisticas">Estadísticas</a></li>
                    <li class="nav-item"><a class="nav-link" href="#stl">Inferencial</a></li>
                    <li class="nav-item"><a class="nav-link" href="#profundidad">In-Situ</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Report Header -->
    <div class="report-header" id="top">
        <div class="container-main">
            <h1 class="report-title">
                <i class="fas fa-water"></i> Análisis Integral de Producción Primaria Fitoplanctónica
            </h1>
            <p class="report-subtitle">Golfo de California (2000-2024) — Datos Satelitales MODIS Aqua + Validación In-Situ eDNA</p>
            <p class="report-meta">
                <i class="far fa-calendar"></i> Generado: {now.strftime('%d/%m/%Y %H:%M')} &nbsp;|&nbsp;
                <i class="fas fa-database"></i> 300 meses, 10 variables PFT, 3 índices climáticos &nbsp;|&nbsp;
                <i class="fas fa-draw-polygon"></i> Filtrado espacial: Golfo de California (shapefile)
            </p>
        </div>
    </div>

    <div class="container-main">

        <!-- Overview -->
        <div id="inicio" class="section-header" style="border-left-color: var(--success);">
            <h2 class="section-title" style="color: var(--success);">Descripción General</h2>
            <p class="section-description">
                Reporte integrado con <strong>todos los resultados</strong> del análisis de tipos funcionales de fitoplancton (PFT)
                en el Golfo de California durante 2000-2024. Incluye análisis descriptivo (mapas, series temporales, composición),
                análisis inferencial avanzado (STL, Fourier, HMM, Granger, CCA, regresión segmentada, extremos)
                y validación con datos in-situ de eDNA.
            </p>
        </div>
"""


def generate_toc():
    html = """
        <!-- Table of Contents -->
        <div class="toc" id="contenidos">
            <div class="toc-title"><i class="fas fa-list"></i> Tabla de Contenidos (20 secciones)</div>
            <div class="toc-grid">
"""
    for sec in SECTIONS:
        html += f"""                <a href="#{sec['id']}" class="toc-item">
                    <span class="toc-num" style="background: {sec['color']};">{sec['num']}</span>
                    <span class="toc-label">{sec['titulo']}</span>
                </a>
"""
    html += """            </div>
        </div>
"""
    return html


def generate_carousel_section(section, figures):
    """Generate a carousel section with bullet navigation."""
    sec_id = section['id']
    color = section['color']

    html = f"""
        <div id="{sec_id}" class="section-header" style="border-left-color: {color};">
            <h2 class="section-title" style="color: {color};">
                <i class="fas {section['icono']}"></i> {section['num']}. {section['titulo']}
            </h2>
            <p class="section-description">{section['descripcion']}</p>
        </div>
"""

    if not figures:
        html += f"""        <div class="figure-group" style="border-top-color: {color};">
            <div class="alert alert-warning"><i class="fas fa-info-circle"></i> No se encontraron figuras para esta sección.</div>
        </div>
"""
        return html

    # Navigation bullets
    html += f"""        <div class="figure-group" style="border-top-color: {color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
                <h4 style="color: {color}; margin: 0; font-size: 1rem;">Selecciona una figura ({len(figures)} disponibles):</h4>
                <div style="display: flex; gap: 10px;">
                    <button class="carousel-btn" onclick="previousFigure('{sec_id}')" style="background-color: {color};">
                        <i class="fas fa-chevron-left"></i> Anterior
                    </button>
                    <span id="{sec_id}_counter" style="align-self: center; color: #666; font-size: 0.9rem;">1 / {len(figures)}</span>
                    <button class="carousel-btn" onclick="nextFigure('{sec_id}')" style="background-color: {color};">
                        Siguiente <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
"""
    for idx, fig_path in enumerate(figures):
        label = extract_var_name(fig_path.stem)
        if label == fig_path.stem:
            label = fig_path.stem.replace('_', ' ')[:30]
        is_active = 'active' if idx == 0 else ''
        html += f"""                <button class="nav-bullet {is_active}" onclick="showFigure('{sec_id}', {idx})"
                        data-group="{sec_id}" data-index="{idx}">
                    {label}
                </button>
"""
    html += """            </div>
        </div>
"""

    # Figure display container
    html += f"""        <div class="figure-group" style="text-align: center; border-top-color: {color};">
            <div id="{sec_id}_figures_container">
"""
    for idx, fig_path in enumerate(figures):
        fig_name = fig_path.name
        label = extract_var_name(fig_path.stem)
        if label == fig_path.stem:
            label = fig_path.stem.replace('_', ' ')
        display = 'block' if idx == 0 else 'none'
        html += f"""                <div id="{sec_id}_fig_{idx}" class="figure-display" style="display: {display};">
                    <div class="figure-title"><i class="fas fa-image"></i> {label}</div>
                    <img src="figuras/{fig_name}" alt="{fig_name}" class="figure-image" style="max-height: 750px; width: auto;">
                    <p style="margin-top: 12px; font-size: 0.85rem; color: #999; font-style: italic;">{fig_name}</p>
                </div>
"""
    html += f"""            </div>
        </div>

        <div class="figure-group" style="border-top-color: {color};">
            <div class="observation-box">
                <div class="observation-title"><i class="fas fa-pen-fancy"></i> Observaciones — {section['titulo']}</div>
                <div class="observation-content" contenteditable="true">
                    <ul class="bullet-list">
                        <li>Agregar observación...</li>
                    </ul>
                </div>
            </div>
        </div>
"""
    return html


def generate_plotly_section(section):
    """Generate section with Plotly interactive charts."""
    color = section['color']
    html = f"""
        <div id="{section['id']}" class="section-header" style="border-left-color: {color};">
            <h2 class="section-title" style="color: {color};">
                <i class="fas {section['icono']}"></i> {section['num']}. {section['titulo']}
            </h2>
            <p class="section-description">{section['descripcion']}</p>
        </div>

        <div class="figure-group" style="border-top-color: {color};">
            <p style="color: #666; margin-bottom: 20px;">
                <i class="fas fa-info-circle"></i>
                Haz clic en los elementos de la leyenda para mostrar/ocultar.
                Usa el zoom con el mouse y explora los datos interactivamente.
            </p>
        </div>
"""
    plotly_charts = [
        ('species_composition_pie.html', 'Composición de Especies (Pastel)'),
        ('size_composition_pie.html', 'Composición por Tamaño (Pastel)'),
        ('species_composition_timeseries.html', 'Series Temporales de Especies'),
        ('size_composition_timeseries.html', 'Series Temporales de Tamaño'),
        ('species_composition_stacked.html', 'Área Acumulada de Especies'),
        ('size_composition_stacked.html', 'Área Acumulada de Tamaño'),
    ]
    for chart_file, chart_title in plotly_charts:
        chart_path = FIGURES_DIR / chart_file
        if chart_path.exists() or (PLOTLY_BASE / chart_file).exists():
            html += f"""        <div class="figure-group" style="border-top-color: {color};">
            <div class="figure-title">{chart_title}</div>
            <iframe src="figuras/{chart_file}" style="width: 100%; height: 650px; border: none; border-radius: 6px;"></iframe>
        </div>
"""

    # Also show static composition PNGs
    comp_dir = FIGURES_BASE / 'composition'
    if comp_dir.exists():
        comp_pngs = sorted(comp_dir.glob('*.png'))
        if comp_pngs:
            html += f"""        <div class="figure-group" style="border-top-color: {color};">
            <div class="figure-title">Figuras Estáticas de Composición</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px;">
"""
            for fig in comp_pngs:
                html += f"""                <div style="text-align: center;">
                    <img src="figuras/{fig.name}" class="figure-image" style="max-height: 400px;">
                    <p style="margin-top: 8px; font-size: 0.85rem; color: #999;">{fig.stem.replace('_', ' ')}</p>
                </div>
"""
            html += """            </div>
        </div>
"""

    html += f"""        <div class="figure-group" style="border-top-color: {color};">
            <div class="observation-box">
                <div class="observation-title"><i class="fas fa-pen-fancy"></i> Observaciones — {section['titulo']}</div>
                <div class="observation-content" contenteditable="true">
                    <ul class="bullet-list"><li>Agregar observación...</li></ul>
                </div>
            </div>
        </div>
"""
    return html


def generate_stats_section(section, json_data):
    """Generate quantitative statistics tables from JSON data."""
    color = section['color']
    html = f"""
        <div class="section-divider">
            <span class="divider-title"><i class="fas fa-chart-bar"></i> ANÁLISIS CUANTITATIVO</span>
        </div>

        <div id="{section['id']}" class="section-header" style="border-left-color: {color};">
            <h2 class="section-title" style="color: {color};">
                <i class="fas {section['icono']}"></i> {section['num']}. {section['titulo']}
            </h2>
            <p class="section-description">{section['descripcion']}</p>
        </div>
"""

    if not json_data:
        html += """        <div class="figure-group"><div class="alert alert-warning">No se encontró el archivo de datos cuantitativos.</div></div>
"""
        return html

    variables = json_data.get('variables', {})

    # Quinquennial statistics table
    html += """        <div class="figure-group">
            <div class="figure-title"><i class="fas fa-chart-bar"></i> Estadísticas Quinquenales por Variable</div>
            <div style="overflow-x: auto;">
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th>Período</th>
                            <th>Media</th>
                            <th>Mediana</th>
                            <th>Desv. Est.</th>
                            <th>Mín</th>
                            <th>Máx</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for var_name in VAR_ORDER:
        if var_name not in variables:
            continue
        var_data = variables[var_name]
        var_display = VAR_DESCRIPTIONS.get(var_name, var_name)
        quinq = var_data.get('quinquennial_statistics', {})
        first = True
        for period in ['2000-2004', '2005-2009', '2010-2014', '2015-2019', '2020-2024']:
            if period not in quinq:
                continue
            stats = quinq[period]
            label = var_display if first else ''
            first = False
            mean_val = f"{stats.get('mean', 0):.4f}" if stats.get('mean') is not None else '-'
            median_val = f"{stats.get('median', 0):.4f}" if stats.get('median') is not None else '-'
            std_val = f"{stats.get('std', 0):.4f}" if stats.get('std') is not None else '-'
            min_val = f"{stats.get('min', 0):.4f}" if stats.get('min') is not None else '-'
            max_val = f"{stats.get('max', 0):.4f}" if stats.get('max') is not None else '-'
            html += f"""                        <tr>
                            <td><strong>{label}</strong></td>
                            <td>{period}</td>
                            <td>{mean_val}</td>
                            <td>{median_val}</td>
                            <td>{std_val}</td>
                            <td>{min_val}</td>
                            <td>{max_val}</td>
                        </tr>
"""

    html += """                    </tbody>
                </table>
            </div>
        </div>
"""

    # Trend and climate correlations
    html += """        <div class="figure-group">
            <div class="figure-title"><i class="fas fa-chart-line"></i> Tendencia Lineal y Correlaciones Climáticas</div>
            <div style="overflow-x: auto;">
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th>Pendiente (año⁻¹)</th>
                            <th>r MEI</th>
                            <th>Lag MEI</th>
                            <th>r NIÑO3.4</th>
                            <th>Lag NIÑO3.4</th>
                            <th>r PDO</th>
                            <th>Lag PDO</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for var_name in VAR_ORDER:
        if var_name not in variables:
            continue
        var_data = variables[var_name]
        var_display = VAR_DESCRIPTIONS.get(var_name, var_name)
        trend = var_data.get('linear_trend', {})
        clim = var_data.get('climate_correlations', {})

        slope_yr = trend.get('slope_per_year', None)
        slope_str = f"{slope_yr:.6f}" if slope_yr is not None else '-'

        def corr_cell(idx_name):
            idx_data = clim.get(idx_name, {})
            r = idx_data.get('best_correlation', idx_data.get('correlation', None))
            lag = idx_data.get('best_lag', idx_data.get('lag', None))
            r_str = f"{r:.3f}" if r is not None else '-'
            lag_str = str(lag) if lag is not None else '-'
            return r_str, lag_str

        r_mei, lag_mei = corr_cell('MEI')
        r_nino, lag_nino = corr_cell('NINO34')
        r_pdo, lag_pdo = corr_cell('PDO')

        html += f"""                        <tr>
                            <td><strong>{var_display}</strong></td>
                            <td>{slope_str}</td>
                            <td>{r_mei}</td>
                            <td>{lag_mei}</td>
                            <td>{r_nino}</td>
                            <td>{lag_nino}</td>
                            <td>{r_pdo}</td>
                            <td>{lag_pdo}</td>
                        </tr>
"""

    html += """                    </tbody>
                </table>
            </div>
            <div class="interpretation-box" style="margin-top: 15px;">
                <h5><i class="fas fa-lightbulb"></i> Interpretación</h5>
                <ul>
                    <li><strong>Pendiente:</strong> Cambio anual en concentración (mg m⁻³ año⁻¹). Positivo = tendencia creciente.</li>
                    <li><strong>r:</strong> Correlación de Pearson óptima con el índice climático (-1 a 1).</li>
                    <li><strong>Lag:</strong> Desfase en meses para la correlación óptima (0 = simultáneo).</li>
                </ul>
            </div>
        </div>
"""

    html += f"""        <div class="figure-group" style="border-top-color: {color};">
            <div class="observation-box">
                <div class="observation-title"><i class="fas fa-pen-fancy"></i> Observaciones — Estadísticas</div>
                <div class="observation-content" contenteditable="true">
                    <ul class="bullet-list"><li>Agregar observación...</li></ul>
                </div>
            </div>
        </div>
"""
    return html


def generate_crosscorr_section(section):
    """Generate cross-correlation results table from CSV files."""
    color = section['color']
    html = f"""
        <div class="section-divider">
            <span class="divider-title"><i class="fas fa-flask"></i> ANÁLISIS INFERENCIAL AVANZADO</span>
        </div>

        <div id="{section['id']}" class="section-header" style="border-left-color: {color};">
            <h2 class="section-title" style="color: {color};">
                <i class="fas {section['icono']}"></i> {section['num']}. {section['titulo']}
            </h2>
            <p class="section-description">{section['descripcion']}</p>
        </div>

        <div class="figure-group" style="border-top-color: {color};">
            <div class="method-box">
                <h5><i class="fas fa-microscope"></i> Método</h5>
                <p>Correlación de Pearson entre anomalías de biomasa e índices climáticos (MEI, PDO, NIÑO3.4)
                para desfases de 0 a 6 meses. Significancia evaluada con <strong>1000 pruebas de permutación</strong> (α = 0.05).</p>
            </div>
"""

    # Load and display cross-correlation CSVs
    crosscorr_dir = FIGURES_BASE / 'analisis_estadistico_filt'
    if not crosscorr_dir.exists():
        crosscorr_dir = FIGURES_BASE / 'cross_correlation'

    csv_files = sorted(crosscorr_dir.glob('crosscorr_*.csv')) if crosscorr_dir.exists() else []

    if csv_files:
        html += """            <div class="figure-title"><i class="fas fa-table"></i> Mejor correlación por variable e índice climático</div>
            <div style="overflow-x: auto;">
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th>Índice</th>
                            <th>Mejor Lag (meses)</th>
                            <th>r (correlación)</th>
                            <th>p-valor</th>
                            <th>Significativo</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for csv_file in csv_files:
            # Parse var and index from filename: crosscorr_DIATO_mean_vs_MEI.csv
            stem = csv_file.stem
            parts = stem.replace('crosscorr_', '').split('_vs_')
            var_key = parts[0].replace('_mean', '') if parts else ''
            idx_key = parts[1] if len(parts) > 1 else ''
            var_display = VAR_DESCRIPTIONS.get(var_key, var_key)

            rows = load_csv_data(csv_file)
            # Find best lag (highest |r| with significance)
            best_row = None
            best_abs_r = -1
            for row in rows:
                try:
                    r_val = float(row.get('r', 0))
                    p_val = float(row.get('p_perm', 1))
                    if abs(r_val) > best_abs_r:
                        best_abs_r = abs(r_val)
                        best_row = row
                except (ValueError, TypeError):
                    continue

            if best_row:
                r_val = float(best_row.get('r', 0))
                p_val = float(best_row.get('p_perm', 1))
                lag_val = best_row.get('lag', '-')
                is_sig = p_val < 0.05
                sig_badge = '<span class="badge-sig sig">✔️ Sí</span>' if is_sig else '<span class="badge-sig nosig">✖ No</span>'
                html += f"""                        <tr>
                            <td>{var_display}</td>
                            <td>{idx_key}</td>
                            <td>{lag_val}</td>
                            <td>{r_val:.3f}</td>
                            <td>{p_val:.4f}</td>
                            <td>{sig_badge}</td>
                        </tr>
"""

        html += """                    </tbody>
                </table>
            </div>
"""
    else:
        html += """            <p style="color: #666;"><i class="fas fa-info-circle"></i> No se encontraron resultados de correlación cruzada.</p>
"""

    html += f"""            <div class="interpretation-box">
                <h5><i class="fas fa-lightbulb"></i> Interpretación</h5>
                <ul>
                    <li><strong>r positivo:</strong> Relación directa (aumento del índice → aumento de biomasa).</li>
                    <li><strong>r negativo:</strong> Relación inversa (aumento del índice → disminución de biomasa).</li>
                    <li><strong>Lag:</strong> Meses de desfase. Un lag=3 indica que el índice predice la biomasa con 3 meses de anticipación.</li>
                </ul>
            </div>
        </div>
"""
    return html


def generate_granger_section(section):
    """Generate Granger causality results table."""
    color = section['color']
    granger_dir = FIGURES_BASE / 'granger_causality'

    html = f"""
        <div id="{section['id']}" class="section-header" style="border-left-color: {color};">
            <h2 class="section-title" style="color: {color};">
                <i class="fas {section['icono']}"></i> {section['num']}. {section['titulo']}
            </h2>
            <p class="section-description">{section['descripcion']}</p>
        </div>

        <div class="figure-group" style="border-top-color: {color};">
            <div class="method-box">
                <h5><i class="fas fa-microscope"></i> Método</h5>
                <p>La causalidad de Granger prueba si los valores pasados de un índice climático X mejoran la predicción
                de la biomasa Y mediante una prueba F para cada lag (1-6 meses). Si p &lt; 0.05, se dice que X
                "causa" a Y en sentido de Granger en ese lag.</p>
            </div>
"""

    csv_files = sorted(granger_dir.glob('*.csv')) if granger_dir.exists() else []

    if csv_files:
        html += """            <div class="figure-title"><i class="fas fa-table"></i> Resumen de Causalidad de Granger</div>
            <div style="overflow-x: auto;">
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th>Índice</th>
                            <th>Mejor Lag</th>
                            <th>p-valor (F-test)</th>
                            <th>Significativo</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for csv_file in csv_files:
            # Parse var and index from filename like DIATO_mean_causality_MEI.csv
            stem = csv_file.stem
            parts = stem.split('_causality_')
            var_key = parts[0].replace('_mean', '') if parts else stem
            idx_key = parts[1] if len(parts) > 1 else ''
            var_display = VAR_DESCRIPTIONS.get(var_key, var_key)

            rows = load_csv_data(csv_file)
            # Wide format: columns are lag_1, lag_2, ..., lag_6 with p-values
            if rows:
                row = rows[0]  # Single row with lag columns
                best_lag = None
                best_p = 1.0
                for col_name, val in row.items():
                    if col_name.startswith('lag_'):
                        try:
                            p_val = float(val)
                            lag_num = col_name.replace('lag_', '')
                            if p_val < best_p:
                                best_p = p_val
                                best_lag = lag_num
                        except (ValueError, TypeError):
                            continue

                if best_lag is not None:
                    is_sig = best_p < 0.05
                    sig_badge = '<span class="badge-sig sig">✔️ Sí</span>' if is_sig else '<span class="badge-sig nosig">✖ No</span>'
                    html += f"""                        <tr>
                            <td>{var_display}</td>
                            <td>{idx_key}</td>
                            <td>{best_lag}</td>
                            <td>{best_p:.4f}</td>
                            <td>{sig_badge}</td>
                        </tr>
"""

        html += """                    </tbody>
                </table>
            </div>
"""

    html += f"""            <div class="interpretation-box">
                <h5><i class="fas fa-lightbulb"></i> Interpretación</h5>
                <ul>
                    <li><strong>p &lt; 0.05:</strong> El índice predice significativamente la biomasa en ese lag.</li>
                    <li><strong>Lag óptimo:</strong> El lag con menor p-valor indica la escala temporal de influencia.</li>
                    <li><strong>Advertencia:</strong> Causalidad de Granger ≠ causalidad real. Solo indica capacidad predictiva.</li>
                </ul>
            </div>
        </div>
"""
    return html


def generate_cca_section(section):
    """Generate CCA results table."""
    color = section['color']
    cca_file = FIGURES_BASE / 'canonical_correlation' / 'correlacion_canonica.csv'

    html = f"""
        <div id="{section['id']}" class="section-header" style="border-left-color: {color};">
            <h2 class="section-title" style="color: {color};">
                <i class="fas {section['icono']}"></i> {section['num']}. {section['titulo']}
            </h2>
            <p class="section-description">{section['descripcion']}</p>
        </div>

        <div class="figure-group" style="border-top-color: {color};">
            <div class="method-box">
                <h5><i class="fas fa-microscope"></i> Método</h5>
                <p>La Correlación Canónica (CCA) busca combinaciones lineales de variables PFT que correlacionan
                máximamente con combinaciones de índices climáticos. Cada dimensión canónica tiene su propia correlación.</p>
            </div>
"""

    if cca_file.exists():
        rows = load_csv_data(cca_file)
        if rows:
            html += """            <div class="figure-title"><i class="fas fa-table"></i> Correlaciones Canónicas</div>
            <div style="overflow-x: auto;">
                <table class="stats-table">
                    <thead>
                        <tr>
"""
            headers = list(rows[0].keys())
            for h in headers:
                html += f"                            <th>{h}</th>\n"
            html += """                        </tr>
                    </thead>
                    <tbody>
"""
            for row in rows:
                html += "                        <tr>\n"
                for h in headers:
                    val = row.get(h, '-')
                    try:
                        fval = float(val)
                        val = f"{fval:.4f}"
                    except (ValueError, TypeError):
                        pass
                    html += f"                            <td>{val}</td>\n"
                html += "                        </tr>\n"
            html += """                    </tbody>
                </table>
            </div>
"""

    html += f"""            <div class="interpretation-box">
                <h5><i class="fas fa-lightbulb"></i> Interpretación</h5>
                <ul>
                    <li><strong>Correlación &gt; 0.7:</strong> Relación fuerte entre el conjunto PFT y los índices climáticos.</li>
                    <li><strong>Correlación 0.3-0.7:</strong> Relación moderada.</li>
                    <li><strong>Correlación &lt; 0.3:</strong> Relación débil.</li>
                </ul>
            </div>
        </div>
"""
    return html


def generate_joint_section(section):
    """Generate joint extremes results table."""
    color = section['color']
    joint_dir = FIGURES_BASE / 'joint_extremes'

    html = f"""
        <div id="{section['id']}" class="section-header" style="border-left-color: {color};">
            <h2 class="section-title" style="color: {color};">
                <i class="fas {section['icono']}"></i> {section['num']}. {section['titulo']}
            </h2>
            <p class="section-description">{section['descripcion']}</p>
        </div>

        <div class="figure-group" style="border-top-color: {color};">
            <div class="method-box">
                <h5><i class="fas fa-microscope"></i> Método</h5>
                <p>Se identifican meses con eventos extremos simultáneos: biomasa ALTA (&gt;p90) con índice ALTO (&gt;p90),
                o biomasa BAJA (&lt;p10) con índice BAJO (&lt;p10). Esto evalúa la co-ocurrencia de extremos.</p>
            </div>
"""

    csv_files = sorted(joint_dir.glob('*.csv')) if joint_dir.exists() else []

    if csv_files:
        html += """            <div class="figure-title"><i class="fas fa-table"></i> Resumen de Eventos Extremos Conjuntos</div>
            <div style="overflow-x: auto;">
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th>Índice</th>
                            <th>Tipo</th>
                            <th>N eventos</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for csv_file in csv_files:
            stem = csv_file.stem
            # Parse: DIATO_mean_joint_extremes_MEI.csv
            parts = stem.replace('_joint_extremes_', '|').split('|')
            var_key = parts[0].replace('_mean', '') if parts else stem
            idx_key = parts[1] if len(parts) > 1 else ''
            var_display = VAR_DESCRIPTIONS.get(var_key, var_key)

            rows = load_csv_data(csv_file)
            # Count events by type
            high_count = sum(1 for r in rows if r.get('tipo', r.get('type', '')).lower() in ('alto', 'high', 'both_high'))
            low_count = sum(1 for r in rows if r.get('tipo', r.get('type', '')).lower() in ('bajo', 'low', 'both_low'))
            total = len(rows)

            if total > 0:
                html += f"""                        <tr>
                            <td>{var_display}</td>
                            <td>{idx_key}</td>
                            <td>Altos / Bajos / Total</td>
                            <td>{high_count} / {low_count} / {total}</td>
                        </tr>
"""
            else:
                html += f"""                        <tr>
                            <td>{var_display}</td>
                            <td>{idx_key}</td>
                            <td>-</td>
                            <td>Sin eventos conjuntos</td>
                        </tr>
"""

        html += """                    </tbody>
                </table>
            </div>
"""

    html += f"""            <div class="interpretation-box">
                <h5><i class="fas fa-lightbulb"></i> Interpretación</h5>
                <ul>
                    <li><strong>Muchos eventos conjuntos altos:</strong> Períodos productivos coinciden con condiciones climáticas favorables.</li>
                    <li><strong>Muchos eventos conjuntos bajos:</strong> Crisis de biomasa coinciden con estrés ambiental.</li>
                    <li><strong>Pocos eventos:</strong> Extremos desacoplados; otros factores dominan la dinámica.</li>
                </ul>
            </div>
        </div>
"""
    return html


def generate_insitu_divider():
    return """
        <div class="section-divider">
            <span class="divider-title"><i class="fas fa-vial"></i> VALIDACIÓN IN-SITU (eDNA)</span>
        </div>
"""


def generate_footer():
    return f"""
        <!-- Footer -->
    </div>

    <footer>
        <p><strong><i class="fas fa-water"></i> Reporte Integral de Producción Primaria Fitoplanctónica</strong></p>
        <p>Golfo de California (2000-2024) — Análisis Satelital + Inferencial + In-Situ</p>
        <p style="font-size: 0.9rem; margin-top: 15px; opacity: 0.8;">
            20 secciones: Composición | Mapas | Series Temporales | Estadísticas | STL | Fourier | HMM |
            Extremos | Correlación cruzada | Granger | CCA | Regresión segmentada | Eventos conjuntos | In-Situ
        </p>
        <p style="font-size: 0.85rem; opacity: 0.7; margin-top: 10px;">
            <i class="fas fa-calendar"></i> Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} |
            <code>generate_html_report_complete_v2.py</code>
        </p>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const figureStates = {{}};

        function initializeFigureGroup(groupId) {{
            if (!figureStates[groupId]) {{
                figureStates[groupId] = {{ currentIndex: 0 }};
            }}
        }}

        function showFigure(groupId, index) {{
            initializeFigureGroup(groupId);
            const container = document.getElementById(groupId + '_figures_container');
            if (!container) return;
            const figures = container.querySelectorAll('.figure-display');
            if (index < 0 || index >= figures.length) return;

            figures.forEach((fig, idx) => {{
                fig.style.display = idx === index ? 'block' : 'none';
            }});

            const bullets = document.querySelectorAll('[data-group="' + groupId + '"]');
            bullets.forEach((bullet, idx) => {{
                bullet.classList.toggle('active', idx === index);
            }});

            figureStates[groupId].currentIndex = index;

            const counter = document.getElementById(groupId + '_counter');
            if (counter) counter.textContent = (index + 1) + ' / ' + figures.length;
        }}

        function nextFigure(groupId) {{
            initializeFigureGroup(groupId);
            const container = document.getElementById(groupId + '_figures_container');
            if (!container) return;
            const figures = container.querySelectorAll('.figure-display');
            const nextIndex = (figureStates[groupId].currentIndex + 1) % figures.length;
            showFigure(groupId, nextIndex);
        }}

        function previousFigure(groupId) {{
            initializeFigureGroup(groupId);
            const container = document.getElementById(groupId + '_figures_container');
            if (!container) return;
            const figures = container.querySelectorAll('.figure-display');
            const prevIndex = (figureStates[groupId].currentIndex - 1 + figures.length) % figures.length;
            showFigure(groupId, prevIndex);
        }}

        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function(e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }});
        }});

        // Editable observation boxes
        document.querySelectorAll('.observation-content').forEach(box => {{
            box.addEventListener('click', function() {{
                this.classList.toggle('editing');
                this.focus();
            }});
        }});

        // Keyboard navigation
        document.addEventListener('keydown', function(e) {{
            if (e.target.contentEditable === 'true') return;
            const visibleSection = document.querySelector('.figure-group:hover');
            if (!visibleSection) return;
            const container = visibleSection.querySelector('[id$="_figures_container"]');
            if (!container) return;
            const groupId = container.id.replace('_figures_container', '');
            if (e.key === 'ArrowLeft') previousFigure(groupId);
            if (e.key === 'ArrowRight') nextFigure(groupId);
        }});
    </script>
</body>
</html>
"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("GENERANDO REPORTE HTML COMPLETO E INTEGRADO")
    print("=" * 70)

    # Copy all figures
    total_copied = copy_all_figures()

    # Load JSON data
    json_data = load_json_report()

    # Build HTML
    html = generate_header()
    html += generate_toc()

    print("\nGenerando secciones:")
    for section in SECTIONS:
        tipo = section['tipo']
        print(f"  {section['num']}. {section['titulo']} ({tipo})")

        if tipo == 'plotly':
            html += generate_plotly_section(section)

        elif tipo == 'carousel':
            directory = section.get('directorio')
            pattern = section.get('patron', '*.png')
            figures = find_images(directory, pattern) if directory else []
            html += generate_carousel_section(section, figures)

        elif tipo == 'tablas':
            html += generate_stats_section(section, json_data)

        elif tipo == 'tabla_crosscorr':
            html += generate_crosscorr_section(section)

        elif tipo == 'tabla_granger':
            html += generate_granger_section(section)

        elif tipo == 'tabla_cca':
            html += generate_cca_section(section)

        elif tipo == 'tabla_joint':
            html += generate_joint_section(section)

        # Add divider before in-situ sections
        if section['id'] == 'joint':
            html += generate_insitu_divider()

    html += generate_footer()

    # Write output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)

    print(f"\n{'=' * 70}")
    print(f"REPORTE GENERADO EXITOSAMENTE")
    print(f"  Archivo: {OUTPUT_FILE}")
    print(f"  Tamaño: {file_size_mb:.1f} MB")
    print(f"  Figuras copiadas: {total_copied}")
    print(f"  Secciones: {len(SECTIONS)}")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
