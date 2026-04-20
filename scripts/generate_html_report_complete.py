#!/usr/bin/env python3
"""
Script to generate an updated HTML report including:
- New filtered figures from today (40 new images)
- Quantitative analysis results (JSON data)
- Statistical analysis summary
- Complete comparison analysis

Output: Interactive HTML report + ZIP package
"""

import json
import os
from pathlib import Path
from datetime import datetime
import base64

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'figures'
FIGURES_DIR = DATA_DIR / 'fig_filt'
ANALYSIS_DIR = DATA_DIR / 'analisis_estadistico_filt'
JSON_REPORT = DATA_DIR / 'reporte_analisis_numerico.json'
OUTPUT_HTML = DATA_DIR / 'REPORTE_COMPLETO_FILTRADO.html'

VARIABLES = ['CHL', 'DIATO', 'DINO', 'GREEN', 'HAPTO', 'MICRO', 'NANO', 
             'PICO', 'PROCHLO', 'PROKAR']

VAR_DESCRIPTIONS = {
    'CHL': 'Total Chlorophyll-a',
    'DIATO': 'Diatoms',
    'DINO': 'Dinoflagellates',
    'GREEN': 'Green Algae',
    'HAPTO': 'Haptophytes',
    'MICRO': 'Microphytoplankton',
    'NANO': 'Nanophytoplankton',
    'PICO': 'Picophytoplankton',
    'PROCHLO': 'Prochlorococcus',
    'PROKAR': 'Prokaryotes'
}


