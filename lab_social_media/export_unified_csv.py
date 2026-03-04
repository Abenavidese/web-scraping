"""
Script para generar CSV unificado en formato de investigación
Formato: Red Social | Publicación | Comentario | Sentimiento | Explicación | Términos

Uso:
    python export_unified_csv.py --query "María Elisa Padilla"
"""

import pandas as pd
import json
import os
import argparse
from pathlib import Path
import re

def slugify(text):
    """Convierte texto a formato slug para nombres de archivo"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')

def extract_terms_from_processed(processed_text):
    """Extrae términos clave del texto procesado (primeras 10 palabras)"""
    if not processed_text or pd.isna(processed_text):
        return ""
    words = str(processed_text).split()[:10]
    return ", ".join(words)

def process_x_twitter(query_slug, user_id="default"):
    """Procesa datos de X (Twitter)"""
    path = f"users/{user_id}/x/{query_slug}/sentiment_results.csv"
    
    if not os.path.exists(path):
        print(f"⚠️  No se encontró: {path}")
        return []
    
    df = pd.read_csv(path, encoding='utf-8')
    rows = []
    
    for _, row in df.iterrows():
        post_text = row.get('post_text', '')
        post_processed = row.get('post_processed', '')
        sentiment = row.get('sentiment', 'neutral')
        reasoning = row.get('sentiment_reasoning', '')
        
        # Extraer comentarios del JSON
        comments_json = row.get('comments_json', '[]')
        try:
            comments = json.loads(comments_json) if isinstance(comments_json, str) else comments_json
        except:
            comments = []
        
        # Si hay comentarios, crear una fila por comentario
        if comments and len(comments) > 0:
            for comment in comments:
                comment_text = comment if isinstance(comment, str) else str(comment)
                rows.append({
                    'Red Social': 'X (Twitter)',
                    'Publicación': post_text[:200],  # Limitar longitud
                    'Comentario': comment_text[:300],
                    'Sentimiento': sentiment.upper(),
                    'Explicación': reasoning[:200],
                    'Términos': extract_terms_from_processed(post_processed)
                })
        else:
            # Si no hay comentarios, usar el post como comentario
            rows.append({
                'Red Social': 'X (Twitter)',
                'Publicación': post_text[:200],
                'Comentario': post_text[:300],
                'Sentimiento': sentiment.upper(),
                'Explicación': reasoning[:200],
                'Términos': extract_terms_from_processed(post_processed)
            })
    
    return rows

def process_instagram(query_slug, user_id="default"):
    """Procesa datos de Instagram"""
    # Buscar archivo con el nombre del query
    base_path = f"users/{user_id}/instagram/{query_slug}"
    
    # Intentar diferentes nombres de archivo
    possible_files = [
        f"sentiment_results_{query_slug}.csv",
        "sentiment_results.csv"
    ]
    
    path = None
    for filename in possible_files:
        test_path = os.path.join(base_path, filename)
        if os.path.exists(test_path):
            path = test_path
            break
    
    if not path:
        print(f"⚠️  No se encontró archivo de Instagram en: {base_path}")
        return []
    
    df = pd.read_csv(path, encoding='utf-8')
    rows = []
    
    for _, row in df.iterrows():
        caption = row.get('caption_snippet', row.get('text', ''))
        processed = row.get('clean_text', row.get('processed_text', ''))
        sentiment = row.get('sentiment', row.get('sentiment_deepseek', 'neutral'))
        reasoning = row.get('sentiment_reasoning', row.get('explanation_deepseek', ''))
        
        rows.append({
            'Red Social': 'Instagram',
            'Publicación': caption[:200],
            'Comentario': caption[:300],
            'Sentimiento': str(sentiment).upper(),
            'Explicación': str(reasoning)[:200],
            'Términos': extract_terms_from_processed(processed)
        })
    
    return rows

def process_facebook(query_slug, user_id="default"):
    """Procesa datos de Facebook"""
    path = f"users/{user_id}/facebook/{query_slug}/datos_extraidos_deepseek.csv"
    
    if not os.path.exists(path):
        print(f"⚠️  No se encontró: {path}")
        return []
    
    df = pd.read_csv(path, encoding='utf-8')
    rows = []
    
    for _, row in df.iterrows():
        content = row.get('content', '')
        sentiment = row.get('sentiment_deepseek', 'neutral')
        explanation = row.get('explanation_deepseek', '')
        
        # Extraer comentarios del JSON
        comments_json = row.get('comments', '[]')
        try:
            comments = json.loads(comments_json) if isinstance(comments_json, str) else comments_json
        except:
            comments = []
        
        # Si hay comentarios, crear una fila por comentario
        if comments and len(comments) > 0:
            for comment in comments:
                if isinstance(comment, dict):
                    comment_text = comment.get('text', '')
                    comment_sentiment = comment.get('sentiment', sentiment)
                    comment_reasoning = comment.get('sentiment_reasoning', explanation)
                else:
                    comment_text = str(comment)
                    comment_sentiment = sentiment
                    comment_reasoning = explanation
                
                rows.append({
                    'Red Social': 'Facebook',
                    'Publicación': content[:200],
                    'Comentario': comment_text[:300],
                    'Sentimiento': str(comment_sentiment).upper(),
                    'Explicación': str(comment_reasoning)[:200],
                    'Términos': extract_terms_from_processed(content)
                })
        else:
            # Si no hay comentarios, usar el post
            rows.append({
                'Red Social': 'Facebook',
                'Publicación': content[:200],
                'Comentario': content[:300],
                'Sentimiento': str(sentiment).upper(),
                'Explicación': str(explanation)[:200],
                'Términos': extract_terms_from_processed(content)
            })
    
    return rows

def process_linkedin(query_slug, user_id="default"):
    """Procesa datos de LinkedIn"""
    path = f"users/{user_id}/linkedin/{query_slug}/datos_extraidos_deepseek.csv"
    
    if not os.path.exists(path):
        print(f"⚠️  No se encontró: {path}")
        return []
    
    df = pd.read_csv(path, encoding='utf-8')
    rows = []
    
    for _, row in df.iterrows():
        content = row.get('content', '')
        sentiment = row.get('sentiment_deepseek', 'neutral')
        explanation = row.get('explanation_deepseek', '')
        
        # Extraer comentarios del JSON
        comments_json = row.get('comments', '[]')
        try:
            comments = json.loads(comments_json) if isinstance(comments_json, str) else comments_json
        except:
            comments = []
        
        # Si hay comentarios, crear una fila por comentario
        if comments and len(comments) > 0:
            for comment in comments:
                comment_text = comment if isinstance(comment, str) else str(comment)
                rows.append({
                    'Red Social': 'LinkedIn',
                    'Publicación': content[:200],
                    'Comentario': comment_text[:300],
                    'Sentimiento': str(sentiment).upper(),
                    'Explicación': str(explanation)[:200],
                    'Términos': extract_terms_from_processed(content)
                })
        else:
            # Si no hay comentarios, usar el post
            rows.append({
                'Red Social': 'LinkedIn',
                'Publicación': content[:200],
                'Comentario': content[:300],
                'Sentimiento': str(sentiment).upper(),
                'Explicación': str(explanation)[:200],
                'Términos': extract_terms_from_processed(content)
            })
    
    return rows

def main():
    parser = argparse.ArgumentParser(description='Exportar datos unificados a CSV')
    parser.add_argument('--query', type=str, required=True, help='Query de búsqueda')
    parser.add_argument('--user-id', type=str, default='default', help='ID de usuario')
    parser.add_argument('--output', type=str, default=None, help='Archivo de salida (opcional)')
    
    args = parser.parse_args()
    
    query_slug = slugify(args.query)
    
    print(f"\n🔍 Buscando datos para: {args.query}")
    print(f"📂 Query slug: {query_slug}")
    print("=" * 80)
    
    # Procesar cada red social
    all_rows = []
    
    print("\n[X (Twitter)] Procesando...")
    x_rows = process_x_twitter(query_slug, args.user_id)
    all_rows.extend(x_rows)
    print(f"✅ {len(x_rows)} filas extraídas")
    
    print("\n[Instagram] Procesando...")
    ig_rows = process_instagram(query_slug, args.user_id)
    all_rows.extend(ig_rows)
    print(f"✅ {len(ig_rows)} filas extraídas")
    
    print("\n[Facebook] Procesando...")
    fb_rows = process_facebook(query_slug, args.user_id)
    all_rows.extend(fb_rows)
    print(f"✅ {len(fb_rows)} filas extraídas")
    
    print("\n[LinkedIn] Procesando...")
    li_rows = process_linkedin(query_slug, args.user_id)
    all_rows.extend(li_rows)
    print(f"✅ {len(li_rows)} filas extraídas")
    
    # Crear DataFrame
    if not all_rows:
        print("\n❌ No se encontraron datos para exportar.")
        return
    
    df = pd.DataFrame(all_rows)
    
    # Determinar nombre de archivo de salida
    if args.output:
        output_file = args.output
    else:
        output_file = f"export_unified_{query_slug}.csv"
    
    # Guardar CSV
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print("\n" + "=" * 80)
    print(f"✅ EXPORTACIÓN COMPLETADA")
    print(f"📊 Total de filas: {len(df)}")
    print(f"📁 Archivo: {output_file}")
    print("\n📈 Distribución por red social:")
    print(df['Red Social'].value_counts())
    print("\n💭 Distribución de sentimientos:")
    print(df['Sentimiento'].value_counts())
    print("=" * 80)

if __name__ == "__main__":
    main()
