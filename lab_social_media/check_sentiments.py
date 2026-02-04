from shared.data_unifier import DataUnifier
import pandas as pd

db = DataUnifier()
user_id = '36fe43fb-1c7c-44aa-868e-4448f55ddd04'

result = pd.read_sql_query(
    'SELECT network, sentiment, COUNT(*) as count FROM posts WHERE user_id = ? GROUP BY network, sentiment', 
    db.conn, 
    params=[user_id]
)

print("\n=== Sentimientos por Red ===")
print(result.to_string())

total = pd.read_sql_query('SELECT COUNT(*) as total FROM posts WHERE user_id = ?', db.conn, params=[user_id])
print(f"\nTotal posts: {total.iloc[0]['total']}")
