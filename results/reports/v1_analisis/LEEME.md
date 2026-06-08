# 📊 Reporte de Análisis de Producción Primaria - Golfo de California (2000-2024)

## 📁 Estructura del Proyecto

```
reporte_analisis/
├── index.html              # Archivo principal del reporte (ABRIR ESTE ARCHIVO)
├── LEEME.md                # Este archivo
└── figuras/                # Carpeta con todas las figuras (52 elementos)
    ├── *.html              # Gráficos interactivos Plotly (6 archivos)
    └── *.png               # Mapas y análisis estacionales (46 imágenes)
```

## 🎯 Características del Reporte

### ✨ Funcionalidades Interactivas

#### 1. **Gráficos Plotly Interactivos** 📈
   - **Sección de Composición**: 6 gráficos interactivos con Plotly
     - Gráficos de pastel (pie charts) clickeables
     - Series temporales con zoom y hover
     - Gráficos de área acumulada
   - **Características**:
     - Haz clic en la leyenda para mostrar/ocultar datos
     - Usa el zoom con el mouse para explorar períodos específicos
     - Hover para ver valores exactos
     - Descarga como PNG desde el gráfico

#### 2. **Carrusel con Viñetas** 🔘
   - Otras secciones (Diferencias Quinquenales, Estacional, etc.)
   - Navega entre figuras usando botones
   - Haz clic en viñetas para saltar a figura específica
   - Contador visual

#### 3. **Observaciones Editables** ✍️
   - Cada sección tiene un área de observaciones (fondo rosa)
   - Haz clic para editar las viñetas
   - Los cambios se guardan automáticamente
   - Agrupa observaciones por tipo de análisis

### 📊 Secciones del Reporte

#### 1. **Composición de Fitoplancton** (6 gráficos Plotly interactivos)
- ✅ **Gráfico de Pastel - Especies**: Distribución de 6 especies
- ✅ **Gráfico de Pastel - Tamaño**: Distribución por 3 clases de tamaño
- ✅ **Series Temporales - Especies**: Evolución 2000-2024 interactiva
- ✅ **Series Temporales - Tamaño**: Evolución 2000-2024 interactiva
- ✅ **Área Acumulada - Especies**: Composición acumulada
- ✅ **Área Acumulada - Tamaño**: Composición acumulada por tamaño

#### 2. **Diferencias Quinquenales** (10 figuras PNG)
- Mapas comparativos 2020-2024 vs períodos anteriores
- Una figura por variable (10 variables diferentes)
- Uso de color divergente (rojo = aumento, azul = disminución)
- Navegación por carrusel

#### 3. **Análisis Estacional** (10 figuras PNG)
- Patrones de variación estacional para cada variable
- Identificación de meses de mayor/menor concentración
- Navegación por carrusel

#### 4. **Series Temporales con Índices Climáticos** (Vacío - por procesar)
- Evolución temporal de fitoplancton con superposición de:
  - **NIÑO 3.4** (naranja): Índice de temperatura
  - **MEI** (púrpura punteado): Multivariate ENSO Index
  - **PDO** (gris punteado): Pacific Decadal Oscillation
- Útil para identificar correlaciones con fenómenos climáticos

#### 5. **Patrones Latitud-Tiempo** (Vacío - por procesar)
- Heatmaps de concentración promediados por latitud
- Mostrar patrones espaciales a lo largo del tiempo

#### 6. **Mapas Quinquenales** (Vacío - por procesar)
- Mapas de concentración para cada período de 5 años
- Visualización geográfica de la distribución

## 🚀 Cómo Usar el Reporte

### Abrir el Reporte
1. Ve a: `/home/atlantis/atlantis_primary_producton/ocean_primary_production/reporte_analisis/`
2. Abre `index.html` en tu navegador favorito (Chrome, Firefox, Safari, Edge)

### Explorar Gráficos Plotly (Composición)
1. En la sección de composición encontrarás gráficos interactivos
2. **Haz clic en la leyenda** para mostrar/ocultar series específicas
3. **Zoom**: Haz clic y arrastra en el gráfico para hacer zoom
4. **Hover**: Pasa el mouse sobre los datos para ver valores exactos
5. **Descargar**: Haz clic en el ícono de cámara para descargar como PNG

