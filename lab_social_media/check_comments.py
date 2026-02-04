from shared.data_unifier import DataUnifier

u = DataUnifier()
cursor = u.conn.cursor()

cursor.execute('''
    SELECT network, query, num_comments 
    FROM posts 
    WHERE user_id = ? AND network IN ('linkedin', 'facebook')
''', ('36fe43fb-1c7c-44aa-868e-4448f55ddd04',))

print('LinkedIn and Facebook posts:')
results = cursor.fetchall()
for r in results:
    print(f'  {r[0]} ({r[1]}): {r[2]} comments')
print(f'\nTotal: {len(results)} posts')
