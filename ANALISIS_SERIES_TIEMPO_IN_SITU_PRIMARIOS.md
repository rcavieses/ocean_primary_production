# Análisis de Series de Tiempo para Productores Primarios
## Período: 2000-2024 (Registros Mensuales)

### Resumen Ejecutivo

Se ha realizado un análisis completo de las series de tiempo de **7 grupos de productores primarios** basado en **188,406 registros** del archivo de taxonomía. El análisis cubre un período de **25 años (2000-2024)** con granularidad mensual.

---

## 📊 GRUPOS IDENTIFICADOS

| Grupo | Registros | Descripción |
|-------|-----------|-------------|
| **Dinoflagelados** | 37,584 | Protistas fotosintéticos, importantes productores primarios |
| **Otros Eucariotas** | 34,101 | Eucariotas diversos con capacidad fotosintética |
| **Otros** | 109,269 | Organismos no clasificados en otros grupos |
| **Protozoa** | 6,318 | Protozoarios, incluyendo algunos fotosintéticos |
| **Haptofitas** | 972 | Algas microscópicas (coccolitóforos, etc.) |
| **Clorofitas** | 81 | Algas verdes |
| **Cianobacterias** | 81 | Bacterias fotosintéticas |
| **TOTAL** | **188,406** | Registros con fecha válida 2000-2024 |

---

## 📁 ARCHIVOS GENERADOS

### 1. Series de Tiempo (CSV) - Matriz Mes × Año

**Ubicación:** `/resultados_series_tiempo/`

Cada grupo tiene un archivo CSV con estructura:
- **Filas:** 12 meses (Enero - Diciembre)
- **Columnas:** 25 años (2000 - 2024)
- **Celdas:** Número de registros por mes/año
- **Celdas Vacías:** Meses sin registros (espacios en blanco)

**Archivos:**
- `dinoflagelados_in_situ_timeseries.csv`
- `otros_eucariotas_in_situ_timeseries.csv`
- `otros_in_situ_timeseries.csv`
- `protozoa_in_situ_timeseries.csv`
- `haptofitas_in_situ_timeseries.csv`
- `clorofitas_in_situ_timeseries.csv`
- `cianobacterias_in_situ_timeseries.csv`

**Ejemplo de formato:**
```
,2000,2001,2002,...,2024
Enero,,,,...,
Febrero,,,,2784.0,
Marzo,,,,...,
...
```

### 2. Estadísticas Mensuales (CSV)

**Ubicación:** `/resultados_series_tiempo/`

Para cada grupo, se calcula:
- **Total_Registros:** suma de registros en ese mes (todos los años)
- **Años_con_Datos:** número de años en que hay registros para ese mes
- **Promedio_por_Año:** media de registros por año para ese mes

**Archivos:**
- `dinoflagelados_in_situ_monthly_stats.csv`
- `otros_eucariotas_in_situ_monthly_stats.csv`
- Y 5 más...

**Ejemplo:**
```
Mes,Total_Registros,Años_con_Datos,Promedio_por_Año
Enero,0,0,0.0
Junio,6032,3,241.28
```

---

## 📈 GRÁFICAS GENERADAS

**Ubicación:** `/resultados_series_tiempo/figuras_primarios/`

### Gráficas de Series de Tiempo
- **`series_tiempo_in_situ_primarios_completa.png`** 
  - 7 paneles individuales (uno por grupo)
  - Muestra evolución temporal del 2000-2024
  - Incluye estadísticas (Total, Promedio, Máximo)
  - Líneas con puntos para visualizar tendencias

- **`in_situ_comparativa_grupos_primarios.png`**
  - Una gráfica con todos los grupos superpuestos
  - Permite comparar dinámicas entre grupos
  - Valores mensuales del período completo

### Heatmaps (Mapas de Calor)
**Uno por grupo:** `heatmap_in_situ_[grupo].png` (7 archivos)

