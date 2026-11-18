# Reanálisis del manuscrito: tipos funcionales de fitoplancton (PFT), Golfo de California

Código de los análisis estadísticos del manuscrito y de su revisión. Los datos no están en este
repositorio (ver *Datos*). Todos los scripts se corren desde la raíz del repositorio y escriben en
`manuscript/reanalysis/salidas/`, carpeta que se excluye del control de versiones.

## Entorno

Versiones con las que se generaron los resultados de la revisión (VM Linux x86-64):

| Componente | Versión |
|---|---|
| Python | 3.10.12 |
| xarray | 2025.6.1 |
| statsmodels | 0.15.0 |
| hmmlearn (HMM gaussiano) | 0.3.3 |
| numpy / pandas / scipy | 2.2.6 / 2.3.3 / 1.15.3 |
| scikit-learn (dependencia de hmmlearn) | 1.7.2 |
| netCDF4 | 1.7.4 |
| geopandas / shapely / cartopy / pyshp | 1.1.4 / 2.1.2 / 0.25.0 / 3.1.9 |
| matplotlib | 3.10.9 |

Lista fijada: `requirements_reanalisis.txt`.

```bash
python3.10 -m venv .venv && . .venv/bin/activate
pip install -r manuscript/reanalysis/requirements_reanalisis.txt
```

Los análisis originales del repositorio (`src/analysis/`) se corrieron con Python 3.10.12, xarray
2025.6.1, **statsmodels 0.14.6** y hmmlearn 0.3.3. `granger_revision.py` da resultados idénticos
(diferencia numérica 0) con statsmodels 0.14.6 y 0.15.0. Los HMM usan `random_state=42`, y las
pruebas por permutación usan semillas fijas.

## Datos

| Archivo esperado | Fuente |
|---|---|
| `data/raw/pft_golfo_california_2000_2024.nc` | Copernicus Marine Service, producto `cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D` (GlobColour, diario, 4 km), recorte 18–33° N, 117–102° O, 2000–2024; se descarga con `src/pipeline/download_pft_data.py` |
| `data/processed/pft_monthly_statistics.nc` | Medias mensuales sobre el polígono del golfo; se genera con `src/pipeline/preprocess_pft_data.py` |
| `data/raw/nino34.long.anom.csv`, `pdo.timeseries.sstens.csv`, `mei.exttimeseries.csv` | NOAA Physical Sciences Laboratory (series mensuales de índices climáticos) |
| `data/insitu/taxonomy_corrected_edna*.csv` | eDNA in situ; disponibles bajo solicitud a los autores |
| `results/satellite/figures/shapefiles/regionmarinamx.shp` | Polígono del Golfo de California (incluido en el repositorio) |

## Serie mensual con el polígono

`src/pipeline/preprocess_pft_data.py --out data/processed/pft_monthly_statistics_poligono.nc` genera la serie con
el polígono del golfo (13,928 píxeles); falla si el shapefile no carga y escribe el número real de píxeles en los
atributos. El archivo `pft_monthly_statistics.nc` original corresponde al rectángulo de descarga (ver
`procedencia_mensual.py`).

## Orden de ejecución

```bash
P=data/processed/pft_monthly_statistics.nc
python3 manuscript/reanalysis/stl_recortado.py --pft $P
python3 manuscript/reanalysis/granger_robusto.py --pft $P --indices data/raw
python3 manuscript/reanalysis/granger_revision.py --pft $P --indices data/raw         # familias de 15 y 3 pares, escalón GREEN, tabla suplementaria
python3 manuscript/reanalysis/tendencias_escalon_green.py --pft $P \
        --json-original results/satellite/tables/reporte_analisis_numerico.json
python3 manuscript/reanalysis/enso_fases.py --pft $P --nino data/raw/nino34.long.anom.csv
python3 manuscript/reanalysis/composicion_regional.py --raw data/raw/pft_golfo_california_2000_2024.nc   # lee el NetCDF diario
python3 manuscript/reanalysis/regional_tabla_figura.py
python3 -c "import sys; sys.path.insert(0,'manuscript/figures'); import make_manuscript_figures as m; m.fig_area_estudio()"
python3 manuscript/reanalysis/edna_auditoria.py --csv data/insitu/taxonomy_corrected_edna.csv --pft $P --out manuscript/reanalysis/salidas/edna_v1
python3 manuscript/reanalysis/edna_estratos.py --csv data/insitu/taxonomy_corrected_edna.csv
# eDNA con solo detecciones (abundancia > 0, sin el bloque de totales de la v1)
python3 manuscript/reanalysis/edna_auditoria.py --csv data/insitu/taxonomy_corrected_edna.csv --pft $P --solo-detecciones --out manuscript/reanalysis/salidas/edna_detecciones/v1
python3 manuscript/reanalysis/edna_auditoria.py --csv data/insitu/taxonomy_corrected_edna_2.csv --pft $P --solo-detecciones --out manuscript/reanalysis/salidas/edna_detecciones/v2
python3 manuscript/reanalysis/edna_panel_detecciones.py --csv data/insitu/taxonomy_corrected_edna_2.csv --pft $P
python3 manuscript/reanalysis/edna_detecciones_tablas.py   # requiere también las salidas sin --solo-detecciones en salidas/edna_<v1|v2|merged>
python3 manuscript/reanalysis/edna_normalizado.py --csv data/insitu/taxonomy_corrected_edna.csv --pft $P --raw data/raw/pft_golfo_california_2000_2024.nc
python3 manuscript/reanalysis/edna_v2_fechas.py --csv data/insitu/taxonomy_corrected_edna_2.csv --fuentes <tablas de sitios .xlsx>
python3 manuscript/reanalysis/hmm_semillas.py --pft $P --original results/satellite/figures/hmm_regimen_change/DIATO_mean_hmm_states.csv
python3 manuscript/reanalysis/procedencia_mensual.py --raw data/raw/pft_golfo_california_2000_2024.nc --nc $P --meses 2010-06 2003-01 2020-08
```

