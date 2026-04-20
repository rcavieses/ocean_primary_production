# Metodología de Análisis: Series de Tiempo de Productores Primarios (eDNA In Situ)

## Datos de Entrada

### Archivo fuente: `taxonomy_corrected_edna.csv`

Este archivo contiene registros de muestreo de ADN ambiental (eDNA) recolectados en el Golfo de California. Cada fila representa la detección de una especie en un evento de muestreo. El archivo tiene **190,732 registros** y **22 columnas**:

| Columna | Descripción |
|---------|-------------|
| `Original_ID` | Identificador único del registro |
| `Abundancia` | Abundancia estimada del organismo (entero, muchos son 0 = solo presencia) |
| `ZONE` | Zona geográfica del Golfo (Central, North, South, South Pacific, Transición) |
| `SITE NAME` | Nombre del sitio de muestreo |
| `Shallow (m)` | Profundidad de muestreo en capa superficial (1–26 m) |
| `Mid-water (m)` | Profundidad de muestreo en capa intermedia (35–140 m) |
| `Deep (m)` | Profundidad de muestreo en capa profunda (220–1000 m) |
| `Latitude`, `Longitude` | Coordenadas del sitio |
| `Collected date year` | Fecha de colecta (número serial de Excel o formato DD/MM/YYYY) |
| `Season` | Estación (spring-summer, autumn-winter) |
| `Ocean Depth (-) (m)` | Profundidad del fondo oceánico en el sitio |
| `Distance from bottom (m)` | Distancia de la muestra al fondo |
| `Ocean Zone` | Zona oceánica (Pelagic, Benthic) |
| `source` | Fuente del dato (`eDNA`) |
| `species` | Nombre de la especie identificada |
| `kingdom` | Reino taxonómico |
| `phylum` | Filo taxonómico |
| `class` | Clase taxonómica |
| `order` | Orden taxonómico |
| `family` | Familia taxonómica |
| `genus` | Género taxonómico |

---

## Paso 1: Carga del Archivo CSV

Se lee el archivo CSV completo con `pandas.read_csv()`. Se obtienen 190,732 registros.

```python
df = pd.read_csv('taxonomy_corrected_edna.csv')
```

---

## Paso 2: Conversión de Fechas

La columna `Collected date year` contiene fechas en **dos formatos mixtos**:

1. **Números seriales de Excel** (ej. `44391`, `43657`): representan días transcurridos desde el 30 de diciembre de 1899.
2. **Texto en formato DD/MM/YYYY** (ej. `23/06/2018`).

Se aplica una función de conversión que detecta el formato automáticamente:

- Si el valor contiene `/`, se interpreta como texto con formato `DD/MM/YYYY`.
- Si es un número, se convierte del sistema serial de Excel usando la época `1899-12-30` como referencia y sumando los días correspondientes.
- Valores nulos o no convertibles se marcan como `NaT` (Not a Time).

```python
def excel_date_to_datetime(excel_date):
    if isinstance(excel_date, str) and '/' in excel_date:
        return pd.to_datetime(excel_date, format='%d/%m/%Y')
    excel_epoch = datetime(1899, 12, 30)
    return excel_epoch + pd.Timedelta(days=int(excel_date))
```

Resultado: se crea la columna `date` con tipo `datetime64`.

---

## Paso 3: Filtrado Temporal

Se eliminan registros sin fecha válida y se filtra al rango **2000–2024**:

- Se extraen las columnas `year` y `month` a partir de `date`.
- Se conservan solo los registros donde `2000 ≤ year ≤ 2024`.

Resultado: **~188,406 registros** con fecha válida en el rango de interés.

---

## Paso 4: Clasificación Taxonómica en Grupos Funcionales

Cada registro se clasifica en un **grupo funcional de productor primario** basándose en su taxonomía. La clasificación utiliza tres columnas jerárquicas: `phylum`, `class` y `kingdom`. Se busca coincidencia en ese orden con los siguientes grupos:

| Grupo Funcional | Phylums / Clases / Reinos Asociados |
|----------------|--------------------------------------|
| **Diatomeas** | Bacillariophyta, Diatomophyceae, Fragilariophyceae, Bacillariophyceae |
| **Dinoflagelados** | Dinophyta, Dinophyceae |
| **Clorofitas** | Chlorophyta, Chlorophyceae, Ulvophyceae |
| **Cianobacterias** | Cyanobacteria, Oxyphotobacteria |
| **Haptofitas** | Haptophyta, Prymnesiophyceae, Coccolithophyceae |
| **Otros Eucariotas** | Eukaryota (reino) |
| **Protozoa** | Protozoa, Discosea (phylum Amoebozoa) |
| **Otros** | Todo lo que no encaja en los grupos anteriores |

