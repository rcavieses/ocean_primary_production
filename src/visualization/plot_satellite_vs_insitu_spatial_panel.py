#!/usr/bin/env python3
"""
Spatial Comparison Panel: Satellite vs In Situ Concentration
=============================================================

Generates a publication-quality figure panel showing:
  - Satellite-derived phytoplankton concentration time series
  - In situ eDNA frequency by sampling location
  - Scatter plots comparing temporal and spatial patterns
  - Comprehensive statistical comparison
  - Geographic distribution of samples

Data:
  - Satellite: pft_monthly_statistics.nc (Copernicus, 2000-2024)
  - In situ: taxonomy_corrected_edna_2.csv (eDNA, Gulf of California)
  
Outputs: Publication-quality PNG figures (300 dpi)

Author: Ocean Primary Production Analysis Pipeline
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle
from scipy.stats import linregress, pearsonr, spearmanr
from scipy.interpolate import griddata
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

# Set style for publication-quality figures
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica'],
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 12,
    'axes.linewidth': 1.0,
    'axes.labelweight': 'bold',
    'lines.linewidth': 1.5,
})

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'results' / 'satellite' / 'figures' / 'spatial_comparison_panel'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Data files
SATELLITE_FILE = DATA_DIR / 'processed' / 'pft_monthly_statistics.nc'
TAXONOMY_FILE = DATA_DIR / 'insitu' / 'taxonomy_corrected_edna_2.csv'

# Time range (use overlap period between satellite and in situ data)
START_DATE = '2000-01-01'
END_DATE = '2016-12-31'  # In situ data ends in Dec 2016

# Primary Producer Classification (mapped to actual phyla in data)
PRIMARY_PRODUCERS = {
    'Diatoms': ['Bacillariophyta'],
    'Dinoflagellates': ['Dino NA', 'Dinophyta'],  # 'Dino NA' is in the data
    'Green Algae': ['Chlorophyta'],
    'Haptophytes': ['Haptista', 'Haptophyta'],  # 'Haptista' is in the data
    'Ciliophora': ['Ciliophora'],  # Small protist predators
}

# Satellite <-> In Situ mapping
SPECIES_MAPPING = [
    {
        'name_en': 'Diatoms',
        'sat_var': 'DIATO_mean',
        'insitu_group': 'Diatoms',
        'color_sat': '#1B9E77',
        'color_insitu': '#D95F02',
    },
    {
        'name_en': 'Dinoflagellates',
        'sat_var': 'DINO_mean',
        'insitu_group': 'Dinoflagellates',
        'color_sat': '#2E86AB',
        'color_insitu': '#E63946',
    },
    {
        'name_en': 'Green Algae',
        'sat_var': 'GREEN_mean',
        'insitu_group': 'Green Algae',
        'color_sat': '#66A61E',
        'color_insitu': '#E6AB02',
    },
    {
        'name_en': 'Haptophytes',
        'sat_var': 'HAPTO_mean',
        'insitu_group': 'Haptophytes',
        'color_sat': '#7570B3',
        'color_insitu': '#A6761D',
    },
    {
        'name_en': 'Ciliated Protists',
        'sat_var': 'CHL_mean',
        'insitu_group': 'Ciliophora',
        'color_sat': '#E7298A',
        'color_insitu': '#66C2A5',
    },
    {
        'name_en': 'Total Chlorophyll',
        'sat_var': 'CHL_mean',
        'insitu_group': 'All',
        'color_sat': '#A6761D',
        'color_insitu': '#F0E442',
    },
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def excel_date_to_datetime(excel_date):
    """Convert Excel serial number or DD/MM/YYYY string to datetime."""
    if pd.isna(excel_date) or excel_date == '':
        return pd.NaT
    try:
        if isinstance(excel_date, str):
            if '/' in excel_date:
                return pd.to_datetime(excel_date, format='%d/%m/%Y', errors='coerce')
            else:
                excel_date = float(excel_date)
        excel_epoch = datetime(1899, 12, 30)
        return excel_epoch + pd.Timedelta(days=int(excel_date))
    except (ValueError, OverflowError):
        return pd.NaT


def load_satellite_data():
    """Load satellite PFT monthly statistics."""
    print("[INFO] Loading satellite data...")
    ds = xr.open_dataset(SATELLITE_FILE)
    
    # Convert time to datetime if needed
    if not isinstance(ds.time.values[0], np.datetime64):
        ds['time'] = pd.to_datetime(ds.time.values)
    
    # Filter to date range
    ds = ds.sel(time=slice(START_DATE, END_DATE))
    
    print(f"    → Dimensions: {dict(ds.dims)}")
    print(f"    → Variables: {list(ds.data_vars)}")
    
    return ds


def load_insitu_data():
    """Load in situ eDNA data."""
    print("[INFO] Loading in situ eDNA data...")
    df = pd.read_csv(TAXONOMY_FILE)
    
    print(f"    → Original records: {len(df)}")
    print(f"    → Columns: {list(df.columns)[:10]}...")
    
    # Normalize column names to lowercase
    df.columns = df.columns.str.lower()
    
    # Parse date column (already in YYYY-MM-DD format)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    else:
        print("[WARNING] No date column found")
        df['date'] = pd.NaT
    
    # Drop records without valid dates
    df = df.dropna(subset=['date'])
    
    # Filter to overlap period (2000-2016)
    df['year'] = df['date'].dt.year
    df = df[(df['year'] >= 2000) & (df['year'] <= 2016)].copy()
    
    print(f"    → Records after filtering (2000-2016): {len(df)}")
    
    return df


def classify_insitu_sample(row, group_name):
    """Classify an in situ sample to a functional group."""
    if group_name == 'All':
        return True
    
    if group_name not in PRIMARY_PRODUCERS:
        return False
    
    phyla_list = PRIMARY_PRODUCERS[group_name]
    
    # Check phylum column (direct string matching)
    try:
        phylum = str(row['phylum']).strip() if pd.notna(row['phylum']) else ''
        if phylum in phyla_list:
            return True
    except (KeyError, TypeError):
        pass
    
    return False


def get_insitu_by_group(df, group_name):
    """Get in situ samples for a specific functional group."""
    if group_name == 'All':
        return df.copy()
    
    mask = df.apply(lambda row: classify_insitu_sample(row, group_name), axis=1)
    return df[mask].copy()


def compute_statistics(sat_values, insitu_values):
    """Compute comprehensive comparison statistics."""
    # Remove NaN
    valid = ~(np.isnan(sat_values) | np.isnan(insitu_values))
    
    if valid.sum() < 3:
        return None
    
    sat_v = sat_values[valid]
    insitu_v = insitu_values[valid]
    
    # Correlations
    pearson_r, pearson_p = pearsonr(sat_v, insitu_v)
    spearman_r, spearman_p = spearmanr(sat_v, insitu_v)
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = linregress(sat_v, insitu_v)
    
    # Error metrics
    diff = sat_v - insitu_v
    rmse = np.sqrt(np.mean(diff**2))
    mae = np.mean(np.abs(diff))
    mape = np.mean(np.abs(diff / (insitu_v + 1e-6))) * 100
    
    return {
        'pearson_r': pearson_r,
        'pearson_p': pearson_p,
        'spearman_r': spearman_r,
        'spearman_p': spearman_p,
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'rmse': rmse,
        'mae': mae,
        'mape': mape,
        'n': valid.sum(),
        'sat_mean': sat_v.mean(),
        'sat_std': sat_v.std(),
        'insitu_mean': insitu_v.mean(),
        'insitu_std': insitu_v.std(),
    }


def interpolate_insitu_abundance(insitu_df, extent=(-117, -102, 18, 33), resolution=0.5):
    """Interpolate in situ abundance data to regular grid for mapping background."""
    if 'abundance' not in insitu_df.columns or len(insitu_df) < 3:
        return None, None, None
    
    lon = insitu_df['longitude'].values
    lat = insitu_df['latitude'].values
    values = insitu_df['abundance'].values
    
    # Clip extreme outliers for better visualization
    values = np.clip(values, 0, np.percentile(values, 95))
    
    # Create mesh grid for interpolation
    lon_grid, lat_grid = np.meshgrid(
        np.arange(extent[0], extent[1], resolution),
        np.arange(extent[2], extent[3], resolution)
    )
    
    # Flatten for interpolation
    points = np.column_stack([lon, lat])
    
    # Remove NaN
    valid = ~np.isnan(values)
    if valid.sum() < 3:
        return None, None, None
    
    # Interpolate
    interp_data = griddata(points[valid], values[valid], 
                          (lon_grid, lat_grid), method='cubic', fill_value=np.nan)
    
    return lon_grid, lat_grid, interp_data


def create_comparison_panel(species, ds, insitu_df):
    """Create publication-quality comparison panel with Cartopy basemaps and in situ abundance colors."""
    print(f"\n[INFO] Creating panel for {species['name_en']}...")
    
    # Get in situ samples for this group
    insitu_classified = get_insitu_by_group(insitu_df, species['insitu_group']).copy()
    
    if len(insitu_classified) == 0:
        print(f"[WARNING] No in situ samples for {species['name_en']}")
        return None
    
    # Get satellite variable
    sat_var = species['sat_var']
    if sat_var not in ds.data_vars:
        print(f"[WARNING] Satellite variable {sat_var} not found")
        return None
    
    # Extract satellite time series (temporal average for region)
    sat_data = ds[sat_var].values
    sat_time = pd.to_datetime(ds.time.values)
    
    # Monthly frequency of in situ samples
    insitu_classified['year_month'] = insitu_classified['date'].dt.to_period('M')
    insitu_freq = insitu_classified.groupby('year_month').size()
    
    # Match satellite and in situ time periods
    sat_df = pd.DataFrame({'sat_value': sat_data}, index=sat_time)
    sat_df['year_month'] = sat_df.index.to_period('M')
    
    # Merge for comparison
    comparison = pd.DataFrame({
        'year_month': insitu_freq.index,
        'insitu_count': insitu_freq.values,
    })
    sat_monthly = sat_df.groupby('year_month')['sat_value'].mean()
    comparison['sat_value'] = comparison['year_month'].map(sat_monthly)
    comparison = comparison.dropna()
    
    if len(comparison) < 3:
        print(f"[WARNING] Insufficient comparison points")
        return None
    
    # Compute statistics
    stats = compute_statistics(comparison['sat_value'].values, comparison['insitu_count'].values)
    
    # Interpolate in situ abundance data for mapping
    lon_grid, lat_grid, insitu_interp = interpolate_insitu_abundance(insitu_classified)
    
    # Create figure with new layout: 2x3 grid with Cartopy projections
    fig = plt.figure(figsize=(18, 10))
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.30)
    
    # Gulf of California extent
    extent = [-117, -102, 18, 33]
    projection = ccrs.PlateCarree()
    
    # =========================================================================
    # TOP ROW: COMPARATIVE MAPS WITH CARTOPY BASEMAPS
    # =========================================================================
    
    # 1. In Situ Abundance Distribution Map (interpolated background)
    ax1 = fig.add_subplot(gs[0, 0], projection=projection)
    ax1.set_extent(extent, crs=projection)
    
    # Add base map features
    ax1.coastlines(resolution='10m', linewidth=1.5, color='black')
    ax1.add_feature(cfeature.BORDERS, linewidth=0.8, edgecolor='gray')
    ax1.add_feature(cfeature.LAND, facecolor='#CCCCCC', alpha=0.7)
    
    # Plot interpolated in situ abundance as background
    if insitu_interp is not None:
        im1 = ax1.contourf(lon_grid, lat_grid, insitu_interp, cmap='YlOrRd', 
                          levels=15, alpha=0.7, transform=projection)
        cbar1 = plt.colorbar(im1, ax=ax1, pad=0.05, shrink=0.8)
        cbar1.set_label('Abundance Density (OTUs)', fontsize=9)
    
    # Overlay in situ points colored by Abundance
    if 'abundance' in insitu_classified.columns:
        abundance_vals = insitu_classified['abundance'].values
        abundance_vals = np.clip(abundance_vals, 0, np.percentile(abundance_vals, 95))
        
        scatter1 = ax1.scatter(insitu_classified['longitude'], 
                              insitu_classified['latitude'],
                              c=abundance_vals, cmap='plasma', s=150, 
                              alpha=0.85, edgecolors='white', linewidth=1.5,
                              transform=projection, zorder=5)
    
    ax1.set_title(f'In Situ Abundance Distribution\n({species["name_en"]})', 
                  fontweight='bold', fontsize=11, color=species['color_sat'])
    ax1.gridlines(draw_labels=True, linewidth=0.5, alpha=0.3, linestyle='--')
    
    # 2. In Situ Sampling Temporal Distribution Map
    ax2 = fig.add_subplot(gs[0, 1], projection=projection)
    ax2.set_extent(extent, crs=projection)
    
    # Add base map features
    ax2.coastlines(resolution='10m', linewidth=1.5, color='black')
    ax2.add_feature(cfeature.BORDERS, linewidth=0.8, edgecolor='gray')
    ax2.add_feature(cfeature.LAND, facecolor='#CCCCCC', alpha=0.7)
    
    # Plot interpolated background (lighter)
    if insitu_interp is not None:
        ax2.contourf(lon_grid, lat_grid, insitu_interp, cmap='YlOrRd', 
                    levels=15, alpha=0.3, transform=projection)
    
    # Overlay in situ points colored by year
    scatter2 = ax2.scatter(insitu_classified['longitude'], 
                          insitu_classified['latitude'],
                          c=insitu_classified['date'].dt.year, 
                          cmap='viridis', s=150, alpha=0.85, 
                          edgecolors='white', linewidth=1.5,
                          transform=projection, zorder=5)
    cbar2 = plt.colorbar(scatter2, ax=ax2, pad=0.05, shrink=0.8)
    cbar2.set_label('Year of Sampling', fontsize=9)
    
    ax2.set_title(f'Temporal Distribution\n({species["name_en"]})', 
                  fontweight='bold', fontsize=11, color=species['color_insitu'])
    ax2.gridlines(draw_labels=True, linewidth=0.5, alpha=0.3, linestyle='--')
    
    # 3. Satellite vs In Situ Difference Map
    ax3 = fig.add_subplot(gs[0, 2], projection=projection)
    ax3.set_extent(extent, crs=projection)
    
    # Add base map features
    ax3.coastlines(resolution='10m', linewidth=1.5, color='black')
    ax3.add_feature(cfeature.BORDERS, linewidth=0.8, edgecolor='gray')
    ax3.add_feature(cfeature.LAND, facecolor='#CCCCCC', alpha=0.7)
    
    if len(comparison) > 3:
        # Normalize both datasets to 0-1
        sat_norm = (comparison['sat_value'].values - comparison['sat_value'].min()) / \
                   (comparison['sat_value'].max() - comparison['sat_value'].min() + 1e-6)
        insitu_norm = (comparison['insitu_count'].values - comparison['insitu_count'].min()) / \
                      (comparison['insitu_count'].max() - comparison['insitu_count'].min() + 1e-6)
        diff_values = sat_norm - insitu_norm
        
        # Create scatter colored by difference
        scatter_diff = ax3.scatter(insitu_classified['longitude'][:len(diff_values)], 
                                  insitu_classified['latitude'][:len(diff_values)],
                                  c=diff_values, cmap='RdBu_r', s=150, alpha=0.85,
                                  edgecolors='white', linewidth=1.5, vmin=-1, vmax=1,
                                  transform=projection, zorder=5)
        cbar3 = plt.colorbar(scatter_diff, ax=ax3, pad=0.05, shrink=0.8)
        cbar3.set_label('Normalized Difference', fontsize=9)
    
    ax3.set_title('Satellite vs In Situ\n(Red=Sat High, Blue=InSitu High)', 
                  fontweight='bold', fontsize=11)
    ax3.gridlines(draw_labels=True, linewidth=0.5, alpha=0.3, linestyle='--')
    
    # =========================================================================
    # BOTTOM ROW: STATISTICAL ANALYSIS
    # =========================================================================
    
    # 4. Correlation Scatter Plot
    ax4 = fig.add_subplot(gs[1, 0])
    
    ax4.scatter(comparison['sat_value'], comparison['insitu_count'],
               s=140, alpha=0.7, color=species['color_sat'],
               edgecolors='black', linewidth=1.3)
    
    if stats and not np.isnan(stats['slope']):
        x_range = np.array([comparison['sat_value'].min(), comparison['sat_value'].max()])
        y_fit = stats['slope'] * x_range + stats['intercept']
        ax4.plot(x_range, y_fit, 'r--', linewidth=2.5, alpha=0.9, label='Regression')
    
    ax4.set_xlabel(f'{sat_var} Satellite Value (mg m⁻³)', fontweight='bold', fontsize=10)
    ax4.set_ylabel('In Situ Record Count', fontweight='bold', fontsize=10)
    ax4.set_title('Temporal Correlation Analysis', fontweight='bold', fontsize=11)
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=9)
    
    if stats:
        stats_box = f"r = {stats['pearson_r']:.3f}\np = {stats['pearson_p']:.2e}\nR² = {stats['r_squared']:.3f}"
        ax4.text(0.05, 0.95, stats_box, transform=ax4.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.85))
    
    # 5. Residual Analysis Plot
    ax5 = fig.add_subplot(gs[1, 1])
    
    if stats and not np.isnan(stats['slope']):
        predicted = stats['slope'] * comparison['sat_value'] + stats['intercept']
        residuals = comparison['insitu_count'] - predicted
        ax5.scatter(predicted, residuals, s=120, alpha=0.7, color=species['color_sat'],
                   edgecolors='black', linewidth=1.2)
        ax5.axhline(y=0, color='r', linestyle='--', linewidth=2.5, alpha=0.9)
        ax5.set_xlabel('Predicted Count', fontweight='bold', fontsize=10)
        ax5.set_ylabel('Residuals', fontweight='bold', fontsize=10)
        ax5.set_title('Model Residuals', fontweight='bold', fontsize=11)
        ax5.grid(True, alpha=0.3)
    
    # 6. Compact Statistics Box
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')
    
    if stats:
        summary_text = f"""STATISTICS
{'─'*30}
n = {stats['n']}
r (Pearson) = {stats['pearson_r']:.3f}
R² = {stats['r_squared']:.3f}
p-value = {stats['pearson_p']:.2e}