def load_json_report(filepath):
    """Load the quantitative analysis report."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load JSON report: {e}")
        return None


def get_image_paths(var):
    """Get image file paths for a variable."""
    return {
        'mean_map': FIGURES_DIR / f'{var}_mean_map.png',
        'quinquennial_maps': FIGURES_DIR / f'{var}_quinquennial_maps.png',
        'quinquennial_diff': FIGURES_DIR / f'{var}_quinquennial_diff_maps.png',
        'timeseries': FIGURES_DIR / f'{var}_timeseries_analysis.png'
    }


def generate_html():
    """Generate the complete HTML report."""
    
    # Load JSON report
    report = load_json_report(JSON_REPORT)
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis Completo PFT - Golfo de California 2000-2024</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <style>
        :root {{
            --primary: #0d6efd;
            --secondary: #6c757d;
            --success: #198754;
            --danger: #dc3545;
            --warning: #ffc107;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #333;
            padding-top: 70px;
        }}
        
        .navbar {{
            background: linear-gradient(90deg, #0d6efd 0%, #0a58ca 100%);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 1000;
        }}
        
        .navbar-brand {{
            font-weight: bold;
            font-size: 1.5rem;
        }}
        
        .hero {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 20px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        .hero h1 {{
            font-size: 2.8rem;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .hero .subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        
        .hero .meta {{
            font-size: 0.95rem;
            opacity: 0.8;
        }}
        
        .section {{
            background: white;
            margin: 30px auto;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            max-width: 1400px;
        }}
        
        .section-title {{
            font-size: 2rem;
            font-weight: bold;
            color: #0d6efd;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #0d6efd;
        }}
        
        .subsection-title {{
            font-size: 1.4rem;
            font-weight: 600;
            color: #495057;
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        
        .figure-container {{
            margin: 25px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #0d6efd;
        }}
        
        .figure-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .figure-title {{
            font-weight: 600;
            color: #0d6efd;
            margin-bottom: 10px;
        }}
        
        .stats-table {{
            font-size: 0.95rem;
            margin: 20px 0;
        }}
        
        .stats-table th {{
            background-color: #0d6efd;
            color: white;
            font-weight: 600;
            padding: 12px;
        }}
        
        .stats-table td {{
            padding: 10px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .stats-table tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .metric-card {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            transition: all 0.3s ease;
        }}
        
        .metric-card:hover {{
            border-color: #0d6efd;
            box-shadow: 0 4px 12px rgba(13, 110, 253, 0.2);
        }}
        
        .metric-label {{
            font-size: 0.85rem;
            color: #6c757d;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        
        .metric-value {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #0d6efd;
        }}
        
        .metric-unit {{
            font-size: 0.85rem;
            color: #6c757d;
            margin-left: 5px;
        }}
        
        .summary-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        
        .summary-box h3 {{
            font-weight: bold;
            margin-bottom: 15px;
        }}
        
        .summary-box ul {{
            list-style-position: inside;
            margin: 0;
        }}
        
        .summary-box li {{
            margin: 8px 0;
        }}
        
        .tabs-container {{
            margin: 20px 0;
        }}
        
        .nav-tabs .nav-link {{
            color: #495057;
            border: none;
            border-bottom: 3px solid transparent;
            font-weight: 500;
        }}
        
        .nav-tabs .nav-link.active {{
            color: #0d6efd;
            background-color: transparent;
            border-color: #0d6efd;
        }}
        
        .tab-content {{
            border: 1px solid #dee2e6;
            border-top: none;
            padding: 25px;
            background: #f8f9fa;
        }}
        
        .footer {{
            background: #212529;
            color: white;
            padding: 30px;
            text-align: center;
            margin-top: 50px;
        }}
        
        .badge-info {{
            background-color: #0d6efd;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            display: inline-block;
            margin: 5px 5px 5px 0;
        }}
        
        .alert-summary {{
            background-color: #e7f3ff;
            border-left: 4px solid #0d6efd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .comparison-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }}
        
        @media (min-width: 1200px) {{
            .comparison-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        .print-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 999;
        }}
        
        @media print {{
            .navbar, .print-btn {{
                display: none;
            }}
            
            .section {{
                page-break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ddd;
            }}
        }}
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-dark navbar-expand-lg">
        <div class="container-fluid">
            <a class="navbar-brand" href="#top"><i class="fas fa-chart-line"></i> PFT Analysis Gulf of CA</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="#overview">Overview</a></li>
                    <li class="nav-item"><a class="nav-link" href="#analyses">Analyses</a></li>
                    <li class="nav-item"><a class="nav-link" href="#statistics">Statistics</a></li>
                    <li class="nav-item"><a class="nav-link" href="#climate">Climate</a></li>
                </ul>
            </div>
        </div>
    </nav>
    
    <!-- Hero Section -->
    <div class="hero" id="top">
        <h1><i class="fas fa-water"></i> Análisis Completo de Fitoplancton</h1>
        <p class="subtitle">Golfo de California 2000-2024 | Datos Filtrados Espacialmente</p>
        <p class="meta">
            <i class="fas fa-calendar"></i> Generado: {datetime.now().strftime('%d de %B, %Y')} |
            <i class="fas fa-check-circle"></i> Datos: 13,928 puntos (8.96% del grid)
        </p>
    </div>
    
    <!-- Overview Section -->
    <div class="section" id="overview">
        <h2 class="section-title"><i class="fas fa-info-circle"></i> Descripción General</h2>
        
        <div class="alert-summary">
            <h4><i class="fas fa-file-pdf"></i> Reporte Completo y Actualizado</h4>
            <p>Este reporte integra todos los análisis realizados hoy incluyendo:</p>
            <ul class="mb-0 mt-2">
                <li><strong>40 figuras nuevas</strong> - Mapas filtrados, comparaciones quinquenales, series temporales</li>
                <li><strong>Análisis cuantitativos</strong> - Estadísticas espaciales, anomalías, tendencias, correlaciones</li>
                <li><strong>Análisis estadísticos</strong> - Correlaciones cruzadas, extremos conjuntos, análisis canónico</li>
                <li><strong>Índices climáticos</strong> - Correlaciones con MEI, NINO3.4, PDO con desfases temporales</li>
            </ul>
        </div>
        
        <div class="comparison-grid">
            <div class="metric-card">
                <div class="metric-label">🔍 Zona de Estudio</div>
                <div class="metric-value">Golfo de California</div>
                <div style="color: #6c757d; font-size: 0.9rem; margin-top: 10px;">
                    Lat: 20.40-31.81°N | Lon: 114.85-105.23°W
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">📊 Período de Datos</div>
                <div class="metric-value">2000-2024</div>
                <div style="color: #6c757d; font-size: 0.9rem; margin-top: 10px;">
                    25 años | Resolución mensual
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">🧬 Variables Analizadas</div>
                <div class="metric-value">10</div>
                <div style="color: #6c757d; font-size: 0.9rem; margin-top: 10px;">
                    Tipos de fitoplancton funcional (PFT)
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">💾 Filtrado Espacial</div>
                <div class="metric-value">13,928</div>
                <div style="color: #6c757d; font-size: 0.9rem; margin-top: 10px;">
                    puntos válidos | 8.96% del grid
                </div>
            </div>
        </div>
    </div>
    
    <!-- Variables Section -->
    <div class="section" id="analyses">
        <h2 class="section-title"><i class="fas fa-images"></i> Análisis Visual de Variables</h2>
        <p>Cada variable incluye 4 visualizaciones:</p>
        <div class="badge-info"><i class="fas fa-map"></i> Mapa medio 2000-2024</div>
        <div class="badge-info"><i class="fas fa-layer-group"></i> Mapas por período de 5 años</div>
        <div class="badge-info"><i class="fas fa-chart-line"></i> Anomalías vs 2020-2024</div>
        <div class="badge-info"><i class="fas fa-chart-area"></i> Series temporales mensuales</div>
        
        {generate_variables_section(report)}
    </div>
    
    <!-- Statistics Section -->
    <div class="section" id="statistics">
        <h2 class="section-title"><i class="fas fa-chart-bar"></i> Análisis Cuantitativos</h2>
        {generate_statistics_section(report)}
    </div>
    
    <!-- Climate Section -->
    <div class="section" id="climate">
        <h2 class="section-title"><i class="fas fa-cloud"></i> Correlaciones Climáticas</h2>
        {generate_climate_section(report)}
    </div>
    
    <!-- Summary Section -->
    <div class="section">
        <h2 class="section-title"><i class="fas fa-star"></i> Resumen Ejecutivo</h2>
        {generate_summary_section(report)}
    </div>
    
    <!-- Footer -->
    <div class="footer">
        <p>Reporte General de Análisis de Fitoplancton - Golfo de California</p>
        <p style="margin: 0; opacity: 0.8; font-size: 0.9rem;">
            Datos filtrados espacialmente | Período: 2000-2024 | Generado: {datetime.now().isoformat()}
        </p>
    </div>
    
    <!-- Print Button -->
    <button class="btn btn-primary print-btn" onclick="window.print()">
        <i class="fas fa-print"></i> Imprimir/PDF
    </button>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap5.min.js"></script>
    <script>
        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
        
        // Initialize tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {{
            return new bootstrap.Tooltip(tooltipTriggerEl);
        }});
    </script>
</body>
</html>
"""
    
    return html_content


