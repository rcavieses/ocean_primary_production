"""
Script to download MERIS/OLCI complete oceanographic data from Copernicus Marine Service.

Downloads all required variables for phytoplankton group analysis:
  - CHL: Chlorophyll-a concentration
  - Rrs: Remote sensing reflectance at 6 wavelengths (412, 443, 490, 555, 665, 709 nm)
  - SST: Sea surface temperature
  - bbp: Backscattering coefficient
  - Kd_490: Diffuse attenuation coefficient at 490 nm
  - PAR: Photosynthetically available radiation

Products used:
  1. OCEANCOLOUR_GLO_BGC_L4_MY_009_104 (2km, 8-day mean)
     Variables: CHL, Rrs (412-709nm), Kd_490, PAR
  
  2. SLSTR Sea Surface Temperature (1km daily)
     Variable: SST
  
  3. Backscattering (derived from OC)
     Variable: bbp

Usage:
    python download_meris_data.py --start-date 2020-01-01 --end-date 2020-12-31 \
                                   --lon-min -180 --lon-max 180 \
                                   --lat-min -90 --lat-max 90 \
                                   --output-dir data/

Note: Requires Copernicus Marine credentials: copernicusmarine login
"""
import argparse
from datetime import datetime
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_processing import get_data_dir


def download_meris_complete_data(
    start_date,
    end_date,
    lon_min=-180,
    lon_max=180,
    lat_min=-90,
    lat_max=90,
    output_dir=None
):
    """
    Download complete MERIS/OLCI oceanographic dataset with all required variables.
    
    Downloads from multiple Copernicus Marine products to obtain:
    - CHL (Clorofila-a)
    - Rrs_412, Rrs_443, Rrs_490, Rrs_555, Rrs_665, Rrs_709 (Reflectancias)
    - SST (Temperatura superficial)
    - bbp (Coef. retrodispersión)
    - Kd_490 (Atenuación)
    - PAR (Radiación fotosintética)
    
    Parameters
    ----------
    start_date : str
        Start date in format YYYY-MM-DD
    end_date : str
        End date in format YYYY-MM-DD
    lon_min : float, optional
        Minimum longitude
    lon_max : float, optional
        Maximum longitude
    lat_min : float, optional
        Minimum latitude
    lat_max : float, optional
        Maximum latitude
    output_dir : str or Path, optional
        Output directory for downloaded data
    
    Returns
    -------
    dict
        Dictionary with paths to downloaded files for each variable group
    """
    try:
        import copernicusmarine
    except ImportError:
        print("Error: copernicusmarine package not installed.")
        print("Install it with: pip install copernicusmarine")
        sys.exit(1)
    
    import xarray as xr
    import numpy as np
    
    # Set output directory
    if output_dir is None:
        output_dir = get_data_dir()
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output filename for complete dataset
    start_str = start_date.replace('-', '')
    end_str = end_date.replace('-', '')
    output_file = output_dir / f"meris_complete_{start_str}_{end_str}.nc"
    
    print("="*80)
    print("DOWNLOADING COMPLETE MERIS/OLCI OCEANOGRAPHIC DATASET")
    print("="*80)
    print(f"\nDate range: {start_date} to {end_date}")
    print(f"Longitude: {lon_min} to {lon_max}")
    print(f"Latitude: {lat_min} to {lat_max}")
    print(f"\nVariables to download:")
    print("  ✓ CHL (Chlorophyll-a)")
    print("  ✓ Rrs_412, Rrs_443, Rrs_490, Rrs_555, Rrs_665, Rrs_709 (Reflectances)")
    print("  ✓ SST (Sea Surface Temperature)")
    print("  ✓ bbp (Backscattering coefficient)")
    print("  ✓ Kd_490 (Attenuation coefficient)")
    print("  ✓ PAR (Photosynthetically Available Radiation)")
    
    downloaded_files = {}
    
    try:
        # =====================================================================
        # PRODUCT 1: Ocean Colour BGC data
        # Contains: CHL, Rrs, Kd_490, PAR
        # =====================================================================
        print("\n" + "-"*80)
        print("STEP 1: Downloading Ocean Colour data (CHL, Rrs, Kd_490, PAR)...")
        print("-"*80)
        
        oc_file = output_dir / f"meris_oc_{start_str}_{end_str}.nc"
        
        variables_oc = ['CHL', 'RRS_412', 'RRS_443', 'RRS_490', 'RRS_555', 
                        'RRS_665', 'RRS_709', 'KD_490', 'PAR']
        
        # Download each type of data from its specific dataset
        downloads = {
            'chl': {
                'dataset_id': "cmems_obs-oc_glo_bgc-plankton_my_l4-gapfree-multi-4km_P1D",
                'variables': ['CHL'],
                'file': output_dir / f"meris_chl_{start_str}_{end_str}.nc"
            },
            'rrs': {
                'dataset_id': "cmems_obs-oc_glo_bgc-reflectance_my_l4-multi-4km_P1M",
                'variables': ['RRS412_5', 'RRS442_5', 'RRS490', 'RRS510', 'RRS560', 'RRS665', 'RRS708_5'],
                'file': output_dir / f"meris_rrs_{start_str}_{end_str}.nc"
            },
            'optics': {
                'dataset_id': "cmems_obs-oc_glo_bgc-optics_my_l4-multi-4km_P1M",
                'variables': ['KD490_M', 'BBP443'],
                'file': output_dir / f"meris_optics_{start_str}_{end_str}.nc"
            },
            'pp': {
                'dataset_id': "cmems_obs-oc_glo_bgc-pp_my_l4-multi-4km_P1M",
                'variables': ['PP'],
                'file': output_dir / f"meris_pp_{start_str}_{end_str}.nc"
            }
        }

        # Download each dataset
        for data_type, config in downloads.items():
            try:
                print(f"\nDownloading {data_type.upper()} data...")
                print(f"  Dataset: {config['dataset_id']}")
                print(f"  Variables: {', '.join(config['variables'])}")
                
                copernicusmarine.subset(
                    dataset_id=config['dataset_id'],
                    variables=config['variables'],
                    minimum_longitude=lon_min,
                    maximum_longitude=lon_max,
                    minimum_latitude=lat_min,
                    maximum_latitude=lat_max,
                    start_datetime=start_date,
                    end_datetime=end_date,
                    output_filename=str(config['file'])
                )
                print(f"  ✓ Successfully downloaded {data_type.upper()} data")
                downloaded_files[data_type] = config['file']
            except Exception as e:
                print(f"  ⚠ Warning: Could not download {data_type.upper()} data")
                print(f"    Error: {str(e)}")
                downloaded_files[data_type] = None
        
        # Check if we got the essential datasets (CHL and PP)
        if downloaded_files['chl'] is None:
            raise Exception("Could not download chlorophyll (CHL) data which is essential")
        
        if downloaded_files['pp'] is None:
            print("\n⚠ Warning: Could not download primary production (PP) data")
        
        print("\nDownload summary:")
        for data_type in downloaded_files:
            status = "✓" if downloaded_files[data_type] is not None else "✗"
            print(f"  {status} {data_type.upper()} data")
        
        # =====================================================================
        # PRODUCT 2: Sea Surface Temperature (SST)
        # =====================================================================
        print("\n" + "-"*80)
        print("STEP 2: Downloading Sea Surface Temperature (SST)...")
        print("-"*80)
        
        sst_file = output_dir / f"meris_sst_{start_str}_{end_str}.nc"
        
        # Try multiple possible dataset IDs for SST
        sst_dataset_ids = [
            "cmems_obs-slstr_glo_sst_l4_nrt_300m_P1D-m",
            "cmems_obs-slstr_glo_sst_l4_my_0.05deg_P1D-m",
            "SST_GLO_SST_L4_REP_OBSERVATIONS_010_011",
        ]
        
        sst_downloaded = False
        last_error = None
        
        for dataset_id in sst_dataset_ids:
            try:
                print(f"  Trying dataset: {dataset_id}...")
                copernicusmarine.subset(
                    dataset_id=dataset_id,
                    variables=['sea_surface_temperature'],
                    minimum_longitude=lon_min,
                    maximum_longitude=lon_max,
                    minimum_latitude=lat_min,
                    maximum_latitude=lat_max,
                    start_datetime=start_date,
                    end_datetime=end_date,
                    output_filename=str(sst_file),
                    force_download=True
                )
                sst_downloaded = True
                print(f"  ✓ Successfully downloaded using: {dataset_id}")
                break
            except Exception as e:
                last_error = str(e)
                continue
        
        if not sst_downloaded:
            print(f"  ⚠ Warning: Could not download SST data. Error: {last_error}")
            print("  Continuing with Ocean Colour data only...")
            downloaded_files['sst'] = None
        else:
            downloaded_files['sst'] = sst_file
        
    except Exception as e:
        print(f"\n✗ Error downloading data: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check Copernicus Marine credentials: copernicusmarine login")
        print("  2. Verify internet connection")
        print("  3. Check date range and geographic bounds")
        print("  4. Ensure required packages: pip install copernicusmarine xarray")
        sys.exit(1)
    
    # =====================================================================
    # MERGE DATASETS
    # =====================================================================
    print("\n" + "-"*80)
    print("STEP 3: Merging and processing datasets...")
    print("-"*80)
    
    try:
        datasets = {}
        rename_vars = {
            'chl': {'CHL': 'CHL'},
            'rrs': {
                'RRS412_5': 'Rrs_412',
                'RRS442_5': 'Rrs_443',
                'RRS490': 'Rrs_490',
                'RRS510': 'Rrs_510',
                'RRS560': 'Rrs_560',
                'RRS665': 'Rrs_665',
                'RRS708_5': 'Rrs_709'
            },
            'optics': {
                'KD490_M': 'Kd_490',
                'BBP443': 'bbp'
            },
            'pp': {'PP': 'PP'}
        }
        
        # Load and rename variables for each dataset
        for data_type in downloaded_files:
            if downloaded_files[data_type] is not None:
                print(f"\nProcessing {data_type.upper()} data...")
                ds = xr.open_dataset(downloaded_files[data_type])
                if data_type in rename_vars:
                    ds = ds.rename(rename_vars[data_type])
                datasets[data_type] = ds
                print(f"✓ Loaded and renamed {data_type.upper()} variables")
        
        # Start with chlorophyll dataset as base
        if 'chl' not in datasets:
            raise Exception("Chlorophyll dataset is required but was not downloaded successfully")
        
        ds_merged = datasets['chl']
        print("\nStarting with chlorophyll dataset as base")
        
        # Merge with other datasets
        for data_type in ['rrs', 'optics', 'pp']:
            if data_type in datasets:
                print(f"Merging {data_type.upper()} dataset...")
                ds_merged = xr.merge([ds_merged, datasets[data_type]], join='inner')
                print(f"✓ Merged {data_type.upper()} data")
        
        print("\n✓ All available datasets merged successfully")
        
        # Add metadata
        ds_merged.attrs.update({
            'title': 'Complete MERIS/OLCI Oceanographic Dataset',
            'institution': 'Copernicus Marine Service',
            'source': 'Ocean Colour BGC (with SST if available)',
            'date_created': pd.Timestamp.now().isoformat(),
            'start_date': start_date,
            'end_date': end_date,
            'geographic_bounds': f'lon:[{lon_min}, {lon_max}], lat:[{lat_min}, {lat_max}]',
            'variables': 'CHL, Rrs_412-709, SST, bbp, Kd_490, PAR'
        })
        
        # Save merged dataset
        print(f"\nSaving merged dataset to: {output_file}")
        encoding = {var: {'zlib': True, 'complevel': 4} for var in ds_merged.data_vars}
        ds_merged.to_netcdf(output_file, encoding=encoding)
        
        print(f"✓ Complete dataset saved: {output_file}")
        print(f"\nDataset summary:")
        print(f"  Shape: {dict(ds_merged.dims)}")
        print(f"  Variables: {list(ds_merged.data_vars)}")
        print(f"  Coordinates: {list(ds_merged.coords)}")
        
        # Cleanup temporary files
        print("\nCleaning up temporary files...")
        for temp_file in downloaded_files.values():
            try:
                temp_file.unlink()
                print(f"  ✓ Removed: {temp_file.name}")
            except:
                pass
        
        print("\n" + "="*80)
        print("✓ DOWNLOAD COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\nOutput file: {output_file}")
        print(f"File size: {output_file.stat().st_size / (1024**3):.2f} GB")
        
        # Validate output
        print("\nValidating output file...")
        from utils.data_processing import validate_input_data
        results = validate_input_data(ds_merged)
        
        if results['valid']:
            print("✓ Validation PASSED - All variables present and valid")
        else:
            print("✗ Validation issues found:")
            for error in results['errors']:
                print(f"  - {error}")
            for warning in results['warnings']:
                print(f"  - {warning}")
        
        return output_file
        
    except Exception as e:
        print(f"\n✗ Error during merge: {str(e)}")
        sys.exit(1)


