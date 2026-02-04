from shared.data_unifier import DataUnifier

u = DataUnifier()
cursor = u.conn.cursor()

cursor.execute('''
    SELECT id, post_id, author, url, sentiment, sentiment_reasoning
    FROM posts 
    WHERE network = 'instagram' AND query = 'iphone' 
    LIMIT 1
''')

print('Instagram post full data:')
r = cursor.fetchone()
if r:
    print(f'ID: {r[0]}')
    print(f'post_id: {r[1]}')
    print(f'author: {r[2]}')
    print(f'url: {r[3]}')
    print(f'sentiment: {r[4]}')
    print(f'sentiment_reasoning: {r[5][:200] if r[5] else "NULL"}')