### Navegar Carrusel (Otras Secciones)
1. Usa los botones "Anterior" y "Siguiente"
2. O haz clic directamente en los puntos/viñetas
3. El contador te muestra tu posición actual

### Editar Observaciones
1. Haz clic en el área de observaciones (fondo rosa)
2. La caja se activará para edición
3. Edita o agrega viñetas:
   ```
   • Mi observación 1
   • Mi observación 2
   • Mi observación 3
   ```
4. Los cambios se guardan automáticamente

### Guardar tu Trabajo
- **En el navegador**: Los cambios se guardan automáticamente
- **Descargar actualizado**: 
  - Chrome/Firefox: Ctrl+S o Cmd+S
  - Menú: File > Save Page As (guarda HTML + figuras)

## 📈 Datos Procesados

### Archivo de Estadísticas
- **Ubicación**: `data/pft_monthly_statistics.nc`
- **Tamaño**: 127 KB (vs 82 GB del original)
- **Compresión**: 99.99%
- **Contenido**: Estadísticas mensuales (media, std, min, max) para 10 variables
- **Período**: Enero 2000 - Diciembre 2024 (300 meses)

### Variables Analizadas
1. **CHL** - Clorofila-a Total
2. **DIATO** - Diatomeas
3. **DINO** - Dinoflagelados
4. **GREEN** - Algas Verdes
5. **HAPTO** - Haptófitos
6. **MICRO** - Microfitoplancton (>20 μm)
7. **NANO** - Nanofitoplancton (2-20 μm)
8. **PICO** - Picofitoplancton (<2 μm)
9. **PROCHLO** - Proclorococcus
10. **PROKAR** - Procariontes

## 🔧 Scripts Disponibles

### `scripts/preprocess_pft_data.py`
- Procesa el dataset completo variable por variable
- Genera estadísticas mensuales comprimidas
- Ahorra 99.99% de espacio

### `scripts/plot_composition_percentages.py`
- Genera figuras PNG de composición porcentual
- Usa el archivo de estadísticas (bajo consumo de memoria)
- Crea 6 figuras PNG (obsoletas, reemplazadas por Plotly)

### `scripts/generate_plotly_charts.py` ⭐ NUEVO
- Genera 6 gráficos interactivos con Plotly
- Pie charts, series temporales, áreas acumuladas
- HTML embebido, bajo tamaño de archivo
- Interactividad completa (zoom, hover, leyendas)

### `scripts/generate_html_report_spanish.py`
- Genera el reporte HTML con características interactivas
- Detecta sección de composición para usar Plotly
- Mantiene carrusel para otras secciones
- Copia figuras a la carpeta del reporte

## 💡 Ventajas de Plotly para Composición

✨ **Mejor experiencia de usuario**:
- Exploración interactiva sin recargar
- Zoom temporal para análisis detallado
- Leyendas clickeables para filtrar datos
- Información al pasar el mouse

📉 **Eficiencia**:
- Archivos mucho más pequeños que PNG
- HTML embebido, sin imágenes externas
- Carga rápida en el navegador

🎨 **Funcionalidad**:
- Comparación fácil de múltiples series
- Exportación directa a PNG desde el gráfico
- Responsive en móviles
- Compatible con todos los navegadores modernos

## 🌐 Compatibilidad

- ✅ Chrome/Chromium 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+
- ✅ Navegadores móviles (responsive)

## 📊 Tecnologías Utilizadas

- **HTML/CSS**: Estructura y estilos del reporte
- **JavaScript**: Navegación y interactividad
- **Plotly.js**: Gráficos interactivos
- **Bootstrap 5**: Diseño responsivo
- **Python**: Generación de datos y gráficos
- **Xarray**: Procesamiento de datos NetCDF
- **Pandas**: Manipulación de datos
- **Matplotlib**: Figuras estáticas (PNG)

## 📝 Metadata del Reporte

- **Área de estudio**: Golfo de California
- **Período**: 2000-2024 (25 años)
- **Resolución temporal**: Mensual
- **Resolución espacial**: ~4 km (datos MODIS)
- **Fuente**: Copernicus Marine Service (CMEMS)
- **Total de figuras**: 52 (6 Plotly + 46 PNG)
- **Tamaño del reporte**: ~28 MB

---

**Última actualización**: 20 de Enero de 2026
**Versión**: 2.0 (Con Plotly interactivo)
