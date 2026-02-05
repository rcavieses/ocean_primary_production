#!/usr/bin/env python3
"""
Script to generate an interactive HTML report that embeds all figures
created by other analysis scripts in the ocean_primary_production project.

Features:
- Automatically discovers and embeds figures from analysis scripts
- Organizes figures by analysis type with descriptive headers
- Includes placeholders for user observations
- Bootstrap-based responsive design
- Professional styling and navigation
"""

import os
from pathlib import Path
from datetime import datetime
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

base_dir = Path(__file__).parent.parent
figures_base = base_dir / 'data' / 'figures'
output_file = base_dir / 'Rwork' / 'analysis_report.html'

# Define figure groups with their properties
FIGURE_GROUPS = [
    {
        'id': 'latseries',
        'title': '1. Patrones Latitud-Tiempo (Heatmaps)',
        'description': 'Series de tiempo promediadas por latitud para cada tipo de fitoplancton.',
        'directory': figures_base / 'latseries',
        'image_pattern': '*_latseries.png',
        'group_by': 'species',  # Group by variable
    },
    {
        'id': 'timeseries_indices',
        'title': '2. Series Temporales Mensuales con Índices Climáticos',
        'description': 'Evolución temporal de fitoplancton con superposición de índices climáticos (NIÑO3.4, MEI, PDO).',
        'directory': figures_base / 'timeseries_indices',
        'image_pattern': '*_timeseries_analysis.png',
        'group_by': 'variable',
    },
    {
        'id': 'quinquennial_diff',
        'title': '3. Mapas de Diferencia Quinquenal',
        'description': 'Comparación de concentraciones entre el período 2020-2024 y períodos anteriores.',
        'directory': figures_base / 'quinquennial_diff',
        'image_pattern': '*_quinquennial_diff_maps.png',
        'group_by': 'variable',
    },
    {
        'id': 'quinquennial_maps',
        'title': '4. Mapas Quinquenales',
        'description': 'Mapas de concentración promediados para cada período de cinco años.',
        'directory': figures_base / 'quinquennial',
        'image_pattern': '*_quinquennial_map.png',
        'group_by': 'variable',
    },
    {
        'id': 'seasonal_analysis',
        'title': '5. Análisis Estacional',
        'description': 'Patrones de variación estacional para cada variable de fitoplancton.',
        'directory': figures_base / 'seasonal_analysis',
        'image_pattern': '*_seasonal*.png',
        'group_by': 'variable',
    },
]

# Variable descriptions for better display
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

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_images(directory, pattern):
    """Find images matching a pattern in a directory."""
    if not directory.exists():
        return []
    
    import glob
    matches = glob.glob(str(directory / pattern))
    return sorted([Path(m) for m in matches])


def extract_variable_name(filename):
    """Extract variable name from filename."""
    name = filename.split('_')[0]
    return name if name in VAR_DESCRIPTIONS else name


def get_relative_path(file_path, base_path):
    """Get relative path from base for HTML linking."""
    return Path(file_path).relative_to(base_path.parent)


