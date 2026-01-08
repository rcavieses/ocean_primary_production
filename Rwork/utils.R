# =============================================================================
# Funciones utilitarias para análisis de PFT
# Gulf of California Phytoplankton Analysis (2000-2024)
# =============================================================================

#' Instala y carga paquetes requeridos
#' @param packages Vector de nombres de paquetes
load_packages <- function(packages) {
  install_if_missing <- function(pkg) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
      install.packages(pkg, repos = "https://cloud.r-project.org/")
    }
  }
  invisible(lapply(packages, install_if_missing))
  invisible(lapply(packages, library, character.only = TRUE))
}

# =============================================================================
# Funciones para datos NIÑO3.4
# =============================================================================

#' Carga datos de anomalías NIÑO3.4
#' @param nino_file Ruta al archivo CSV de NIÑO3.4
#' @param start_date Fecha de inicio para filtrar
#' @param end_date Fecha de fin para filtrar
#' @return Dataframe con fecha y anomalía NIÑO3.4
load_nino34_data <- function(nino_file, start_date = "2000-01-01", end_date = "2024-12-31") {
  # Leer archivo saltando la primera línea (cabecera con descripción)
  nino_raw <- read.csv(nino_file, skip = 0, header = FALSE, 
                       col.names = c("Date", "NINO34"), 
                       stringsAsFactors = FALSE)
  
  # Eliminar primera fila (cabecera original)
  nino_raw <- nino_raw[-1, ]
  
  # Limpiar y convertir
  nino_raw$Date <- as.Date(trimws(nino_raw$Date))
  nino_raw$NINO34 <- as.numeric(trimws(nino_raw$NINO34))
  
  # Reemplazar valores faltantes (-99.99)
  nino_raw$NINO34[nino_raw$NINO34 < -90] <- NA
  
  # Filtrar por fechas
  nino_data <- nino_raw[nino_raw$Date >= as.Date(start_date) & 
                        nino_raw$Date <= as.Date(end_date), ]
  
  # Clasificar eventos ENSO
  nino_data$ENSO_phase <- ifelse(nino_data$NINO34 >= 0.5, "El Niño",
                                  ifelse(nino_data$NINO34 <= -0.5, "La Niña", "Neutral"))
  
  return(nino_data)
}

# =============================================================================
# Funciones para guardar/cargar datos intermedios
# =============================================================================

#' Guarda datos de mapa a archivo CSV para reutilización
#' @param data_matrix Matriz de datos del mapa
#' @param lon Vector de longitudes
#' @param lat Vector de latitudes
#' @param output_file Ruta del archivo de salida
#' @param metadata Lista con metadatos adicionales
save_map_data <- function(data_matrix, lon, lat, output_file, metadata = NULL) {
  df <- expand.grid(lon = lon, lat = lat)
  df$value <- as.vector(data_matrix)
  
  # Agregar metadatos como atributos
  if (!is.null(metadata)) {
    attr(df, "metadata") <- metadata
    
    # Guardar metadatos en archivo separado
    meta_file <- gsub("\\.csv$", "_metadata.json", output_file)
    jsonlite::write_json(metadata, meta_file, pretty = TRUE)
  }
  
  write.csv(df, output_file, row.names = FALSE)
  return(invisible(df))
}

#' Carga datos de mapa desde archivo CSV
#' @param input_file Ruta del archivo de entrada
#' @return Lista con dataframe, lon, lat y metadatos
load_map_data <- function(input_file) {
  df <- read.csv(input_file)
  
  lon <- sort(unique(df$lon))
  lat <- sort(unique(df$lat))
  
  # Intentar cargar metadatos
  meta_file <- gsub("\\.csv$", "_metadata.json", input_file)
  metadata <- NULL
  if (file.exists(meta_file)) {
    metadata <- jsonlite::read_json(meta_file)
  }
  
  return(list(
    data = df,
    lon = lon,
    lat = lat,
    metadata = metadata
  ))
}

