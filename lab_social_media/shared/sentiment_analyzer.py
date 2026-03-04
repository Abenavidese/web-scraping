# -*- coding: utf-8 -*-
"""
Centralized Sentiment Analyzer using DeepSeek API
Replaces individual LLM implementations (OpenAI, Hugging Face, Ollama, Grok)
"""

import os
import sys
import json
import time
import uuid
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

# Fix Windows encoding issues for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment variables
try:
    from dotenv import load_dotenv
    # Load from root .env
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, '.env')
    load_dotenv(dotenv_path=env_path)
except ImportError:
    print("WARNING: python-dotenv not installed. Run: pip install python-dotenv")

# Import OpenAI-compatible client (DeepSeek uses OpenAI SDK)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("WARNING: openai not installed. Run: pip install openai")


from pydantic import BaseModel, Field, ValidationError
from typing import Literal
import concurrent.futures

class SentimentAnalysis(BaseModel):
    sentiment: Literal["positive", "neutral", "negative", "mixed", "unknown"]
    emotion: Literal["fear", "anger", "sadness", "distrust", "hope", "trust", "call_to_action", "neutral_state"]
    intensity: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class DeepSeekSentimentAnalyzer:
    """Centralized sentiment analyzer using DeepSeek API with Pydantic validation"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize DeepSeek client.
        
        Args:
            api_key: DeepSeek API key. If None, reads from DEEPSEEK_API_KEY env var
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        # Get API key
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No DeepSeek API key provided. Set DEEPSEEK_API_KEY in .env file.\n"
                "Get your API key at: https://platform.deepseek.com/api_keys"
            )
        
        # Get configuration
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.prompt_version = "v2.0_shared"
        
        # Initialize client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        print(f"✅ DeepSeek API configured (model: {self.model})")
    
    def analyze_batch(
        self,
        items: List[Dict[str, Any]],
        text_field: str = 'text',
        comments_field: Optional[str] = None,
        max_retries: int = 2,
        max_workers: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a batch of items using concurrent individual calls.
        
        Args:
            items: List of dictionaries containing text to analyze
            text_field: Field name containing the main text
            comments_field: Optional field name containing comments JSON string or list
            max_retries: Number of retry attempts per individual call
            max_workers: Number of parallel processing threads
        
        Returns:
            List of dictionaries with sentiment analysis results
        """
        if not items:
            return []
        
        print(f"\n🔍 Analyzing {len(items)} items concurrently with DeepSeek...")
        
        def process_single(item):
            text = str(item.get(text_field, ''))
            
            # Handle comments parsing
            comments = None
            if comments_field and comments_field in item:
                val = item[comments_field]
                if isinstance(val, str) and val.strip().startswith('['):
                    try:
                        comments = json.loads(val)
                    except:
                        comments = []
                elif isinstance(val, list):
                    comments = val
            
            return self.analyze_individual(text, comments, max_retries)
            
        # Execute concurrently
        results = []
        completed = 0
        total = len(items)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {executor.submit(process_single, item): item for item in items}
            
            for future in concurrent.futures.as_completed(future_to_item):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as exc:
                    print(f"⚠️ Error in concurrent processing: {exc}")
                    results.append({
                        'sentiment': 'unknown',
                        'emotion': 'none',
                        'intensity': 'none',
                        'confidence': 0.0,
                        'reasoning': f"Error: {str(exc)}",
                        'score': 0.0,
                        'status': 'error'
                    })
                
                completed += 1
                if completed % max(1, total // 10) == 0 or completed == total:
                    print(f"   [{completed}/{total}] items processed...")
                    
        return results
    
    def analyze_individual(
        self,
        text: str,
        comments: Optional[List[str]] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for a single item with Pydantic validation and auto-repair.
        
        Args:
            text: Main text to analyze
            comments: Optional list of comments
            max_retries: Number of retry attempts for schema validation
        
        Returns:
            Dictionary with parsed sentiment analysis or fallback values
        """
        
        system_prompt = (
            f"Eres un experto analizador de sentimientos. Version: {self.prompt_version}\n"
            "Tu tarea es analizar el texto suministrado en el contexto de un POST (y posiblemente sus COMENTARIOS).\n"
            "Identifica el sentimiento predominante, la emoción primaria y su intensidad.\n"
            "Debes responder ÚNICAMENTE con un JSON válido que cumpla con este esquema exacto:\n"
            f"{json.dumps(SentimentAnalysis.model_json_schema(), ensure_ascii=False)}\n\n"
            "No incluyas texto extra, ni bloques de código (```json). SOLO el objeto JSON."
        )
        
        user_prompt = f"TEXTO A ANALIZAR: {text[:1500]}\n"
        
        if comments and len(comments) > 0:
            comments_str_list = []
            for c in comments[:10]:
                if isinstance(c, dict):
                    comments_str_list.append(str(c.get('text', ''))[:200])
                else:
                    comments_str_list.append(str(c)[:200])
            comments_str = " | ".join(comments_str_list)
            user_prompt += f"\nCOMENTARIOS DEL POST: {comments_str}\n"
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=300
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Clean markdown if present
                if response_text.startswith("```json"):
                    response_text = response_text.replace("```json", "").replace("```", "").strip()
                elif response_text.startswith("```"):
                    response_text = response_text.replace("```", "").strip()
                
                # Parse and strict-validate using Pydantic
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as decode_error:
                    error_msg = f"JSONDecodeError: {str(decode_error)}. Por favor corrige el output y responde SÓLO con JSON válido."
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({"role": "user", "content": error_msg})
                    continue
                
                try:
                    analysis = SentimentAnalysis(**data)
                    return {
                        'status': 'success',
                        'sentiment': analysis.sentiment,
                        'emotion': analysis.emotion,
                        'intensity': analysis.intensity,
                        'confidence': analysis.confidence,
                        'score': analysis.confidence, # backward compatibility
                        'reasoning': analysis.reasoning
                    }
                except ValidationError as ve:
                    error_msg = f"ValidationError: {str(ve)}. El JSON no cumple el esquema requerido. Corrige campos según las categorías (enums) permitidas en el esquema."
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({"role": "user", "content": error_msg})
                    continue
                    
            except Exception as e:
                print(f"   ⚠️ API Error (attempt {attempt+1}): {e}")
                time.sleep(2)
        
        return {
            'status': 'failed',
            'sentiment': 'unknown',
            'emotion': 'none',
            'intensity': 'none',
            'confidence': 0.0,
            'score': 0.0,
            'reasoning': 'Analysis mapping failed after retries'
        }

    def harmonize_dataset(self, df: pd.DataFrame, platform: str, target_per_month: int = 1000) -> pd.DataFrame:
        """
        Phase 3: Harmonization and balance.
        Estratifica por year y month. Si N > target, hace subsample.
        Si N < target, conserva todo y marca low_volume.
        Exports run_audit.csv and saves normalized parquet.
        """
        print(f"\n=== Phase 3: Harmonizing Dataset for {platform} ===")
        
        if 'year' not in df.columns or 'month' not in df.columns:
            # Intentar deducir
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
                df['year'] = df['timestamp'].dt.year
                df['month'] = df['timestamp'].dt.month
            else:
                df['year'] = datetime.now().year
                df['month'] = datetime.now().month
                
        # Fill NA
        df['year'] = df['year'].fillna(datetime.now().year).astype(int)
        df['month'] = df['month'].fillna(datetime.now().month).astype(int)
        
        audit_records = []
        harmonized_frames = []
        
        out_dir = f"normalized/final/{platform}"
        os.makedirs(out_dir, exist_ok=True)
        
        for (year, month), group in df.groupby(['year', 'month']):
            current_n = len(group)
            
            if current_n > target_per_month:
                # Subsample
                sampled = group.sample(n=target_per_month, random_state=42)
                low_volume = False
                final_n = target_per_month
            else:
                sampled = group.copy()
                low_volume = True
                final_n = current_n
                
            sampled['is_low_volume'] = low_volume
            harmonized_frames.append(sampled)
            
            audit_records.append({
                'platform': platform,
                'year': year,
                'month': month,
                'original_n': current_n,
                'target_n': target_per_month,
                'final_n': final_n,
                'low_volume_flag': low_volume,
                'timestamp': datetime.now().isoformat()
            })
            
            # Export parquet
            ym_str = f"{year}-{month:02d}"
            pq_path = os.path.join(out_dir, f"{ym_str}.parquet")
            sampled.to_parquet(pq_path, index=False)
            print(f"  -> Saved normalized data to {pq_path} (N={final_n})")
            
        final_df = pd.concat(harmonized_frames, ignore_index=True) if harmonized_frames else pd.DataFrame()
        
        # Save audit
        audit_df = pd.DataFrame(audit_records)
        os.makedirs("reports", exist_ok=True)
        audit_path = os.path.join("reports", f"run_audit_{platform}_{int(time.time())}.csv")
        audit_df.to_csv(audit_path, index=False)
        print(f"  -> Saved audit report to {audit_path}")
        
        return final_df

    def process_dataset_robustly(self, df: pd.DataFrame, platform: str, text_col: str = 'text', comments_col: str = 'comments', max_workers: int = 5) -> pd.DataFrame:
        """
        Phase 4: Hierarchical Classification + Robustness Metrics
        Executes robust LLM calls and tracks metrics, outputs labelled Parquet.
        """
        print(f"\n=== Phase 4: Robust LLM Classification for {platform} ===")
        total_items = len(df)
        
        metrics = {
            "total_attempts": 0,
            "failed_status_count": 0,
            "invalid_json_count": 0, 
            "confidences": []
        }
        
        items = []
        for idx, row in df.iterrows():
            item = dict(row)
            item['text_for_llm'] = row[text_col] if text_col in row else row.get('text', '')
            item['comments_for_llm'] = row[comments_col] if comments_col in row else ''
            items.append(item)
            
        # Analysis
        start_time = time.time()
        results = self.analyze_batch(
            items,
            text_field='text_for_llm',
            comments_field='comments_for_llm',
            max_retries=2,
            max_workers=max_workers
        )
        end_time = time.time()
        
        # Merge results into dataframe
        for idx, res in enumerate(results):
            df.at[idx, 'sentiment'] = res.get('sentiment', 'unknown')
            df.at[idx, 'emotion'] = res.get('emotion', 'none')
            df.at[idx, 'intensity'] = res.get('intensity', 'none')
            df.at[idx, 'confidence'] = res.get('confidence', 0.0)
            df.at[idx, 'reasoning'] = res.get('reasoning', '')
            
            if res.get('status') == 'failed':
                metrics['failed_status_count'] += 1
            if res.get('confidence', 0.0) > 0:
                metrics['confidences'].append(res['confidence'])
                
        metrics['total_attempts'] = len(results)
        
        # Output Labeled Data
        year_month = datetime.now().strftime("%Y-%m")
        labeled_dir = f"labeled/{platform}"
        os.makedirs(labeled_dir, exist_ok=True)
        parquet_path = f"{labeled_dir}/{year_month}.parquet"
        
        df.to_parquet(parquet_path, index=False)
        print(f"\n✅ Labeled data saved to {parquet_path}")
        
        # Export Quality Metrics
        run_id = str(uuid.uuid4())[:8]
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        failed_rate = metrics["failed_status_count"] / max(1, total_items)
        conf_series = pd.Series(metrics["confidences"])
        
        metrics_data = {
           "run_id": run_id,
           "platform": platform,
           "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "total_processed": total_items,
           "tasa_llm_status_failed": failed_rate,
           "confidence_mean": conf_series.mean() if not conf_series.empty else 0,
           "confidence_std": conf_series.std() if not conf_series.empty else 0,
           "confidence_q1": conf_series.quantile(0.25) if not conf_series.empty else 0,
           "confidence_q2": conf_series.quantile(0.50) if not conf_series.empty else 0,
           "confidence_q3": conf_series.quantile(0.75) if not conf_series.empty else 0,
           "prompt_version": self.prompt_version,
           "execution_time_s": round(end_time - start_time, 2)
        }
        
        metrics_df = pd.DataFrame([metrics_data])
        metrics_path = f"{reports_dir}/llm_quality_{run_id}.csv"
        metrics_df.to_csv(metrics_path, index=False)
        print(f"✅ LLM Quality metrics report saved to {metrics_path}")
        
        return df


# Convenience functions for backward compatibility
def analyze_sentiment_batch(
    items: List[Dict[str, Any]],
    text_field: str = 'text',
    comments_field: Optional[str] = None,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Analyze sentiment for a batch of items using DeepSeek.
    
    Args:
        items: List of dictionaries containing text to analyze
        text_field: Field name containing the main text
        comments_field: Optional field name containing comments
        api_key: Optional API key (uses env var if not provided)
    
    Returns:
        List of sentiment analysis results
    """
    analyzer = DeepSeekSentimentAnalyzer(api_key=api_key)
    return analyzer.analyze_batch(items, text_field, comments_field)


def analyze_sentiment_individual(
    text: str,
    comments: Optional[List[str]] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze sentiment for a single item using DeepSeek.
    
    Args:
        text: Main text to analyze
        comments: Optional list of comments
        api_key: Optional API key (uses env var if not provided)
    
    Returns:
        Sentiment analysis result
    """
    analyzer = DeepSeekSentimentAnalyzer(api_key=api_key)
    return analyzer.analyze_individual(text, comments)


if __name__ == "__main__":
    # Test the analyzer
    print("=== Testing DeepSeek Sentiment Analyzer ===\n")
    
    test_items = [
        {
            'post_id': '1',
            'text': 'Me encanta este producto, es increíble!',
            'comments_json': '["Totalmente de acuerdo", "El mejor!"]'
        },
        {
            'post_id': '2',
            'text': 'Muy decepcionado con el servicio',
            'comments_json': '["Yo también", "Pésimo"]'
        }
    ]
    
    try:
        results = analyze_sentiment_batch(test_items, text_field='text', comments_field='comments_json')
        
        print("\n📊 Results:")
        for i, result in enumerate(results):
            print(f"\n[{i+1}] Sentiment: {result['sentiment']}")
            print(f"    Score: {result['score']}")
            print(f"    Reasoning: {result['reasoning']}")
    except Exception as e:
        print(f"❌ Error: {e}")
