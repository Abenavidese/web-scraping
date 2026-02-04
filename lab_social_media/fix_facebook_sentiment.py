"""
Script para actualizar los sentimientos de Facebook desde el JSON existente
"""
import json
import csv
import os
from shared.data_unifier import DataUnifier

user_id = "36fe43fb-1c7c-44aa-868e-4448f55ddd04"
query = "iphone"

# Cargar JSON de Facebook
json_path = f"users/{user_id}/facebook/{query}/results_facebook_{query}.json"
if not os.path.exists(json_path):
    print(f"❌ No se encontró: {json_path}")
    exit(1)

with open(json_path, 'r', encoding='utf-8') as f:
    posts_data = json.load(f)

print(f"📊 Cargados {len(posts_data)} posts de Facebook")

# Generar CSV con formato correcto
output_dir = f"users/{user_id}/facebook/{query}"
csv_path = os.path.join(output_dir, "datos_extraidos_deepseek.csv")

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["source", "title", "content", "comments", "sentiment_deepseek", "explanation_deepseek"])
    
    for post in posts_data:
        source = "facebook"
        title = post.get("post_url", "N/A")
        content = post.get("caption_snippet", "")
        comments_json = json.dumps(post.get("comments", []), ensure_ascii=False)
        
        # Extraer sentimiento del primer comentario como aproximación
        # (esto es temporal hasta que se vuelva a scrapear con el código actualizado)
        sentiment = "NEUTRAL"
        explanation = "Análisis temporal basado en comentarios"
        
        comments = post.get("comments", [])
        if comments:
            # Contar sentimientos de comentarios
            sentiments_count = {}
            for comment in comments:
                s = comment.get("sentiment", "NEUTRAL").upper()
                sentiments_count[s] = sentiments_count.get(s, 0) + 1
            
            # Usar el sentimiento más común
            if sentiments_count:
                sentiment = max(sentiments_count, key=sentiments_count.get)
                explanation = f"Inferido de {len(comments)} comentarios: {sentiments_count}"
        
        writer.writerow([source, title, content, comments_json, sentiment, explanation])

print(f"✅ CSV generado: {csv_path}")

# Ahora reimportar los datos
print("\n🔄 Reimportando datos de Facebook...")

# Primero eliminar datos antiguos de Facebook
unifier = DataUnifier()
cursor = unifier.conn.cursor()
cursor.execute("DELETE FROM posts WHERE network = 'facebook'")
cursor.execute("DELETE FROM comments WHERE network = 'facebook'")
unifier.conn.commit()
print("🗑️  Datos antiguos de Facebook eliminados")

# Importar nuevos datos
unifier.import_from_csv('facebook', csv_path, query, user_id)

# Verificar
stats = unifier.get_stats()
print(f"\n📊 Posts de Facebook: {stats['posts_by_network'].get('facebook', 0)}")

# Mostrar distribución de sentimientos
sentiment_df = unifier.get_sentiment_distribution()
print("\n💭 Distribución de sentimientos:")
print(sentiment_df[sentiment_df['network'] == 'facebook'])

print("\n✅ Proceso completado")
