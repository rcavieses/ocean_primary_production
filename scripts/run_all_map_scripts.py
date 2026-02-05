#!/usr/bin/env python3
"""
Script to run all map visualization scripts for PFT data.
Processes data without spatial filtering.
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# Set matplotlib to non-interactive backend before importing anything else
os.environ['MPLBACKEND'] = 'Agg'

# Configuration
base_dir = Path(__file__).parent.parent
scripts_dir = base_dir / 'scripts'

# List of map scripts to run
MAP_SCRIPTS = [
    'plot_pft_maps.py',
    'plot_pft_monthly_timeseries.py',
    'plot_pft_quinquennial_maps.py',
    'plot_pft_quinquennial_diff.py',
    'plot_composition_percentages.py',
    'plot_lat_time_optimized.py',
]

def run_script(script_name):
    """Run a single script and return success/failure"""
    script_path = scripts_dir / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    print(f"\n{'='*70}")
    print(f"Running: {script_name}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(base_dir),
            check=True,
            capture_output=False
        )
        print(f"✓ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ {script_name} error: {str(e)}")
        return False

def main():
    """Execute all map scripts"""
    print("="*70)
    print("EXECUTING ALL MAP VISUALIZATION SCRIPTS")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {base_dir}")
    
    results = {}
    successful = 0
    failed = 0
    
    for script in MAP_SCRIPTS:
        results[script] = run_script(script)
        if results[script]:
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total scripts: {len(MAP_SCRIPTS)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\nDetailed Results:")
    for script, success in results.items():
        status = "✓" if success else "❌"
        print(f"  {status} {script}")
    
    print(f"\n{'='*70}\n")
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
