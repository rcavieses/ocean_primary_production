"""
Configuration file for phytoplankton group production analysis.
"""

# Model configuration
SOM_CONFIG = {
    'map_size': (8, 8),      # SOM grid dimensions
    'learning_rate': 0.5,     # Initial learning rate
    'sigma': 2.0,             # Initial neighborhood radius
    'n_iterations': 1500,     # Training iterations
    'random_state': 42        # For reproducibility
}

# Phytoplankton groups
PHYTOPLANKTON_GROUPS = {
    'Diatoms': {
        'pp_coefficient': 5.5,    # Higher efficiency for diatoms
        'pp_exponent': 0.8,
        'preferred_conditions': 'high_nutrients',
        'color': '#1f77b4'        # Blue
    },
    'Prokaryotes': {
        'pp_coefficient': 3.0,    # Lower efficiency for small cells
        'pp_exponent': 0.6,
        'preferred_conditions': 'oligotrophic',
        'color': '#ff7f0e'        # Orange
    },
    'Dinoflagellates': {
        'pp_coefficient': 4.0,    # Intermediate efficiency
        'pp_exponent': 0.7,
        'preferred_conditions': 'intermediate',
        'color': '#2ca02c'        # Green
    }
}

# Input variables and their properties
INPUT_VARIABLES = {
    'CHL': {
        'long_name': 'Chlorophyll-a concentration',
        'units': 'mg m⁻³',
        'valid_range': [0.01, 50],
        'log_transform': True
    },
    'Rrs_412': {
        'long_name': 'Remote sensing reflectance at 412 nm',
        'units': 'sr⁻¹',
        'valid_range': [0.0001, 0.05],
        'log_transform': False
    },
    'Rrs_443': {
        'long_name': 'Remote sensing reflectance at 443 nm',
        'units': 'sr⁻¹',
        'valid_range': [0.0001, 0.04],
        'log_transform': False
    },
    'Rrs_490': {
        'long_name': 'Remote sensing reflectance at 490 nm',
        'units': 'sr⁻¹',
        'valid_range': [0.0001, 0.03],
        'log_transform': False
    },
    'Rrs_555': {
        'long_name': 'Remote sensing reflectance at 555 nm',
        'units': 'sr⁻¹',
        'valid_range': [0.0001, 0.02],
        'log_transform': False
    },
    'Rrs_665': {
        'long_name': 'Remote sensing reflectance at 665 nm',
        'units': 'sr⁻¹',
        'valid_range': [0.0001, 0.01],
        'log_transform': False
    },
    'Rrs_709': {
        'long_name': 'Remote sensing reflectance at 709 nm',
        'units': 'sr⁻¹',
        'valid_range': [0.0001, 0.01],
        'log_transform': False
    },
    'SST': {
        'long_name': 'Sea Surface Temperature',
        'units': '°C',
        'valid_range': [-2, 35],
        'log_transform': False
    },
    'bbp': {
        'long_name': 'Backscattering coefficient',
        'units': 'm⁻¹',
        'valid_range': [0.0001, 0.1],
        'log_transform': True
    },
    'Kd_490': {
        'long_name': 'Diffuse attenuation coefficient at 490 nm',
        'units': 'm⁻¹',
        'valid_range': [0.01, 5.0],
        'log_transform': True
    },
    'PAR': {
        'long_name': 'Photosynthetically Available Radiation',
        'units': 'mol photons m⁻² d⁻¹',
        'valid_range': [1, 70],
        'log_transform': False
    }
}

# Output configuration
OUTPUT_CONFIG = {
    'create_maps': True,
    'create_netcdf': True,
    'create_report': True,
    'map_dpi': 300,
    'compression_level': 4
}

# Quality thresholds
QUALITY_THRESHOLDS = {
    'min_r2': 0.3,           # Minimum acceptable R²
    'max_rmse_ratio': 0.5,   # Maximum RMSE as fraction of mean
    'min_reliability': 0.2   # Minimum reliability index
}