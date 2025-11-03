"""
Script to estimate primary production from MERIS Chlorophyll-a data
using Random Forest machine learning model.

Usage:
    # Train a new model with synthetic data and apply to MERIS data
    python estimate_primary_production.py --input-file data/meris_chl_a_20100101_20101231.nc \
                                           --output-file data/primary_production_2010.nc \
                                           --train-model

    # Use a pre-trained model
    python estimate_primary_production.py --input-file data/meris_chl_a_20100101_20101231.nc \
                                           --output-file data/primary_production_2010.nc \
                                           --model-file models/pp_model.pkl
"""
import argparse
import sys
from pathlib import Path
import numpy as np
import xarray as xr

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_processing import load_netcdf_data, get_data_dir
from functions.primary_production_model import (
    PrimaryProductionModel,
    create_synthetic_training_data
)


def estimate_primary_production(
    input_file,
    output_file=None,
    model_file=None,
    train_new_model=False,
    chl_var_name='CHL'
):
    """
    Estimate primary production from chlorophyll data.
    
    Parameters
    ----------
    input_file : str or Path
        Path to input NetCDF file with chlorophyll data
    output_file : str or Path, optional
        Path to output NetCDF file
    model_file : str or Path, optional
        Path to saved model file (for loading/saving)
    train_new_model : bool, optional
        Whether to train a new model
    chl_var_name : str, optional
        Name of chlorophyll variable in the dataset
    
    Returns
    -------
    xarray.Dataset
        Dataset with primary production estimates
    """
    input_file = Path(input_file)
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    print(f"Loading chlorophyll data from: {input_file}")
    
    # Load the data
    try:
        ds = load_netcdf_data(input_file)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
    
    # Check if chlorophyll variable exists
    if chl_var_name not in ds:
        print(f"Error: Variable '{chl_var_name}' not found in dataset")
        print(f"Available variables: {list(ds.data_vars)}")
        sys.exit(1)
    
    print(f"Chlorophyll data shape: {ds[chl_var_name].shape}")
    
    # Initialize model
    model = PrimaryProductionModel(n_estimators=100, random_state=42)
    
    # Train or load model
    if train_new_model:
        print("\nTraining new Random Forest model...")
        print("Generating synthetic training data...")
        
        # Create synthetic training data
        chl_train, pp_train = create_synthetic_training_data(n_samples=10000)
        
        # Prepare features
        X_train, _ = model.prepare_features(chl_train)
        
        # Train the model
        metrics = model.train(X_train, pp_train)
        
        # Save the model if model_file is provided
        if model_file:
            model.save(model_file)
        
    elif model_file:
        print(f"\nLoading pre-trained model from: {model_file}")
        model_file = Path(model_file)
        
        if not model_file.exists():
            print(f"Error: Model file not found: {model_file}")
            sys.exit(1)
        
        model.load(model_file)
    else:
        print("Error: Must either train a new model (--train-model) or provide a model file (--model-file)")
        sys.exit(1)
    
    # Estimate primary production
    print("\nEstimating primary production...")
    
    chl_data = ds[chl_var_name].values
    
    # Handle different array dimensions
    if len(chl_data.shape) == 3:  # time, lat, lon
        n_time = chl_data.shape[0]
        pp_data = np.zeros_like(chl_data)
        
        for t in range(n_time):
            pp_data[t] = model.estimate_from_chlorophyll(chl_data[t])
            if (t + 1) % 10 == 0:
                print(f"  Processed {t + 1}/{n_time} time steps")
    else:
        pp_data = model.estimate_from_chlorophyll(chl_data)
    
    print("Estimation complete!")
    
    # Create output dataset
    ds_out = ds.copy()
    ds_out['primary_production'] = (ds[chl_var_name].dims, pp_data)
    ds_out['primary_production'].attrs = {
        'long_name': 'Estimated Primary Production',
        'units': 'mg C/m²/day',
        'method': 'Random Forest regression from chlorophyll-a',
        'description': 'Estimated ocean primary production using machine learning'
    }
    
    # Save output
    if output_file:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\nSaving results to: {output_file}")
        ds_out.to_netcdf(output_file)
        print("Results saved successfully!")
    
    # Print statistics
    print("\nPrimary Production Statistics:")
    print(f"  Mean: {np.nanmean(pp_data):.2f} mg C/m²/day")
    print(f"  Std: {np.nanstd(pp_data):.2f} mg C/m²/day")
    print(f"  Min: {np.nanmin(pp_data):.2f} mg C/m²/day")
    print(f"  Max: {np.nanmax(pp_data):.2f} mg C/m²/day")
    
    return ds_out


def main():
    """Main function to parse arguments and estimate primary production."""
    parser = argparse.ArgumentParser(
        description="Estimate primary production from MERIS Chlorophyll-a data"
    )
    
    parser.add_argument(
        "--input-file",
        type=str,
        required=True,
        help="Path to input NetCDF file with chlorophyll data"
    )
    
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Path to output NetCDF file (default: None, no output saved)"
    )
    
    parser.add_argument(
        "--model-file",
        type=str,
        default=None,
        help="Path to model file (for loading or saving)"
    )
    
    parser.add_argument(
        "--train-model",
        action="store_true",
        help="Train a new model with synthetic data"
    )
    
    parser.add_argument(
        "--chl-var",
        type=str,
        default="CHL",
        help="Name of chlorophyll variable in dataset (default: CHL)"
    )
    
    args = parser.parse_args()
    
    # Estimate primary production
    estimate_primary_production(
        input_file=args.input_file,
        output_file=args.output_file,
        model_file=args.model_file,
        train_new_model=args.train_model,
        chl_var_name=args.chl_var
    )


if __name__ == "__main__":
    main()
