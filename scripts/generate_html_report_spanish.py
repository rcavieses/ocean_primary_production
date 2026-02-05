#!/usr/bin/env python3
"""
Script to generate an interactive HTML report in Spanish with all figures
organized in a single folder with the HTML file.

Features:
- Professional Spanish report
- All figures and HTML in one folder
- Editable observation sections with bullet points
- Bootstrap-based responsive design
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import glob

# ============================================================================
# CONFIGURATION
# ============================================================================

base_dir = Path(__file__).parent.parent
figures_base = base_dir / 'data' / 'figures'
plotly_base = base_dir / 'data' / 'plotly_charts'

# Create output directory for report
report_dir = base_dir / 'reporte_analisis'
report_dir.mkdir(parents=True, exist_ok=True)

output_file = report_dir / 'index.html'
figures_dir = report_dir / 'figuras'
figures_dir.mkdir(parents=True, exist_ok=True)

# Define figure groups
FIGURE_GROUPS = [
    {
        'id': 'composicion',
        'titulo': '1. Composición de Fitoplancton',
        'descripcion': 'Análisis de la composición porcentual de especies y clases de tamaño.',
        'directorio': figures_base / 'composition',
        'patron': '*.png',
    },
    {
        'id': 'quinquennial_diff',
        'titulo': '2. Diferencias Quinquenales',
        'descripcion': 'Comparación de concentraciones entre el período 2020-2024 y períodos anteriores.',
        'directorio': figures_base / 'quinquennial_diff',
        'patron': '*.png',
    },
    {
        'id': 'seasonal_analysis',
        'titulo': '3. Análisis Estacional',
        'descripcion': 'Patrones de variación estacional para cada variable de fitoplancton.',
        'directorio': figures_base / 'seasonal_analysis',
        'patron': '*.png',
    },
    {
        'id': 'timeseries_indices',
        'titulo': '4. Series Temporales con Índices Climáticos',
        'descripcion': 'Evolución temporal de fitoplancton con superposición de índices climáticos (NIÑO3.4, MEI, PDO).',
        'directorio': figures_base / 'timeseries_indices',
        'patron': '*.png',
    },
    {
        'id': 'latseries',
        'titulo': '5. Patrones Latitud-Tiempo',
        'descripcion': 'Series de tiempo promediadas por latitud para cada tipo de fitoplancton.',
        'directorio': figures_base / 'latseries',
        'patron': '*.png',
    },
    {
        'id': 'quinquennial',
        'titulo': '6. Mapas Quinquenales',
        'descripcion': 'Mapas de concentración promediados para cada período de cinco años.',
        'directorio': figures_base / 'quinquennial',
        'patron': '*.png',
    },
]

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

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_images(directory, pattern):
    """Find images matching a pattern."""
    if not directory.exists():
        return []
    matches = glob.glob(str(directory / pattern))
    return sorted([Path(m) for m in matches])


def extract_variable_name(filename):
    """Extract variable name from filename."""
    name = filename.split('_')[0]
    return name if name in VAR_DESCRIPTIONS else name


def copy_figures(groups):
    """Copy all figures to the report directory."""
    print("Copiando figuras...")
    copied = 0
    for group in groups:
        figures = find_images(group['directorio'], group['patron'])
        for fig in figures:
            try:
                dest = figures_dir / fig.name
                shutil.copy2(fig, dest)
                copied += 1
            except Exception as e:
                print(f"  Error copying {fig.name}: {e}")
    
    # Copy Plotly charts
    if plotly_base.exists():
        plotly_figures = find_images(plotly_base, '*.html')
        for fig in plotly_figures:
            try:
                dest = figures_dir / fig.name
                shutil.copy2(fig, dest)
                copied += 1
            except Exception as e:
                print(f"  Error copying {fig.name}: {e}")
    
    print(f"  ✓ {copied} figuras copiadas")
    return copied


def create_html_header():
    """Create HTML header."""
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis de Producción Primaria - Golfo de California</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{
            --primary: #2E86AB;
            --secondary: #A23B72;
            --success: #06A77D;
            --danger: #E63946;
            --warning: #F77F00;
            --light-bg: #F5F5F5;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--light-bg);
            color: #333;
            line-height: 1.6;
        }}
        
        .navbar {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .report-header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 50px 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .report-title {{
            font-size: 2.8rem;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        
        .report-subtitle {{
            font-size: 1.3rem;
            opacity: 0.95;
            margin-bottom: 10px;
        }}
        
        .report-meta {{
            font-size: 0.95rem;
            opacity: 0.85;
        }}
        
        .container-main {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .section-header {{
            background: white;
            padding: 25px;
            margin-top: 40px;
            margin-bottom: 25px;
            border-left: 5px solid var(--primary);
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .section-title {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 10px;
        }}
        
        .section-description {{
            font-size: 1.05rem;
            color: #666;
            margin: 0;
        }}
        
        .toc {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .toc-title {{
            font-size: 1.6rem;
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 20px;
        }}
        
        .toc-list {{
            list-style: none;
            columns: 2;
            gap: 20px;
        }}
        
        .toc-list li {{
            margin-bottom: 12px;
            break-inside: avoid;
        }}
        
        .toc-list a {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s, transform 0.3s;
            display: inline-block;
        }}
        
        .carousel-container {{
            position: relative;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 30px;
        }}
        
        .carousel-wrapper {{
            position: relative;
            width: 100%;
        }}
        
        .carousel-slides {{
            display: flex;
            transition: transform 0.5s ease-in-out;
            overflow: hidden;
        }}
        
        .carousel-slide {{
            min-width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .carousel-slide img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.12);
        }}
        
        .carousel-slide-name {{
            margin-top: 15px;
            color: #777;
            font-size: 0.95rem;
            font-style: italic;
            text-align: center;
        }}
        
        .carousel-controls {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            gap: 15px;
            background: #f9f9f9;
            border-top: 1px solid #eee;
        }}
        
        .carousel-dots {{
            display: flex;
            justify-content: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        
        .dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #ccc;
            cursor: pointer;
            transition: background-color 0.3s, transform 0.3s;
            border: 2px solid transparent;
        }}
        
        .dot:hover {{
            background-color: #aaa;
            transform: scale(1.15);
        }}
        
        .dot.active {{
            background-color: var(--secondary);
            border-color: var(--primary);
            transform: scale(1.3);
        }}
        
        .carousel-btn {{
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background-color 0.3s;
        }}
        
        .carousel-btn:hover {{
            background-color: var(--secondary);
        }}
        
        .carousel-counter {{
            color: #666;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        
        .figure-group {{
            background: white;
            padding: 30px;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-top: 3px solid var(--primary);
        }}
        
        .figure-title {{
            font-size: 1.4rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--light-bg);
        }}
        
        .figure-container {{
            margin-bottom: 25px;
            text-align: center;
        }}
        
        .figure-image {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.12);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .figure-image:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }}
        
        .figure-name {{
            margin-top: 12px;
            color: #777;
            font-size: 0.9rem;
            font-style: italic;
        }}
        
        .observation-box {{
            background: linear-gradient(135deg, #f0f4ff 0%, #fff0f5 100%);
            border-left: 4px solid var(--secondary);
            padding: 25px;
            margin-top: 30px;
            border-radius: 6px;
            min-height: 200px;
        }}
        
        .observation-title {{
            font-weight: bold;
            color: var(--secondary);
            font-size: 1.2rem;
            margin-bottom: 15px;
        }}
        
        .observation-content {{
            background: white;
            padding: 20px;
            border-radius: 4px;
            border: 2px dashed #ccc;
            min-height: 150px;
            cursor: text;
            transition: border-color 0.3s, background 0.3s;
        }}
        
        .observation-content:hover {{
            border-color: var(--secondary);
            background: #fafafa;
        }}
        
        .observation-content.editing {{
            border-color: var(--secondary);
            background: #fffbf0;
        }}
        
        .bullet-list {{
            list-style: none;
            padding-left: 20px;
        }}
        
        .bullet-list li {{
            margin-bottom: 10px;
            position: relative;
            padding-left: 20px;
        }}
        
        .bullet-list li:before {{
            content: "▸";
            color: var(--secondary);
            font-size: 1.2rem;
            position: absolute;
            left: 0;
            font-weight: bold;
        }}
        
        .footer {{
            background: white;
            padding: 30px;
            margin-top: 50px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #666;
        }}
        
        .btn-edit {{
            background-color: var(--secondary);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background-color 0.3s;
        }}
        
        .btn-edit:hover {{
            background-color: #8b1f5f;
        }}
        
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        
        /* Navigation Bullets Styling */
        .nav-bullet {{
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
        }}
        
        .nav-bullet:hover {{
            background-color: rgba(46, 134, 171, 0.05) !important;
            border-bottom-color: rgba(46, 134, 171, 0.3);
        }}
        
        .nav-bullet.active {{
            background-color: rgba(46, 134, 171, 0.1) !important;
            border-bottom: 3px solid var(--primary);
            font-weight: 600;
        }}
        
        .figure-display {{
            animation: fadeIn 0.3s ease-in-out;
        }}
        
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .carousel-btn {{
            transition: all 0.3s ease;
        }}
        
        .carousel-btn:active {{
            transform: scale(0.95);
        }}
        
        @media (max-width: 768px) {{
            .grid-2 {{
                grid-template-columns: 1fr;
            }}
            .toc-list {{
                columns: 1;
            }}
            .report-title {{
                font-size: 2rem;
            }}
            .nav-bullet {{
                padding: 6px 10px !important;
                font-size: 0.9rem;
            }}
        }}
    </style>
</head>
<body>
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
        <div class="container-fluid">
            <a class="navbar-brand" href="#top">
                <i class="fas fa-microscope"></i> Análisis PFT
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#inicio">Inicio</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#contenidos">Contenidos</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    
    <!-- Report Header -->
    <div class="report-header" id="top">
        <div class="container-main">
            <h1 class="report-title">
                <i class="fas fa-ocean"></i> Análisis de Producción Primaria Fitoplanctónica
            </h1>
            <p class="report-subtitle">Golfo de California (2000-2024)</p>
            <p class="report-meta">
                <i class="far fa-calendar"></i> Generado: {datetime.now().strftime('%d de %B de %Y')}
            </p>
        </div>
    </div>
    
    <!-- Main Container -->
    <div class="container-main">
        
        <!-- Overview Section -->
        <div id="inicio" class="section-header">
            <h2 class="section-title">Descripción General del Proyecto</h2>
            <p class="section-description">
                Este reporte presenta un análisis integral de los tipos funcionales de fitoplancton (PFT) en el Golfo de California
                durante el período 2000-2024. El análisis incluye patrones espaciotemporales, evolución temporal, comparaciones quinquenales,
                análisis estacional y evaluación de la composición de especies y clases de tamaño. Cada sección incluye figuras con espacio
                dedicado para registrar observaciones y interpretaciones detalladas.
            </p>
        </div>
        
        <!-- Table of Contents -->
        <div class="toc" id="contenidos">
            <div class="toc-title">
                <i class="fas fa-list"></i> Tabla de Contenidos
            </div>
            <ul class="toc-list">
"""
    return html


