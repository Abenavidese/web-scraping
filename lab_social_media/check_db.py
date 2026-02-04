import sqlite3
import os

db_path = 'data/social_media.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM posts")
        count = cursor.fetchone()[0]
        print(f"Total posts in DB: {count}")
        conn.close()
    except Exception as e:
        print(f"Error reading DB: {e}")
else:
    print("DB file does not exist")