#' Guarda datos de serie temporal a archivo CSV
#' @param df Dataframe con la serie temporal
#' @param output_file Ruta del archivo de salida
#' @param var_name Nombre de la variable
save_timeseries_data <- function(df, output_file, var_name) {
  df$variable <- var_name
  write.csv(df, output_file, row.names = FALSE)
  return(invisible(df))
}

#' Calcula la media quinquenal para una variable
#' @param data_file Ruta al archivo NetCDF
#' @param var_name Nombre de la variable
#' @param time Vector de fechas
#' @param start_date Fecha de inicio del período
#' @param end_date Fecha de fin del período
#' @param lon_dim Dimensión de longitud
#' @param lat_dim Dimensión de latitud
#' @return Matriz con la media del período
calc_quinquennial_mean <- function(data_file, var_name, time, start_date, end_date, lon_dim, lat_dim) {
  idx <- which(time >= as.Date(start_date) & time <= as.Date(end_date))
  
  if (length(idx) == 0) return(NULL)
  
  nc <- ncdf4::nc_open(data_file)
  
  sum_data <- matrix(0, nrow = lon_dim, ncol = lat_dim)
  count_data <- matrix(0, nrow = lon_dim, ncol = lat_dim)
  
  for (t_idx in idx) {
    data_slice <- ncdf4::ncvar_get(nc, var_name,
                                   start = c(1, 1, t_idx),
                                   count = c(lon_dim, lat_dim, 1))
    
    valid <- !is.na(data_slice)
    sum_data[valid] <- sum_data[valid] + data_slice[valid]
    count_data[valid] <- count_data[valid] + 1
    
    rm(data_slice)
  }
  
  ncdf4::nc_close(nc)
  gc()
  
  mean_data <- sum_data / count_data
  mean_data[count_data == 0] <- NA
  
  rm(sum_data, count_data)
  gc()
  
  return(mean_data)
}

#' Calcula la media estacional para un período
#' @param data_file Ruta al archivo NetCDF
#' @param var_name Nombre de la variable
#' @param time Vector de fechas
#' @param start_date Fecha de inicio del período
#' @param end_date Fecha de fin del período
#' @param season_months Vector de meses de la estación
#' @param lon_dim Dimensión de longitud
#' @param lat_dim Dimensión de latitud
#' @return Media espacial para la estación
calc_seasonal_mean <- function(data_file, var_name, time, start_date, end_date, 
                               season_months, lon_dim, lat_dim) {
  idx_period <- which(time >= as.Date(start_date) & time <= as.Date(end_date))
  months <- lubridate::month(time)
  idx_season <- which(months %in% season_months)
  idx <- intersect(idx_period, idx_season)
  
  if (length(idx) == 0) return(NA)
  
  nc <- ncdf4::nc_open(data_file)
  
  total_sum <- 0
  total_count <- 0
  
  for (t_idx in idx) {
    data_slice <- ncdf4::ncvar_get(nc, var_name,
                                   start = c(1, 1, t_idx),
                                   count = c(lon_dim, lat_dim, 1))
    valid_vals <- data_slice[!is.na(data_slice)]
    total_sum <- total_sum + sum(valid_vals)
    total_count <- total_count + length(valid_vals)
    rm(data_slice, valid_vals)
  }
  
  ncdf4::nc_close(nc)
  gc()
  
  if (total_count == 0) return(NA)
  return(total_sum / total_count)
}

