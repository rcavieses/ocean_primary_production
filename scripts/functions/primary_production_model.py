"""
Primary production estimation models using machine learning.
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from pathlib import Path


class PrimaryProductionModel:
    """
    Random Forest model for estimating primary production from chlorophyll-a data.
    
    Based on empirical relationships between chlorophyll-a concentration and
    primary production in marine ecosystems.
    """
    
    def __init__(self, n_estimators=100, random_state=42):
        """
        Initialize the Random Forest model.
        
        Parameters
        ----------
        n_estimators : int, optional
            Number of trees in the forest
        random_state : int, optional
            Random state for reproducibility
        """
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            n_jobs=-1
        )
        self.is_fitted = False
    
    def prepare_features(self, chlorophyll_data):
        """
        Prepare features from chlorophyll data.
        
        Parameters
        ----------
        chlorophyll_data : numpy.ndarray
            Chlorophyll-a concentration values (mg/m³)
        
        Returns
        -------
        numpy.ndarray
            Feature matrix
        """
        # Remove invalid values
        valid_mask = (chlorophyll_data > 0) & ~np.isnan(chlorophyll_data)
        valid_chl = chlorophyll_data[valid_mask]
        
        # Create features
        features = np.column_stack([
            valid_chl,                    # Original chlorophyll value
            np.log10(valid_chl),          # Log-transformed chlorophyll
            valid_chl ** 2,               # Squared chlorophyll
            np.sqrt(valid_chl)            # Square root chlorophyll
        ])
        
        return features, valid_mask
    
    def train(self, X_train, y_train, validation_split=0.2):
        """
        Train the Random Forest model.
        
        Parameters
        ----------
        X_train : numpy.ndarray
            Training features
        y_train : numpy.ndarray
            Training target (primary production values)
        validation_split : float, optional
            Fraction of data to use for validation
        
        Returns
        -------
        dict
            Training metrics
        """
        # Split data for validation
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_train, y_train,
            test_size=validation_split,
            random_state=42
        )
        
        # Train the model
        print("Training Random Forest model...")
        self.model.fit(X_tr, y_tr)
        self.is_fitted = True
        
        # Evaluate on validation set
        y_pred = self.model.predict(X_val)
        
        metrics = {
            'mse': mean_squared_error(y_val, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_val, y_pred)),
            'r2': r2_score(y_val, y_pred)
        }
        
        print(f"Validation RMSE: {metrics['rmse']:.4f}")
        print(f"Validation R²: {metrics['r2']:.4f}")
        
        return metrics
    
    def predict(self, X):
        """
        Predict primary production from features.
        
        Parameters
        ----------
        X : numpy.ndarray
            Feature matrix
        
        Returns
        -------
        numpy.ndarray
            Predicted primary production values
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before prediction")
        
        return self.model.predict(X)
    
    def estimate_from_chlorophyll(self, chlorophyll_data):
        """
        Estimate primary production directly from chlorophyll data.
        
        Parameters
        ----------
        chlorophyll_data : numpy.ndarray
            Chlorophyll-a concentration values (mg/m³)
        
        Returns
        -------
        numpy.ndarray
            Estimated primary production with same shape as input
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before prediction")
        
        original_shape = chlorophyll_data.shape
        flat_data = chlorophyll_data.flatten()
        
        # Prepare features
        features, valid_mask = self.prepare_features(flat_data)
        
        # Initialize output with NaN
        output = np.full(len(flat_data), np.nan)
        
        # Predict for valid values
        if len(features) > 0:
            predictions = self.predict(features)
            output[valid_mask] = predictions
        
        return output.reshape(original_shape)
    
    def save(self, filepath):
        """
        Save the trained model to disk.
        
        Parameters
        ----------
        filepath : str or Path
            Path to save the model
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, filepath)
        print(f"Model saved to: {filepath}")
    
    def load(self, filepath):
        """
        Load a trained model from disk.
        
        Parameters
        ----------
        filepath : str or Path
            Path to the saved model
        """
        self.model = joblib.load(filepath)
        self.is_fitted = True
        print(f"Model loaded from: {filepath}")


def create_synthetic_training_data(n_samples=10000, empirical_coefficient=4.5, 
                                   empirical_exponent=0.7, noise_level=0.1):
    """
    Create synthetic training data based on empirical relationships.
    
    This is a placeholder function. In practice, you would use real
    measured data from oceanographic studies.
    
    Parameters
    ----------
    n_samples : int, optional
        Number of samples to generate
    empirical_coefficient : float, optional
        Coefficient 'a' in the relationship PP = a * Chl^b (default: 4.5)
    empirical_exponent : float, optional
        Exponent 'b' in the relationship PP = a * Chl^b (default: 0.7)
    noise_level : float, optional
        Relative noise level as fraction of primary production (default: 0.1)
    
    Returns
    -------
    numpy.ndarray, numpy.ndarray
        Chlorophyll concentrations and corresponding primary production values
    """
    # Generate chlorophyll values (mg/m³)
    # Typical range: 0.01 to 10 mg/m³
    chlorophyll = np.random.lognormal(mean=0, sigma=1.5, size=n_samples)
    chlorophyll = np.clip(chlorophyll, 0.01, 10)
    
    # Estimate primary production using empirical relationship
    # Based on relationship: PP ≈ a * Chl^b
    # Where PP is in mg C/m²/day and Chl is in mg/m³
    primary_production = empirical_coefficient * (chlorophyll ** empirical_exponent)
    
    # Add noise
    noise = np.random.normal(0, noise_level * primary_production, size=n_samples)
    primary_production += noise
    primary_production = np.maximum(primary_production, 0)
    
    return chlorophyll, primary_production
