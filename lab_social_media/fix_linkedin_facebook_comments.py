"""
Script para actualizar num_comments en posts de LinkedIn y Facebook
extrayendo el conteo desde el JSON de comments
"""
from shared.data_unifier import DataUnifier
import json

u = DataUnifier()
cursor = u.conn.cursor()

# Get LinkedIn and Facebook posts with comments column
cursor.execute('''
    SELECT id, network, query, text 
    FROM posts 
    WHERE user_id = ? AND network IN ('linkedin', 'facebook')
''', ('36fe43fb-1c7c-44aa-868e-4448f55ddd04',))

posts_to_update = []
for post_id, network, query, text_field in cursor.fetchall():
    # The comments are stored in the 'text' field as JSON for linkedin/facebook
    # Actually, let me check the actual structure
    pass

# Let me check one post to see the structure
cursor.execute('''
    SELECT id, network, text, url
    FROM posts 
    WHERE network = 'linkedin' 
    LIMIT 1
''')

post = cursor.fetchone()
if post:
    print(f"LinkedIn post sample:")
    print(f"  ID: {post[0]}")
    print(f"  Network: {post[1]}")
    print(f"  Text length: {len(post[2]) if post[2] else 0}")
    print(f"  URL: {post[3]}")
    print()

# Check if there's a comments column
cursor.execute("PRAGMA table_info(posts)")
columns = [col[1] for col in cursor.fetchall()]
print("Posts table columns:", columns)