#' Procesa series temporales mensuales para una variable con NIÑO3.4
#' @param var_name Nombre de la variable
#' @param data_file Ruta al archivo NetCDF
#' @param time Vector de fechas
#' @param lon_dim Dimensión de longitud
#' @param lat_dim Dimensión de latitud
#' @param var_descriptions Lista de descripciones de variables
#' @param units Unidades de medida
#' @param nino_data Dataframe con datos NIÑO3.4 (opcional)
#' @param output_dir Directorio para guardar datos intermedios (opcional)
#' @return Lista con gráficos de serie temporal y anomalía
process_timeseries <- function(var_name, data_file, time, lon_dim, lat_dim, 
                               var_descriptions, units, nino_data = NULL, 
                               output_dir = NULL) {
  
  description <- var_descriptions[var_name]
  
  nc <- ncdf4::nc_open(data_file)
  
  time_dim <- length(time)
  spatial_mean <- numeric(time_dim)
  
  block_size <- 12
  for (start_t in seq(1, time_dim, by = block_size)) {
    end_t <- min(start_t + block_size - 1, time_dim)
    n_times <- end_t - start_t + 1
    
    data_block <- ncdf4::ncvar_get(nc, var_name,
                                   start = c(1, 1, start_t),
                                   count = c(lon_dim, lat_dim, n_times))
    
    for (i in 1:n_times) {
      spatial_mean[start_t + i - 1] <- mean(data_block[,,i], na.rm = TRUE)
    }
    
    rm(data_block)
  }
  
  ncdf4::nc_close(nc)
  gc()
  
  df <- data.frame(
    date = time,
    value = spatial_mean
  )
  
  rm(spatial_mean)
  
  df$rolling_mean <- zoo::rollmean(df$value, k = 12, fill = NA, align = "center")
  
  mean_val <- mean(df$value, na.rm = TRUE)
  df$anomaly <- df$value - mean_val
  
  # Integrar datos NIÑO3.4 si están disponibles
  if (!is.null(nino_data)) {
    df <- merge(df, nino_data[, c("Date", "NINO34", "ENSO_phase")], 
                by.x = "date", by.y = "Date", all.x = TRUE)
  }
  
  # Guardar datos intermedios si se especifica directorio
  if (!is.null(output_dir)) {
    ts_file <- file.path(output_dir, paste0(var_name, "_timeseries_data.csv"))
    save_timeseries_data(df, ts_file, var_name)
  }
  
  stats <- list(
    min = min(df$value, na.rm = TRUE),
    max = max(df$value, na.rm = TRUE),
    mean = mean_val,
    sd = sd(df$value, na.rm = TRUE)
  )
  
  # Gráfico de serie temporal con NIÑO3.4
  if (!is.null(nino_data) && "NINO34" %in% names(df)) {
    # Escalar NIÑO3.4 para visualización
    nino_scaled <- df$NINO34 * (stats$sd / 2) + mean_val
    
    p1 <- plotly::plot_ly(df, x = ~date) %>%
      # Sombreado de fases ENSO
      plotly::add_trace(y = ~value, type = 'scatter', mode = 'lines',
                        name = 'Media Mensual',
                        line = list(color = '#2E86AB', width = 1.5),
                        fill = 'tozeroy',
                        fillcolor = 'rgba(46, 134, 171, 0.2)') %>%
      plotly::add_trace(y = ~rolling_mean, type = 'scatter', mode = 'lines',
                        name = 'Media Móvil 12 Meses',
                        line = list(color = '#E63946', width = 2.5)) %>%
      plotly::add_trace(y = nino_scaled, type = 'scatter', mode = 'lines',
                        name = 'NIÑO3.4 (escalado)',
                        line = list(color = '#FF9500', width = 1.5, dash = 'dot'),
                        yaxis = 'y2') %>%
      plotly::layout(
        title = list(text = paste0("<b>", description, " - Serie Temporal con NIÑO3.4</b>"),
                     font = list(size = 14)),
        xaxis = list(title = "<b>Tiempo</b>"),
        yaxis = list(title = paste0("<b>", units, "</b>")),
        yaxis2 = list(
          title = "<b>NIÑO3.4 (°C)</b>",
          overlaying = "y",
          side = "right",
          showgrid = FALSE,
          range = c(-3, 3)
        ),
        hovermode = "x unified",
        legend = list(orientation = "h", y = -0.15),
        annotations = list(
          list(
            x = 0.02, y = 0.98, xref = "paper", yref = "paper",
            text = sprintf("Min: %.3f | Max: %.3f | Media: %.3f | Std: %.3f",
                           stats$min, stats$max, stats$mean, stats$sd),
            showarrow = FALSE,
            bgcolor = "rgba(245, 222, 179, 0.9)",
            bordercolor = "black",
            font = list(family = "monospace", size = 10)
          )
        )
      )
    
    # Gráfico de anomalías con NIÑO3.4
    df$color <- ifelse(df$anomaly >= 0, "Positiva", "Negativa")
    
    p2 <- plotly::plot_ly(df, x = ~date) %>%
      plotly::add_trace(y = ~anomaly, type = 'bar',
                        color = ~color,
                        colors = c("Positiva" = "#2ca02c", "Negativa" = "#d62728"),
                        name = "Anomalía PFT") %>%
      plotly::add_trace(y = ~NINO34, type = 'scatter', mode = 'lines',
                        name = 'NIÑO3.4',
                        line = list(color = '#FF9500', width = 2)) %>%
      plotly::layout(
        title = list(text = paste0("<b>", description, " - Anomalía vs NIÑO3.4</b>"),
                     font = list(size = 14)),
        xaxis = list(title = "<b>Tiempo</b>"),
        yaxis = list(title = paste0("<b>Anomalía (", units, ") / NIÑO3.4 (°C)</b>")),
        barmode = 'relative',
        showlegend = TRUE,
        legend = list(orientation = "h", y = -0.15),
        shapes = list(
          list(type = "line", x0 = min(df$date), x1 = max(df$date),
               y0 = 0.5, y1 = 0.5, line = list(color = "#E74C3C", dash = "dash", width = 1)),
          list(type = "line", x0 = min(df$date), x1 = max(df$date),
               y0 = -0.5, y1 = -0.5, line = list(color = "#3498DB", dash = "dash", width = 1))
        )
      )
    
  } else {
    # Gráfico sin NIÑO3.4 (comportamiento original)
    p1 <- plotly::plot_ly(df, x = ~date) %>%
      plotly::add_trace(y = ~value, type = 'scatter', mode = 'lines',
                        name = 'Media Mensual',
                        line = list(color = '#2E86AB', width = 1.5),
                        fill = 'tozeroy',
                        fillcolor = 'rgba(46, 134, 171, 0.2)') %>%
      plotly::add_trace(y = ~rolling_mean, type = 'scatter', mode = 'lines',
                        name = 'Media Móvil 12 Meses',
                        line = list(color = '#E63946', width = 2.5)) %>%
      plotly::layout(
        title = list(text = paste0("<b>", description, " - Serie Temporal Mensual</b>"),
                     font = list(size = 14)),
        xaxis = list(title = "<b>Tiempo</b>"),
        yaxis = list(title = paste0("<b>", units, "</b>")),
        hovermode = "x unified",
        annotations = list(
          list(
            x = 0.02, y = 0.98, xref = "paper", yref = "paper",
            text = sprintf("Min: %.3f | Max: %.3f | Media: %.3f | Std: %.3f",
                           stats$min, stats$max, stats$mean, stats$sd),
            showarrow = FALSE,
            bgcolor = "rgba(245, 222, 179, 0.9)",
            bordercolor = "black",
            font = list(family = "monospace", size = 10)
          )
        )
      )
    
    df$color <- ifelse(df$anomaly >= 0, "Positiva", "Negativa")
    
    p2 <- plotly::plot_ly(df, x = ~date, y = ~anomaly, type = 'bar',
                          color = ~color,
                          colors = c("Positiva" = "#2ca02c", "Negativa" = "#d62728")) %>%
      plotly::layout(
        title = list(text = paste0("<b>", description, " - Anomalía Mensual</b>"),
                     font = list(size = 14)),
        xaxis = list(title = "<b>Tiempo</b>"),
        yaxis = list(title = paste0("<b>Anomalía (", units, ")</b>")),
        barmode = 'relative',
        showlegend = TRUE
      )
  }
  
  return(list(timeseries = p1, anomaly = p2, stats = stats, data = df))
}

