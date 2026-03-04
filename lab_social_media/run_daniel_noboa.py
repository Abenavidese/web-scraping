# -*- coding: utf-8 -*-
"""
Script helper para ejecutar master_scraper de forma no interactiva
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from master_scraper import SocialMediaScraperManager

if __name__ == "__main__":
    manager = SocialMediaScraperManager()
    
    # Configuración
    query = "Daniel Noboa"
    num_posts = 10
    num_comments = 5
    
    print(f"🚀 Ejecutando scraping paralelo...")
    print(f"   Tema: {query}")
    print(f"   Posts: {num_posts}")
    print(f"   Comentarios por post: {num_comments}")
    print()
    
    # Ejecutar en modo paralelo
    results, total_time = manager.run_parallel(
        query=query,
        posts=num_posts,
        comments=num_comments
    )
    
    print(f"\n✅ Ejecución completada en {total_time:.2f}s")
    print(f"   Revisa el directorio 'runs/' para ver los archivos generados")
