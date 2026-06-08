# Guía de Uso: Reporte de Análisis Numérico

**Generado:** 3 de Marzo de 2026  
**Script:** `scripts/generate_analysis_report.py`  
**Archivos de salida:**
- `data/figures/reporte_analisis_numerico.json` (66 KB) - Para máquinas/IA
- `data/figures/REPORTE_ANALISIS_CUANTITATIVO.md` (20 KB) - Para humanos

---

## 📋 Descripción General

Este reporte proporciona un análisis numérico exhaustivo de todas las variables de fitoplancton (PFT) en el Golfo de California, incluyendo:

1. **Estadísticas espaciales** (2000-2024)
2. **Comparaciones quinquenales** (5 períodos de 5 años)
3. **Anomalías respecto a 2020-2024** (período de referencia)
4. **Características temporales** (series mensuales)
5. **Tendencias lineales** (por mes y por año)
6. **Correlaciones climáticas** (MEI, NINO3.4, PDO)
7. **Comparaciones inter-variable** (correlaciones entre PFTs)

---

## 🎯 Uso Recomendado por Caso de Uso

### Para Científicos/Analistas
Use el archivo **Markdown** (`REPORTE_ANALISIS_CUANTITATIVO.md`):
- Abierto en VS Code o navegador
- Tablas formateadas y legibles
- Incluye contexto narrativo
- Fácil para análisis y escritura de reportes

**Cómo abrir:**
```bash
# En VS Code
code data/figures/REPORTE_ANALISIS_CUANTITATIVO.md

# O en cualquier navegador si se convierte a HTML
```

### Para Sistemas Automáticos/IA
Use el archivo **JSON** (`reporte_analisis_numerico.json`):
- Estructura jerárquica clara
- Fácil de parsear programáticamente
- Incluye todos los metadatos necesarios
- Ideal para integración en pipelines

**Cómo cargar en Python:**
```python
import json

with open('data/figures/reporte_analisis_numerico.json') as f:
    report = json.load(f)

# Ejemplo: obtener estadísticas de CHL
chl_stats = report['variables']['CHL']['map_statistics']
print(f"CHL media: {chl_stats['mean']:.4f} mg m⁻³")

# Ejemplo: obtener correlación con NINO3.4
nino_corr = report['variables']['CHL']['climate_correlations']['NINO34']
print(f"Correlación máxima: {nino_corr['max_correlation']:.4f}")
print(f"Desfase en meses: {nino_corr['lag_at_max']}")
```

### Para Dashboards/Visualizaciones
Los datos pueden extraerse del JSON para:
- Crear gráficos de tendencia
- Mapas de anomalías
- Series temporales interactivas
- Correlogramas climáticos

---

## 📊 Estructura del Reporte JSON

### Nivel 1: Metadatos
```json
"metadata": {
  "generated_at": "2026-03-03T23:17:29.726691",
  "dataset": "...",
  "filtered": true,
  "filter_type": "shapefile_polygon",
  "study_area": "Gulf of California",
  "period_start": "2000-01-01",
  "period_end": "2024-12-31",
  "variables_count": 10
}
```

### Nivel 2: Variables (10 PFTs)
Cada variable contiene 5 secciones:

#### A. `map_statistics` - Estadísticas Espaciales
```json
"map_statistics": {
  "period": "2000-2024",
  "mean": 1.0755,          // Media espacial
  "median": 1.0154,        // Mediana
  "std": 0.4598,           // Desviación estándar
  "min": 0.4203,           // Valor mínimo
  "max": 2.4562,           // Valor máximo
  "count_valid_points": 300,
  "percentile_5": 0.4897,
  "percentile_25": 0.6708,
  "percentile_75": 1.3694,
  "percentile_95": 1.9668
}
```

#### B. `quinquennial_statistics` - Comparación por Período
```json
"quinquennial_statistics": {
  "2000-2004": {
    "mean": 1.0868,
    "median": 1.0241,
    "std": 0.4789,
    "min": 0.4203,
    "max": 2.3576,
    "count": 60
  },
  // ... más períodos: 2005-2009, 2010-2014, 2015-2019, 2020-2024
}
```

#### C. `anomalies_vs_2020_2024` - Cambios desde Período Reciente
```json
"anomalies_vs_2020_2024": {
  "2000-2004": {
    "absolute_change": 0.0207,    // en mg m⁻³
    "percent_change": 1.94        // porcentaje
  },
  // ... más períodos
}
```

#### D. `temporal_statistics` - Características de Series Mensuales
```json
"temporal_statistics": {
  "mean": 1.0755,
  "std": 0.4606,
  "min": 0.4203,
  "max": 2.4562,
  "coefficient_of_variation": 42.83,    // % variabilidad
  "data_points": 300,
  "coverage_percent": 100.0
}
```

#### E. `linear_trend` - Tendencias (2000-2024)
```json
"linear_trend": {
  "slope_per_month": -0.000588,    // cambio mensual
  "slope_per_year": -0.0071,       // cambio anual
  "intercept": 0.9234
}
```

#### F. `climate_correlations` - Correlaciones con Índices
```json
"climate_correlations": {
  "MEI": {
    "max_correlation": -0.2661,              // valor de correlación
    "lag_at_max": -5,                        // desfase en meses
    "correlations_by_lag": {                 // todos los desfases
      "-12": -0.1234,
      "-11": -0.1345,
      // ... hasta "+12"
      "0": -0.2340,
      // ...
      "+12": -0.0856
    }
  },
  "NINO34": {...},
  "PDO": {...}
}
```

### Nivel 3: Comparaciones Inter-Variable
```json
"inter_variable_comparisons": {
  "CHL_vs_DIATO": {
    "temporal_correlation": 0.8234
  },
  "DIATO_vs_DINO": {
    "temporal_correlation": 0.6123
  },
  // ... más pares variables
}
```

