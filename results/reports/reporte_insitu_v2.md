
# Reporte de Análisis — Producción Primaria Fitoplanctónica


## Golfo de California (2000–2024)

**Generado:** 2026-04-21 18:53  

**Taxonomía in-situ:** `taxonomy_corrected_edna_2.csv` (versión v2)  

**Fuente satelital:** MODIS Aqua Level-3, 4 km, mensual  

**Período:** Enero 2000 – Diciembre 2024 (300 meses)  

---


## 1. Estadísticas Satelitales por Variable (2000–2024)

Concentraciones mensuales promediadas espacialmente sobre el Golfo de California (mg m⁻³).

| Variable | Nombre | Media | Desv. Est. | Mínimo | Máximo |
| --- | --- | --- | --- | --- | --- |
| CHL | Clorofila-a Total | 0.4880 | 0.1662 | 0.2361 | 1.0207 |
| DIATO | Diatomeas | 0.0603 | 0.0483 | 0.0089 | 0.3019 |
| DINO | Dinoflagelados | 0.0195 | 0.0095 | 0.0091 | 0.0647 |
| GREEN | Algas Verdes | 0.1062 | 0.0401 | 0.0479 | 0.2270 |
| HAPTO | Haptófitos | 0.0617 | 0.0151 | 0.0373 | 0.1259 |
| MICRO | Microfitoplancton | 0.0798 | 0.0514 | 0.0183 | 0.3234 |
| NANO | Nanofitoplancton | 0.0617 | 0.0151 | 0.0373 | 0.1259 |
| PICO | Picofitoplancton | 0.1420 | 0.0371 | 0.0871 | 0.2528 |
| PROCHLO | Proclorococcus | 0.0614 | 0.0505 | 0.0134 | 0.2594 |
| PROKAR | Procariontes | 0.0358 | 0.0074 | 0.0241 | 0.0541 |


## 2. Datos In-Situ eDNA — Resumen por Grupo Taxonómico

Archivo: `taxonomy_corrected_edna_2.csv` · Período válido: 2000–2024

| Grupo | Total Registros | Promedio Mensual/Año |
| --- | --- | --- |
| Clorofitas | 2,748 | 9.2 |
| Diatomeas | 1,446 | 4.8 |
| Dinoflagelados | 1,216 | 4.1 |
| Haptofitas | 328 | 1.1 |
| Otros | 11,251 | 37.5 |
| Protozoa | 26 | 0.1 |
| **TOTAL** | **17,015** |  |


## 3. Análisis por Profundidad

Distribución de abundancia eDNA por capa de profundidad: Superficial (1–26 m), Intermedia (35–140 m), Profunda (220–1000 m).

| Grupo | Capa | Profundidad | N_registros | N_con_abundancia | Abundancia_total | Abundancia_media | Abundancia_max | Abundancia_mediana | Satelital_media_mgm3 | Variable_satelital |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dinoflagelados | Superficial | 1-26 m | 1216 | 1216 | 70671 | 58.11759868421053 | 4633 | 5.0 | 0.019478555910151314 | DINO_mean |
| Dinoflagelados | Intermedia | 35-140 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.019478555910151314 | DINO_mean |
| Dinoflagelados | Profunda | 220-1000 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.019478555910151314 | DINO_mean |
| Diatomeas | Superficial | 1-26 m | 1446 | 1446 | 129609 | 89.63278008298755 | 11753 | 5.0 | 0.060332868824264516 | DIATO_mean |
| Diatomeas | Intermedia | 35-140 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.060332868824264516 | DIATO_mean |
| Diatomeas | Profunda | 220-1000 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.060332868824264516 | DIATO_mean |
| Clorofitas | Superficial | 1-26 m | 2748 | 2748 | 550799 | 200.4363173216885 | 57610 | 3.0 | 0.10619900876449215 | GREEN_mean |
| Clorofitas | Intermedia | 35-140 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.10619900876449215 | GREEN_mean |
| Clorofitas | Profunda | 220-1000 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.10619900876449215 | GREEN_mean |
| Haptofitas | Superficial | 1-26 m | 328 | 328 | 40829 | 124.47865853658537 | 5020 | 4.0 | 0.061744177493232265 | HAPTO_mean |
| Haptofitas | Intermedia | 35-140 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.061744177493232265 | HAPTO_mean |
| Haptofitas | Profunda | 220-1000 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.061744177493232265 | HAPTO_mean |
| Cianobacterias | Superficial | 1-26 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.03579266618385359 | PROKAR_mean |
| Cianobacterias | Intermedia | 35-140 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.03579266618385359 | PROKAR_mean |
| Cianobacterias | Profunda | 220-1000 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.03579266618385359 | PROKAR_mean |
| Otros Eucariotas | Superficial | 1-26 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.48795516123374305 | CHL_mean |
| Otros Eucariotas | Intermedia | 35-140 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.48795516123374305 | CHL_mean |
| Otros Eucariotas | Profunda | 220-1000 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.48795516123374305 | CHL_mean |
| Protozoa | Superficial | 1-26 m | 26 | 26 | 237 | 9.115384615384615 | 43 | 6.0 | 0.48795516123374305 | CHL_mean |
| Protozoa | Intermedia | 35-140 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.48795516123374305 | CHL_mean |
| Protozoa | Profunda | 220-1000 m | 0 | 0 | 0 | 0.0 | 0 | 0.0 | 0.48795516123374305 | CHL_mean |


