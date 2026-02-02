# -*- coding: utf-8 -*-
import os
import sys
import json
import pandas as pd
import time
from sentiment_prep import create_llm_prompt

# Fix Windows encoding issues for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Cargar variables de entorno desde .env
# Usar ruta absoluta para compatibilidad con multiprocessing en Windows
try:
    from dotenv import load_dotenv
    import os
    # Obtener directorio del script actual
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    load_dotenv(dotenv_path=env_path)
except ImportError:
    print("WARNING: python-dotenv not installed. Run: pip install python-dotenv")

# HARDCODED API KEY FALLBACK (for multiprocessing compatibility)
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = ""

# Importar OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("WARNING: openai not installed. Run: pip install openai")


def setup_openai(api_key=None):
    """
    Configura el cliente de OpenAI.
    
    Args:
        api_key: API key de OpenAI. Si es None, busca en OPENAI_API_KEY
    
    Returns:
        Cliente configurado o None si falla
    """
    if not OPENAI_AVAILABLE:
        print("ERROR: openai package not installed")
        return None
    
    # Obtener API key
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: No API key provided. Set OPENAI_API_KEY environment variable")
        print("Get your API key at: https://platform.openai.com/api-keys")
        return None
    
    # Crear cliente
    client = OpenAI(api_key=api_key)
    
    print("✅ OpenAI API configured successfully")
    return client


def create_optimized_batch_prompt(df_sentiment):
    """
    Crea un prompt ULTRA-OPTIMIZADO para minimizar tokens.
    Usa formato compacto y solo información esencial.
    
    Args:
        df_sentiment: DataFrame con posts y comentarios
        
    Returns:
        String con prompt optimizado
    """
    # Prompt ultra-compacto
    prompt = "Analiza sentimiento de posts según comentarios. Responde JSON array.\n\nPOSTS:\n"
    
    for idx, row in df_sentiment.iterrows():
        comments_list = json.loads(row['comments_json'])
        
        # Formato compacto: ID | POST | COMMENTS
        prompt += f"\n{idx+1}|{row['post_id']}|{row['post_text'][:200]}"  # Limitar post a 200 chars
        
        if comments_list and len(comments_list) > 0:
            # Concatenar comentarios de forma compacta
            comments_compact = " | ".join([c[:100] for c in comments_list[:5]])  # Max 5 comentarios, 100 chars c/u
            prompt += f"|{comments_compact}"
        else:
            prompt += "|NO_COMMENTS"
        
        prompt += "\n"
    
    # Instrucciones compactas
    prompt += '\nRespuesta JSON: [{"id":"post_id","s":"positive/negative/neutral/mixed","sc":0-1,"r":"razón breve"}]\nSolo JSON, sin markdown.'
    
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

def analyze_batch_deepseek(df_sentiment):
    """
    Analiza tweets y respuestas con DeepSeek en BATCH (Granular).
    """
    if not DEEPSEEK_AVAILABLE or not deepseek.client:
        print("⚠️ DeepSeek client not available. Skipping analysis.")
        return pd.DataFrame()
    
    print(f"\n🔍 Preparing granular analysis for {len(df_sentiment)} tweets...")
    
    all_items = []
    
    for idx, row in df_sentiment.iterrows():
        # Usar username o ID para identificar
        post_id = f"tweet_{idx}" 
        user = row.get('username', 'Unknown')
        
        # 1. Agregar el TWEET
        text = str(row['post_text']).strip()
        if text:
            all_items.append({
                "internal_id": f"{post_id}_TWEET",
                "post_id": post_id,
                "user": user,
                "type": "TWEET",
                "text": text
            })
            
        # 2. Agregar RESPUESTAS (comments)
        try:
            comments_list = json.loads(row['comments_json'])
            for i, comment in enumerate(comments_list):
                if comment.strip():
                    all_items.append({
                        "internal_id": f"{post_id}_REPLY_{i}",
                        "post_id": post_id,
                        "user": "ReplyUser",
                        "type": "REPLY",
                        "text": comment
                    })
        except:
            pass
            
    print(f"   📊 Total items to analyze: {len(all_items)} (Tweets + Replies)")
    
    if not all_items:
        return pd.DataFrame()
    
    # Batch request
    items_payload = [{"id": item['internal_id'], "text": item['text']} for item in all_items]
    
    print(f"   📤 Sending batch to DeepSeek API...")
    batch_results = deepseek.analyze_sentiment_batch(items_payload, context="Twitter/X")
    print(f"   📥 Received {len(batch_results)} results.")
    
    # Construir DataFrame granular
    granular_data = []
    for item in all_items:
        res = batch_results.get(item['internal_id'], {
            "sentiment": "NEUTRAL", 
            "score": 0.5, 
            "reasoning": "Analysis failed"
        })
        granular_data.append({
            "parent_id": item['post_id'],
            "user": item['user'],
            "item_type": item['type'],
            "text_content": item['text'],
            "sentiment": res['sentiment'],
            "sentiment_score": res['score'],
            "sentiment_reasoning": res['reasoning']
        })

    print(f"\n✅ DeepSeek granular analysis completed!")
    return pd.DataFrame(granular_data)

def main_sentiment_analysis(input_csv='output/sentiment_input.csv', 
                           output_csv='output/sentiment_results.csv',
                           api_key=None):
    """
    Análisis de sentimientos con DeepSeek.
    """
    print("=== Sentiment Analysis with DeepSeek ===\n")
    
    if not os.path.exists(input_csv):
        print(f"❌ Input file not found: {input_csv}")
        return None

    # Cargar datos
    print(f"Loading data from {input_csv}...")
    df_sentiment = pd.read_csv(input_csv)
    print(f"Loaded {len(df_sentiment)} posts\n")
    
    # Analizar usando DeepSeek
    df_results = analyze_batch_deepseek(df_sentiment)
    
    # Guardar
    df_results.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\n💾 Results saved to {output_csv}")
    
    # Resumen
    print("\n📊 Sentiment Summary:")
    sentiment_counts = df_results['sentiment'].value_counts()
    for sentiment, count in sentiment_counts.items():
        print(f"   {sentiment}: {count}")
    
    if 'sentiment_score' in df_results.columns:
        avg_score = df_results['sentiment_score'].astype(float).mean()
        print(f"\n📈 Average sentiment score: {avg_score:.2f}")
    
    return df_results

if __name__ == "__main__":
    main_sentiment_analysis()
