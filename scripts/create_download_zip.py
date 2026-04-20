#!/usr/bin/env python3
"""
Script para crear ZIP de descarga con reporte completo filtrado.
Incluye: HTML interactivo, figuras, análisis cuantitativos, metodología.

Fecha: 3 de Marzo de 2026
"""

import os
import zipfile
import json
from datetime import datetime
from pathlib import Path

# Configuración de rutas
SCRIPTS_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPTS_DIR.parent  # Nautical_primary_producton/ocean_primary_production
DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = DATA_DIR / "figures"

# Archivos a incluir en el ZIP
ZIP_FILENAME = "reporte_completo_golfo_california_2026_filtrado.zip"
ZIP_PATH = FIGURES_DIR / ZIP_FILENAME

# Archivos que incluir
FILES_TO_INCLUDE = [
    # Reporte principal
    (FIGURES_DIR / "REPORTE_COMPLETO_FILTRADO.html", "REPORTE_COMPLETO_FILTRADO.html"),
    
    # Datos cuantitativos
    (FIGURES_DIR / "reporte_analisis_numerico.json", "reporte_analisis_numerico.json"),
    (FIGURES_DIR / "REPORTE_ANALISIS_CUANTITATIVO.md", "REPORTE_ANALISIS_CUANTITATIVO.md"),
    
    # Metodología
    (PROJECT_ROOT / "METODOLOGIA_ANALISIS.md", "METODOLOGIA_ANALISIS.md"),
    
    # Guías de uso
    (FIGURES_DIR / "GUIA_USO_REPORTES.md", "GUIA_USO_REPORTES.md") if (FIGURES_DIR / "GUIA_USO_REPORTES.md").exists() else None,
]

# Carpetas que incluir (recursivamente)
FOLDERS_TO_INCLUDE = [
    # Figuras filtradas
    (FIGURES_DIR / "fig_filt", "fig_filt"),
]

