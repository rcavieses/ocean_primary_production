#!/usr/bin/env Rscript
# Script para ejecutar el análisis PFT
# Uso: Rscript run_analysis.R

# Cambiar directorio de trabajo
setwd("/home/atlantis/atlantis_primary_producton/ocean_primary_production/Rwork")

# Cargar librerías necesarias
if (!requireNamespace("rmarkdown", quietly = TRUE)) {
  install.packages("rmarkdown", repos = "https://cloud.r-project.org/")
}

library(rmarkdown)

# Crear timestamp
timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")

# Renderizar el notebook
cat("===============================================\n")
cat("Iniciando análisis PFT - Golfo de California\n")
cat("Timestamp:", timestamp, "\n")
cat("===============================================\n\n")

output_file <- paste0("pft_analysis_", timestamp, ".html")

tryCatch({
  render(
    input = "pft_analysis.Rmd",
    output_file = output_file,
    quiet = FALSE
  )
  
  cat("\n===============================================\n")
  cat("✓ Análisis completado exitosamente!\n")
  cat("Archivo generado:", output_file, "\n")
  cat("===============================================\n")
  
}, error = function(e) {
  cat("\n✗ Error durante la ejecución:\n")
  cat(e$message, "\n")
  quit(status = 1)
})