def generate_variables_section(report):
    """Generate HTML for variable analyses."""
    html = ""
    
    for var in VARIABLES:
        html += f"""
    <div class="subsection-title" style="margin-top: 40px;">
        <span style="color: #0d6efd;">●</span> {var} - {VAR_DESCRIPTIONS[var]}
    </div>
    
    <div class="tabs-container">
        <ul class="nav nav-tabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="tab-{var}-mean" data-bs-toggle="tab" 
                        data-bs-target="#content-{var}-mean" role="tab">Mapa Medio</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="tab-{var}-quint" data-bs-toggle="tab" 
                        data-bs-target="#content-{var}-quint" role="tab">Mapas Quinquenales</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="tab-{var}-diff" data-bs-toggle="tab" 
                        data-bs-target="#content-{var}-diff" role="tab">Anomalías</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="tab-{var}-ts" data-bs-toggle="tab" 
                        data-bs-target="#content-{var}-ts" role="tab">Series Temporal</button>
            </li>
        </ul>
        
        <div class="tab-content">
            <div id="content-{var}-mean" class="tab-pane fade show active">
                <div class="figure-container">
                    <div class="figure-title"><i class="fas fa-map-marker-alt"></i> Mapa Promedio 2000-2024</div>
                    <img src="fig_filt/{var}_mean_map.png" alt="{var} Mean Map" class="img-fluid">
                    <small style="color: #6c757d; display: block; margin-top: 10px;">
                        Distribución espacial promedio del período completo (2000-2024)
                    </small>
                </div>
            </div>
            
            <div id="content-{var}-quint" class="tab-pane fade">
                <div class="figure-container">
                    <div class="figure-title"><i class="fas fa-columns"></i> Mapas por Período de 5 Años</div>
                    <img src="fig_filt/{var}_quinquennial_maps.png" alt="{var} Quinquennial Maps" class="img-fluid">
                    <small style="color: #6c757d; display: block; margin-top: 10px;">
                        Comparación espacial: 2000-04, 2005-09, 2010-14, 2015-19, 2020-24
                    </small>
                </div>
            </div>
            
            <div id="content-{var}-diff" class="tab-pane fade">
                <div class="figure-container">
                    <div class="figure-title"><i class="fas fa-wave-square"></i> Diferencias vs 2020-2024</div>
                    <img src="fig_filt/{var}_quinquennial_diff_maps.png" alt="{var} Differences" class="img-fluid">
                    <small style="color: #6c757d; display: block; margin-top: 10px;">
                        Anomalías: Cambio relativo respecto al período más reciente (2020-2024)
                    </small>
                </div>
            </div>
            
            <div id="content-{var}-ts" class="tab-pane fade">
                <div class="figure-container">
                    <div class="figure-title"><i class="fas fa-chart-line"></i> Series Temporal Mensual</div>
                    <img src="fig_filt/{var}_timeseries_analysis.png" alt="{var} Timeseries" class="img-fluid">
                    <small style="color: #6c757d; display: block; margin-top: 10px;">
                        Evolución temporal mensual con tendencia lineal ajustada
                    </small>
                </div>
            </div>
        </div>
    </div>
"""
    
    return html


