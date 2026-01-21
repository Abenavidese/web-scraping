# ARQUITECTURA DEL SISTEMA - MASTER SCRAPER PARALELO

## 📐 Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO                                   │
│                       ↓                                      │
│              python master_scraper.py                        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              MASTER SCRAPER (Proceso Principal)              │
│                                                              │
│  1. Solicita parámetros UNA VEZ:                            │
│     • Tema de búsqueda                                      │
│     • Número de posts                                       │
│     • Número de comentarios                                 │
│                                                              │
│  2. Crea Pool de Multiprocessing (4 procesos)               │
└─────────────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓                ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PROCESO 1   │ │  PROCESO 2   │ │  PROCESO 3   │ │  PROCESO 4   │
│              │ │              │ │              │ │              │
│  X/Twitter   │ │  Instagram   │ │  Facebook    │ │  LinkedIn    │
│              │ │              │ │              │ │              │
│  main.py     │ │  scraper.py  │ │  scraper.py  │ │  main.py     │
│  --query     │ │  --query     │ │  --query     │ │  --query     │
│  --posts     │ │  --posts     │ │  --posts     │ │  --posts     │
│  --comments  │ │  --comments  │ │  --comments  │ │  --comments  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        ↓                ↓                ↓                ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  EXTRACCIÓN  │ │  EXTRACCIÓN  │ │  EXTRACCIÓN  │ │  EXTRACCIÓN  │
│              │ │              │ │              │ │              │
│  • Login     │ │  • Login     │ │  • Login     │ │  • Cookie    │
│  • Búsqueda  │ │  • Hashtag   │ │  • Búsqueda  │ │  • Búsqueda  │
│  • Posts     │ │  • Posts     │ │  • Posts     │ │  • Posts     │
│  • Comentar. │ │  • Comentar. │ │  • Comentar. │ │  • Comentar. │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        ↓                ↓                ↓                ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ PROCESAMIENTO│ │ PROCESAMIENTO│ │ PROCESAMIENTO│ │ PROCESAMIENTO│
│     NLP      │ │     NLP      │ │     NLP      │ │     NLP      │
│              │ │              │ │              │ │              │
│  1. Limpieza │ │  1. Limpieza │ │  1. Limpieza │ │  1. Limpieza │
│  2. Tokeniz. │ │  2. Tokeniz. │ │  2. Tokeniz. │ │  2. Tokeniz. │
│  3. Stopword │ │  3. Stopword │ │  3. Stopword │ │  3. Stopword │
│  4. Stemming │ │  4. Stemming │ │  4. Stemming │ │  4. Stemming │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        ↓                ↓                ↓                ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ RESULTADOS   │ │ RESULTADOS   │ │ RESULTADOS   │ │ RESULTADOS   │
│              │ │              │ │              │ │              │
│  • CSV       │ │  • JSON      │ │  • JSON      │ │  • CSV       │
│  • JSON      │ │  • CSV       │ │  • CSV       │ │  • PNG       │
│  • PNG       │ │  • PNG       │ │  • PNG       │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        ↓                ↓                ↓                ↓
        └────────────────┼────────────────┘                
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              MASTER SCRAPER (Recolección)                    │
│                                                              │
│  3. Espera a que todos los procesos terminen                │
│  4. Recolecta resultados de cada proceso                    │
│  5. Calcula métricas:                                       │
│     • Tiempo individual de cada scraper                     │
│     • Tiempo total paralelo                                 │
│     • Speedup = T_secuencial / T_paralelo                   │
│     • Eficiencia = Speedup / N_procesos                     │
│  6. Genera log detallado                                    │
│  7. Muestra resumen en pantalla                             │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    RESULTADOS FINALES                        │
│                                                              │
│  • logs/execution_log_YYYYMMDD_HHMMSS.txt                   │
│  • Datos de X/Twitter en x_scrapper/output/                 │
│  • Datos de Instagram en App_Paralela_Instagram/Resultados/ │
│  • Datos de Facebook en App_Paralela_facebook/Resultados/   │
│  • Datos de LinkedIn en linkedin_scrapper/output/           │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Flujo de Datos

### 1. Entrada (Input)
```
Usuario → Master Scraper
  ├─ Tema: "Inteligencia Artificial"
  ├─ Posts: 10
  └─ Comentarios: 5
```

