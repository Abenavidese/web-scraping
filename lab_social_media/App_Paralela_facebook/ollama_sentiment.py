# -*- coding: utf-8 -*-
"""
Facebook Sentiment Analyzer using DeepSeek API
Migrated from Ollama to centralized DeepSeek
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional

# Fix Windows encoding issues for emojis
# if sys.platform == 'win32':
#     import io
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
#     sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import centralized DeepSeek analyzer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.sentiment_analyzer import DeepSeekSentimentAnalyzer


def classify_comments_sentiment(
    comment_texts: List[str],
    _unused_api_key: Optional[str] = None,
    model: Optional[str] = None,
    batch_size: int = 15
) -> List[Dict[str, Any]]:
    """
    Clasifica sentimientos de comentarios usando DeepSeek API.
    
    Args:
        comment_texts: Lista de textos de comentarios
        _unused_api_key: Ignorado (para compatibilidad con firma anterior)
        model: Ignorado (DeepSeek usa su propio modelo)
        batch_size: Tamaño de lote para procesamiento
    
    Returns:
        Lista de diccionarios con 'sentiment' y 'reasoning'
    """
    if not comment_texts:
        return []
    
    print(f"\n🔍 Analyzing {len(comment_texts)} comments with DeepSeek...")
    
    try:
        # Initialize DeepSeek analyzer
        analyzer = DeepSeekSentimentAnalyzer()
        
        # Process in batches
        all_results = []
        
        for i in range(0, len(comment_texts), batch_size):
            batch = comment_texts[i:i + batch_size]
            print(f"   Processing batch {i//batch_size + 1} ({len(batch)} comments)...")
            
            # Prepare items
            items = [
                {'id': idx, 'text': text}
                for idx, text in enumerate(batch, start=i)
            ]
            
            # Analyze batch
            results = analyzer.analyze_batch(items, text_field='text')
            
            # Convert to expected format (uppercase sentiment labels)
            for result in results:
                sentiment = result['sentiment'].upper()
                
                # Map to expected labels
                if 'POSITIV' in sentiment:
                    sentiment = 'POSITIVO'
                elif 'NEGATIV' in sentiment:
                    sentiment = 'NEGATIVO'
                else:
                    sentiment = 'NEUTRAL'
                
                all_results.append({
                    'sentiment': sentiment,
                    'reasoning': result['reasoning']
                })
        
        print(f"✅ Analyzed {len(all_results)} comments successfully")
        return all_results
        
    except Exception as e:
        print(f"❌ Error in sentiment analysis: {e}")
        print("   Returning default values...")
        
        # Return default values on error
        return [
            {
                'sentiment': 'NEUTRAL',
                'reasoning': f'Error en análisis: {str(e)[:50]}'
            }
            for _ in comment_texts
        ]


if __name__ == "__main__":
    # Test the analyzer
    print("=== Testing Facebook Sentiment Analyzer with DeepSeek ===\n")
    
    test_comments = [
        "Me encanta este post!",
        "Muy mal servicio",
        "Está bien, nada especial"
    ]
    
    results = classify_comments_sentiment(test_comments)
    
    print("\n📊 Results:")
    for i, (comment, result) in enumerate(zip(test_comments, results)):
        print(f"\n[{i+1}] Comment: {comment}")
        print(f"    Sentiment: {result['sentiment']}")
        print(f"    Reasoning: {result['reasoning']}")
