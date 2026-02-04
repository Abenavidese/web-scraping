# -*- coding: utf-8 -*-
"""
Test script for DeepSeek Sentiment Analyzer
Tests the centralized sentiment analysis module
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.sentiment_analyzer import DeepSeekSentimentAnalyzer, analyze_sentiment_batch


def test_basic_functionality():
    """Test basic sentiment analysis functionality"""
    print("=" * 60)
    print("Testing DeepSeek Sentiment Analyzer")
    print("=" * 60)
    print()
    
    # Test data
    test_items = [
        {
            'post_id': '1',
            'text': 'Me encanta este producto, es increíble y muy útil!',
            'comments_json': '["Totalmente de acuerdo", "El mejor producto!", "Excelente calidad"]'
        },
        {
            'post_id': '2',
            'text': 'Muy decepcionado con el servicio al cliente',
            'comments_json': '["Yo también tuve mala experiencia", "Pésimo servicio", "No lo recomiendo"]'
        },
        {
            'post_id': '3',
            'text': 'Información sobre el nuevo producto lanzado hoy',
            'comments_json': '["Gracias por la info", "Interesante", "Ok"]'
        }
    ]
    
    try:
        print("Testing batch analysis...")
        results = analyze_sentiment_batch(
            test_items,
            text_field='text',
            comments_field='comments_json'
        )
        
        print("\n" + "=" * 60)
        print("Results:")
        print("=" * 60)
        
        for i, (item, result) in enumerate(zip(test_items, results), 1):
            print(f"\n[{i}] Post: {item['text'][:50]}...")
            print(f"    Sentiment: {result['sentiment']}")
            print(f"    Score: {result['score']}")
            print(f"    Reasoning: {result['reasoning']}")
        
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nMake sure you have:")
        print("1. Set DEEPSEEK_API_KEY in .env file")
        print("2. Installed required packages: pip install openai python-dotenv")
        return False


def test_individual_analysis():
    """Test individual sentiment analysis"""
    print("\n" + "=" * 60)
    print("Testing Individual Analysis")
    print("=" * 60)
    
    try:
        analyzer = DeepSeekSentimentAnalyzer()
        
        text = "Este es un excelente producto, lo recomiendo totalmente!"
        comments = ["Estoy de acuerdo", "Muy bueno"]
        
        result = analyzer.analyze_individual(text, comments)
        
        print(f"\nText: {text}")
        print(f"Comments: {comments}")
        print(f"\nSentiment: {result['sentiment']}")
        print(f"Score: {result['score']}")
        print(f"Reasoning: {result['reasoning']}")
        
        print("\n✅ Individual analysis test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Individual analysis test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n🧪 Running DeepSeek Sentiment Analyzer Tests\n")
    
    # Test batch analysis
    batch_success = test_basic_functionality()
    
    # Test individual analysis
    if batch_success:
        individual_success = test_individual_analysis()
    else:
        individual_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Batch Analysis: {'✅ PASSED' if batch_success else '❌ FAILED'}")
    print(f"Individual Analysis: {'✅ PASSED' if individual_success else '❌ FAILED'}")
    print("=" * 60)
    
    if batch_success and individual_success:
        print("\n🎉 All tests passed! DeepSeek integration is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check your configuration.")