### 2. Distribución Paralela
```
Master Scraper → multiprocessing.Pool.starmap()
  ├─ Proceso 1: X/Twitter (--query "IA" --posts 10 --comments 5)
  ├─ Proceso 2: Instagram (--query "IA" --posts 10 --comments 5)
  ├─ Proceso 3: Facebook (--query "IA" --posts 10 --comments 5)
  └─ Proceso 4: LinkedIn (--query "IA" --posts 10 --comments 5)
```

### 3. Procesamiento Paralelo
```
Cada Proceso (independiente):
  1. Extracción de datos (Playwright/Selenium)
  2. Procesamiento NLP
     ├─ Limpieza (URLs, emojis, puntuación)
     ├─ Tokenización
     ├─ Eliminación de stopwords
     └─ Stemming/Lemmatization
  3. Generación de visualizaciones
  4. Guardado de resultados
```

### 4. Salida (Output)
```
Cada Proceso → Archivos independientes
Master Scraper → Log consolidado + Métricas
```

## 📊 Métricas de Rendimiento

### Tiempos de Ejecución

```
┌─────────────────────────────────────────────────────────┐
│                  EJECUCIÓN SECUENCIAL                    │
│                                                          │
│  X/Twitter:   [████████████████████] 42.15s             │
│  Instagram:   [████████████████] 38.67s                 │
│  Facebook:    [█████████████████████] 45.32s            │
│  LinkedIn:    [███████████████████] 40.89s              │
│                                                          │
│  TOTAL: 167.03 segundos                                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  EJECUCIÓN PARALELA                      │
│                                                          │
│  X/Twitter:   [████████████████████] 42.15s             │
│  Instagram:   [████████████████] 38.67s                 │
│  Facebook:    [█████████████████████] 45.32s ← Máximo   │
│  LinkedIn:    [███████████████████] 40.89s              │
│                                                          │
│  TOTAL: 45.32 segundos (tiempo del más lento)           │
└─────────────────────────────────────────────────────────┘

Speedup: 167.03s / 45.32s = 3.69x
Eficiencia: 3.69 / 4 = 92.16%
Tiempo ahorrado: 121.71s (72.87%)
```

## 🏗️ Componentes del Sistema

### Master Scraper (`master_scraper.py`)

```python
class SocialMediaScraperManager:
    ├─ __init__()           # Configuración de scrapers
    ├─ print_header()       # Encabezado visual
    ├─ run_scraper()        # Ejecuta un scraper individual
    ├─ run_parallel()       # Orquesta ejecución paralela
    ├─ print_summary()      # Muestra resumen de resultados
    └─ save_log()           # Guarda log detallado
```

### Scrapers Individuales

#### X/Twitter (`x_scrapper/main.py`)
```python
async def main():
    ├─ argparse              # Parseo de argumentos CLI
    ├─ XScraper              # Extracción con Playwright
    ├─ process_data_parallel # Procesamiento NLP
    └─ generate_wordcloud    # Visualizaciones
```

#### Instagram (`App_Paralela_Instagram/scraper.py`)
```python
def run():
    ├─ argparse                  # Parseo de argumentos CLI
    ├─ Playwright (sync)         # Extracción
    ├─ procesamiento_texto       # Pipeline NLP
    └─ visualizar_nube_palabras  # Visualizaciones
```

#### Facebook (`App_Paralela_facebook/scraper.py`)
```python
def run():
    ├─ argparse                  # Parseo de argumentos CLI
    ├─ Playwright (sync)         # Extracción
    ├─ procesamiento_texto       # Pipeline NLP
    └─ visualizar_nube_palabras  # Visualizaciones
```

#### LinkedIn (`linkedin_scrapper/main.py`)
```python
async def main():
    ├─ argparse              # Parseo de argumentos CLI
    ├─ LinkedInScraper       # Extracción con cookie
    ├─ NLPProcessor          # Pipeline NLP completo
    └─ matplotlib            # Visualizaciones
```

## 🔐 Autenticación

