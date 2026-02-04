# -*- coding: utf-8 -*-
"""
Data Cleaner - Text Processing with Multiple Cleaning Levels
Provides three levels of text cleaning for downloadable CSVs
"""

import re
import string
from typing import List, Dict, Any
import pandas as pd


class DataCleaner:
    """Handles text cleaning at different levels of aggressiveness"""
    
    def __init__(self):
        # Spanish stopwords (common words to remove)
        self.stopwords = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber',
            'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le', 'lo', 'todo',
            'pero', 'más', 'hacer', 'o', 'poder', 'decir', 'este', 'ir', 'otro', 'ese',
            'la', 'si', 'me', 'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy',
            'sin', 'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno', 'mismo',
            'yo', 'también', 'hasta', 'año', 'dos', 'querer', 'entre', 'así', 'primero',
            'desde', 'grande', 'eso', 'ni', 'nos', 'llegar', 'pasar', 'tiempo', 'ella',
            'sí', 'día', 'uno', 'bien', 'poco', 'deber', 'entonces', 'poner', 'cosa',
            'tanto', 'hombre', 'parecer', 'nuestro', 'tan', 'donde', 'ahora', 'parte',
            'después', 'vida', 'quedar', 'siempre', 'creer', 'hablar', 'llevar', 'dejar',
            'nada', 'cada', 'seguir', 'menos', 'nuevo', 'encontrar', 'algo', 'solo',
            'decir', 'mundo', 'país', 'fin', 'llamar', 'venir', 'pensar', 'salir',
            'volver', 'tomar', 'conocer', 'vivir', 'sentir', 'tratar', 'mirar', 'contar',
            'empezar', 'esperar', 'buscar', 'existir', 'entrar', 'trabajar', 'escribir',
            'perder', 'producir', 'ocurrir', 'entender', 'pedir', 'recibir', 'recordar',
            'terminar', 'permitir', 'aparecer', 'conseguir', 'comenzar', 'servir', 'sacar',
            'necesitar', 'mantener', 'resultar', 'leer', 'caer', 'cambiar', 'presentar',
            'crear', 'abrir', 'considerar', 'oír', 'acabar', 'mil', 'contra', 'cual',
            'durante', 'ellos', 'ellas', 'nosotros', 'vosotros', 'ustedes', 'mí', 'ti',
            'the', 'and', 'is', 'in', 'to', 'of', 'it', 'for', 'on', 'with', 'as', 'at',
            'this', 'that', 'from', 'by', 'be', 'are', 'was', 'were', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
            'might', 'can', 'an', 'or', 'but', 'not', 'all', 'if', 'when', 'there', 'what'
        }
    
    def clean_basic(self, text: str) -> str:
        """
        Basic cleaning: Remove special characters, emojis, extra whitespace
        Preserves original words and structure
        """
        if not isinstance(text, str):
            return ""
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove mentions and hashtags symbols (keep the word)
        text = re.sub(r'[@#]', '', text)
        
        # Remove emojis and special unicode characters
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Remove extra punctuation (keep basic ones)
        text = re.sub(r'[^\w\s.,!?-]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def clean_normal(self, text: str) -> str:
        """
        Normal cleaning: Basic + stopwords removal + tokenization
        Good balance between cleaning and preserving meaning
        """
        # Apply basic cleaning first
        text = self.clean_basic(text)
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Tokenize and remove stopwords
        words = text.split()
        words = [word for word in words if word not in self.stopwords and len(word) > 2]
        
        return ' '.join(words)
    
    def clean_aggressive(self, text: str) -> str:
        """
        Aggressive cleaning: Normal + stemming + additional filtering
        Maximum cleaning for analysis, may lose some context
        """
        # Apply normal cleaning first
        text = self.clean_normal(text)
        
        # Simple stemming (remove common suffixes)
        words = text.split()
        stemmed_words = []
        
        for word in words:
            # Spanish suffixes
            if word.endswith('mente'):
                word = word[:-5]
            elif word.endswith('ción') or word.endswith('sión'):
                word = word[:-4]
            elif word.endswith('ador') or word.endswith('edor') or word.endswith('idor'):
                word = word[:-4]
            elif word.endswith('ante') or word.endswith('ente') or word.endswith('ible'):
                word = word[:-4]
            elif word.endswith('oso') or word.endswith('osa') or word.endswith('ivo') or word.endswith('iva'):
                word = word[:-3]
            elif word.endswith('ar') or word.endswith('er') or word.endswith('ir'):
                word = word[:-2]
            elif word.endswith('s') and len(word) > 3:
                word = word[:-1]
            
            # English suffixes
            if word.endswith('ing'):
                word = word[:-3]
            elif word.endswith('ed'):
                word = word[:-2]
            elif word.endswith('ly'):
                word = word[:-2]
            
            if len(word) > 2:
                stemmed_words.append(word)
        
        return ' '.join(stemmed_words)
    
    def process_dataframe(self, df: pd.DataFrame, level: str = 'normal', text_columns: List[str] = None) -> pd.DataFrame:
        """
        Process a DataFrame with the specified cleaning level
        
        Args:
            df: Input DataFrame
            level: 'basico', 'normal', or 'agresivo'
            text_columns: List of column names to clean. If None, auto-detect text columns
        
        Returns:
            DataFrame with cleaned text columns
        """
        df_copy = df.copy()
        
        # Auto-detect text columns if not specified
        if text_columns is None:
            text_columns = []
            for col in df_copy.columns:
                if col in ['post_caption', 'content', 'text', 'comment', 'post_text', 'caption_snippet']:
                    text_columns.append(col)
        
        # Select cleaning function
        if level == 'basico':
            clean_func = self.clean_basic
        elif level == 'agresivo':
            clean_func = self.clean_aggressive
        else:  # normal
            clean_func = self.clean_normal
        
        # Apply cleaning to each text column
        for col in text_columns:
            if col in df_copy.columns:
                df_copy[f'{col}_cleaned'] = df_copy[col].apply(lambda x: clean_func(str(x)) if pd.notna(x) else '')
        
        return df_copy


if __name__ == "__main__":
    # Test the cleaner
    cleaner = DataCleaner()
    
    test_text = "¡Hola! 👋 Este es un texto de prueba con @menciones, #hashtags y https://example.com enlaces. ¿Funciona bien? 🎉"
    
    print("Original:")
    print(test_text)
    print("\nBásico:")
    print(cleaner.clean_basic(test_text))
    print("\nNormal:")
    print(cleaner.clean_normal(test_text))
    print("\nAgresivo:")
    print(cleaner.clean_aggressive(test_text))
