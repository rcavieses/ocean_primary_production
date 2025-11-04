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


def load_meris_data(filepath):
    """
    Load MERIS/OLCI satellite data from NetCDF file with validation.
    
    Parameters
    ----------
    filepath : str or Path
        Path to MERIS NetCDF file
        
    Returns
    -------
    xarray.Dataset
        Dataset with validated variables
        
    Raises
    ------
    FileNotFoundError
        If file does not exist
    ValueError
        If required variables are missing or data is invalid
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"MERIS data file not found: {filepath}")
    
    # Load dataset
    ds = xr.open_dataset(filepath)
    
    # Define required variables
    required_vars = ['CHL', 'Rrs_412', 'Rrs_443', 'Rrs_490', 'Rrs_555', 
                    'Rrs_665', 'Rrs_709', 'SST', 'bbp', 'Kd_490', 'PAR']
    
    # Check for missing variables
    missing_vars = [var for var in required_vars if var not in ds.data_vars]
    if missing_vars:
        raise ValueError(f"Missing required variables: {missing_vars}")
    
    # Validate data ranges
    validation_ranges = {
        'CHL': (0.01, 50.0),
        'SST': (-2, 35),
        'Rrs_412': (0.0001, 0.05),
        'Rrs_443': (0.0001, 0.04),
        'Rrs_490': (0.0001, 0.03),
        'Rrs_555': (0.0001, 0.02),
        'Rrs_665': (0.0001, 0.01),
        'Rrs_709': (0.0001, 0.01),
        'bbp': (0.0001, 0.1),
        'Kd_490': (0.01, 5.0),
        'PAR': (1, 70)
    }
    
    # Log validation warnings
    for var, (vmin, vmax) in validation_ranges.items():
        if var in ds.data_vars:
            data = ds[var].values
            valid_mask = ~np.isnan(data)
            if np.any(valid_mask):
                data_min = np.nanmin(data)
                data_max = np.nanmax(data)
                if data_min < vmin or data_max > vmax:
                    print(f"Warning: {var} has values outside typical range [{vmin}, {vmax}]")
                    print(f"  Actual range: [{data_min:.4f}, {data_max:.4f}]")
    
    return ds


def extract_time_series(ds, lon_range, lat_range):
    """
    Extract time series for given geographic region.
    
    Parameters
    ----------
    ds : xarray.Dataset
        Input dataset
    lon_range : tuple
        (lon_min, lon_max)
    lat_range : tuple
        (lat_min, lat_max)
        
    Returns
    -------
    xarray.Dataset
        Subset with time series data for specified region
        
    Raises
    ------
    ValueError
        If coordinates not found or range invalid
    """
    # Find coordinate names
    lon_names = ['lon', 'longitude', 'x']
    lat_names = ['lat', 'latitude', 'y']
    
    lon_coord = next((coord for coord in lon_names if coord in ds.coords), None)
    lat_coord = next((coord for coord in lat_names if coord in ds.coords), None)
    
    if lon_coord is None or lat_coord is None:
        raise ValueError(f"Could not find coordinates. Available: {list(ds.coords)}")
    
    # Extract region
    ds_subset = ds.sel({
        lon_coord: slice(lon_range[0], lon_range[1]),
        lat_coord: slice(lat_range[0], lat_range[1])
    })
    
    return ds_subset


def validate_input_data(ds, required_vars=None):
    """
    Validate input dataset completeness and quality.
    
    Parameters
    ----------
    ds : xarray.Dataset
        Input dataset to validate
    required_vars : list, optional
        List of required variables. If None, uses MERIS standard variables
        
    Returns
    -------
    dict
        Validation results with issues list
    """
    if required_vars is None:
        required_vars = ['CHL', 'Rrs_412', 'Rrs_443', 'Rrs_490', 'Rrs_555', 
                        'Rrs_665', 'Rrs_709', 'SST', 'bbp', 'Kd_490', 'PAR']
    
    issues = []
    warnings = []
    
    # Check for required variables
    missing_vars = [var for var in required_vars if var not in ds.data_vars]
    if missing_vars:
        issues.append(f"Missing variables: {missing_vars}")
    
    # Check for time dimension
    if 'time' not in ds.dims:
        warnings.append("No time dimension found")
    
    # Check for spatial dimensions
    spatial_dims = [dim for dim in ds.dims if dim in ['x', 'y', 'lon', 'lat', 'latitude', 'longitude']]
    if len(spatial_dims) < 2:
        issues.append("Missing spatial dimensions")
    
    # Check for data quality
    for var in required_vars:
        if var in ds.data_vars:
            data = ds[var].values
            n_valid = np.sum(~np.isnan(data))
            n_total = data.size
            coverage = 100 * n_valid / n_total if n_total > 0 else 0
            
            if coverage < 50:
                warnings.append(f"{var}: only {coverage:.1f}% valid data")
            elif coverage < 80:
                warnings.append(f"{var}: {coverage:.1f}% valid data (consider quality)")
    
    return {
        'valid': len(issues) == 0,
        'errors': issues,
        'warnings': warnings
    }


def handle_missing_data(ds, method='interpolate', fill_value=None):
    """
    Handle missing values in dataset.
    
    Parameters
    ----------
    ds : xarray.Dataset
        Input dataset with potential NaN values
    method : str, optional
        'interpolate' - Linear interpolation
        'fill' - Fill with constant value
        'drop' - Remove NaN values
    fill_value : float, optional
        Value to use when method='fill'
        
    Returns
    -------
    xarray.Dataset
        Dataset with missing values handled
    """
    ds_out = ds.copy()
    
    for var in ds_out.data_vars:
        data = ds_out[var]
        
        if method == 'interpolate':
            # Interpolate NaN values
            ds_out[var] = data.interpolate_na(dim=list(ds_out[var].dims)[0] if ds_out[var].dims else None)
        elif method == 'fill':
            if fill_value is None:
                fill_value = data.mean().values
            ds_out[var] = data.fillna(fill_value)
        elif method == 'drop':
            ds_out[var] = data.dropna(dim=list(data.dims))
    
    return ds_out


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
    
    print(f"Data saved to: {filepath}")


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