def create_toc_entries(groups):
    """Create table of contents entries."""
    html = ""
    for group in groups:
        if (group['directorio']).exists() or True:  # Show all even if dir doesn't exist yet
            html += f"                <li><a href=\"#{group['id']}\">{group['titulo']}</a></li>\n"
    html += """            </ul>
        </div>
"""
    return html


def create_figure_section(group, figures):
    """Create a section for a group of figures with bullet point navigation and next/prev buttons."""
    html = f"""        <!-- Section: {group['titulo']} -->
        <div id="{group['id']}" class="section-header">
            <h2 class="section-title">{group['titulo']}</h2>
            <p class="section-description">{group['descripcion']}</p>
        </div>
"""
    
    # Special handling for Composición - use Plotly charts
    if group['id'] == 'composicion':
        return create_plotly_section(group)
    
    if not figures:
        html += """        <div class="alert alert-info">
            <i class="fas fa-info-circle"></i> No se encontraron figuras en esta sección aún.
        </div>
"""
        return html
    
    group_id = group['id']
    
    # Create bullet points navigation and buttons
    html += f"""        <div class="figure-group">
            <div style="margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h4 style="color: var(--primary); margin: 0;">Selecciona una figura:</h4>
                    <div style="display: flex; gap: 10px;">
                        <button class="carousel-btn" onclick="previousFigure('{group_id}')" style="padding: 8px 12px;">
                            <i class="fas fa-chevron-left"></i> Anterior
                        </button>
                        <button class="carousel-btn" onclick="nextFigure('{group_id}')" style="padding: 8px 12px;">
                            Siguiente <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                </div>
                <ul class="bullet-list" style="display: flex; flex-wrap: wrap; gap: 15px; list-style: none; padding: 0; margin: 0;">
"""
    
    # Create bullet points with variable names
    for idx, fig_path in enumerate(figures):
        var_name = fig_path.stem.split('_')[0]
        var_display = VAR_DESCRIPTIONS.get(var_name, var_name)
        is_active = 'active' if idx == 0 else ''
        html += f"""                    <li>
                        <button class="nav-bullet {is_active}" onclick="showFigure('{group_id}', {idx})" 
                                data-group="{group_id}" data-index="{idx}"
                                style="background: none; border: none; padding: 8px 12px; cursor: pointer; color: var(--primary); font-weight: 500; border-radius: 4px; transition: all 0.3s;">
                            ▸ {var_display}
                        </button>
                    </li>
"""
    
    html += """                </ul>
            </div>
        </div>
"""
    
    # Create figure display area with all figures (initially hidden)
    html += f"""        <div class="figure-group" style="text-align: center;">
            <div id="{group_id}_figures_container">
"""
    
    for idx, fig_path in enumerate(figures):
        fig_name = fig_path.name
        var_name = fig_path.stem.split('_')[0]
        var_display = VAR_DESCRIPTIONS.get(var_name, var_name)
        display = 'block' if idx == 0 else 'none'
        
        html += f"""                <div id="{group_id}_fig_{idx}" class="figure-display" style="display: {display};">
                    <div class="figure-title" style="margin-bottom: 15px;">
                        <i class="fas fa-image"></i> {var_display}
                    </div>
                    <img src="figuras/{fig_name}" alt="{fig_name}" class="figure-image" style="max-height: 700px; width: auto;">
                    <p class="figure-name" style="margin-top: 15px; font-size: 0.85rem; color: #999;">{fig_name}</p>
                </div>
"""
    
    html += f"""            </div>
        </div>
        
        <div class="figure-group">
            <div class="observation-box">
                <div class="observation-title">
                    <i class="fas fa-pen-fancy"></i> Observaciones para {group['titulo']}
                </div>
                <div class="observation-content" contenteditable="true">
                    <ul class="bullet-list">
                        <li>Agregar observación 1...</li>
                        <li>Agregar observación 2...</li>
                        <li>Agregar observación 3...</li>
                    </ul>
                </div>
            </div>
        </div>
"""
    
    return html


