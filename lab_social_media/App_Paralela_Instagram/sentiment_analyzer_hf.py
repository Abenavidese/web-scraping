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


def analyze_batch_huggingface(client, df_sentiment, model_id="meta-llama/Llama-3.2-3B-Instruct"):
    """
    Analiza todos los posts en batch usando Hugging Face.
    """
    if client is None:
        return df_sentiment
    
    print(f"\n🔍 Analyzing {len(df_sentiment)} Instagram posts with Hugging Face")
    print(f"   🤖 Model: {model_id}")
    print("   💰 Cost: $0.00 (100% FREE!)")
    
    # Crear prompt optimizado
    batch_prompt = create_batch_prompt_hf(df_sentiment)
    
    print(f"   📊 Prompt length: ~{len(batch_prompt)} chars")
    
    retry_count = 3
    for attempt in range(retry_count):
        try:
            print(f"\n📤 Sending request (attempt {attempt + 1}/{retry_count})...")
            
            # Llamar a Hugging Face usando chat completions (conversational)
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {
                        "role": "user",
                        "content": batch_prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Extraer texto de la respuesta
            response_text = response.choices[0].message.content
            
            print(f"\n✅ Response received ({len(response_text)} chars)")
            
            # Limpiar respuesta
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            # Parsear JSON
            try:
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    results = json.loads(json_str)
                else:
                    results = json.loads(response_text)
                
                if not isinstance(results, list):
                    print(f"⚠️ Response is not a list (attempt {attempt + 1}/{retry_count})")
                    print(f"Response preview: {response_text[:200]}")
                    continue
                
                # Actualizar DataFrame
                print("\n✅ Analysis successful! Updating results...")
                for idx, row in df_sentiment.iterrows():
                    post_id = str(row['post_id'])
                    result = None
                    
                    for r in results:
                        if str(r.get('id')) == post_id or str(r.get('post_id')) == post_id:
                            result = r
                            break
                    
                    if result is None and idx < len(results):
                        result = results[idx]
                    
                    if result:
                        sentiment = result.get('sentiment', 'unknown')
                        score = result.get('score', 0.5)
                        reasoning = result.get('reasoning', 'No reasoning provided')
                        
                        df_sentiment.at[idx, 'sentiment'] = sentiment
                        df_sentiment.at[idx, 'sentiment_score'] = score
                        df_sentiment.at[idx, 'sentiment_reasoning'] = reasoning
                        
                        print(f"   [{idx + 1}] ✅ {sentiment} (score: {score})")
                    else:
                        print(f"   [{idx + 1}] ⚠️ No result")
                        df_sentiment.at[idx, 'sentiment'] = 'unknown'
                        df_sentiment.at[idx, 'sentiment_score'] = 0.5
                        df_sentiment.at[idx, 'sentiment_reasoning'] = 'No result'
                
                print("\n✅ Sentiment analysis completed!")
                return df_sentiment
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parse error (attempt {attempt + 1}/{retry_count}): {e}")
                print(f"Response preview: {response_text[:300]}")
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if 'loading' in error_msg or '503' in error_msg:
                print(f"   ⏳ Model is loading... waiting 20 seconds")
                time.sleep(20)
                continue
            elif 'rate' in error_msg or '429' in error_msg:
                print(f"   ⚠️ Rate limit reached, waiting 10 seconds...")
                time.sleep(10)
                continue
            else:
                print(f"⚠️ Error (attempt {attempt + 1}/{retry_count}): {e}")
        
        if attempt < retry_count - 1:
            print("   Waiting 5 seconds before retry...")
            time.sleep(5)
    
    # Fallback a análisis individual
    print("\n⚠️ Batch analysis failed, trying individual analysis...")
    return analyze_individual_huggingface(client, df_sentiment, model_id)


def analyze_individual_huggingface(client, df_sentiment, model_id="meta-llama/Llama-3.2-3B-Instruct"):
    """
    Analiza posts individualmente como fallback.
    """
    print(f"\n🔍 Analyzing {len(df_sentiment)} posts individually...")
    
    for idx, row in df_sentiment.iterrows():
        try:
            comments_list = json.loads(row['comments_json'])
            
            prompt = f"""Analyze sentiment of this Instagram post based on comments.

POST: {row['post_caption'][:150]}

COMMENTS: {' | '.join([c[:80] for c in comments_list[:5]]) if comments_list else 'NONE'}

Respond ONLY with JSON: {{"sentiment":"positive/negative/neutral/mixed","score":0-1,"reasoning":"brief"}}"""
            
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content
            
            # Limpiar y parsear
            response_text = response_text.strip()
            if '```' in response_text:
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response_text[start:end]
                data = json.loads(json_str)
                
                df_sentiment.at[idx, 'sentiment'] = data.get('sentiment', 'unknown')
                df_sentiment.at[idx, 'sentiment_score'] = data.get('score', 0.5)
                df_sentiment.at[idx, 'sentiment_reasoning'] = data.get('reasoning', 'No reasoning')
                
                print(f"   [{idx + 1}] ✅ {data.get('sentiment')}")
            else:
                raise ValueError("No JSON found")
                
        except Exception as e:
            print(f"   [{idx + 1}] ❌ Error: {e}")
            df_sentiment.at[idx, 'sentiment'] = 'unknown'
            df_sentiment.at[idx, 'sentiment_score'] = 0.5
            df_sentiment.at[idx, 'sentiment_reasoning'] = f'Error: {str(e)[:50]}'
        
        time.sleep(1)
    
    return df_sentiment


def main_sentiment_analysis_instagram(input_csv='Resultados/sentiment_input.csv',
                                     output_csv='Resultados/sentiment_results.csv',
                                     api_key=None,
                                     model_id="meta-llama/Llama-3.2-3B-Instruct"):
    """
    Análisis de sentimientos para Instagram con Hugging Face.
    """
    print("=" * 60)
    print("Instagram Sentiment Analysis with Hugging Face (FREE)")
    print("=" * 60)
    print()
    
    # Cargar datos
    print(f"Loading data from {input_csv}...")
    df_sentiment = pd.read_csv(input_csv)
    print(f"Loaded {len(df_sentiment)} posts\n")
    
    # Configurar Hugging Face
    client = setup_huggingface(api_key)
    
    if client is None:
        print("Cannot proceed without Hugging Face configuration")
        return df_sentiment
    
    # Analizar en batch
    df_results = analyze_batch_huggingface(client, df_sentiment, model_id)
    
    # Guardar
    df_results.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\n💾 Results saved to {output_csv}")
    
    # Resumen
    print("\n📊 Sentiment Summary:")
    sentiment_counts = df_results['sentiment'].value_counts()
    for sentiment, count in sentiment_counts.items():
        print(f"   {sentiment}: {count}")
    
    avg_score = df_results['sentiment_score'].astype(float).mean()
    print(f"\n📈 Average sentiment score: {avg_score:.2f}")
    
    return df_results


if __name__ == "__main__":
    main_sentiment_analysis_instagram()
