import pandas as pd
import json

def prepare_sentiment_data(tweets_list):
    """
    Prepara los datos para análisis de sentimientos con LLM.
    Agrupa cada post con sus comentarios para analizar el sentimiento general.
    
    Args:
        tweets_list: Lista de diccionarios con tweets y comentarios
        
    Returns:
        DataFrame con posts y sus comentarios agrupados
    """
    
    # Crear DataFrame desde la lista
    df = pd.DataFrame(tweets_list)
    
    # Separar posts y comentarios
    posts = df[df['type'] == 'post'].copy()
    comments = df[df['type'] == 'comment'].copy()
    
    # Preparar datos para análisis de sentimientos
    sentiment_data = []
    
    for _, post in posts.iterrows():
        post_url = post['parent_url']
        
        # Obtener todos los comentarios de este post
        post_comments = comments[comments['parent_url'] == post_url]
        
        # Crear lista de textos de comentarios
        comment_texts = post_comments['text'].tolist()
        
        # Crear entrada para análisis
        sentiment_entry = {
            'post_id': post_url.split('/')[-1] if post_url else 'unknown',
            'post_author': post['author'],
            'post_text': post['text'],
            'post_url': post_url,
            'num_comments': len(comment_texts),
            'comments_text': ' | '.join(comment_texts) if comment_texts else 'No comments',
            'all_comments': json.dumps(comment_texts, ensure_ascii=False)  # JSON para LLM
        }
        
        sentiment_data.append(sentiment_entry)
    
    return pd.DataFrame(sentiment_data)


def prepare_sentiment_data_with_processed(df_processed):
    """
    Prepara datos para análisis de sentimientos usando el DataFrame ya procesado.
    Incluye tanto texto original como procesado.
    
    Args:
        df_processed: DataFrame con datos procesados (de processor.py)
        
    Returns:
        DataFrame con posts y comentarios agrupados, incluyendo texto procesado
    """
    
    # Separar posts y comentarios
    posts = df_processed[df_processed['type'] == 'post'].copy()
    comments = df_processed[df_processed['type'] == 'comment'].copy()
    
    sentiment_data = []
    
    for _, post in posts.iterrows():
        post_url = post['parent_url']
        
        # Obtener comentarios de este post
        post_comments = comments[comments['parent_url'] == post_url]
        
        # Textos originales
        comment_texts = post_comments['text'].tolist()
        
        # Textos procesados (para análisis más limpio)
        if 'text_clean_semantic' in post_comments.columns:
            comment_processed = post_comments['text_clean_semantic'].tolist()
        else:
            comment_processed = post_comments['text'].tolist()
        
        comments_list_for_json = []
        for _, c_row in post_comments.iterrows():
            comments_list_for_json.append({
                "comment_id": c_row.get('item_id', ''),
                "timestamp": c_row.get('timestamp', ''),
                "text": c_row.get('text', ''),
                "processed_text": c_row.get('text_clean_semantic', c_row.get('text', '')),
                "intensity_text": c_row.get('text_clean_intensity', ''),
                "author": c_row.get('author', '')
            })
            
        sentiment_entry = {
            'post_id': post_url.split('/')[-1] if post_url else 'unknown',
            'post_author': post['author'],
            'post_text': post['text'],
            'post_processed': post.get('text_clean_semantic', post['text']),
            'post_intensity': post.get('text_clean_intensity', ''),
            'post_url': post_url,
            'num_comments': len(comment_texts),
            
            # Comentarios originales
            'comments_raw': ' | '.join(comment_texts) if comment_texts else 'No comments',
            
            # Comentarios procesados (mejor para LLM)
            'comments_processed': ' | '.join(comment_processed) if comment_processed else 'No comments',
            
            # JSON estructurado para LLM
            'comments_json': json.dumps(comments_list_for_json, ensure_ascii=False)
        }
        
        sentiment_data.append(sentiment_entry)
    
    df_sentiment = pd.DataFrame(sentiment_data)
    
    # Agregar columna para el resultado del LLM (vacía por ahora)
    df_sentiment['sentiment'] = ''
    df_sentiment['sentiment_score'] = ''
    df_sentiment['sentiment_reasoning'] = ''
    
    return df_sentiment


def create_llm_prompt(post_text, comments_list):
    """
    Crea un prompt optimizado para análisis de sentimientos con LLM.
    
    Args:
        post_text: Texto del post original
        comments_list: Lista de textos de comentarios
        
    Returns:
        String con el prompt formateado para el LLM
    """
    
    if not comments_list or len(comments_list) == 0:
        return f"""Analiza el sentimiento de este post (no hay comentarios):

POST: {post_text}

Responde en formato JSON:
{{
    "sentiment": "positive/negative/neutral/mixed",
    "score": 0.0-1.0,
    "reasoning": "breve explicación"
}}"""
    
    comments_formatted = '\n'.join([f"{i+1}. {comment}" for i, comment in enumerate(comments_list)])
    
    prompt = f"""Analiza el sentimiento general de la audiencia sobre este post basándote en los comentarios:

POST ORIGINAL:
{post_text}

COMENTARIOS ({len(comments_list)}):
{comments_formatted}

Basándote ÚNICAMENTE en los comentarios, determina qué opina la gente sobre el post.

Responde en formato JSON:
{{
    "sentiment": "positive/negative/neutral/mixed",
    "score": 0.0-1.0,
    "reasoning": "breve explicación de por qué los comentarios reflejan este sentimiento"
}}"""
    
    return prompt


def generate_llm_prompts_csv(df_sentiment, output_path='output/llm_prompts.csv'):
    """
    Genera un CSV con prompts listos para enviar al LLM.
    
    Args:
        df_sentiment: DataFrame de prepare_sentiment_data_with_processed()
        output_path: Ruta donde guardar el CSV
    """
    
    prompts_data = []
    
    for _, row in df_sentiment.iterrows():
        # Parsear comentarios del JSON
        comments_list = json.loads(row['comments_json'])
        
        # Crear prompt
        prompt = create_llm_prompt(row['post_text'], comments_list)
        
        prompts_data.append({
            'post_id': row['post_id'],
            'post_url': row['post_url'],
            'num_comments': row['num_comments'],
            'llm_prompt': prompt
        })
    
    df_prompts = pd.DataFrame(prompts_data)
    df_prompts.to_csv(output_path, index=False, encoding='utf-8')
    print(f"LLM prompts saved to {output_path}")
    
    return df_prompts
