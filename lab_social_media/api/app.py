# -*- coding: utf-8 -*-
"""
REST API for Social Media Analytics
Provides endpoints to access unified social media data
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.data_unifier import DataUnifier
from shared.chat_manager import ChatManager

# Fix Windows encoding
# Fix Windows encoding
if sys.platform == 'win32':
    # import io
    # sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    pass

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize database
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'social_media.db')
unifier = DataUnifier(DB_PATH)
chat_manager = ChatManager()

def slugify(text):
    """Convert text to slug format for directory names"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """API root endpoint"""
    return jsonify({
        'name': 'Social Media Analytics API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/posts': 'Get posts with optional filters',
            'GET /api/posts/<post_id>': 'Get specific post with comments',
            'GET /api/sentiments': 'Get sentiment distribution',
            'GET /api/analytics': 'Get analytics summary',
            'GET /api/queries': 'Get all tracked queries',
            'GET /api/stats': 'Get database statistics',
            'GET /api/networks': 'Get available networks',
            'POST /api/scrape': 'Execute scrapers in parallel (multiprocessing)'
        }
    })


@app.route('/api/posts', methods=['GET'])
def get_posts():
    """
    Get posts with optional filters.
    
    Query Parameters:
        - network: Filter by network (x, instagram, facebook, linkedin)
        - sentiment: Filter by sentiment (positive, negative, neutral, mixed)
        - query: Filter by search query
        - limit: Maximum number of results (default: 100)
    
    Example:
        GET /api/posts?network=x&sentiment=positive&limit=50
    """
    try:
        user_id = request.args.get('user_id')
        network = request.args.get('network')
        sentiment = request.args.get('sentiment')
        query = request.args.get('query')
        limit = int(request.args.get('limit', 100))
        
        # Validate limit
        if limit > 1000:
            limit = 1000
        
        df = unifier.get_all_posts(user_id, network, sentiment, query, limit)
        
        # Convert to list of dicts
        posts = df.to_dict('records')
        
        # Convert NaN to None for JSON serialization
        for post in posts:
            for key, value in post.items():
                if pd.isna(value):
                    post[key] = None
        
        return jsonify({
            'success': True,
            'total': len(posts),
            'filters': {
                'user_id': user_id,
                'network': network,
                'sentiment': sentiment,
                'query': query,
                'limit': limit
            },
            'posts': posts
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    """
    Get a specific post with all its comments.
    
    Example:
        GET /api/posts/2016216029999874296
    """
    try:
        post = unifier.get_post_with_comments(post_id)
        
        if post is None:
            return jsonify({
                'success': False,
                'error': 'Post not found'
            }), 404
        
        # Convert NaN to None
        import pandas as pd
        for key, value in post.items():
            if isinstance(value, float) and pd.isna(value):
                post[key] = None
        
        return jsonify({
            'success': True,
            'post': post
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sentiments', methods=['GET'])
def get_sentiments():
    """
    Get sentiment distribution across networks.
    
    Query Parameters:
        - network: Optional network filter
    
    Example:
        GET /api/sentiments?network=instagram
    """
    try:
        user_id = request.args.get('user_id')
        network = request.args.get('network')
        
        df = unifier.get_sentiment_distribution(user_id, network)
        
        # Convert to list of dicts
        distribution = df.to_dict('records')
        
        # Also provide summary by network
        summary = {}
        for item in distribution:
            net = item['network']
            if net not in summary:
                summary[net] = {
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'mixed': 0,
                    'total': 0
                }
            
            sentiment = item['sentiment'].lower()  # Normalize to lowercase
            count = item['count']
            
            # Map sentiment variations to standard keys
            sentiment_mapping = {
                'positivo': 'positive',
                'positive': 'positive',
                'negativo': 'negative',
                'negative': 'negative',
                'neutro': 'neutral',
                'neutral': 'neutral',
                'mixed': 'mixed',
                'mixto': 'mixed',
                'unknown': None  # Ignore unknown sentiments
            }
            
            mapped_sentiment = sentiment_mapping.get(sentiment)
            if mapped_sentiment and mapped_sentiment in summary[net]:
                summary[net][mapped_sentiment] += count
            summary[net]['total'] += count
        
        return jsonify({
            'success': True,
            'distribution': distribution,
            'summary': summary
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """
    Get analytics summary by network.
    
    Example:
        GET /api/analytics
    """
    try:
        user_id = request.args.get('user_id')
        df = unifier.get_analytics_summary(user_id)
        
        # Convert to list of dicts
        analytics = df.to_dict('records')
        
        # Convert NaN to None
        import pandas as pd
        for item in analytics:
            for key, value in item.items():
                if isinstance(value, float) and pd.isna(value):
                    item[key] = None
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/queries', methods=['GET'])
def get_queries():
    """
    Get all tracked search queries.
    
    Example:
        GET /api/queries
    """
    try:
        user_id = request.args.get('user_id')
        df = unifier.get_queries(user_id)
        
        queries = df.to_dict('records')
        
        return jsonify({
            'success': True,
            'queries': queries
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get overall database statistics.
    
    Example:
        GET /api/stats
    """
    try:
        user_id = request.args.get('user_id')
        stats = unifier.get_stats(user_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/networks', methods=['GET'])
def get_networks():
    """
    Get list of available social networks.
    
    Example:
        GET /api/networks
    """
    return jsonify({
        'success': True,
        'networks': [
            {
                'id': 'x',
                'name': 'X (Twitter)',
                'icon': '𝕏'
            },
            {
                'id': 'instagram',
                'name': 'Instagram',
                'icon': '📷'
            },
            {
                'id': 'facebook',
                'name': 'Facebook',
                'icon': '👥'
            },
            {
                'id': 'linkedin',
                'name': 'LinkedIn',
                'icon': '💼'
            }
        ]
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

# ============================================================================
# SCRAPER EXECUTION ENDPOINT
# ============================================================================

@app.route('/api/scrape', methods=['POST'])
def run_scrapers():
    """
    Execute selected scrapers in parallel
    
    Request Body (JSON):
        {
            "networks": ["x", "instagram", "facebook", "linkedin"],
            "query": "Search topic",
            "num_posts": 10,
            "num_comments": 5
        }
    
    Example:
        POST /api/scrape
        {
            "networks": ["x", "facebook"],
            "query": "AI Technology",
            "num_posts": 5,
            "num_comments": 3
        }
    
    Returns:
        {
            "success": true,
            "query": "AI Technology",
            "networks_requested": ["x", "facebook"],
            "networks_completed": 2,
            "successful": 2,
            "failed": 0,
            "total_execution_time": 45.3,
            "results": [...]
        }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        networks = data.get('networks', [])
        query = data.get('query')
        
        if not networks:
            return jsonify({
                'success': False,
                'error': 'No networks specified',
                'valid_networks': ['x', 'instagram', 'facebook', 'linkedin']
            }), 400
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        # Get optional parameters
        num_posts = data.get('num_posts', 10)
        num_comments = data.get('num_comments', 5)
        user_id = data.get('user_id', 'default')
        limits = data.get('limits', {})
        
        # Validate types
        if not isinstance(networks, list):
            return jsonify({
                'success': False,
                'error': 'networks must be a list'
            }), 400
        
        if not isinstance(num_posts, int) or num_posts < 1:
            return jsonify({
                'success': False,
                'error': 'num_posts must be a positive integer'
            }), 400
        
        if not isinstance(num_comments, int) or num_comments < 0:
            return jsonify({
                'success': False,
                'error': 'num_comments must be a non-negative integer'
            }), 400
        
        # Import scraper manager
        from scraper_manager import ScraperManager
        
        # Initialize manager
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        manager = ScraperManager(base_dir)
        
        # Run scrapers
        result = manager.run_scrapers(
            networks=networks,
            query=query,
            num_posts=num_posts,
            num_comments=num_comments,

            user_id=user_id,
            limits=limits
        )
        

        
        # Auto-import data into database
        if result['success']:
            slug = slugify(query)
            users_dir = os.path.join(base_dir, 'users')
            
            for scraper_res in result.get('results', []):
                if scraper_res.get('status') == 'success':
                    network = scraper_res['network']
                    print(f"📥 Importing data for {network}...", flush=True)
                    
                    # Construct paths
                    # Path: users/{user_id}/{network}/{slug}/
                    data_dir = os.path.join(users_dir, user_id, network, slug)
                    
                    sentiment_csv = os.path.join(data_dir, 'sentiment_results.csv')
                    sentiment_csv_alt = os.path.join(data_dir, 'datos_extraidos_deepseek.csv')
                    metrics_json = os.path.join(data_dir, 'metrics.json')
                    
                    # Import
                    if os.path.exists(sentiment_csv):
                         unifier.import_from_csv(network, sentiment_csv, query, user_id)
                    elif os.path.exists(sentiment_csv_alt):
                         unifier.import_from_csv(network, sentiment_csv_alt, query, user_id)
                    
                    if os.path.exists(metrics_json):
                         unifier.import_metrics(network, metrics_json, user_id)

        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


@app.route('/api/chat-with-data', methods=['POST'])
def chat_with_data():
    """Endpoint for chatting with the latest extracted data."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        user_id = data.get('user_id')
        message = data.get('message')
        
        if not user_id or not message:
            return jsonify({'error': 'Missing user_id or message'}), 400
            
        result = chat_manager.chat(user_id, message)
        
        if "error" in result:
             return jsonify({'error': result['error']}), 500
             
        return jsonify(result)
        
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import pandas as pd  # Import here to avoid circular import
    
    print("=" * 60)
    print("🚀 Social Media Analytics API")
    print("=" * 60)
    print(f"📦 Database: {DB_PATH}")
    print(f"🌐 Server: http://localhost:5000")
    print("=" * 60)
    print("\nAvailable endpoints:")
    print("  GET /api/posts")
    print("  GET /api/posts/<post_id>")
    print("  GET /api/sentiments")
    print("  GET /api/analytics")
    print("  GET /api/queries")
    print("  GET /api/stats")
    print("  GET /api/networks")
    print("\n" + "=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
