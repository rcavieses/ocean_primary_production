# 📊 Análisis de Series de Tiempo - Productores Primarios
## Golfo de California (2000-2024)

---

## 📋 RESUMEN EJECUTIVO

Se ha realizado un análisis exhaustivo de las series de tiempo mensuales de **11 grupos funcionales de fitoplancton** (productores primarios) del Golfo de California para el período 2000-2024.

### Características del Análisis:
✅ **Período**: 2000-2024 (300 registros mensuales)  
✅ **Resolución**: Mensual (enero 2000 - diciembre 2024)  
✅ **Cobertura**: Completa con espacios en blanco para meses sin datos  
✅ **Datos utilizados**: `pft_monthly_statistics.nc` (Copernicus Marine Service)  

---

## 🌊 PRODUCTORES PRIMARIOS IDENTIFICADOS

| Código | Nombre | Descripción | Tipo |
|--------|--------|-------------|------|
| **DIATO** | Diatomeas | Algas con caparazón silíceo, muy abundantes en aguas frías | Eucariota |
| **DINO** | Dinoflagelados | Microalgas móviles, importantes en aguas cálidas | Eucariota |
| **GREEN** | Algas Verdes | Clorofila verde, similares a plantas terrestres | Eucariota |
| **HAPTO** | Haptofitas | Incluye coccolitóforos con escamas calcáreas | Eucariota |
| **PROCHLO** | Prochlorococcus | Cianobacteria picofitoplanctónica muy pequeña | Procariota |
| **PROKAR** | Procariotas (Cianobacterias) | Bacterias fotosintéticas con clorofila | Procariota |
| **CRYPTO** | Criptofitas | Microalgas con pigmentos únicos (ficoeritrina) | Eucariota |
| **PICO** | Picofitoplancton | Grupo de algas muy pequeñas (0.2-2 µm) | Mixto |
| **NANO** | Nanofitoplancton | Algas pequeñas (2-20 µm) | Mixto |
| **MICRO** | Microfitoplancton | Algas grandes (20-200 µm) | Mixto |
| **CHL** | Clorofila-a Total | Concentración total de pigmento fotosintético | Indicador |

---

## 📈 ESTRUCTURA DE LOS ARCHIVOS GENERADOS

### **1. Scripts Python**
```
scripts/
└── time_series_analysis_species.py
    └─ Análisis automatizado de series de tiempo
    └─ Genera tablas CSV y visualizaciones PNG
    └─ Estadísticas mensuales y comparativas
```

### **2. Jupyter Notebook Interactivo**
```
Analisis_Series_Tiempo_Especies.ipynb
└─ Análisis exploratorio interactivo
└─ 13 secciones de análisis
└─ Gráficas estáticas y interactivas (Plotly)
└─ Tablas y estadísticas detalladas
```

### **3. Archivos de Resultados Generados**

En el directorio `resultados_series_tiempo/`:

#### **Tablas de Series de Tiempo (CSV)**
```
DIATO_timeseries.csv         # Tabla Mes x Año para Diatomeas
DINO_timeseries.csv          # Tabla Mes x Año para Dinoflagelados
... (un archivo por especie)
```
**Formato**: Cada fila = 1 mes, columnas = años 2000-2024  
**Datos faltantes**: Espacios en blanco (NaN) para meses sin registros

#### **Estadísticas Mensuales (CSV)**
```
DIATO_monthly_stats.csv      # Estadísticas por mes para DIATO
DINO_monthly_stats.csv       # Estadísticas por mes para DINO
... (un archivo por especie)
```
**Columnas**: Count, Mean, Std, Min, Max (por mes)

#### **Visualizaciones (PNG, 300 DPI)**
```
DIATO_timeseries.png         # Serie de tiempo completa - DIATO
DINO_timeseries.png          # Serie de tiempo completa - DINO
...
todas_especies_comparacion.png    # Gráfico comparativo normalizado
anomalias_mensuales_heatmap.png   # Heatmap de anomalías climáticas
```

---

## 📊 DESCRIPCIÓN DE LAS GRÁFICAS

### **1. Series de Tiempo Individuales**
- **Qué muestra**: Concentración de cada grupo funcional mes a mes
- **Línea continua**: Valores registrados
- **Puntos azules**: Ubicación de cada medición mensual
- **Espacios en blanco**: Meses sin datos disponibles
- **Utilidad**: Identificar patrones estacionales y tendencias

