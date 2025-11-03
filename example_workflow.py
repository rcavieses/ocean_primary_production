"""
Example workflow demonstrating how to use the ocean primary production tools.

This script shows:
1. How to download MERIS chlorophyll data
2. How to train a Random Forest model
3. How to estimate primary production from the data

Note: This is a demonstration script. Actual data download requires
      Copernicus Marine credentials.
"""
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from functions.primary_production_model import (
    PrimaryProductionModel,
    create_synthetic_training_data
)


def example_workflow():
    """Demonstrate the complete workflow."""
    
    print("=" * 70)
    print("Ocean Primary Production Estimation - Example Workflow")
    print("=" * 70)
    
    # Step 1: Demonstrate model training with synthetic data
    print("\n" + "=" * 70)
    print("Step 1: Train Random Forest Model")
    print("=" * 70)
    
    print("\nGenerating synthetic training data...")
    chl_train, pp_train = create_synthetic_training_data(n_samples=5000)
    print(f"Generated {len(chl_train)} training samples")
    print(f"Chlorophyll range: {chl_train.min():.3f} - {chl_train.max():.3f} mg/m³")
    print(f"Primary production range: {pp_train.min():.2f} - {pp_train.max():.2f} mg C/m²/day")
    
    # Initialize and train model
    print("\nInitializing Random Forest model...")
    model = PrimaryProductionModel(n_estimators=50, random_state=42)
    
    print("Preparing features...")
    X_train, _ = model.prepare_features(chl_train)
    print(f"Feature matrix shape: {X_train.shape}")
    
    print("\nTraining model...")
    metrics = model.train(X_train, pp_train, validation_split=0.2)
    
    print("\nModel Performance:")
    print(f"  RMSE: {metrics['rmse']:.4f}")
    print(f"  R² Score: {metrics['r2']:.4f}")
    
    # Step 2: Demonstrate prediction
    print("\n" + "=" * 70)
    print("Step 2: Predict Primary Production")
    print("=" * 70)
    
    # Create test data
    import numpy as np
    print("\nCreating test chlorophyll data...")
    test_chl = np.array([0.1, 0.5, 1.0, 2.0, 5.0])
    
    print("Estimating primary production...")
    test_pp = model.estimate_from_chlorophyll(test_chl)
    
    print("\nResults:")
    print(f"{'Chlorophyll (mg/m³)':<25} {'Primary Production (mg C/m²/day)':<35}")
    print("-" * 60)
    for chl, pp in zip(test_chl, test_pp):
        print(f"{chl:<25.2f} {pp:<35.2f}")
    
    # Step 3: Show how to use with real data
    print("\n" + "=" * 70)
    print("Step 3: Working with Real MERIS Data")
    print("=" * 70)
    
    print("\nTo download real MERIS data:")
    print("  1. Configure Copernicus credentials: copernicusmarine login")
    print("  2. Run download script:")
    print("     python scripts/download_meris_data.py \\")
    print("         --start-date 2010-01-01 \\")
    print("         --end-date 2010-12-31 \\")
    print("         --lon-min -180 --lon-max 180 \\")
    print("         --lat-min -90 --lat-max 90")
    
    print("\nTo estimate primary production from downloaded data:")
    print("  python scripts/estimate_primary_production.py \\")
    print("      --input-file data/meris_chl_a_20100101_20101231.nc \\")
    print("      --output-file data/primary_production_2010.nc \\")
    print("      --train-model \\")
    print("      --model-file models/pp_model.pkl")
    
    print("\n" + "=" * 70)
    print("Example workflow completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        example_workflow()
    except ImportError as e:
        print(f"\nError: Missing required packages.")
        print(f"Details: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
