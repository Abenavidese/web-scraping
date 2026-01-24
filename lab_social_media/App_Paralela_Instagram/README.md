# Instagram Scraper con Análisis de Sentimientos

Scraper de Instagram con análisis de sentimientos **100% GRATIS** usando Hugging Face.

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar API key en .env
HUGGINGFACE_API_KEY=tu_api_key_aqui

# 3. Ejecutar
python scraper.py
```

## 📊 Características

- ✅ Scraping de posts y comentarios de Instagram
- ✅ Procesamiento NLP (limpieza, tokenización, stemming)
- ✅ Visualizaciones (word clouds, gráficos de frecuencia)
- ✅ **Análisis de sentimientos con Hugging Face (GRATIS!)**
- ✅ Optimizado con smart sleeps (55% más rápido)
- ✅ Soporte para hashtags multi-palabra (CamelCase)

## 💰 Costo

**$0.00** - Completamente gratuito, sin tarjeta de crédito requerida.

## 📁 Resultados

Todos los resultados se guardan en `Resultados/`:
- `results_{query}.json` - Posts originales
- `processed_{query}.csv` - Texto procesado
- `sentiment_results_{query}.csv` - **Análisis de sentimientos**
- `frecuencia_{query}_wordcloud.png` - Word cloud
- Y más...

## 🔧 Configuración

### Obtener API Key de Hugging Face (GRATIS):

1. https://huggingface.co/settings/tokens
2. Crear cuenta (sin tarjeta)
3. Click "New token" → Tipo: Read
4. Copiar token a `.env`

## 📖 Uso

### Básico:
```bash
python scraper.py
```

### Personalizado:
```bash
python scraper.py --query "machine learning" --posts 10 --comments 5
```

## 📚 Documentación

Ver `instagram_final_summary.md` para documentación completa.

## ✅ Verificado

Sistema probado y funcionando:
- 4 posts positive (scores: 0.9, 0.95, 0.92, 0.98)
- 1 post neutral (score: 0.05)
- Score promedio: 0.76

---

**¡Listo para usar!** 🎉
