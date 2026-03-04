# 📊 ESTADÍSTICAS COMPLETAS - Daniel Noboa

## 🆔 Identificación del Experimento

```json
{
  "run_id": "de0df4cc-b84d-43cf-8f13-6a378a88e2dc",
  "query": "Daniel Noboa",
  "date_time_start": "2026-02-17T20:50:29.535900",
  "date_time_end": "2026-02-17T20:52:50.625792",
  "mode": "parallel",
  "n_processes": 4
}
```

---

## 💻 Recursos del Sistema

### Hardware Utilizado

| Recurso | Especificación |
|---------|----------------|
| **CPU** | Intel64 Family 6 Model 198 Stepping 2, GenuineIntel |
| **Núcleos Físicos** | 24 |
| **Núcleos Lógicos** | 24 |
| **RAM Total** | **31.43 GB** |
| **OS** | Windows 11 |
| **Python** | 3.14.0 |
| **Arquitectura** | AMD64 |

> **Nota**: El sistema tiene **31.43 GB de RAM** disponible. Durante la ejecución, el scraper utilizó memoria para:
> - 4 procesos paralelos (uno por plataforma)
> - Almacenamiento temporal de datos
> - Procesamiento NLP
> - Análisis de sentimientos con LLM

---

## 📈 Volumen de Datos Procesados

### Por Plataforma

| Plataforma | Posts | Comentarios | % del Total |
|------------|-------|-------------|-------------|
| X (Twitter) | 10 | 32 | 27.12% |
| Instagram | 10 | 44 | 37.29% |
| Facebook | 7 | 35 | 29.66% |
| LinkedIn | 10 | 7 | 5.93% |
| **TOTAL** | **37** | **118** | **100%** |

### Estadísticas Generales

- **Total de comentarios extraídos**: 118
- **Total de posts scrapeados**: 37
- **Duplicados removidos**: 0
- **Comentarios después de limpieza**: 0
- **Items fallidos**: 0

---

## ⏱️ Tiempos de Ejecución

### Tiempo Total

```
Inicio:  2026-02-17 20:50:29
Fin:     2026-02-17 20:52:50
Duración: 141.09 segundos (2 min 21 seg)
```

### Desglose por Etapa

| Etapa | Tiempo (s) | % del Total |
|-------|-----------|-------------|
| **Scraping Total** | 141.09 | 100% |
| - X (Twitter) | 50.81 | 36.0% |
| - Instagram | 55.37 | 39.2% |
| - Facebook | 87.72 | 62.2% |
| - LinkedIn | 91.69 | 65.0% |
| **Preprocesamiento NLP** | 29.95 | 21.2% |
| **Análisis de Sentimientos (LLM)** | 76.41 | 54.2% |
| **Promedio por Comentario** | 1.20 | - |

> **Nota**: Los tiempos de plataforma se ejecutan en paralelo, por eso la suma supera el 100%

---

## 🚀 Métricas de Rendimiento

### Throughput

- **Comentarios por minuto**: 50.18
- **Comentarios por hora**: 3,010.8
- **Tiempo promedio por comentario**: 1.20 segundos

### Escalabilidad

- **Speedup**: null (requiere ejecución secuencial para comparar)
- **Efficiency**: null (se calcula con speedup)
- **Procesos paralelos**: 4

---

## 💭 Calidad de Clasificación

### Distribución de Sentimientos

| Sentimiento | Cantidad | Porcentaje |
|-------------|----------|------------|
| **Positivo** 😊 | 31 | 50.0% |
| **Negativo** 😠 | 20 | 32.26% |
| **Neutral** 😐 | 11 | 17.74% |
| **Mixto** 🤔 | 0 | 0.0% |
| **Desconocido** ❓ | 0 | 0.0% |

**Total analizado**: 62 items (posts + comentarios seleccionados)

---

## 🛡️ Robustez del Scraping

### Errores por Plataforma

