from shared.data_unifier import DataUnifier

u = DataUnifier()
cursor = u.conn.cursor()

# Check comments table for linkedin and facebook
cursor.execute('''
    SELECT network, COUNT(*) 
    FROM comments 
    WHERE user_id = ? 
    GROUP BY network
''', ('36fe43fb-1c7c-44aa-868e-4448f55ddd04',))

print('Comments by network in comments table:')
for r in cursor.fetchall():
    print(f'  {r[0]}: {r[1]} comments')

# Check specific query
cursor.execute('''
    SELECT c.network, c.post_id, COUNT(*) as cnt
    FROM comments c
    JOIN posts p ON c.post_id = p.id
    WHERE c.user_id = ? AND c.network IN ('linkedin', 'facebook')
    GROUP BY c.network, c.post_id
    LIMIT 10
''', ('36fe43fb-1c7c-44aa-868e-4448f55ddd04',))

print('\nComments per post (linkedin/facebook):')
for r in cursor.fetchall():
    print(f'  {r[0]} post_id={r[1]}: {r[2]} comments')
