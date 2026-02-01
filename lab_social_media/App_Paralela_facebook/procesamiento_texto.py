import json
import os
import re
import nltk
import matplotlib.pyplot as plt
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize

# Descargar recursos necesarios de NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Descargando 'punkt'...")
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Descargando 'stopwords'...")
    nltk.download('stopwords')

def cargar_datos_json(ruta_archivo):
    """Carga los datos desde un archivo JSON."""
    if not os.path.exists(ruta_archivo):
        print(f"Error: El archivo {ruta_archivo} no existe.")
        return []
    
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            return data
        except json.JSONDecodeError:
            print(f"Error: No se pudo decodificar el archivo {ruta_archivo}.")
            return []

def limpiar_texto(texto):
    """
    Realiza la limpieza y normalización del texto:
    - Convertir a minúsculas
    - Remover URLs
    - Remover menciones (@usuario) y hashtags (#)
    - Remover caracteres especiales, números y puntuación
    - Remover espacios extra
    """
    if not texto:
        return ""
    
    # 1. Convertir a minúsculas
    texto = texto.lower()
    
    # 2. Remover URLs
    texto = re.sub(r'http\S+|www\S+|https\S+', '', texto, flags=re.MULTILINE)
    
    # 3. Remover menciones (@) y hashtags (#) - Opcional: a veces los hashtags tienen info útil
    # Aquí removemos el símbolo pero dejamos el texto del hashtag si se desea, 
    # o removemos todo el token. Por ahora removemos todo el token que empiece con @
    texto = re.sub(r'@\w+', '', texto)
    # Removemos hashtags #
    texto = re.sub(r'#\w+', '', texto)
    
    # 4. Remover caracteres especiales, números y puntuación (dejamos solo letras y espacios)
    # \w incluye numeros, asi que usamos [^a-zA-ZáéíóúñÁÉÍÓÚÑ]
    texto = re.sub(r'[^a-záéíóúñ\s]', '', texto)
    
    # 5. Remover espacios extra
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto

def procesar_texto(data):
    """
    Procesa la lista de posts extraídos.
    Retorna una lista de tokens limpios y procesados de todo el corpus.
    """
    corpus_completo = ""
    
    print("Iniciando procesamiento de texto...")
    
    for post in data:
        # Concatenar caption
        caption = post.get('caption_snippet', '')
        if caption:
            corpus_completo += " " + caption
            
        # Concatenar comentarios
        comentarios = post.get('comments', [])
        for comentario in comentarios:
            texto_comentario = comentario.get('text', '')
            if texto_comentario:
                corpus_completo += " " + texto_comentario
    
    # 1. Limpieza
    texto_limpio = limpiar_texto(corpus_completo)
    
    # 2. Tokenización
    tokens = word_tokenize(texto_limpio, language='spanish')
    
    # 3. Remover Stopwords (Español e Inglés porque hay mezcla)
    stop_words = set(stopwords.words('spanish') + stopwords.words('english'))
    # Agregamos algunas custom si es necesario
    stop_words.update(['si', 'video', 'photo', 'shared', 'may', 'be', 'image', 'text', 'tagging', 'by']) 
    
    tokens_filtrados = [word for word in tokens if word not in stop_words and len(word) > 2]
    
    # 4. Stemming (Usaremos SnowballStemmer para español)
    stemmer = SnowballStemmer('spanish')
    tokens_stemmed = [stemmer.stem(word) for word in tokens_filtrados]
    
    # Retornamos tokens_filtrados para visualización (más legible) y tokens_stemmed para análisis
    return tokens_filtrados, tokens_stemmed

def visualizar_nube_palabras(tokens, nombre_archivo="reporte_palabras.png"):
    """
    Genera un gráfico de barras con las palabras más frecuentes.
    """
    conteo = Counter(tokens)
    top_20 = conteo.most_common(20)
    
    if not top_20:
        print("No hay suficientes datos para graficar.")
        return

    palabras = [x[0] for x in top_20]
    frecuencias = [x[1] for x in top_20]
    
    plt.figure(figsize=(12, 6))
    plt.bar(palabras, frecuencias, color='skyblue')
    plt.xlabel('Palabras')
    plt.ylabel('Frecuencia')
    plt.title('Top 20 Palabras Más Frecuentes (Instagram)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    plt.savefig(nombre_archivo)
    print(f"Gráfico guardado como: {nombre_archivo}")
    # plt.show() # Descomentar si se ejecuta en entorno con GUI

def main():
    # Buscar archivos JSON en el directorio actual
    archivos = [f for f in os.listdir('.') if f.startswith('results_') and f.endswith('.json')]
    
    if not archivos:
        print("No se encontraron archivos 'results_*.json'. Ejecuta primero el scraper.")
        return
    
    print(f"Archivos encontrados: {archivos}")
    
    todos_los_datos = []
    for archivo in archivos:
        print(f"Cargando {archivo}...")
        datos = cargar_datos_json(archivo)
        todos_los_datos.extend(datos)
        
    print(f"Total de posts a procesar: {len(todos_los_datos)}")
    
    # Procesar
    tokens_limpios, tokens_stemmed = procesar_texto(todos_los_datos)
    
    print(f"Total de tokens extraídos: {len(tokens_limpios)}")
    print(f"Ejemplo de tokens limpios: {tokens_limpios[:10]}")
    print(f"Ejemplo de tokens stemming: {tokens_stemmed[:10]}")
    
    # Visualizar
    visualizar_nube_palabras(tokens_limpios, "frecuencia_palabras_instagram.png")
    
    print("\n--- Proceso Completo ---")
    print("1. Limpieza y Normalización: OK")
    print("2. Tokenización: OK")
    print("3. Stopwords: OK")
    print("4. Stemming: OK")
    print("5. Visualización: OK (Gráfico generado)")

if __name__ == "__main__":
    main()
