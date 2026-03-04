"""
Script de prueba para verificar que el sistema funciona con 5 comentarios
Uso: python test_5_comments.py --query "test"
"""

import subprocess
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Probar con 5 comentarios')
    parser.add_argument('--query', type=str, default="test", help='Query de búsqueda')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🧪 PRUEBA: 5 COMENTARIOS")
    print("="*80)
    print(f"Query: {args.query}")
    print("="*80 + "\n")
    
    # Ejecutar master scraper con límites muy bajos para prueba rápida
    print("📊 Ejecutando scrapers con límites bajos (prueba)...")
    print("   --posts 2 --comments 1 = ~8 comentarios máximo")
    
    cmd = [
        sys.executable,
        "master_scraper.py",
        "--query", args.query,
        "--posts", "2",
        "--comments", "1"
    ]
    
    print(f"\nEjecutando: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n❌ Error ejecutando scrapers")
        return 1
    
    # Generar CSV unificado
    print("\n📋 Generando CSV unificado...")
    cmd_unified = [
        sys.executable,
        "generate_unified_csv.py",
        "--query", args.query
    ]
    
    print(f"Ejecutando: {' '.join(cmd_unified)}\n")
    result = subprocess.run(cmd_unified)
    
    if result.returncode != 0:
        print("\n❌ Error generando CSV unificado")
        return 1
    
    print("\n" + "="*80)
    print("✅ PRUEBA COMPLETADA")
    print("="*80)
    print(f"\nArchivo generado: formato_investigacion_{args.query.lower().replace(' ', '_')}.csv")
    print("Revisa el archivo para verificar que el formato es correcto\n")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
