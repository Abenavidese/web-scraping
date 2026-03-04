# Academic Metrics System - Usage Guide

## Overview

The Academic Metrics System automatically collects comprehensive metrics for every scraping run, generating three files per execution:

1. **`run_<uuid>_metrics.json`** - Complete metrics in JSON format
2. **`run_<uuid>_dataset.csv`** - Dataset with all extracted comments and sentiments
3. **`run_<uuid>.log`** - Timestamped execution log

All files are saved in the `runs/` directory at the project root.

## Metrics Categories

### 1. Experiment Identification
```json
{
  "run_id": "051a1a3d-23c6-437b-a62b-cc0fbb19f646",
  "query": "Inteligencia Artificial",
  "date_time_start": "2026-02-17T20:41:39.382268",
  "date_time_end": "2026-02-17T20:41:41.383333",
  "mode": "parallel",
  "n_processes": 4,
  "platforms_enabled": ["x", "instagram", "facebook", "linkedin"]
}
```

### 2. Data Volume
```json
{
  "total_comments_extracted": 200,
  "comments_per_platform": {
    "x": 50,
    "instagram": 50,
    "facebook": 50,
    "linkedin": 50
  },
  "total_posts_scraped": 40,
  "posts_per_platform": {...},
  "duplicates_removed": 0,
  "comments_after_cleaning": 0,
  "failed_items": {}
}
```

### 3. Timing (all in seconds)
```json
{
  "time_total_s": 2.001065,
  "time_scraping_total_s": 2.000671,
  "time_scraping_per_platform_s": {
    "x": 0.5,
    "instagram": 0.5,
    "facebook": 0.5,
    "linkedin": 0.5
  },
  "time_preprocess_s": 2.5,
  "time_llm_inference_s": 8.3,
  "avg_time_per_comment_s": 0.01
}
```

### 4. Performance & Scalability
```json
{
  "throughput_comments_per_min": 5996.81,
  "throughput_comments_per_hour": 359808.6,
  "speedup": 3.5,  // Only when both parallel and sequential runs exist
  "efficiency": 87.5  // (speedup / n_processes) * 100
}
```

### 5. Classification Quality
```json
{
  "sentiment_counts": {
    "positive": 150,
    "negative": 50,
    "neutral": 100,
    "mixed": 0,
    "unknown": 0
  },
  "sentiment_percentages": {
    "positive": 50.0,
    "negative": 16.67,
    "neutral": 33.33,
    "mixed": 0.0,
    "unknown": 0.0
  },
  "manual_validation": null  // Optional
}
```

### 6. Scraping Robustness
```json
{
  "errors_per_platform": {
    "x": 1,
    "instagram": 1,
    "facebook": 1,
    "linkedin": 1
  },
  "error_types": ["timeout", "selector_not_found"],
  "retries_per_platform": {...},
  "blocked_detected": false
}
```

### 7. Execution Environment
```json
{
  "cpu_info": "Intel64 Family 6 Model 198 Stepping 2, GenuineIntel",
  "num_cores": 24,
  "num_logical_cores": 24,
  "ram_gb": 31.43,
  "os": "Windows 11",
  "python_version": "3.14.0",
  "machine": "AMD64"
}
```

## Usage Examples

### Example 1: Run Parallel Scraping

```bash
cd c:\Users\EleXc\Music\limpieza_scratching\lab_social_media
python master_scraper.py
```

**User Input:**
```
Ingrese el tema de búsqueda: Inteligencia Artificial
Modo de scraping: [1] Por posts (antiguo) [2] Por comentarios (nuevo): 2
Número objetivo de comentarios totales: 800
Máximo de posts a scrapear: 200
```

**Output:**
```
✅ Archivos académicos generados:
   📊 Métricas: C:\...\runs\run_abc123_metrics.json
   📄 Dataset: C:\...\runs\run_abc123_dataset.csv
   📝 Log: C:\...\runs\run_abc123.log
```

### Example 2: Calculate Speedup

To calculate speedup and efficiency, run both modes with the same query:

**Step 1: Run Sequential**
```bash
python master_scraper.py
# Select option: [2] Modo Secuencial
# Use query: "Machine Learning"
# Posts: 10, Comments: 5
```

**Step 2: Run Parallel**
```bash
python master_scraper.py
# Select option: [1] Modo Paralelo (default)
# Use SAME query: "Machine Learning"
# Posts: 10, Comments: 5
```

**Step 3: Compare Metrics**
```python
import json

# Load both metrics files
with open('runs/run_sequential_uuid_metrics.json') as f:
    seq_metrics = json.load(f)

with open('runs/run_parallel_uuid_metrics.json') as f:
    par_metrics = json.load(f)

# Calculate speedup manually
seq_time = seq_metrics['timing']['time_total_s']
par_time = par_metrics['timing']['time_total_s']
speedup = seq_time / par_time
efficiency = (speedup / 4) * 100

print(f"Sequential Time: {seq_time:.2f}s")
print(f"Parallel Time: {par_time:.2f}s")
print(f"Speedup: {speedup:.2f}x")
print(f"Efficiency: {efficiency:.2f}%")
```

### Example 3: Analyze Results for Paper

```python
import json
import pandas as pd
from pathlib import Path

# Load all metrics from runs directory
runs_dir = Path('runs')
all_metrics = []

for metrics_file in runs_dir.glob('*_metrics.json'):
    with open(metrics_file) as f:
        metrics = json.load(f)
        all_metrics.append({
            'run_id': metrics['experiment_id']['run_id'],
            'query': metrics['experiment_id']['query'],
            'mode': metrics['experiment_id']['mode'],
            'total_comments': metrics['data_volume']['total_comments_extracted'],
            'total_time': metrics['timing']['time_total_s'],
            'throughput_per_min': metrics['performance']['throughput_comments_per_min'],
            'speedup': metrics['performance']['speedup'],
            'efficiency': metrics['performance']['efficiency']
        })

# Create DataFrame
df = pd.DataFrame(all_metrics)

# Filter parallel runs only
parallel_runs = df[df['mode'] == 'parallel']

# Calculate statistics
print("=== PARALLEL EXECUTION STATISTICS ===")
print(f"Average Throughput: {parallel_runs['throughput_per_min'].mean():.2f} comments/min")
print(f"Average Speedup: {parallel_runs['speedup'].mean():.2f}x")
print(f"Average Efficiency: {parallel_runs['efficiency'].mean():.2f}%")
print(f"Total Comments Processed: {parallel_runs['total_comments'].sum()}")

# Export for paper
df.to_csv('runs/paper_analysis.csv', index=False)
print("\n✅ Analysis exported to runs/paper_analysis.csv")
```

## Dataset CSV Format

The `run_<uuid>_dataset.csv` file contains all extracted comments with sentiment analysis:

| Column | Description |
|--------|-------------|
| `run_id` | Unique run identifier |
| `platform` | Social media platform (x, instagram, facebook, linkedin) |
| `post_id` | Post identifier |
| `comment_id` | Comment identifier |
| `text` | Comment text |
| `sentiment` | Sentiment classification (positive, negative, neutral, mixed) |
| `sentiment_score` | Confidence score (0-1) |
| `reasoning` | LLM explanation for the sentiment |
| `terms` | Key terms extracted (optional) |
| `timestamp` | Extraction timestamp (ISO 8601) |

## Log File Format

The `run_<uuid>.log` file contains timestamped events:

