# -*- coding: utf-8 -*-
import os
import sys
import json
import glob
import pandas as pd
from typing import Dict, Any, Optional, List
from .sentiment_analyzer import DeepSeekSentimentAnalyzer

class ChatManager:
    """
    Manages the 'Chat with Data' feature.
    - Locates relevant data for a user.
    - Prepares context for the LLM.
    - Communicates with DeepSeek to answer questions.
    """
    
    def __init__(self, users_root: str = "../users"):
        self.users_root = users_root
        self.analyzer = DeepSeekSentimentAnalyzer()
        
    def find_latest_data(self, user_id: str) -> Dict[str, Any]:
        """
        Finds the most recent scrape directory for a given user.
        Returns a dict with paths to metrics and results.
        """
        user_dir = os.path.join(self.users_root, user_id)
        if not os.path.exists(user_dir):
            return {"error": "User directory not found"}
            
        # Search all subdirectories (networks -> queries -> timestamps usually)
        # Assuming structure: users/{user_id}/{network}/{query_slug}/...
        # Actually, simpler approach: find any folder with 'metrics.json' recursively
        # and sort by modification time.
        
        metrics_files = []
        for root, dirs, files in os.walk(user_dir):
            if "metrics.json" in files:
                metrics_path = os.path.join(root, "metrics.json")
                metrics_files.append(metrics_path)
                
        if not metrics_files:
            return {"error": "No scraped data found"}
            
        # Sort by modification time (newest first)
        latest_metrics_path = max(metrics_files, key=os.path.getmtime)
        data_dir = os.path.dirname(latest_metrics_path)
        
        # Find associated CSV results (sentiment_results.csv or similar)
        csv_files = glob.glob(os.path.join(data_dir, "*sentiment_results*.csv"))
        sentiment_csv = csv_files[0] if csv_files else None
        
        return {
            "path": data_dir,
            "metrics_file": latest_metrics_path,
            "sentiment_csv": sentiment_csv,
            "timestamp": os.path.getmtime(latest_metrics_path)
        }

    def load_context(self, data_info: Dict[str, Any]) -> str:
        """
        Loads data from files and formats it into a context string.
        """
        if "error" in data_info:
            return ""
            
        context_parts = []
        
        # 1. Load Metrics
        try:
            with open(data_info['metrics_file'], 'r', encoding='utf-8') as f:
                metrics = json.load(f)
                # Simplify metrics for context to save tokens
                simple_metrics = {
                    "network": metrics.get("social_network"),
                    "query": metrics.get("query"),
                    "total_posts": metrics.get("data_metrics", {}).get("posts_extracted"),
                    "total_comments": metrics.get("data_metrics", {}).get("comments_extracted"),
                    "sentiment": metrics.get("sentiment_distribution"),
                    "date": metrics.get("timestamp")
                }
                context_parts.append(f"METRICS SUMMARY:\n{json.dumps(simple_metrics, indent=2)}")
        except Exception as e:
            context_parts.append(f"Error loading metrics: {e}")
            
        # 2. Load Sample Comments (Positive vs Negative)
        if data_info['sentiment_csv']:
            try:
                df = pd.read_csv(data_info['sentiment_csv'])
                if 'sentiment' in df.columns and 'comment' in df.columns:
                    # Get sample of comments
                    pos_comments = df[df['sentiment'].str.upper() == 'POSITIVE']['comment'].head(3).tolist()
                    neg_comments = df[df['sentiment'].str.upper() == 'NEGATIVE']['comment'].head(3).tolist()
                    
                    context_parts.append("\nSAMPLE COMMENTS:")
                    if pos_comments:
                        context_parts.append("Positive Examples:\n- " + "\n- ".join(str(c)[:100] for c in pos_comments))
                    if neg_comments:
                         context_parts.append("Negative Examples:\n- " + "\n- ".join(str(c)[:100] for c in neg_comments))
            except Exception as e:
                context_parts.append(f"Error loading comments: {e}")
                
        return "\n\n".join(context_parts)

    def chat(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Main entry point for chat.
        """
        # 1. Find Data
        data_locations = self.find_latest_data(user_id)
        if "error" in data_locations:
            return {
                "response": "I couldn't find any data for you yet. Please run a scrape first.",
                "context_used": "None"
            }
            
        # 2. Prepare Context
        context_str = self.load_context(data_locations)
        
        # 3. Build Prompt
        system_prompt = (
            "Eres un asistente experto en análisis de datos de redes sociales.\n"
            "Tienes acceso a los resultados más recientes de scraping del usuario (métricas y comentarios de muestra).\n"
            "Responde las preguntas del usuario basándote estrictamente en estos datos.\n"
            "Si la respuesta no está en los datos, dilo de forma cortés.\n"
            "Sé conciso, profesional y perspicaz.\n"
            "IMPORTANTE: SIEMPRE responde en ESPAÑOL, sin importar el idioma de la pregunta."
        )
        
        full_prompt = f"DATA CONTEXT:\n{context_str}\n\nUSER QUESTION:\n{message}"
        
        # 4. Call DeepSeek (using the analyzer's client)
        # We reuse the analyzer's internal _call_deepseek_api or similar if available,
        # but DeepSeekSentimentAnalyzer is specific to sentiment.
        # We might need to call the client directly.
        # Let's inspect DeepSeekSentimentAnalyzer to see if we can reuse the client easily.
        # Ideally, we should add a raw text generation method to it or use the same lib.
        
        # For now, I'll implement a direct call here using the same library/pattern
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            )
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                stream=False
            )
            
            answer = response.choices[0].message.content
            return {
                "response": answer,
                "sources": [data_locations.get("metrics_file")]
            }
            
        except Exception as e:
            return {
                "response": f"I encountered an error analyzing your data: {e}",
                "error": str(e)
            }