#' Crea mapa de diferencias con plotly y guarda datos intermedios
#' @param diff_data Matriz de diferencias
#' @param lon Vector de longitudes
#' @param lat Vector de latitudes
#' @param period1 Nombre del primer período
#' @param period2 Nombre del segundo período
#' @param units Unidades de medida
#' @param var_name Nombre de la variable (opcional, para guardar datos)
#' @param output_dir Directorio de salida para datos intermedios (opcional)
#' @return Gráfico plotly
create_diff_map_plotly <- function(diff_data, lon, lat, period1, period2, units,
                                    var_name = NULL, output_dir = NULL) {
  df <- expand.grid(lon = lon, lat = lat)
  df$value <- as.vector(diff_data)
  df <- df[!is.na(df$value), ]
  
  if (nrow(df) == 0) return(NULL)
  
  # Guardar datos intermedios si se especifica
  if (!is.null(output_dir) && !is.null(var_name)) {
    data_file <- file.path(output_dir, 
                           paste0(var_name, "_diff_", period1, "_vs_", period2, ".csv"))
    metadata <- list(
      variable = var_name,
      period1 = period1,
      period2 = period2,
      units = units,
      created = as.character(Sys.time())
    )
    save_map_data(diff_data, lon, lat, data_file, metadata)
  }
  
  max_abs <- max(abs(df$value), na.rm = TRUE)
  
  p <- plotly::plot_ly(df, x = ~lon, y = ~lat, z = ~value, type = 'heatmap',
                       colorscale = list(
                         list(0, "#2166ac"),
                         list(0.5, "#f7f7f7"),
                         list(1, "#b2182b")
                       ),
                       zmin = -max_abs, zmax = max_abs,
                       colorbar = list(title = paste0("Δ ", units))) %>%
    plotly::layout(
      title = list(text = paste0("<b>", period2, " - ", period1, "</b>"),
                   font = list(size = 12)),
      xaxis = list(title = "Longitud", scaleanchor = "y"),
      yaxis = list(title = "Latitud"),
      aspectratio = list(x = 1, y = 1)
    )
  
  return(p)
}