---

## 🔍 Ejemplos de Análisis

### Ejemplo 1: Encontrar Variable con Mayor Variabilidad
```python
import json

with open('reporte_analisis_numerico.json') as f:
    report = json.load(f)

# Calcular coeficiente de variación
cv_values = {}
for var, data in report['variables'].items():
    cv = data['temporal_statistics']['coefficient_of_variation']
    cv_values[var] = cv

# Top 3 variables más variables
sorted_cv = sorted(cv_values.items(), key=lambda x: x[1], reverse=True)
for var, cv in sorted_cv[:3]:
    print(f"{var}: {cv:.2f}%")
```

### Ejemplo 2: Detectar Tendencias Significativas
```python
# Variables con tendencia negativa (disminución)
print("Variables con disminución anual:")
for var, data in report['variables'].items():
    trend = data['linear_trend']['slope_per_year']
    if trend < 0:
        rel_change = (trend / data['temporal_statistics']['mean'] * 100)
        print(f"  {var}: {trend:.6f}/año ({rel_change:+.3f}%/año)")
```

### Ejemplo 3: Encontrar Strongest Teleconnections
```python
# Correlación más fuerte con cualquier índice climático
strongest_corr = {}
for var, data in report['variables'].items():
    if 'climate_correlations' in data:
        for index, corr_data in data['climate_correlations'].items():
            key = f"{var}_{index}"
            strongest_corr[key] = {
                'correlation': abs(corr_data['max_correlation']),
                'lag': corr_data['lag_at_max'],
                'actual_corr': corr_data['max_correlation']
            }

# Top 5 correlaciones
sorted_corr = sorted(strongest_corr.items(), 
                    key=lambda x: x[1]['correlation'], 
                    reverse=True)
for pair, data in sorted_corr[:5]:
    print(f"{pair}: r={data['actual_corr']:+.4f}, lag={data['lag']} meses")
```

### Ejemplo 4: Análisis de Cambio Decadal
```python
# ¿Cómo cambió la producción desde 2000-2004 a 2020-2024?
print("Cambios decadales (2000-04 → 2020-24):")
for var, data in report['variables'].items():
    if 'anomalies_vs_2020_2024' in data:
        change_2000_2004 = data['anomalies_vs_2020_2024']['2000-2004']
        pct = change_2000_2004['percent_change']
        sign = "↑" if pct > 0 else "↓"
        print(f"  {var}: {sign} {abs(pct):.2f}%")
```

---

## 📈 Interpretación de Resultados

### Sobre Correlaciones Climáticas
- **Lag negativo**: El índice climático lidera (causa → efecto)
- **Lag positivo**: La variable PFT lidera (reacción anticipada)
- **Lag cero**: Relación síncrona (respuesta inmediata)

**Ejemplo:** CHL con NINO3.4 lag=-2:
- La anomalía de NINO3.4 precede a cambios en CHL por ~2 meses
- Útil para pronósticos

### Sobre Anomalías
- Comparadas respecto a 2020-2024 (período más reciente)
- Positivo = más altas que período reciente
- Negativo = más bajas que período reciente

**Ejemplo:** 2015-2019 fue 12.99% MENOR que 2020-2024

### Sobre Tendencias Lineales
- Representan cambio constante por unidad de tiempo
- Pueden indicar cambios a largo plazo (clima, productividad)
- Se deben interpretar con cuidado (pueden ser ciclos)

---

## 🔄 Cómo Regenerar el Reporte

Si necesitas actualizar el reporte con nuevos datos o análisis:

```bash
cd /home/atlantis/atlantis_primary_producton/ocean_primary_production

# Ejecutar script
python3 scripts/generate_analysis_report.py

# Los archivos se sobrescriben en:
# - data/figures/reporte_analisis_numerico.json
# - data/figures/REPORTE_ANALISIS_CUANTITATIVO.md
```

El script toma ~5-10 minutos en ejecutarse.

---

## 📝 Notas Técnicas

- **Datos filtrados espacialmente** al polígono del Golfo de California
- **Filtrado aplicado en:** `preprocess_pft_data.py` (3 Marzo 2026)
- **Variables incluidas:** 10 tipos de fitoplancton funcional (PFT)
- **Período temporal:** Enero 2000 - Diciembre 2024 (25 años)
- **Resolución:** Estadísticas mensuales agregadas espacialmente
- **Índices climáticos:** MEI, NINO3.4, PDO (datos NOAA)

---

## 🎓 Preguntas Frecuentes

**P: ¿Por qué algunos valores están faltando?**
R: Los datos con NaN se excluyen automáticamente. El campo `count_valid_points` indica cuántos datos se usaron.

**P: ¿Cuál es la diferencia entre `mean_statistics` y `temporal_statistics`?**
R: 
- `map_statistics`: Promedio espacial de todos los puntos (12 meses × puntos)
- `temporal_statistics`: Estadísticas de la serie mensual (1 valor por mes)

**P: ¿Cómo interpreto un lag negativo?**
R: Significa que el índice climático lidera. Ejemplo: lag=-2 en NINO3.4 significa que cambios en NINO3.4 ocurren 2 meses ANTES de cambios en la variable PFT.

**P: ¿Puedo usar este reporte para pronósticos?**
R: Parcialmente. Las correlaciones con lag <0 son potencialmente predictivas, pero se requiere validación periódica.

---

## 📞 Para Más Información

- Ver: `REPORTE_ANALISIS_FILTRADO.md` (especificaciones técnicas)
- Ver: `RESUMEN_EJECUTIVO.md` (resumen de analyses ejecutados)
- Ver: `VALIDACION_TECNICA.txt` (verificaciones y validaciones)

