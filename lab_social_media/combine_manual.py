import pandas as pd
import os
import glob

def main():
    import argparse
    from slugify import slugify

    parser = argparse.ArgumentParser(description='Combinar CSVs manuales')
    parser.add_argument('--query', type=str, required=True, help='Query slug (e.g. elipadillacardoso, maeli_cuenca)')
    args = parser.parse_args()
    
    # Try to use the query as is first, if not found then slugify
    # But usually folder structure uses slugified names. 
    # Let's assume input needs to be checked.
    
    # Check if folder exists for raw query
    if os.path.exists(f"users/default/x/{args.query}"):
        query_slug = args.query
    else:
        query_slug = slugify(args.query)

    base_path = "users/default"
    networks = ["x", "facebook", "instagram", "linkedin"]
    
    print(f"Buscando datos para: {query_slug}")
    
    all_dfs = []
    
    for network in networks:
        # Try both "formato_investigacion.csv" and other potential CSVs
        path_pattern = f"{base_path}/{network}/{query_slug}/*.csv"
        files = glob.glob(path_pattern)
        
        for file_path in files:
            try:
                # Skip intermediate or metadata files if possible, prefer standard ones
                if "sentiment" in file_path or "processed" in file_path:
                    continue
                    
                print(f"Leyendo: {file_path}")
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                
                # Normalize columns if needed
                # Add mapping logic if we found discrepancies
                rename_map = {
                    'Text': 'Comentario',
                    'Comment': 'Comentario',
                    'comment_text': 'Comentario',
                    'content': 'Comentario',
                    'Post': 'Publicación',
                    'post_caption': 'Publicación',
                    'Sentiment': 'Sentimiento',
                    'sentiment': 'Sentimiento',
                    'Explanation': 'Explicación',
                    'explanation': 'Explicación',
                    'sentiment_reasoning': 'Explicación',
                    'terms': 'Términos'
                }
                df.rename(columns=rename_map, inplace=True)

                if 'Red Social' not in df.columns:
                    df['Red Social'] = network.capitalize()
                    
                all_dfs.append(df)
            except Exception as e:
                print(f"Error leyendo {file_path}: {e}")
                
    if not all_dfs:
        print("No se encontraron datos.")
        return

    combined_df = pd.concat(all_dfs, ignore_index=True)
    total_found = len(combined_df)
    print(f"\nTotal encontrado: {total_found}")
    
    # Ensure columns exist and enforce order
    required_cols = ['Red Social', 'Publicación', 'Comentario', 'Sentimiento', 'Explicación', 'Términos']
    for col in required_cols:
        if col not in combined_df.columns:
            combined_df[col] = ''
            
    # STRICTLY select only these columns
    combined_df = combined_df[required_cols]

    # Generate output filename dynamically
    # Clean slug for filename (upper case, replace - with _)
    filename_base = query_slug.upper().replace('-', '_')
    output_final = f"{filename_base}.csv"
    
    combined_df.to_csv(output_final, index=False, encoding='utf-8-sig')
    print(f"Guardado archivo final formateado: {output_final}")
    
    if total_found > 800:
        output_800 = f"{filename_base}_800.csv"
        combined_df.head(800).to_csv(output_800, index=False, encoding='utf-8-sig')
        print(f"Guardado 800: {output_800}")

if __name__ == "__main__":
    main()
