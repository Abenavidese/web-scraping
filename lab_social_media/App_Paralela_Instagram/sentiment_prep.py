import pandas as pd
import json
import os

def prepare_sentiment_data_instagram(json_file):
    """
    Prepara datos de Instagram para análisis de sentimientos.
    Agrupa cada post con sus comentarios.
    
    Args:
        json_file: Ruta al archivo JSON con resultados de Instagram
        
    Returns:
        DataFrame con posts y comentarios agrupados
    """
    
    # Cargar datos JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        posts_data = json.load(f)
    
    sentiment_data = []
    
    for idx, post in enumerate(posts_data):
        # Extraer ID del post desde la URL
        post_url = post.get('post_url', '')
        post_id = post_url.split('/')[-2] if post_url else f'post_{idx}'
        
        # Extraer caption (texto del post)
        caption = post.get('caption_snippet', 'No caption')
        
        # Extraer comentarios
        comments = post.get('comments', [])
        comment_texts = [c.get('text', '') for c in comments if c.get('text')]
        
        # Crear entrada para análisis
        sentiment_entry = {
            'post_id': post_id,
            'post_url': post_url,
            'post_caption': caption,
            'image_url': post.get('image_url', ''),
            'num_comments': len(comment_texts),
            'comments_raw': ' | '.join(comment_texts) if comment_texts else 'No comments',
            'comments_json': json.dumps(comment_texts, ensure_ascii=False),
            'sentiment': '',
            'sentiment_score': '',
            'sentiment_reasoning': ''
        }
        
        sentiment_data.append(sentiment_entry)
    
    return pd.DataFrame(sentiment_data)


def create_llm_prompt_instagram(post_caption, comments_list):
    """
    Crea un prompt optimizado para análisis de sentimientos de Instagram.
    
    Args:
        post_caption: Caption/descripción del post
        comments_list: Lista de textos de comentarios
        
    Returns:
        String con el prompt formateado para el LLM
    """
    
    if not comments_list or len(comments_list) == 0:
        return f"""Analiza el sentimiento de este post de Instagram (no hay comentarios):

POST: {post_caption}

Responde en formato JSON:
{{
    "sentiment": "positive/negative/neutral/mixed",
    "score": 0.0-1.0,
    "reasoning": "breve explicación"
}}"""
    
    comments_formatted = '\n'.join([f"{i+1}. {comment}" for i, comment in enumerate(comments_list)])
    
    prompt = f"""Analiza el sentimiento general de la audiencia sobre este post de Instagram basándote en los comentarios:

POST ORIGINAL:
{post_caption}

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


def generate_llm_prompts_csv_instagram(df_sentiment, output_path='Resultados/llm_prompts.csv'):
    """
    Genera un CSV con prompts listos para enviar al LLM.
    
    Args:
        df_sentiment: DataFrame de prepare_sentiment_data_instagram()
        output_path: Ruta donde guardar el CSV
    """
    
    prompts_data = []
    
    for _, row in df_sentiment.iterrows():
        # Parsear comentarios del JSON
        comments_list = json.loads(row['comments_json'])
        
        # Crear prompt
        prompt = create_llm_prompt_instagram(row['post_caption'], comments_list)
        
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


def process_all_instagram_results(results_dir='Resultados'):
    """
    Procesa todos los archivos results_*.json en el directorio de resultados.
    
    Args:
        results_dir: Directorio con archivos de resultados
        
    Returns:
        DataFrame combinado con todos los posts
    """
    
    all_sentiment_data = []
    
    # Buscar todos los archivos results_*.json
    for filename in os.listdir(results_dir):
        if filename.startswith('results_') and filename.endswith('.json'):
            filepath = os.path.join(results_dir, filename)
            print(f"Processing {filename}...")
            
            df = prepare_sentiment_data_instagram(filepath)
            all_sentiment_data.append(df)
    
    if all_sentiment_data:
        combined_df = pd.concat(all_sentiment_data, ignore_index=True)
        return combined_df
    else:
        print("No results files found!")
        return pd.DataFrame()


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Instagram Sentiment Data Preparation ===\n")
    
    # Procesar todos los resultados
    df_sentiment = process_all_instagram_results()
    
    if not df_sentiment.empty:
        # Guardar datos preparados
        df_sentiment.to_csv('Resultados/sentiment_input.csv', index=False, encoding='utf-8')
        print(f"\nSentiment data saved to Resultados/sentiment_input.csv")
        print(f"Total posts: {len(df_sentiment)}")
        
        # Generar prompts
        generate_llm_prompts_csv_instagram(df_sentiment)