```
┌─────────────────────────────────────────────────────────┐
│  X/Twitter                                               │
│  ├─ Usuario/Contraseña en variables de entorno          │
│  └─ Login automático con Playwright                     │
├─────────────────────────────────────────────────────────┤
│  Instagram                                               │
│  ├─ Sesión guardada en auth.json                        │
│  └─ Login automático si no existe sesión                │
├─────────────────────────────────────────────────────────┤
│  Facebook                                                │
│  ├─ Sesión guardada en auth_fb.json                     │
│  └─ Login automático si no existe sesión                │
├─────────────────────────────────────────────────────────┤
│  LinkedIn                                                │
│  ├─ Cookie li_at en config.py                           │
│  └─ Inyección de cookie en navegador                    │
└─────────────────────────────────────────────────────────┘
```

## 📦 Estructura de Archivos

```
lab_social_media/
│
├── master_scraper.py              ← EJECUTAR ESTE
├── README_MASTER_SCRAPER.md
├── RESUMEN_CAMBIOS.md
├── INSTRUCCIONES_USO.md
├── GUIA_RAPIDA.py
│
├── logs/                          ← Logs generados
│   └── execution_log_*.txt
│
├── x_scrapper/
│   ├── main.py                    ← Modificado (argparse)
│   ├── scraper.py
│   ├── processor.py
│   ├── visualization.py
│   └── output/                    ← Resultados X
│       ├── tweets_raw.csv
│       ├── tweets_processed.csv
│       ├── tweets_refined.csv
│       ├── wordcloud.png
│       └── frequency_plot.png
│
├── App_Paralela_Instagram/
│   ├── scraper.py                 ← Modificado (argparse)
│   ├── procesamiento_texto.py
│   └── Resultados/                ← Resultados Instagram
│       ├── results_*.json
│       ├── processed_*.json
│       ├── processed_*.csv
│       └── frecuencia_*.png
│
├── App_Paralela_facebook/
│   ├── scraper.py                 ← Modificado (argparse)
│   ├── procesamiento_texto.py
│   └── Resultados/                ← Resultados Facebook
│       ├── results_facebook_*.json
│       ├── processed_facebook_*.json
│       ├── processed_facebook_*.csv
│       └── frecuencia_facebook_*.png
│
└── linkedin_scrapper/
    ├── main.py                    ← Modificado (argparse)
    ├── config.py
    ├── scrapers/
    │   └── linkedin_scraper.py
    ├── utils/
    │   └── nlp_processor.py
    └── output/                    ← Resultados LinkedIn
        ├── datos_extraidos.csv
        └── frecuencia_palabras.png
```

## 🎓 Cumplimiento de Requisitos de la Práctica

### ✅ Requisito 1: Extracción Paralela
- **Implementado**: `multiprocessing.Pool` con 4 procesos
- **Evidencia**: Tiempos de ejecución simultáneos en logs

### ✅ Requisito 2: Múltiples Redes Sociales
- **Implementado**: X, Instagram, Facebook, LinkedIn
- **Evidencia**: 4 carpetas de resultados independientes

### ✅ Requisito 3: Pipeline de Procesamiento de Texto
1. **Limpieza y normalización** ✅
   - Minúsculas, puntuación, URLs, emojis
2. **Tokenización** ✅
   - División en palabras/tokens
3. **Stopwords** ✅
   - Eliminación de palabras comunes
4. **Stemming/Lemmatization** ✅
   - Forma canónica de palabras

### ✅ Requisito 4: Visualizaciones
- **Bolsa de palabras** ✅
- **Nubes de palabras** ✅
- **Gráficos de frecuencia** ✅

### ✅ Requisito 5: Medición de Tiempos
- **Tiempos individuales** ✅
- **Tiempo total** ✅
- **Métricas de paralelización** ✅

## 🚀 Ventajas Técnicas

1. **Escalabilidad**: Fácil agregar más redes sociales
2. **Modularidad**: Cada scraper es independiente
3. **Robustez**: Si un scraper falla, los demás continúan
4. **Eficiencia**: Aprovecha múltiples núcleos del CPU
5. **Mantenibilidad**: Código organizado y documentado

---

**Autor**: Sistema de Extracción Paralela de Redes Sociales  
**Curso**: Computación Paralela - ESPE  
**Docente**: Ing. Gabriel León Paredes, PhD.