def create_html_header(title, description):
    """Create HTML header section."""
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #2E86AB;
            --secondary-color: #A23B72;
            --success-color: #06A77D;
            --danger-color: #E63946;
            --warning-color: #F77F00;
            --light-bg: #F5F5F5;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--light-bg);
            color: #333;
        }}
        
        .navbar {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .navbar-brand {{
            font-weight: bold;
            font-size: 1.3rem;
        }}
        
        .report-header {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 40px 20px;
            margin-bottom: 30px;
            border-radius: 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .report-title {{
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .report-meta {{
            font-size: 1rem;
            opacity: 0.9;
        }}
        
        .section-header {{
            background: white;
            padding: 20px;
            margin-top: 40px;
            margin-bottom: 20px;
            border-left: 5px solid var(--primary-color);
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        
        .section-title {{
            font-size: 1.8rem;
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 10px;
        }}
        
        .section-description {{
            font-size: 1rem;
            color: #666;
            margin-bottom: 0;
        }}
        
        .figure-group {{
            background: white;
            padding: 30px;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-top: 3px solid var(--primary-color);
        }}
        
        .figure-title {{
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--light-bg);
        }}
        
        .figure-container {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .figure-image {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .figure-image:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}
        
        .observation-box {{
            background: linear-gradient(135deg, #f0f4ff 0%, #fff0f5 100%);
            border-left: 4px solid var(--secondary-color);
            padding: 20px;
            margin-top: 25px;
            border-radius: 6px;
            min-height: 150px;
        }}
        
        .observation-title {{
            font-weight: bold;
            color: var(--secondary-color);
            font-size: 1.1rem;
            margin-bottom: 10px;
        }}
        
        .observation-placeholder {{
            color: #999;
            font-style: italic;
            padding: 15px;
            background: white;
            border-radius: 4px;
            border: 2px dashed #ccc;
        }}
        
        .observation-text {{
            color: #333;
            line-height: 1.6;
        }}
        
        .footer {{
            background: white;
            padding: 30px;
            margin-top: 50px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #666;
        }}
        
        .container-main {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .toc {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .toc-title {{
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 15px;
        }}
        
        .toc-list {{
            list-style: none;
            padding: 0;
        }}
        
        .toc-list li {{
            margin-bottom: 10px;
        }}
        
        .toc-list a {{
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }}
        
        .toc-list a:hover {{
            color: var(--secondary-color);
            text-decoration: underline;
        }}
        
        .icon-info {{
            display: inline-block;
            width: 25px;
            height: 25px;
            background: var(--primary-color);
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 25px;
            margin-right: 10px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#top">
                <i class="fas fa-chart-line"></i> PFT Analysis Report
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#overview">Overview</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#sections">Sections</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    
    <!-- Report Header -->
    <div class="report-header" id="top">
        <div class="container-main">
            <h1 class="report-title">
                <i class="fas fa-microscope"></i> Ocean Primary Production Analysis
            </h1>
            <p class="report-meta">
                Phytoplankton Functional Types (PFT) - Gulf of California (2000-2024)
            </p>
            <p class="report-meta">
                <i class="far fa-calendar"></i> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </div>
    
    <!-- Main Container -->
    <div class="container-main">
        
        <!-- Overview Section -->
        <div id="overview" class="section-header">
            <h2 class="section-title">Project Overview</h2>
            <p class="section-description">
                This report presents a comprehensive analysis of phytoplankton functional types in the Gulf of California
                from 2000 to 2024. The analysis includes latitude-time patterns, temporal evolution, quinquennial comparisons,
                and seasonal variations. Each section includes figures and dedicated space for your detailed observations and
                interpretations.
            </p>
        </div>
        
        <!-- Table of Contents -->
        <div class="toc" id="sections">
            <div class="toc-title">
                <i class="fas fa-list"></i> Contents
            </div>
            <ul class="toc-list">
"""
    return html


def create_toc_entries(figure_groups):
    """Create table of contents entries."""
    html = ""
    for group in figure_groups:
        if (group['directory']).exists():
            group_id = group['id']
            group_title = group['title']
            html += f'                <li><a href="#{group_id}">{group_title}</a></li>\n'
    html += """            </ul>
        </div>
"""
    return html


def create_figure_section(group, figures):
    """Create a section for a group of figures."""
    html = f"""        <!-- Section: {group['title']} -->
        <div id="{group['id']}" class="section-header">
            <h2 class="section-title">{group['title']}</h2>
            <p class="section-description">{group['description']}</p>
        </div>
"""
    
    if not figures:
        html += """        <div class="alert alert-info">
            <i class="fas fa-info-circle"></i> No figures found in this section.
        </div>
"""
        return html
    
    # Group figures by variable
    grouped = {}
    for fig in figures:
        var_name = extract_variable_name(fig.name)
        if var_name not in grouped:
            grouped[var_name] = []
        grouped[var_name].append(fig)
    
    # Create figure containers
    for var_name in sorted(grouped.keys()):
        fig_list = grouped[var_name]
        var_desc = VAR_DESCRIPTIONS.get(var_name, var_name)
        
        html += f"""        <div class="figure-group">
            <div class="figure-title">{var_desc} ({var_name})</div>
"""
        
        for fig_path in fig_list:
            rel_path = get_relative_path(fig_path, base_dir)
            html += f"""            <div class="figure-container">
                <img src="{rel_path}" alt="{fig_path.name}" class="figure-image">
                <p style="margin-top: 10px; color: #666; font-size: 0.9rem;"><em>{fig_path.name}</em></p>
            </div>
"""
        
        # Add observation box
        html += f"""            <div class="observation-box">
                <div class="observation-title">
                    <i class="fas fa-pen-fancy"></i> Observations for {var_desc} ({var_name})
                </div>
                <div class="observation-placeholder">
                    <!-- EDITABLE: Add your observations about {var_desc} here -->
                    <p>Write your detailed observations and interpretations for {var_desc} ({var_name}) in this section...</p>
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
                <strong>Report Information:</strong> This analysis report was automatically generated by 
                <code>generate_html_report.py</code>
            </p>
            <p style="margin-top: 15px; color: #999;">
                Gulf of California Primary Production Analysis | 2000-2024 Dataset
            </p>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Smooth scrolling for TOC links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
        
        // Add edit functionality to observation boxes
        document.querySelectorAll('.observation-placeholder').forEach(box => {{
            box.addEventListener('click', function() {{
                const isEditable = this.contentEditable === 'true';
                this.contentEditable = !isEditable;
                this.style.backgroundColor = isEditable ? '' : '#fff9e6';
                this.style.cursor = isEditable ? 'default' : 'text';
            }});
        }});
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
    print("GENERATING HTML ANALYSIS REPORT")
    print("=" * 70)
    
    # Start building HTML
    html_content = create_html_header(
        "Ocean Primary Production Analysis Report",
        "Phytoplankton Functional Types Analysis - Gulf of California 2000-2024"
    )
    
    # Add table of contents
    print("\n📋 Building table of contents...")
    html_content += create_toc_entries(FIGURE_GROUPS)
    
    # Process each figure group
    print("\n📊 Processing figure groups...\n")
    for group in FIGURE_GROUPS:
        print(f"  Processing: {group['title']}")
        figures = find_images(group['directory'], group['image_pattern'])
        
        if figures:
            print(f"    ✓ Found {len(figures)} figure(s)")
            html_content += create_figure_section(group, figures)
        else:
            print(f"    ℹ No figures found (directory may not exist yet)")
            html_content += create_figure_section(group, [])
    
    # Add footer
    print("\n✍️  Adding footer and finalizing...\n")
    html_content += create_html_footer()
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("=" * 70)
    print(f"✓ Report generated successfully!")
    print(f"  Output: {output_file}")
    print(f"  File size: {output_file.stat().st_size / 1024:.2f} KB")
    print("=" * 70)
    print("\n📝 EDITING OBSERVATIONS:")
    print("   - Open the HTML file in your browser")
    print("   - Click on the observation boxes (pink background) to edit them")
    print("   - Your changes will be saved in the browser")
    print("   - To save permanently, use your browser's 'Save As' or copy the content")
    print("=" * 70)


if __name__ == '__main__':
    main()
