"""
Script para obtener EXACTAMENTE 800 comentarios
Ejecuta scrapers, combina resultados y filtra a 800 comentarios exactos

Uso: python get_800_comments.py --query "María Elisa Padilla"
"""

import subprocess
import sys
import os
import pandas as pd
import argparse

def slugify(text):
    """Convert text to slug format"""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')

def main():
    parser = argparse.ArgumentParser(description='Obtener EXACTAMENTE 800 comentarios')
    parser.add_argument('--query', type=str, required=True, help='Query de búsqueda')
    
    args = parser.parse_args()
    query = args.query
    query_slug = slugify(query)
    
    print("\n" + "="*80)
    print("OBJETIVO: 800 COMENTARIOS EXACTOS")
    print("="*80)
    print(f"Query: {query}")
    print(f"Slug: {query_slug}")
    print("="*80 + "\n")
    
    # PASO 1: Ejecutar scrapers con límites altos
    print("[PASO 1/3] Ejecutando scrapers...")
    print("Parámetros: --posts 150 --comments 100")
    print("Esto garantiza capturar MUCHOS comentarios por post")
    print("Total potencial: ~60,000 comentarios (más que suficiente para 800)\n")
    
    cmd = [
        sys.executable,
        "master_scraper.py",
        "--query", query,
        "--posts", "150",  # AUMENTADO: 150 posts por red social
        "--comments", "100"  # 100 comentarios por post para asegurar 800+
    ]
    
    print(f"Ejecutando: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n[ERROR] Scrapers fallaron")
        return 1
    
    print("\n[OK] Scrapers completados\n")
    
    # PASO 2: Combinar CSVs
    print("[PASO 2/3] Combinando CSVs de todas las redes sociales...\n")
    
    csv_files = []
    base_path = "users/default"
    networks = ["x", "facebook", "instagram", "linkedin"]
    
    for network in networks:
        csv_path = f"{base_path}/{network}/{query_slug}/formato_investigacion.csv"
        if os.path.exists(csv_path):
            print(f"  [OK] Encontrado: {network}")
            csv_files.append((network, csv_path))
        else:
            print(f"  [SKIP] No encontrado: {network}")
    
    if not csv_files:
        print("\n[ERROR] No se encontraron archivos CSV")
        return 1
    
    # Leer y combinar todos los CSVs
    all_dfs = []
    for network, csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            all_dfs.append(df)
            print(f"  [OK] Leído {network}: {len(df)} comentarios")
        except Exception as e:
            print(f"  [ERROR] {network}: {e}")
    
    if not all_dfs:
        print("\n[ERROR] No se pudieron leer los CSVs")
        return 1
    
    # Concatenar todos
    df_combined = pd.concat(all_dfs, ignore_index=True)
    
    print(f"\n[OK] Total de comentarios recolectados: {len(df_combined)}")
    print("\nDistribución original:")
    print(df_combined['Red Social'].value_counts())
    
    # PASO 3: Filtrar a EXACTAMENTE 800 comentarios
    print(f"\n[PASO 3/3] Filtrando a EXACTAMENTE 800 comentarios...\n")
    
    if len(df_combined) < 800:
        print(f"[ADVERTENCIA] Solo se encontraron {len(df_combined)} comentarios (menos de 800)")
        print("Guardando todos los comentarios disponibles...")
        df_final = df_combined
    else:
        # Distribución proporcional por red social
        counts = df_combined['Red Social'].value_counts()
        total = len(df_combined)
        target = 800
        
        print("Calculando distribución proporcional...")
        filtered_dfs = []
        
        for network in counts.index:
            network_df = df_combined[df_combined['Red Social'] == network]
            # Proporción de esta red en el total
            proportion = len(network_df) / total
            # Cuántos comentarios tomar de esta red
            take = int(proportion * target)
            
            # Tomar los primeros N comentarios
            filtered_dfs.append(network_df.head(take))
            print(f"  {network}: {take} comentarios ({proportion*100:.1f}%)")
        
        # Combinar
        df_final = pd.concat(filtered_dfs, ignore_index=True)
        
        # Ajustar si no llegamos a 800 exactos
        if len(df_final) < 800:
            remaining = 800 - len(df_final)
            print(f"\n  Agregando {remaining} comentarios adicionales...")
            
            # Tomar comentarios adicionales de la red con más datos
            largest_network = counts.index[0]
            network_df = df_combined[df_combined['Red Social'] == largest_network]
            
            # Tomar comentarios que no están ya incluidos
            already_included = len(filtered_dfs[0])
            extra = network_df.iloc[already_included:already_included + remaining]
            df_final = pd.concat([df_final, extra], ignore_index=True)
        
        # Asegurar EXACTAMENTE 800
        df_final = df_final.head(800)
    
    # Guardar archivo final
    output_file = f"formato_investigacion_800_{query_slug}.csv"
    df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print("\n" + "="*80)
    print("COMPLETADO: 800 COMENTARIOS EXACTOS")
    print("="*80)
    print(f"\nArchivo generado: {output_file}")
    print(f"Total de comentarios: {len(df_final)}")
    
    print("\nDistribución final por red social:")
    final_counts = df_final['Red Social'].value_counts()
    for network, count in final_counts.items():
        print(f"  {network}: {count} comentarios")
    
    print("\nDistribución de sentimientos:")
    sentiment_counts = df_final['Sentimiento'].value_counts()
    for sentiment, count in sentiment_counts.items():
        print(f"  {sentiment}: {count} comentarios")
    
    print("\n" + "="*80)
    print("LISTO PARA ENTREGAR AL INGENIERO")
    print("="*80)
    print(f"\nArchivo: {output_file}")
    print("Formato: Red Social | Publicación | Comentario | Sentimiento | Explicación | Términos")
    print("\n")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
