import pandas as pd
import numpy as np
import re
import hashlib
import os
import emoji
from langdetect import detect, LangDetectException
import datetime
import uuid

def normalizar_timestamps(df):
    """Normaliza timestamps a UTC ISO-8601 y deriva year/month."""
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
    else:
        df['timestamp'] = pd.NaT
        df['year'] = np.nan
        df['month'] = np.nan
    return df

def text_norm_for_hash(text):
    """Normaliza texto estrictamente para deduplicación exacta."""
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def deduplicar_exacta(df):
    """Añade columna hash y marca is_duplicate usando text_norm_for_hash."""
    df['text_norm_for_hash'] = df['text'].apply(text_norm_for_hash)
    df['hash'] = df['text_norm_for_hash'].apply(lambda x: hashlib.sha1(x.encode('utf-8')).hexdigest())
    df['is_duplicate'] = df.duplicated('hash', keep='first')
    return df

def text_clean_semantic(text):
    """Limpieza semántica: minúsculas, sin URLs/menciones, mantiene puntuación básica e interior de hashtags."""
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+', '', text)
    text = re.sub(r'\#(\w+)', r'\1', text) # Elimina '#' pero conserva palabra
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def text_clean_intensity(text):
    """Limpieza de intensidad: conserva MAYUSCULAS, elongaciones, signos de exclamación y transforma emojis a texto."""
    if not isinstance(text, str): return ""
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+', '', text)
    text = emoji.demojize(text, language='es')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_features(df):
    """Extrae features de texto como conteo de caracteres, ratios y flags heurísticas."""
    def get_caps_ratio(text):
        if not isinstance(text, str) or len(text) == 0: return 0.0
        caps = sum(1 for c in text if c.isupper())
        alpha_len = sum(1 for c in text if c.isalpha())
        return caps / alpha_len if alpha_len > 0 else 0.0

    def profanity_flag(text):
        if not isinstance(text, str): return False
        bad_words = ['mierda', 'carajo', 'puta', 'puto', 'joder', 'coño', 'pendejo', 'hdp']
        text_lower = text.lower()
        for w in bad_words:
            if re.search(rf'\b{w}\b', text_lower):
                return True
        return False

    df['len_chars'] = df['text'].astype(str).str.len()
    df['len_tokens'] = df['text'].astype(str).apply(lambda x: len(x.split()))
    df['num_exclamations'] = df['text'].astype(str).apply(lambda x: x.count('!'))
    df['num_questions'] = df['text'].astype(str).apply(lambda x: x.count('?'))
    df['caps_ratio'] = df['text'].apply(get_caps_ratio)
    df['emoji_count'] = df['text'].apply(lambda x: emoji.emoji_count(x) if isinstance(x, str) else 0)
    df['url_count'] = df['text'].astype(str).apply(lambda x: len(re.findall(r'http\S+|www\S+|https\S+', x)))
    df['profanity_flag'] = df['text'].apply(profanity_flag)
    
    return df

def detectar_idioma(text):
    if not isinstance(text, str) or text.strip() == "": return "unknown"
    text_clean = re.sub(r'http\S+|www\S+|https\S+', '', text).strip()
    if not text_clean: return "unknown"
    try:
        return detect(text_clean)
    except LangDetectException:
        return "unknown"

def filtro_idioma(df):
    """Añade columnas de idioma e is_es."""
    df['language'] = df['text'].apply(detectar_idioma)
    df['is_es'] = df['language'] == 'es'
    return df

def filtro_spam(df):
    """Detecta spam basándose en heurísticas sencillas."""
    def is_spam(row):
        text = str(row['text'])
        # Spam: solo enlaces
        text_no_urls = re.sub(r'http\S+|www\S+|https\S+', '', text).strip()
        if len(text_no_urls) == 0 and row['url_count'] > 0:
            return True
        # Spam: demasiados hashtags (>10)
        hashtags = re.findall(r'\#\w+', text)
        if len(hashtags) > 10:
            return True
        # Spam: repetición extrema de un carácter (>15 veces)
        if re.search(r'(.)\1{15,}', text):
            return True
        return False

    df['is_spam'] = df.apply(is_spam, axis=1)
    return df

