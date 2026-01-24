# 🎭 Análisis de Sentimientos con Google Gemini

## 🚀 Configuración Rápida

### 1. Obtener API Key de Google Gemini (GRATIS)

1. Ve a: https://aistudio.google.com/app/apikey
2. Inicia sesión con tu cuenta de Google
3. Haz clic en "Create API Key"
4. Copia la API key generada

### 2. Configurar la API Key

**Opción A: Variable de entorno (Recomendado)**
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="tu_api_key_aqui"

# Windows CMD
set GEMINI_API_KEY=tu_api_key_aqui

# Linux/Mac
export GEMINI_API_KEY="tu_api_key_aqui"
```

**Opción B: Archivo .env**
```bash
# Crear archivo .env en la raíz del proyecto
GEMINI_API_KEY=tu_api_key_aqui
```

### 3. Instalar dependencias

```bash
pip install google-generativeai
```

O instalar todo:
```bash
pip install -r requirements.txt
```

---

## 📊 Uso

### Método 1: Análisis Automático (Integrado en el pipeline)

Ejecuta el scraper normalmente y el análisis se hará automáticamente:

```bash
python main.py --query "inteligencia artificial" --posts 10 --comments 5
```

### Método 2: Análisis Manual (Solo análisis)

Si ya tienes `sentiment_input.csv` generado:

```bash
python sentiment_analyzer.py
```

Esto leerá `output/sentiment_input.csv` y generará `output/sentiment_results.csv`

---

## 📁 Archivos Generados

| Archivo | Descripción |
|---------|-------------|
| `sentiment_input.csv` | Posts con comentarios agrupados (sin análisis) |
| `sentiment_results.csv` | Posts con análisis de sentimientos completado |
| `llm_prompts.csv` | Prompts usados para el análisis |

---

## 🎯 Formato de Resultados

El CSV de resultados incluye:

```csv
post_id, post_text, num_comments, sentiment, sentiment_score, sentiment_reasoning
```

**Valores de `sentiment`:**
- `positive` - Comentarios favorables/de apoyo
- `negative` - Comentarios críticos/en desacuerdo  
- `neutral` - Comentarios informativos sin opinión clara
- `mixed` - Mezcla de opiniones positivas y negativas
- `unknown` - Error en el análisis

**`sentiment_score`:** 0.0 (muy negativo) a 1.0 (muy positivo)

---

## ⚙️ Configuración Avanzada

### Cambiar modelo de Gemini

En `sentiment_analyzer.py`, línea 44:
```python
# Gemini 1.5 Flash (rápido, gratis)
model = genai.GenerativeModel('gemini-1.5-flash')

# Gemini 1.5 Pro (más preciso, límites más bajos)
# model = genai.GenerativeModel('gemini-1.5-pro')
```

### Ajustar rate limiting

En `sentiment_analyzer.py`, función `analyze_all_sentiments()`:
```python
# Cambiar delay entre llamadas (default: 1.0 segundo)
analyze_all_sentiments(df, delay_between_calls=2.0)
```

---

## 📊 Límites de la API Gratuita

**Gemini 1.5 Flash:**
- ✅ 15 requests por minuto
- ✅ 1,500 requests por día
- ✅ 1 millón de tokens por minuto

**Recomendación:** Con `delay_between_calls=1.0`, puedes analizar ~900 posts por hora sin problemas.

---

## 🐛 Troubleshooting

### Error: "google-generativeai not installed"
```bash
pip install google-generativeai
```

### Error: "No API key provided"
Asegúrate de configurar `GEMINI_API_KEY` como variable de entorno.

### Error: "Rate limit exceeded"
Aumenta `delay_between_calls` a 4.0 segundos:
```python
analyze_all_sentiments(df, delay_between_calls=4.0)
```

### Respuestas JSON inválidas
El código incluye retry logic (3 intentos) y limpieza automática de respuestas.

---

## 💡 Ejemplo de Uso Completo

```bash
# 1. Configurar API key
$env:GEMINI_API_KEY="AIza..."

# 2. Scraping + Análisis automático
python main.py --query "machine learning" --posts 20 --comments 10

# 3. Ver resultados
# Abrir output/sentiment_results.csv
```

---

## 🎓 Recursos

- **Gemini API Docs:** https://ai.google.dev/docs
- **Obtener API Key:** https://aistudio.google.com/app/apikey
- **Pricing:** https://ai.google.dev/pricing (Free tier muy generoso)
