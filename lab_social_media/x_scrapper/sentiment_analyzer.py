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


def analyze_batch_openai(client, df_sentiment, model="gpt-4o-mini"):
    """
    Analiza todos los posts en batch usando OpenAI.
    Optimizado para mínimo uso de tokens.
    
    Args:
        client: Cliente de OpenAI
        df_sentiment: DataFrame con posts
        model: Modelo a usar (gpt-4o-mini es el más barato)
    
    Returns:
        DataFrame actualizado
    """
    if client is None:
        return df_sentiment
    
    print(f"\n🔍 Analyzing {len(df_sentiment)} posts with OpenAI ({model})...")
    print("   💰 Using token-optimized prompts for cost efficiency")
    
    # Crear prompt optimizado
    batch_prompt = create_optimized_batch_prompt(df_sentiment)
    
    # Calcular tokens aproximados (1 token ≈ 4 caracteres)
    estimated_tokens = len(batch_prompt) // 4
    print(f"   📊 Estimated input tokens: ~{estimated_tokens}")
    
    # Calcular max_tokens dinámicamente según número de posts
    # Cada análisis necesita ~80 tokens (id, sentiment, score, reasoning)
    # Agregamos 30% de buffer + overhead del JSON
    num_posts = len(df_sentiment)
    max_tokens_output = max(500, int(num_posts * 80 * 1.3 + 200))
    print(f"   📤 Max output tokens: {max_tokens_output} (calculated for {num_posts} posts)")
    
    retry_count = 3
    for attempt in range(retry_count):
        try:
            print(f"\n📤 Sending request (attempt {attempt + 1}/{retry_count})...")
            
            # Llamar a OpenAI con configuración optimizada
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un analizador de sentimientos. Responde solo JSON compacto."
                    },
                    {
                        "role": "user", 
                        "content": batch_prompt
                    }
                ],
                temperature=0.3,  # Baja temperatura para respuestas consistentes
                max_tokens=max_tokens_output,   # Calculado dinámicamente según posts
                response_format={"type": "json_object"}  # Forzar JSON
            )
            
            # Extraer respuesta
            response_text = response.choices[0].message.content.strip()
            
            # Mostrar uso de tokens
            usage = response.usage
            print(f"   💰 Tokens used: {usage.total_tokens} (input: {usage.prompt_tokens}, output: {usage.completion_tokens})")
            
            # Calcular costo aproximado (GPT-4o-mini: $0.150/1M input, $0.600/1M output)
            cost_input = (usage.prompt_tokens / 1_000_000) * 0.150
            cost_output = (usage.completion_tokens / 1_000_000) * 0.600
            total_cost = cost_input + cost_output
            print(f"   💵 Estimated cost: ${total_cost:.6f}")
            
            # Parsear JSON
            # OpenAI puede devolver {"results": [...]} o directamente [...]
            data = json.loads(response_text)
            
            # Extraer array de resultados
            if isinstance(data, dict):
                # Buscar el array en el dict
                results = data.get('results') or data.get('sentiments') or list(data.values())[0]
            else:
                results = data
            
            if not isinstance(results, list):
                print(f"⚠️ Response is not a list (attempt {attempt + 1}/{retry_count})")
                continue
            
            # Actualizar DataFrame
            print("\n✅ Analysis successful! Updating results...")
            for idx, row in df_sentiment.iterrows():
                post_id = str(row['post_id'])
                result = None
                
                # Buscar por ID o índice
                for r in results:
                    if str(r.get('id')) == post_id or str(r.get('post_id')) == post_id:
                        result = r
                        break
                
                if result is None and idx < len(results):
                    result = results[idx]
                
                if result:
                    # Mapear campos (pueden tener nombres cortos)
                    sentiment = result.get('s') or result.get('sentiment') or 'unknown'
                    score = result.get('sc') or result.get('score') or 0.5
                    reasoning = result.get('r') or result.get('reasoning') or 'No reasoning provided'
                    
                    df_sentiment.at[idx, 'sentiment'] = sentiment
                    df_sentiment.at[idx, 'sentiment_score'] = score
                    df_sentiment.at[idx, 'sentiment_reasoning'] = reasoning
                    
                    print(f"   [{idx + 1}] ✅ {sentiment} (score: {score})")
                else:
                    print(f"   [{idx + 1}] ⚠️ No result, using defaults")
                    df_sentiment.at[idx, 'sentiment'] = 'unknown'
                    df_sentiment.at[idx, 'sentiment_score'] = 0.5
                    df_sentiment.at[idx, 'sentiment_reasoning'] = 'No result'
            
            print("\n✅ Sentiment analysis completed!")
            return df_sentiment
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error (attempt {attempt + 1}/{retry_count}): {e}")
            print(f"Response: {response_text[:300]}...")
            
        except Exception as e:
            print(f"⚠️ Error (attempt {attempt + 1}/{retry_count}): {e}")
        
        if attempt < retry_count - 1:
            print("   Waiting 3 seconds before retry...")
            time.sleep(3)
    
    # Si falla todo
    print("\n❌ All attempts failed, using defaults")
    for idx in df_sentiment.index:
        df_sentiment.at[idx, 'sentiment'] = 'unknown'
        df_sentiment.at[idx, 'sentiment_score'] = 0.5
        df_sentiment.at[idx, 'sentiment_reasoning'] = 'Analysis failed'
    
    return df_sentiment


def main_sentiment_analysis(input_csv='output/sentiment_input.csv', 
                           output_csv='output/sentiment_results.csv',
                           api_key=None):
    """
    Análisis de sentimientos con OpenAI.
    """
    print("=== Sentiment Analysis with OpenAI ===\n")
    
    # Cargar datos
    print(f"Loading data from {input_csv}...")
    df_sentiment = pd.read_csv(input_csv)
    print(f"Loaded {len(df_sentiment)} posts\n")
    
    # Configurar OpenAI
    client = setup_openai(api_key)
    
    if client is None:
        print("Cannot proceed without OpenAI configuration")
        return df_sentiment
    
    # Analizar en batch
    df_results = analyze_batch_openai(client, df_sentiment)
    
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
    main_sentiment_analysis()