def run_etl_pipeline(input_csv, platform="x", skip_idioma=False):
    """Ejecuta el pipeline completo dado un csv crudo, dividiéndolo por año-mes y generando reportes."""
    print(f"--- Iniciando ETL Pipeline Phase 2 para {input_csv} ---")
    
    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} no existe.")
        return
        
    df = pd.read_csv(input_csv)
    n_raw = len(df)
    print(f"1. Datos cargados: {n_raw} filas.")
    
    # 2.1 Unificación y Staging
    df = normalizar_timestamps(df)
    
    # 2.2 Deduplicación
    df = deduplicar_exacta(df)
    n_after_dedupe = len(df[~df['is_duplicate']])
    print(f"2. Deduplicación terminada: {n_raw - n_after_dedupe} duplicados exactos marcados.")
    
    # 2.3 Limpieza y Features
    df['text_clean_semantic'] = df['text'].apply(text_clean_semantic)
    df['text_clean_intensity'] = df['text'].apply(text_clean_intensity)
    df = extract_features(df)
    print(f"3. Limpieza de texto y extracción de features finalizada.")
    
    # 2.4 Idioma
    if not skip_idioma:
        df = filtro_idioma(df)
        n_after_lang = len(df[(~df['is_duplicate']) & (df['is_es'])])
        print(f"4. Filtro de idioma aplicado. {len(df[df['language'] != 'es'])} filas no son español.")
    else:
        df['language'] = 'es'
        df['is_es'] = True
        n_after_lang = n_after_dedupe
        print("4. Filtro de idioma omitido por flag (asumiendo todo español).")
    
    # 2.5 Spam
    df = filtro_spam(df)
    n_after_spam = len(df[(~df['is_duplicate']) & (df['is_es']) & (~df['is_spam'])])
    print(f"5. Filtro anti-spam aplicado. {len(df[df['is_spam']])} filas marcadas como spam.")
    
    # Organizar directorios y guardar Parquets divididos por year-month
    staged_dir = os.path.join("staged", platform)
    os.makedirs(staged_dir, exist_ok=True)
    
    # Fill nan years/months for partitioning to "unknown"
    df['year_month'] = df.apply(
        lambda x: "unknown" if pd.isna(x['year']) else f"{int(x['year'])}-{int(x['month']):02d}", 
        axis=1
    )
    
    # Save partitioned parquet
    for ym, group in df.groupby('year_month'):
        # Drop temporary 'year_month' column 
        group_to_save = group.drop(columns=['year_month'])
        out_path = os.path.join(staged_dir, f"{ym}.parquet")
        group_to_save.to_parquet(out_path, index=False)
        print(f"  -> Guardado partición: {out_path} ({len(group_to_save)} filas)")
    
    # 2.6 Reporte de Calidad
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_data = {
        "run_id": run_id,
        "platform": platform,
        "N_raw": n_raw,
        "N_after_dedupe": n_after_dedupe,
        "N_after_lang_filter": n_after_lang,
        "N_after_spam_filter": n_after_spam,
        "perc_duplicates": round((n_raw - n_after_dedupe) / n_raw * 100, 2) if n_raw > 0 else 0,
        "perc_non_es": round(len(df[df['language'] != 'es']) / n_raw * 100, 2) if n_raw > 0 else 0,
        "perc_spam": round(len(df[df['is_spam']]) / n_raw * 100, 2) if n_raw > 0 else 0,
        "median_len_tokens": df['len_tokens'].median()
    }
    
    report_df = pd.DataFrame([report_data])
    report_path = os.path.join(reports_dir, f"data_quality_{run_id}.csv")
    report_df.to_csv(report_path, index=False)
    print(f"6. Data Quality Report generado: {report_path}")
    print("--- ETL Pipeline Finalizado Exitosamente ---")
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ETL Pipeline Phase 2")
    parser.add_argument("--input", "-i", type=str, required=True, help="Ruta al archivo CSV raw")
    parser.add_argument("--platform", "-p", type=str, default="x", help="Plataforma de origen (ej. x, facebook)")
    parser.add_argument("--skip-idioma", action="store_true", help="Omitir detección de idioma (para ahorrar tiempo)")
    
    args = parser.parse_args()
    run_etl_pipeline(args.input, platform=args.platform, skip_idioma=args.skip_idioma)
