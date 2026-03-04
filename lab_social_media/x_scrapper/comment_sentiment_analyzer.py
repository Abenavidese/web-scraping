import os
import json
import time
import uuid
from datetime import datetime
from typing import Literal, Dict, Any
import pandas as pd
from pydantic import BaseModel, Field, ValidationError

# Intentar cargar variables de entorno locales de la raíz si no existen
try:
    from dotenv import load_dotenv
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, '.env')
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

from openai import OpenAI

# 1. Pydantic Model for strictly closed categories
class CommentAnalysis(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    emotion: Literal["fear", "anger", "sadness", "distrust", "hope", "trust", "call_to_action"]
    intensity: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0.0, le=1.0)

class RobustSentimentAnalyzer:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("No DeepSeek API key provided. Set DEEPSEEK_API_KEY in .env.")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        
        # We use standard OpenAI client for DeepSeek compatibility
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        # 1. Prompting robusto y controlado por versión
        self.prompt_version = "v1.0"
        
        # Metrics tracking
        self.metrics = {
            "total_attempts": 0,
            "invalid_json_count": 0,
            "failed_status_count": 0,
            "confidences": []
        }
        
    def analyze_comment(self, post_text: str, comment_text: str, max_retries: int = 1) -> Dict[str, Any]:
        """
        Analiza un solo comentario con Pydantic validation y repair automático.
        """
        # Instruye categorías cerradas y el formato JSON
        system_prompt = (
            f"Eres un experto analizador de sentimientos. Version: {self.prompt_version}\n"
            "Tu tarea es analizar un COMETARIO específico en el contexto de su POST ORIGINAL.\n"
            "Debes responder ÚNICAMENTE con un JSON válido que cumpla con este esquema exacto:\n"
            f"{json.dumps(CommentAnalysis.model_json_schema(), ensure_ascii=False)}\n\n"
            "No incluyas texto extra, ni bloques de código (```json). SOLO el objeto JSON."
        )
        
        user_prompt = (
            f"POST ORIGINAL: {post_text}\n"
            f"COMENTARIO A ANALIZAR: {comment_text}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Retry loop (Validation + repair)
        for attempt in range(max_retries + 1):
            self.metrics["total_attempts"] += 1
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Clean markdown if present
                if response_text.startswith("```json"):
                    response_text = response_text.replace("```json", "").replace("```", "").strip()
                elif response_text.startswith("```"):
                    response_text = response_text.replace("```", "").strip()
                
                # Intentar parsear JSON
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as decode_error:
                    self.metrics["invalid_json_count"] += 1
                    error_msg = f"JSONDecodeError: {str(decode_error)}. Por favor corrige el output y responde SÓLO con JSON válido."
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({"role": "user", "content": error_msg})
                    continue
                
                # Validar con Pydantic
                try:
                    analysis = CommentAnalysis(**data)
                    self.metrics["confidences"].append(analysis.confidence)
                    return {
                        "llm_status": "success",
                        "sentiment": analysis.sentiment,
                        "emotion": analysis.emotion,
                        "intensity": analysis.intensity,
                        "confidence": analysis.confidence,
                        "raw_json_output": response_text
                    }
                except ValidationError as ve:
                    self.metrics["invalid_json_count"] += 1
                    error_msg = f"ValidationError: {str(ve)}. El JSON no cumple el esquema requerido. Por favor corrige los campos y valores según las categorías (enums) permitidas en el esquema."
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({"role": "user", "content": error_msg})
                    continue
                    
            except Exception as e:
                print(f"   ⚠️ API Error (attempt {attempt+1}): {e}")
                time.sleep(2)
                
        # Si todos los reintentos fallan
        self.metrics["failed_status_count"] += 1
        return {
            "llm_status": "failed",
            "sentiment": None,
            "emotion": None,
            "intensity": None,
            "confidence": None,
            "raw_json_output": None
        }

def process_dataset(input_csv: str = "output/sentiment_input.csv", max_rows: int = None, platform: str = "x"):
    print(f"=== Starting Robust Comment-Level Sentiment Analysis ===")
    # 1. Read the data
    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)
    if max_rows:
        df = df.head(max_rows)
        print(f"Limiting to {max_rows} posts.")
        
    try:
        analyzer = RobustSentimentAnalyzer()
    except Exception as e:
        print(f"❌ Error initializing analyzer: {e}")
        return
    
    labeled_data = []
    total_comments = 0
    total_posts = len(df)
    
    for idx, row in df.iterrows():
        post_id = row['post_id']
        post_text = row['post_text']
        
        # Parse comments
        try:
            comments = json.loads(row['comments_json']) if pd.notna(row['comments_json']) else []
        except:
            comments = []
            
        print(f"[{idx+1}/{total_posts}] Post {post_id} - Analyzing {len(comments)} comments...")
        for comment in comments:
            total_comments += 1
            
            result = analyzer.analyze_comment(post_text, comment, max_retries=1)
            
            labeled_entry = {
                "post_id": post_id,
                "comment_text": comment,
                "prompt_version": analyzer.prompt_version,
                "llm_status": result["llm_status"],
                "sentiment": result["sentiment"],
                "emotion": result["emotion"],
                "intensity": result["intensity"],
                "confidence": result["confidence"]
            }
            labeled_data.append(labeled_entry)
            
            # Print status symbol
            status_symbol = "✅" if result["llm_status"] == "success" else "❌"
            print(f"   {status_symbol} {result['sentiment']} | {result['emotion']} | conf: {result['confidence']}")
            
    # Save the output
    df_labeled = pd.DataFrame(labeled_data)
    
    now = datetime.now()
    year_month = now.strftime("%Y-%m")
    
    # 2. Output Labeled Data a formato Parquet
    labeled_dir = f"labeled/{platform}"
    os.makedirs(labeled_dir, exist_ok=True)
    parquet_path = f"{labeled_dir}/{year_month}.parquet"
    
    df_labeled.to_parquet(parquet_path, index=False)
    print(f"\n✅ Labeled data saved to {parquet_path}")
    
    # 3. Métricas de estabilidad (Q1/Q2 extra)
    run_id = str(uuid.uuid4())[:8]
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    total_attempts = analyzer.metrics["total_attempts"]
    invalid_json_rate = analyzer.metrics["invalid_json_count"] / max(1, total_attempts)
    failed_status_rate = analyzer.metrics["failed_status_count"] / max(1, total_comments)
    
    conf_series = pd.Series(analyzer.metrics["confidences"]).dropna()
    
    metrics_data = {
        "run_id": run_id,
        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "total_posts": total_posts,
        "total_comments_processed": total_comments,
        "tasa_json_invalido": invalid_json_rate,
        "tasa_llm_status_failed": failed_status_rate,
        "confidence_mean": conf_series.mean() if not conf_series.empty else 0,
        "confidence_std": conf_series.std() if not conf_series.empty else 0,
        "confidence_q1": conf_series.quantile(0.25) if not conf_series.empty else 0,
        "confidence_q2": conf_series.quantile(0.50) if not conf_series.empty else 0,
        "confidence_q3": conf_series.quantile(0.75) if not conf_series.empty else 0,
        "prompt_version": analyzer.prompt_version
    }
    
    metrics_df = pd.DataFrame([metrics_data])
    metrics_path = f"{reports_dir}/llm_quality_{run_id}.csv"
    metrics_df.to_csv(metrics_path, index=False)
    print(f"✅ Metrics report saved to {metrics_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="output/sentiment_input.csv", help="Cuidado al elegir el path del CSV fuente")
    parser.add_argument("--max-rows", type=int, help="Limit number of posts to process (for testing)")
    parser.add_argument("--platform", default="x", help="Platform name for labeled output path")
    args = parser.parse_args()
    
    process_dataset(input_csv=args.input, max_rows=args.max_rows, platform=args.platform)