### Figuras — Análisis de Profundidad

**01_timeseries_depth_clorofitas**  

![01_timeseries_depth_clorofitas](../insitu/edna_v2/profundidad/01_timeseries_depth_clorofitas.png)  



**01_timeseries_depth_diatomeas**  

![01_timeseries_depth_diatomeas](../insitu/edna_v2/profundidad/01_timeseries_depth_diatomeas.png)  



**01_timeseries_depth_dinoflagelados**  

![01_timeseries_depth_dinoflagelados](../insitu/edna_v2/profundidad/01_timeseries_depth_dinoflagelados.png)  



**01_timeseries_depth_haptofitas**  

![01_timeseries_depth_haptofitas](../insitu/edna_v2/profundidad/01_timeseries_depth_haptofitas.png)  



**01_timeseries_depth_protozoa**  

![01_timeseries_depth_protozoa](../insitu/edna_v2/profundidad/01_timeseries_depth_protozoa.png)  



**02_perfil_vertical_abundancia**  

![02_perfil_vertical_abundancia](../insitu/edna_v2/profundidad/02_perfil_vertical_abundancia.png)  



**03_estacionalidad_por_profundidad**  

![03_estacionalidad_por_profundidad](../insitu/edna_v2/profundidad/03_estacionalidad_por_profundidad.png)  



**04_abundancia_por_capa_grupo**  

![04_abundancia_por_capa_grupo](../insitu/edna_v2/profundidad/04_abundancia_por_capa_grupo.png)  



**05_correlacion_sat_vs_insitu_por_capa**  

![05_correlacion_sat_vs_insitu_por_capa](../insitu/edna_v2/profundidad/05_correlacion_sat_vs_insitu_por_capa.png)  



**06_heatmap_profundidad_dinoflagelados**  

![06_heatmap_profundidad_dinoflagelados](../insitu/edna_v2/profundidad/06_heatmap_profundidad_dinoflagelados.png)  



**06_heatmap_profundidad_protozoa**  

![06_heatmap_profundidad_protozoa](../insitu/edna_v2/profundidad/06_heatmap_profundidad_protozoa.png)  



**07_resumen_multipanel_profundidad**  

![07_resumen_multipanel_profundidad](../insitu/edna_v2/profundidad/07_resumen_multipanel_profundidad.png)  



**08_boxplot_abundancia_por_capa**  

![08_boxplot_abundancia_por_capa](../insitu/edna_v2/profundidad/08_boxplot_abundancia_por_capa.png)  




## 4. Series Temporales In-Situ (Figuras)

**barras_apiladas_in_situ_proporciones_anuales**  

![barras_apiladas_in_situ_proporciones_anuales](../insitu/edna_v2/series_tiempo/figuras_primarios/barras_apiladas_in_situ_proporciones_anuales.png)  



**heatmap_in_situ_clorofitas**  

![heatmap_in_situ_clorofitas](../insitu/edna_v2/series_tiempo/figuras_primarios/heatmap_in_situ_clorofitas.png)  



**heatmap_in_situ_diatomeas**  

![heatmap_in_situ_diatomeas](../insitu/edna_v2/series_tiempo/figuras_primarios/heatmap_in_situ_diatomeas.png)  



**heatmap_in_situ_dinoflagelados**  

![heatmap_in_situ_dinoflagelados](../insitu/edna_v2/series_tiempo/figuras_primarios/heatmap_in_situ_dinoflagelados.png)  



**heatmap_in_situ_haptofitas**  

![heatmap_in_situ_haptofitas](../insitu/edna_v2/series_tiempo/figuras_primarios/heatmap_in_situ_haptofitas.png)  



**heatmap_in_situ_otros**  

