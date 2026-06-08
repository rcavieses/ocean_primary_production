#!/usr/bin/env python3
"""
Script para descargar datos de grupos fitoplanctónicos (PFT) desde Copernicus Marine Service.

Producto: OCEANCOLOUR_GLO_BGC_L4_MY_009_104 (4km, multianual)
Variables: Producción primaria por grupos funcionales de fitoplancton

Uso:
    python download_pft_data.py
"""

import copernicusmarine
from datetime import datetime
from pathlib import Path

# Configuración de la descarga
CONFIG = {
    # Período temporal
    'start_date': '2000-01-01',
    'end_date': '2024-12-31',
    
    # Región: Golfo de California
    'lon_min': -117.0,
    'lon_max': -102.0,
    'lat_min': 18.0,
    'lat_max': 33.0,
    
    # Producto correcto para PFT con resolución 4km
    'dataset_id': 'cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D',
                  
    # Variables de producción primaria por grupo funcional
    'variables': [
        'DIATO',   # Diatomeas
        'DINO',    # Dinoflagelados
        'HAPTO',   # Haptofitas
        'GREEN',   # Algas verdes (antes CHLORO)
        'PROKAR',  # Procariotas (cianobacterias) - antes PROK
        'CRYPTO',  # Criptofitas
        'CHL'      # Clorofila total (opcional, para contexto)
    ],
    
    # Archivo de salida
    'output_dir': Path(__file__).parent.parent.parent / 'data',
    'output_filename': 'pft_golfo_california_2000_2024.nc'
}


def download_pft_data():
    """
    Descargar datos de grupos fitoplanctónicos desde Copernicus Marine Service.
    """
    # Crear directorio de salida si no existe
    CONFIG['output_dir'].mkdir(parents=True, exist_ok=True)
    output_file = CONFIG['output_dir'] / CONFIG['output_filename']
    print(f"\nIniciando descarga...\n")
      
    try:
        copernicusmarine.subset(
            dataset_id=CONFIG['dataset_id'],
            # No especificar variables descarga TODAS las variables del producto
            minimum_longitude=CONFIG['lon_min'],
            maximum_longitude=CONFIG['lon_max'],
            minimum_latitude=CONFIG['lat_min'],
            maximum_latitude=CONFIG['lat_max'],
            start_datetime=CONFIG['start_date'],
            end_datetime=CONFIG['end_date'],
            output_filename=str(output_file)
        )
        
        print("\n" + "="*80)
        print("✓ DESCARGA COMPLETADA EXITOSAMENTE")
        print("="*80)
        print(f"\nArchivo guardado en: {output_file}")
        
        # Mostrar tamaño del archivo
        if output_file.exists():
            file_size_mb = output_file.stat().st_size / (1024**2)
            print(f"Tamaño del archivo: {file_size_mb:.2f} MB")
        
        return output_file
        
    except Exception as e:
        print("\n" + "="*80)
        print("✗ ERROR DURANTE LA DESCARGA")
        raise


if __name__ == "__main__":
    download_pft_data()