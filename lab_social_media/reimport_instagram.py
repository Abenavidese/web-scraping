from shared.data_unifier import DataUnifier

u = DataUnifier()
cursor = u.conn.cursor()

# Delete Instagram posts
cursor.execute("DELETE FROM posts WHERE network = 'instagram' AND query = 'iphone'")
cursor.execute("DELETE FROM comments WHERE network = 'instagram'")
u.conn.commit()
print('Deleted Instagram posts')

# Reimport
csv_path = 'users/36fe43fb-1c7c-44aa-868e-4448f55ddd04/instagram/iphone/sentiment_results_iphone.csv'
u.import_from_csv('instagram', csv_path, 'iphone', '36fe43fb-1c7c-44aa-868e-4448f55ddd04')
print('Reimported Instagram data')

# Verify
cursor.execute("SELECT id, text, LENGTH(text) FROM posts WHERE network = 'instagram' LIMIT 1")
r = cursor.fetchone()
if r:
    print(f'\nVerify - Post ID {r[0]}: text_len={r[2]}, text={r[1][:100]}...')
