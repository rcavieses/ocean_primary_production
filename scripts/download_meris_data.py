"""
Script to download MERIS 8-Day mean sea surface Chlorophyll-a concentration data
from Copernicus Marine Environment Monitoring Service (CMEMS).

Data Product: OCEANCOLOUR_GLO_BGC_L4_MY_009_104
Variable: Chlorophyll-a concentration (CHL)
Resolution: 4km (monthly aggregated product)
Temporal resolution: Monthly mean

Usage:
    python download_meris_data.py --start-date 2010-01-01 --end-date 2010-12-31 \
                                   --lon-min -180 --lon-max 180 \
                                   --lat-min -90 --lat-max 90

Note: You need to have Copernicus Marine credentials configured.
      Run: copernicusmarine login
"""
import argparse
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_processing import get_data_dir


def download_meris_chlorophyll(
    start_date,
    end_date,
    lon_min=-180,
    lon_max=180,
    lat_min=-90,
    lat_max=90,
    output_dir=None
):
    """
    Download MERIS chlorophyll-a data from Copernicus Marine Service.
    
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
    Path
        Path to downloaded file
    """
    try:
        import copernicusmarine
    except ImportError:
        print("Error: copernicusmarine package not installed.")
        print("Install it with: pip install copernicusmarine")
        sys.exit(1)
    
    # Set output directory
    if output_dir is None:
        output_dir = get_data_dir()
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output filename
    start_str = start_date.replace('-', '')
    end_str = end_date.replace('-', '')
    output_file = output_dir / f"meris_chl_a_{start_str}_{end_str}.nc"
    
    print(f"Downloading MERIS Chlorophyll-a data...")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Longitude range: {lon_min} to {lon_max}")
    print(f"  Latitude range: {lat_min} to {lat_max}")
    print(f"  Output file: {output_file}")
    
    try:
        # Download data using Copernicus Marine Toolbox
        # Product: OCEANCOLOUR_GLO_BGC_L4_MY_009_104
        # Dataset: cmems_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1M
        copernicusmarine.subset(
            dataset_id="cmems_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1M",
            variables=["CHL"],
            minimum_longitude=lon_min,
            maximum_longitude=lon_max,
            minimum_latitude=lat_min,
            maximum_latitude=lat_max,
            start_datetime=start_date,
            end_datetime=end_date,
            output_filename=str(output_file),
            force_download=True
        )
        
        print(f"\nDownload completed successfully!")
        print(f"Data saved to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"\nError downloading data: {str(e)}")
        print("\nNote: Make sure you have:")
        print("  1. Valid Copernicus Marine credentials")
        print("  2. Logged in using: copernicusmarine login")
        print("  3. Internet connection")
        sys.exit(1)


def main():
    """Main function to parse arguments and download data."""
    parser = argparse.ArgumentParser(
        description="Download MERIS Chlorophyll-a data from Copernicus Marine Service"
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
    
    # Download data
    download_meris_chlorophyll(
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
