from shared.data_unifier import DataUnifier

u = DataUnifier()
cursor = u.conn.cursor()

cursor.execute('''
    SELECT id, text, processed_text, LENGTH(text) as text_len
    FROM posts 
    WHERE network = 'instagram' AND query = 'iphone' 
    LIMIT 3
''')

print('Instagram posts text:')
for r in cursor.fetchall():
    post_id, text, processed, text_len = r
    print(f'\nID {post_id}:')
    print(f'  text length: {text_len}')
    print(f'  text: {text[:150] if text else "NULL"}...')
    print(f'  processed: {processed[:100] if processed else "NULL"}')