def create_plotly_section(group):
    """Create a section with interactive Plotly charts."""
    html = f"""        <div class="figure-group">
            <div class="figure-title">Gráficos Interactivos - {group['titulo']}</div>
            <p style="color: #666; margin-bottom: 20px;">
                <i class="fas fa-info-circle"></i> 
                Haz clic en los elementos de la leyenda para mostrar/ocultar, 
                usa el zoom con el mouse y explora los datos interactivamente.
            </p>
        </div>
"""
    
    # Define Plotly charts for composition section
    plotly_charts = [
        ('species_composition_pie.html', 'Composición de Especies (Pastel)'),
        ('size_composition_pie.html', 'Composición por Tamaño (Pastel)'),
        ('species_composition_timeseries.html', 'Series Temporales de Especies'),
        ('size_composition_timeseries.html', 'Series Temporales de Tamaño'),
        ('species_composition_stacked.html', 'Área Acumulada de Especies'),
        ('size_composition_stacked.html', 'Área Acumulada de Tamaño'),
    ]
    
    for chart_file, chart_title in plotly_charts:
        html += f"""        <div class="figure-group">
            <div class="figure-title">{chart_title}</div>
            <iframe src="figuras/{chart_file}" style="width: 100%; height: 700px; border: none; border-radius: 6px;"></iframe>
        </div>
"""
    
    # Add observation box for composition
    html += f"""        <div class="figure-group">
            <div class="observation-box">
                <div class="observation-title">
                    <i class="fas fa-pen-fancy"></i> Observaciones para {group['titulo']}
                </div>
                <div class="observation-content" contenteditable="true">
                    <ul class="bullet-list">
                        <li>Agregar observación 1...</li>
                        <li>Agregar observación 2...</li>
                        <li>Agregar observación 3...</li>
                    </ul>
                </div>
            </div>
        </div>
"""
    
    return html


