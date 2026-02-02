import json
import os
import re
import urllib.request

ALLOWED_LABELS = {"POSITIVO", "NEGATIVO", "NEUTRAL"}


def _ollama_request(payload):
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    url = f"{host}/api/chat"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _chunk_list(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _parse_sentiment_results(text):
    """
    Parsea la respuesta del LLM para extraer sentimientos y razonamientos.
    Espera formato: [{"sentiment": "POSITIVO", "reasoning": "..."}, ...]
    """
    if not text:
        return []
    
    try:
        # Intentar parsear como JSON directo
        data = json.loads(text)
    except Exception:
        # Buscar JSON en el texto
        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception:
                data = []
        else:
            data = []

    # Si es una lista, retornarla
    if isinstance(data, list):
        return data
    
    # Si es un dict, buscar la lista dentro
    if isinstance(data, dict):
        for key in ("results", "sentiments", "data", "classifications"):
            if isinstance(data.get(key), list):
                return data[key]
    
    # Fallback: extraer solo las etiquetas
    labels = re.findall(r"\b(POSITIVO|NEGATIVO|NEUTRAL)\b", text.upper())
    return [{"sentiment": label, "reasoning": "Sin explicación disponible"} for label in labels]



# Importar DeepSeek Client desde utils_common
import sys
import time

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

def analyze_facebook_deepseek_granular(posts_data):
    """
    Analiza posts de Facebook y sus comentarios de forma granular usando DeepSeek Batch.
    posts_data: Lista de diccionarios con info de posts.
    Retorna: DataFrame con análisis detallado.
    """
    if not DEEPSEEK_AVAILABLE or not deepseek.client:
        print("⚠️ DeepSeek client not available.")
        return []

    print(f"   Preparando análisis granular para {len(posts_data)} posts de Facebook...")
    
    import pandas as pd
    all_items = []
    
    for idx, post in enumerate(posts_data):
        post_id = str(idx) # Facebook scrape doesn't always have ID
        
        # 1. Post Content
        content = post.get('content', '').strip()
        if content:
            all_items.append({
                "internal_id": f"fb_post_{idx}",
                "parent_id": f"post_{idx}",
                "type": "POST",
                "text": content
            })
            
        # 2. Comments
        comments = post.get('comments', [])
        for c_idx, comment in enumerate(comments):
            c_text = comment.get('text', '').strip()
            if c_text:
                all_items.append({
                    "internal_id": f"fb_comment_{idx}_{c_idx}",
                    "parent_id": f"post_{idx}",
                    "type": "COMMENT",
                    "text": c_text
                })

    if not all_items:
        return []

    # Batch Process
    print(f"   📤 Enviando {len(all_items)} items a DeepSeek (Batch)...")
    
    # Prepare payload for client
    payload_items = [{"id": x["internal_id"], "text": x["text"]} for x in all_items]
    batch_results = deepseek.analyze_sentiment_batch(payload_items, context="Facebook")
    
    print(f"   📥 Recibidos {len(batch_results)} resultados.")

    # Format Results
    granular_results = []
    for item in all_items:
        res = batch_results.get(item['internal_id'], {
            "sentiment": "NEUTRAL", 
            "score": 0.5, 
            "reasoning": "Analysis failed"
        })
        granular_results.append({
            "parent_id": item['parent_id'],
            "type": item['type'],
            "text": item['text'],
            "sentiment": res['sentiment'],
            "score": res['score'],
            "reasoning": res['reasoning']
        })
        
    # Guardar CSV granular inmediatamente
    try:
        df = pd.DataFrame(granular_results)
        df.to_csv("Resultados/sentiment_results_granular.csv", index=False, encoding='utf-8')
        print("   💾 Granular CSV saved to Resultados/sentiment_results_granular.csv")
    except Exception as e:
        print(f"Error saving granular CSV: {e}")

    return granular_results
