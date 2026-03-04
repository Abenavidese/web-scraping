import pandas as pd
from textblob import TextBlob
import re

# Simple list of Spanish stopwords for term extraction
STOPWORDS = {
    'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por', 'un', 'para', 'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'este', 'sí', 'porque', 'esta', 'entre', 'cuando', 'muy', 'sin', 'sobre', 'también', 'me', 'hasta', 'hay', 'donde', 'quien', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros', 'mi', 'mis', 'tú', 'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros', 'vosotras', 'os', 'mío', 'mía', 'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos', 'suyas', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras', 'es', 'son', 'fue', 'era', 'ser', 'estar'
}

def clean_text(text):
    if not isinstance(text, str):
        return ""
    # Remove special chars and digits
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    return text.lower()

def extract_terms(text):
    if not isinstance(text, str):
        return ""
    
    cleaned = clean_text(text)
    words = cleaned.split()
    terms = [w for w in words if w not in STOPWORDS and len(w) > 2]
    # Return top 10 terms joined by comma
    return ", ".join(terms[:10])

def analyze_sentiment(text):
    if not isinstance(text, str) or not text.strip():
        return "NEUTRO", "No hay texto suficiente para analizar.", ""
        
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    
    # Generate terms
    terms = extract_terms(text)
    
    if polarity > 0.1:
        sentiment = "POSITIVO"
        explanation = "El comentario tiene un tono positivo. Palabras clave detectadas sugieren aprobación o apoyo."
    elif polarity < -0.1:
        sentiment = "NEGATIVO"
        explanation = "El comentario tiene un tono negativo. Palabras clave detectadas sugieren crítica o desaprobación."
    else:
        sentiment = "NEUTRO"
        explanation = "El comentario es mayormente neutro u objetivo. No muestra una fuerte inclinación emocional."
        
    return sentiment, explanation, terms

import argparse

def main():
    parser = argparse.ArgumentParser(description='Rellenar sentimientos faltantes')
    parser.add_argument('--file', type=str, required=True, help='Archivo CSV a procesar')
    args = parser.parse_args()
    
    file_path = args.file
    print(f"Leyendo archivo: {file_path}")
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return

    # Count empty sentiments or terms
    # Check for NaN or empty string in Sentimiento OR Términos
    mask = (
        df['Sentimiento'].isna() | (df['Sentimiento'] == '') |
        df['Términos'].isna() | (df['Términos'] == '')
    )
    count = mask.sum()
    print(f"Encontrados {count} filas con datos faltantes (Sentimiento o Términos).")
    
    if count == 0:
        print("No hay filas vacías que procesar.")
        
    print("Procesando filas...")
    
    processed_count = 0
    for index, row in df[mask].iterrows():
        # Prefer Comentario, fallback to Publicación
        text = row['Comentario']
        if pd.isna(text) or str(text).strip() == "":
            text = row['Publicación']
            
        # Analyze and regenerate to ensure consistency (and standard Spanish terms)
        sentiment, explanation, terms = analyze_sentiment(text)
        
        # We overwrite to ensure consistency (e.g. POSITIVE -> POSITIVO)
        df.at[index, 'Sentimiento'] = sentiment
        df.at[index, 'Explicación'] = explanation
        df.at[index, 'Términos'] = terms
        processed_count += 1
        
    print(f"Procesadas {processed_count} filas.")

    # Save the updated file
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"✅ Archivo actualizado guardado: {file_path}")
    
    # Show sentiment distribution
    print("\nDistribución final:")
    print(df['Sentimiento'].value_counts())

if __name__ == "__main__":
    main()
