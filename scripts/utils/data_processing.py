"""
Utility functions for ocean primary production data processing.
"""
import os
import numpy as np
import xarray as xr
from pathlib import Path


def get_data_dir():
    """Get the data directory path."""
    return Path(__file__).parent.parent.parent / "data"


def load_netcdf_data(filepath):
    """
    Load NetCDF data file.
    
    Parameters
    ----------
    filepath : str or Path
        Path to the NetCDF file
        
    Returns
    -------
    xarray.Dataset
        Loaded dataset
    """
    return xr.open_dataset(filepath)


def preprocess_chlorophyll_data(ds, var_name='CHL'):
    """
    Preprocess chlorophyll data for analysis.
    
    Parameters
    ----------
    ds : xarray.Dataset
        Input dataset
    var_name : str, optional
        Name of the chlorophyll variable
        
    Returns
    -------
    xarray.Dataset
        Preprocessed dataset
    """
    # Remove invalid values
    if var_name in ds:
        ds[var_name] = ds[var_name].where(ds[var_name] > 0)
    
    return ds


def extract_features_for_ml(ds, var_name='CHL'):
    """
    Extract features from dataset for machine learning.
    
    Parameters
    ----------
    ds : xarray.Dataset
        Input dataset
    var_name : str, optional
        Name of the main variable
        
    Returns
    -------
    numpy.ndarray, numpy.ndarray
        Features (X) and valid mask
    """
    # Get the main variable
    if var_name not in ds:
        raise ValueError(f"Variable {var_name} not found in dataset")
    
    data = ds[var_name].values
    
    # Create features: original value, log-transformed value
    valid_mask = ~np.isnan(data) & (data > 0)
    
    n_samples = np.sum(valid_mask)
    features = np.zeros((n_samples, 2))
    
    # Extract valid values
    valid_data = data[valid_mask]
    features[:, 0] = valid_data
    features[:, 1] = np.log10(valid_data)
    
    return features, valid_mask


def save_processed_data(data, filepath):
    """
    Save processed data to file.
    
    Parameters
    ----------
    data : xarray.Dataset or numpy.ndarray
        Data to save
    filepath : str or Path
        Output file path
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    if isinstance(data, xr.Dataset):
        data.to_netcdf(filepath)
    else:
        np.save(filepath, data)
