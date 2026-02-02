
# Importar DeepSeek Client desde utils_common
import sys
import os
# Asegurar que podemos importar utils_common subiendo un nivel
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir)) # Subir 2 niveles: linkedin_scraper -> lab_social_media -> root
sys.path.append(parent_dir)

try:
    from utils_common.deepseek_client import deepseek
    DEEPSEEK_AVAILABLE = True
except ImportError as e:
    DEEPSEEK_AVAILABLE = False
    print(f"WARNING: Could not import DeepSeek client: {e}")


class LLMAnalyzer:
    def __init__(self):
        self.client = deepseek
        
    def analyze(self, text, network, llm_provider='deepseek'):
        """
        Analiza usando DeepSeek (el provider ya es irrelevante, forzamos DeepSeek).
        Retorna (Sentimiento, Explicación) strings para compatibilidad con llamadas legacy (si las hay).
        """
        if not text:
            return "NEUTRAL", "Texto vacío"
            
        if not self.client.client:
             return "NEUTRAL", "DeepSeek API Key no configurada"

        result = self.client.analyze_sentiment(text, context=network)
        return result['sentiment'], result['reasoning']

    def analyze_batch_granular(self, posts_data):
        """
        Analiza items granulares (Post y Comentarios) en Batch.
        posts_data: Lista de dicts de posts scrapeados.
        Retorna: Lista de resultados granulares.
        """
        if not self.client.client:
            print("⚠️ DeepSeek client not available.")
            return []
            
        print(f"   Preparando análisis granular para {len(posts_data)} posts de LinkedIn...")
        
        all_items = []
        for idx, post in enumerate(posts_data):
            # 1. Post Body
            content = post.get('content', '').strip()
            if content:
                all_items.append({
                    "internal_id": f"li_post_{idx}",
                    "parent_id": f"post_{idx}",
                    "type": "POST",
                    "text": content,
                    # Preservar metadatos para el CSV final si queremos
                    "author": post.get('author', 'Unknown')
                })
            
            # 2. Comentarios
            comments = post.get('comments', [])
            # A veces comentarios es int, asegurar que sea lista
            if isinstance(comments, list):
                for c_idx, comment in enumerate(comments):
                    c_text = comment.get('text', '').strip() if isinstance(comment, dict) else str(comment).strip()
                    if c_text:
                        all_items.append({
                            "internal_id": f"li_comment_{idx}_{c_idx}",
                            "parent_id": f"post_{idx}",
                            "type": "COMMENT",
                            "text": c_text,
                            "author": comment.get('author', 'Unknown') if isinstance(comment, dict) else "Unknown"
                        })
                        
        if not all_items:
            return []
            
        # Batch Process
        print(f"   📤 Enviando {len(all_items)} items a DeepSeek (Batch)...")
        payload = [{"id": x["internal_id"], "text": x["text"]} for x in all_items]
        
        batch_results = self.client.analyze_sentiment_batch(payload, context="LinkedIn")
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
                "author": item.get('author', 'Unknown'),
                "text": item['text'],
                "sentiment": res['sentiment'],
                "score": res['score'],
                "reasoning": res['reasoning']
            })
            
        return granular_results
