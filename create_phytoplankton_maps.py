#!/usr/bin/env python3
"""
Script para crear mapas de grupos de fitoplancton en una sola figura.

Este script genera visualizaciones completas de los diferentes grupos de fitoplancton
(Diatomeas, Procariotas, Dinoflagelados) mostrando sus distribuciones espaciales,
fracciones y producción primaria en paneles múltiples.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / "scripts"))

def create_phytoplankton_maps():
    """
    Crear mapas completos de grupos de fitoplancton en una sola figura.
    """
    print("="*80)
    print("CREANDO MAPAS DE GRUPOS DE FITOPLANCTON")
    print("="*80)
    
    try:
        # Import required modules
        from scripts.config import PHYTOPLANKTON_GROUPS
        from scripts.functions.primary_production_model import PrimaryProductionModel
        
        # Try to load xarray for real data
        try:
            import xarray as xr
            has_xarray = True
        except ImportError:
            print("! xarray no disponible, usando datos sintéticos")
            has_xarray = False
        
        # Set up paths
        base_dir = Path(__file__).parent
        data_dir = base_dir / "data"
        output_dir = data_dir / "phytoplankton_maps"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create data
        if has_xarray:
            meris_file = data_dir / "meris_chl_a_20080101_20241231.nc"
            
            if meris_file.exists():
                print("Cargando datos MERIS...")
                ds = xr.open_dataset(meris_file)
                
                # Use a specific time slice (middle of dataset)
                if 'time' in ds.dims and len(ds.time) > 1:
                    time_idx = len(ds.time) // 2
                    chl_data = ds.CHL.isel(time=time_idx).values
                    lon = ds.longitude.values
                    lat = ds.latitude.values
                    print(f"Usando datos del {ds.time.values[time_idx]}")
                else:
                    chl_data = ds.CHL.values.squeeze()
                    lon = ds.longitude.values
                    lat = ds.latitude.values
                
                print(f"Datos cargados: {chl_data.shape}")
            else:
                print("Archivo MERIS no encontrado, creando datos sintéticos...")
                has_xarray = False
        
        if not has_xarray:
            print("Creando datos sintéticos...")
            # Create synthetic data
            nx, ny = 120, 80
            lon = np.linspace(-20, 20, nx)
            lat = np.linspace(30, 70, ny)
            
            # Create coordinate grids
            LON, LAT = np.meshgrid(lon, lat)
            
            # Create realistic chlorophyll distribution
            # Higher near coasts and in certain regions
            coast_effect = np.exp(-((LON)**2 + (LAT-50)**2) / 100)  # North Sea-like region
            shelf_effect = np.exp(-((LON+10)**2 + (LAT-45)**2) / 200)  # Atlantic shelf
            
            # Base chlorophyll with gradients
            chl_data = (0.2 + 1.5 * coast_effect + 0.8 * shelf_effect + 
                       0.3 * np.random.random((ny, nx)))
            chl_data = np.maximum(chl_data, 0.05)  # Minimum value
            
            print(f"Datos sintéticos creados: {chl_data.shape}")
        
        # Simulate phytoplankton group analysis
        print("Simulando análisis de grupos de fitoplancton...")
        
        # Create group fractions based on environmental conditions
        def calculate_group_fractions(chl, lon_grid, lat_grid):
            """Calculate realistic group fractions based on environmental proxies."""
            ny, nx = chl.shape
            
            # Initialize fraction arrays
            diatom_frac = np.zeros((ny, nx))
            prokaryote_frac = np.zeros((ny, nx))
            dino_frac = np.zeros((ny, nx))
            
            for i in range(ny):
                for j in range(nx):
                    chl_val = chl[i, j]
                    lat_val = lat_grid[i, j] if len(lat_grid.shape) == 2 else lat_grid[i]
                    
                    # Diatoms: prefer high Chl-a, temperate latitudes
                    if chl_val > 1.0 and 40 < lat_val < 60:
                        diatom_frac[i, j] = 0.6 + 0.2 * np.random.random()
                    elif chl_val > 0.5:
                        diatom_frac[i, j] = 0.3 + 0.3 * np.random.random()
                    else:
                        diatom_frac[i, j] = 0.1 + 0.2 * np.random.random()
                    
                    # Prokaryotes: prefer low Chl-a, warmer waters
                    if chl_val < 0.3:
                        prokaryote_frac[i, j] = 0.6 + 0.2 * np.random.random()
                    elif lat_val < 40:  # Warmer latitudes
                        prokaryote_frac[i, j] = 0.4 + 0.3 * np.random.random()
                    else:
                        prokaryote_frac[i, j] = 0.2 + 0.3 * np.random.random()
                    
                    # Dinoflagellates: remainder, but with some constraints
                    remaining = 1.0 - diatom_frac[i, j] - prokaryote_frac[i, j]
                    dino_frac[i, j] = max(0.05, remaining)
                    
                    # Normalize to sum to 1
                    total = diatom_frac[i, j] + prokaryote_frac[i, j] + dino_frac[i, j]
                    if total > 0:
                        diatom_frac[i, j] /= total
                        prokaryote_frac[i, j] /= total
                        dino_frac[i, j] /= total
            
            return diatom_frac, prokaryote_frac, dino_frac
        
        # Calculate fractions
        if len(lat.shape) == 1 and len(lon.shape) == 1:
            LON, LAT = np.meshgrid(lon, lat)
        else:
            LON, LAT = lon, lat
            
        diatom_fraction, prokaryote_fraction, dino_fraction = calculate_group_fractions(
            chl_data, LON, LAT
        )
        
        # Calculate group-specific chlorophyll
        diatom_chl = chl_data * diatom_fraction
        prokaryote_chl = chl_data * prokaryote_fraction
        dino_chl = chl_data * dino_fraction
        
        # Calculate group-specific primary production using model coefficients
        group_configs = PHYTOPLANKTON_GROUPS
        
        diatom_pp = group_configs['Diatoms']['pp_coefficient'] * (diatom_chl ** group_configs['Diatoms']['pp_exponent'])
        prokaryote_pp = group_configs['Prokaryotes']['pp_coefficient'] * (prokaryote_chl ** group_configs['Prokaryotes']['pp_exponent'])
        dino_pp = group_configs['Dinoflagellates']['pp_coefficient'] * (dino_chl ** group_configs['Dinoflagellates']['pp_exponent'])
        
        # Total primary production
        total_pp = diatom_pp + prokaryote_pp + dino_pp
        
        print("Creando visualizaciones...")
        
        # Create the comprehensive figure
        fig = plt.figure(figsize=(20, 24))
        
        # Define consistent coordinate arrays for plotting
        if len(lon.shape) == 1:
            plot_lon, plot_lat = np.meshgrid(lon, lat)
        else:
            plot_lon, plot_lat = lon, lat
        
        # Color maps for different variables
        chl_cmap = 'plasma'
        frac_cmap = 'viridis'
        pp_cmap = 'YlOrRd'
        
        # 1. Total Chlorophyll-a (panel superior)
        ax1 = plt.subplot(4, 4, (1, 2))
        im1 = ax1.pcolormesh(plot_lon, plot_lat, chl_data, shading='auto', cmap=chl_cmap)
        ax1.set_title('Clorofila-a Total (mg/m³)', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Longitud (°)')
        ax1.set_ylabel('Latitud (°)')
        plt.colorbar(im1, ax=ax1, shrink=0.8)
        
        # 2. Total Primary Production
        ax2 = plt.subplot(4, 4, (3, 4))
        im2 = ax2.pcolormesh(plot_lon, plot_lat, total_pp, shading='auto', cmap=pp_cmap)
        ax2.set_title('Producción Primaria Total (mg C/m²/d)', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Longitud (°)')
        ax2.set_ylabel('Latitud (°)')
        plt.colorbar(im2, ax=ax2, shrink=0.8)
        
        # Group-specific panels (3 rows x 4 columns for each group)
        groups_data = {
            'Diatomeas': {
                'fraction': diatom_fraction,
                'chlorophyll': diatom_chl,
                'pp': diatom_pp,
                'color': group_configs['Diatoms']['color'],
                'row': 1  # Second row
            },
            'Procariotas': {
                'fraction': prokaryote_fraction,
                'chlorophyll': prokaryote_chl,
                'pp': prokaryote_pp,
                'color': group_configs['Prokaryotes']['color'],
                'row': 2  # Third row
            },
            'Dinoflagelados': {
                'fraction': dino_fraction,
                'chlorophyll': dino_chl,
                'pp': dino_pp,
                'color': group_configs['Dinoflagellates']['color'],
                'row': 3  # Fourth row
            }
        }
        
        for group_name, group_data in groups_data.items():
            row = group_data['row']
            base_pos = row * 4 + 1
            
            # Group fraction
            ax_frac = plt.subplot(4, 4, base_pos)
            im_frac = ax_frac.pcolormesh(plot_lon, plot_lat, group_data['fraction'], 
                                       shading='auto', cmap=frac_cmap, vmin=0, vmax=1)
            ax_frac.set_title(f'{group_name}\nFracción', fontsize=12, fontweight='bold')
            ax_frac.set_ylabel('Latitud (°)')
            plt.colorbar(im_frac, ax=ax_frac, shrink=0.8)
            
            # Group chlorophyll
            ax_chl = plt.subplot(4, 4, base_pos + 1)
            im_chl = ax_chl.pcolormesh(plot_lon, plot_lat, group_data['chlorophyll'], 
                                     shading='auto', cmap=chl_cmap)
            ax_chl.set_title(f'Chl-a {group_name}\n(mg/m³)', fontsize=12, fontweight='bold')
            plt.colorbar(im_chl, ax=ax_chl, shrink=0.8)
            
            # Group primary production
            ax_pp = plt.subplot(4, 4, base_pos + 2)
            im_pp = ax_pp.pcolormesh(plot_lon, plot_lat, group_data['pp'], 
                                   shading='auto', cmap=pp_cmap)
            ax_pp.set_title(f'PP {group_name}\n(mg C/m²/d)', fontsize=12, fontweight='bold')
            plt.colorbar(im_pp, ax=ax_pp, shrink=0.8)
            
            # Group statistics
            ax_stats = plt.subplot(4, 4, base_pos + 3)
            ax_stats.axis('off')
            
            # Calculate statistics
            mean_frac = np.nanmean(group_data['fraction'])
            mean_chl = np.nanmean(group_data['chlorophyll'])
            mean_pp = np.nanmean(group_data['pp'])
            max_pp = np.nanmax(group_data['pp'])
            
            # Contribution to total PP
            contrib = (mean_pp / np.nanmean(total_pp)) * 100
            
            stats_text = f"Estadísticas {group_name}:\n\n"
            stats_text += f"Fracción media: {mean_frac:.3f}\n"
            stats_text += f"Chl-a media: {mean_chl:.3f} mg/m³\n"
            stats_text += f"PP media: {mean_pp:.1f} mg C/m²/d\n"
            stats_text += f"PP máxima: {max_pp:.1f} mg C/m²/d\n"
            stats_text += f"Contribución: {contrib:.1f}%\n"
            
            ax_stats.text(0.05, 0.95, stats_text, transform=ax_stats.transAxes,
                         fontsize=10, verticalalignment='top', fontfamily='monospace',
                         bbox=dict(boxstyle="round,pad=0.3", facecolor=group_data['color'], alpha=0.3))
        
        # Add main title
        fig.suptitle('Análisis de Grupos de Fitoplancton\nDistribución Espacial y Producción Primaria', 
                    fontsize=18, fontweight='bold', y=0.98)
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save the figure
        output_file = output_dir / 'mapa_grupos_fitoplancton_completo.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
        
        print(f"✓ Mapa principal guardado: {output_file}")
        
        # Create a summary comparison figure
        create_comparison_figure(groups_data, total_pp, plot_lon, plot_lat, output_dir)
        
        # Create pie chart summary
        create_pie_chart_summary(groups_data, total_pp, output_dir)
        
        # Show the main figure
        plt.show()
        
        # Print summary
        print("\n" + "="*80)
        print("RESUMEN DEL ANÁLISIS")
        print("="*80)
        
        print(f"\nEstadísticas generales:")
        print(f"- Clorofila-a total media: {np.nanmean(chl_data):.3f} mg/m³")
        print(f"- Producción primaria total media: {np.nanmean(total_pp):.1f} mg C/m²/d")
        print(f"- Área analizada: {chl_data.shape[0]} × {chl_data.shape[1]} píxeles")
        
        print(f"\nContribuciones por grupo:")
        for group_name, group_data in groups_data.items():
            mean_pp = np.nanmean(group_data['pp'])
            contrib = (mean_pp / np.nanmean(total_pp)) * 100
            print(f"- {group_name}: {contrib:.1f}% ({mean_pp:.1f} mg C/m²/d)")
        
        print(f"\nArchivos generados:")
        for file in sorted(output_dir.glob("*.png")):
            print(f"- {file.name}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_comparison_figure(groups_data, total_pp, plot_lon, plot_lat, output_dir):
    """Crear figura de comparación directa entre grupos."""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Comparación Directa de Grupos de Fitoplancton', fontsize=16, fontweight='bold')
    
    # Fractions comparison
    ax1 = axes[0, 0]
    
    # Stack fractions for comparison
    bottom = np.zeros_like(list(groups_data.values())[0]['fraction'])
    colors = [data['color'] for data in groups_data.values()]
    
    for i, (group_name, group_data) in enumerate(groups_data.items()):
        if i == 0:
            im = ax1.pcolormesh(plot_lon, plot_lat, group_data['fraction'], 
                              shading='auto', cmap='Reds', vmin=0, vmax=1, alpha=0.7)
        elif i == 1:
            im = ax1.pcolormesh(plot_lon, plot_lat, group_data['fraction'], 
                              shading='auto', cmap='Blues', vmin=0, vmax=1, alpha=0.7)
        else:
            im = ax1.pcolormesh(plot_lon, plot_lat, group_data['fraction'], 
                              shading='auto', cmap='Greens', vmin=0, vmax=1, alpha=0.7)
    
    ax1.set_title('Fracciones de Grupos (Superpuestas)')
    ax1.set_xlabel('Longitud (°)')
    ax1.set_ylabel('Latitud (°)')
    
    # Primary production comparison
    ax2 = axes[0, 1]
    
    # Dominant group map
    pp_arrays = [data['pp'] for data in groups_data.values()]
    group_names = list(groups_data.keys())
    
    # Find dominant group at each pixel
    dominant_group = np.zeros_like(pp_arrays[0])
    for i in range(dominant_group.shape[0]):
        for j in range(dominant_group.shape[1]):
            pp_values = [arr[i, j] for arr in pp_arrays]
            dominant_group[i, j] = np.argmax(pp_values)
    
    # Create discrete colormap for dominant groups
    cmap_discrete = mcolors.ListedColormap(['#1f77b4', '#ff7f0e', '#2ca02c'])
    im2 = ax2.pcolormesh(plot_lon, plot_lat, dominant_group, 
                        shading='auto', cmap=cmap_discrete, vmin=0, vmax=2)
    
    ax2.set_title('Grupo Dominante por Píxel')
    ax2.set_xlabel('Longitud (°)')
    ax2.set_ylabel('Latitud (°)')
    
    # Add colorbar with group labels
    cbar2 = plt.colorbar(im2, ax=ax2)
    cbar2.set_ticks([0, 1, 2])
    cbar2.set_ticklabels(group_names)
    
    # Total PP distribution
    ax3 = axes[1, 0]
    im3 = ax3.pcolormesh(plot_lon, plot_lat, total_pp, shading='auto', cmap='viridis')
    ax3.set_title('Producción Primaria Total (mg C/m²/d)')
    ax3.set_xlabel('Longitud (°)')
    ax3.set_ylabel('Latitud (°)')
    plt.colorbar(im3, ax=ax3)
    
    # Scatter plot: Total PP vs Chlorophyll by dominant group
    ax4 = axes[1, 1]
    
    # Flatten arrays for scatter plot
    chl_flat = groups_data['Diatomeas']['chlorophyll'].flatten()
    pp_flat = total_pp.flatten()
    dom_flat = dominant_group.flatten()
    
    # Sample for visualization (too many points otherwise)
    sample_size = min(2000, len(chl_flat))
    sample_idx = np.random.choice(len(chl_flat), sample_size, replace=False)
    
    colors_scatter = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for i, group_name in enumerate(group_names):
        mask = dom_flat[sample_idx] == i
        if np.any(mask):
            ax4.scatter(chl_flat[sample_idx][mask], pp_flat[sample_idx][mask], 
                       c=colors_scatter[i], label=group_name, alpha=0.6, s=10)
    
    ax4.set_xlabel('Clorofila-a Total (mg/m³)')
    ax4.set_ylabel('Producción Primaria Total (mg C/m²/d)')
    ax4.set_title('PP vs Chl-a por Grupo Dominante')
    ax4.legend()
    ax4.set_xscale('log')
    ax4.set_yscale('log')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save comparison figure
    comparison_file = output_dir / 'comparacion_grupos_fitoplancton.png'
    plt.savefig(comparison_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Figura de comparación guardada: {comparison_file}")


def create_pie_chart_summary(groups_data, total_pp, output_dir):
    """Crear gráficos de torta con resumen estadístico."""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Resumen Estadístico - Grupos de Fitoplancton', fontsize=16, fontweight='bold')
    
    # Calculate contributions
    group_names = list(groups_data.keys())
    pp_contributions = []
    chl_contributions = []
    mean_fractions = []
    
    total_mean_pp = np.nanmean(total_pp)
    total_chl = sum([np.nanmean(data['chlorophyll']) for data in groups_data.values()])
    
    for group_data in groups_data.values():
        pp_mean = np.nanmean(group_data['pp'])
        chl_mean = np.nanmean(group_data['chlorophyll'])
        frac_mean = np.nanmean(group_data['fraction'])
        
        pp_contributions.append(pp_mean)
        chl_contributions.append(chl_mean)
        mean_fractions.append(frac_mean)
    
    colors = [data['color'] for data in groups_data.values()]
    
    # PP contribution pie chart
    ax1 = axes[0, 0]
    wedges1, texts1, autotexts1 = ax1.pie(pp_contributions, labels=group_names, autopct='%1.1f%%',
                                          colors=colors, startangle=90)
    ax1.set_title('Contribución a la Producción Primaria')
    
    # Chlorophyll contribution pie chart
    ax2 = axes[0, 1]
    wedges2, texts2, autotexts2 = ax2.pie(chl_contributions, labels=group_names, autopct='%1.1f%%',
                                          colors=colors, startangle=90)
    ax2.set_title('Contribución a la Clorofila-a')
    
    # Fraction distribution
    ax3 = axes[1, 0]
    wedges3, texts3, autotexts3 = ax3.pie(mean_fractions, labels=group_names, autopct='%1.1f%%',
                                          colors=colors, startangle=90)
    ax3.set_title('Fracción Media por Grupo')
    
    # Statistics table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Create statistics table
    stats_data = []
    for i, (group_name, group_data) in enumerate(groups_data.items()):
        pp_mean = np.nanmean(group_data['pp'])
        chl_mean = np.nanmean(group_data['chlorophyll'])
        frac_mean = np.nanmean(group_data['fraction'])
        
        stats_data.append([
            group_name,
            f"{frac_mean:.3f}",
            f"{chl_mean:.3f}",
            f"{pp_mean:.1f}",
            f"{(pp_mean/total_mean_pp)*100:.1f}%"
        ])
    
    # Add totals row
    stats_data.append([
        "TOTAL",
        "1.000",
        f"{total_chl:.3f}",
        f"{total_mean_pp:.1f}",
        "100.0%"
    ])
    
    # Create table
    table = ax4.table(cellText=stats_data,
                     colLabels=['Grupo', 'Fracción', 'Chl-a\n(mg/m³)', 'PP\n(mg C/m²/d)', 'Contrib.\nPP (%)'],
                     cellLoc='center',
                     loc='center',
                     bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Color the group rows
    for i in range(len(group_names)):
        for j in range(5):
            table[(i+1, j)].set_facecolor(colors[i])
            table[(i+1, j)].set_alpha(0.3)
    
    # Color the total row
    for j in range(5):
        table[(len(group_names)+1, j)].set_facecolor('lightgray')
        table[(len(group_names)+1, j)].set_alpha(0.5)
    
    ax4.set_title('Estadísticas Detalladas', fontsize=12, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # Save pie chart summary
    pie_file = output_dir / 'resumen_estadistico_grupos.png'
    plt.savefig(pie_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Resumen estadístico guardado: {pie_file}")


def main():
    """Función principal."""
    success = create_phytoplankton_maps()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())