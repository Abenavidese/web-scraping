# -*- coding: utf-8 -*-
"""
Database Migration Script - Add user_id field to all tables
Adds user_id column to existing database and updates all records
"""

import sqlite3
import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def migrate_database(db_path='data/social_media.db'):
    """Add user_id field to all tables"""
    
    print("=" * 70)
    print("🔄 DATABASE MIGRATION - Adding user_id field")
    print("=" * 70)
    
    if not os.path.exists(db_path):
        print(f"\n❌ Database not found: {db_path}")
        print("   Create it first by running: python import_data.py")
        return
    
    print(f"\n📦 Database: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if user_id already exists in posts table
        cursor.execute("PRAGMA table_info(posts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' in columns:
            print("\n⚠️ Migration already completed - user_id field exists")
            
            # Show current user_id distribution
            cursor.execute("SELECT user_id, COUNT(*) FROM posts GROUP BY user_id")
            results = cursor.fetchall()
            print("\n📊 Current user_id distribution:")
            for user_id, count in results:
                print(f"   • {user_id}: {count} posts")
            
            conn.close()
            return
        
        print("\n🔧 Adding user_id field to tables...")
        
        # Add user_id to posts table
        print("   1. Adding user_id to posts table...")
        cursor.execute("ALTER TABLE posts ADD COLUMN user_id VARCHAR(100) DEFAULT 'default'")
        cursor.execute("UPDATE posts SET user_id = 'default' WHERE user_id IS NULL")
        print("      ✅ Done")
        
        # Add user_id to comments table
        print("   2. Adding user_id to comments table...")
        cursor.execute("ALTER TABLE comments ADD COLUMN user_id VARCHAR(100) DEFAULT 'default'")
        cursor.execute("UPDATE comments SET user_id = 'default' WHERE user_id IS NULL")
        print("      ✅ Done")
        
        # Add user_id to analytics table
        print("   3. Adding user_id to analytics table...")
        cursor.execute("ALTER TABLE analytics ADD COLUMN user_id VARCHAR(100) DEFAULT 'default'")
        cursor.execute("UPDATE analytics SET user_id = 'default' WHERE user_id IS NULL")
        print("      ✅ Done")
        
        # Add user_id to queries table
        print("   4. Adding user_id to queries table...")
        cursor.execute("ALTER TABLE queries ADD COLUMN user_id VARCHAR(100) DEFAULT 'default'")
        cursor.execute("UPDATE queries SET user_id = 'default' WHERE user_id IS NULL")
        print("      ✅ Done")
        
        # Create indexes
        print("\n🔍 Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_user_id ON queries(user_id)")
        print("   ✅ Indexes created")
        
        # Commit changes
        conn.commit()
        
        # Verify migration
        print("\n✅ Migration completed successfully!")
        
        # Show statistics
        cursor.execute("SELECT COUNT(*) FROM posts")
        posts_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comments")
        comments_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analytics")
        analytics_count = cursor.fetchone()[0]
        
        print("\n📊 Database statistics:")
        print(f"   • Posts: {posts_count} (all assigned to 'default' user)")
        print(f"   • Comments: {comments_count} (all assigned to 'default' user)")
        print(f"   • Analytics: {analytics_count} (all assigned to 'default' user)")
        
        # Show schema
        print("\n📋 Updated schema for posts table:")
        cursor.execute("PRAGMA table_info(posts)")
        columns = cursor.fetchall()
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            print(f"   • {col_name}: {col_type}")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()
    
    print("\n" + "=" * 70)
    print("✅ MIGRATION COMPLETED")
    print("=" * 70)
    print("\n💡 Next steps:")
    print("   1. Update .env with: USER_ID=default")
    print("   2. Test API with: curl http://localhost:5000/api/stats")
    print("   3. Create new users by changing USER_ID in .env")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    migrate_database()
