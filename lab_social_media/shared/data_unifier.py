# -*- coding: utf-8 -*-
"""
Data Unifier - Unified Database for Social Media Analytics
Imports data from all scrapers into a centralized SQLite database
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import sys
import os

# Fix Windows encoding
# Fix Windows encoding
if sys.platform == 'win32':
    # import io
    # sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    pass


class DataUnifier:
    """
    Centralized database manager for all social media scrapers.
    Provides unified access to posts, comments, and analytics.
    """
    
    def __init__(self, db_path: str = 'data/social_media.db'):
        """
        Initialize database connection and create tables.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Create data directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        print(f"📦 Database initialized: {db_path}")
        self.create_tables()
    
    def create_tables(self):
        """Create database schema if tables don't exist"""
        cursor = self.conn.cursor()
        
        # Table: posts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id VARCHAR(255) UNIQUE NOT NULL,
                network VARCHAR(50) NOT NULL,
                author VARCHAR(255),
                text TEXT,
                url VARCHAR(500),
                created_at TIMESTAMP,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Processed data
                processed_text TEXT,
                
                -- Sentiment analysis
                sentiment VARCHAR(50),
                sentiment_score FLOAT,
                sentiment_reasoning TEXT,
                
                -- Metadata
                query VARCHAR(255),
                num_comments INTEGER DEFAULT 0,
                user_id VARCHAR(255) DEFAULT 'default'
            )
        ''')
        
        # Add user_id column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE posts ADD COLUMN user_id VARCHAR(255) DEFAULT "default"')
            self.conn.commit()
            print("✅ Added user_id column to posts table")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Table: comments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id VARCHAR(255),
                post_id VARCHAR(255) NOT NULL,
                network VARCHAR(50) NOT NULL,
                author VARCHAR(255),
                text TEXT,
                processed_text TEXT,
                created_at TIMESTAMP,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id VARCHAR(255) DEFAULT 'default',
                
                FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
            )
        ''')
        
        # Add user_id column to comments if it doesn't exist
        try:
            cursor.execute('ALTER TABLE comments ADD COLUMN user_id VARCHAR(255) DEFAULT "default"')
            self.conn.commit()
            print("✅ Added user_id column to comments table")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Table: analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                network VARCHAR(50) NOT NULL,
                query VARCHAR(255) NOT NULL,
                execution_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Execution metrics
                scraping_time FLOAT,
                processing_time FLOAT,
                sentiment_time FLOAT,
                total_time FLOAT,
                
                -- Data metrics
                posts_extracted INTEGER,
                comments_extracted INTEGER,
                items_analyzed INTEGER,
                
                -- Sentiment distribution
                positive_count INTEGER,
                negative_count INTEGER,
                neutral_count INTEGER,
                mixed_count INTEGER,
                
                -- Performance
                posts_per_second FLOAT,
                avg_time_per_post FLOAT,
                user_id VARCHAR(255) DEFAULT 'default'
            )
        ''')
        
        # Add user_id column to analytics if it doesn't exist
        try:
            cursor.execute('ALTER TABLE analytics ADD COLUMN user_id VARCHAR(255) DEFAULT "default"')
            self.conn.commit()
            print("✅ Added user_id column to analytics table")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Table: queries (track search queries)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scraped TIMESTAMP,
                total_posts INTEGER DEFAULT 0,
                total_comments INTEGER DEFAULT 0
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_network ON posts(network)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_sentiment ON posts(sentiment)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_query ON posts(query)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_network ON analytics(network)')
        
        self.conn.commit()
        print("✅ Database schema created/verified")
    
    def import_from_csv(self, network: str, sentiment_results_path: str, query: str, user_id: str = 'default'):
        """
        Import data from sentiment_results.csv into the database.
        
        Args:
            network: Network name ('x', 'instagram', 'facebook', 'linkedin')
            sentiment_results_path: Path to sentiment_results.csv
            query: Search query used for scraping
            user_id: User ID for data organization (default: 'default')
        """
        if not os.path.exists(sentiment_results_path):
            print(f"⚠️ File not found: {sentiment_results_path}")
            return
        
        print(f"\n📥 Importing {network} data from {sentiment_results_path}")
        
        try:
            df = pd.read_csv(sentiment_results_path, encoding='utf-8')
            print(f"   Found {len(df)} posts")
            
            cursor = self.conn.cursor()
            posts_imported = 0
            comments_imported = 0
            
            for _, row in df.iterrows():
                # Insert post
                try:
                    # Detectar el campo de sentimiento (puede ser 'sentiment' o 'sentiment_deepseek')
                    sentiment_field = 'sentiment_deepseek' if 'sentiment_deepseek' in row else 'sentiment'
                    explanation_field = 'explanation_deepseek' if 'explanation_deepseek' in row else 'sentiment_reasoning'
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO posts 
                        (post_id, network, author, text, url, processed_text, 
                         sentiment, sentiment_score, sentiment_reasoning, query, num_comments, user_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(row.get('post_id', f"{network}_{_}")),
                        network,
                        str(row.get('post_author', row.get('author', ''))),
                        str(row.get('post_text', row.get('content', row.get('text', '')))),
                        str(row.get('post_url', row.get('url', ''))),
                        str(row.get('post_processed', row.get('content', ''))),
                        str(row.get(sentiment_field, 'unknown')),
                        float(row.get('sentiment_score', 0.5)),
                        str(row.get(explanation_field, '')),
                        query,
                        int(row.get('num_comments', 0)),
                        user_id
                    ))
                    posts_imported += 1
                except Exception as e:
                    print(f"   ⚠️ Error importing post {row.get('post_id', _)}: {e}")
                    continue
                
                # Insert comments
                try:
                    comments_json = row.get('comments_json', '[]')
                    if isinstance(comments_json, str):
                        comments = json.loads(comments_json)
                    else:
                        comments = []
                    
                    for i, comment_text in enumerate(comments):
                        cursor.execute('''
                            INSERT INTO comments 
                            (comment_id, post_id, network, text, user_id)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            f"{row['post_id']}_comment_{i}",
                            str(row['post_id']),
                            network,
                            str(comment_text),
                            user_id
                        ))
                        comments_imported += 1
                except Exception as e:
                    print(f"   ⚠️ Error importing comments for post {row.get('post_id')}: {e}")
            
            # Update query tracking
            cursor.execute('''
                INSERT OR REPLACE INTO queries (query_text, last_scraped, total_posts, total_comments)
                VALUES (?, ?, 
                    COALESCE((SELECT total_posts FROM queries WHERE query_text = ?), 0) + ?,
                    COALESCE((SELECT total_comments FROM queries WHERE query_text = ?), 0) + ?)
            ''', (query, datetime.now(), query, posts_imported, query, comments_imported))
            
            self.conn.commit()
            print(f"   ✅ Imported {posts_imported} posts and {comments_imported} comments")
            
        except Exception as e:
            print(f"   ❌ Error importing data: {e}")
            self.conn.rollback()
    
    def import_metrics(self, network: str, metrics_path: str, user_id: str = 'default'):
        """
        Import metrics from metrics_*.json into analytics table.
        
        Args:
            network: Network name
            metrics_path: Path to metrics JSON file
            user_id: User ID for data organization (default: 'default')
        """
        if not os.path.exists(metrics_path):
            print(f"⚠️ Metrics file not found: {metrics_path}")
            return
        
        print(f"\n📊 Importing {network} metrics from {metrics_path}")
        
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
            
            cursor = self.conn.cursor()
            
            exec_times = metrics.get('execution_times', {})
            data_metrics = metrics.get('data_metrics', {})
            sentiment_dist = metrics.get('sentiment_distribution', {})
            perf_metrics = metrics.get('performance_metrics', {})
            
            cursor.execute('''
                INSERT INTO analytics 
                (network, query, scraping_time, processing_time, sentiment_time, total_time,
                 posts_extracted, comments_extracted, items_analyzed,
                 positive_count, negative_count, neutral_count, mixed_count,
                 posts_per_second, avg_time_per_post, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                network,
                metrics.get('query', ''),
                exec_times.get('scraping', 0),
                exec_times.get('text_processing', 0),
                exec_times.get('sentiment_analysis', 0),
                exec_times.get('total', 0),
                data_metrics.get('posts_extracted', 0),
                data_metrics.get('comments_extracted', 0),
                data_metrics.get('comments_analyzed', 0),
                sentiment_dist.get('positive', 0),
                sentiment_dist.get('negative', 0),
                sentiment_dist.get('neutral', 0),
                sentiment_dist.get('mixed', 0),
                perf_metrics.get('posts_per_second', 0),
                perf_metrics.get('avg_time_per_post', 0),
                user_id
            ))
            
            self.conn.commit()
            print(f"   ✅ Metrics imported successfully")
            
        except Exception as e:
            print(f"   ❌ Error importing metrics: {e}")
    
    def get_all_posts(self, user_id: Optional[str] = None,
                      network: Optional[str] = None, 
                      sentiment: Optional[str] = None, 
                      query: Optional[str] = None,
                      limit: int = 100) -> pd.DataFrame:
        """
        Get posts with optional filters.
        
        Args:
            user_id: Filter by user ID
            network: Filter by network ('x', 'instagram', etc.)
            sentiment: Filter by sentiment ('positive', 'negative', etc.)
            query: Filter by search query
            limit: Maximum number of results
        
        Returns:
            DataFrame with posts
        """
        sql = "SELECT * FROM posts WHERE 1=1"
        params = []
        
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        
        if network:
            sql += " AND network = ?"
            params.append(network)
        
        if sentiment:
            sql += " AND sentiment = ?"
            params.append(sentiment)
        
        if query:
            sql += " AND query = ?"
            params.append(query)
        
        sql += " ORDER BY scraped_at DESC LIMIT ?"
        params.append(limit)
        
        return pd.read_sql_query(sql, self.conn, params=params)
    
    def get_post_with_comments(self, post_id: str) -> Dict[str, Any]:
        """
        Get a post with all its comments.
        
        Args:
            post_id: Post ID
        
        Returns:
            Dictionary with post and comments
        """
        # Get post
        post_df = pd.read_sql_query(
            "SELECT * FROM posts WHERE post_id = ?", 
            self.conn, 
            params=[post_id]
        )
        
        if len(post_df) == 0:
            return None
        
        post = post_df.iloc[0].to_dict()
        
        # Get comments
        comments_df = pd.read_sql_query(
            "SELECT * FROM comments WHERE post_id = ? ORDER BY scraped_at",
            self.conn,
            params=[post_id]
        )
        
        post['comments'] = comments_df.to_dict('records')
        
        return post
    
    def get_sentiment_distribution(self, user_id: Optional[str] = None, network: Optional[str] = None) -> pd.DataFrame:
        """
        Get sentiment distribution across networks.
        
        Args:
            user_id: Optional user filter
            network: Optional network filter
        
        Returns:
            DataFrame with sentiment counts by network
        """
        sql = '''
            SELECT network, sentiment, COUNT(*) as count
            FROM posts
            WHERE 1=1
        '''
        params = []
        
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        
        if network:
            sql += " AND network = ?"
            params.append(network)
        
        sql += " GROUP BY network, sentiment ORDER BY network, sentiment"
        
        return pd.read_sql_query(sql, self.conn, params=params)
    
    def get_analytics_summary(self, user_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get analytics summary by network.
        
        Args:
            user_id: Optional user filter
        
        Returns:
            DataFrame with analytics summary
        """
        sql = '''
            SELECT 
                network,
                COUNT(DISTINCT query) as total_queries,
                SUM(posts_extracted) as total_posts,
                SUM(comments_extracted) as total_comments,
                AVG(total_time) as avg_time,
                SUM(positive_count) as total_positive,
                SUM(negative_count) as total_negative,
                SUM(neutral_count) as total_neutral
            FROM analytics
            WHERE 1=1
        '''
        params = []
        
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        
        sql += " GROUP BY network ORDER BY network"
        
        return pd.read_sql_query(sql, self.conn, params=params)
    
    def get_queries(self, user_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get all tracked queries.
        
        Args:
            user_id: Optional user filter
        
        Returns:
            DataFrame with queries
        """
        sql = "SELECT * FROM queries WHERE 1=1"
        params = []
        
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        
        sql += " ORDER BY last_scraped DESC"
        
        return pd.read_sql_query(sql, self.conn, params=params)
    
    def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get overall database statistics.
        
        Args:
            user_id: Optional user filter
        
        Returns:
            Dictionary with stats
        """
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Build WHERE clause
        where_clause = ""
        params = []
        if user_id:
            where_clause = " WHERE user_id = ?"
            params = [user_id]
        
        # Total posts
        cursor.execute(f"SELECT COUNT(*) FROM posts{where_clause}", params)
        stats['total_posts'] = cursor.fetchone()[0]
        
        # Total comments
        cursor.execute(f"SELECT COUNT(*) FROM comments{where_clause}", params)
        stats['total_comments'] = cursor.fetchone()[0]
        
        # Posts by network
        cursor.execute(f"SELECT network, COUNT(*) FROM posts{where_clause} GROUP BY network", params)
        stats['posts_by_network'] = dict(cursor.fetchall())
        
        # Sentiment distribution
        cursor.execute(f"SELECT sentiment, COUNT(*) FROM posts{where_clause} GROUP BY sentiment", params)
        stats['sentiment_distribution'] = dict(cursor.fetchall())
        
        # Total queries
        cursor.execute(f"SELECT COUNT(*) FROM queries{where_clause}", params)
        stats['total_queries'] = cursor.fetchone()[0]
        
        return stats
    
    def export_to_json(self, output_path: str, query: Optional[str] = None):
        """
        Export data to JSON format.
        
        Args:
            output_path: Path to output JSON file
            query: Optional query filter
        """
        print(f"\n📤 Exporting data to {output_path}")
        
        # Get posts
        posts_df = self.get_all_posts(query=query, limit=10000)
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'query': query,
            'total_posts': len(posts_df),
            'posts': []
        }
        
        for _, post_row in posts_df.iterrows():
            post_data = post_row.to_dict()
            
            # Get comments for this post
            comments_df = pd.read_sql_query(
                "SELECT * FROM comments WHERE post_id = ?",
                self.conn,
                params=[post_row['post_id']]
            )
            
            post_data['comments'] = comments_df.to_dict('records')
            export_data['posts'].append(post_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Exported {len(posts_df)} posts")
    
    def close(self):
        """Close database connection"""
        self.conn.close()
        print("📦 Database connection closed")


def main():
    """Example usage of DataUnifier"""
    print("=" * 60)
    print("Data Unifier - Social Media Analytics Database")
    print("=" * 60)
    
    # Initialize database
    unifier = DataUnifier('data/social_media.db')
    
    # Example: Import data from all scrapers
    # Note: Update paths based on your actual file locations
    
    query = "Nicolas Muñoz"
    
    # Import X/Twitter data
    x_path = "x_scrapper/output/sentiment_results.csv"
    if os.path.exists(x_path):
        unifier.import_from_csv('x', x_path, query)
        
        x_metrics = "x_scrapper/output/metrics_Nicolas Muñoz.json"
        if os.path.exists(x_metrics):
            unifier.import_metrics('x', x_metrics)
    
    # Import Instagram data
    ig_path = "App_Paralela_Instagram/Resultados/sentiment_results.csv"
    if os.path.exists(ig_path):
        unifier.import_from_csv('instagram', ig_path, query)
    
    # Import Facebook data
    fb_path = "App_Paralela_facebook/Resultados/sentiment_results.csv"
    if os.path.exists(fb_path):
        unifier.import_from_csv('facebook', fb_path, query)
    
    # Import LinkedIn data
    li_path = "linkedin_scraper/output/sentiment_results.csv"
    if os.path.exists(li_path):
        unifier.import_from_csv('linkedin', li_path, query)
        
        li_metrics = "linkedin_scraper/output/metrics_Nicolas Muñoz.json"
        if os.path.exists(li_metrics):
            unifier.import_metrics('linkedin', li_metrics)
    
    # Display statistics
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    
    stats = unifier.get_stats()
    print(f"\n📊 Total Posts: {stats['total_posts']}")
    print(f"💬 Total Comments: {stats['total_comments']}")
    print(f"🔍 Total Queries: {stats['total_queries']}")
    
    print("\n📱 Posts by Network:")
    for network, count in stats['posts_by_network'].items():
        print(f"   {network}: {count}")
    
    print("\n💭 Sentiment Distribution:")
    for sentiment, count in stats['sentiment_distribution'].items():
        print(f"   {sentiment}: {count}")
    
    # Show sentiment distribution by network
    print("\n" + "=" * 60)
    print("SENTIMENT BY NETWORK")
    print("=" * 60)
    sentiment_df = unifier.get_sentiment_distribution()
    print(sentiment_df.to_string(index=False))
    
    # Show analytics summary
    print("\n" + "=" * 60)
    print("ANALYTICS SUMMARY")
    print("=" * 60)
    analytics_df = unifier.get_analytics_summary()
    if len(analytics_df) > 0:
        print(analytics_df.to_string(index=False))
    else:
        print("No analytics data available")
    
    # Export to JSON
    unifier.export_to_json('data/export.json', query=query)
    
    unifier.close()


if __name__ == "__main__":
    main()
