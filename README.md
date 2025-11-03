# Ocean Primary Production Estimation

This project provides tools to download MERIS satellite data from Copernicus Marine Service and estimate ocean primary production using machine learning (Random Forest) models.

## Project Structure

```
ocean_primary_production/
├── data/                    # Data directory (not tracked in git)
├── models/                  # Trained models directory (not tracked in git)
├── scripts/                 # Main scripts directory
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   └── data_processing.py
│   ├── functions/          # Core functionality
│   │   ├── __init__.py
│   │   └── primary_production_model.py
│   ├── download_meris_data.py
│   └── estimate_primary_production.py
├── example_workflow.py      # Example demonstrating the workflow
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rcavieses/ocean_primary_production.git
cd ocean_primary_production
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Copernicus Marine credentials:
```bash
copernicusmarine login
```
You'll need to create a free account at [Copernicus Marine Service](https://marine.copernicus.eu/).

## Quick Start

Run the example workflow to see the system in action:
```bash
python example_workflow.py
```

This demonstrates:
- Training a Random Forest model with synthetic data
- Making predictions from chlorophyll concentrations
- Complete workflow instructions

## Usage

### 1. Download MERIS Chlorophyll-a Data

Download 8-day mean sea surface chlorophyll-a concentration data from Copernicus:

```bash
python scripts/download_meris_data.py \
    --start-date 2010-01-01 \
    --end-date 2010-12-31 \
    --lon-min -180 --lon-max 180 \
    --lat-min -90 --lat-max 90 \
    --output-dir data/
```

Options:
- `--start-date`: Start date (YYYY-MM-DD) - required
- `--end-date`: End date (YYYY-MM-DD) - required
- `--lon-min`, `--lon-max`: Longitude range (default: -180 to 180)
- `--lat-min`, `--lat-max`: Latitude range (default: -90 to 90)
- `--output-dir`: Output directory (default: data/)

### 2. Estimate Primary Production

Estimate ocean primary production from chlorophyll data using Random Forest:

```bash
# Train a new model and apply to data
python scripts/estimate_primary_production.py \
    --input-file data/meris_chl_a_20100101_20101231.nc \
    --output-file data/primary_production_2010.nc \
    --train-model \
    --model-file models/pp_model.pkl

# Use a pre-trained model
python scripts/estimate_primary_production.py \
    --input-file data/meris_chl_a_20100101_20101231.nc \
    --output-file data/primary_production_2010.nc \
    --model-file models/pp_model.pkl
```

Options:
- `--input-file`: Path to input NetCDF file with chlorophyll data - required
- `--output-file`: Path to output NetCDF file
- `--model-file`: Path to model file (for loading or saving)
- `--train-model`: Train a new model with synthetic data
- `--chl-var`: Name of chlorophyll variable (default: CHL)

## Data Sources

- **MERIS Data**: Ocean Colour Climate Change Initiative (OC-CCI) data from Copernicus Marine Service
- **Product ID**: OCEANCOLOUR_GLO_BGC_L4_MY_009_104
- **Variable**: Chlorophyll-a concentration (CHL)
- **Resolution**: 4km (monthly aggregated product)
- **Temporal Coverage**: Historical archive

## Methodology

The primary production estimation uses a Random Forest regression model that learns the relationship between chlorophyll-a concentration and primary production. The model is trained on synthetic data based on empirical relationships from oceanographic studies.

### Features Used
1. Chlorophyll-a concentration (mg/m³)
2. Log-transformed chlorophyll
3. Squared chlorophyll
4. Square root chlorophyll

### Model Output
- Primary production in mg C/m²/day
- Spatial maps matching input chlorophyll data

## References

- [Mapping Sea Surface Chlorophyll in Python](https://medium.com/geospatial-analytics/mapping-sea-surface-chlorophyll-in-python-35bf1e8a7eeb)
- [Copernicus Marine Service](https://marine.copernicus.eu/)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
