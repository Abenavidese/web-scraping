import pandas as pd
import nltk
import re
import string
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize
import concurrent.futures

# Ensure NLTK resources are available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def clean_text(text):
    """
    Cleans text: lowercase, remove URLs, punctuation, numbers, emojis.
    """
    # Lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # Remove user @ references and '#' from hashtags
    text = re.sub(r'\@\w+|\#', '', text)
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    # Remove emojis (simplistic regex) matches any non-ascii char (can include accents though)
    # Better to keep accents for spanish if needed, so strict emoji removal:
    # We'll assume non-ascii removal for now unless spanish text requires it. 
    # Let's use a simpler approach: remove non-alphanumeric + spaces
    # text = re.sub(r'[^\w\s]', '', text) 
    return text.strip()

def process_tweet(tweet_text):
    """
    Full pipeline for a single tweet text.
    Returns list of processed tokens.
    """
    # 1. Cleaning
    clean = clean_text(tweet_text)
    
    # 2. Tokenization
    try:
        tokens = word_tokenize(clean, language='spanish')
    except:
        tokens = clean.split()

    # 3. Stopword Removal
    stop_words = set(stopwords.words('spanish')) # Assuming content might be Spanish based on Lab Guide
    tokens = [w for w in tokens if w not in stop_words and len(w) > 2]

    # 4. Stemming
    stemmer = SnowballStemmer('spanish')
    stems = [stemmer.stem(w) for w in tokens]

    return stems

def process_data_parallel(tweets_list):
    """
    Processes a list of tweet dictionaries in parallel.
    Expected input: [{'text': '...', ...}, ...]
    Returns pandas DataFrame with original and processed data.
    """
    texts = [t['text'] for t in tweets_list]

    # Parallel processing using ProcessPoolExecutor
    with concurrent.futures.ProcessPoolExecutor() as executor:
        processed_results = list(executor.map(process_tweet, texts))

    # Combine back into simple structure
    df = pd.DataFrame(tweets_list)
    df['processed_tokens'] = processed_results
    df['processed_text'] = df['processed_tokens'].apply(lambda x: ' '.join(x))
    
    return df