![heatmap_in_situ_otros](../insitu/edna_v2/series_tiempo/figuras_primarios/heatmap_in_situ_otros.png)  



**heatmap_in_situ_protozoa**  

![heatmap_in_situ_protozoa](../insitu/edna_v2/series_tiempo/figuras_primarios/heatmap_in_situ_protozoa.png)  



**in_situ_comparativa_grupos_primarios**  

![in_situ_comparativa_grupos_primarios](../insitu/edna_v2/series_tiempo/figuras_primarios/in_situ_comparativa_grupos_primarios.png)  



**pie_in_situ_proporciones_totales**  

![pie_in_situ_proporciones_totales](../insitu/edna_v2/series_tiempo/figuras_primarios/pie_in_situ_proporciones_totales.png)  



**pie_in_situ_proporciones_totales_excluido**  

![pie_in_situ_proporciones_totales_excluido](../insitu/edna_v2/series_tiempo/figuras_primarios/pie_in_situ_proporciones_totales_excluido.png)  



**series_tiempo_in_situ_primarios_completa**  

![series_tiempo_in_situ_primarios_completa](../insitu/edna_v2/series_tiempo/figuras_primarios/series_tiempo_in_situ_primarios_completa.png)  




## 5. Correlación Cruzada con Índices Climáticos

Correlación de Pearson con desfases 0–6 meses entre anomalías de biomasa e índices MEI, NIÑO3.4, PDO. Significancia por 1,000 permutaciones.

| Variable | Índice | Correlación | Lag (meses) | p-valor |
| --- | --- | --- | --- | --- |
| Diatomeas | MEI |  | 0 |  |
| Diatomeas | NINO34 |  | 0 |  |
| Diatomeas | PDO |  | 0 |  |
| Dinoflagelados | MEI |  | 0 |  |
| Dinoflagelados | NINO34 |  | 0 |  |
| Dinoflagelados | PDO |  | 0 |  |
| Algas Verdes | MEI |  | 0 |  |
| Algas Verdes | NINO34 |  | 0 |  |
| Algas Verdes | PDO |  | 0 |  |
| Haptófitos | MEI |  | 0 |  |
| Haptófitos | NINO34 |  | 0 |  |
| Haptófitos | PDO |  | 0 |  |
| Microfitoplancton | MEI |  | 0 |  |
| Microfitoplancton | NINO34 |  | 0 |  |
| Microfitoplancton | PDO |  | 0 |  |
| Nanofitoplancton | MEI |  | 0 |  |
| Nanofitoplancton | NINO34 |  | 0 |  |
| Nanofitoplancton | PDO |  | 0 |  |
| Picofitoplancton | MEI |  | 0 |  |
| Picofitoplancton | NINO34 |  | 0 |  |
| Picofitoplancton | PDO |  | 0 |  |
| Proclorococcus | MEI |  | 0 |  |
| Proclorococcus | NINO34 |  | 0 |  |
| Proclorococcus | PDO |  | 0 |  |
| Procariontes | MEI |  | 0 |  |
| Procariontes | NINO34 |  | 0 |  |
| Procariontes | PDO |  | 0 |  |


## 6. Cambios de Régimen (HMM)

Modelos Ocultos de Markov (2 estados) para detectar transiciones entre regímenes productivos alto y bajo.

| Variable | N transiciones | Meses estado alto | Meses estado bajo |
| --- | --- | --- | --- |
| Diatomeas | 0 | 0 | 0 |
| Dinoflagelados | 0 | 0 | 0 |
| Algas Verdes | 0 | 0 | 0 |
| Haptófitos | 0 | 0 | 0 |
| Microfitoplancton | 0 | 0 | 0 |
| Nanofitoplancton | 0 | 0 | 0 |
| Picofitoplancton | 0 | 0 | 0 |
| Proclorococcus | 0 | 0 | 0 |
| Procariontes | 0 | 0 | 0 |


## 7. Figuras Satelitales


### Mapas de Concentración Media

**CHL_mean_map**  

![CHL_mean_map](../satellite/figures/maps/CHL_mean_map.png)  



**DIATO_mean_map**  

![DIATO_mean_map](../satellite/figures/maps/DIATO_mean_map.png)  



**DINO_mean_map**  

![DINO_mean_map](../satellite/figures/maps/DINO_mean_map.png)  



**GREEN_mean_map**  

![GREEN_mean_map](../satellite/figures/maps/GREEN_mean_map.png)  



**HAPTO_mean_map**  

![HAPTO_mean_map](../satellite/figures/maps/HAPTO_mean_map.png)  