| Plataforma | Errores | Reintentos | Estado |
|------------|---------|------------|--------|
| X (Twitter) | 0 | 0 | ✅ |
| Instagram | 0 | 0 | ✅ |
| Facebook | 0 | 0 | ✅ |
| LinkedIn | 0 | 0 | ✅ |

### Resumen de Robustez

- **Total de errores**: 0
- **Tipos de error**: Ninguno
- **Bloqueos detectados**: No
- **Tasa de éxito**: 100%

---

## 📁 Archivos del Run

### Ubicación

```
c:\Users\EleXc\Music\limpieza_scratching\lab_social_media\runs\
```

### Archivos Generados

1. **`run_de0df4cc-b84d-43cf-8f13-6a378a88e2dc_metrics.json`**
   - Tamaño: 2,231 bytes
   - Contiene: Todas las métricas en formato JSON

2. **`run_de0df4cc-b84d-43cf-8f13-6a378a88e2dc.log`**
   - Tamaño: 1,370 bytes
   - Contiene: Log de ejecución con timestamps

3. **`RESUMEN_Daniel_Noboa.md`**
   - Resumen ejecutivo en Markdown

---

## 📊 Datos para el Paper

### Tabla de Recursos

```latex
\begin{table}[h]
\centering
\begin{tabular}{lr}
\hline
\textbf{Recurso} & \textbf{Valor} \\
\hline
CPU & Intel 24 cores \\
RAM & 31.43 GB \\
OS & Windows 11 \\
Python & 3.14.0 \\
Procesos & 4 paralelos \\
\hline
\end{tabular}
\caption{Ambiente de ejecución}
\end{table}
```

### Tabla de Resultados

```latex
\begin{table}[h]
\centering
\begin{tabular}{lrrr}
\hline
\textbf{Plataforma} & \textbf{Posts} & \textbf{Comentarios} & \textbf{Tiempo (s)} \\
\hline
X (Twitter) & 10 & 32 & 50.81 \\
Instagram & 10 & 44 & 55.37 \\
Facebook & 7 & 35 & 87.72 \\
LinkedIn & 10 & 7 & 91.69 \\
\hline
\textbf{Total} & \textbf{37} & \textbf{118} & \textbf{141.09} \\
\hline
\end{tabular}
\caption{Resultados del scraping paralelo - Daniel Noboa}
\end{table}
```

---

## 🔍 Cómo Acceder a los Datos

### Opción 1: Leer el JSON directamente

```python
import json

with open('runs/run_de0df4cc-b84d-43cf-8f13-6a378a88e2dc_metrics.json') as f:
    metrics = json.load(f)

# Acceder a datos específicos
print(f"Run ID: {metrics['experiment_id']['run_id']}")
print(f"RAM: {metrics['environment']['ram_gb']} GB")
print(f"CPU: {metrics['environment']['cpu_info']}")
print(f"Comentarios: {metrics['data_volume']['total_comments_extracted']}")
print(f"Tiempo total: {metrics['timing']['time_total_s']:.2f}s")
```

### Opción 2: Ver el archivo JSON completo

Abre el archivo:
```
c:\Users\EleXc\Music\limpieza_scratching\lab_social_media\runs\run_de0df4cc-b84d-43cf-8f13-6a378a88e2dc_metrics.json
```

### Opción 3: Ver el log de ejecución

Abre el archivo:
```
c:\Users\EleXc\Music\limpieza_scratching\lab_social_media\runs\run_de0df4cc-b84d-43cf-8f13-6a378a88e2dc.log
```

---

## 📌 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Run ID** | `de0df4cc-b84d-43cf-8f13-6a378a88e2dc` |
| **Query** | Daniel Noboa |
| **RAM del Sistema** | **31.43 GB** |
| **CPU** | Intel 24 cores |
| **Tiempo Total** | 141.09 segundos |
| **Comentarios Extraídos** | 118 |
| **Posts Scrapeados** | 37 |
| **Throughput** | 50.18 comentarios/min |
| **Errores** | 0 |
| **Tasa de Éxito** | 100% |

---

**Generado**: 2026-02-17 20:58:30