## Scripts

| Script | Qué hace |
|---|---|
| `stl_recortado.py` | STL recortado al periodo con datos + HMM de diatomeas (Fig. 5) |
| `granger_robusto.py` | Granger log10, desestacionalizado, ADF/KPSS, BH (versión con 18 pares) |
| `granger_revision.py` | Familia principal de 15 pares (5 grupos) con su propia BH; PROCHLO hasta mar-2016 con BH propia (y variante con índices preparados en 2002–2024); sensibilidad de GREEN al escalón de 2016 (indicadora y periodo previo); tabla suplementaria con p, q, desfase y ADF/KPSS |
| `escalon.py` | Detección de escalón: Pettitt + modelo de escalón con efectos de mes y p por permutación de bloques |
| `tendencias_escalon_green.py` | Tendencia lineal de GREEN (reproduce la original) con indicadora del escalón y solo antes del escalón; errores HAC, Theil-Sen, Mann-Kendall, tendencia STL |
| `enso_fases.py` | Fases ENSO tipo ONI; composición y anomalías de PFT por fase; permutación con desplazamiento circular |
| `composicion_regional.py` | Composición por bandas de latitud (`REGIONS`) desde el NetCDF diario |
| `regional_tabla_figura.py` | Tabla y figura de la composición por región |
| `edna_auditoria.py` | Auditoría de la eDNA y de los match-ups satélite-eDNA; `--solo-detecciones` excluye ausencias (abundancia = 0) y el bloque de totales |
| `edna_panel_detecciones.py` | Recalcula los match-ups del panel espacial (r = 0.27 / −0.46) con todas las filas y con solo detecciones |
| `edna_detecciones_tablas.py` | Tablas comparativas (cascada y match-ups) entre filas y detecciones |
| `edna_normalizado.py` | Match-ups eDNA (v1) normalizados por esfuerzo: muestras por mes, detecciones/muestra, frecuencia de ocurrencia; satélite de cuenca, banda regional y caja 3x3 |
| `edna_v2_fechas.py` | Formatos de fecha de la v2 (Mac_loughlin, Valdivia) y sus dos lecturas posibles; cruce con las tablas de sitios de las fuentes |
| `hmm_semillas.py` | HMM de diatomeas con 20 semillas, configuración por defecto y de máxima verosimilitud; regenera la Fig. 5 con la mejor solución |
| `procedencia_mensual.py` | Comprueba si `pft_monthly_statistics.nc` se calculó con el polígono o con el rectángulo |
| `control_poligono.py` | Controles de `pft_monthly_statistics_poligono.nc` (meses de prueba, bandas regionales, rectángulo frente a polígono) |
| `serie_cuenca.py` | Composición, escalones, quinquenios y Figs. 2-3 desde un NetCDF mensual (rectángulo o polígono) |
| `comparar_rect_poligono.py` | Tablas rectángulo -> polígono de todos los análisis y cambios de signo, significancia o fecha |
| `fig4_escala.py` | Efecto de la máscara en los mapas de diferencias de la Fig. 4 |
| `edna_estratos.py` | Composición de productores primarios por grupo y estrato (v1, solo detecciones) |
| `composition_no_doublecount.py`, `prochlo_discontinuity.py` | Partición sin doble conteo y prueba de discontinuidad de Prochlorococcus |
| `../figures/make_manuscript_figures.py` | Figuras 1–4 (la Fig. 1 dibuja los límites de `REGIONS`) |