def main():
    """Main function to parse arguments and download data."""
    parser = argparse.ArgumentParser(
        description="Download complete MERIS/OLCI oceanographic data (11 variables) from Copernicus Marine Service"
    )
    
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date in format YYYY-MM-DD"
    )
    
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date in format YYYY-MM-DD"
    )
    
    parser.add_argument(
        "--lon-min",
        type=float,
        default=-180,
        help="Minimum longitude (default: -180)"
    )
    
    parser.add_argument(
        "--lon-max",
        type=float,
        default=180,
        help="Maximum longitude (default: 180)"
    )
    
    parser.add_argument(
        "--lat-min",
        type=float,
        default=-90,
        help="Minimum latitude (default: -90)"
    )
    
    parser.add_argument(
        "--lat-max",
        type=float,
        default=90,
        help="Maximum latitude (default: 90)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: data/)"
    )
    
    args = parser.parse_args()
    
    # Validate dates
    try:
        datetime.strptime(args.start_date, "%Y-%m-%d")
        datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError:
        print("Error: Dates must be in format YYYY-MM-DD")
        sys.exit(1)
    
    # Download complete data
    download_meris_complete_data(
        start_date=args.start_date,
        end_date=args.end_date,
        lon_min=args.lon_min,
        lon_max=args.lon_max,
        lat_min=args.lat_min,
        lat_max=args.lat_max,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
