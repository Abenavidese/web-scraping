import asyncio
import argparse
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from scrapers.linkedin_scraper import LinkedInScraper
from utils.nlp_processor import NLPProcessor
import config # Importar archivo de configuración
import time # Para medir tiempos de ejecución

async def main():
    parser = argparse.ArgumentParser(description="Extracción y Procesamiento de LinkedIn")
    # Argumentos compatibles con master_scraper.py
    parser.add_argument("--query", type=str, default=None, help="Término de búsqueda")
    parser.add_argument("--posts", type=int, default=None, help="Número de posts a extraer")
    parser.add_argument("--comments", type=int, default=None, help="Número de comentarios por post")
    # Mantener compatibilidad con --limit (alias de --posts)
    parser.add_argument("--limit", type=int, default=None, help="Número de posts a extraer (alias de --posts)")
    
    args = parser.parse_args()

    start_total_time = time.time() # Inicio Cronómetro Total

    # Determinar número de posts (prioridad: --posts, luego --limit, luego default)
    if args.posts is not None:
        num_posts = args.posts
    elif args.limit is not None:
        num_posts = args.limit
    else:
        num_posts = config.DEFAULT_LIMIT
    
    # Determinar número de comentarios
    max_comments = args.comments if args.comments is not None else 0

    # Usar query del argumento o default de config (sin input interactivo)
    if not args.query:
        args.query = config.DEFAULT_QUERY

    print(f"--- Iniciando Proceso para: '{args.query}' ---")
    print(f"--- Configuración: {num_posts} posts | Max {max_comments} comentarios/post ---")
    
    # Validar Cookie
    if config.LINKEDIN_LI_AT_COOKIE == "PEGAR_TU_COOKIE_LI_AT_AQUI" or len(config.LINKEDIN_LI_AT_COOKIE) < 10:
        print("\n[!] ERROR: No has pegado tu cookie 'li_at' en config.py.")
        return

    # 1. Fase de Extracción
    # Usamos Cookie Auth
    scraper = LinkedInScraper(li_at_cookie=config.LINKEDIN_LI_AT_COOKIE, headless=False)
    
    print("1. Extrayendo datos de LinkedIn (Simulado vía Google para seguridad)...")
    data = await scraper.extract(args.query, limit=num_posts, max_comments=max_comments)
    
    if not data:
        print("No se encontraron datos. Verifique la conexión o los bloqueos.")
        return

    print(f"   -> {len(data)} items extraídos.")
    extraction_time = time.time() - start_total_time
    print(f"   [Tiempo Extracción]: {extraction_time:.2f} segundos")


    # 2. Fase de Procesamiento NLP
    print("2. Ejecutando Pipeline NLP (Limpieza, Tokenización, Sentiment)...")
    nlp_start_time = time.time()
    processor = NLPProcessor(language='spanish')
    all_tokens = []

    for item in data:
        # 1. LIMPIEZA Y NORMALIZACIÓN (Requisito 1 de la guía)
        # Usamos el procesador para quitar URLs, emojis, puntuación, etc. ANTES de guardar en CSV
        raw_content = item['content'].replace('\n', ' ').replace('\r', '').strip()
        clean_content = processor.clean_text(raw_content)
        
        # Actualizamos el item para que en el CSV se guarde LIMPIO
        item['content'] = clean_content
        
        # LIMPIAR COMENTARIOS TAMBIÉN
        # Unimos con pipe '|' para que sea legible en CSV
        if isinstance(item.get('comments'), list):
            cleaned_comments = [processor.clean_text(c) for c in item['comments']]
            # Filtramos vacíos tras limpieza
            cleaned_comments = [c for c in cleaned_comments if c]
            if cleaned_comments:
                item['comments'] = " | ".join(cleaned_comments)
            else:
                item['comments'] = "Sin comentarios"
        
        # 2., 3., 4. Tokenización, Stopwords, Stemming (Requisitos 2-4)
        tokens = processor.process(clean_content)
        all_tokens.extend(tokens)
        
        # Análisis de Sentimiento (Requisito extra)
        item['sentiment'] = processor.analyze_sentiment(clean_content)
        
        print(f"   Original: {raw_content[:20]}... -> Limpio: {clean_content[:20]}... -> Sentimiento: {item['sentiment']}")

    # 3. Generación de Bolsa de Palabras y Visualización
    print("3. Generando Visualización y Reporte...")
    
    # --- NUEVO: Guardar CSV ---
    import csv
    import os
    os.makedirs('output', exist_ok=True)
    
    csv_file = 'output/datos_extraidos.csv'
    if data:
        keys = data[0].keys()
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        print(f"   [CSV] Datos guardados exitosamente en: {csv_file}")
    # --------------------------

    # Crear Bolsa de Palabras (usando tokens ya procesados arriba)
    bow = processor.get_bag_of_words(all_tokens)
    
    if not bow:
        print("   [NLP] No se pudieron generar tokens sufientes para el gráfico.")
        return

    common_words = bow.most_common(10)
    print("   Top 10 Palabras:", common_words)

    if common_words:
        words, counts = zip(*common_words)
        
        plt.figure(figsize=(10, 6))
        plt.bar(words, counts, color='skyblue')
        plt.xlabel('Palabras (Stemmed)')
        plt.ylabel('Frecuencia')
        plt.title(f'Bolsa de Palabras: {args.query}')
        plt.xticks(rotation=45)
        
        import os
        os.makedirs('output', exist_ok=True)
        output_file = 'output/frecuencia_palabras.png'
        plt.savefig(output_file)
        print(f"   Gráfico guardado en: {output_file}")
        plt.close()
        
        # Generar WordCloud
        print("   Generando WordCloud...")
        text_corpus = ' '.join(all_tokens)
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text_corpus)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Nube de Palabras: {args.query}')
        wordcloud_file = 'output/wordcloud_linkedin.png'
        plt.savefig(wordcloud_file)
        print(f"   WordCloud guardado en: {wordcloud_file}")
        plt.close()
        # plt.show() # Comentado para no bloquear si corre en terminal
    else:
        print("No hay suficientes palabras para graficar.")

    top_words_time = time.time()
    
    nlp_time = top_words_time - nlp_start_time
    print(f"   [Tiempo NLP + Visualización]: {nlp_time:.2f} segundos")

    print("\n--- Proceso Finalizado Exitosamente ---")
    total_time = top_words_time - start_total_time
    print(f"   [Tiempo Total]: {total_time:.2f} segundos")
    print("Revise la carpeta 'output' para ver los resultados.")

if __name__ == "__main__":
    asyncio.run(main())
