import pandas as pd
import sys
import os

# Ensure shared module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.sentiment_analyzer import analyze_sentiment_individual

def analyze_sentiment(text):
    if pd.isna(text) or text == "" or text == "No comments":
        return "UNKNOWN", "NONE", "NONE", 0.0, "No hay texto para analizar"
        
    result = analyze_sentiment_individual(text)
    
    sentiment = result.get('sentiment', 'UNKNOWN').upper()
    emotion = result.get('emotion', 'NONE').upper()
    intensity = result.get('intensity', 'NONE').upper()
    confidence = result.get('confidence', 0.0)
    explanation = result.get('reasoning', 'Sin explicación')
    
    if sentiment == "MIXED":
        sentiment = "MIXTO"
    elif sentiment == "POSITIVE":
        sentiment = "POSITIVO"
    elif sentiment == "NEGATIVE":
        sentiment = "NEGATIVO"
    elif sentiment == "NEUTRAL":
        sentiment = "NEUTRO"
        
    return sentiment, emotion, intensity, confidence, explanation

def main():
    file_path = "formato_investigacion_maría_elisa_padilla.csv"
    print(f"Leyendo archivo: {file_path}")
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return

    # Create new columns if they don't exist
    for col in ['Emocion', 'Intensidad', 'Confianza']:
        if col not in df.columns:
            df[col] = ''

    # Filter for X (Twitter) comments with UNKNOWN sentiment
    mask = (df['Red Social'] == 'X (Twitter)') & (df['Sentimiento'] == 'UNKNOWN')
    
    count = mask.sum()
    print(f"Encontrados {count} comentarios de X para corregir.")
    
    if count == 0:
        print("No se encontraron comentarios para corregir.")
        return

    # Apply sentiment analysis
    print("Aplicando análisis de sentimiento robusto con LLM (DeepSeek)...")
    
    processed = 0
    for index, row in df[mask].iterrows():
        text = row['Comentario']
        # If comment is empty, try using the post content
        if pd.isna(text) or text == "" or text == "No comments":
            text = row['Publicación']
            
        sentiment, emotion, intensity, confidence, explanation = analyze_sentiment(text)
        
        df.at[index, 'Sentimiento'] = sentiment
        df.at[index, 'Explicación'] = explanation
        df.at[index, 'Emocion'] = emotion
        df.at[index, 'Intensidad'] = intensity
        df.at[index, 'Confianza'] = confidence
        
        processed += 1
        if processed % 10 == 0 or processed == count:
            print(f"  [{processed}/{count}] comentarios procesados...")

    # Save the updated file
    output_path = "formato_investigacion_maría_elisa_padilla_fixed.csv"
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"✅ Archivo corregido guardado como: {output_path}")
    print("\nResumen de correcciones (Sentimientos):")
    print(df[df['Red Social'] == 'X (Twitter)']['Sentimiento'].value_counts())

if __name__ == "__main__":
    main()