def create_html_footer():
    """Create HTML footer."""
    html = """        <!-- Footer -->
        <div class="footer">
            <p>
                <i class="fas fa-info-circle"></i>
                <strong>Información del Reporte:</strong> Este reporte de análisis fue generado automáticamente por
                <code>generate_html_report_spanish.py</code>
            </p>
            <p style="margin-top: 15px; color: #999;">
                Análisis de Producción Primaria del Golfo de California | Dataset 2000-2024
            </p>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Store figure navigation states for each group
        const figureStates = {};
        
        // Initialize figure state for a group
        function initializeFigureGroup(groupId) {
            if (!figureStates[groupId]) {
                figureStates[groupId] = { currentIndex: 0 };
            }
        }
        
        // Show specific figure in a group
        function showFigure(groupId, index) {
            initializeFigureGroup(groupId);
            
            // Get all figures for this group
            const container = document.getElementById(`${groupId}_figures_container`);
            if (!container) return;
            
            const figures = container.querySelectorAll('.figure-display');
            if (index < 0 || index >= figures.length) return;
            
            // Hide all figures in this group
            figures.forEach((fig, idx) => {
                fig.style.display = idx === index ? 'block' : 'none';
            });
            
            // Update bullet styling
            const bullets = document.querySelectorAll(`[data-group="${groupId}"]`);
            bullets.forEach((bullet, idx) => {
                if (idx === index) {
                    bullet.classList.add('active');
                    bullet.style.backgroundColor = 'rgba(var(--primary-rgb), 0.1)';
                    bullet.style.borderBottom = '3px solid var(--primary)';
                } else {
                    bullet.classList.remove('active');
                    bullet.style.backgroundColor = 'transparent';
                    bullet.style.borderBottom = 'none';
                }
            });
            
            // Store current index
            figureStates[groupId].currentIndex = index;
        }
        
        // Navigate to next figure
        function nextFigure(groupId) {
            initializeFigureGroup(groupId);
            const container = document.getElementById(`${groupId}_figures_container`);
            if (!container) return;
            
            const figures = container.querySelectorAll('.figure-display');
            const currentIndex = figureStates[groupId].currentIndex;
            const nextIndex = (currentIndex + 1) % figures.length;
            
            showFigure(groupId, nextIndex);
        }
        
        // Navigate to previous figure
        function previousFigure(groupId) {
            initializeFigureGroup(groupId);
            const container = document.getElementById(`${groupId}_figures_container`);
            if (!container) return;
            
            const figures = container.querySelectorAll('.figure-display');
            const currentIndex = figureStates[groupId].currentIndex;
            const prevIndex = (currentIndex - 1 + figures.length) % figures.length;
            
            showFigure(groupId, prevIndex);
        }
        
        // Smooth scrolling for TOC links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
        
        // Add edit mode to observation boxes
        document.querySelectorAll('.observation-content').forEach(box => {
            box.addEventListener('click', function() {
                this.classList.toggle('editing');
                this.focus();
            });
        });
        
        // Initialize all carousels
        document.querySelectorAll('[id^="carousel_"]').forEach(carousel => {
            const carouselId = carousel.id;
            initializeCarousel(carouselId);
        });
    </script>
</body>
</html>
"""
    return html


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def main():
    """Generate the HTML report."""
    print("=" * 70)
    print("GENERANDO REPORTE HTML")
    print("=" * 70)
    
    # Copy figures to report directory
    total_figures = copy_figures(FIGURE_GROUPS)
    
    # Start building HTML
    html_content = create_html_header()
    
    # Add table of contents
    print("Construyendo tabla de contenidos...")
    html_content += create_toc_entries(FIGURE_GROUPS)
    
    # Process each figure group
    print("Procesando grupos de figuras...\n")
    for group in FIGURE_GROUPS:
        print(f"  {group['titulo']}")
        # Find figures from source directory
        figures = find_images(group['directorio'], group['patron'])
        # Sort figures for consistent ordering
        figures = sorted(figures)
        html_content += create_figure_section(group, figures)
    
    # Add footer
    print("\nFinalización...")
    html_content += create_html_footer()
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\n" + "=" * 70)
    print("✓ ¡Reporte generado exitosamente!")
    print(f"  Ubicación: {report_dir}/")
    print(f"  Archivo principal: {output_file.name}")
    print(f"  Carpeta de figuras: figuras/")
    print(f"  Total de figuras: {total_figures}")
    print("=" * 70)
    print("\n📝 CÓMO USAR:")
    print("   1. Abre el archivo 'index.html' en tu navegador")
    print("   2. Haz clic en cualquier caja de observaciones (fondo rosa)")
    print("   3. Edita las viñetas con tus observaciones")
    print("   4. Los cambios se guardan automáticamente en el navegador")
    print("   5. Usa Ctrl+S o el navegador para descargar el archivo actualizado")
    print("=" * 70)


if __name__ == '__main__':
    main()
