# -*- coding: utf-8 -*-
"""
Script para ejecutar scraping masivo de Daniel Noboa
1000 posts, 1000 comentarios
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from master_scraper import SocialMediaScraperManager

if __name__ == "__main__":
    manager = SocialMediaScraperManager()
    
    # Configuración MASIVA
    query = "Daniel Noboa"
    num_posts = 1000
    num_comments = 1000
    
    print("="*80)
    print("🚀 SCRAPING MASIVO - DANIEL NOBOA")
    print("="*80)
    print(f"   Tema: {query}")
    print(f"   Posts: {num_posts}")
    print(f"   Comentarios por post: {num_comments}")
    print(f"   ⚠️  ADVERTENCIA: Este proceso puede tomar MUCHO tiempo")
    print(f"   ⚠️  Se extraerán potencialmente miles de comentarios")
    print("="*80)
    print()
    
    # Ejecutar en modo paralelo
    print("⏳ Iniciando scraping paralelo masivo...")
    print("   Esto puede tomar varios minutos o incluso horas...")
    print()
    
    results, total_time = manager.run_parallel(
        query=query,
        posts=num_posts,
        comments=num_comments
    )
    
    print()
    print("="*80)
    print(f"✅ SCRAPING MASIVO COMPLETADO")
    print(f"   Tiempo total: {total_time:.2f}s ({total_time/60:.2f} minutos)")
    print(f"   Revisa el directorio 'runs/' para ver los archivos generados")
    print("="*80)
