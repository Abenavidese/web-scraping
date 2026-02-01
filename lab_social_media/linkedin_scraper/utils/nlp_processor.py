import re
import string
from collections import Counter
import unicodedata # Para normalización de acentos
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer

class NLPProcessor:
    def __init__(self, language='spanish'):
        self.language = language
        # Descargar recursos necesarios si no existen
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            print("Descargando recursos NLTK...")
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('punkt_tab')

        # Cargar stopwords de español E inglés para limpiar mejor el ruido
        spanish_stops = set(stopwords.words('spanish'))
        english_stops = set(stopwords.words('english'))
        
        self.stop_words = spanish_stops.union(english_stops)
        
        self.stemmer = SnowballStemmer(self.language)

    def clean_text(self, text: str) -> str:
        """
        1. Limpieza y normalización.
        """
        # Reemplazar Non-breaking spaces (\xa0) que causan uniones de palabras
        text = text.replace('\xa0', ' ')
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Hashtags y menciones (Mantenemos el texto del hashtag, solo quitamos el símbolo # y @)
        text = text.replace('#', '').replace('@', '')
        
        # ELIMINAR PALABRA "HASHTAG" que LinkedIn pone para lectores de pantalla
        text = text.replace('hashtag', '')
        
        # Remover puntuación y caracteres especiales (incluyendo emojis)
        # ESTRICTO: Solo permitimos letras (a-z), números, espacios y acentos específicos.
        # Todo lo demás (emojis, símbolos raros) se va.
        text = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ\s]', ' ', text)
        
        # NOTA: Ya NO eliminamos números para no perder contexto (ej: "Año 2024", "C1 Inglés")
        # text = re.sub(r'\d+', '', text) 
        
        # Remover espacios vacíos extra
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def process(self, text: str) -> list:
        """
        Ejecuta el pipeline completo: Limpieza -> Tokenización -> Stopwords -> Stemming
        """
        # 1. Limpieza
        cleaned_text = self.clean_text(text)
        
        # 2. Tokenización (Partir en palabras)
        tokens = word_tokenize(cleaned_text, language=self.language)
        
        # 3. Remover Stopwords y tokens cortos
        filtered_tokens = [
            word for word in tokens 
            if word not in self.stop_words and len(word) > 2
        ]
        
        # 4. Stemming (DESACTIVADO: Para mostrar palabras completas)
        # stemmed_tokens = [self.stemmer.stem(word) for word in filtered_tokens]
        
        return filtered_tokens

    def get_bag_of_words(self, all_tokens: list) -> Counter:
        """Genera la bolsa de palabras (frecuencia)."""
        return Counter(all_tokens)

    def analyze_sentiment(self, text: str) -> str:
        """
        Análisis de sentimiento básico basado en léxico (Regla 'b' de instrucciones).
        Retorna: Positivo, Negativo o Neutral.
        """
        # Léxico básico (expandible)
        positive_words = {'bueno', 'excelente', 'gran', 'oportunidad', 'feliz', 'gracias', 'mejor', 'crecimiento', 'éxito', 'hiring', 'buscamos', 'unete', 'ventaja'}
        negative_words = {'mal', 'error', 'fallo', 'problema', 'rechazo', 'triste', 'lamentable', 'peor', 'baja', 'critica'}
        
        # Usamos el texto limpio pero sin stemmizar para coincidir mejor
        clean = self.clean_text(text)
        tokens = clean.split()
        
        score = 0
        for token in tokens:
            if token in positive_words:
                score += 1
            elif token in negative_words:
                score -= 1
                
        if score > 0:
            return "Positivo"
        elif score < 0:
            return "Negativo"
        else:
            return "Neutral"
