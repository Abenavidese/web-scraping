import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd
from collections import Counter

def generate_wordcloud(text_corpus, output_path='wordcloud.png'):
    """Generates and saves a word cloud from the text corpus."""
    if not text_corpus:
        print("No text data for word cloud.")
        return

    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text_corpus)
    
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title("Nube de Palabras (Word Cloud)")
    plt.savefig(output_path)
    print(f"Word cloud saved to {output_path}")
    plt.close()

def plot_top_words(tokens_series, n=20, output_path='top_words.png'):
    """Plots top N most frequent words."""
    all_words = [word for tokens in tokens_series for word in tokens]
    count = Counter(all_words)
    common_words = count.most_common(n)
    
    if not common_words:
        print("No words to plot.")
        return

    words = [x[0] for x in common_words]
    counts = [x[1] for x in common_words]

    plt.figure(figsize=(12, 6))
    plt.bar(words, counts, color='skyblue')
    plt.xlabel('Palabras')
    plt.ylabel('Frecuencia')
    plt.title(f'Top {n} Palabras Más Frecuentes')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Top words plot saved to {output_path}")
    plt.close()
