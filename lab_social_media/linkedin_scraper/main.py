# -*- coding: utf-8 -*-
import asyncio
import sys
import argparse
import matplotlib.pyplot as plt

# Fix Windows encoding issues for emojis
# if sys.platform == 'win32':
#     import io
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
#     sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from scrapers.linkedin_scraper import LinkedInScraper
import config 
import time
import os
import csv
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def slugify(text):
    """Convert text to slug format for directory names"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')


async def main():
    parser = argparse.ArgumentParser(description="Extracción y Procesamiento de LinkedIn + Grok LLM")
    parser.add_argument("--query", type=str, default=None, help="Término de búsqueda")
    parser.add_argument("--posts", type=int, default=config.DEFAULT_LIMIT, help="Número de posts a extraer")
    parser.add_argument("--comments", type=int, default=0, help="Número de comentarios por post")
    parser.add_argument("--year", type=int, default=None, help="Año para el filtrado")
    parser.add_argument("--month", type=int, default=None, help="Mes para el filtrado (1-12)")
    
    args = parser.parse_args()
    start_total_time = time.time()

    # --- INPUT INTERACTIVO (RESTAURADO) ---
    if not args.query:
        print("\n--- CONFIGURACIÓN DE BÚSQUEDA ---")
        try:
            print("(!) Nota: Se usará DEEPSEEK para el análisis de sentimiento.")
            user_input = input(f"Ingrese el término a buscar (Default: '{config.DEFAULT_QUERY}'): ")
            args.query = user_input.strip() if user_input.strip() else config.DEFAULT_QUERY
            
            posts_input = input(f"¿Cuántos posts deseas extraer? (Default: {config.DEFAULT_LIMIT}): ")
            if posts_input.strip().isdigit():
                args.posts = int(posts_input.strip())
                
            comments_input = input(f"¿Cuántos comentarios por post deseas extraer? (Default: 0 - Ninguno): ")
            if comments_input.strip().isdigit():
                args.comments = int(comments_input.strip())
                
            year_input = input(f"¿Año (Opcional, dejar vacío para omitir fecha)? ")
            if year_input.strip().isdigit():
                args.year = int(year_input.strip())
                month_input = input(f"¿Mes (1-12) (Opcional, dejar vacío para omitir)? ")
                if month_input.strip().isdigit():
                    args.month = int(month_input.strip())
                
        except OSError:
             args.query = config.DEFAULT_QUERY
             args.comments = 0
             args.year = None
             args.month = None
    
    # -------------------------

    print(f"--- Iniciando Proceso para: '{args.query}' ---")
    print(f"--- Configuración: {args.posts} posts | Max {args.comments} comentarios/post ---")
    
    # User system configuration
    user_id = os.getenv("USER_ID", "default")
    query_slug = slugify(args.query)
    
    # Adaptar formato de directorio al de X si usa fechas
    if args.year and args.month:
        import calendar
        _, last_day = calendar.monthrange(args.year, args.month)
        query_slug = f"{query_slug}_since{args.year}_{args.month:02d}_01_until{args.year}_{args.month:02d}_{last_day}"
    
    # Create output directory with user system structure
    output_dir = os.path.join("..", "users", user_id, "linkedin", query_slug)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n🔐 User ID: {user_id}")
    print(f"📁 Output directory: {output_dir}")
    
    # Validar Cookie
    if config.LINKEDIN_LI_AT_COOKIE == "PEGAR_TU_COOKIE_LI_AT_AQUI" or len(config.LINKEDIN_LI_AT_COOKIE) < 10:
        print("\n[!] ERROR: No has pegado tu cookie 'li_at' en config.py.")
        return

    # 1. Fase de Extracción
    scraper = LinkedInScraper(li_at_cookie=config.LINKEDIN_LI_AT_COOKIE, headless=False)
    
    print("1. Extrayendo datos de LinkedIn...")
    data = await scraper.extract(args.query, limit=args.posts, max_comments=args.comments, year=args.year, month=args.month)
    
    if not data:
        print("No se encontraron datos.")
        return

    print(f"   -> {len(data)} items extraídos.")
    extraction_time = time.time() - start_total_time
    # 2. Processing and Sentiment Analysis
    print("2. Ejecutando ETL Pipeline y Análisis con DeepSeek...")
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from shared.data_cleaner import ETLProcessor
    from shared.sentiment_analyzer import DeepSeekSentimentAnalyzer
    import pandas as pd
    
    # Prepara datos para ETL (Aplanar de estructura anidada)
    flattened_data = []
    
    # Manejo de timestamps
    from datetime import datetime
    now = datetime.now()
    default_year = args.year if args.year else now.year
    default_month = args.month if args.month else now.month
    
    try:
        import uuid
        import zlib
        for item in data: # data from mock JSON
            item_url = item.get('url', f"https://linkedin.com/post/{uuid.uuid4().hex[:8]}")
            raw_id = item_url.split('/')[-1] if item_url else str(uuid.uuid4())[:8]
            
            # Forzamos un ID Entero puro al igual que X usando CRC32 (evitando colisiones básicas)
            item_id = str(abs(zlib.crc32(raw_id.encode("utf-8"))))
            
            # Extraer año/mes de timestamp si existe, si no por defecto
            ts = item.get('timestamp', '')
            year, month = default_year, default_month
            if ts:
                try:
                    if 'T' in str(ts):
                        dt = datetime.strptime(str(ts).split('T')[0], "%Y-%m-%d")
                        year, month = dt.year, dt.month
                except:
                    pass
            
            flattened_data.append({
                "type": "post",
                "author": item.get('author', 'Unknown'),
                "text": item.get('content', ''),
                "parent_url": item_url,
                "timestamp": ts,
                "item_id": item_id,
                "year": year,
                "month": month,
                "post_id": item_id
            })
            
            for comment in item.get('comments', []):
                comment_uuid = str(uuid.uuid4())
                comment_id = str(abs(zlib.crc32(comment_uuid.fallback.encode("utf-8"))) if hasattr(comment_uuid, 'fallback') else abs(zlib.crc32(comment_uuid.encode('utf-8'))))
                flattened_data.append({
                    "type": "comment",
                    "author": "Unknown LinkedIn User",
                    "text": comment,
                    "parent_url": item_url,
                    "timestamp": ts,
                    "item_id": comment_id,
                    "year": year,
                    "month": month,
                    "post_id": item_id
                })
    except Exception as e:
        print(f"Error aplanando datos: {e}")
        
    df_raw = pd.DataFrame(flattened_data)
    
    if df_raw.empty:
        print("No hay datos extraidos.")
        return
        
    etl = ETLProcessor()
    topic_kws = [args.query] if args.query else []
    try:
        df_processed = etl.run_etl_pipeline(df_raw, platform='linkedin', run_id=f"run_li_{int(time.time())}", topic_keywords=topic_kws)
    except Exception as e:
        print(f"Error in ETL pipeline: {e}")
        df_processed = df_raw.copy()
        
    try:
        analyzer = DeepSeekSentimentAnalyzer()
        
        # Analyze sentiments using the precise fields
        sentiments = []
        emotions = []
        intensities = []
        confidences = []
        reasonings = []
        
        for idx, row in df_processed.iterrows():
            text_to_analyze = row.get('processed_text', row.get('text', ''))
            print(f"Analyzing [{idx+1}/{len(df_processed)}]...")
            
            if not text_to_analyze or str(text_to_analyze).strip() == '':
                sentiments.append('neutral')
                emotions.append('none')
                intensities.append('none')
                confidences.append(0.0)
                reasonings.append('No text analyzed')
                continue
                
            res = analyzer.analyze_individual(text_to_analyze)
            sentiments.append(res.get('sentiment', 'unknown'))
            emotions.append(res.get('emotion', 'none'))
            intensities.append(res.get('intensity', 'none'))
            confidences.append(res.get('confidence', 0.0))
            reasonings.append(res.get('reasoning', 'No reasoning provided'))
            
            print(f" -> {res.get('sentiment', 'unknown')} | {res.get('emotion', 'none')} | {res.get('intensity', 'none')} ({res.get('confidence', 0.0)})")
            
        df_processed['sentiment'] = sentiments
        df_processed['emotion'] = emotions
        df_processed['intensity'] = intensities
        df_processed['confidence'] = confidences
        df_processed['explanation_deepseek'] = reasonings
        df_processed['sentiment_deepseek'] = sentiments
        
    except Exception as e:
        print(f"Error analyzer: {e}")

    # Convertir a estructura antigua de data/csv para guardar compatibilidad
    data = df_processed.to_dict('records')
    
    # 3. Reporte y Visualización

    print("3. Generando Reporte...")
    
    csv_file = os.path.join(output_dir, 'datos_extraidos_deepseek.csv')
    
    if data:
        # Preparar datos para CSV (convertir listas a JSON strings)
        csv_data = []
        for item in data:
            csv_item = item.copy()
            # Convertir comments (lista) a string para CSV
            if 'comments' in csv_item and isinstance(csv_item['comments'], list):
                csv_item['comments'] = json.dumps(csv_item['comments'], ensure_ascii=False)
            csv_data.append(csv_item)
        
        keys = list(csv_data[0].keys())
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(csv_data)
        print(f"   [CSV] Datos guardados: {csv_file}")
        
        # ✅ NUEVO: Generar CSV unificado en formato de investigación
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from shared.unified_csv_exporter import convert_linkedin_to_unified
            
            unified_csv_path = os.path.join(output_dir, "formato_investigacion.csv")
            convert_linkedin_to_unified(csv_file, unified_csv_path)
            print(f"   [CSV Unificado] Formato Investigación: {unified_csv_path}")
        except Exception as e:
            print(f"   ⚠️  Error generando CSV unificado: {e}")

    # Optional Visualization block disabled to preserve original workflow structure
    
    total_time = time.time() - start_total_time
    nlp_time = total_time - extraction_time
    
    # --- PERFORMANCE METRICS REPORT ---
    print("\n" + "="*50)
    print(f"       PERFORMANCE REPORT: {args.query.upper()}")
    print("="*50)
    print(f"Total Posts Extracted:  {len(data)}")
    print("-" * 50)
    print(f"1. Extraction Phase:    {extraction_time:.2f} seconds")
    print(f"2. NLP + LLM Analysis:  {nlp_time:.2f} seconds (DeepSeek - Concurrent)")
    print("-" * 50)
    print(f"TOTAL EXECUTION TIME:   {total_time:.2f} seconds")
    print("="*50)
    
    # Calculate sentiment distribution
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    for item in data:
        s = item.get('sentiment_deepseek', 'Neutro').lower()
        if 'positiv' in s:
            sentiment_distribution["positive"] += 1
        elif 'negativ' in s:
            sentiment_distribution["negative"] += 1
        else:
            sentiment_distribution["neutral"] += 1
    # Calculate total comments
    total_comments = sum(len(item.get('comments', [])) for item in data)
    
    # Generate metrics JSON for master scraper
    metrics = {
        "social_network": "LinkedIn",
        "llm_used": "DeepSeek",
        "query": args.query,
        "execution_times": {
            "scraping": round(extraction_time, 2),
            "text_processing": round(nlp_time, 2),
            "sentiment_analysis": round(nlp_time, 2),  # LLM analysis included in NLP time
            "total": round(total_time, 2)
        },
        "data_metrics": {
            "posts_extracted": len(data),
            "comments_extracted": total_comments,
            "comments_analyzed": 0,  # Mantenemos consistencia con otros scrapers
            "total_text_items": len(data)
        },
        "sentiment_distribution": sentiment_distribution,
        "performance_metrics": {
            "posts_per_second": round(len(data) / extraction_time if extraction_time > 0 else 0, 2),
            "comments_per_second": 0,  # Mantenemos consistencia con otros scrapers
            "avg_time_per_post": round(extraction_time / len(data) if len(data) > 0 else 0, 2)
        }
    }
    
    # Save metrics JSON
    metrics_filename = os.path.join(output_dir, "metrics.json")
    with open(metrics_filename, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
    print(f"\n📊 Metrics saved to: {metrics_filename}")
    
    # Print metrics in JSON format for master scraper to capture
    print("\n### METRICS_JSON_START ###")
    print(json.dumps(metrics, ensure_ascii=False))
    print("### METRICS_JSON_END ###")
    
    print(f"\n--- Proceso Finalizado en {total_time:.2f}s ---")

if __name__ == "__main__":
    asyncio.run(main())
