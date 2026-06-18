#!/usr/bin/env bash
# Script para empaquetar el reporte HTML con todas sus figuras en un ZIP

set -e

# Directorios
RWORK_DIR="/home/atlantis/atlantis_primary_producton/ocean_primary_production/Rwork"
FIGURES_DIR="/home/atlantis/atlantis_primary_producton/ocean_primary_production/data/figures"
INTERMEDIATE_DIR="/home/atlantis/atlantis_primary_producton/ocean_primary_production/data/figures/intermediate_data"
DATA_DIR="/home/atlantis/atlantis_primary_producton/ocean_primary_production/data"

# Crear directorio temporal
TEMP_DIR=$(mktemp -d)
echo "Directorio temporal: $TEMP_DIR"

# Crear estructura de carpetas
mkdir -p "$TEMP_DIR/reporte/figures"
mkdir -p "$TEMP_DIR/reporte/data"

# Copiar archivo HTML principal
echo "Copiando HTML principal..."
cp "$RWORK_DIR/pft_analysis.html" "$TEMP_DIR/reporte/index.html"

# Copiar todas las figuras
echo "Copiando figuras..."
if [ -d "$FIGURES_DIR/html_outputs" ]; then
    cp -r "$FIGURES_DIR/html_outputs" "$TEMP_DIR/reporte/figures/"
    echo "  ✓ Figuras HTML copiadas"
fi

# Copiar datos intermedios
echo "Copiando datos intermedios..."
if [ -d "$INTERMEDIATE_DIR" ]; then
    cp -r "$INTERMEDIATE_DIR" "$TEMP_DIR/reporte/data/"
    echo "  ✓ Datos intermedios copiados"
fi

# Copiar archivos de datos
echo "Copiando archivos de datos..."
if [ -f "$DATA_DIR/nino34.long.anom.csv" ]; then
    cp "$DATA_DIR/nino34.long.anom.csv" "$TEMP_DIR/reporte/data/"
    echo "  ✓ Datos NIÑO3.4 copiados"
fi

# Copiar utils.R y README.md
echo "Copiando archivos de referencia..."
cp "$RWORK_DIR/utils.R" "$TEMP_DIR/reporte/"
cp "$RWORK_DIR/README.md" "$TEMP_DIR/reporte/" 2>/dev/null || true
cp "$RWORK_DIR/pft_analysis.Rmd" "$TEMP_DIR/reporte/" 2>/dev/null || true

# Crear archivo HTML actualizado con paths relativos
echo "Actualizando paths relativos en HTML..."
cd "$TEMP_DIR/reporte"

# Actualizar references en el HTML
sed -i 's|../data/figures/html_outputs/|figures/html_outputs/|g' index.html
sed -i 's|../data/figures/|figures/|g' index.html
sed -i 's|src="|src="figures/|g' index.html 2>/dev/null || true

# Crear archivo README para el ZIP
cat > README.txt << 'EOF'
=== REPORTE PFT - GOLFO DE CALIFORNIA (2000-2024) ===

CONTENIDO:
- index.html: Reporte principal (abrir en navegador)
- figures/: Todas las figuras interactivas y datos
- data/: Datos intermedios y archivos de entrada
- pft_analysis.Rmd: Código fuente del análisis
- utils.R: Funciones utilitarias
- README.md: Documentación completa

INSTRUCCIONES:
1. Descomprimir el archivo ZIP
2. Abrir index.html en un navegador web
3. Todos los gráficos se cargarán localmente

CARACTERÍSTICAS:
✓ Gráficos interactivos (Plotly)
✓ Series temporales con NIÑO3.4
✓ Mapas de diferencias quinquenales
✓ Análisis estacional
✓ Datos intermedios para reproducción

NAVEGACIÓN:
- Use las pestañas para cambiar entre variables
- Los gráficos son interactivos (zoom, pan, etc.)
- Haga clic en la leyenda para mostrar/ocultar series

REQUISITOS:
- Navegador moderno (Chrome, Firefox, Safari, Edge)
- JavaScript habilitado

Nota: Este reporte es autocontendido y funciona completamente offline.
EOF

echo "  ✓ README.txt creado"

# Crear ZIP
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ZIP_FILE="/home/atlantis/atlantis_primary_producton/ocean_primary_production/reporte_pft_${TIMESTAMP}.zip"

cd "$TEMP_DIR"
zip -r "$ZIP_FILE" reporte > /dev/null 2>&1

echo ""
echo "=========================================="
echo "✓ Reporte empaquetado exitosamente"
echo "=========================================="
echo "Archivo: $ZIP_FILE"
echo "Tamaño: $(du -h "$ZIP_FILE" | cut -f1)"
echo ""
echo "Contenido del ZIP:"
unzip -l "$ZIP_FILE" | head -30
echo ""
echo "Para usar:"
echo "1. Descomprimir: unzip reporte_pft_${TIMESTAMP}.zip"
echo "2. Abrir: reporte/index.html"
echo ""

# Limpiar
rm -rf "$TEMP_DIR"

echo "✓ Proceso completado"