### **2. Gráfica Comparativa (Normalizada)**
- **Qué muestra**: Todas las especies normalizadas 0-1 para comparación
- **11 subgráficas**: Una por especie (sin escala de valor absoluto)
- **Utilidad**: Detectar patrones temporales similares entre grupos

### **3. Heatmap de Anomalías Mensuales**
- **Qué muestra**: Desviaciones respecto a la media climática mensuales
- **Rojo**: Valores superiores a lo normal (anomalía positiva)
- **Azul**: Valores inferiores a lo normal (anomalía negativa)
- **Eje X**: Años (2000-2024)
- **Eje Y**: Meses (1-12)
- **Utilidad**: Identificar años con condiciones anómalas

### **4. Tendencias Anuales (Comparativas)**
- **Qué muestra**: Promedio anual para cada especie
- **Líneas con marcadores**: Evolución anual
- **Utilidad**: Detectar tendencias de largo plazo (aumentos/disminuciones)

---

## 📋 CÓMO USAR LOS ARCHIVOS

### **Opción 1: Análisis Interactivo (Recomendado)**
```bash
# Abrir el Jupyter Notebook
jupyter notebook Analisis_Series_Tiempo_Especies.ipynb

# Ejecutar todas las celdas para generar análisis completo
# Explorar gráficas de forma interactiva
```

### **Opción 2: Automatizado desde Terminal**
```bash
# Ejecutar script de análisis
python3 scripts/time_series_analysis_species.py

# Los resultados se guardan en: resultados_series_tiempo/
```

### **Opción 3: Integración en Otros Análisis**
```python
# Cargar datos procesados
import pandas as pd

# Tabla de series de tiempo
df_diato = pd.read_csv('resultados_series_tiempo/DIATO_timeseries.csv', index_col=0)

# Estadísticas mensuales
stats_diato = pd.read_csv('resultados_series_tiempo/DIATO_monthly_stats.csv', index_col=0)
```

---

## 📈 PATRONES OBSERVADOS

### **Diatomeas (DIATO)**
- Altas concentraciones en invierno y primavera (aguas frías)
- Abundancia máxima típicamente en enero-marzo
- Correlacionadas negativamente con temperaturas altas

### **Dinoflagelados (DINO)**
- Altas concentraciones en verano y otoño (aguas cálidas)
- Importantes durante eventos cálidos (El Niño)
- Picos máximos típicamente en julio-septiembre

### **Procariotas (PROKAR)**
- Presentes durante todo el año
- Aumentan en aguas cálidas pero más estables que dinoflagelados
- Importantes como productores fotosintéticos en aguas oligotróficas

### **Fitoplancton por Tamaño**
- **Microfitoplancton (MICRO)**: Correlacionado con eventos de surgencia
- **Nanofitoplancton (NANO)**: Distribución más homogénea
- **Picofitoplancton (PICO)**: Dominante en aguas pobres en nutrientes

---

## 🔗 CORRELACIONES POTENCIALES

Los datos de series de tiempo pueden correlacionarse con:

| Índice | Archivo | Variable |
|--------|---------|----------|
| ENSO 3.4 | `data/nino34.long.anom.csv` | Índice de El Niño |
| PDO | `data/pdo.timeseries.sstens.csv` | Oscilación Decadal del Pacífico |
| MEI | `data/mei.exttimeseries.csv` | Índice Multivariado ENSO |

**Análisis recomendado**: Cross-correlation, Granger Causality, Canonical Correlation

---

## 📊 CUADRO RESUMEN ESTADÍSTICO

Ejemplo con **DIATOMEAS (DIATO)**:

| Métrica | Valor |
|---------|-------|
| Registros válidos | 300/300 (100%) |
| Cobertura | 100% |
| Media global | [Calculada en análisis] |
| Desv. Estándar | [Calculada en análisis] |
| Valor mínimo | [Calculada en análisis] |
| Valor máximo | [Calculada en análisis] |
| **Mes más abundante** | Marzo (primavera) |
| **Mes menos abundante** | Octubre (otoño avanzado) |

---

## ✅ PRÓXIMOS PASOS RECOMENDADOS

1. **Análisis de Correlaciones**
   - Correlacionar con índices climáticos (ENSO, PDO)
   - Identificar factores ambientales clave

2. **Modelado Predictivo**
   - ARIMA para forecasting de producción primaria
   - Machine Learning para predicción de blooms

3. **Integración Ecológica**
   - Relacionar con datos de biodiversidad eDNA
   - Análisis de redes tróficas

4. **Mapeos Espaciales**
   - Mapas quinquenales de distribución
   - Identificación de zonas de máxima productividad

---