def create_readme():
    """Crea un README.txt con instrucciones de uso."""
    readme_content = """╔════════════════════════════════════════════════════════════════════════════╗
║                    REPORTE COMPLETO - GOLFO DE CALIFORNIA                    ║
║              Análisis de Producción Primaria del Fitoplancton 2000-2024       ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 CONTENIDO DEL ARCHIVO

Este ZIP contiene un análisis científico exhaustivo de 10 tipos funcionales de 
fitoplancton en el Golfo de California durante 25 años (2000-2024), con filtrado 
espacial a 13,928 puntos dentro del polígono del Golfo.

📁 ESTRUCTURA DEL ARCHIVO

├── REPORTE_COMPLETO_FILTRADO.html    ← ABRIR ESTE ARCHIVO EN UN NAVEGADOR WEB
│   └── Reporte interactivo con:
│       • 10 secciones de variables (CHL, DIATO, DINO, etc.)
│       • 40 figuras de visualización (4 tipos × 10 variables)
│       • Tablas de estadísticas cuantitativas
│       • Correlaciones con índices climáticos (MEI, NINO3.4, PDO)
│       • Resumen ejecutivo con rankings
│
├── fig_filt/                          ← Todos los archivos PNG individuales
│   ├── CHL_mean_map.png
│   ├── CHL_quinquennial_maps.png
│   ├── CHL_quinquennial_diff_maps.png
│   ├── CHL_timeseries_analysis.png
│   ├── ... (40 archivos total - 4 por variable)
│
├── reporte_analisis_numerico.json     ← Datos cuantitativos (formato máquina/JSON)
│   └── Estructura jerárquica con:
│       • Estadísticas espaciales (media, mediana, std, etc.)
│       • Comparaciones quinquenales (5 períodos)
│       • Anomalías respectivas a 2020-2024
│       • Tendencias lineales (pendiente, R², p-valor)
│       • Correlaciones climáticas con 25 desfases temporales
│
├── REPORTE_ANALISIS_CUANTITATIVO.md   ← Tablas y análisis en formato Markdown
│   └── Salida legible para humanos con interpretaciones
│
├── METODOLOGIA_ANALISIS.md            ← Descripción técnica completa
│   └── Incluye:
│       • Descripción de datos de entrada
│       • Proceso de filtrado espacial (punto-en-polígono)
│       • Metodología de cada análisis realizado
│       • Validación de calidad de datos
│       • Software y dependencias utilizadas
│
├── GUIA_USO_REPORTES.md              ← Instrucciones para interpretar datos
│
└── README.txt                         ← Este archivo


🚀 CÓMO USAR

1️⃣  OPCIÓN RÁPIDA (Recomendada)
    • Extrae el ZIP donde desees
    • Abre "REPORTE_COMPLETO_FILTRADO.html" en tu navegador
    • Haz clic en las pestañas/links para navegar el contenido
    • Usa el botón "Imprimir/PDF" para guardar como PDF

2️⃣  OPCIÓN TÉCNICA (Análisis Profundo)
    • Lee "METODOLOGIA_ANALISIS.md" para entender procesos
    • Abre "reporte_analisis_numerico.json" en un editor JSON o Python:
      ```python
      import json
      with open('reporte_analisis_numerico.json') as f:
          data = json.load(f)
      # Acceso a variables: data['variables']['CHL']['map_statistics']
      ```
    • Consulta las figuras individuales en la carpeta fig_filt/

3️⃣  OPCIÓN MARKDOWN (Documentación)
    • "REPORTE_ANALISIS_CUANTITATIVO.md" - Tablas y análisis
    • "GUIA_USO_REPORTES.md" - Explicación de estructura
    • "METODOLOGIA_ANALISIS.md" - Detalles técnicos


📊 RESUMEN DE DATOS

┌─────────────────────────────────────────────────────────────────────────────┐
│ ZONA DE ESTUDIO         │ Golfo de California, Polígono Shapefile           │
│ PUNTOS GEOGRAFICOS      │ 13,928 (8.96% del grid global)                    │
│ PERÍODO                 │ Enero 2000 - Diciembre 2024 (300 meses)           │
│ VARIABLES ANALIZADAS    │ 10 tipos funcionales de fitoplancton (PFTs)       │
│ RESOLUCIÓN ESPACIAL     │ 4 km (MODIS Aqua)                                 │
│ RANGO GEOGRAFICO        │ Lat: 20.40°N-31.81°N, Lon: 114.85°W-105.23°W     │
│ ÍNDICES CLIMÁTICOS      │ MEI, NINO3.4, PDO (con desfases hasta ±12 meses)  │
│ ANÁLISIS EFECTUADOS     │ Estadísticos, quinquenales, anomalías, tendencias │
│ FIGURAS GENERADAS       │ 40 PNG (mapas, series temporales, comparativas)    │
│ TAMAÑO DEL REPORTE      │ HTML: 146.3 KB, JSON: 66 KB, PNG: ~1.6 MB        │
└─────────────────────────────────────────────────────────────────────────────┘


💡 VARIABLES ANALIZADAS (10 PFTs)

1. CHL          - Clorofila-a Total (indicador de biomasa fitoplanctónica)
2. DIATO        - Diatomeas (típicamente muy productivas)
3. DINO         - Dinoflagelados (sensibles a cambios de nutrientes)
4. GREEN        - Algas Verdes (abundantes en aguas mesotrofas)
5. HAPTO        - Haptófitas (importantes en regiones subtropicales)
6. MICRO        - Microfitoplancton >20 μm (típicamente diatomeas)
7. NANO         - Nanofitoplancton 2-20 μm (grupo diverso)
8. PICO         - Picofitoplancton <2 μm (cianobacterias principalmente)
9. PROCHLO      - Prochlorococcus (dominante en aguas oligotróficas)
10. PROKAR      - Procariotas (bacterias marinas fotosintetizantes)


🔬 ANÁLISIS INCLUIDOS

✓ ESTADÍSTICAS ESPACIALES
  • Media, mediana, desviación estándar, mín, máx
  • Percentiles (5, 25, 75, 95)
  • Por todo el período 2000-2024

✓ COMPARATIVAS QUINQUENALES
  • Período 1: 2000-2004
  • Período 2: 2005-2009
  • Período 3: 2010-2014
  • Período 4: 2015-2019
  • Período 5: 2020-2024 (referencia)
  
✓ ANOMALÍAS DECADALES
  • Diferencia absoluta respecto a 2020-2024
  • Cambio porcentual respecto a período más reciente
  
✓ TENDENCIAS LINEALES
  • Pendiente de regresión (cambio por mes y por año)
  • Coeficiente R² (ajuste del modelo)
  • p-valor (significancia estadística)
  
✓ CORRELACIONES CLIMÁTICAS
  • Índices: MEI, NINO3.4, PDO
  • Desfases: -12 a +12 meses
  • Significancia: Test de permutación (1000 iteraciones)
  • Interpretación de lags para efectos predictivos


🌐 REQUISITOS PARA ABRIR

OPCIÓN 1: Navegador Web (Recomendado)
  • Chrome, Firefox, Safari, Edge (cualquier navegador moderno)
  • NO requiere conexión a Internet
  • Compatible con móvil, tablet y desktop

OPCIÓN 2: Editor de Texto
  • Cualquier editor de texto (VS Code, Sublime, Gedit, Notepad++)
  • Para ver HTML source: usa "Ver código fuente" en navegador

OPCIÓN 3: Python (Para análisis avanzado)
  • Python 3.7+
  • Librerías: json, pandas, numpy
  ```
  import json
  with open('reporte_analisis_numerico.json') as f:
      data = json.load(f)
  ```


📝 INTERPRETACIÓN RÁPIDA

MAPAS DE MEDIA (primera figura de cada variable):
  → Muestra dónde está concentrado cada tipo de fitoplancton
  → Colores oscuros = concentraciones altas
  → Colores claros = concentraciones bajas

MAPAS QUINQUENALES (segunda figura):
  → Comparación de 5 períodos de 5 años cada uno
  → Permite ver evolución decadal
  → Busca áreas donde el color cambia a través del tiempo

MAPAS DE ANOMALÍAS (tercera figura):
  → Rojo = más abundante que 2020-2024
  → Azul = menos abundante que 2020-2024
  → Blanco = aproximadamente igual

SERIES TEMPORALES (cuarta figura):
  → Línea azul: promedio móvil (12 meses) - elimina ruido
  → Línea roja: tendencia a largo plazo (25 años)
  → Bandas grises: variación estacional típica
  → Interpretación: ¿tendencia al alza o baja?


❓ PREGUNTAS FRECUENTES

P: ¿Puedo compartir este ZIP?
R: Sí. El análisis usa datos públicos (MODIS, NOAA, INEGI).
   Se recomienda mantener este README.txt en la distribución.

P: ¿Qué significan los valores en el JSON?
R: Ver "GUIA_USO_REPORTES.md" para estructura completa.
   Unidades típicas: mg m⁻³ (concentración en agua de mar)

P: ¿Cuál es la precisión de los datos?
R: MODIS tiene incertidumbre típica de ±35% para clorofila.
   Se reportan valores medios previo promediar 300-13,928 datos.

P: ¿Cómo descargo solo algunas figuras?
R: Abre la carpeta fig_filt/ y descarga las PNG individuales
   que necesites. Nombres autoexplicativos.

P: ¿Puedo importar esto en ArcGIS/QGIS?
R: Los PNG son imágenes estándar (sí).
   Los datos NetCDF originales pueden ser importados (requiere
   el archivo pft_monthly_statistics.nc original).

P: ¿Se incluyen datos de incertidumbre?
R: No en el HTML/PDF, pero sí en el archivo JSON original
   ("_std" = desviación estándar de cada métrica)


📞 INFORMACIÓN TÉCNICA

FECHA DE GENERACIÓN: 3 de Marzo de 2026
VERSIÓN DEL ANÁLISIS: 1.0
AUTOR: Análisis Automatizado con Python
LENGUAJE: Python 3.10.12 + librerías científicas
VALIDACIÓN: Todos los datos filtrados geográficamente al Golfo de California

ARCHIVOS ORIGINALES (si necesitas procesamiento adicional):
  • pft_golfo_california_2000_2024.nc (81 GB - dataset completo)
  • pft_monthly_statistics.nc (127 KB - datos agregados, usado para este análisis)
  • Shapefiles del Golfo de California (regionmarinamx.shp)
  • Índices climáticos CSV (mei.csv, nino34.csv, pdo.csv)

REPRODUCIBILIDAD:
  Todos los scripts utilizados están documentados en:
  - ocean_primary_production/scripts/ (original repository)
  - METODOLOGIA_ANALISIS.md (punto de partida para ejecutar análisis)


📧 CITAS CIENTÍFICAS

Si utilizas este análisis en investigación, cita:

MODIS Aqua/Phytoplankton Functional Types:
"MODIS Aqua Ocean Color Data", NASA OBDAAC, 2000-2024

Índices Climáticos:
"NOAA Climate Indices: MEI, ONI, and PDO", NOAA PSL

Golfo de California:
Incluye límites administrativos y oceanográficos del INE (Instituto Nacional
de Ecología, México)


═════════════════════════════════════════════════════════════════════════════

¡Gracias por usar este reporte!

Para preguntas o sugerencias, consulta la documentación incluida.

═════════════════════════════════════════════════════════════════════════════
"""
    return readme_content


