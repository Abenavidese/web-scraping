# -*- coding: utf-8 -*-
"""
LinkedIn LLM Processor using DeepSeek API
Migrated to use centralized DeepSeek analyzer
"""

import os
import sys

# Import centralized DeepSeek analyzer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.sentiment_analyzer import DeepSeekSentimentAnalyzer


class LLMAnalyzer:
    """
    LLM Analyzer for LinkedIn posts using DeepSeek API.
    Maintains compatibility with existing async workflow.
    """
    
    def __init__(self):
        """Initialize DeepSeek analyzer"""
        try:
            self.analyzer = DeepSeekSentimentAnalyzer()
            print("✅ LinkedIn LLM Analyzer initialized with DeepSeek")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize DeepSeek: {e}")
            self.analyzer = None
    
    def analyze(self, text: str, network: str = "LinkedIn", provider: str = "deepseek"):
        """
        Analyze sentiment of text using DeepSeek.
        
        Args:
            text: Text to analyze
            network: Social network name (for context)
            provider: LLM provider (ignored, always uses DeepSeek)
        
        Returns:
            Tuple of (sentiment, explanation)
        """
        if not text or len(text) < 5:
            return "Neutro", "Texto insuficiente para analizar."
        
        if not self.analyzer:
            return "Error", "DeepSeek analyzer not initialized"
        
        try:
            # Use individual analysis for single posts
            result = self.analyzer.analyze_individual(text)
            
            # Map sentiment to Spanish format expected by LinkedIn scraper
            sentiment = result['sentiment']
            if 'positiv' in sentiment.lower():
                sentiment = "Positivo"
            elif 'negativ' in sentiment.lower():
                sentiment = "Negativo"
            elif 'neutral' in sentiment.lower():
                sentiment = "Neutro"
            else:
                sentiment = "Neutro"
            
            explanation = result['reasoning']
            
            return sentiment, explanation
            
        except Exception as e:
            return "Error", f"Fallo en análisis con DeepSeek: {str(e)}"


if __name__ == "__main__":
    # Test the analyzer
    print("=== Testing LinkedIn LLM Analyzer with DeepSeek ===\n")
    
    analyzer = LLMAnalyzer()
    
    test_texts = [
        "Excelente oportunidad de trabajo en una empresa innovadora!",
        "Muy decepcionado con el proceso de selección",
        "Información sobre el puesto de desarrollador"
    ]
    
    for i, text in enumerate(test_texts, 1):
        sentiment, explanation = analyzer.analyze(text, "LinkedIn")
        print(f"\n[{i}] Text: {text}")
        print(f"    Sentiment: {sentiment}")
        print(f"    Explanation: {explanation}")
