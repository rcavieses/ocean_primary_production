"""
Análisis de Series de Tiempo para Productores Primarios
Analiza frecuencia de registros por grupo de especies de productores primarios
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from openpyxl.utils.datetime import from_excel
import os
from pathlib import Path

# Argumentos
parser = argparse.ArgumentParser(description='Series de tiempo de productores primarios in situ')
parser.add_argument('--taxonomy', choices=['v1', 'v2'], default='v2',
                    help='Versión del archivo de taxonomía: v1=taxonomy_corrected_edna.csv, v2=taxonomy_corrected_edna_2.csv')
args = parser.parse_args()

TAXONOMY_VERSION = args.taxonomy
TAXONOMY_FILENAME = 'taxonomy_corrected_edna.csv' if TAXONOMY_VERSION == 'v1' else 'taxonomy_corrected_edna_2.csv'

# Configuración
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR    = str(BASE_DIR / 'data')
OUTPUT_DIR  = str(BASE_DIR / 'results' / 'insitu' / f'edna_{TAXONOMY_VERSION}' / 'series_tiempo')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Crear directorio para figuras
FIGURES_DIR = os.path.join(OUTPUT_DIR, 'figuras_primarios')
os.makedirs(FIGURES_DIR, exist_ok=True)

print(f"[series_tiempo_primarios] Taxonomía: {TAXONOMY_FILENAME}")
print(f"[series_tiempo_primarios] Output:    {OUTPUT_DIR}")

def excel_date_to_datetime(excel_date):
    """Convierte número serial de Excel a datetime"""
    if pd.isna(excel_date) or excel_date == '':
        return pd.NaT
    try:
        if isinstance(excel_date, str):
            if '/' in excel_date:
                return pd.to_datetime(excel_date, format='%d/%m/%Y', errors='coerce')
            else:
                excel_date = float(excel_date)
        excel_epoch = datetime(1899, 12, 30)
        return excel_epoch + pd.Timedelta(days=int(excel_date))
    except:
        return pd.NaT

def normalize_schema(df, version):
    """Normaliza columnas al esquema común independientemente de la versión del archivo."""
    if version == 'v1':
        df['date'] = df['Collected date year'].apply(excel_date_to_datetime)
    else:
        # v2 ya tiene columna 'date' en formato ISO YYYY-MM-DD
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df

print("Cargando datos de taxonomía...")
df = pd.read_csv(os.path.join(DATA_DIR, 'insitu', TAXONOMY_FILENAME), low_memory=False)

print(f"Registros totales: {len(df)}")

print("Procesando fechas...")
df = normalize_schema(df, TAXONOMY_VERSION)

# Filtrar registros sin fecha válida
df = df.dropna(subset=['date'])
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month

# Filtrar rango 2000-2024
df = df[(df['year'] >= 2000) & (df['year'] <= 2024)].copy()

print(f"Registros con fecha válida (2000-2024): {len(df)}")

# Identificar productores primarios por grupo taxonómico
# Grupos comunes de productores primarios marinos
PRIMARY_PRODUCERS = {
    'Diatomeas': ['Bacillariophyta', 'Diatomophyceae', 'Fragilariophyceae', 'Bacillariophyceae'],
    'Dinoflagelados': ['Dinophyta', 'Dinophyceae'],
    'Clorofitas': ['Chlorophyta', 'Chlorophyceae', 'Ulvophyceae'],
    'Cianobacterias': ['Cyanobacteria', 'Oxyphotobacteria'],
    'Haptofitas': ['Haptophyta', 'Prymnesiophyceae', 'Coccolithophyceae'],
    'Otros Eucariotas': ['Eukaryota'],
    'Protozoa': ['Protozoa', 'Discosea'],
}

def classify_producer(row):
    """Clasifica el organismo en grupo de productor primario"""
    phylum = str(row.get('phylum', '')).strip() if pd.notna(row.get('phylum')) else ''
    class_tax = str(row.get('class', '')).strip() if pd.notna(row.get('class')) else ''
    kingdom = str(row.get('kingdom', '')).strip() if pd.notna(row.get('kingdom')) else ''
    
    # Buscar coincidencias en phylum
    for group, values in PRIMARY_PRODUCERS.items():
        if phylum in values or class_tax in values or kingdom in values:
            return group
    
    # Si tiene photosynthetic en la descripción
    if kingdom == 'Protozoa' or phylum == 'Amoebozoa':
        return 'Protozoa'
    
    return 'Otros'

print("Clasificando organismos...")
df['grupo_primario'] = df.apply(classify_producer, axis=1)

# Conteos por grupo
print("\nOrganismos por grupo:")
for grupo in sorted(df['grupo_primario'].unique()):
    count = len(df[df['grupo_primario'] == grupo])
    print(f"  {grupo}: {count}")

# Crear matriz de series de tiempo para cada grupo
grupos = sorted(df['grupo_primario'].unique())

# Meses en español
meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

años = list(range(2000, 2025))

print(f"\nGenerando series de tiempo mensuales ({len(grupos)} grupos)...")

# Almacenar series de tiempo para cada grupo
series_dict = {}

for grupo in grupos:
    df_grupo = df[df['grupo_primario'] == grupo]
    
    # Crear matriz vacía con NaN
    matriz = pd.DataFrame(
        np.nan,
        index=range(1, 13),  # 12 meses
        columns=años
    )
    
    # Llenar con conteos
    for year in años:
        for month in range(1, 13):
            count = len(df_grupo[(df_grupo['year'] == year) & (df_grupo['month'] == month)])
            if count > 0:
                matriz.loc[month, year] = count
    
    # Convertir índice de números a nombres de meses
    matriz.index = meses
    
    series_dict[grupo] = matriz
    
    # Guardar CSV
    filename = f"{grupo.lower().replace(' ', '_')}_in_situ_timeseries.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)
    matriz.to_csv(filepath)
    print(f"  ✓ {grupo}: {filepath}")

# Crear análisis de estadísticas mensuales
print("\nGenerando estadísticas mensuales...")

for grupo in grupos:
    df_grupo = df[df['grupo_primario'] == grupo]
    
    # Estadísticas por mes (promedio entre años)
    stats_mensuales = []
    for month in range(1, 13):
        registros = df_grupo[df_grupo['month'] == month]
        años_con_datos = registros['year'].nunique()
        total_registros = len(registros)
        
        stats_mensuales.append({
            'Mes': meses[month - 1],
            'Total_Registros': total_registros,
            'Años_con_Datos': años_con_datos,
            'Promedio_por_Año': total_registros / (2025 - 2000) if total_registros > 0 else 0
        })
    
    stats_df = pd.DataFrame(stats_mensuales)
    filename = f"{grupo.lower().replace(' ', '_')}_in_situ_monthly_stats.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)
    stats_df.to_csv(filepath, index=False)
    print(f"  ✓ {grupo} (stats): {filepath}")

# Crear gráficas
print("\nGenerando gráficas...")

fig, axes = plt.subplots(len(grupos), 1, figsize=(16, 3 * len(grupos)))

if len(grupos) == 1:
    axes = [axes]

for idx, grupo in enumerate(grupos):
    matriz = series_dict[grupo]
    
    # Preparar datos para ploteo
    # Convertir matriz en series de tiempo mensual
    tiempo = []
    valores = []
    
    for year in años:
        for month in range(1, 13):
            if pd.notna(matriz.loc[meses[month-1], year]):
                # Usar fecha específica para el eje X
                fecha = pd.Timestamp(year, month, 15)
                tiempo.append(fecha)
                valores.append(matriz.loc[meses[month-1], year])
    
    if len(tiempo) > 0:
        ax = axes[idx]
        ax.plot(tiempo, valores, marker='o', markersize=4, linewidth=1.5, alpha=0.7)
        ax.fill_between(tiempo, valores, alpha=0.3)
        ax.set_title(f'Serie de Tiempo: {grupo} (2000-2024)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Año-Mes', fontsize=10)
        ax.set_ylabel('Registros Mensuales', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        
        # Agregar estadísticas
        total = sum(valores)
        promedio = np.mean(valores)
        max_val = np.max(valores)
        texto_stats = f'Total: {int(total)} | Promedio: {promedio:.1f} | Máximo: {int(max_val)}'
        ax.text(0.02, 0.98, texto_stats, transform=ax.transAxes, 
                verticalalignment='top', fontsize=9, bbox=dict(boxstyle='round', 
                facecolor='wheat', alpha=0.5))

plt.tight_layout()
filepath = os.path.join(FIGURES_DIR, 'series_tiempo_in_situ_primarios_completa.png')
plt.savefig(filepath, dpi=300, bbox_inches='tight')
print(f"  ✓ Serie temporal completa: {filepath}")
plt.close()

# Crear gráfica de comparación entre grupos
print("\nGenerando gráfica comparativa...")

fig, ax = plt.subplots(figsize=(16, 8))

for grupo in grupos:
    df_grupo = df[df['grupo_primario'] == grupo]
    
    # Crear matriz de fechas y valores para identificar gaps
    fecha_valor = {}  # {fecha: valor}
    
    for year in años:
        for month in range(1, 13):
            registros = df_grupo[(df_grupo['year'] == year) & (df_grupo['month'] == month)]
            if len(registros) > 0:
                fecha = pd.Timestamp(year, month, 15)
                fecha_valor[fecha] = len(registros)
    
    if len(fecha_valor) > 0:
        # Ordenar por fecha
        fechas_ordenadas = sorted(fecha_valor.keys())
        valores_ordenados = [fecha_valor[f] for f in fechas_ordenadas]
        
        # Obtener color para este grupo
        color = None
        
        # Plotear todos los puntos
        puntos = ax.plot(fechas_ordenadas, valores_ordenados, marker='o', markersize=4, 
                linestyle='none', label=grupo, alpha=0.7)
        color = puntos[0].get_color()
        
        # Conectar puntos considerando si son consecutivos o no
        # Considerar dos puntos como consecutivos si están a menos de 2 meses de diferencia
        for i in range(len(fechas_ordenadas) - 1):
            fecha_actual = fechas_ordenadas[i]
            fecha_siguiente = fechas_ordenadas[i + 1]
            
            # Calcular días entre fechas
            dias_diferencia = (fecha_siguiente - fecha_actual).days
            
            # Si están dentro de 2 meses (~60 días), línea sólida; si no, línea punteada
            if dias_diferencia <= 60:
                # Puntos consecutivos: línea sólida
                ax.plot([fecha_actual, fecha_siguiente], 
                       [valores_ordenados[i], valores_ordenados[i+1]],
                       linestyle='-', linewidth=1.5, alpha=0.7, color=color)
            else:
                # Puntos NO consecutivos: línea punteada
                ax.plot([fecha_actual, fecha_siguiente], 
                       [valores_ordenados[i], valores_ordenados[i+1]],
                       linestyle='--', linewidth=1.5, alpha=0.7, color=color)

ax.set_title('Comparación de Registros por Grupo de Productor Primario (2000-2024)', 
             fontsize=14, fontweight='bold')
ax.set_xlabel('Año-Mes', fontsize=11)
ax.set_ylabel('Registros Mensuales', fontsize=11)
ax.legend(loc='best', fontsize=10)
ax.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

filepath = os.path.join(FIGURES_DIR, 'in_situ_comparativa_grupos_primarios.png')
plt.savefig(filepath, dpi=300, bbox_inches='tight')
print(f"  ✓ Gráfica comparativa: {filepath}")
plt.close()

# Crear heatmap de actividad mensual por año
print("\nGenerando heatmaps...")

for grupo in grupos:
    matriz = series_dict[grupo]
    
    fig, ax = plt.subplots(figsize=(18, 6))
    
    # Crear heatmap
    sns.heatmap(matriz, annot=True, fmt='.0f', cmap='YlOrRd', 
                cbar_kws={'label': 'Registros'}, ax=ax, 
                linewidths=0.5, linecolor='gray')
    
    ax.set_title(f'Actividad Mensual de {grupo} (2000-2024)', 
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Año', fontsize=11)
    ax.set_ylabel('Mes', fontsize=11)
    
    plt.tight_layout()
    filename = f"heatmap_in_situ_{grupo.lower().replace(' ', '_')}.png"
    filepath = os.path.join(FIGURES_DIR, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"  ✓ Heatmap {grupo}: {filepath}")
    plt.close()

# Crear gráfica de barras apiladas (proporciones por año)
print("\nGenerando gráfica de barras apiladas...")

# Calcular registros por grupo y año
datos_por_año = {}
for year in años:
    datos_por_año[year] = {}
    for grupo in grupos:
        df_grupo = df[(df['grupo_primario'] == grupo) & (df['year'] == year)]
        datos_por_año[year][grupo] = len(df_grupo)

# Crear DataFrame para la gráfica
df_barras = pd.DataFrame(datos_por_año).T  # Transponer para tener años en filas
df_barras_pct = df_barras.div(df_barras.sum(axis=1), axis=0) * 100  # Convertir a porcentaje

fig, ax = plt.subplots(figsize=(16, 8))

# Crear barras apiladas
df_barras_pct.plot(kind='bar', stacked=True, ax=ax, width=0.8, 
                    colormap='tab10' if len(grupos) <= 10 else 'tab20')

ax.set_title('Proporción Porcentual de Grupos por Año (2000-2024)', 
             fontsize=14, fontweight='bold')
ax.set_xlabel('Año', fontsize=11)
ax.set_ylabel('Porcentaje (%)', fontsize=11)
ax.set_ylim([0, 100])
ax.legend(title='Grupo', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
ax.grid(axis='y', alpha=0.3)

# Rotar etiquetas del eje X
plt.xticks(rotation=45)
plt.tight_layout()

filepath = os.path.join(FIGURES_DIR, 'barras_apiladas_in_situ_proporciones_anuales.png')
plt.savefig(filepath, dpi=300, bbox_inches='tight')
print(f"  ✓ Gráfica barras apiladas: {filepath}")
plt.close()

# Crear gráfica de pie (proporciones totales)
print("\nGenerando gráfica de pie...")

# Calcular totales por grupo
totales_grupo = {}
for grupo in grupos:
    df_grupo = df[df['grupo_primario'] == grupo]
    totales_grupo[grupo] = len(df_grupo)

# Crear pie chart
fig, ax = plt.subplots(figsize=(12, 8))

# Ordenar por cantidad descendente para mejor visualización
grupos_ordenados = sorted(totales_grupo.items(), key=lambda x: x[1], reverse=True)
labels = [g[0] for g in grupos_ordenados]
sizes = [g[1] for g in grupos_ordenados]
percentages = [s / sum(sizes) * 100 for s in sizes]

# Colores
colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))

# Crear pie chart con etiquetas mejoradas
wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                    colors=colors, startangle=90,
                                    textprops={'fontsize': 10})

# Mejorar apariencia de las etiquetas porcentuales
for autotext in autotexts:
    autotext.set_color('black')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(9)

ax.set_title('Proporción Total de Grupos de Productores Primarios (2000-2024)',
             fontsize=14, fontweight='bold', pad=20)

# Crear tabla con valores absolutos
tabla_datos = []
for label, size, pct in zip(labels, sizes, percentages):
    tabla_datos.append([label, f'{size:,}', f'{pct:.1f}%'])

# Agregar tabla debajo del gráfico
tabla = ax.table(cellText=tabla_datos,
                colLabels=['Grupo', 'Registros', 'Porcentaje'],
                cellLoc='center',
                loc='bottom',
                bbox=[0, -0.35, 1, 0.25])
tabla.auto_set_font_size(False)
tabla.set_fontsize(9)
tabla.scale(1, 1.5)

# Estilo de la tabla
for i in range(len(tabla_datos) + 1):
    if i == 0:
        tabla[(i, 0)].set_facecolor('#4CAF50')
        tabla[(i, 1)].set_facecolor('#4CAF50')
        tabla[(i, 2)].set_facecolor('#4CAF50')
        tabla[(i, 0)].set_text_props(weight='bold', color='white')
        tabla[(i, 1)].set_text_props(weight='bold', color='white')
        tabla[(i, 2)].set_text_props(weight='bold', color='white')
    else:
        tabla[(i, 0)].set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
        tabla[(i, 1)].set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
        tabla[(i, 2)].set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')

plt.subplots_adjust(bottom=0.35)

filepath = os.path.join(FIGURES_DIR, 'pie_in_situ_proporciones_totales.png')
plt.savefig(filepath, dpi=300, bbox_inches='tight')
print(f"  ✓ Gráfica pie: {filepath}")
plt.close()

# Crear gráfica de pie sin "Otros" y "Otros Eucariotas"
print("Generando gráfica de pie (excluido)...")

# Calcular totales por grupo excluyendo "Otros" y "Otros Eucariotas"
totales_grupo_excluido = {}
for grupo in grupos:
    if grupo not in ['Otros', 'Otros Eucariotas']:
        df_grupo = df[df['grupo_primario'] == grupo]
        totales_grupo_excluido[grupo] = len(df_grupo)

# Crear pie chart
fig, ax = plt.subplots(figsize=(12, 8))

# Ordenar por cantidad descendente para mejor visualización
grupos_ordenados_exc = sorted(totales_grupo_excluido.items(), key=lambda x: x[1], reverse=True)
labels_exc = [g[0] for g in grupos_ordenados_exc]
sizes_exc = [g[1] for g in grupos_ordenados_exc]
percentages_exc = [s / sum(sizes_exc) * 100 for s in sizes_exc]

# Colores
colors_exc = plt.cm.Set2(np.linspace(0, 1, len(labels_exc)))

# Crear pie chart con etiquetas mejoradas
wedges, texts, autotexts = ax.pie(sizes_exc, labels=labels_exc, autopct='%1.1f%%',
                                    colors=colors_exc, startangle=90,
                                    textprops={'fontsize': 10})

# Mejorar apariencia de las etiquetas porcentuales
for autotext in autotexts:
    autotext.set_color('black')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(9)

ax.set_title('Proporción de Grupos de Productores Primarios (2000-2024)\nExcluyendo "Otros" y "Otros Eucariotas"',
             fontsize=14, fontweight='bold', pad=20)

# Crear tabla con valores absolutos
tabla_datos_exc = []
for label, size, pct in zip(labels_exc, sizes_exc, percentages_exc):
    tabla_datos_exc.append([label, f'{size:,}', f'{pct:.1f}%'])

# Agregar tabla debajo del gráfico
tabla_exc = ax.table(cellText=tabla_datos_exc,
                    colLabels=['Grupo', 'Registros', 'Porcentaje'],
                    cellLoc='center',
                    loc='bottom',
                    bbox=[0, -0.35, 1, 0.25])
tabla_exc.auto_set_font_size(False)
tabla_exc.set_fontsize(9)
tabla_exc.scale(1, 1.5)

# Estilo de la tabla
for i in range(len(tabla_datos_exc) + 1):
    if i == 0:
        tabla_exc[(i, 0)].set_facecolor('#2196F3')
        tabla_exc[(i, 1)].set_facecolor('#2196F3')
        tabla_exc[(i, 2)].set_facecolor('#2196F3')
        tabla_exc[(i, 0)].set_text_props(weight='bold', color='white')
        tabla_exc[(i, 1)].set_text_props(weight='bold', color='white')
        tabla_exc[(i, 2)].set_text_props(weight='bold', color='white')
    else:
        tabla_exc[(i, 0)].set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
        tabla_exc[(i, 1)].set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
        tabla_exc[(i, 2)].set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')

plt.subplots_adjust(bottom=0.35)

filepath = os.path.join(FIGURES_DIR, 'pie_in_situ_proporciones_totales_excluido.png')
plt.savefig(filepath, dpi=300, bbox_inches='tight')
print(f"  ✓ Gráfica pie (excluido): {filepath}")
plt.close()

# Resumen general
print("\n" + "="*60)
print("RESUMEN DEL ANÁLISIS")
print("="*60)
print(f"Período analizado: 2000-2024")
print(f"Registros totales: {len(df)}")
print(f"Grupos identificados: {len(grupos)}")
print(f"\nArchivos generados:")
print(f"  - Series de tiempo (CSV): {len(grupos)} archivos")
print(f"  - Estadísticas mensuales (CSV): {len(grupos)} archivos")
print(f"  - Gráficas: 2 + {len(grupos)} archivos")
print(f"\nDirectorio output: {OUTPUT_DIR}")
print(f"Directorio figuras: {FIGURES_DIR}")
print("="*60)