def create_zip():
    """Crea el archivo ZIP con todos los contenidos."""
    
    print("\n" + "="*80)
    print("CREANDO ZIP DE DESCARGA".center(80))
    print("="*80 + "\n")
    
    # Crear el archivo ZIP
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        
        # Agregar archivos individuales
        print("📄 Agregando archivos...")
        for file_info in FILES_TO_INCLUDE:
            if file_info is None:
                continue
            file_path, arcname = file_info
            if file_path.exists():
                zipf.write(file_path, arcname)
                file_size = file_path.stat().st_size / 1024  # KB
                print(f"   ✓ {arcname:<50} ({file_size:>8.1f} KB)")
            else:
                print(f"   ⚠ {arcname:<50} (NO ENCONTRADO)")
        
        # Agregar carpeta de figuras
        print("\n📁 Agregando carpeta de figuras...")
        figures_count = 0
        for folder_info in FOLDERS_TO_INCLUDE:
            folder_path, arcname = folder_info
            if folder_path.exists():
                for file_path in folder_path.glob("*.png"):
                    zipf.write(file_path, f"{arcname}/{file_path.name}")
                    figures_count += 1
                print(f"   ✓ {arcname:<50} ({figures_count} figuras)")
            else:
                print(f"   ⚠ {arcname:<50} (CARPETA NO ENCONTRADA)")
        
        # Agregar README.txt
        print("\n📋 Agregando README.txt...")
        readme_content = create_readme()
        zipf.writestr("README.txt", readme_content)
        print(f"   ✓ README.txt")
        
        # Información del ZIP
        print("\n📊 Contenido del ZIP:")
        zipf.printdir()
        
        # Obtener tamaño total
        zip_size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
        print(f"\n✅ ZIP creado exitosamente!")
        print(f"   Ruta: {ZIP_PATH}")
        print(f"   Tamaño: {zip_size_mb:.2f} MB")
        print(f"   Número de archivos: {len(zipf.namelist())}")
        
        # Listar contenido
        print(f"\n📦 Contenido del archivo:")
        for info in sorted(zipf.filelist, key=lambda x: x.filename):
            file_size = info.file_size / 1024 if info.file_size > 0 else 0
            if file_size > 100:  # Solo mostrar si es > 100 KB
                print(f"   • {info.filename:<55} ({file_size:>8.1f} KB)")
            elif file_size > 0:
                print(f"   • {info.filename:<55} ({file_size:>8.1f} KB)")
            else:
                print(f"   • {info.filename:<55} (carpeta)")
    
    print("\n" + "="*80)
    print("✨ ¿LISTO PARA DESCARGAR Y COMPARTIR? ✨".center(80))
    print("="*80)
    print(f"\nUbicación: {ZIP_PATH}")
    print(f"Tamaño: {zip_size_mb:.2f} MB")
    print(f"Descarga este archivo para compartir el análisis completo.")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        create_zip()
    except Exception as e:
        print(f"❌ Error al crear ZIP: {e}")
        import traceback
        traceback.print_exc()
