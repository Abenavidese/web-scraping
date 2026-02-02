# -*- coding: utf-8 -*-
import asyncio
import sys
import argparse
import matplotlib.pyplot as plt

# Fix Windows encoding issues for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from scrapers.linkedin_scraper import LinkedInScraper
from utils.nlp_processor import NLPProcessor
from utils.llm_processor import LLMAnalyzer
import config 
import time
import os
import csv

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
            print("(!) Nota: Se usará GROK para el análisis de sentimiento.")
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
    print("2. Ejecutando Pipeline NLP y Análisis CONCURRENTE con Grok (Ahora DeepSeek Granular)...")
    nlp_start_time = time.time()
    
    processor = NLPProcessor(language='spanish')
    llm_analyzer = LLMAnalyzer()
    
    all_tokens = []
    
    # Pre-procesamiento sincrónico (limpieza)
    for item in data:
        raw_content = item['content'].replace('\n', ' ').replace('\r', '').strip()
        clean_content = processor.clean_text(raw_content)
        item['content'] = clean_content # Actualizamos data limpia
        
        # Guardamos tokens para BoW
        tokens = processor.process(clean_content)
        all_tokens.extend(tokens)

    # Análisis Granular Batch
    print(f"   -> Ejecutando análisis granular batch...")
    granular_results = llm_analyzer.analyze_batch_granular(data)

    # Actualizar Data Original con Sentimientos (Post level)
    # Mapping back results to data structure for JSON consistency
    for item in granular_results:
        # parent_id = post_0
        if item['type'] == 'POST':
            try:
                idx = int(item['parent_id'].split('_')[1])
                if idx < len(data):
                    data[idx]['sentiment_deepseek'] = item['sentiment']
                    data[idx]['explanation_deepseek'] = item['reasoning']
            except: pass
            
    # Imprimir algunos resultados
    for i, item in enumerate(data):
        s = item.get('sentiment_deepseek', 'NEUTRAL')
        e = item.get('explanation_deepseek', 'Sin análisis')
        print(f"   [{i+1}] Sentimiento: {s} | Exp: {str(e)[:50]}...")

    # 3. Reporte y Visualización
    print("3. Generando Reporte...")
    
    os.makedirs('output', exist_ok=True)
    
    # Guardar CSV Granular Principal (Standard para todos los scrapers)
    import pandas as pd
    try:
        df_granular = pd.DataFrame(granular_results)
        df_granular.to_csv("output/sentiment_results_granular.csv", index=False, encoding='utf-8')
        print(f"   [CSV] Resultados Granulares guardados: output/sentiment_results_granular.csv")
    except Exception as e:
        print(f"   [Error] No se pudo guardar CSV granular: {e}")

    # Guardar CSV extra para comments separados (por compatibilidad solicitada)
    print("Saving separated sentiment CSVs...")
    sentiments_lists = { "positivos": [], "negativos": [], "neutros": [] }
    
    for item in granular_results:
        if item['type'] == 'COMMENT':
            s = item['sentiment'].upper()
            txt = item['text']
            # Buscar URL del padre
            p_idx = int(item['parent_id'].split('_')[1])
            p_url = "https://linkedin.com" # Placeholder, LinkedIn scraper doesn't fetch specific URL per post easily currently
            
            if s == "POSITIVO": sentiments_lists["positivos"].append([txt, p_url])
            elif s == "NEGATIVO": sentiments_lists["negativos"].append([txt, p_url])
            else: sentiments_lists["neutros"].append([txt, p_url])
            
    for s_type, rows in sentiments_lists.items():
        csv_name = f"output/comentarios_{s_type}_{args.query}.csv"
        try:
            with open(csv_name, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Comentario", "URL Post Original"])
                writer.writerows(rows)
            print(f"   Saved {len(rows)} {s_type} comments to: {csv_name}")
        except: pass

    # CSV Legacy
    csv_file = 'output/datos_extraidos_deepseek.csv'
    if data:
        keys = list(data[0].keys())
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
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
        plt.savefig('output/frecuencia_palabras.png')
        print("   [Gráfico] output/frecuencia_palabras.png")
    
    total_time = time.time() - start_total_time
    nlp_time = total_time - extraction_time
    
    # --- PERFORMANCE METRICS REPORT ---
    print("\n" + "="*50)
    print(f"       PERFORMANCE REPORT: {args.query.upper()}")
    print("="*50)
    print(f"Total Posts Extracted:  {len(data)}")
    print("-" * 50)
    print(f"1. Extraction Phase:    {extraction_time:.2f} seconds")
    print(f"2. NLP + LLM Analysis:  {nlp_time:.2f} seconds (Batch DeepSeek)")
    print("-" * 50)
    print(f"TOTAL EXECUTION TIME:   {total_time:.2f} seconds")
    print("="*50)
    
    # Calculate sentiment distribution
    import json
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    # Count from granular results (more accurate)
    for item in granular_results:
        s = item['sentiment'].lower()
        if 'positiv' in s: sentiment_distribution["positive"] += 1
        elif 'negativ' in s: sentiment_distribution["negative"] += 1
        else: sentiment_distribution["neutral"] += 1
    
    # Generate metrics JSON for master scraper
    metrics = {
        "social_network": "LinkedIn",
        "llm_used": "Grok",
        "query": args.query,
        "execution_times": {
            "scraping": round(extraction_time, 2),
            "text_processing": round(nlp_time, 2),
            "sentiment_analysis": round(nlp_time, 2),  # LLM analysis included in NLP time
            "total": round(total_time, 2)
        },
        "data_metrics": {
            "posts_extracted": len(data),
            "comments_extracted": 0,  # LinkedIn scraper doesn't extract comments separately
            "comments_analyzed": 0,
            "total_text_items": len(data)
        },
        "sentiment_distribution": sentiment_distribution,
        "performance_metrics": {
            "posts_per_second": round(len(data) / extraction_time if extraction_time > 0 else 0, 2),
            "comments_per_second": 0,
            "avg_time_per_post": round(extraction_time / len(data) if len(data) > 0 else 0, 2)
        }
    }
    
    # Save metrics JSON
    metrics_filename = f"output/metrics_{args.query}.json"
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
