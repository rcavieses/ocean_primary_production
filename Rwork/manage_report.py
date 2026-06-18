#!/usr/bin/env python3
"""
Script para crear y gestionar el ZIP del reporte PFT
Permite validar, actualizar y crear nuevas versiones del ZIP
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import argparse

def get_project_root():
    """Obtiene la ruta raíz del proyecto"""
    return Path("/home/atlantis/atlantis_primary_producton/ocean_primary_production")

def create_report_zip(output_name=None, verbose=True):
    """Crea un nuevo ZIP del reporte"""
    
    project_root = get_project_root()
    rwork = project_root / "Rwork"
    figures = project_root / "data" / "figures"
    intermediate = project_root / "data" / "figures" / "intermediate_data"
    data = project_root / "data"
    
    # Crear directorio temporal
    temp_dir = Path("/tmp/reporte_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)
    
    reporte_dir = temp_dir / "reporte"
    reporte_dir.mkdir()
    
    if verbose:
        print("=" * 50)
        print("Creando ZIP del Reporte PFT")
        print("=" * 50)
    
    # Crear estructura
    (reporte_dir / "figures").mkdir()
    (reporte_dir / "data").mkdir()
    
    # Copiar HTML
    html_src = rwork / "pft_analysis.html"
    if html_src.exists():
        shutil.copy(html_src, reporte_dir / "index.html")
        if verbose:
            print("✓ HTML principal copiado")
    else:
        print("✗ Error: pft_analysis.html no encontrado")
        return None
    
    # Copiar figuras
    if (figures / "html_outputs").exists():
        shutil.copytree(
            figures / "html_outputs",
            reporte_dir / "figures" / "html_outputs"
        )
        if verbose:
            print("✓ Figuras copiadas")
    
    # Copiar datos intermedios
    if intermediate.exists():
        shutil.copytree(
            intermediate,
            reporte_dir / "data" / "intermediate_data"
        )
        if verbose:
            print("✓ Datos intermedios copiados")
    
    # Copiar archivos de datos
    nino_file = data / "nino34.long.anom.csv"
    if nino_file.exists():
        shutil.copy(nino_file, reporte_dir / "data")
        if verbose:
            print("✓ Datos NIÑO3.4 copiados")
    
    # Copiar archivos de referencia
    for fname in ["utils.R", "README.md", "pft_analysis.Rmd"]:
        src = rwork / fname
        if src.exists():
            shutil.copy(src, reporte_dir)
    if verbose:
        print("✓ Archivos de referencia copiados")
    
    # Actualizar paths en HTML
    html_file = reporte_dir / "index.html"
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazar paths
    content = content.replace("../data/figures/html_outputs/", "figures/html_outputs/")
    content = content.replace("../data/figures/", "figures/")
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    if verbose:
        print("✓ Paths relativos actualizados")
    
    # Crear README.txt
    readme_txt = reporte_dir / "README.txt"
    readme_txt.write_text("""=== REPORTE PFT - GOLFO DE CALIFORNIA (2000-2024) ===

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
""")
    if verbose:
        print("✓ README.txt creado")
    
    # Crear ZIP
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_name is None:
        zip_path = project_root / f"reporte_pft_{timestamp}.zip"
    else:
        zip_path = project_root / output_name
    
    # Comprimir
    shutil.make_archive(
        str(zip_path).replace('.zip', ''),
        'zip',
        temp_dir
    )
    
    # Limpiar
    shutil.rmtree(temp_dir)
    
    if verbose:
        zip_size = zip_path.stat().st_size / (1024 * 1024)  # MB
        print(f"\n{'=' * 50}")
        print("✓ ZIP creado exitosamente")
        print(f"Archivo: {zip_path.name}")
        print(f"Tamaño: {zip_size:.1f} MB")
        print(f"{'=' * 50}")
    
    return zip_path

def list_zips(verbose=True):
    """Lista todos los ZIPs disponibles"""
    project_root = get_project_root()
    zips = list(project_root.glob("reporte_pft_*.zip"))
    
    if verbose:
        print(f"\nArchivos ZIP disponibles ({len(zips)}):")
        print("-" * 60)
    
    for z in sorted(zips, reverse=True):
        size_mb = z.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(z.stat().st_mtime)
        print(f"{z.name:<45} {size_mb:>6.1f} MB  {mtime.strftime('%Y-%m-%d %H:%M')}")
    
    return zips

def validate_zip(zip_path):
    """Valida que el ZIP contiene todos los archivos necesarios"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            
            required = [
                'reporte/index.html',
                'reporte/figures/html_outputs/',
                'reporte/data/',
                'reporte/README.txt'
            ]
            
            all_present = all(
                any(name.startswith(req) for name in names)
                for req in required
            )
            
            if all_present:
                print(f"✓ ZIP válido: {zip_path.name}")
                print(f"  - Total de archivos: {len(names)}")
                return True
            else:
                print(f"✗ ZIP incompleto: faltan archivos")
                return False
                
    except zipfile.BadZipFile:
        print(f"✗ Archivo ZIP corrupto")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Gestiona el ZIP del reporte PFT"
    )
    parser.add_argument(
        "command",
        choices=["create", "list", "validate"],
        help="Comando a ejecutar"
    )
    parser.add_argument(
        "-o", "--output",
        help="Nombre del archivo de salida (para 'create')"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Modo silencioso"
    )
    
    args = parser.parse_args()
    
    if args.command == "create":
        zip_path = create_report_zip(output_name=args.output, verbose=not args.quiet)
        if zip_path:
            print(f"\nUso: unzip {zip_path.name}")
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.command == "list":
        list_zips(verbose=not args.quiet)
        sys.exit(0)
    
    elif args.command == "validate":
        project_root = get_project_root()
        zips = list(project_root.glob("reporte_pft_*.zip"))
        
        if not zips:
            print("No se encontraron archivos ZIP")
            sys.exit(1)
        
        # Validar el más reciente
        latest_zip = sorted(zips, reverse=True)[0]
        if validate_zip(latest_zip):
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()
