# -*- coding: utf-8 -*-
"""
Centralized Sentiment Analyzer using DeepSeek API
Replaces individual LLM implementations (OpenAI, Hugging Face, Ollama, Grok)
"""

import os
import sys
import json
import time
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


class DeepSeekSentimentAnalyzer:
    """Centralized sentiment analyzer using DeepSeek API"""
    
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
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a batch of items.
        
        Args:
            items: List of dictionaries containing text to analyze
            text_field: Field name containing the main text (e.g., 'post_text', 'post_caption')
            comments_field: Optional field name containing comments JSON string
            max_retries: Number of retry attempts
        
        Returns:
            List of dictionaries with sentiment analysis results:
            {
                'sentiment': 'positive/negative/neutral/mixed',
                'score': float (0-1),
                'reasoning': str
            }
        """
        if not items:
            return []
        
        print(f"\n🔍 Analyzing {len(items)} items with DeepSeek...")
        
        # Create batch prompt
        prompt = self._create_batch_prompt(items, text_field, comments_field)
        
        # Estimate tokens
        estimated_tokens = len(prompt) // 4
        print(f"   📊 Estimated input tokens: ~{estimated_tokens}")
        
        # Calculate max output tokens
        max_tokens_output = max(500, int(len(items) * 80 * 1.3 + 200))
        print(f"   📤 Max output tokens: {max_tokens_output}")
        
        # Retry loop
        for attempt in range(max_retries):
            try:
                print(f"\n📤 Sending request (attempt {attempt + 1}/{max_retries})...")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un analizador de sentimientos experto. Responde solo con JSON válido."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=max_tokens_output
                )
                
                # Extract response
                response_text = response.choices[0].message.content.strip()
                
                # Show token usage
                usage = response.usage
                print(f"   💰 Tokens used: {usage.total_tokens} (input: {usage.prompt_tokens}, output: {usage.completion_tokens})")
                
                # Parse JSON
                results = self._parse_response(response_text, len(items))
                
                print(f"\n✅ Analysis successful! Processed {len(results)} items")
                return results
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parse error (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Response preview: {response_text[:300]}...")
                
            except Exception as e:
                print(f"⚠️ Error (attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                print("   Waiting 3 seconds before retry...")
                time.sleep(3)
        
        # If all retries fail, return defaults
        print("\n❌ All attempts failed, using default values")
        return [
            {
                'sentiment': 'unknown',
                'score': 0.5,
                'reasoning': 'Analysis failed after retries'
            }
            for _ in items
        ]
    
    def analyze_individual(
        self,
        text: str,
        comments: Optional[List[str]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for a single item.
        
        Args:
            text: Main text to analyze
            comments: Optional list of comments
            max_retries: Number of retry attempts
        
        Returns:
            Dictionary with sentiment analysis:
            {
                'sentiment': 'positive/negative/neutral/mixed',
                'score': float (0-1),
                'reasoning': str
            }
        """
        prompt = self._create_individual_prompt(text, comments)
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un analizador de sentimientos. Responde solo con JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=200
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Clean and parse JSON
                response_text = self._clean_json_response(response_text)
                data = json.loads(response_text)
                
                return {
                    'sentiment': data.get('sentiment', 'unknown'),
                    'score': data.get('score', 0.5),
                    'reasoning': data.get('reasoning', 'No reasoning provided')
                }
                
            except Exception as e:
                print(f"⚠️ Error analyzing item (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return {
            'sentiment': 'unknown',
            'score': 0.5,
            'reasoning': 'Analysis failed'
        }
    
    def _create_batch_prompt(
        self,
        items: List[Dict[str, Any]],
        text_field: str,
        comments_field: Optional[str]
    ) -> str:
        """Create optimized batch prompt"""
        prompt = "Analiza el sentimiento de los siguientes posts. Responde con un JSON array.\n\nPOSTS:\n"
        
        for idx, item in enumerate(items):
            text = str(item.get(text_field, ''))[:200]  # Limit to 200 chars
            item_id = item.get('post_id', item.get('id', idx + 1))
            
            prompt += f"\n{idx+1}|{item_id}|{text}"
            
            # Add comments if available
            if comments_field and comments_field in item:
                comments_json = item[comments_field]
                try:
                    if isinstance(comments_json, str):
                        comments_list = json.loads(comments_json)
                    else:
                        comments_list = comments_json
                    
                    if comments_list and len(comments_list) > 0:
                        comments_compact = " | ".join([str(c)[:100] for c in comments_list[:5]])
                        prompt += f"|{comments_compact}"
                    else:
                        prompt += "|NO_COMMENTS"
                except:
                    prompt += "|NO_COMMENTS"
            else:
                prompt += "|NO_COMMENTS"
            
            prompt += "\n"
        
        prompt += '\n\nRespuesta JSON: [{"id":"post_id","sentiment":"positive/negative/neutral/mixed","score":0-1,"reasoning":"razón breve"}]\nSolo JSON, sin markdown.'
        
        return prompt
    
    def _create_individual_prompt(self, text: str, comments: Optional[List[str]]) -> str:
        """Create prompt for individual analysis"""
        prompt = f"Analiza el sentimiento de este post:\n\nPOST: {text[:200]}\n"
        
        if comments and len(comments) > 0:
            comments_str = " | ".join([c[:80] for c in comments[:5]])
            prompt += f"\nCOMENTARIOS: {comments_str}\n"
        else:
            prompt += "\nCOMENTARIOS: NINGUNO\n"
        
        prompt += '\n\nResponde con JSON: {"sentiment":"positive/negative/neutral/mixed","score":0-1,"reasoning":"breve"}\nSolo JSON, sin markdown.'
        
        return prompt
    
    def _clean_json_response(self, text: str) -> str:
        """Clean JSON response from markdown or extra text"""
        text = text.strip()
        
        # Remove markdown code blocks
        if text.startswith('```json'):
            text = text.replace('```json', '').replace('```', '').strip()
        elif text.startswith('```'):
            text = text.replace('```', '').strip()
        
        # Extract JSON array or object - be more aggressive
        # Look for the FIRST opening bracket and LAST matching closing bracket
        if '[' in text:
            start = text.find('[')
            # Find the matching closing bracket by counting
            bracket_count = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == '[':
                    bracket_count += 1
                elif text[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            
            if start != -1 and end > start:
                text = text[start:end]
        elif '{' in text:
            start = text.find('{')
            # Find the matching closing brace
            brace_count = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            if start != -1 and end > start:
                text = text[start:end]
        
        return text.strip()

    
    def _parse_response(self, response_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """Parse and validate response"""
        response_text = self._clean_json_response(response_text)
        
        data = json.loads(response_text)
        
        # Extract array from response
        if isinstance(data, dict):
            results = data.get('results') or data.get('sentiments') or list(data.values())[0]
        else:
            results = data
        
        if not isinstance(results, list):
            raise ValueError("Response is not a list")
        
        # Normalize results
        normalized = []
        for i in range(expected_count):
            if i < len(results):
                result = results[i]
                normalized.append({
                    'sentiment': result.get('s') or result.get('sentiment', 'unknown'),
                    'score': result.get('sc') or result.get('score', 0.5),
                    'reasoning': result.get('r') or result.get('reasoning', 'No reasoning')
                })
            else:
                normalized.append({
                    'sentiment': 'unknown',
                    'score': 0.5,
                    'reasoning': 'No result from API'
                })
        
        return normalized


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
