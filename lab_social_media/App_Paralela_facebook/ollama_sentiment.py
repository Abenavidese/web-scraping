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


def classify_comments_sentiment(
    comment_texts,
    _unused_api_key=None,
    model=None,
    batch_size=15,  # Reducido para mejor calidad de respuesta
):
    """
    Clasifica sentimientos de comentarios usando Ollama con explicabilidad.
    
    Args:
        comment_texts: Lista de textos de comentarios
        model: Modelo de Ollama a usar
        batch_size: Tamaño de lote para procesamiento
    
    Returns:
        Lista de diccionarios con 'sentiment' y 'reasoning'
    """
    if not comment_texts:
        return []

    model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    # Prompt mejorado para incluir explicabilidad
    system_prompt = (
        "Eres un clasificador de sentimiento para comentarios de redes sociales. "
        "Debes clasificar cada comentario Y explicar brevemente por qué. "
        "Responde SOLO con un JSON array con este formato: "
        '[{"sentiment": "POSITIVO/NEGATIVO/NEUTRAL", "reasoning": "breve explicación"}]. '
        "No uses markdown ni texto adicional. Solo el JSON array."
    )

    results = []
    for batch in _chunk_list(comment_texts, batch_size):
        user_content = (
            "Clasifica el sentimiento de estos comentarios en español y explica brevemente cada uno.\n\n"
            f"Comentarios:\n"
        )
        
        # Enumerar comentarios para mejor tracking
        for i, comment in enumerate(batch, 1):
            user_content += f"{i}. {comment}\n"
        
        user_content += (
            f'\n\nResponde con JSON: [{{"sentiment": "POSITIVO/NEGATIVO/NEUTRAL", "reasoning": "explicación breve"}}]'
        )
        
        payload = {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "options": {
                "temperature": 0.3,  # Un poco más de creatividad para explicaciones
                "num_gpu": 99  # Force GPU usage
            },
        }
        
        try:
            response = _ollama_request(payload)
            text = response.get("message", {}).get("content", "").strip()
            
            # Parsear resultados con explicabilidad
            parsed_results = _parse_sentiment_results(text)
            
            # Validar y normalizar resultados
            for i in range(len(batch)):
                if i < len(parsed_results):
                    result = parsed_results[i]
                    
                    # Extraer sentimiento
                    if isinstance(result, dict):
                        sentiment = result.get("sentiment", "NEUTRAL")
                        reasoning = result.get("reasoning", "Sin explicación")
                    elif isinstance(result, str):
                        sentiment = result
                        reasoning = "Sin explicación disponible"
                    else:
                        sentiment = "NEUTRAL"
                        reasoning = "Formato de respuesta inválido"
                    
                    # Normalizar sentimiento
                    sentiment = sentiment.strip().upper()
                    if sentiment not in ALLOWED_LABELS:
                        sentiment = "NEUTRAL"
                    
                    results.append({
                        "sentiment": sentiment,
                        "reasoning": reasoning
                    })
                else:
                    # Fallback si no hay suficientes resultados
                    results.append({
                        "sentiment": "NEUTRAL",
                        "reasoning": "No se pudo analizar el comentario"
                    })
                    
        except Exception as e:
            # En caso de error, agregar resultados por defecto
            print(f"Error en clasificación de lote: {e}")
            for _ in range(len(batch)):
                results.append({
                    "sentiment": "NEUTRAL",
                    "reasoning": f"Error en análisis: {str(e)[:50]}"
                })

    return results