```
[2026-02-17 20:41:39.382] [INFO] RUN_START run_id=051a1a3d-23c6-437b-a62b-cc0fbb19f646
[2026-02-17 20:41:39.383] [INFO] RUN_START query='Inteligencia Artificial' mode=parallel platforms=['x', 'instagram', 'facebook', 'linkedin']
[2026-02-17 20:41:39.384] [INFO] PLATFORM_START platform=x
[2026-02-17 20:41:39.884] [INFO] PLATFORM_END platform=x posts=10 comments=50 errors=1
[2026-02-17 20:41:39.885] [INFO] PREPROCESS_TIME time=2.50s
[2026-02-17 20:41:40.185] [INFO] LLM_TIME time=8.30s
[2026-02-17 20:41:41.383] [INFO] RUN_END total_time=2.00s comments=200
[2026-02-17 20:41:41.384] [INFO] EXPORT_METRICS path=C:\...\runs\run_051a1a3d_metrics.json
[2026-02-17 20:41:41.385] [INFO] EXPORT_DATASET path=C:\...\runs\run_051a1a3d_dataset.csv rows=1
```

## Programmatic Usage

You can also use the `AcademicMetricsCollector` directly in your code:

```python
from shared.academic_metrics import AcademicMetricsCollector

# Initialize
collector = AcademicMetricsCollector()

# Start run
collector.start_run(
    query="Machine Learning",
    mode="parallel",
    platforms=["x", "instagram", "facebook", "linkedin"],
    n_processes=4
)

# Record platform execution
collector.record_platform_start("x")
# ... scraping happens ...
collector.record_platform_end("x", posts=10, comments=50, errors=0)

# Record timing
collector.record_preprocessing_time(2.5)
collector.record_llm_time(8.3)

# Record sentiments
for sentiment in ["positive", "positive", "negative", "neutral"]:
    collector.add_sentiment_result(sentiment)

# Add dataset rows
collector.add_dataset_row(
    platform="x",
    post_id="123",
    comment_id="456",
    text="Great product!",
    sentiment="positive",
    sentiment_score=0.95,
    reasoning="Expresses satisfaction"
)

# End run
collector.end_run()

# Export all files
files = collector.export_all()
print(f"Metrics: {files['metrics']}")
print(f"Dataset: {files['dataset']}")
print(f"Log: {files['log']}")

# Print summary
print(collector.get_summary())
```

## Tips for Academic Papers

### For Methods Section
- Use `environment` data to describe experimental setup
- Reference `n_processes` and hardware specs
- Cite `platforms_enabled` for data sources

### For Results Section
- Use `timing` data for execution time comparisons
- Use `performance.speedup` and `performance.efficiency` for parallelization analysis
- Use `data_volume` for dataset statistics
- Use `quality.sentiment_distribution` for classification results

### For Discussion Section
- Use `robustness` data to discuss challenges and limitations
- Reference `error_types` and `blocked_detected` for reliability analysis
- Use `throughput` metrics for scalability discussion

### For Tables/Figures
```python
# Example: Create comparison table
import pandas as pd

data = {
    'Mode': ['Sequential', 'Parallel'],
    'Time (s)': [167.03, 45.32],
    'Speedup': [1.0, 3.69],
    'Efficiency (%)': [100.0, 92.16],
    'Comments/min': [287.5, 1060.2]
}

df = pd.DataFrame(data)
df.to_latex('table_performance.tex', index=False)
```

## Troubleshooting

### Issue: No dataset.csv generated
**Cause**: No data was added via `add_dataset_row()`  
**Solution**: Ensure scrapers are populating the dataset

### Issue: Speedup is null
**Cause**: No sequential time was set  
**Solution**: Run sequential mode first, or use `set_sequential_time()`

### Issue: Metrics file is missing timing data
**Cause**: `end_run()` was not called  
**Solution**: Always call `end_run()` before exporting

## File Locations

- **Metrics Files**: `c:\Users\EleXc\Music\limpieza_scratching\lab_social_media\runs\`
- **Legacy Logs**: `c:\Users\EleXc\Music\limpieza_scratching\lab_social_media\logs\`
- **Scraper Outputs**: `c:\Users\EleXc\Music\limpieza_scratching\lab_social_media\users\{user_id}\{platform}\{query}\`

## Next Steps

1. Run multiple experiments with different queries
2. Collect metrics from all runs
3. Analyze results using pandas/numpy
4. Generate visualizations for paper
5. Calculate statistical significance
6. Write up findings in academic format