*... y 5 figuras más en `results/satellite/figures/maps/`*



### Series Temporales con Índices Climáticos

**CHL_timeseries_with_indices**  

![CHL_timeseries_with_indices](../satellite/figures/timeseries/timeseries_indices/CHL_timeseries_with_indices.png)  



**DIATO_timeseries_with_indices**  

![DIATO_timeseries_with_indices](../satellite/figures/timeseries/timeseries_indices/DIATO_timeseries_with_indices.png)  



**DINO_timeseries_with_indices**  

![DINO_timeseries_with_indices](../satellite/figures/timeseries/timeseries_indices/DINO_timeseries_with_indices.png)  



**GREEN_timeseries_with_indices**  

![GREEN_timeseries_with_indices](../satellite/figures/timeseries/timeseries_indices/GREEN_timeseries_with_indices.png)  



**HAPTO_timeseries_with_indices**  

![HAPTO_timeseries_with_indices](../satellite/figures/timeseries/timeseries_indices/HAPTO_timeseries_with_indices.png)  



*... y 5 figuras más en `results/satellite/figures/timeseries/timeseries_indices/`*



### Descomposición STL

**DIATO_mean_stl_decomposition**  

![DIATO_mean_stl_decomposition](../satellite/figures/stl_decomposition/DIATO_mean_stl_decomposition.png)  



**DINO_mean_stl_decomposition**  

![DINO_mean_stl_decomposition](../satellite/figures/stl_decomposition/DINO_mean_stl_decomposition.png)  



**GREEN_mean_stl_decomposition**  

![GREEN_mean_stl_decomposition](../satellite/figures/stl_decomposition/GREEN_mean_stl_decomposition.png)  



**HAPTO_mean_stl_decomposition**  

![HAPTO_mean_stl_decomposition](../satellite/figures/stl_decomposition/HAPTO_mean_stl_decomposition.png)  



**MICRO_mean_stl_decomposition**  

![MICRO_mean_stl_decomposition](../satellite/figures/stl_decomposition/MICRO_mean_stl_decomposition.png)  



*... y 4 figuras más en `results/satellite/figures/stl_decomposition/`*



### Análisis Fourier

**DIATO_mean_fourier_spectrum**  

![DIATO_mean_fourier_spectrum](../satellite/figures/fourier_analysis/DIATO_mean_fourier_spectrum.png)  



**DINO_mean_fourier_spectrum**  

![DINO_mean_fourier_spectrum](../satellite/figures/fourier_analysis/DINO_mean_fourier_spectrum.png)  



**GREEN_mean_fourier_spectrum**  

![GREEN_mean_fourier_spectrum](../satellite/figures/fourier_analysis/GREEN_mean_fourier_spectrum.png)  



**HAPTO_mean_fourier_spectrum**  

![HAPTO_mean_fourier_spectrum](../satellite/figures/fourier_analysis/HAPTO_mean_fourier_spectrum.png)  



**MICRO_mean_fourier_spectrum**  

![MICRO_mean_fourier_spectrum](../satellite/figures/fourier_analysis/MICRO_mean_fourier_spectrum.png)  



*... y 4 figuras más en `results/satellite/figures/fourier_analysis/`*



### Cambios de Régimen HMM

**DIATO_mean_hmm_regimen**  

![DIATO_mean_hmm_regimen](../satellite/figures/hmm_regimen_change/DIATO_mean_hmm_regimen.png)  



**DINO_mean_hmm_regimen**  

![DINO_mean_hmm_regimen](../satellite/figures/hmm_regimen_change/DINO_mean_hmm_regimen.png)  



**GREEN_mean_hmm_regimen**  

![GREEN_mean_hmm_regimen](../satellite/figures/hmm_regimen_change/GREEN_mean_hmm_regimen.png)  



**HAPTO_mean_hmm_regimen**  

![HAPTO_mean_hmm_regimen](../satellite/figures/hmm_regimen_change/HAPTO_mean_hmm_regimen.png)  



**MICRO_mean_hmm_regimen**  

![MICRO_mean_hmm_regimen](../satellite/figures/hmm_regimen_change/MICRO_mean_hmm_regimen.png)  



*... y 4 figuras más en `results/satellite/figures/hmm_regimen_change/`*



### Extremos Alternativos (PELT)

**DIATO_mean_extremos_alternativos**  

![DIATO_mean_extremos_alternativos](../satellite/figures/extremos_alternativos/DIATO_mean_extremos_alternativos.png)  



**DINO_mean_extremos_alternativos**  