def generate_statistics_section(report):
    """Generate HTML for quantitative statistics."""
    if not report:
        return "<p>No statistical data available</p>"
    
    html = """
    <div class="alert-summary">
        <strong>Métricas Principales:</strong> Media, Mediana, Desviación Estándar, Mín/Máx, Percentiles
    </div>
    
    <div class="tabs-container">
        <ul class="nav nav-tabs" role="tablist">
"""
    
    for i, var in enumerate(VARIABLES):
        active = "active" if i == 0 else ""
        html += f"""
            <li class="nav-item" role="presentation">
                <button class="nav-link {active}" id="tab-stat-{var}" data-bs-toggle="tab" 
                        data-bs-target="#stat-{var}" role="tab">{var}</button>
            </li>
"""
    
    html += """
        </ul>
        
        <div class="tab-content">
"""
    
    for i, var in enumerate(VARIABLES):
        if var not in report['variables']:
            continue
        
        active = "show active" if i == 0 else ""
        var_data = report['variables'][var]
        
        if 'map_statistics' in var_data:
            stats = var_data['map_statistics']
            html += f"""
            <div id="stat-{var}" class="tab-pane fade {active}">
                <h5 class="mb-3">{VAR_DESCRIPTIONS[var]} - Estadísticas Espaciales (2000-2024)</h5>
                
                <div class="comparison-grid">
                    <div class="metric-card">
                        <div class="metric-label">Media</div>
                        <div class="metric-value">{stats['mean']:.4f}</div>
                        <div class="metric-unit">{var_data.get('unit', 'mg m⁻³')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Mediana</div>
                        <div class="metric-value">{stats['median']:.4f}</div>
                        <div class="metric-unit">{var_data.get('unit', 'mg m⁻³')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Desv. Estándar</div>
                        <div class="metric-value">{stats['std']:.4f}</div>
                        <div class="metric-unit">{var_data.get('unit', 'mg m⁻³')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Mínimo</div>
                        <div class="metric-value">{stats['min']:.4f}</div>
                        <div class="metric-unit">{var_data.get('unit', 'mg m⁻³')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Máximo</div>
                        <div class="metric-value">{stats['max']:.4f}</div>
                        <div class="metric-unit">{var_data.get('unit', 'mg m⁻³')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Rango</div>
                        <div class="metric-value">{stats['max'] - stats['min']:.4f}</div>
                        <div class="metric-unit">{var_data.get('unit', 'mg m⁻³')}</div>
                    </div>
"""
            
            # Add quinquennial comparison if available
            if 'quinquennial_statistics' in var_data:
                html += """
                </div>
                
                <h6 class="mt-4 mb-3">Comparación Quinquenal</h6>
                <div class="table-responsive">
                    <table class="table table-striped stats-table">
                        <thead>
                            <tr>
                                <th>Período</th>
                                <th>Media</th>
                                <th>Std</th>
                                <th>Mín</th>
                                <th>Máx</th>
                            </tr>
                        </thead>
                        <tbody>
"""
                
                for period, period_data in var_data['quinquennial_statistics'].items():
                    html += f"""
                            <tr>
                                <td><strong>{period}</strong></td>
                                <td>{period_data['mean']:.4f}</td>
                                <td>{period_data['std']:.4f}</td>
                                <td>{period_data['min']:.4f}</td>
                                <td>{period_data['max']:.4f}</td>
                            </tr>
"""
                
                html += """
                        </tbody>
                    </table>
                </div>
"""
            
            # Add anomalies if available
            if 'anomalies_vs_2020_2024' in var_data:
                html += """
                <h6 class="mt-4 mb-3">Anomalías vs 2020-2024</h6>
                <div class="table-responsive">
                    <table class="table table-striped stats-table">
                        <thead>
                            <tr>
                                <th>Período</th>
                                <th>Cambio Absoluto</th>
                                <th>% Cambio</th>
                            </tr>
                        </thead>
                        <tbody>
"""
                
                for period, anom_data in var_data['anomalies_vs_2020_2024'].items():
                    sign_abs = "+" if anom_data['absolute_change'] > 0 else ""
                    sign_pct = "+" if anom_data['percent_change'] > 0 else ""
                    html += f"""
                            <tr>
                                <td><strong>{period}</strong></td>
                                <td style="color: {'green' if anom_data['absolute_change'] > 0 else 'red'};">
                                    {sign_abs}{anom_data['absolute_change']:.4f}
                                </td>
                                <td style="color: {'green' if anom_data['percent_change'] > 0 else 'red'};">
                                    {sign_pct}{anom_data['percent_change']:.2f}%
                                </td>
                            </tr>
"""
                
                html += """
                        </tbody>
                    </table>
                </div>
"""
            
            html += """
                </div>
            </div>
"""
    
    html += """
        </div>
    </div>
"""
    
    return html


