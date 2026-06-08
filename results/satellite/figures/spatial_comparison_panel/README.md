# Satellite vs In Situ Spatial Comparison Panels
## Publication-Quality Scientific Figures

**Gulf of California (Golfo de California), 2000-2016**  
**Ocean Primary Production Analysis**

---

## Overview

This directory contains publication-quality comparison panels illustrating the relationship between satellite-derived phytoplankton functional type (PFT) concentrations and in situ eDNA observations across the Gulf of California. Each panel represents a different phytoplankton functional group with a comprehensive multi-faceted analysis.

---

## Figure Description

Each comparison panel consists of **6 subplots** organized in a 2×3 grid (dimensions: 18" × 10", 300 dpi):

### **Panel Layout**

#### **Top Row (Row 0):**

1. **Temporal Time Series (Top-Left, spanning 2 columns)**
   - **Primary axis (left):** Satellite-derived concentration (mg m⁻³) plotted as line with markers
   - **Secondary axis (right):** In situ record frequency (monthly count) displayed as stacked bars
   - **Color coding:** Satellite = specific phylum color; In Situ = corresponding contrasting color
   - **Purpose:** Shows temporal co-variation between satellite and in situ observations
   - **Resolution:** Monthly data from 2000-2016 (204 months)

2. **Sampling Location Map (Top-Right)**
   - **Scatter plot:** Geographic coordinates of all in situ samples
   - **Color scale:** Year of sampling (2000-2016 gradient using 'plasma' colormap)
   - **Axes:** Longitude (°E) vs Latitude (°N)
   - **Purpose:** Visualizes spatial distribution and temporal sampling coverage in the Gulf

#### **Bottom Row (Row 1):**

3. **Correlation Scatter Plot (Bottom-Left)**
   - **X-axis:** Satellite mean concentration (mg m⁻³) - monthly aggregates
   - **Y-axis:** In situ record frequency (number of observations per month)
   - **Markers:** 100-sized circles with species-specific color and black edge
   - **Regression line:** Red dashed line showing linear relationship (if significant)
   - **Statistics box:** Displays correlation coefficient (r), p-value, and R²
   - **Purpose:** Quantifies the relationship strength between satellite and in situ data

4. **Residual Analysis Plot (Bottom-Middle)**
   - **X-axis:** Predicted in situ values (from linear regression model)
   - **Y-axis:** Residuals (observed - predicted)
   - **Reference line:** Red dashed horizontal line at y=0
   - **Markers:** 80-sized circles with black edges
   - **Purpose:** Assesses model fit quality and identifies systematic deviations

5. **Statistical Summary Box (Bottom-Right)**
   - **Sample size:** Number of monthly comparison points (n)
   - **Satellite statistics:** Mean concentration ± standard deviation (mg m⁻³)
   - **In Situ statistics:** Mean frequency ± standard deviation (records/month)
   - **Correlation metrics:** Pearson r, Spearman ρ, p-values
   - **Regression parameters:** Slope, R², intercept
   - **Error metrics:** RMSE, MAE, MAPE
   - **Font:** Monospace (Courier) for clarity

---

## Included Figures