- **Estructura:** Matriz 12 meses × 25 años
- **Código de color:** Intensidad indica número de registros
- **Utilidad:** 
  - Identificar patrones estacionales
  - Visualizar años/meses ausentes
  - Detectar anomalías

### Gráficas de Proporciones

- **`barras_apiladas_in_situ_proporciones_anuales.png`**
  - Barras apiladas al 100% por año (2000-2024)
  - Muestra composición porcentual de cada grupo
  - Permite ver cambios en dominancia temporal

- **`pie_in_situ_proporciones_totales.png`**
  - Gráfica de pastel con proporciones totales
  - Incluye tabla con registros absolutos y porcentajes
  - Visión global de importancia relativa de cada grupo

---

## 🔍 HALLAZGOS CLAVE

### Dinoflagelados (37,584 registros)
- **Patrón:** Registros concentrados en mayo-octubre
- **Pico:** Julio (10,672 registros)
- **Ausencia:** Enero, marzo, septiembre, diciembre
- **Implicación:** Floración estacional típica de primavera-otoño

### Otros Eucariotas (34,101 registros)
- **Distribución:** Más uniforme durante el año
- **Variabilidad:** Presente en múltiples años

### Protozoa (6,318 registros)
- **Presencia:** Registros en varios meses del año
- **Patrón:** Menos concentrado que dinoflagelados

### Grupos Minoritarios (Cianobacterias, Clorofitas)
- **Registros limitados:** 81 cada uno
- **Potencial sesgo:** Pueden ser subestimados en muestreo

---

## 💡 INTERPRETACIÓN DE DATOS

### Filas Vacías (espacios en blanco)
Indican meses sin registros durante el período 2000-2024.
- Puede indicar: ausencia real, sesgo de muestreo, o baja abundancia

### Valores Altos
Concentración de registros en ciertos meses/años.
- **Dinoflagelados:** Floración en verano-otoño del Golfo de California

### Ausencias Sistemáticas
Algunos grupos no registrados en ciertos períodos.
- Requiere análisis de cobertura de muestreo

---

## 📊 CÓMO USAR LOS ARCHIVOS

### Para Análisis Estadísticos
1. Usar archivos CSV de *timeseries para análisis de tendencias
2. Aplicar modelos de serie de tiempo (ARIMA, STL, etc.)
3. Analizar estacionalidad

### Para Visualización
1. Revisar heatmaps para patrones estacionales
2. Examinar gráficas de serie temporal para tendencias
3. Usar gráfica comparativa para relaciones entre grupos

### Para Reportes
1. Incluir estadísticas mensuales para contexto
2. Incorporar gráficas para visualización rápida
3. Referir a matrices CSV para detalles numéricos

---

## 📝 NOTAS TÉCNICAS

- **Conversión de Fechas:** Números seriales de Excel convertidos a fechas calendáricas
- **Rango:** Solo se incluyeron registros 2000-2024
- **Filtrado:** Se excluyeron registros sin fecha válida (~2,300)
- **Clasificación:** Basada en phylum/clase del archivo de taxonomía
- **Resolución:** Mensual (12 intervalos por año)

---

## 🎯 PRÓXIMOS PASOS SUGERIDOS

1. **Análisis de Tendencia:** Evaluar cambios a largo plazo
2. **Correlación:** Relacionar con variables ambientales (temperatura, nutrientes)
3. **Validación:** Revisar sesgo de muestreo por período
4. **Predicción:** Usar series de tiempo para pronósticos estacionales
5. **Integración:** Combinar con datos oceanográficos (MEI, PDO, Niño 3.4)

---

**Script:** `scripts/analisis_series_tiempo_in_situ_primarios.py`  
**Documentación:** `ANALISIS_SERIES_TIEMPO_IN_SITU_PRIMARIOS.md`  
**Generado:** 2024-03-09  
**Versión:** 1.0
