#!/usr/bin/env python3
"""
Script to generate a comprehensive numerical report from all PFT analysis scripts.
Extracts key statistics from maps, quinquennial comparisons, and time series.
Output format: JSON (for AI/machine reading) + Markdown (for human reading)

Author: Analysis System
Date: March 3, 2026
"""

import os
os.environ['MPLBACKEND'] = 'Agg'

import xarray as xr
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import sys
import warnings

warnings.filterwarnings("ignore")

# Importar configuración y filtras
sys.path.insert(0, str(Path(__file__).parent))
from config_gulf_california import get_gulf_of_california_filter

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / 'data' / 'pft_golfo_california_2000_2024.nc'
STATISTICS_FILE = BASE_DIR / 'data' / 'pft_monthly_statistics.nc'
OUTPUT_DIR = BASE_DIR / 'data' / 'figures'
REPORT_JSON = OUTPUT_DIR / 'reporte_analisis_numerico.json'
REPORT_MD = OUTPUT_DIR / 'REPORTE_ANALISIS_CUANTITATIVO.md'

# Climate data files
NINO_FILE = BASE_DIR / 'data' / 'nino34.long.anom.csv'
MEI_FILE = BASE_DIR / 'data' / 'mei.exttimeseries.csv'
PDO_FILE = BASE_DIR / 'data' / 'pdo.timeseries.sstens.csv'

