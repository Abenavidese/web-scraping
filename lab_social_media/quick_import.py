from shared.data_unifier import DataUnifier
import os

user_id = '36fe43fb-1c7c-44aa-868e-4448f55ddd04'
query = 'iphone'
query_slug = 'iphone'

db = DataUnifier()

print(f"\n🔐 Importing for user: {user_id}")
print(f"🔍 Query: {query}\n")

# X
x_sentiment = f"users/{user_id}/x/{query_slug}/sentiment_results.csv"
if os.path.exists(x_sentiment):
    db.import_from_csv('x', x_sentiment, query, user_id)
    print(f"✅ X imported")
else:
    print(f"❌ X not found: {x_sentiment}")

# Instagram
ig_sentiment = f"users/{user_id}/instagram/{query_slug}/sentiment_results_{query_slug}.csv"
if os.path.exists(ig_sentiment):
    db.import_from_csv('instagram', ig_sentiment, query, user_id)
    print(f"✅ Instagram imported")
else:
    print(f"❌ Instagram not found: {ig_sentiment}")

# Facebook - tiene formato especial
fb_sentiment = f"users/{user_id}/facebook/{query_slug}/sentiment_results_{query_slug}.csv"
if not os.path.exists(fb_sentiment):
    fb_sentiment = f"users/{user_id}/facebook/{query_slug}/processed_facebook_{query_slug}.csv"
if os.path.exists(fb_sentiment):
    db.import_from_csv('facebook', fb_sentiment, query, user_id)
    print(f"✅ Facebook imported")
else:
    print(f"❌ Facebook not found")

# LinkedIn
li_sentiment = f"users/{user_id}/linkedin/{query_slug}/datos_extraidos_deepseek.csv"
if os.path.exists(li_sentiment):
    db.import_from_csv('linkedin', li_sentiment, query, user_id)
    print(f"✅ LinkedIn imported")
else:
    print(f"❌ LinkedIn not found: {li_sentiment}")

print("\n" + "="*50)
print("Checking results...")
import pandas as pd
result = pd.read_sql_query(
    'SELECT network, sentiment, COUNT(*) as count FROM posts WHERE user_id = ? GROUP BY network, sentiment', 
    db.conn, 
    params=[user_id]
)
print(result.to_string())