![DINO_mean_extremos_alternativos](../satellite/figures/extremos_alternativos/DINO_mean_extremos_alternativos.png)  



**GREEN_mean_extremos_alternativos**  

![GREEN_mean_extremos_alternativos](../satellite/figures/extremos_alternativos/GREEN_mean_extremos_alternativos.png)  



**HAPTO_mean_extremos_alternativos**  

![HAPTO_mean_extremos_alternativos](../satellite/figures/extremos_alternativos/HAPTO_mean_extremos_alternativos.png)  



**MICRO_mean_extremos_alternativos**  

![MICRO_mean_extremos_alternativos](../satellite/figures/extremos_alternativos/MICRO_mean_extremos_alternativos.png)  



*... y 4 figuras más en `results/satellite/figures/extremos_alternativos/`*



### Regresión Segmentada

**DIATO_mean_vs_MEI_piecewise**  

![DIATO_mean_vs_MEI_piecewise](../satellite/figures/piecewise_regression/DIATO_mean_vs_MEI_piecewise.png)  



**DIATO_mean_vs_NINO34_piecewise**  

![DIATO_mean_vs_NINO34_piecewise](../satellite/figures/piecewise_regression/DIATO_mean_vs_NINO34_piecewise.png)  



**DIATO_mean_vs_PDO_piecewise**  

![DIATO_mean_vs_PDO_piecewise](../satellite/figures/piecewise_regression/DIATO_mean_vs_PDO_piecewise.png)  



**DINO_mean_vs_MEI_piecewise**  

![DINO_mean_vs_MEI_piecewise](../satellite/figures/piecewise_regression/DINO_mean_vs_MEI_piecewise.png)  



**DINO_mean_vs_NINO34_piecewise**  

![DINO_mean_vs_NINO34_piecewise](../satellite/figures/piecewise_regression/DINO_mean_vs_NINO34_piecewise.png)  



*... y 13 figuras más en `results/satellite/figures/piecewise_regression/`*



## 8. Metodología Resumida

| Análisis | Método | Software |

| --- | --- | --- |

| Datos satelitales | MODIS Aqua L3, 4 km, mensual (Copernicus Marine) | `xarray`, `netCDF4` |

| Índices climáticos | MEI, NIÑO3.4, PDO (NOAA) | `pandas` |

| Datos in-situ | eDNA — Golfo de California | `pandas` |

| Descomposición temporal | STL (Loess) | `statsmodels` |

| Cambios de régimen | HMM 2 estados | `hmmlearn` |

| Causalidad | Granger F-test, lags 1–6 | `statsmodels` |

| Correlación cruzada | Pearson + 1,000 permutaciones | `numpy`, `scipy` |

| Correlación canónica | CCA | `sklearn` |

| Regresión segmentada | Piecewise breakpoint | `pwlf` |

| Extremos conjuntos | Percentiles p10/p90 co-ocurrencia | `pandas` |




## 9. Estructura de Resultados

```

results/

├── satellite/

│   ├── figures/         ← Mapas, series temporales, análisis estadísticos

│   └── tables/          ← CSVs de correlaciones, regresiones, extremos

├── insitu/

│   ├── edna_v1/         ← taxonomy_corrected_edna.csv (188,325 registros)

│   │   ├── series_tiempo/

│   │   └── profundidad/

│   └── edna_v2/         ← taxonomy_corrected_edna_2.csv (17,015 registros) ← ACTIVO

│       ├── series_tiempo/

│       └── profundidad/

└── reports/

    ├── index.html        ← Reporte HTML interactivo (20 secciones)

    └── reporte_insitu_v2.md  ← Este archivo

```


## 10. Comparación v1 vs v2

| Métrica | edna_v1 | edna_v2 (activo) |

| --- | --- | --- |

| Registros válidos 2000–2024 | 188,325 | 17,015 |

| Grupos taxonómicos | 6 (sin Diatomeas) | 6 (con Diatomeas) |

| Diatomeas (Bacillariophyta) | Clasificadas como *Otros* | Grupo separado ✓ |

| Formato fecha | Serial Excel | ISO 8601 |

| Columna profundidad | 3 cols (Shallow/Mid/Deep) | 1 col `Depth` (m) |

| Abundancia | Conteo registros | `Abundance` explícita |




## Notas

- Reporte generado automáticamente por `src/reports/generate_markdown_report.py`.

- Para cambiar la versión de taxonomía: `TAXONOMY_VERSION=v1 python3 generate_markdown_report.py`

- Reporte HTML completo con figuras interactivas: `results/reports/index.html`
