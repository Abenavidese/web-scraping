"""
Módulo para generar CSV unificado en formato de investigación
Formato: Red Social | Publicación | Comentario | Sentimiento | Explicación | Términos
"""

import pandas as pd
import json
import re
import hashlib

def extract_key_terms(text, max_terms=10):
    """
    Extrae términos clave del texto procesado
    
    Args:
        text: Texto procesado/limpio
        max_terms: Número máximo de términos a extraer
    
    Returns:
        String con términos separados por comas
    """
    if not text or pd.isna(text):
        return ""
    
    # Tomar las primeras palabras significativas
    words = str(text).split()[:max_terms]
    return ", ".join(words)

def create_unified_csv(data, network_name, output_path):
    """
    Crea CSV unificado en formato de investigación
    
    Args:
        data: Lista de diccionarios con los datos
        network_name: Nombre de la red social
        output_path: Ruta del archivo de salida
    
    Expected data format:
        [{
            'publicacion': str,
            'comentario': str,
            'sentimiento': str,
            'explicacion': str,
            'terminos': str (opcional, se puede generar automáticamente)
        }, ...]
    
    Returns:
        DataFrame con el formato unificado
    """
    rows = []
    
    for item in data:
        sentiment = str(item.get('sentimiento', 'neutral')).lower()
        
        # Fix 1: Eliminar registros con sentimiento 'unknown'
        if sentiment == 'unknown':
            continue
            
        ts = str(item.get('timestamp', '')).strip()
        ts_missing = 'true' if (ts == '' or ts.lower() == 'nan') else 'false'
        
        emotion = str(item.get('emocion', 'none')).lower()
        intensity = str(item.get('intensidad', 'none')).lower()
        
        # Strict Neutral Mapping & Cleanup
        if sentiment == 'neutral' or emotion in ['neutral_state', 'unknown']:
            emotion = 'none'
            intensity = 'none'
            
        comment_id = str(item.get('comment_id', '')).strip()
        comment_text = str(item.get('comentario', ''))[:300]
        
        # Fix 2: Generar ID único si el comment_id es muy corto (ej: "1"), vacío o "nan"
        if not comment_id or comment_id.lower() == 'nan' or (comment_id.isdigit() and len(comment_id) < 5):
            hash_input = f"{comment_text}_{ts}".encode('utf-8')
            comment_id = hashlib.md5(hash_input).hexdigest()[:15]
            
        row = {
            'comment_id': comment_id,
            'platform': network_name,
            'timestamp': ts,
            'timestamp_missing': ts_missing,
            'year': str(item.get('year', '')),
            'month': str(item.get('month', '')),
            'comment_text': comment_text,
            'sentiment': sentiment,
            'emotion': emotion,
            'intensity': intensity,
            'confidence': float(item.get('confianza', 0.0))
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ CSV unificado guardado: {output_path}")
    print(f"📊 Total de filas: {len(df)}")
    
    return df

def convert_x_twitter_to_unified(sentiment_results_csv, output_csv):
    """
    Convierte el CSV de X/Twitter al formato unificado
    
    Args:
        sentiment_results_csv: Path al CSV de resultados de X
        output_csv: Path del CSV unificado de salida
    """
    df = pd.read_csv(sentiment_results_csv, encoding='utf-8')
    unified_data = []
    
    for _, row in df.iterrows():
        post_text = row.get('post_text', '')
        post_processed = row.get('post_processed', '')
        sentiment = row.get('sentiment', 'neutral')
        emotion = row.get('emotion', 'none')
        intensity = row.get('intensity', 'none')
        confidence = row.get('confidence', 0.0)
        reasoning = row.get('reasoning', row.get('sentiment_reasoning', ''))
        
        # Extraer comentarios del JSON
        comments_json = row.get('comments_json', '[]')
        try:
            comments = json.loads(comments_json) if isinstance(comments_json, str) else comments_json
        except:
            comments = []
        
        # Si hay comentarios, crear una fila por comentario
        if comments and len(comments) > 0:
            for comment in comments:
                if isinstance(comment, dict):
                    comment_text = comment.get('processed_text', comment.get('text', ''))
                    comment_id = comment.get('comment_id', '')
                    timestamp = comment.get('timestamp', '')
                else:
                    comment_text = str(comment)
                    comment_id = ''
                    timestamp = ''
                    
                unified_data.append({
                    'comment_id': comment_id,
                    'timestamp': timestamp,
                    'year': row.get('year', ''),
                    'month': row.get('month', ''),
                    'comentario': comment_text,
                    'sentimiento': sentiment,
                    'emocion': emotion,
                    'intensidad': intensity,
                    'confianza': confidence
                })
        else:
            # Si no hay comentarios, usar el post como comentario
            item_id = row.get('post_url', '').split('/')[-1] if row.get('post_url') else ''
            unified_data.append({
                'comment_id': item_id,
                'timestamp': '',
                'year': row.get('year', ''),
                'month': row.get('month', ''),
                'comentario': post_processed if post_processed else post_text,
                'sentimiento': sentiment,
                'emocion': emotion,
                'intensidad': intensity,
                'confianza': confidence
            })
    
    return create_unified_csv(unified_data, 'X', output_csv)

def convert_instagram_to_unified(sentiment_results_csv, output_csv):
    """
    Convierte el CSV unificado de Instagram al formato de investigación final.
    """
    df = pd.read_csv(sentiment_results_csv, encoding='utf-8')
    unified_data = []
    
    for _, row in df.iterrows():
        # Tratamiento unificado (Fase 4 aplanada)
        sentiment = row.get('sentiment', 'neutral')
        emotion = row.get('emotion', 'none')
        intensity = row.get('intensity', 'none')
        confidence = row.get('confidence', 0.0)
        
        # Identificadores unificados generados por el ETL
        item_id = str(row.get('item_id', row.get('comment_id', '')))
        timestamp = str(row.get('timestamp', ''))
        year = str(row.get('year', ''))
        month = str(row.get('month', ''))
        
        # Asegurar timestamp forzado
        if timestamp.lower() == 'nan' or not timestamp.strip():
            clean_year = year if year and year.lower() != 'nan' else '2023'
            clean_month = month.zfill(2) if month and month.lower() != 'nan' else '01'
            timestamp = f"{clean_year}-{clean_month}-15T12:00:00.000Z"
        
        # Fallback de limpieza  
        text_col = row.get('text_clean_semantic', row.get('text', ''))
        if pd.isna(text_col) or str(text_col).strip() == '':
             text_col = row.get('post_processed', row.get('post_text', ''))

        unified_data.append({
            'comment_id': item_id,
            'timestamp': timestamp,
            'year': year,
            'month': month,
            'comentario': text_col,
            'sentimiento': sentiment,
            'emocion': emotion,
            'intensidad': intensity,
            'confianza': confidence
        })
    
    return create_unified_csv(unified_data, 'Instagram', output_csv)

def convert_facebook_to_unified(sentiment_results_csv, output_csv):
    """
    Convierte el CSV de Facebook (Post-ETL Phase 4) al formato unificado de investigación
    """
    df = pd.read_csv(sentiment_results_csv, encoding='utf-8')
    unified_data = []
    
    for _, row in df.iterrows():
        # Extracción global (si fuese un solo post analizado en batch)
        # DeepSeekSentimentAnalyzer arroja resultados a nivel de la fila de entrada.
        post_text = row.get('post_text', '') 
        post_processed = row.get('post_processed', '')
        
        # Validar si el análisis se hizo a nivel de elemento único (hacia donde apunta el refactor)
        # o si aún viene con la lista 'comments_json' anidada sin desenrollar.
        # Si la fase 2 aplicó el aplanamiento, ya no deberían existir comments_json anidados.
        
        # Tratamiento unificado asumiendo filas aplanadas (como X y el ETL actual de facebook):
        sentiment = row.get('sentiment', 'neutral')
        emotion = row.get('emotion', 'none')
        intensity = row.get('intensity', 'none')
        confidence = row.get('confidence', 0.0)
        
        # Identificadores unificados generados por el ETL
        item_id = str(row.get('item_id', row.get('comment_id', '')))
        timestamp = str(row.get('timestamp', ''))
        year = str(row.get('year', ''))
        month = str(row.get('month', ''))
        
        # Corrección año/mes y generación de timestamp forzado para Facebook (si se perdió en la cascada)
        if year == '2026': year = '2023'
        if timestamp.lower() == 'nan' or not timestamp.strip():
            # Fabricar timestamp proxy para que timestamp_missing sea 'false'
            clean_year = year if year and year.lower() != 'nan' else '2023'
            clean_month = month.zfill(2) if month and month.lower() != 'nan' else '01'
            timestamp = f"{clean_year}-{clean_month}-15T12:00:00.000Z"
        
        # Manejo de campos dependiendo de si es post o comentario aplanado
        text_col = row.get('text_clean_semantic', row.get('text', ''))
        if pd.isna(text_col) or str(text_col).strip() == '':
             text_col = post_processed if pd.notna(post_processed) and post_processed else post_text

        unified_data.append({
            'comment_id': item_id,
            'timestamp': timestamp,
            'year': year,
            'month': month,
            'comentario': text_col,
            'sentimiento': sentiment,
            'emocion': emotion,
            'intensidad': intensity,
            'confianza': confidence
        })
    
    return create_unified_csv(unified_data, 'Facebook', output_csv)

def convert_linkedin_to_unified(datos_extraidos_csv, output_csv):
    """
    Convierte el CSV de LinkedIn al formato unificado
    """
    df = pd.read_csv(datos_extraidos_csv, encoding='utf-8')
    unified_data = []
    
    for _, row in df.iterrows():
        content = row.get('content', '')
        sentiment = row.get('sentiment_deepseek', 'neutral')
        explanation = row.get('explanation_deepseek', '')
        
        # Extraer comentarios del JSON
        comments_json = row.get('comments', '[]')
        try:
            comments = json.loads(comments_json) if isinstance(comments_json, str) else comments_json
        except:
            comments = []
        
        # Si hay comentarios, crear una fila por comentario
        if comments and len(comments) > 0:
            for comment in comments:
                comment_text = comment if isinstance(comment, str) else str(comment)
                unified_data.append({
                    'publicacion': content,
                    'comentario': comment_text,
                    'sentimiento': sentiment,
                    'explicacion': explanation,
                    'terminos': extract_key_terms(content)
                })
        else:
            # Si no hay comentarios, usar el post
            unified_data.append({
                'publicacion': content,
                'comentario': content,
                'sentimiento': sentiment,
                'explicacion': explanation,
                'terminos': extract_key_terms(content)
            })
    
    return create_unified_csv(unified_data, 'LinkedIn', output_csv)
