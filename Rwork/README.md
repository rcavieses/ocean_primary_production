# Análisis PFT - Golfo de California (2000-2024)

## Descripción

Este análisis procesa datos de fitoplancton del Golfo de California (2000-2024) e integra información de anomalías NIÑO3.4 para entender la variabilidad de la producción primaria fitoplanctónica.

## Estructura de carpetas

```
ocean_primary_production/
├── Rwork/                           # Análisis R
│   ├── pft_analysis.Rmd            # Notebook principal (R Markdown)
│   ├── pft_analysis_simple.Rmd     # Versión alternativa simplificada
│   ├── utils.R                      # Funciones utilitarias
│   ├── run_analysis.R               # Script para ejecutar análisis
│   └── README.md                    # Este archivo
│
├── scripts/                         # Scripts Python
│   ├── plot_pft_maps.py
│   ├── plot_pft_monthly_timeseries.py
│   ├── plot_pft_quinquennial_diff.py
│   ├── plot_pft_quinquennial_maps.py
│   ├── plot_pft_seasonal_quinquennial_comparison.py
│   └── ...
│
├── data/                            # Datos
│   ├── pft_golfo_california_2000_2024.nc  # NetCDF principal
│   ├── nino34.long.anom.csv              # Anomalías NIÑO3.4
│   └── figures/
│       ├── html_outputs/            # Gráficos interactivos HTML
│       │   ├── timeseries/
│       │   ├── quinquennial/
│       │   └── seasonal/
│       └── intermediate_data/       # Datos intermedios para regeneración
│           ├── timeseries/
│           ├── quinquennial/
│           └── seasonal/
│
└── analisis_html/                   # (Deprecated - usar Rwork/)
```

## Instalación de dependencias

### En Linux/Mac (primera vez):

```bash
cd ocean_primary_production/Rwork
Rscript -e "install.packages(c('ncdf4', 'tidyverse', 'lubridate', 'plotly', 'zoo', 'htmlwidgets', 'jsonlite', 'rmarkdown'), repos='https://cloud.r-project.org/')"
```

### En R interactivo:

```r
packages <- c("ncdf4", "tidyverse", "lubridate", "plotly", "zoo", "htmlwidgets", "jsonlite", "rmarkdown")
install.packages(packages, repos = "https://cloud.r-project.org/")
```

## Ejecución del análisis

### Opción 1: Desde terminal (recomendado)

```bash
cd /home/atlantis/atlantis_primary_producton/ocean_primary_production/Rwork
Rscript run_analysis.R
```

### Opción 2: Desde R interactivo

```r
setwd("/home/atlantis/atlantis_primary_producton/ocean_primary_production/Rwork")
rmarkdown::render("pft_analysis.Rmd")
```

### Opción 3: Desde RStudio

1. Abrir `pft_analysis.Rmd` en RStudio
2. Hacer clic en "Knit" o presionar Ctrl+Shift+K

## Salida

El análisis genera:

### Archivos HTML interactivos
- `pft_analysis_YYYYMMDD_HHMMSS.html` - Reporte completo con todos los gráficos embebidos

### Datos intermedios (en `../data/figures/intermediate_data/`)
- **timeseries/**: `*_timeseries_data.csv` - Series temporales mensuales
- **quinquennial/**: `*_diff_PERIOD1_vs_PERIOD2.csv` + `*_metadata.json` - Mapas de diferencias
- **seasonal/**: `*_seasonal_data.csv` - Datos estacionales

## Contenido del análisis

### 1. Series Temporales Mensuales
- Gráficos interactivos con:
  - Media mensual
  - Media móvil de 12 meses
  - Anomalía NIÑO3.4 (escala doble eje Y)
  - Anomalías de PFT vs NIÑO3.4
- Datos guardados en CSV para reproducción

### 2. Diferencias Quinquenales
- Mapas de diferencias entre períodos consecutivos:
  - 2005-2009 vs 2000-2004
  - 2010-2014 vs 2005-2009
  - 2015-2019 vs 2010-2014
  - 2020-2024 vs 2015-2019
- Colormap divergente (rojo=incremento, azul=decremento)
- Datos espaciales guardados en CSV

### 3. Comparación Estacional
- Gráficos por barras agrupadas (Primavera, Verano, Otoño, Invierno)
- Gráficos de tendencias estacionales
- Datos tabulares guardados en CSV

## Variables analizadas

| Variable | Descripción | Unidades |
|----------|-------------|----------|
| CHL | Clorofila-a Total | mg m⁻³ |
| DIATO | Diatomeas | mg m⁻³ |
| DINO | Dinoflagelados | mg m⁻³ |
| GREEN | Algas Verdes | mg m⁻³ |
| HAPTO | Haptofitas | mg m⁻³ |
| MICRO | Microfitoplancton | mg m⁻³ |
| NANO | Nanofitoplancton | mg m⁻³ |
| PICO | Picofitoplancton | mg m⁻³ |
| PROCHLO | Prochlorococcus | mg m⁻³ |
| PROKAR | Procariotas | mg m⁻³ |

## Integración NIÑO3.4

Los gráficos de series temporales incluyen información de anomalías NIÑO3.4 de NOAA:
- **El Niño**: NIÑO3.4 ≥ 0.5°C
- **La Niña**: NIÑO3.4 ≤ -0.5°C
- **Neutral**: -0.5°C < NIÑO3.4 < 0.5°C

Fuente: [NOAA PSL](https://psl.noaa.gov/data/timeseries/month/)

## Regeneración de gráficos

Los datos intermedios guardados permiten regenerar gráficos sin recargar los datos NetCDF:

```r
# Ejemplo: Regenerar un mapa de diferencias
source("utils.R")

data <- load_map_data("../data/figures/intermediate_data/quinquennial/CHL_diff_2000-2004_vs_2005-2009.csv")

p <- plotly::plot_ly(data$data, x = ~lon, y = ~lat, z = ~value, type = 'heatmap')
```

## Solución de problemas

### Error: "no se puede abrir el archivo NetCDF"
- Verificar que `../data/pft_golfo_california_2000_2024.nc` existe
- Verificar permisos de lectura

### Error: "dimensiones incompatibles"
- Verificar que el archivo NetCDF contiene las variables esperadas
- Ejecutar en terminal: `ncdump -h ../data/pft_golfo_california_2000_2024.nc`

### El HTML no muestra gráficos
- Los gráficos se generan on-the-fly en el navegador
- Verificar que JavaScript está habilitado en el navegador
- Descargar y abrir el HTML localmente

### Ejecución lenta
- El análisis procesa ~300 timesteps de datos espaciales
- La ejecución puede tardar 30-60 minutos en hardware estándar
- Usar `run_analysis.R` para ejecutar en segundo plano

## Notas técnicas

- **Formato de datos**: NetCDF con variables georeferenciadas
- **Resolución temporal**: Mensual (2000-2024)
- **Procesamiento de memoria**: Los datos se cargan en bloques para optimizar uso de RAM
- **Gráficos**: Plotly (interactivos, HTML autocontendidos)
- **Formato de reporte**: HTML5 autocontendido (funciona offline)

## Autores

Ocean Primary Production Analysis Team

## Referencias

- Dataset: Gulf of California Phytoplankton (2000-2024)
- NIÑO3.4: NOAA Physical Sciences Laboratory

---

*Última actualización: `r format(Sys.time(), "%Y-%m-%d")`*
