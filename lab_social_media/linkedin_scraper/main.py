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
from utils.nlp_processor import NLPProcessor
from utils.llm_processor import LLMAnalyzer
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

async def analyze_post_concurrently(llm_analyzer, clean_text, network="LinkedIn", provider="grok"):
    """Wrapper para análisis LLM asíncrono"""
    return llm_analyzer.analyze(clean_text, network, provider)

async def main():
    parser = argparse.ArgumentParser(description="Extracción y Procesamiento de LinkedIn + Grok LLM")
    parser.add_argument("--query", type=str, default=None, help="Término de búsqueda")
    parser.add_argument("--posts", type=int, default=config.DEFAULT_LIMIT, help="Número de posts a extraer")
    parser.add_argument("--comments", type=int, default=0, help="Número de comentarios por post")
    
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
                
        except OSError:
             args.query = config.DEFAULT_QUERY
             args.comments = 0
    
    # -------------------------

    print(f"--- Iniciando Proceso para: '{args.query}' ---")
    print(f"--- Configuración: {args.posts} posts | Max {args.comments} comentarios/post ---")
    
    # User system configuration
    user_id = os.getenv("USER_ID", "default")
    query_slug = slugify(args.query)
    
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
    data = await scraper.extract(args.query, limit=args.posts, max_comments=args.comments)
    
    if not data:
        print("No se encontraron datos.")
        return

    print(f"   -> {len(data)} items extraídos.")
    extraction_time = time.time() - start_total_time

    # 2. Fase de Procesamiento NLP & LLM
    print("2. Ejecutando Pipeline NLP y Análisis CONCURRENTE con DeepSeek...")
    nlp_start_time = time.time()
    
    processor = NLPProcessor(language='spanish')
    llm_analyzer = LLMAnalyzer()
    
    all_tokens = []
    
    # Lista de tareas para asyncio.gather (Concurrencia)
    llm_tasks = []
    
    # Contar comentarios totales
    total_comments = 0
    for item in data:
        if 'comments' in item and item['comments']:
            total_comments += len(item['comments'])
    
    print(f"   -> Total posts: {len(data)} | Total comentarios: {total_comments}")
    
    # Pre-procesamiento sincrónico (limpieza) - Solo Posts
    for item in data:
        raw_content = item['content'].replace('\n', ' ').replace('\r', '').strip()
        clean_content = processor.clean_text(raw_content)
        item['content'] = clean_content # Actualizamos data limpia
        
        # Guardamos tokens para BoW (incluir comentarios)
        tokens = processor.process(clean_content)
        all_tokens.extend(tokens)
        
        # Tokens de comentarios para BoW
        if 'comments' in item and item['comments']:
            for comment in item['comments']:
                clean_comment = processor.clean_text(comment)
                tokens_comment = processor.process(clean_comment)
                all_tokens.extend(tokens_comment)
        
        # Preparamos Tarea LLM solo para el POST
        llm_tasks.append(analyze_post_concurrently(llm_analyzer, clean_content, "LinkedIn", "deepseek"))

    # Ejecución Concurrente del LLM
    print(f"   -> Enviando {len(llm_tasks)} peticiones concurrentes a DeepSeek...")
    llm_results = await asyncio.gather(*llm_tasks)
    
    # Asignar resultados a la data
    for i, (sentiment, explanation) in enumerate(llm_results):
        data[i]['sentiment_deepseek'] = sentiment
        data[i]['explanation_deepseek'] = explanation
        print(f"   [{i+1}] Sentimiento: {sentiment} | Exp: {explanation[:50]}...")

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

    # Visualización (BoW)
    bow = processor.get_bag_of_words(all_tokens)
    if bow:
        common_words = bow.most_common(10)
        words, counts = zip(*common_words)
        plt.figure(figsize=(10, 6))
        plt.bar(words, counts, color='lightgreen')
        plt.xlabel('Palabras')
        plt.ylabel('Frecuencia')
        plt.title(f'Top Palabras - {args.query}')
        plt.savefig(os.path.join(output_dir, 'frecuencia_palabras.png'))
        print(f"   [Gráfico] {output_dir}/frecuencia_palabras.png")
    
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