def generate_climate_section(report):
    """Generate HTML for climate correlations."""
    if not report:
        return "<p>No climate correlation data available</p>"
    
    html = """
    <div class="alert-summary">
        <strong>Índices Climáticos:</strong> MEI, NINO3.4, PDO | 
        <strong>Desfases (lags):</strong> -12 a +12 meses
    </div>
    
    <div class="tabs-container">
        <ul class="nav nav-tabs" role="tablist">
"""
    
    for i, var in enumerate(VARIABLES):
        active = "active" if i == 0 else ""
        html += f"""
            <li class="nav-item" role="presentation">
                <button class="nav-link {active}" id="tab-clim-{var}" data-bs-toggle="tab" 
                        data-bs-target="#clim-{var}" role="tab">{var}</button>
            </li>
"""
    
    html += """
        </ul>
        
        <div class="tab-content">
"""
    
    for i, var in enumerate(VARIABLES):
        if var not in report['variables']:
            continue
        
        active = "show active" if i == 0 else ""
        var_data = report['variables'][var]
        
        if 'climate_correlations' in var_data:
            html += f"""
            <div id="clim-{var}" class="tab-pane fade {active}">
                <h5 class="mb-3">Correlaciones Climáticas - {VAR_DESCRIPTIONS[var]}</h5>
                
                <div class="row">
"""
            
            for index, corr_data in var_data['climate_correlations'].items():
                html += f"""
                    <div class="col-md-6 mb-3">
                        <div class="metric-card">
                            <div class="metric-label">{index}</div>
                            <div style="font-size: 1.1rem; margin-bottom: 5px;">
                                <strong>r =</strong> <span style="color: {'green' if corr_data['max_correlation'] > 0 else 'red'};">
                                    {corr_data['max_correlation']:+.4f}
                                </span>
                            </div>
                            <div style="font-size: 0.9rem; color: #6c757d;">
                                Desfase: <strong>{corr_data['lag_at_max']}</strong> meses
                            </div>
                            <small style="color: #6c757d; display: block; margin-top: 8px;">
                                {'Índice lidera' if corr_data['lag_at_max'] < 0 else 'Variable lidera' if corr_data['lag_at_max'] > 0 else 'Relación síncrona'}
                            </small>
                        </div>
                    </div>
"""
            
            html += """
                </div>
            </div>
"""
    
    html += """
        </div>
    </div>
"""
    
    return html