### Algoritmo de clasificación

Para cada registro se ejecuta la siguiente lógica:

1. Se obtienen los valores de `phylum`, `class` y `kingdom` del registro.
2. Se itera sobre cada grupo funcional y sus valores taxonómicos asociados.
3. Si alguno de los tres campos coincide con algún valor del grupo, se asigna ese grupo.
4. Si no hay coincidencia con ningún grupo pero `kingdom = 'Protozoa'` o `phylum = 'Amoebozoa'`, se asigna al grupo **Protozoa**.
5. Si no hay coincidencia alguna, se asigna al grupo **Otros**.

```python
def classify_producer(row):
    phylum = row.get('phylum', '')
    class_tax = row.get('class', '')
    kingdom = row.get('kingdom', '')
    
    for group, values in PRIMARY_PRODUCERS.items():
        if phylum in values or class_tax in values or kingdom in values:
            return group
    
    if kingdom == 'Protozoa' or phylum == 'Amoebozoa':
        return 'Protozoa'
    
    return 'Otros'
```

### Resultado de la clasificación

| Grupo | Registros |
|-------|-----------|
| Otros | 104,490 |
| Dinoflagelados | 42,363 |
| Otros Eucariotas | 34,101 |
| Protozoa | 6,318 |
| Haptofitas | 972 |
| Cianobacterias | 81 |
| Clorofitas | 81 |

> **Nota:** El grupo "Otros" incluye organismos que no son productores primarios (animales, hongos, etc.) pero que fueron detectados por eDNA en las mismas muestras.

---

## Paso 5: Construcción de la Matriz de Series de Tiempo

Para cada grupo funcional se construye una **matriz de frecuencia mensual** con dimensiones **12 meses × 25 años** (2000–2024).

### Procedimiento:

1. Se filtra el DataFrame al grupo funcional de interés.
2. Se crea una matriz vacía (`NaN`) de 12 filas (meses) × 25 columnas (años).
3. Para cada combinación año-mes, se cuenta el **número de registros** (filas del CSV) que coinciden.
4. Si el conteo es >0, se almacena el valor. Si es 0, se deja como `NaN` (indicando ausencia de muestreo, no ausencia de organismos).

```python
for year in range(2000, 2025):
    for month in range(1, 13):
        count = len(df_grupo[(df_grupo['year'] == year) & (df_grupo['month'] == month)])
        if count > 0:
            matriz.loc[month, year] = count
```

### Variable medida: Frecuencia de Ocurrencia

La métrica utilizada es la **frecuencia de ocurrencia** (número de registros eDNA por mes), **no** la abundancia absoluta. Esto se debe a que:
- La mayoría de los registros tienen `Abundancia = 0` (indicando presencia/ausencia).
- Solo ~6.8% de los registros tienen abundancia >0.
- La frecuencia de detección eDNA es un proxy de la presencia y actividad del grupo en el ambiente.

---

## Paso 6: Cálculo de Estadísticas Mensuales

Para cada grupo se calculan estadísticas agregadas por mes a lo largo de todos los años:

| Estadística | Descripción |
|-------------|-------------|
| `Total_Registros` | Suma de registros en ese mes para todos los años |
| `Años_con_Datos` | Número de años diferentes que tienen datos en ese mes |
| `Promedio_por_Año` | `Total_Registros / 25` (promedio anual para ese mes) |

---

## Paso 7: Conversión a Serie de Tiempo Lineal

La matriz mes × año se transforma en una **serie de tiempo lineal** para graficado:

1. Se recorre cada celda de la matriz (año, mes).
2. Si contiene un valor (no es `NaN`), se crea una fecha tipo `Timestamp(año, mes, 15)` (día 15 de cada mes como referencia).
3. Se almacenan pares (fecha, valor) ordenados cronológicamente.

Esto genera una serie temporal con **gaps naturales**: los meses sin muestreo aparecen como espacios vacíos en la gráfica, distinguiéndose de meses con muestreo pero sin detección.

---

## Paso 8: Generación de Visualizaciones

Se generan las siguientes figuras para cada grupo funcional:

### 8.1 Series de tiempo individuales
- Línea + puntos con relleno tipo área para cada grupo.
- Caja de texto con estadísticas: total de registros, promedio mensual y valor máximo.
- Eje X: año-mes; Eje Y: registros mensuales.
- **Archivo:** `series_tiempo_in_situ_primarios_completa.png`

### 8.2 Gráfica comparativa entre grupos
- Todos los grupos en una sola gráfica con colores distintos.
- Puntos conectados con línea sólida si son consecutivos (≤60 días entre ellos) o línea punteada si hay un gap temporal mayor.
- **Archivo:** `in_situ_comparativa_grupos_primarios.png`