#' Crea comparación estacional
#' @param seasonal_values Lista de valores estacionales por período
#' @param var_name Nombre de la variable
#' @param description Descripción de la variable
#' @param periods Lista de períodos quinquenales
#' @param seasons Lista de estaciones
#' @param units Unidades de medida
#' @return Lista con gráficos de barras y líneas
create_seasonal_comparison <- function(seasonal_values, var_name, description, 
                                        periods, seasons, units) {
  df <- expand.grid(
    Period = names(periods),
    Season = names(seasons),
    stringsAsFactors = FALSE
  )
  
  df$Value <- sapply(1:nrow(df), function(i) {
    seasonal_values[[df$Season[i]]][[df$Period[i]]]
  })
  
  df$Period <- factor(df$Period, levels = names(periods))
  df$Season <- factor(df$Season, levels = names(seasons))
  
  season_colors <- c(
    "Primavera" = "#2ecc71",
    "Verano" = "#e74c3c",
    "Otoño" = "#f39c12",
    "Invierno" = "#3498db"
  )
  
  p1 <- plotly::plot_ly(df, x = ~Period, y = ~Value, color = ~Season,
                        colors = season_colors,
                        type = 'bar',
                        text = ~round(Value, 3),
                        textposition = 'outside') %>%
    plotly::layout(
      title = list(text = paste0("<b>", description, 
                                 " - Promedios Estacionales por Quinquenio</b>"),
                   font = list(size = 14)),
      xaxis = list(title = "<b>Período Quinquenal</b>"),
      yaxis = list(title = paste0("<b>", units, "</b>")),
      barmode = 'group',
      legend = list(title = list(text = "<b>Estación</b>"))
    )
  
  p2 <- plotly::plot_ly(df, x = ~Period, y = ~Value, color = ~Season,
                        colors = season_colors,
                        type = 'scatter', mode = 'lines+markers',
                        line = list(width = 2.5),
                        marker = list(size = 10)) %>%
    plotly::layout(
      title = list(text = paste0("<b>", description, 
                                 " - Tendencias Estacionales</b>"),
                   font = list(size = 14)),
      xaxis = list(title = "<b>Período Quinquenal</b>"),
      yaxis = list(title = paste0("<b>", units, "</b>")),
      legend = list(title = list(text = "<b>Estación</b>"))
    )
  
  return(list(bars = p1, lines = p2, data = df))
}
