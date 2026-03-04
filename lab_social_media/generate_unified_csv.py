"""
Script Post-Procesador: Genera CSV Unificado después de ejecutar scrapers
Uso: python generate_unified_csv.py --query "María Elisa Padilla"

Este script busca los archivos de salida de los 4 scrapers y genera
un CSV unificado en el formato requerido por el ingeniero.
"""

import os
import sys
import argparse

# Agregar el directorio shared al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.unified_csv_exporter import (
    convert_x_twitter_to_unified,
    convert_instagram_to_unified,
    convert_facebook_to_unified,
    convert_linkedin_to_unified,
    slugify
)

def main():
    parser = argparse.ArgumentParser(description='Generar CSV unificado desde resultados de scrapers')
    parser.add_argument('--query', type=str, required=True, help='Query de búsqueda usado en los scrapers')
    parser.add_argument('--user-id', type=str, default='default', help='ID de usuario (default: "default")')
    parser.add_argument('--output', type=str, default=None, help='Archivo de salida (opcional)')
    
    args = parser.parse_args()
    
    query_slug = slugify(args.query)
    user_id = args.user_id
    
    print("\n" + "="*80)
    print(f"🔄 GENERANDO CSV UNIFICADO - Formato de Investigación")
    print("="*80)
    print(f"📝 Query: {args.query}")
    print(f"📂 Query Slug: {query_slug}")
    print(f"👤 User ID: {user_id}")
    print("="*80)
    
    # Determinar archivo de salida
    if args.output:
        final_output = args.output
    else:
        final_output = f"formato_investigacion_{query_slug}.csv"
    
    # Archivos temporales para cada red social
    temp_files = []
    
    # 1. X (Twitter)
    print("\n[1/4] Procesando X (Twitter)...")
    x_input = f"users/{user_id}/x/{query_slug}/sentiment_results.csv"
    if os.path.exists(x_input):
        x_output = f"temp_x_{query_slug}.csv"
        try:
            convert_x_twitter_to_unified(x_input, x_output)
            temp_files.append(x_output)
            print(f"   ✅ X (Twitter) procesado")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
    else:
        print(f"   ⚠️  No encontrado: {x_input}")
    
    # 2. Instagram
    print("\n[2/4] Procesando Instagram...")
    # Intentar diferentes posibles nombres de archivo
    ig_possible_paths = [
        f"users/{user_id}/instagram/{query_slug}/sentiment_results_{query_slug}.csv",
        f"users/{user_id}/instagram/{query_slug}/sentiment_results.csv",
    ]
    
    ig_found = False
    for ig_input in ig_possible_paths:
        if os.path.exists(ig_input):
            ig_output = f"temp_instagram_{query_slug}.csv"
            try:
                convert_instagram_to_unified(ig_input, ig_output)
                temp_files.append(ig_output)
                print(f"   ✅ Instagram procesado")
                ig_found = True
                break
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
    
    if not ig_found:
        print(f"   ⚠️  No encontrado en: {ig_possible_paths}")
    
    # 3. Facebook
    print("\n[3/4] Procesando Facebook...")
    fb_input = f"users/{user_id}/facebook/{query_slug}/datos_extraidos_deepseek.csv"
    if os.path.exists(fb_input):
        fb_output = f"temp_facebook_{query_slug}.csv"
        try:
            convert_facebook_to_unified(fb_input, fb_output)
            temp_files.append(fb_output)
            print(f"   ✅ Facebook procesado")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
    else:
        print(f"   ⚠️  No encontrado: {fb_input}")
    
    # 4. LinkedIn
    print("\n[4/4] Procesando LinkedIn...")
    li_input = f"users/{user_id}/linkedin/{query_slug}/datos_extraidos_deepseek.csv"
    if os.path.exists(li_input):
        li_output = f"temp_linkedin_{query_slug}.csv"
        try:
            convert_linkedin_to_unified(li_input, li_output)
            temp_files.append(li_output)
            print(f"   ✅ LinkedIn procesado")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
    else:
        print(f"   ⚠️  No encontrado: {li_input}")
    
    # Combinar todos los archivos temporales
    if not temp_files:
        print("\n❌ No se encontraron archivos de scrapers para procesar.")
        print("   Asegúrate de haber ejecutado los scrapers primero.")
        return
    
    print(f"\n🔗 Combinando {len(temp_files)} archivos...")
    
    import pandas as pd
    
    all_dfs = []
    for temp_file in temp_files:
        try:
            df = pd.read_csv(temp_file, encoding='utf-8-sig')
            all_dfs.append(df)
            os.remove(temp_file)  # Limpiar archivo temporal
        except Exception as e:
            print(f"   ⚠️  Error leyendo {temp_file}: {e}")
    
    if not all_dfs:
        print("\n❌ No se pudieron leer los archivos temporales.")
        return
    
    # Concatenar todos los DataFrames
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    # Guardar archivo final
    final_df.to_csv(final_output, index=False, encoding='utf-8-sig')
    
    print("\n" + "="*80)
    print("✅ CSV UNIFICADO GENERADO EXITOSAMENTE")
    print("="*80)
    print(f"📁 Archivo: {final_output}")
    print(f"📊 Total de filas: {len(final_df)}")
    print(f"\n📈 Distribución por red social:")
    print(final_df['Red Social'].value_counts())
    print(f"\n💭 Distribución de sentimientos:")
    print(final_df['Sentimiento'].value_counts())
    print("="*80)
    print(f"\n✅ Listo para entregar al ingeniero!")

if __name__ == "__main__":
    main()