# Quinquennial periods
PERIODS = [
    ('2000-2004', '2000-01-01', '2004-12-31'),
    ('2005-2009', '2005-01-01', '2009-12-31'),
    ('2010-2014', '2010-01-01', '2014-12-31'),
    ('2015-2019', '2015-01-01', '2019-12-31'),
    ('2020-2024', '2020-01-01', '2024-12-31')
]

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

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_climate_index(filepath, index_name):
    """Load climate index data (MEI, NINO34, PDO)."""
    try:
        if index_name == 'MEI':
            # Space separated: year month1 month2 ... month12
            chunks = []
            with open(filepath, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if not parts or not parts[0].isdigit() or len(parts) < 13:
                        continue
                    year = int(parts[0])
                    for month_idx, val in enumerate(parts[1:13]):
                        try:
                            val_float = float(val)
                            if val_float > -90:
                                date = pd.Timestamp(year=year, month=month_idx+1, day=1)
                                chunks.append({'Date': date, index_name: val_float})
                        except:
                            pass
            df = pd.DataFrame(chunks)
            return df.set_index('Date')[index_name]
        
        elif index_name == 'NINO34':
            df = pd.read_csv(filepath, skiprows=1, header=None, 
                            names=['Date', 'NINO34'])
            df['Date'] = pd.to_datetime(df['Date'].str.strip())
            df['NINO34'] = pd.to_numeric(df['NINO34'], errors='coerce')
            df = df[df['NINO34'] > -90].dropna()
            return df.set_index('Date')['NINO34']
        
        elif index_name == 'PDO':
            df = pd.read_csv(filepath, skiprows=1, header=None, 
                            usecols=[0, 1], names=['Date', 'PDO'])
            df['Date'] = pd.to_datetime(df['Date'])
            df['PDO'] = pd.to_numeric(df['PDO'], errors='coerce')
            return df.set_index('Date')['PDO']
    
    except Exception as e:
        print(f"Warning: Could not load {index_name}: {e}")
        return None


def compute_period_mean(ds, var, start_date, end_date, mask=None):
    """Compute mean for a variable over a period."""
    # Try both raw variable and mean variable (for statistics file)
    var_to_use = f"{var}_mean" if f"{var}_mean" in ds else var
    
    if var_to_use not in ds:
        return None
    
    data_period = ds[var_to_use].sel(time=slice(start_date, end_date))
    
    # Apply mask only if available
    if mask is not None and 'latitude' in data_period.coords and 'longitude' in data_period.coords:
        data_period = data_period.where(mask, drop=False)
    
    valid_data = data_period.values[~np.isnan(data_period.values)]
    if len(valid_data) == 0:
        return None
    
    return {
        'mean': float(data_period.mean(skipna=True).values),
        'median': float(np.nanmedian(data_period.values)),
        'std': float(np.nanstd(data_period.values)),
        'min': float(np.nanmin(data_period.values)),
        'max': float(np.nanmax(data_period.values)),
        'count': int(len(valid_data))
    }


def correlate_monthly_series(pft_series, climate_series, max_lag=12):
    """Compute correlation between PFT series and climate index at different lags."""
    # Align series to common time range
    common_dates = pft_series.index.intersection(climate_series.index)
    if len(common_dates) < 12:
        return None
    
    pft_aligned = pft_series[common_dates].fillna(pft_series[common_dates].mean())
    climate_aligned = climate_series[common_dates].fillna(climate_series[common_dates].mean())
    
    correlations = {}
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # Shift climate backward (climate leads)
            c = np.corrcoef(pft_aligned[-lag:].values, 
                           climate_aligned[:lag].values)[0, 1]
        elif lag > 0:
            # Shift PFT backward (PFT leads)
            c = np.corrcoef(pft_aligned[:-lag].values, 
                           climate_aligned[lag:].values)[0, 1]
        else:
            c = np.corrcoef(pft_aligned.values, climate_aligned.values)[0, 1]
        
        if not np.isnan(c):
            correlations[lag] = float(c)
    
    if correlations:
        max_corr_lag = max(correlations.items(), key=lambda x: abs(x[1]))
        return {
            'max_correlation': float(max_corr_lag[1]),
            'lag_at_max': int(max_corr_lag[0]),
            'correlations_by_lag': correlations
        }
    return None


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def main():
    print("=" * 70)
    print("GENERATING COMPREHENSIVE ANALYSIS REPORT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    print()
    
    # Load datasets
    print("Loading datasets...")
    
    # Use statistics file for most analysis (much smaller than raw data)
    if STATISTICS_FILE.exists():
        print(f"  Using pre-aggregated statistics: {STATISTICS_FILE}")
        ds_stats = xr.open_dataset(STATISTICS_FILE)
        use_mask = False  # Stats file is 1D (time only)
    else:
        print(f"  Loading raw dataset: {DATA_FILE}")
        ds = xr.open_dataset(DATA_FILE)
        ds_stats = ds
        use_mask = True
    
    # Get spatial mask only if using raw data
    mask = None
    if use_mask:
        mask = get_gulf_of_california_filter(ds_stats, use_shapefile=True)
    
    # Load climate indices
    print("Loading climate indices...")
    mei_series = load_climate_index(MEI_FILE, 'MEI')
    nino_series = load_climate_index(NINO_FILE, 'NINO34')
    pdo_series = load_climate_index(PDO_FILE, 'PDO')
    
    # Initialize report structure
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'dataset': str(DATA_FILE),
            'filtered': True,
            'filter_type': 'shapefile_polygon',
            'study_area': 'Gulf of California',
            'period_start': '2000-01-01',
            'period_end': '2024-12-31',
            'variables_count': len(VARIABLES)
        },
        'variables': {}
    }
    
    # ========================================================================
    # ANALYSIS 1: MAP STATISTICS (Mean, Std, Min, Max over entire period)
    # ========================================================================
    print("\n[1/3] Computing map statistics...")
    
    for var in VARIABLES:
        var_to_use = f"{var}_mean" if f"{var}_mean" in ds_stats else var
        
        if var_to_use not in ds_stats:
            print(f"  WARNING: Variable {var_to_use} not found")
            continue
        
        print(f"  Processing {var}...")
        
        # Compute temporal mean from statistics file
        data_var = ds_stats[var_to_use]
        
        # Apply mask if available (only for raw 2D/3D data)
        if mask is not None and 'latitude' in data_var.coords and 'longitude' in data_var.coords:
            data_var = data_var.where(mask, drop=False)
        
        valid_data = data_var.values[~np.isnan(data_var.values)]
        
        report['variables'][var] = {
            'description': VAR_DESCRIPTIONS[var],
            'unit': 'mg m⁻³',
            'map_statistics': {
                'period': '2000-2024',
                'mean': float(np.nanmean(data_var.values)),
                'median': float(np.nanmedian(data_var.values)),
                'std': float(np.nanstd(data_var.values)),
                'min': float(np.nanmin(data_var.values)),
                'max': float(np.nanmax(data_var.values)),
                'count_valid_points': int(len(valid_data)),
                'percentile_5': float(np.nanpercentile(data_var.values, 5)),
                'percentile_25': float(np.nanpercentile(data_var.values, 25)),
                'percentile_75': float(np.nanpercentile(data_var.values, 75)),
                'percentile_95': float(np.nanpercentile(data_var.values, 95))
            }
        }
    
    # ========================================================================
    # ANALYSIS 2: QUINQUENNIAL COMPARISONS
    # ========================================================================
    print("\n[2/3] Computing quinquennial statistics and anomalies...")
    
    for var in VARIABLES:
        var_to_use = f"{var}_mean" if f"{var}_mean" in ds_stats else var
        
        if var_to_use not in ds_stats:
            continue
        
        print(f"  Processing {var}...")
        
        period_stats = {}
        for period_name, start_date, end_date in PERIODS:
            stats = compute_period_mean(ds_stats, var, start_date, end_date, mask)
            if stats:
                period_stats[period_name] = stats
        
        if period_stats:
            report['variables'][var]['quinquennial_statistics'] = period_stats
            
            # Compute anomalies (difference from reference period 2020-2024)
            if '2020-2024' in period_stats:
                reference_mean = period_stats['2020-2024']['mean']
                anomalies = {}
                for period_name, start_date, end_date in PERIODS[:-1]:  # Exclude 2020-2024
                    if period_name in period_stats:
                        anom_value = period_stats[period_name]['mean'] - reference_mean
                        pct_change = (anom_value / reference_mean * 100) if reference_mean != 0 else 0
                        anomalies[period_name] = {
                            'absolute_change': float(anom_value),
                            'percent_change': float(pct_change)
                        }
                
                if anomalies:
                    report['variables'][var]['anomalies_vs_2020_2024'] = anomalies
    
    # ========================================================================
    # ANALYSIS 3: TEMPORAL SERIES & CLIMATE CORRELATIONS
    # ========================================================================
    print("\n[3/3] Computing temporal series and climate correlations...")
    
    for var in VARIABLES:
        var_to_use = f"{var}_mean" if f"{var}_mean" in ds_stats else var
        
        if var_to_use not in ds_stats:
            continue
        
        print(f"  Processing {var}...")
        
        # Create monthly time series
        pft_var = ds_stats[var_to_use]
        
        # If data is 3D (lat, lon, time), compute spatial mean
        if len(pft_var.dims) == 3:
            pft_monthly = pft_var.mean(dim=['latitude', 'longitude'], skipna=True)
        else:
            pft_monthly = pft_var
        
        # Convert to pandas Series
        pft_series = pft_monthly.to_pandas()
        
        # Compute temporal statistics
        valid_values = pft_series[~pft_series.isna()]
        
        temporal_stats = {
            'mean': float(valid_values.mean()),
            'std': float(valid_values.std()),
            'min': float(valid_values.min()),
            'max': float(valid_values.max()),
            'coefficient_of_variation': float(valid_values.std() / valid_values.mean() * 100) 
                                        if valid_values.mean() != 0 else 0,
            'data_points': int(len(valid_values)),
            'coverage_percent': float(len(valid_values) / len(pft_series) * 100)
        }
        
        report['variables'][var]['temporal_statistics'] = temporal_stats
        
        # Compute trends (linear regression)
        x = np.arange(len(valid_values))
        y = valid_values.values
        if len(x) > 3:
            coeffs = np.polyfit(x, y, 1)
            trend_per_year = coeffs[0] * 12  # Convert to per-year
            report['variables'][var]['linear_trend'] = {
                'slope_per_month': float(coeffs[0]),
                'slope_per_year': float(trend_per_year),
                'intercept': float(coeffs[1])
            }
        
        # Correlations with climate indices
        correlations = {}
        
        if mei_series is not None:
            mei_corr = correlate_monthly_series(pft_series, mei_series)
            if mei_corr:
                correlations['MEI'] = mei_corr
        
        if nino_series is not None:
            nino_corr = correlate_monthly_series(pft_series, nino_series)
            if nino_corr:
                correlations['NINO34'] = nino_corr
        
        if pdo_series is not None:
            pdo_corr = correlate_monthly_series(pft_series, pdo_series)
            if pdo_corr:
                correlations['PDO'] = pdo_corr
        
        if correlations:
            report['variables'][var]['climate_correlations'] = correlations
    
    # ========================================================================
    # COMPARISONS BETWEEN VARIABLES
    # ========================================================================
    print("\nComputing inter-variable comparisons...")
    
    inter_variable_comparison = {}
    for i, var1 in enumerate(VARIABLES):
        var1_to_use = f"{var1}_mean" if f"{var1}_mean" in ds_stats else var1
        
        if var1_to_use not in ds_stats:
            continue
        
        for var2 in VARIABLES[i+1:]:
            var2_to_use = f"{var2}_mean" if f"{var2}_mean" in ds_stats else var2
            
            if var2_to_use not in ds_stats:
                continue
            
            data1 = ds_stats[var1_to_use].values
            data2 = ds_stats[var2_to_use].values
            
            # Ensure same length
            min_len = min(len(data1), len(data2))
            data1 = data1[:min_len]
            data2 = data2[:min_len]
            
            # Remove NaNs from both series
            valid_mask = ~(np.isnan(data1) | np.isnan(data2))
            data1_valid = data1[valid_mask]
            data2_valid = data2[valid_mask]
            
            # Only correlate if both have sufficient data
            if len(data1_valid) > 12:
                c = np.corrcoef(data1_valid, data2_valid)[0, 1]
                if not np.isnan(c):
                    inter_variable_comparison[f'{var1}_vs_{var2}'] = {
                        'temporal_correlation': float(c)
                    }
    
    if inter_variable_comparison:
        report['inter_variable_comparisons'] = inter_variable_comparison
    
    # ========================================================================
    # SAVE REPORTS
    # ========================================================================
    print("\nSaving reports...")
    
    # Save JSON report
    with open(REPORT_JSON, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✓ JSON report saved: {REPORT_JSON}")
    
    # Generate Markdown report
    generate_markdown_report(report, REPORT_MD)
    print(f"✓ Markdown report saved: {REPORT_MD}")
    
    print("\n" + "=" * 70)
    print("REPORT GENERATION COMPLETE")
    print("=" * 70)


def generate_markdown_report(report, filepath):
    """Generate human-readable Markdown report from report dictionary."""
    
    with open(filepath, 'w') as f:
        # Header
        f.write("# Comprehensive Analysis Report: PFT Data for Gulf of California\n\n")
        f.write(f"**Generated:** {report['metadata']['generated_at']}\n\n")
        
        # Metadata
        f.write("## Metadata\n\n")
        f.write(f"- **Dataset:** {report['metadata']['dataset']}\n")
        f.write(f"- **Study Area:** {report['metadata']['study_area']}\n")
        f.write(f"- **Spatial Filtering:** {report['metadata']['filtered']} ({report['metadata']['filter_type']})\n")
        f.write(f"- **Period:** {report['metadata']['period_start']} to {report['metadata']['period_end']}\n")
        f.write(f"- **Variables Analyzed:** {report['metadata']['variables_count']}\n\n")
        
        # Variables Analysis
        f.write("---\n\n")
        f.write("## Variables Analysis\n\n")
        
        for var_name in VARIABLES:
            if var_name not in report['variables']:
                continue
            
            var_data = report['variables'][var_name]
            f.write(f"### {var_name} - {var_data['description']}\n\n")
            
            # Map Statistics
            if 'map_statistics' in var_data:
                stats = var_data['map_statistics']
                f.write("#### Spatial Statistics (2000-2024)\n\n")
                f.write(f"| Metric | Value |\n")
                f.write(f"|--------|-------|\n")
                f.write(f"| Mean | {stats['mean']:.4f} {var_data['unit']} |\n")
                f.write(f"| Median | {stats['median']:.4f} {var_data['unit']} |\n")
                f.write(f"| Std Dev | {stats['std']:.4f} {var_data['unit']} |\n")
                f.write(f"| Min | {stats['min']:.4f} {var_data['unit']} |\n")
                f.write(f"| Max | {stats['max']:.4f} {var_data['unit']} |\n")
                f.write(f"| Range | {stats['max'] - stats['min']:.4f} {var_data['unit']} |\n")
                f.write(f"| P5 | {stats['percentile_5']:.4f} {var_data['unit']} |\n")
                f.write(f"| P25 | {stats['percentile_25']:.4f} {var_data['unit']} |\n")
                f.write(f"| P75 | {stats['percentile_75']:.4f} {var_data['unit']} |\n")
                f.write(f"| P95 | {stats['percentile_95']:.4f} {var_data['unit']} |\n")
                f.write(f"| Valid Points | {stats['count_valid_points']:,} |\n\n")
            
            # Quinquennial Analysis
            if 'quinquennial_statistics' in var_data:
                f.write("#### Quinquennial Period Comparison\n\n")
                quint = var_data['quinquennial_statistics']
                f.write(f"| Period | Mean | Std | Min | Max |\n")
                f.write(f"|--------|------|-----|-----|-----|\n")
                for period, stats in quint.items():
                    f.write(f"| {period} | {stats['mean']:.4f} | {stats['std']:.4f} | "
                           f"{stats['min']:.4f} | {stats['max']:.4f} |\n")
                f.write("\n")
            
            # Anomalies
            if 'anomalies_vs_2020_2024' in var_data:
                f.write("#### Anomalies from 2020-2024 Reference Period\n\n")
                f.write(f"| Period | Absolute Change | % Change |\n")
                f.write(f"|--------|-----------------|----------|\n")
                anom = var_data['anomalies_vs_2020_2024']
                for period, values in anom.items():
                    f.write(f"| {period} | {values['absolute_change']:+.4f} {var_data['unit']} | "
                           f"{values['percent_change']:+.2f}% |\n")
                f.write("\n")
            
            # Temporal Statistics
            if 'temporal_statistics' in var_data:
                f.write("#### Temporal Characteristics (Monthly Series)\n\n")
                temporal = var_data['temporal_statistics']
                f.write(f"| Metric | Value |\n")
                f.write(f"|--------|-------|\n")
                f.write(f"| Mean (monthly) | {temporal['mean']:.4f} {var_data['unit']} |\n")
                f.write(f"| Std Dev | {temporal['std']:.4f} {var_data['unit']} |\n")
                f.write(f"| Coef. of Variation | {temporal['coefficient_of_variation']:.2f}% |\n")
                f.write(f"| Data Coverage | {temporal['coverage_percent']:.1f}% |\n\n")
            
            # Trends
            if 'linear_trend' in var_data:
                f.write("#### Linear Trend (2000-2024)\n\n")
                trend = var_data['linear_trend']
                f.write(f"- **Per Month:** {trend['slope_per_month']:+.6f} {var_data['unit']}/month\n")
                f.write(f"- **Per Year:** {trend['slope_per_year']:+.4f} {var_data['unit']}/year\n")
                trend_pct = (trend['slope_per_year'] / temporal['mean'] * 100) if 'temporal_statistics' in var_data else 0
                f.write(f"- **Relative Change:** {trend_pct:+.3f}% per year\n\n")
            
            # Climate Correlations
            if 'climate_correlations' in var_data:
                f.write("#### Climate Index Correlations\n\n")
                correlations = var_data['climate_correlations']
                for index, corr_data in correlations.items():
                    f.write(f"##### {index}\n\n")
                    f.write(f"- **Maximum Correlation:** {corr_data['max_correlation']:.4f}\n")
                    f.write(f"- **Lag at Max:** {corr_data['lag_at_max']} months\n")
                    f.write(f"  {'(Climate leads)' if corr_data['lag_at_max'] < 0 else '(PFT leads)' if corr_data['lag_at_max'] > 0 else '(Synchronous)'}\n\n")
            
            f.write("---\n\n")
        
        # Inter-variable comparisons
        if 'inter_variable_comparisons' in report:
            f.write("## Inter-Variable Comparisons\n\n")
            f.write(f"| Variable Pair | Temporal Correlation |\n")
            f.write(f"|---|---|\n")
            for pair, data in report['inter_variable_comparisons'].items():
                if 'temporal_correlation' in data:
                    f.write(f"| {pair} | {data['temporal_correlation']:+.4f} |\n")
                elif 'spatial_correlation_mean' in data:
                    f.write(f"| {pair} | {data['spatial_correlation_mean']:+.4f} |\n")
                elif 'spatial_correlation' in data:
                    f.write(f"| {pair} | {data['spatial_correlation']:+.4f} |\n")
            f.write("\n")
        
        # Summary statistics
        f.write("---\n\n")
        f.write("## Summary Statistics\n\n")
        
        f.write("### Variables with Highest Variability (Coefficient of Variation)\n\n")
        f.write(f"| Variable | CV (%) |\n")
        f.write(f"|---|---|\n")
        
        cv_list = []
        for var in VARIABLES:
            if var in report['variables'] and 'temporal_statistics' in report['variables'][var]:
                cv = report['variables'][var]['temporal_statistics']['coefficient_of_variation']
                cv_list.append((var, cv))
        
        cv_list.sort(key=lambda x: x[1], reverse=True)
        for var, cv in cv_list[:5]:
            f.write(f"| {var} | {cv:.2f}% |\n")
        f.write("\n")
        
        f.write("### Variables with Strongest Upward Trends\n\n")
        f.write(f"| Variable | Trend (unit/year) |\n")
        f.write(f"|---|---|\n")
        
        trend_list = []
        for var in VARIABLES:
            if var in report['variables'] and 'linear_trend' in report['variables'][var]:
                trend = report['variables'][var]['linear_trend']['slope_per_year']
                trend_list.append((var, trend))
        
        trend_list.sort(key=lambda x: x[1], reverse=True)
        for var, trend in trend_list[:5]:
            f.write(f"| {var} | {trend:+.6f} |\n")
        f.write("\n")
        
        f.write("### Strongest Climate Correlations\n\n")
        f.write(f"| Variable | Climate Index | Max Correlation | Lag (months) |\n")
        f.write(f"|---|---|---|---|\n")
        
        corr_list = []
        for var in VARIABLES:
            if var in report['variables'] and 'climate_correlations' in report['variables'][var]:
                for index, corr_data in report['variables'][var]['climate_correlations'].items():
                    corr_list.append((var, index, corr_data['max_correlation'], corr_data['lag_at_max']))
        
        corr_list.sort(key=lambda x: abs(x[2]), reverse=True)
        for var, index, corr, lag in corr_list[:10]:
            f.write(f"| {var} | {index} | {corr:+.4f} | {lag} |\n")
        f.write("\n")
        
        f.write("---\n\n")
        f.write("*Report generated by Comprehensive Analysis System*\n")


if __name__ == '__main__':
    main()
