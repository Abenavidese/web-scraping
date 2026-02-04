# -*- coding: utf-8 -*-
"""
REST API for Social Media Analytics
Provides endpoints to access unified social media data
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import sys
import sys
import os
import re
import json
import time
import uuid
from queue import Queue
from threading import Thread

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
        
        # Calculate global sentiment totals
        global_sentiment = {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'mixed': 0,
            'total': 0
        }
        
        for net_data in summary.values():
            global_sentiment['positive'] += net_data['positive']
            global_sentiment['negative'] += net_data['negative']
            global_sentiment['neutral'] += net_data['neutral']
            global_sentiment['mixed'] += net_data['mixed']
            global_sentiment['total'] += net_data['total']
        
        return jsonify({
            'success': True,
            'distribution': distribution,
            'summary': summary,
            'global': global_sentiment
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
                    sentiment_csv_query = os.path.join(data_dir, f'sentiment_results_{slug}.csv')
                    metrics_json = os.path.join(data_dir, 'metrics.json')
                    
                    # Import
                    if os.path.exists(sentiment_csv):
                         unifier.import_from_csv(network, sentiment_csv, query, user_id)
                    elif os.path.exists(sentiment_csv_query):
                         unifier.import_from_csv(network, sentiment_csv_query, query, user_id)
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


# Global storage for active scraping sessions
active_sessions = {}

@app.route('/api/scrape/stream', methods=['POST'])
def run_scrapers_stream():
    """
    Execute scrapers with real-time progress streaming via SSE
    
    Request Body: Same as /api/scrape
    
    Returns: Server-Sent Events stream with progress updates
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        networks = data.get('networks', [])
        query = data.get('query')
        
        if not networks or not query:
            return jsonify({'success': False, 'error': 'networks and query are required'}), 400
        
        num_posts = data.get('num_posts', 10)
        num_comments = data.get('num_comments', 5)
        user_id = data.get('user_id', 'default')
        limits = data.get('limits', {})
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create event queue for this session
        event_queue = Queue()
        active_sessions[session_id] = {'queue': event_queue, 'done': False}
        
        # Start scraping in background thread
        def run_scraping():
            from scraper_manager import ScraperManager
            from progress_tracker import progress_tracker
            
            try:
                # Emit start event
                event_queue.put({'type': 'start', 'session_id': session_id, 'query': query, 'networks': networks})
                
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                manager = ScraperManager(base_dir)
                
                # Subscribe to progress
                def on_progress(event):
                    event_queue.put(event)
                
                progress_tracker.subscribe(session_id, on_progress)
                
                # Run scrapers
                result = manager.run_scrapers(
                    networks=networks,
                    query=query,
                    num_posts=num_posts,
                    num_comments=num_comments,
                    user_id=user_id,
                    limits=limits,
                    session_id=session_id
                )
                
                # Auto-import
                if result['success']:
                    slug = re.sub(r'[^\w\s-]', '', query).strip().replace(' ', '_').lower()
                    users_dir = os.path.join(base_dir, 'users')
                    
                    for scraper_res in result.get('results', []):
                        if scraper_res.get('status') == 'success':
                            network = scraper_res['network']
                            event_queue.put({'type': 'import_start', 'network': network})
                            
                            data_dir = os.path.join(users_dir, user_id, network, slug)
                            sentiment_csv = os.path.join(data_dir, 'sentiment_results.csv')
                            sentiment_csv_alt = os.path.join(data_dir, 'datos_extraidos_deepseek.csv')
                            sentiment_csv_query = os.path.join(data_dir, f'sentiment_results_{slug}.csv')
                            metrics_json = os.path.join(data_dir, 'metrics.json')
                            
                            if os.path.exists(sentiment_csv):
                                unifier.import_from_csv(network, sentiment_csv, query, user_id)
                            elif os.path.exists(sentiment_csv_query):
                                unifier.import_from_csv(network, sentiment_csv_query, query, user_id)
                            elif os.path.exists(sentiment_csv_alt):
                                unifier.import_from_csv(network, sentiment_csv_alt, query, user_id)
                            
                            if os.path.exists(metrics_json):
                                unifier.import_metrics(network, metrics_json, user_id)
                            
                            event_queue.put({'type': 'import_done', 'network': network})
                
                event_queue.put({'type': 'complete', 'result': result})
                
            except Exception as e:
                event_queue.put({'type': 'error', 'error': str(e)})
            finally:
                active_sessions[session_id]['done'] = True
                progress_tracker.clear_session(session_id)
        
        thread = Thread(target=run_scraping, daemon=True)
        thread.start()
        
        # Return session ID for client to connect to SSE stream
        return jsonify({'success': True, 'session_id': session_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scrape/events/<session_id>')
def scrape_events(session_id):
    """
    SSE endpoint for real-time scraping progress
    """
    def event_stream():
        if session_id not in active_sessions:
            yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid session'})}\n\n"
            return
        
        session = active_sessions[session_id]
        event_queue = session['queue']
        
        try:
            while not session['done'] or not event_queue.empty():
                try:
                    # Wait for event with timeout
                    event = event_queue.get(timeout=1)
                    yield f"data: {json.dumps(event)}\n\n"
                except:
                    # Timeout, send heartbeat
                    yield f": heartbeat\n\n"
                    
        finally:
            # Clean up
            if session_id in active_sessions:
                del active_sessions[session_id]
    
    return Response(event_stream(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get global statistics for a user.
    
    Query params:
        user_id: User ID to get stats for
    
    Returns:
        {
            "total_posts": int,
            "total_comments": int,
            "total_words": int,
            "networks_used": [str]
        }
    """
    user_id = request.args.get('user_id', 'default')
    
    try:
        cursor = unifier.conn.cursor()
        
        # Get total posts
        cursor.execute("""
            SELECT COUNT(*) FROM posts WHERE user_id = ?
        """, (user_id,))
        total_posts = cursor.fetchone()[0]
        
        # Get total comments
        cursor.execute("""
            SELECT COUNT(*) FROM comments WHERE user_id = ?
        """, (user_id,))
        total_comments = cursor.fetchone()[0]
        
        # Get total words (approximate from text length)
        cursor.execute("""
            SELECT SUM(LENGTH(text) - LENGTH(REPLACE(text, ' ', '')) + 1) 
            FROM posts WHERE user_id = ? AND text IS NOT NULL
        """, (user_id,))
        result = cursor.fetchone()[0]
        total_words = result if result else 0
        
        # Get networks used
        cursor.execute("""
            SELECT DISTINCT network FROM posts WHERE user_id = ?
        """, (user_id,))
        networks_used = [row[0] for row in cursor.fetchall()]
        
        return jsonify({
            "total_posts": total_posts,
            "total_comments": total_comments,
            "total_words": total_words,
            "networks_used": networks_used
        })
    
    except Exception as e:
        app.logger.error(f"Error in /api/stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/latest-results', methods=['GET'])
def get_latest_results():
    """
    Get results from the most recent scraping session (same query, all networks).
    
    Query params:
        user_id: User ID to get results for
    
    Returns:
        {
            "query": str,
            "session_date": str,
            "posts": [{...}],
            "stats": {...}
        }
    """
    user_id = request.args.get('user_id', 'default')
    
    try:
        cursor = unifier.conn.cursor()
        
        # Get the most recent query based on scraped_at
        cursor.execute("""
            SELECT query, MAX(scraped_at) as latest
            FROM posts
            WHERE user_id = ? AND query IS NOT NULL
            GROUP BY query
            ORDER BY latest DESC
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result or not result[0]:
            return jsonify({"query": None, "session_date": None, "posts": [], "stats": {}})
        
        latest_query = result[0]
        latest_scraped = result[1]
        
        # Get all posts for this query across all networks
        cursor.execute("""
            SELECT id, post_id, network, author, text, url, created_at, 
                   scraped_at, processed_text, sentiment, sentiment_score, 
                   sentiment_reasoning, query, num_comments, user_id
            FROM posts
            WHERE user_id = ? AND query = ?
        """, (user_id, latest_query))
        
        posts = []
        for row in cursor.fetchall():
            posts.append({
                "id": row[0],
                "post_id": row[1],
                "network": row[2],
                "author": row[3],
                "text": row[4],
                "url": row[5],
                "created_at": row[6],
                "scraped_at": row[7],
                "processed_text": row[8],
                "sentiment": row[9],
                "sentiment_score": row[10],
                "sentiment_reasoning": row[11],
                "query": row[12],
                "num_comments": row[13],
                "user_id": row[14]
            })
        
        # Calculate stats
        stats = {
            "total_posts": len(posts),
            "total_comments": sum(int(p["num_comments"] or 0) for p in posts),
            "networks": list(set(p["network"] for p in posts)),
            "by_network": {}
        }
        
        # Stats by network
        for post in posts:
            net = post["network"]
            if net not in stats["by_network"]:
                stats["by_network"][net] = {"posts": 0, "comments": 0}
            stats["by_network"][net]["posts"] += 1
            stats["by_network"][net]["comments"] += int(post["num_comments"] or 0)
        
        return jsonify({
            "query": latest_query,
            "session_date": latest_scraped,
            "posts": posts,
            "stats": stats
        })
    
    except Exception as e:
        app.logger.error(f"Error in /api/latest-results: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/queries', methods=['GET'])
def get_queries():
    """
    Get query history for a user.
    
    Query params:
        user_id: User ID to get queries for
    
    Returns:
        {
            "queries": [
                {
                    "id": int,
                    "query_text": str,
                    "network": str,
                    "created_at": str,
                    "status": str
                }
            ]
        }
    """
    user_id = request.args.get('user_id', 'default')
    
    try:
        cursor = unifier.conn.cursor()
        
        # Get unique queries from posts
        cursor.execute("""
            SELECT 
                ROW_NUMBER() OVER (ORDER BY MIN(COALESCE(created_at, datetime('now'))) DESC) as id,
                query,
                network,
                COALESCE(MIN(created_at), datetime('now')) as created_at,
                'completed' as status
            FROM posts 
            WHERE user_id = ? AND query IS NOT NULL
            GROUP BY query, network
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
        
        queries = []
        for row in cursor.fetchall():
            queries.append({
                "id": row[0],
                "query_text": row[1],
                "network": row[2],
                "created_at": row[3],
                "status": row[4]
            })
        
        return jsonify({"queries": queries})
    
    except Exception as e:
        app.logger.error(f"Error in /api/queries: {e}")
        return jsonify({"error": str(e), "queries": []}), 500


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


@app.route('/api/download-csv', methods=['POST'])
def download_csv():
    """
    Generate and download cleaned CSV based on user's latest data.
    
    Request:
    {
        "user_id": "uuid",
        "cleaning_level": "basico|normal|agresivo",
        "network": "all|instagram|x|facebook|linkedin"  # optional, default: all
    }
    
    Response:
    CSV file download
    """
    try:
        from flask import send_file
        from shared.data_cleaner import DataCleaner
        import io
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = data.get('user_id', 'default')
        cleaning_level = data.get('cleaning_level', 'normal')
        network_filter = data.get('network', 'all')
        
        # Validate cleaning level
        if cleaning_level not in ['basico', 'normal', 'agresivo']:
            return jsonify({'error': 'Invalid cleaning level. Use: basico, normal, or agresivo'}), 400
        
        # Get data from database
        query = """
            SELECT 
                p.network,
                p.post_id,
                p.url,
                p.text as post_content,
                p.sentiment,
                p.sentiment_score,
                p.created_at as timestamp,
                COUNT(c.id) as comments_count
            FROM posts p
            LEFT JOIN comments c ON p.id = c.post_id
            WHERE p.user_id = ?
        """
        
        params = [user_id]
        
        if network_filter != 'all':
            query += " AND p.network = ?"
            params.append(network_filter)
        
        query += " GROUP BY p.id ORDER BY p.created_at DESC"
        
        df = pd.read_sql_query(query, unifier.conn, params=params)
        
        if df.empty:
            return jsonify({'error': 'No data found for this user'}), 404
        
        # Apply cleaning
        cleaner = DataCleaner()
        df_cleaned = cleaner.process_dataframe(
            df, 
            level=cleaning_level,
            text_columns=['post_content']
        )
        
        # Create CSV in memory
        output = io.StringIO()
        df_cleaned.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        # Convert to bytes for download
        csv_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
        csv_bytes.seek(0)
        
        # Generate filename
        filename = f"datos_{cleaning_level}_{user_id[:8]}.csv"
        
        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Download CSV Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


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