Error Metrics:
RMSE: {stats['rmse']:.3f}
MAE:  {stats['mae']:.3f}
MAPE: {stats['mape']:.1f}%

Satellite Mean: {stats['sat_mean']:.3f}
Satellite Std: {stats['sat_std']:.3f}
InSitu Mean: {stats['insitu_mean']:.1f}
InSitu Std: {stats['insitu_std']:.1f}
        """
    else:
        summary_text = "Insufficient\ndata for\nstatistics"
    
    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
            fontsize=7.5, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.85, pad=0.8))
    
    # Main title
    fig.suptitle(f'{species["name_en"]}: Spatial & Temporal Comparison (Satellite vs In Situ)\nGulf of California, 2000-2016',
                fontsize=13, fontweight='bold', y=0.998)
    
    return fig


def main():
    """Main execution."""
    print("\n" + "="*70)
    print("SATELLITE vs IN SITU SPATIAL COMPARISON PANEL GENERATOR")
    print("="*70)
    print(f"Output directory: {OUTPUT_DIR}")
    
    try:
        # Load data
        ds = load_satellite_data()
        insitu_df = load_insitu_data()
        
        print(f"[SUCCESS] Data loaded successfully")
        
        # Create panels
        generated_count = 0
        for species in SPECIES_MAPPING:
            try:
                fig = create_comparison_panel(species, ds, insitu_df)
                
                if fig:
                    # Save figure
                    safe_name = (species['name_en']
                                .replace(' ', '_')
                                .replace('(', '')
                                .replace(')', '')
                                .lower())
                    output_file = OUTPUT_DIR / f"spatial_comparison_{safe_name}.png"
                    fig.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
                    print(f"[SUCCESS] Saved: {output_file.name}")
                    generated_count += 1
                    plt.close(fig)
                
            except Exception as e:
                print(f"[ERROR] {species['name_en']}: {str(e)}")
                continue
        
        print("="*70)
        print(f"[DONE] Generated {generated_count} comparison panels")
        print(f"       Output: {OUTPUT_DIR}")
        print("="*70)
        
    except Exception as e:
        print(f"[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
