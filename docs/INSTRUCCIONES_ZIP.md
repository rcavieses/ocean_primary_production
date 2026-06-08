# INSTRUCCIONES: Cómo usar el ZIP del Reporte PFT

## 1. Contenido del ZIP

El archivo `reporte_pft_YYYYMMDD_HHMMSS.zip` contiene:

```
reporte/
├── index.html                    # 🔗 Archivo principal (abrir aquí)
├── README.txt                    # Instrucciones
├── pft_analysis.Rmd             # Código fuente (R Markdown)
├── utils.R                       # Funciones de utilidad
├── figures/
│   └── html_outputs/            # Todos los gráficos interactivos
│       ├── timeseries/          # Series temporales mensuales
│       ├── quinquennial/        # Mapas de diferencias
│       ├── seasonal/            # Comparaciones estacionales
│       └── [archivos HTML y dependencias]
└── data/
    ├── intermediate_data/       # Datos para regeneración
    │   ├── timeseries/         # *.csv
    │   ├── quinquennial/       # *.csv + *.json
    │   └── seasonal/           # *.csv
    └── nino34.long.anom.csv    # Datos NIÑO3.4
```

## 2. Cómo descomprimir y usar

### En Linux/Mac:
```bash
# Descomprimir
unzip reporte_pft_20260115_192257.zip

# Abrir en navegador
cd reporte
# Opción 1: Con Python
python3 -m http.server 8000
# Luego abrir: http://localhost:8000/index.html

# Opción 2: Abrir directamente
firefox index.html
# o
open index.html  # en Mac
```

### En Windows:
1. Click derecho en el ZIP → Extraer todo
2. Entrar a la carpeta `reporte`
3. Doble click en `index.html`

## 3. Características del Reporte

✅ **Gráficos Interactivos**
- Zoom, pan, hover info
- Mostrar/ocultar series
- Descargar como PNG

✅ **Integración NIÑO3.4**
- Anomalías NIÑO3.4 en series temporales
- Clasificación de eventos ENSO
- Doble eje Y para comparación

✅ **Análisis Completo**
- 10 variables de fitoplancton
- 4 períodos quinquenales
- 4 estaciones del año

✅ **Datos Intermedios**
- Archivos CSV para regeneración
- Metadatos JSON
- Reproducibilidad garantizada

## 4. Funcionamiento Offline

✓ El reporte funciona completamente OFFLINE
✓ No requiere conexión a internet
✓ Todos los gráficos se procesan localmente
✓ Compatible con todos los navegadores modernos

## 5. Si quiere regenerar los gráficos

Requiere:
- R con paquetes: ncdf4, tidyverse, plotly, etc.
- Archivo NetCDF original: `pft_golfo_california_2000_2024.nc`

Pasos:
```r
setwd("ruta/a/reporte")
source("utils.R")
# ... ejecutar código del análisis
```

## 6. Navegación en el Reporte

El HTML tiene pestañas para:
1. **Series Temporales** - Evolución mensual con NIÑO3.4
2. **Diferencias Quinquenales** - Cambios entre períodos
3. **Comparación Estacional** - Variaciones por estación

Cada sección tiene:
- Datos interactivos (Plotly)
- Múltiples variables (seleccionar con pestañas)
- Controles de zoom y descarga

## 7. Resolución de problemas

**Los gráficos no aparecen:**
- ✓ Verificar que JavaScript está habilitado
- ✓ Usar navegador moderno (Chrome, Firefox, Safari)
- ✓ Probar en modo local (http://localhost:8000/)

**El ZIP es muy grande (109 MB):**
- ✓ Normal - incluye todas las dependencias
- ✓ Se comprime bien al transmitir
- ✓ Funciona offline completamente

**Quiero usar datos específicos:**
- ✓ Consultar archivos en `data/intermediate_data/`
- ✓ CSVs con formato: lon, lat, value
- ✓ Metadatos en archivos JSON

## 8. Información sobre archivos

### Archivo Principal
- **index.html**: Reporte consolidado, autocontendido
- Tamaño: ~31 KB
- Contiene referencias a figuras y datos en estructura relativa

### Figuras (html_outputs/)
- **timeseries/**: Series temporales mensuales
  - `*_combined_timeseries.html`: Gráfico principal
  - `*_monthly_anomaly.html`: Anomalía vs NIÑO3.4

- **quinquennial/**: Diferencias entre períodos
  - `*_quinquennial_diff.html`: Mapas interactivos
  - Colormaps: Rojo=aumento, Azul=disminución

- **seasonal/**: Análisis estacional
  - `*_seasonal_comparison.html`: Barras agrupadas
  - `*_seasonal_trends.html`: Líneas de tendencia

### Datos (intermediate_data/)
- **timeseries/**: `*_timeseries_data.csv`
  - Columnas: date, value, rolling_mean, anomaly, NINO34, ENSO_phase
  
- **quinquennial/**: `*_diff_PERIOD_vs_PERIOD.csv`
  - Columnas: lon, lat, value
  - Metadatos: `*_metadata.json`

- **seasonal/**: `*_seasonal_data.csv`
  - Columnas: Period, Season, Value, variable

## 9. Para desarrolladores

Los datos CSV pueden usarse para:
- Visualizaciones personalizadas
- Análisis estadístico adicional
- Validación de resultados
- Integración con otros sistemas

Ejemplo en Python:
```python
import pandas as pd

# Cargar datos
ts_data = pd.read_csv("data/intermediate_data/timeseries/CHL_timeseries_data.csv")
print(ts_data.head())

# Calcular correlación con NIÑO3.4
correlation = ts_data['value'].corr(ts_data['NINO34'])
print(f"Correlación: {correlation:.3f}")
```

## 10. Créditos

- **Datos**: Ocean Primary Production Analysis
- **Índices climáticos**: NOAA
- **Visualización**: Plotly
- **Análisis**: R + tidyverse

---

**Última actualización**: Enero 2026
**Período de datos**: 2000-2024
**Resolución**: Mensual (300 timesteps)
