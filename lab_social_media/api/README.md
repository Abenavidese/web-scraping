# Backend para Aplicación Web - Social Media Analytics

## Descripción

Backend completo para aplicación web de análisis de redes sociales. Incluye:
- Base de datos SQLite unificada
- API REST con Flask
- Importación automática de datos de scrapers
- Endpoints para consultas, filtros y analytics

## Estructura

```
lab_social_media/
├── shared/
│   ├── data_unifier.py       # Módulo de unificación de datos
│   └── sentiment_analyzer.py # Análisis de sentimientos (DeepSeek)
├── api/
│   ├── app.py               # API REST con Flask
│   └── requirements.txt     # Dependencias
├── data/
│   ├── social_media.db      # Base de datos SQLite
│   └── export_*.json        # Exportaciones
└── import_data.py           # Script de importación
```

## Instalación

### 1. Instalar dependencias de la API

```bash
cd api
pip install -r requirements.txt
```

### 2. Verificar que tienes datos de scrapers

Asegúrate de haber ejecutado los scrapers y tener archivos:
- `x_scrapper/output/sentiment_results.csv`
- `App_Paralela_Instagram/Resultados/sentiment_results.csv`
- `App_Paralela_facebook/Resultados/sentiment_results.csv`
- `linkedin_scraper/output/sentiment_results.csv`

## Uso

### Paso 1: Importar Datos

Ejecuta el script de importación para poblar la base de datos:

```bash
python import_data.py
```

El script te pedirá el query de búsqueda usado en los scrapers.

### Paso 2: Iniciar API

```bash
cd api
python app.py
```

La API estará disponible en: `http://localhost:5000`

### Paso 3: Probar Endpoints

Abre tu navegador o usa curl/Postman:

```bash
# Ver estadísticas
http://localhost:5000/api/stats

# Ver todos los posts
http://localhost:5000/api/posts

# Filtrar por red social
http://localhost:5000/api/posts?network=instagram

# Filtrar por sentimiento
http://localhost:5000/api/posts?sentiment=positive

# Ver distribución de sentimientos
http://localhost:5000/api/sentiments

# Ver analytics
http://localhost:5000/api/analytics
```

## Endpoints de la API

### GET /api/posts

Obtiene posts con filtros opcionales.

**Parámetros**:
- `network`: x, instagram, facebook, linkedin
- `sentiment`: positive, negative, neutral, mixed
- `query`: Texto de búsqueda
- `limit`: Máximo de resultados (default: 100)

**Ejemplo**:
```
GET /api/posts?network=x&sentiment=positive&limit=50
```

**Respuesta**:
```json
{
  "success": true,
  "total": 15,
  "filters": {
    "network": "x",
    "sentiment": "positive",
    "limit": 50
  },
  "posts": [
    {
      "id": 1,
      "post_id": "123",
      "network": "x",
      "author": "Author Name",
      "text": "Post text...",
      "sentiment": "positive",
      "sentiment_score": 0.85,
      "num_comments": 5
    }
  ]
}
```

### GET /api/posts/<post_id>

Obtiene un post específico con todos sus comentarios.

**Ejemplo**:
```
GET /api/posts/2016216029999874296
```

**Respuesta**:
```json
{
  "success": true,
  "post": {
    "post_id": "2016216029999874296",
    "network": "x",
    "author": "Author",
    "text": "Post text...",
    "sentiment": "positive",
    "comments": [
      {
        "comment_id": "123_comment_0",
        "author": "Commenter",
        "text": "Comment text..."
      }
    ]
  }
}
```

### GET /api/sentiments

Obtiene distribución de sentimientos.

**Parámetros**:
- `network`: Filtro opcional por red

**Ejemplo**:
```
GET /api/sentiments?network=instagram
```

**Respuesta**:
```json
{
  "success": true,
  "distribution": [
    {"network": "instagram", "sentiment": "positive", "count": 15},
    {"network": "instagram", "sentiment": "negative", "count": 8}
  ],
  "summary": {
    "instagram": {
      "positive": 15,
      "negative": 8,
      "neutral": 5,
      "total": 28
    }
  }
}
```

### GET /api/analytics

Obtiene resumen de analytics por red social.

**Respuesta**:
```json
{
  "success": true,
  "analytics": [
    {
      "network": "x",
      "total_queries": 1,
      "total_posts": 10,
      "total_comments": 50,
      "avg_time": 45.32,
      "total_positive": 4,
      "total_negative": 5,
      "total_neutral": 1
    }
  ]
}
```

### GET /api/queries

Obtiene todas las búsquedas rastreadas.

**Respuesta**:
```json
{
  "success": true,
  "queries": [
    {
      "id": 1,
      "query_text": "Nicolas Muñoz",
      "created_at": "2026-02-03T19:00:00",
      "last_scraped": "2026-02-03T19:30:00",
      "total_posts": 40,
      "total_comments": 150
    }
  ]
}
```