### 8.3 Heatmaps de actividad mensual
- Un heatmap por grupo, mostrando la matriz meses (filas) × años (columnas).
- Escala de color `YlOrRd` con valores numéricos anotados en cada celda.
- Permite identificar patrones estacionales y años con mayor actividad.
- **Archivos:** `heatmap_in_situ_{grupo}.png`

### 8.4 Barras apiladas de proporciones anuales
- Para cada año, muestra la proporción porcentual que ocupa cada grupo respecto al total.
- Identifica cambios en la composición comunitaria a lo largo del tiempo.
- **Archivo:** `barras_apiladas_in_situ_proporciones_anuales.png`

### 8.5 Gráficas de pastel (proporción global)
- Proporción total de registros por grupo para todo el período 2000–2024.
- Una versión con todos los grupos y otra excluyendo "Otros" y "Otros Eucariotas" para visualizar mejor los productores primarios identificados.
- **Archivos:** `pie_in_situ_proporciones_totales.png`, `pie_in_situ_proporciones_totales_excluido.png`

---

## Paso 9: Exportación de Resultados

Para cada grupo funcional se exportan dos archivos CSV:

1. **`{grupo}_in_situ_timeseries.csv`**: Matriz completa mes × año con conteos.
2. **`{grupo}_in_situ_monthly_stats.csv`**: Estadísticas mensuales agregadas.

Todos los archivos se guardan en `resultados_series_tiempo/` y las figuras en `resultados_series_tiempo/figuras_primarios/`.

---

## Resumen del Pipeline

```
taxonomy_corrected_edna.csv
        │
        ▼
   [1] Carga CSV (190,732 registros × 22 columnas)
        │
        ▼
   [2] Conversión de fechas (serial Excel → datetime)
        │
        ▼
   [3] Filtrado temporal (2000–2024) → ~188,406 registros
        │
        ▼
   [4] Clasificación taxonómica → 8 grupos funcionales
        │
        ├──► Diatomeas       (Bacillariophyta)
        ├──► Dinoflagelados  (Dinophyta, Myzozoa)
        ├──► Clorofitas      (Chlorophyta)
        ├──► Cianobacterias  (Cyanobacteria)
        ├──► Haptofitas      (Haptophyta)
        ├──► Otros Eucariotas(Eukaryota)
        ├──► Protozoa        (Protozoa, Amoebozoa)
        └──► Otros           (no clasificados como PP)
        │
        ▼
   [5] Matriz de frecuencia mensual (12 meses × 25 años) por grupo
        │
        ▼
   [6] Estadísticas mensuales agregadas
        │
        ▼
   [7] Serie de tiempo lineal con gaps naturales
        │
        ▼
   [8] Visualizaciones (series, heatmaps, barras, pasteles)
        │
        ▼
   [9] Exportación CSV + PNG
```

---

## Consideraciones y Limitaciones

1. **Sesgo temporal de muestreo**: Los datos eDNA no cubren uniformemente todos los meses de todos los años. La cobertura es más densa entre 2017 y 2023, con pocos o ningún dato antes de 2017.

2. **Frecuencia vs Abundancia**: La métrica principal es la frecuencia de ocurrencia (conteo de registros), no la abundancia. La abundancia registrada es mayoritariamente 0 (presencia/ausencia), con solo ~6.8% de registros con valores >0.

3. **Profundidad de muestreo**: El muestreo se realizó en tres capas (Superficial: 1–26 m, Intermedia: 35–140 m, Profunda: 220–1000 m). Los datos satelitales solo miden la capa superficial del océano, por lo que las comparaciones directas deben considerar esta diferencia.

4. **Clasificación taxonómica**: La clasificación en grupos funcionales se basa en coincidencias exactas de texto en las columnas `phylum`, `class` y `kingdom`. Organismos con taxonomía incompleta o nombres no contemplados se asignan al grupo "Otros".

5. **Representatividad geográfica**: Las muestras eDNA son puntuales en el Golfo de California, mientras que los datos satelitales son promedios espaciales sobre toda la región.

---

## Scripts Relacionados

| Script | Función |
|--------|---------|
| `analisis_series_tiempo_in_situ_primarios.py` | Pipeline principal descrito en este documento |
| `plot_satellite_vs_insitu_timeseries.py` | Comparación de series satelitales vs in situ |
| `analisis_profundidad_abundancia.py` | Análisis por capa de profundidad y abundancia |
| `plot_pft_monthly_timeseries.py` | Series de tiempo satelitales con índices climáticos |
