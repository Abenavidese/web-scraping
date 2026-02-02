"""
Instagram Sentiment Analyzer using Hugging Face InferenceClient
100% FREE - No credit card required
Uses official huggingface_hub library for reliability
"""

import os
import json
import pandas as pd
import time
from sentiment_prep import create_llm_prompt_instagram

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not installed")

# Importar Hugging Face Client
try:
    from huggingface_hub import InferenceClient
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("WARNING: huggingface_hub not installed. Run: pip install huggingface_hub")


def setup_huggingface(api_key=None):
    """
    Configura Hugging Face API para Instagram.
    
    Args:
        api_key: API key de Hugging Face
    
    Returns:
        InferenceClient configurado o None
    """
    if not HF_AVAILABLE:
        print("ERROR: huggingface_hub package not installed")
        return None
    
    if api_key is None:
        api_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
    
    if not api_key:
        print("ERROR: No Hugging Face API key provided")
        print("Set HUGGINGFACE_API_KEY in .env")
        print("\nGet your FREE API key at: https://huggingface.co/settings/tokens")
        return None
    
    client = InferenceClient(token=api_key)
    print("✅ Hugging Face API configured for Instagram")
    return client


def create_batch_prompt_hf(df_sentiment):
    """
    Crea un prompt optimizado para Hugging Face en formato batch.
    """
    prompt = """Analyze sentiment of Instagram posts based on comments. Respond ONLY with JSON array.

POSTS:
"""
    
    for idx, row in df_sentiment.iterrows():
        comments_list = json.loads(row['comments_json'])
        
        prompt += f"\n{idx+1}. ID:{row['post_id']}\n"
        prompt += f"   Caption: {row['post_caption'][:150]}\n"
        
        if comments_list and len(comments_list) > 0:
            comments_compact = " | ".join([c[:80] for c in comments_list[:5]])
            prompt += f"   Comments: {comments_compact}\n"
        else:
            prompt += f"   Comments: NONE\n"
    
    prompt += '\n\nRespond with JSON: [{"id":"post_id","sentiment":"positive/negative/neutral/mixed","score":0-1,"reasoning":"brief"}]'
    
    return prompt



# Importar DeepSeek Client desde utils_common
import sys
# Asegurar que podemos importar utils_common subiendo un nivel
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from utils_common.deepseek_client import deepseek
    DEEPSEEK_AVAILABLE = True
except ImportError as e:
    DEEPSEEK_AVAILABLE = False
    print(f"WARNING: Could not import DeepSeek client: {e}")


def analyze_instagram_deepseek(df_sentiment):
    """
    Analiza posts de Instagram con DeepSeek en BATCH (Granular: Post vs Comentarios).
    Retorna un nuevo DataFrame con una fila por ITEM validado.
    """
    if not DEEPSEEK_AVAILABLE or not deepseek.client:
        print("⚠️ DeepSeek client not available. Skipping analysis.")
        return pd.DataFrame() # Retorna vacío si falla
    
    print(f"\n🔍 Preparing granular analysis for {len(df_sentiment)} posts...")
    
    # Lista plana de todos los items a analizar (Posts y Comentarios por separado)
    all_items = []
    
    for idx, row in df_sentiment.iterrows():
        post_id = str(row['post_id'])
        post_url = row.get('post_url', '')
        
        # 1. Agregar el POST (Caption)
        caption = str(row['post_caption']).strip()
        if caption and caption.lower() != 'no caption':
            all_items.append({
                "internal_id": f"{post_id}_POST",
                "post_id": post_id,
                "post_url": post_url,
                "type": "POST",
                "text": caption
            })
            
        # 2. Agregar COMENTARIOS
        try:
            comments_list = json.loads(row['comments_json'])
            for i, comment in enumerate(comments_list):
                if comment.strip():
                    all_items.append({
                        "internal_id": f"{post_id}_COMMENT_{i}",
                        "post_id": post_id,
                        "post_url": post_url,
                        "type": "COMMENT",
                        "text": comment
                    })
        except:
            pass # Si falla el json load, ignoramos comentarios
            
    print(f"   📊 Total items to analyze: {len(all_items)} (Posts + Comments)")
    
    if not all_items:
        return pd.DataFrame()

    # Preparar payload para batch
    items_payload = []
    for item in all_items:
        items_payload.append({
            "id": item['internal_id'],
            "text": item['text']
        })

    # Llamada batch
    print(f"   📤 Sending batch to DeepSeek API...")
    batch_results = deepseek.analyze_sentiment_batch(items_payload, context="Instagram Social Media")
    print(f"   📥 Received {len(batch_results)} results.")

    # Construir DataFrame final detallado
    granular_data = []
    
    for item in all_items:
        res = batch_results.get(item['internal_id'], {
            "sentiment": "NEUTRAL", 
            "score": 0.5, 
            "reasoning": "Analysis failed or timed out"
        })
        
        granular_data.append({
            "post_id": item['post_id'],
            "post_url": item['post_url'],
            "item_type": item['type'],
            "text_content": item['text'],
            "sentiment": res['sentiment'],
            "sentiment_score": res['score'],
            "sentiment_reasoning": res['reasoning']
        })

    print(f"\n✅ DeepSeek granular analysis completed!")
    return pd.DataFrame(granular_data)


def main_sentiment_analysis_instagram(input_csv='Resultados/sentiment_input.csv',
                                     output_csv='Resultados/sentiment_results.csv',
                                     api_key=None,
                                     model_id=None):
    """
    Análisis de sentimientos para Instagram con DeepSeek.
    """
    print("=" * 60)
    print("Instagram Sentiment Analysis with DeepSeek")
    print("=" * 60)
    print()
    
    if not os.path.exists(input_csv):
        print(f"❌ Input file not found: {input_csv}")
        return None

    # Cargar datos
    print(f"Loading data from {input_csv}...")
    df_sentiment = pd.read_csv(input_csv)
    print(f"Loaded {len(df_sentiment)} posts\n")
    
    # Analizar
    df_results = analyze_instagram_deepseek(df_sentiment)
    
    # Guardar
    df_results.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\n💾 Results saved to {output_csv}")
    
    # Resumen
    print("\n📊 Sentiment Summary:")
    if 'sentiment' in df_results.columns:
        sentiment_counts = df_results['sentiment'].value_counts()
        for sentiment, count in sentiment_counts.items():
            print(f"   {sentiment}: {count}")
    
    if 'sentiment_score' in df_results.columns:
        avg_score = df_results['sentiment_score'].astype(float).mean()
        print(f"\n📈 Average sentiment score: {avg_score:.2f}")
    
    return df_results


if __name__ == "__main__":
    main_sentiment_analysis_instagram()