### GET /api/stats

Obtiene estadísticas generales de la base de datos.

**Respuesta**:
```json
{
  "success": true,
  "stats": {
    "total_posts": 40,
    "total_comments": 150,
    "total_queries": 1,
    "posts_by_network": {
      "x": 10,
      "instagram": 10,
      "facebook": 10,
      "linkedin": 10
    },
    "sentiment_distribution": {
      "positive": 15,
      "negative": 18,
      "neutral": 7
    }
  }
}
```

### GET /api/networks

Obtiene lista de redes sociales disponibles.

**Respuesta**:
```json
{
  "success": true,
  "networks": [
    {"id": "x", "name": "X (Twitter)", "icon": "𝕏"},
    {"id": "instagram", "name": "Instagram", "icon": "📷"},
    {"id": "facebook", "name": "Facebook", "icon": "👥"},
    {"id": "linkedin", "name": "LinkedIn", "icon": "💼"}
  ]
}
```

## Base de Datos

### Esquema

#### Tabla: posts
```sql
- id: INTEGER PRIMARY KEY
- post_id: VARCHAR(255) UNIQUE
- network: VARCHAR(50)
- author: VARCHAR(255)
- text: TEXT
- url: VARCHAR(500)
- processed_text: TEXT
- sentiment: VARCHAR(50)
- sentiment_score: FLOAT
- sentiment_reasoning: TEXT
- query: VARCHAR(255)
- num_comments: INTEGER
- created_at: TIMESTAMP
- scraped_at: TIMESTAMP
```

#### Tabla: comments
```sql
- id: INTEGER PRIMARY KEY
- comment_id: VARCHAR(255)
- post_id: VARCHAR(255) FK
- network: VARCHAR(50)
- author: VARCHAR(255)
- text: TEXT
- processed_text: TEXT
- created_at: TIMESTAMP
- scraped_at: TIMESTAMP
```

#### Tabla: analytics
```sql
- id: INTEGER PRIMARY KEY
- network: VARCHAR(50)
- query: VARCHAR(255)
- execution_date: TIMESTAMP
- scraping_time: FLOAT
- processing_time: FLOAT
- sentiment_time: FLOAT
- total_time: FLOAT
- posts_extracted: INTEGER
- comments_extracted: INTEGER
- items_analyzed: INTEGER
- positive_count: INTEGER
- negative_count: INTEGER
- neutral_count: INTEGER
- mixed_count: INTEGER
- posts_per_second: FLOAT
- avg_time_per_post: FLOAT
```

## Uso Programático

### Python

```python
from shared.data_unifier import DataUnifier

# Inicializar
unifier = DataUnifier('data/social_media.db')

# Obtener posts
posts_df = unifier.get_all_posts(network='instagram', sentiment='positive')

# Obtener post con comentarios
post = unifier.get_post_with_comments('2016216029999874296')

# Obtener distribución de sentimientos
sentiment_df = unifier.get_sentiment_distribution()

# Obtener estadísticas
stats = unifier.get_stats()

# Exportar a JSON
unifier.export_to_json('export.json', query='Nicolas Muñoz')
```

### JavaScript (Frontend)

```javascript
// Obtener posts
const response = await fetch('http://localhost:5000/api/posts?network=x');
const data = await response.json();
console.log(data.posts);

// Obtener sentimientos
const sentiments = await fetch('http://localhost:5000/api/sentiments');
const sentimentData = await sentiments.json();
console.log(sentimentData.summary);
```

## Exportación de Datos

El script de importación genera automáticamente un archivo JSON con todos los datos:

```bash
data/export_Nicolas_Muñoz.json
```

Este archivo contiene:
- Metadata de exportación
- Todos los posts con sus comentarios
- Información de sentimientos
- Estadísticas generales

## Próximos Pasos

1. **Frontend**: Crear aplicación web con React/Vue/Next.js
2. **Visualizaciones**: Integrar Chart.js o D3.js
3. **Autenticación**: Agregar JWT para proteger endpoints
4. **Caché**: Implementar Redis para consultas frecuentes
5. **Deploy**: Configurar para producción (Gunicorn, Nginx)

## Notas

- La API usa CORS habilitado para permitir requests desde cualquier origen
- SQLite es suficiente para desarrollo; migrar a PostgreSQL para producción
- Los datos se actualizan cada vez que ejecutas `import_data.py`
- La base de datos se crea automáticamente en `data/social_media.db`

## Troubleshooting

### Error: "No module named 'flask'"
```bash
cd api
pip install -r requirements.txt
```

### Error: "Database is locked"
Cierra cualquier conexión abierta a la base de datos.

### Error: "File not found"
Verifica que hayas ejecutado los scrapers y que los archivos CSV existan.

## Soporte

Para más información, consulta:
- `shared/data_unifier.py` - Documentación del módulo
- `api/app.py` - Documentación de endpoints
- `web_app_data_plan.md` - Plan completo de arquitectura
