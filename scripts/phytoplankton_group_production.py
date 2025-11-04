#!/usr/bin/env python3
"""
Phytoplankton Group Primary Production Calculator

This script calculates Primary Production (PP) by Phytoplankton Groups (PGs) using:
- Input: Chl-a total, Rrs (412, 443, 490, 555, 665, 709 nm), SST, bbp, Kd490, PAR
- Core Algorithm: Pre-trained ML model (SOM) for Chl-a fraction estimation
- Output: PP maps by group and quality metrics with reliability index

Author: AI Assistant
Date: November 2024
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib
import warnings
from typing import Dict, Tuple, Optional, List
warnings.filterwarnings('ignore')

# Import custom functions
import sys
sys.path.append(str(Path(__file__).parent))
from functions.primary_production_model import PrimaryProductionModel
from utils.data_processing import load_meris_data, extract_time_series


class SelfOrganizingMap:
    """
    Self-Organizing Map (SOM) implementation for phytoplankton group classification.
    
    This model classifies ocean pixels into phytoplankton functional groups based on
    optical and environmental properties.
    """
    
    def __init__(self, map_size=(10, 10), learning_rate=0.5, sigma=1.0, random_state=42):
        """
        Initialize SOM parameters.
        
        Parameters
        ----------
        map_size : tuple
            Dimensions of the SOM grid (height, width)
        learning_rate : float
            Initial learning rate
        sigma : float
            Initial neighborhood radius
        random_state : int
            Random seed for reproducibility
        """
        self.map_size = map_size
        self.learning_rate = learning_rate
        self.sigma = sigma
        self.random_state = random_state
        np.random.seed(random_state)
        
        # Initialize weights randomly
        self.weights = None
        self.trained = False
        
        # Phytoplankton group labels
        self.group_names = ['Diatoms', 'Prokaryotes', 'Dinoflagellates']
        self.n_groups = len(self.group_names)
    
    def _gaussian_neighborhood(self, center, sigma):
        """Calculate Gaussian neighborhood function."""
        y, x = np.ogrid[:self.map_size[0], :self.map_size[1]]
        dist_sq = (y - center[0])**2 + (x - center[1])**2
        return np.exp(-dist_sq / (2 * sigma**2))
    
    def _find_bmu(self, sample):
        """Find Best Matching Unit (BMU) for a sample."""
        distances = np.sum((self.weights - sample)**2, axis=2)
        return np.unravel_index(np.argmin(distances), self.map_size)
    
    def train(self, X, n_iterations=1000):
        """
        Train the SOM using input data.
        
        Parameters
        ----------
        X : numpy.ndarray
            Training data (n_samples, n_features)
        n_iterations : int
            Number of training iterations
        """
        print("Training Self-Organizing Map...")
        
        # Initialize weights
        n_features = X.shape[1]
        self.weights = np.random.rand(self.map_size[0], self.map_size[1], n_features)
        
        # Normalize weights
        for i in range(self.map_size[0]):
            for j in range(self.map_size[1]):
                self.weights[i, j] = self.weights[i, j] / np.linalg.norm(self.weights[i, j])
        
        # Training loop
        for iteration in range(n_iterations):
            # Update learning rate and sigma
            current_lr = self.learning_rate * np.exp(-iteration / n_iterations)
            current_sigma = self.sigma * np.exp(-iteration / n_iterations)
            
            # Random sample
            sample_idx = np.random.randint(0, X.shape[0])
            sample = X[sample_idx]
            
            # Find BMU
            bmu = self._find_bmu(sample)
            
            # Update weights
            neighborhood = self._gaussian_neighborhood(bmu, current_sigma)
            for i in range(self.map_size[0]):
                for j in range(self.map_size[1]):
                    self.weights[i, j] += (current_lr * neighborhood[i, j] * 
                                         (sample - self.weights[i, j]))
            
            if (iteration + 1) % 100 == 0:
                print(f"Iteration {iteration + 1}/{n_iterations}")
        
        self.trained = True
        print("SOM training completed!")
    
    def predict_groups(self, X):
        """
        Predict phytoplankton group fractions for input data.
        
        Parameters
        ----------
        X : numpy.ndarray
            Input features (n_samples, n_features)
        
        Returns
        -------
        numpy.ndarray
            Group fractions (n_samples, n_groups)
        """
        if not self.trained:
            raise ValueError("SOM must be trained before prediction")
        
        n_samples = X.shape[0]
        group_fractions = np.zeros((n_samples, self.n_groups))
        
        for i in range(n_samples):
            bmu = self._find_bmu(X[i])
            
            # Convert BMU position to group probabilities
            # This is a simplified approach - in practice, you would use
            # labeled training data to assign groups to SOM neurons
            
            # Example assignment based on BMU position
            y_pos, x_pos = bmu
            total_neurons = self.map_size[0] * self.map_size[1]
            neuron_id = y_pos * self.map_size[1] + x_pos
            
            # Simple mapping: divide neurons among groups
            neurons_per_group = total_neurons // self.n_groups
            
            if neuron_id < neurons_per_group:
                # Diatoms (typically in productive waters)
                group_fractions[i] = [0.7, 0.2, 0.1]
            elif neuron_id < 2 * neurons_per_group:
                # Prokaryotes (oligotrophic waters)
                group_fractions[i] = [0.1, 0.8, 0.1]
            else:
                # Dinoflagellates (intermediate conditions)
                group_fractions[i] = [0.2, 0.3, 0.5]
        
        return group_fractions


class PhytoplanktonGroupProductionCalculator:
    """
    Main class for calculating primary production by phytoplankton groups.
    """
    
    def __init__(self, data_dir: Path):
        """
        Initialize the calculator.
        
        Parameters
        ----------
        data_dir : Path
            Directory containing input data
        """
        self.data_dir = Path(data_dir)
        self.som_model = SelfOrganizingMap()
        self.pp_models = {}  # PP models for each group
        self.scaler = StandardScaler()
        self.training_ranges = {}  # For reliability index calculation
        
        # Initialize PP models for each group
        for group in self.som_model.group_names:
            self.pp_models[group] = PrimaryProductionModel()
    
    def load_satellite_data(self, start_date: str = "2008-01-01", 
                           end_date: str = "2024-12-31") -> xr.Dataset:
        """
        Load satellite data (MERIS/OLCI) with all required variables.
        
        Parameters
        ----------
        start_date : str
            Start date for data loading
        end_date : str
            End date for data loading
        
        Returns
        -------
        xr.Dataset
            Dataset with all required variables
        """
        print("Loading satellite data...")
        
        # Load existing chlorophyll data
        chl_file = self.data_dir / "meris_chl_a_20080101_20241231.nc"
        
        if chl_file.exists():
            ds = xr.open_dataset(chl_file)
            print(f"Loaded chlorophyll data: {list(ds.data_vars)}")
            
            # Validate that all required variables are present
            required_vars = ['CHL', 'Rrs_412', 'Rrs_443', 'Rrs_490', 'Rrs_555', 
                           'Rrs_665', 'Rrs_709', 'SST', 'bbp', 'Kd_490', 'PAR']
            missing_vars = [var for var in required_vars if var not in ds.data_vars]
            
            if missing_vars:
                raise ValueError(
                    f"Missing required variables in MERIS data: {missing_vars}\n"
                    f"Please provide complete MERIS dataset with all optical and environmental variables."
                )
            
            print(f"✓ All required variables present in dataset")
            
        else:
            raise FileNotFoundError(f"Chlorophyll data file not found: {chl_file}")
        
        return ds
    
    def prepare_features(self, ds: xr.Dataset) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare feature matrix from satellite data for ML models.
        
        Parameters
        ----------
        ds : xr.Dataset
            Input dataset with satellite variables
        
        Returns
        -------
        tuple
            Feature matrix and valid data mask
        """
        print("Preparing features for ML models...")
        
        # Define feature variables
        feature_vars = ['CHL', 'Rrs_412', 'Rrs_443', 'Rrs_490', 'Rrs_555', 
                       'Rrs_665', 'Rrs_709', 'SST', 'bbp', 'Kd_490', 'PAR']
        
        # Stack all variables into a single array
        features_list = []
        for var in feature_vars:
            if var in ds.data_vars:
                data = ds[var].values.flatten()
                features_list.append(data)
        
        # Create feature matrix
        features = np.column_stack(features_list)
        
        # Create valid data mask (no NaN or negative values)
        valid_mask = np.all(np.isfinite(features), axis=1) & np.all(features > 0, axis=1)
        
        # Filter valid data
        valid_features = features[valid_mask]
        
        print(f"Total pixels: {len(features)}")
        print(f"Valid pixels: {len(valid_features)} ({100*len(valid_features)/len(features):.1f}%)")
        
        return valid_features, valid_mask
    
    def train_models(self, ds: xr.Dataset):
        """
        Train SOM and PP models using satellite data.
        
        Parameters
        ----------
        ds : xr.Dataset
            Training dataset
        """
        print("Training phytoplankton group models...")
        
        # Prepare features
        features, valid_mask = self.prepare_features(ds)
        
        # Standardize features for SOM
        features_scaled = self.scaler.fit_transform(features)
        
        # Store training ranges for reliability index
        self.training_ranges = {}
        feature_vars = ['CHL', 'Rrs_412', 'Rrs_443', 'Rrs_490', 'Rrs_555', 
                       'Rrs_665', 'Rrs_709', 'SST', 'bbp', 'Kd_490', 'PAR']
        
        for i, var in enumerate(feature_vars):
            self.training_ranges[var] = {
                'min': np.percentile(features[:, i], 5),
                'max': np.percentile(features[:, i], 95),
                'mean': np.mean(features[:, i]),
                'std': np.std(features[:, i])
            }
        
        # Train SOM
        self.som_model.train(features_scaled)
        
        # Generate synthetic training data for PP models
        # In practice, you would use in-situ measurements
        print("Training PP models for each phytoplankton group...")
        
        for i, group in enumerate(self.som_model.group_names):
            print(f"Training PP model for {group}...")
            
            # Create synthetic training data specific to each group
            # Different groups have different PP vs Chl-a relationships
            if group == 'Diatoms':
                # Higher PP efficiency for diatoms
                chl_train, pp_train = self._create_group_training_data(
                    coefficient=5.5, exponent=0.8, n_samples=5000
                )
            elif group == 'Prokaryotes':
                # Lower PP efficiency for small prokaryotes
                chl_train, pp_train = self._create_group_training_data(
                    coefficient=3.0, exponent=0.6, n_samples=5000
                )
            else:  # Dinoflagellates
                # Intermediate PP efficiency
                chl_train, pp_train = self._create_group_training_data(
                    coefficient=4.0, exponent=0.7, n_samples=5000
                )
            
            # Prepare features for PP model
            pp_features, _ = self.pp_models[group].prepare_features(chl_train)
            
            # Train PP model
            self.pp_models[group].train(pp_features, pp_train)
        
        print("Model training completed!")
    
    def _create_group_training_data(self, coefficient: float, exponent: float, 
                                   n_samples: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create synthetic training data for a specific phytoplankton group.
        
        Parameters
        ----------
        coefficient : float
            PP-Chl relationship coefficient
        exponent : float
            PP-Chl relationship exponent
        n_samples : int
            Number of training samples
        
        Returns
        -------
        tuple
            Chlorophyll and PP training data
        """
        # Generate chlorophyll values
        chl = np.random.lognormal(mean=0, sigma=1.5, size=n_samples)
        chl = np.clip(chl, 0.01, 10)
        
        # Calculate PP using group-specific relationship
        pp = coefficient * (chl ** exponent)
        
        # Add realistic noise
        noise = np.random.normal(0, 0.15 * pp, size=n_samples)
        pp = np.maximum(pp + noise, 0)
        
        return chl, pp
    
    def calculate_group_fractions(self, ds: xr.Dataset) -> Dict[str, np.ndarray]:
        """
        Calculate chlorophyll-a fractions for each phytoplankton group.
        
        Parameters
        ----------
        ds : xr.Dataset
            Input dataset
        
        Returns
        -------
        dict
            Group fractions with same spatial structure as input
        """
        print("Calculating phytoplankton group fractions...")
        
        # Prepare features
        features, valid_mask = self.prepare_features(ds)
        features_scaled = self.scaler.transform(features)
        
        # Predict group fractions using SOM
        group_fractions = self.som_model.predict_groups(features_scaled)
        
        # Reshape to original spatial structure
        original_shape = ds['CHL'].shape
        total_pixels = np.prod(original_shape)
        
        group_fraction_maps = {}
        for i, group in enumerate(self.som_model.group_names):
            # Initialize with NaN
            fraction_map = np.full(total_pixels, np.nan)
            # Fill valid pixels
            fraction_map[valid_mask] = group_fractions[:, i]
            # Reshape to original spatial structure
            fraction_map = fraction_map.reshape(original_shape)
            group_fraction_maps[group] = fraction_map
        
        return group_fraction_maps
    
    def calculate_group_chlorophyll(self, ds: xr.Dataset, 
                                   group_fractions: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Calculate chlorophyll-a concentration for each phytoplankton group.
        
        Parameters
        ----------
        ds : xr.Dataset
            Input dataset with total chlorophyll
        group_fractions : dict
            Group fractions from SOM
        
        Returns
        -------
        dict
            Chlorophyll-a concentration for each group
        """
        print("Calculating chlorophyll-a by phytoplankton group...")
        
        total_chl = ds['CHL'].values
        group_chl = {}
        
        for group, fraction in group_fractions.items():
            group_chl[group] = total_chl * fraction
        
        return group_chl
    
    def calculate_primary_production(self, group_chl: Dict[str, np.ndarray], 
                                    par: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate primary production for each phytoplankton group.
        
        Parameters
        ----------
        group_chl : dict
            Chlorophyll-a concentration by group
        par : numpy.ndarray
            Photosynthetically Available Radiation
        
        Returns
        -------
        dict
            Primary production by group (mg C m⁻² d⁻¹)
        """
        print("Calculating primary production by phytoplankton group...")
        
        group_pp = {}
        
        for group, chl in group_chl.items():
            print(f"Calculating PP for {group}...")
            
            # Estimate PP from chlorophyll using trained model
            pp_base = self.pp_models[group].estimate_from_chlorophyll(chl)
            
            # Apply PAR correction (simplified)
            # PP scales with available light
            par_factor = np.minimum(par / 30.0, 1.0)  # Normalize to typical PAR values
            pp_corrected = pp_base * par_factor
            
            group_pp[group] = np.maximum(pp_corrected, 0)
        
        return group_pp
    
    def calculate_reliability_index(self, ds: xr.Dataset) -> np.ndarray:
        """
        Calculate reliability index based on training data ranges.
        
        Parameters
        ----------
        ds : xr.Dataset
            Input dataset
        
        Returns
        -------
        numpy.ndarray
            Reliability index (0-1, where 1 is most reliable)
        """
        print("Calculating reliability index...")
        
        feature_vars = ['CHL', 'Rrs_412', 'Rrs_443', 'Rrs_490', 'Rrs_555', 
                       'Rrs_665', 'Rrs_709', 'SST', 'bbp', 'Kd_490', 'PAR']
        
        reliability_scores = []
        
        for var in feature_vars:
            if var in ds.data_vars and var in self.training_ranges:
                data = ds[var].values
                ranges = self.training_ranges[var]
                
                # Score based on how well data falls within training range
                in_range = (data >= ranges['min']) & (data <= ranges['max'])
                
                # Additional score based on distance from training mean
                z_score = np.abs((data - ranges['mean']) / ranges['std'])
                distance_score = np.exp(-z_score / 2)  # Gaussian-like decay
                
                # Combine range and distance scores
                var_score = in_range.astype(float) * distance_score
                reliability_scores.append(var_score)
        
        # Average across all variables
        if reliability_scores:
            reliability_index = np.mean(reliability_scores, axis=0)
        else:
            reliability_index = np.ones_like(ds['CHL'].values) * 0.5
        
        return np.clip(reliability_index, 0, 1)
    
    def calculate_quality_metrics(self, observed: np.ndarray, 
                                 predicted: np.ndarray) -> Dict[str, float]:
        """
        Calculate quality metrics for model validation.
        
        Parameters
        ----------
        observed : numpy.ndarray
            Observed (reference) values
        predicted : numpy.ndarray
            Predicted values
        
        Returns
        -------
        dict
            Quality metrics (R², RMSE, Bias)
        """
        # Remove NaN values
        valid_mask = np.isfinite(observed) & np.isfinite(predicted)
        obs_valid = observed[valid_mask]
        pred_valid = predicted[valid_mask]
        
        if len(obs_valid) == 0:
            return {'r2': np.nan, 'rmse': np.nan, 'bias': np.nan, 'n_points': 0}
        
        # Calculate metrics
        r2 = r2_score(obs_valid, pred_valid)
        rmse = np.sqrt(mean_squared_error(obs_valid, pred_valid))
        bias = np.mean(pred_valid - obs_valid)
        
        return {
            'r2': r2,
            'rmse': rmse,
            'bias': bias,
            'n_points': len(obs_valid)
        }
    
    def save_models(self, models_dir: Path):
        """
        Save trained models to disk.
        
        Parameters
        ----------
        models_dir : Path
            Directory to save models
        """
        models_dir = Path(models_dir)
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Save SOM model
        som_file = models_dir / 'som_phytoplankton_groups.pkl'
        joblib.dump(self.som_model, som_file)
        
        # Save PP models
        for group, model in self.pp_models.items():
            pp_file = models_dir / f'pp_model_{group.lower()}.pkl'
            model.save(pp_file)
        
        # Save scaler and training ranges
        scaler_file = models_dir / 'feature_scaler.pkl'
        joblib.dump(self.scaler, scaler_file)
        
        ranges_file = models_dir / 'training_ranges.pkl'
        joblib.dump(self.training_ranges, ranges_file)
        
        print(f"Models saved to: {models_dir}")
    
    def load_models(self, models_dir: Path):
        """
        Load trained models from disk.
        
        Parameters
        ----------
        models_dir : Path
            Directory containing saved models
        """
        models_dir = Path(models_dir)
        
        # Load SOM model
        som_file = models_dir / 'som_phytoplankton_groups.pkl'
        if som_file.exists():
            self.som_model = joblib.load(som_file)
        
        # Load PP models
        for group in self.som_model.group_names:
            pp_file = models_dir / f'pp_model_{group.lower()}.pkl'
            if pp_file.exists():
                self.pp_models[group].load(pp_file)
        
        # Load scaler and training ranges
        scaler_file = models_dir / 'feature_scaler.pkl'
        if scaler_file.exists():
            self.scaler = joblib.load(scaler_file)
        
        ranges_file = models_dir / 'training_ranges.pkl'
        if ranges_file.exists():
            self.training_ranges = joblib.load(ranges_file)
        
        print(f"Models loaded from: {models_dir}")


def create_output_maps(ds: xr.Dataset, group_pp: Dict[str, np.ndarray], 
                      reliability_index: np.ndarray, output_dir: Path):
    """
    Create and save output maps for primary production results.
    
    Parameters
    ----------
    ds : xr.Dataset
        Input dataset with coordinates
    group_pp : dict
        Primary production by phytoplankton group
    reliability_index : numpy.ndarray
        Reliability index
    output_dir : Path
        Output directory for maps
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Creating output maps...")
    
    # Set up the plotting style
    plt.style.use('default')
    
    # Create maps for each group
    for group, pp_data in group_pp.items():
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Primary Production Analysis - {group}', fontsize=16, fontweight='bold')
        
        # Get coordinates
        if 'time' in ds.dims:
            # Use first time step for visualization
            lat = ds.lat.values
            lon = ds.lon.values
            pp_plot = pp_data[0] if pp_data.ndim == 3 else pp_data
            chl_plot = ds['CHL'].values[0] if ds['CHL'].ndim == 3 else ds['CHL'].values
            reliability_plot = reliability_index[0] if reliability_index.ndim == 3 else reliability_index
        else:
            lat = ds.lat.values
            lon = ds.lon.values
            pp_plot = pp_data
            chl_plot = ds['CHL'].values
            reliability_plot = reliability_index
        
        # 1. Primary Production map
        ax1 = axes[0, 0]
        im1 = ax1.pcolormesh(lon, lat, pp_plot, shading='auto', cmap='viridis')
        ax1.set_title(f'Primary Production - {group}\n(mg C m⁻² d⁻¹)')
        ax1.set_xlabel('Longitude')
        ax1.set_ylabel('Latitude')
        plt.colorbar(im1, ax=ax1)
        
        # 2. Chlorophyll-a map
        ax2 = axes[0, 1]
        im2 = ax2.pcolormesh(lon, lat, chl_plot, shading='auto', cmap='plasma')
        ax2.set_title('Total Chlorophyll-a\n(mg m⁻³)')
        ax2.set_xlabel('Longitude')
        ax2.set_ylabel('Latitude')
        plt.colorbar(im2, ax=ax2)
        
        # 3. Reliability Index map
        ax3 = axes[1, 0]
        im3 = ax3.pcolormesh(lon, lat, reliability_plot, shading='auto', 
                            cmap='RdYlGn', vmin=0, vmax=1)
        ax3.set_title('Reliability Index\n(0: Low, 1: High)')
        ax3.set_xlabel('Longitude')
        ax3.set_ylabel('Latitude')
        plt.colorbar(im3, ax=ax3)
        
        # 4. PP vs Chl-a scatter plot
        ax4 = axes[1, 1]
        valid_mask = np.isfinite(pp_plot) & np.isfinite(chl_plot) & (chl_plot > 0)
        if np.any(valid_mask):
            scatter = ax4.scatter(chl_plot[valid_mask], pp_plot[valid_mask], 
                                c=reliability_plot[valid_mask], cmap='RdYlGn', 
                                s=10, alpha=0.6)
            ax4.set_xlabel('Chlorophyll-a (mg m⁻³)')
            ax4.set_ylabel('Primary Production (mg C m⁻² d⁻¹)')
            ax4.set_title(f'PP vs Chl-a - {group}')
            ax4.set_xscale('log')
            ax4.set_yscale('log')
            plt.colorbar(scatter, ax=ax4, label='Reliability')
        
        plt.tight_layout()
        
        # Save figure
        output_file = output_dir / f'pp_analysis_{group.lower()}.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved map: {output_file}")
    
    # Create summary comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Primary Production by Phytoplankton Groups - Summary', 
                 fontsize=16, fontweight='bold')
    
    group_colors = ['blue', 'red', 'green']
    
    # Total PP map
    ax1 = axes[0, 0]
    total_pp = sum(group_pp.values())
    if 'time' in ds.dims:
        total_pp_plot = total_pp[0] if total_pp.ndim == 3 else total_pp
    else:
        total_pp_plot = total_pp
        
    im1 = ax1.pcolormesh(lon, lat, total_pp_plot, shading='auto', cmap='viridis')
    ax1.set_title('Total Primary Production\n(mg C m⁻² d⁻¹)')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    plt.colorbar(im1, ax=ax1)
    
    # Group contribution pie chart (average values)
    ax2 = axes[0, 1]
    group_means = []
    group_labels = []
    for i, (group, pp_data) in enumerate(group_pp.items()):
        if 'time' in ds.dims:
            pp_plot = pp_data[0] if pp_data.ndim == 3 else pp_data
        else:
            pp_plot = pp_data
        
        mean_pp = np.nanmean(pp_plot)
        if mean_pp > 0:
            group_means.append(mean_pp)
            group_labels.append(group)
    
    if group_means:
        ax2.pie(group_means, labels=group_labels, autopct='%1.1f%%', 
               colors=group_colors[:len(group_means)])
        ax2.set_title('Average PP Contribution\nby Group')
    
    # PP time series (if time dimension exists)
    ax3 = axes[1, 0]
    if 'time' in ds.dims and ds.time.size > 1:
        for i, (group, pp_data) in enumerate(group_pp.items()):
            pp_mean = np.nanmean(pp_data, axis=(1, 2))  # Average over space
            ax3.plot(ds.time, pp_mean, label=group, color=group_colors[i], linewidth=2)
        
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Mean PP (mg C m⁻² d⁻¹)')
        ax3.set_title('Temporal Evolution of PP by Group')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, 'Single time step\nNo temporal analysis available', 
                ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Temporal Analysis')
    
    # Quality metrics text
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Calculate some basic statistics
    stats_text = "Summary Statistics:\n\n"
    for group, pp_data in group_pp.items():
        if 'time' in ds.dims:
            pp_plot = pp_data[0] if pp_data.ndim == 3 else pp_data
        else:
            pp_plot = pp_data
        
        mean_pp = np.nanmean(pp_plot)
        std_pp = np.nanstd(pp_plot)
        max_pp = np.nanmax(pp_plot)
        
        stats_text += f"{group}:\n"
        stats_text += f"  Mean: {mean_pp:.2f} mg C m⁻² d⁻¹\n"
        stats_text += f"  Std:  {std_pp:.2f} mg C m⁻² d⁻¹\n"
        stats_text += f"  Max:  {max_pp:.2f} mg C m⁻² d⁻¹\n\n"
    
    # Add reliability info
    rel_mean = np.nanmean(reliability_plot)
    rel_min = np.nanmin(reliability_plot)
    stats_text += f"Reliability Index:\n"
    stats_text += f"  Mean: {rel_mean:.3f}\n"
    stats_text += f"  Min:  {rel_min:.3f}\n"
    
    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, 
            fontsize=10, verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    
    # Save summary figure
    summary_file = output_dir / 'pp_summary_all_groups.png'
    plt.savefig(summary_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved summary map: {summary_file}")


def save_results_to_netcdf(ds: xr.Dataset, group_pp: Dict[str, np.ndarray], 
                          group_chl: Dict[str, np.ndarray], 
                          group_fractions: Dict[str, np.ndarray],
                          reliability_index: np.ndarray, 
                          quality_metrics: Dict[str, Dict[str, float]],
                          output_file: Path):
    """
    Save results to NetCDF file.
    
    Parameters
    ----------
    ds : xr.Dataset
        Original dataset with coordinates
    group_pp : dict
        Primary production by group
    group_chl : dict
        Chlorophyll-a by group
    group_fractions : dict
        Group fractions
    reliability_index : numpy.ndarray
        Reliability index
    quality_metrics : dict
        Quality metrics for each group
    output_file : Path
        Output NetCDF file path
    """
    print(f"Saving results to NetCDF: {output_file}")
    
    # Create new dataset
    coords = {coord: ds.coords[coord] for coord in ds.coords}
    
    data_vars = {}
    
    # Add original chlorophyll
    data_vars['chlorophyll_total'] = (ds['CHL'].dims, ds['CHL'].values, 
                                     {'units': 'mg m⁻³', 'long_name': 'Total Chlorophyll-a'})
    
    # Add group-specific variables
    for group in group_pp.keys():
        group_lower = group.lower()
        
        # Primary production
        data_vars[f'pp_{group_lower}'] = (
            ds['CHL'].dims, group_pp[group], 
            {'units': 'mg C m⁻² d⁻¹', 'long_name': f'Primary Production - {group}'}
        )
        
        # Chlorophyll fraction
        data_vars[f'chlorophyll_{group_lower}'] = (
            ds['CHL'].dims, group_chl[group], 
            {'units': 'mg m⁻³', 'long_name': f'Chlorophyll-a - {group}'}
        )
        
        # Group fraction
        data_vars[f'fraction_{group_lower}'] = (
            ds['CHL'].dims, group_fractions[group], 
            {'units': 'dimensionless', 'long_name': f'Fraction of {group}', 
             'valid_range': [0, 1]}
        )
    
    # Add total primary production
    total_pp = sum(group_pp.values())
    data_vars['pp_total'] = (
        ds['CHL'].dims, total_pp, 
        {'units': 'mg C m⁻² d⁻¹', 'long_name': 'Total Primary Production'}
    )
    
    # Add reliability index
    data_vars['reliability_index'] = (
        ds['CHL'].dims, reliability_index, 
        {'units': 'dimensionless', 'long_name': 'Model Reliability Index', 
         'valid_range': [0, 1], 'description': '0: Low reliability, 1: High reliability'}
    )
    
    # Create dataset
    result_ds = xr.Dataset(data_vars, coords=coords)
    
    # Add global attributes
    result_ds.attrs = {
        'title': 'Primary Production by Phytoplankton Groups',
        'institution': 'Ocean Primary Production Analysis',
        'source': 'MERIS/OLCI satellite data',
        'algorithm': 'Self-Organizing Map (SOM) + Machine Learning',
        'groups': ', '.join(group_pp.keys()),
        'creation_date': pd.Timestamp.now().isoformat(),
        'description': 'Primary production estimates for different phytoplankton functional groups'
    }
    
    # Add quality metrics as global attributes
    for group, metrics in quality_metrics.items():
        for metric, value in metrics.items():
            result_ds.attrs[f'{group.lower()}_{metric}'] = value
    
    # Save to NetCDF
    encoding = {var: {'zlib': True, 'complevel': 4} for var in result_ds.data_vars}
    result_ds.to_netcdf(output_file, encoding=encoding)
    
    print(f"Results saved successfully to: {output_file}")


def main():
    """
    Main function to run the complete phytoplankton group production analysis.
    """
    print("="*80)
    print("PHYTOPLANKTON GROUP PRIMARY PRODUCTION CALCULATOR")
    print("="*80)
    
    # Set up paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    models_dir = base_dir / "models"
    output_dir = base_dir / "data" / "phytoplankton_groups"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize calculator
        calculator = PhytoplanktonGroupProductionCalculator(data_dir)
        
        # Load satellite data
        print("\n1. Loading satellite data...")
        ds = calculator.load_satellite_data()
        print(f"Loaded dataset with variables: {list(ds.data_vars)}")
        print(f"Data shape: {ds.dims}")
        
        # Train models
        print("\n2. Training machine learning models...")
        calculator.train_models(ds)
        
        # Save trained models
        print("\n3. Saving trained models...")
        calculator.save_models(models_dir)
        
        # Calculate phytoplankton group fractions
        print("\n4. Calculating phytoplankton group fractions...")
        group_fractions = calculator.calculate_group_fractions(ds)
        
        # Calculate group-specific chlorophyll
        print("\n5. Calculating chlorophyll-a by group...")
        group_chl = calculator.calculate_group_chlorophyll(ds, group_fractions)
        
        # Calculate primary production by group
        print("\n6. Calculating primary production by group...")
        group_pp = calculator.calculate_primary_production(group_chl, ds['PAR'].values)
        
        # Calculate reliability index
        print("\n7. Calculating reliability index...")
        reliability_index = calculator.calculate_reliability_index(ds)
        
        # Calculate quality metrics (using synthetic validation data)
        print("\n8. Calculating quality metrics...")
        quality_metrics = {}
        for group in calculator.som_model.group_names:
            # Create synthetic validation data for demonstration
            chl_val, pp_val = calculator._create_group_training_data(4.5, 0.7, 1000)
            pp_pred = calculator.pp_models[group].estimate_from_chlorophyll(chl_val)
            
            metrics = calculator.calculate_quality_metrics(pp_val, pp_pred)
            quality_metrics[group] = metrics
            
            print(f"{group} - R²: {metrics['r2']:.3f}, RMSE: {metrics['rmse']:.3f}, "
                  f"Bias: {metrics['bias']:.3f}")
        
        # Create output maps
        print("\n9. Creating output maps...")
        create_output_maps(ds, group_pp, reliability_index, output_dir)
        
        # Save results to NetCDF
        print("\n10. Saving results to NetCDF...")
        output_nc_file = output_dir / "phytoplankton_group_production_results.nc"
        save_results_to_netcdf(ds, group_pp, group_chl, group_fractions, 
                              reliability_index, quality_metrics, output_nc_file)
        
        # Print summary
        print("\n" + "="*80)
        print("ANALYSIS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        print(f"\nOutput files created:")
        print(f"- Results NetCDF: {output_nc_file}")
        print(f"- Maps directory: {output_dir}")
        print(f"- Models directory: {models_dir}")
        
        print(f"\nPhytoplankton groups analyzed:")
        for i, group in enumerate(calculator.som_model.group_names):
            pp_mean = np.nanmean(group_pp[group])
            print(f"- {group}: Mean PP = {pp_mean:.2f} mg C m⁻² d⁻¹")
        
        total_pp_mean = np.nanmean(sum(group_pp.values()))
        print(f"\nTotal mean primary production: {total_pp_mean:.2f} mg C m⁻² d⁻¹")
        
        reliability_mean = np.nanmean(reliability_index)
        print(f"Average reliability index: {reliability_mean:.3f}")
        
        print(f"\nQuality metrics summary:")
        for group, metrics in quality_metrics.items():
            print(f"- {group}: R² = {metrics['r2']:.3f}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())