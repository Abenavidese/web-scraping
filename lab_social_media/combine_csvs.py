"""
Script simple para combinar los formato_investigacion.csv que ya existen
"""
import pandas as pd
import os
import sys

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "test"
    user_id = "default"
    
    print(f"\nCombinando CSVs para query: {query}")
    
    # Buscar todos los formato_investigacion.csv
    csv_files = []
    base_path = f"users/{user_id}"
    
    networks = ["x", "facebook", "instagram", "linkedin"]
    
    for network in networks:
        csv_path = f"{base_path}/{network}/{query}/formato_investigacion.csv"
        if os.path.exists(csv_path):
            print(f"  [OK] Encontrado: {network}")
            csv_files.append((network, csv_path))
        else:
            print(f"  [SKIP] No encontrado: {network}")
    
    if not csv_files:
        print("\n[ERROR] No se encontraron archivos CSV")
        return 1
    
    # Combinar todos
    all_dfs = []
    for network, csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            all_dfs.append(df)
            print(f"  [OK] Leído {network}: {len(df)} filas")
        except Exception as e:
            print(f"  [ERROR] {network}: {e}")
    
    if not all_dfs:
        print("\n[ERROR] No se pudieron leer los CSVs")
        return 1
    
    # Concatenar
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    # Guardar
    output_file = f"formato_investigacion_{query}.csv"
    final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n[SUCCESS] CSV unificado generado: {output_file}")
    print(f"Total de comentarios: {len(final_df)}")
    print(f"\nDistribución por red social:")
    print(final_df['Red Social'].value_counts())
    
    return 0

if __name__ == "__main__":
    exit(main())