def generate_summary_section(report):
    """Generate executive summary HTML."""
    if not report:
        return "<p>No summary available</p>"
    
    # Find variables with highest variability
    cv_list = []
    for var in VARIABLES:
        if var in report['variables'] and 'temporal_statistics' in report['variables'][var]:
            cv = report['variables'][var]['temporal_statistics']['coefficient_of_variation']
            cv_list.append((var, cv))
    
    cv_list.sort(key=lambda x: x[1], reverse=True)
    
    # Find variables with strongest trends
    trend_list = []
    for var in VARIABLES:
        if var in report['variables'] and 'linear_trend' in report['variables'][var]:
            trend = report['variables'][var]['linear_trend']['slope_per_year']
            trend_list.append((var, trend))
    
    trend_list.sort(key=lambda x: abs(x[1]), reverse=True)
    
    html = f"""
    <div class="summary-box">
        <h3><i class="fas fa-microscope"></i> Variabilidad Temporal</h3>
        <p><strong>Variables con Mayor Fluctuación (Coeficiente de Variación):</strong></p>
        <ul>
"""
    
    for var, cv in cv_list[:5]:
        html += f"            <li>{var}: {cv:.2f}%</li>\n"
    
    html += """
        </ul>
    </div>
    
    <div class="summary-box">
        <h3><i class="fas fa-arrow-trend-up"></i> Tendencias Lineales</h3>
        <p><strong>Variables con Cambios Más Significativos (2000-2024):</strong></p>
        <ul>
"""
    
    for var, trend in trend_list[:5]:
        direction = "↑" if trend > 0 else "↓"
        unit = "mg m⁻³/año"
        html += f"            <li>{direction} {var}: {trend:+.6f} {unit}</li>\n"
    
    html += """
        </ul>
    </div>
"""
    
    return html


def main():
    print("Generating comprehensive HTML report...")
    
    html = generate_html()
    
    # Write HTML file
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ HTML report saved: {OUTPUT_HTML}")
    print(f"  Size: {OUTPUT_HTML.stat().st_size / 1024:.1f} KB")
    

if __name__ == '__main__':
    main()
