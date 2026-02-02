
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env ubicado en la raíz del proyecto
# Ajuste de path para asegurar que encontramos el .env subiendo niveles si es necesario
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # lab_social_media
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

class DeepSeekClient:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            # Intentar fallback si el usuario no ha puesto la key aún
            print(f"⚠️  [DeepSeekClient] DEEPSEEK_API_KEY no encontrada en {env_path}")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )

    def analyze_sentiment(self, text, context="general"):
        """
        Analiza el sentimiento de un texto usando DeepSeek.
        Retorna un diccionario con: sentiment, score, reasoning.
        """
        if not self.client:
            return {
                "sentiment": "NEUTRAL",
                "score": 0.5,
                "reasoning": "API Key no configurada"
            }

        # Truncar texto muy largo para ahorrar tokens y contexto
        safe_text = text[:1000] if text else ""

        prompt = f"""
        Analiza el sentimiento del siguiente texto de redes sociales ({context}).
        
        Texto: "{safe_text}"
        
        Responde SOLO con un JSON válido con este formato, sin bloques de código markdown:
        {{
            "sentiment": "POSITIVO" | "NEGATIVO" | "NEUTRAL",
            "score": 0.0 a 1.0 (float - usa 0.0 para negativo fuerte, 1.0 para positivo fuerte),
            "reasoning": "Breve explicación en español (max 15 palabras)"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Eres un experto analista de sentimientos. Responde solo en JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Limpieza básica por si el modelo incluye markdown
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")
            
            import json
            data = json.loads(content)
            
            # Normalizar output
            return {
                "sentiment": data.get("sentiment", "NEUTRAL").upper(),
                "score": float(data.get("score", 0.5)),
                "reasoning": data.get("reasoning", "Sin explicación")
            }
            
        except Exception as e:
            # print(f"❌ Error DeepSeek: {e}")
            return {
                "sentiment": "NEUTRAL",
                "score": 0.5,
                "reasoning": f"Error API: {str(e)[:30]}"
            }

    def analyze_sentiment_batch(self, items_list, context="general"):
        """
        Analiza una lista de textos en un solo batch.
        items_list: Lista de diccionarios [{'id': '1', 'text': '...'}]
        Retorna: Diccionario {id:Result}
        """
        if not self.client or not items_list:
            return {}

        import json

        results_map = {}
        
        # Procesar en sub-batches de 20 para no saturar contexto
        batch_size = 20
        for i in range(0, len(items_list), batch_size):
            chunk = items_list[i:i+batch_size]
            
            prompt_content = f"Analiza el sentimiento de estos {len(chunk)} elementos de {context}.\n\n"
            for item in chunk:
                # Limpiar texto para evitar romper JSON
                safe_text = str(item['text'])[:500].replace('"', "'").replace('\n', ' ')
                prompt_content += f"ID: {item['id']}\nTEXTO: {safe_text}\n\n"
                
            prompt_content += """
            Responde con un JSON ARRAY de objetos, donde cada objeto tenga:
            {"id": "ID_DEL_ITEM", "sentiment": "POSITIVO|NEGATIVO|NEUTRAL", "score": 0.0-1.0, "reasoning": "breve explicacion"}
            """
            
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "Eres un experto analista. Responde SOLO con un JSON Array válido."},
                        {"role": "user", "content": prompt_content}
                    ],
                    temperature=0.3,
                    max_tokens=2500
                )
                
                content = response.choices[0].message.content.strip()
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "")
                elif content.startswith("```"):
                    content = content.replace("```", "")
                
                batch_results = json.loads(content)
                
                # Si devuelve dict en vez de lista (a veces pasa)
                if isinstance(batch_results, dict):
                    batch_results = [batch_results]
                    
                for res in batch_results:
                    if 'id' in res:
                        results_map[str(res['id'])] = {
                            "sentiment": res.get("sentiment", "NEUTRAL").upper(),
                            "score": float(res.get("score", 0.5)),
                            "reasoning": res.get("reasoning", "Sin explicación")
                        }
                        
            except Exception as e:
                print(f"⚠️ Error en batch DeepSeek: {e}")
                
        return results_map

# Instancia simple para uso directo
deepseek = DeepSeekClient()