### 1. **spatial_comparison_diatoms.png**
- **Phylum:** Bacillariophyta
- **Satellite variable:** DIATO_mean
- **Characteristic:** Diatoms are silica-shelled eukaryotic algae, major primary producers
- **Color scheme:** Satellite (#1B9E77 - teal), In Situ (#D95F02 - orange)

### 2. **spatial_comparison_dinoflagellates.png**
- **Phylum:** Dinophyta (labeled "Dino NA" in eDNA data)
- **Satellite variable:** DINO_mean
- **Characteristic:** Armor-plated unicellular protists; important producers and grazers
- **Color scheme:** Satellite (#2E86AB - blue), In Situ (#E63946 - red)

### 3. **spatial_comparison_green_algae.png**
- **Phylum:** Chlorophyta
- **Satellite variable:** GREEN_mean
- **Characteristic:** Chlorophyll-rich green algae; commonly benthic and planktonic forms
- **Color scheme:** Satellite (#66A61E - green), In Situ (#E6AB02 - gold)

### 4. **spatial_comparison_haptophytes.png**
- **Phylum:** Haptista (labeled in eDNA data)
- **Satellite variable:** HAPTO_mean
- **Characteristic:** Calcifying eukaryotes with characteristic haptonema; form coccoliths
- **Color scheme:** Satellite (#7570B3 - purple), In Situ (#A6761D - brown)

### 5. **spatial_comparison_ciliated_protists.png**
- **Phylum:** Ciliophora
- **Satellite variable:** CHL_mean (proxy for overall productivity)
- **Characteristic:** Heterotrophic ciliated protists; important for microbial loop dynamics
- **Color scheme:** Satellite (#E7298A - magenta), In Situ (#66C2A5 - cyan)

### 6. **spatial_comparison_total_chlorophyll.png**
- **Aggregate measure:** All classified eDNA taxa combined
- **Satellite variable:** CHL_mean (total chlorophyll-a)
- **Characteristic:** Integrated view of total phytoplankton biomass (chlorophyll-a proxy)
- **Color scheme:** Satellite (#A6761D - brown), In Situ (#F0E442 - yellow)

---

## Statistical Interpretation

### **Correlation Coefficient (Pearson r)**
- **Range:** -1 to +1
- **Interpretation:**
  - r > 0.7: Strong positive relationship
  - 0.3 < r < 0.7: Moderate relationship
  - r < 0.3: Weak relationship
  - p-value < 0.05: Statistically significant at 95% confidence

### **R² (Coefficient of Determination)**
- **Interpretation:** Proportion of variance in in situ data explained by satellite data
- Example: R² = 0.45 means 45% of in situ variation is predictable from satellite

### **RMSE (Root Mean Square Error)**
- **Units:** Same as data (records/month)
- **Interpretation:** Typical magnitude of prediction error

### **MAPE (Mean Absolute Percentage Error)**
- **Interpretation:** Average percent deviation; useful for relative error assessment

---

## Data Characteristics

### **Temporal Coverage**
- **Satellite data:** 2000-2024 (Copernicus Product)
- **In Situ data:** 2000-2016 (eDNA sequencing)
- **Overlap period:** 2000-2016 (204 months)

### **Spatial Domain**
- **Region:** Gulf of California (Golfo de California), Mexico
- **Latitude:** 18°N to 33°N
- **Longitude:** 102°W to 117°W
- **Ecosystem:** Semi-enclosed tropical/subtropical marine system

### **Sample Sizes**
- **In situ records (2000-2016):** 17,015 total eDNA observations
- **Monthly comparison points:** Varies by phyla (n shown in each figure)
- **Satellite measurements:** 204 monthly means (gridded and averaged)

---

## Methodological Notes

### **Data Integration**
1. **Satellite data:** Monthly averages computed from daily Copernicus satellite products
2. **In Situ data:** eDNA-based species classification aggregated to functional groups
3. **Temporal alignment:** Both datasets grouped by month-year for comparison
4. **Spatial alignment:** In situ observations treated as point measurements; no spatial interpolation of satellite data

### **Functional Group Classification**
- Classifications based on phylogenetic taxonomy (phylum level)
- Functional groups chosen to align with satellite-retrieved PFT categories
- Nomenclature aligned with scientific literature conventions

### **Statistical Methods**
- **Pearson correlation:** Linear relationship strength
- **Spearman correlation:** Rank-based relationship (less sensitive to outliers)
- **Linear regression:** OLS (Ordinary Least Squares) fit
- **Residual analysis:** Visual assessment of model assumptions

---

## Figure Quality Specifications

### **Technical Details**
- **Format:** PNG (Raster)
- **Resolution:** 300 DPI (publication-grade)
- **Dimensions:** 18" × 10" (16:9 aspect ratio)
- **File size:** ~800 KB per figure
- **Color space:** RGB
- **Font:** Arial, Helvetica (sans-serif)
- **Font sizes:** 
  - Main title: 13 pt (bold)
  - Subplot titles: 11 pt (bold)
  - Axis labels: 10 pt (bold)
  - Tick labels: 9 pt
  - Legend: 9 pt

### **Design Principles**
- Color-blind friendly palette (tested with Dichromat simulator)
- High contrast for legibility at small scales (journal publication)
- Consistent color scheme across all panels
- Professional serif-free typography
- Minimalist design with grid lines for reference

---

## Recommended Usage

### **Publication Context**
- Suitable for inclusion in peer-reviewed manuscripts
- Recommended for figures describing in situ validation studies
- Ideal for supplementary materials on data integration methods
- Useful for presentations on remote sensing verification

### **Figure Captions (Template)**

*Figure X: Satellite versus in situ [Phylum Name] concentrations in the Gulf of California (2000-2016). (A) Temporal comparison showing satellite-derived concentration (left axis, line) and in situ eDNA record frequency (right axis, bars) by month. (B) Geographic distribution of eDNA sampling locations colored by year. (C) Correlation analysis between satellite and in situ data with linear regression fit. (D) Residual plot assessing model fit. (E) Summary statistics including sample size, descriptive statistics, correlation metrics, and error measures.*

---

## Limitations & Caveats

1. **Data Mismatch:** Satellite measures optical properties (bulk chlorophyll) while eDNA detects species presence (binary/abundance)
2. **Temporal Resolution:** In situ sampling is episodic; satellite provides continuous coverage
3. **Spatial Mismatch:** Satellite measures entire water column; eDNA samples typically depth-specific
4. **Proxy Limitations:** Chlorophyll concentration ≠ phytoplankton biomass (variable C:Chl ratios)
5. **Taxonomic Resolution:** eDNA classification limited to phylum level; species-level identification not available
6. **Period Limitation:** Analysis covers 2000-2016; satellite data extends to 2024

---

## Data Sources

### **Satellite Data**
- **Product:** Copernicus Marine Service - Phytoplankton Functional Types (PFT)
- **Provider:** European Commission/Copernicus Program
- **Temporal resolution:** Daily → aggregated to monthly
- **Spatial resolution:** Variable (typically 4 km)
- **Variables:** 10 PFT types (CHL, DIATO, DINO, GREEN, HAPTO, MICRO, NANO, PICO, PROCHLO, PROKAR)

### **In Situ Data**
- **Method:** Environmental DNA (eDNA) metabarcoding
- **Source:** Taxonomic corrected eDNA dataset (version 2.0)
- **Sequencing target:** 18S rRNA and related genes
- **Taxonomic database:** Aligned to standard phyla classification
- **Geographic focus:** Gulf of California marine surveys

### **Climate Indices**
- **NIÑO 3.4 Index:** Monthly anomalies from NOAA
- **MEI (Multivariate ENSO Index):** From NOAA Earth System Research Laboratories
- **PDO (Pacific Decadal Oscillation):** From NOAA Fisheries Northwest Fisheries Science Center

---

## File Information

| Filename | Phyla | Records | Status |
|----------|-------|---------|--------|
| spatial_comparison_diatoms.png | Bacillariophyta | 1,646 | ✓ Complete |
| spatial_comparison_dinoflagellates.png | Dinophyta | 1,662 | ✓ Complete |
| spatial_comparison_green_algae.png | Chlorophyta | 3,485 | ✓ Complete |
| spatial_comparison_haptophytes.png | Haptista | 450 | ✓ Complete |
| spatial_comparison_ciliated_protists.png | Ciliophora | 1,142 | ✓ Complete |
| spatial_comparison_total_chlorophyll.png | All taxa | 17,015 | ✓ Complete |

**Generation Date:** 2026-04-28  
**Script:** `plot_satellite_vs_insitu_spatial_panel.py`  
**Version:** 2.0 (Production Release)

---

## Citation Recommendation

If using these figures in publications, please cite:

> Ocean Primary Production Analysis Pipeline (2026). Satellite vs In Situ Spatial Comparison Panels [Data visualization]. Gulf of California Primary Production Database, version 2.0. [Institution/Authors].

---

## Contact & Questions

For questions about figure generation, data processing, or methodological details, refer to the main analysis pipeline documentation or contact the project maintainers.

**Last Updated:** April 28, 2026  
**Status:** Publication Ready
