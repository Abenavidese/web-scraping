# -*- coding: utf-8 -*-
"""
X/Twitter Sentiment Analyzer using DeepSeek API
Migrated from OpenAI to centralized DeepSeek
"""

import os
import sys
import json
import pandas as pd
import time

# Fix Windows encoding issues for emojis
# if sys.platform == 'win32':
#     import io
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
#     sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import centralized DeepSeek analyzer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.sentiment_analyzer import DeepSeekSentimentAnalyzer


def main_sentiment_analysis(input_csv='output/sentiment_input.csv', 
                           output_csv='output/sentiment_results.csv',
                           api_key=None):
    """
    Análisis de sentimientos con DeepSeek API.
    
    Args:
        input_csv: Path to input CSV with posts and comments
        output_csv: Path to output CSV with sentiment results
        api_key: Optional DeepSeek API key
    """
    print("=== Sentiment Analysis with DeepSeek ===\n")
    
    # Load data
    print(f"Loading data from {input_csv}...")
    df_sentiment = pd.read_csv(input_csv)
    print(f"Loaded {len(df_sentiment)} posts\n")
    
    # Initialize DeepSeek analyzer
    try:
        analyzer = DeepSeekSentimentAnalyzer(api_key=api_key)
    except Exception as e:
        print(f"❌ Cannot initialize DeepSeek: {e}")
        print("Please set DEEPSEEK_API_KEY in .env file")
        return df_sentiment
    
    # Prepare items for analysis
    items = []
    for idx, row in df_sentiment.iterrows():
        items.append({
            'post_id': row['post_id'],
            'post_text': row['post_text'],
            'comments_json': row['comments_json']
        })
    
    # Analyze with DeepSeek
    results = analyzer.analyze_batch(
        items,
        text_field='post_text',
        comments_field='comments_json'
    )
    
    # Update DataFrame with results
    print("\n✅ Updating results...")
    for idx, result in enumerate(results):
        df_sentiment.at[idx, 'sentiment'] = result['sentiment']
        df_sentiment.at[idx, 'sentiment_score'] = result['score']
        df_sentiment.at[idx, 'sentiment_reasoning'] = result['reasoning']
        
        print(f"   [{idx + 1}] ✅ {result['sentiment']} (score: {result['score']})")
    
    # Save results
    df_sentiment.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\n💾 Results saved to {output_csv}")
    
    # Summary
    print("\n📊 Sentiment Summary:")
    sentiment_counts = df_sentiment['sentiment'].value_counts()
    for sentiment, count in sentiment_counts.items():
        print(f"   {sentiment}: {count}")
    
    avg_score = df_sentiment['sentiment_score'].astype(float).mean()
    print(f"\n📈 Average sentiment score: {avg_score:.2f}")
    
    return df_sentiment


if __name__ == "__main__":
    main_sentiment_analysis()
