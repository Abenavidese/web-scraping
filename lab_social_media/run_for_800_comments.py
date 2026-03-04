"""
Script para garantizar exactamente 800 comentarios
Ejecuta los scrapers con límites altos y luego filtra a 800 comentarios

Uso: python run_for_800_comments.py --query "María Elisa Padilla"
"""

import subprocess
import sys
import argparse
import pandas as pd
import os

def main():
    parser = argparse.ArgumentParser(description='Ejecutar scrapers para obtener 800 comentarios')
    parser.add_argument('--query', type=str, required=True, help='Query de búsqueda')
    parser.add_argument('--output', type=str, default=None, help='Archivo de salida (opcional)')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🎯 OBJETIVO: 800 COMENTARIOS")
    print("="*80)
    print(f"Query: {args.query}")
    print("="*80 + "\n")
    
    # Paso 1: Ejecutar master scraper con límites altos
    print("📊 Paso 1: Ejecutando scrapers con límites altos...")
    print("   (Esto garantiza que tengamos suficientes comentarios)")
    
    # Ejecutar con --posts 50 --comments 10 = ~2000 comentarios potenciales
    cmd = [
        sys.executable,
        "master_scraper.py",
        "--query", args.query,
        "--posts", "50",
        "--comments", "10"
    ]
    
    print(f"\nEjecutando: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    if result.returncode != 0:
        print("\n❌ Error ejecutando scrapers")
        return 1
    
    # Paso 2: Generar CSV unificado
    print("\n📋 Paso 2: Generando CSV unificado...")
    cmd_unified = [
        sys.executable,
        "generate_unified_csv.py",
        "--query", args.query
    ]
    
    if args.output:
        cmd_unified.extend(["--output", args.output])
    
    print(f"Ejecutando: {' '.join(cmd_unified)}\n")
    result = subprocess.run(cmd_unified, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    if result.returncode != 0:
        print("\n❌ Error generando CSV unificado")
        return 1
    
    # Paso 3: Filtrar a exactamente 800 comentarios
    print("\n✂️  Paso 3: Filtrando a exactamente 800 comentarios...")
    
    from shared.unified_csv_exporter import slugify
    query_slug = slugify(args.query)
    
    if args.output:
        csv_file = args.output
    else:
        csv_file = f"formato_investigacion_{query_slug}.csv"
    
    if not os.path.exists(csv_file):
        print(f"\n❌ No se encontró el archivo: {csv_file}")
        return 1
    
    # Leer CSV
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    
    print(f"\n📊 Comentarios totales: {len(df)}")
    
    if len(df) < 800:
        print(f"\n⚠️  ADVERTENCIA: Solo se encontraron {len(df)} comentarios (menos de 800)")
        print("   Considera ejecutar con límites más altos")
    else:
        # Filtrar a 800 comentarios (distribución equitativa por red social)
        print("\n🎯 Filtrando a exactamente 800 comentarios...")
        
        # Contar comentarios por red social
        counts = df['Red Social'].value_counts()
        print("\nDistribución original:")
        for network, count in counts.items():
            print(f"   {network}: {count} comentarios")
        
        # Calcular cuántos comentarios tomar de cada red (proporcional)
        total = len(df)
        target = 800
        
        filtered_dfs = []
        for network in counts.index:
            network_df = df[df['Red Social'] == network]
            # Proporción de esta red en el total
            proportion = len(network_df) / total
            # Cuántos comentarios tomar de esta red
            take = int(proportion * target)
            # Tomar los primeros N comentarios
            filtered_dfs.append(network_df.head(take))
        
        # Combinar
        df_filtered = pd.concat(filtered_dfs, ignore_index=True)
        
        # Si no llegamos a 800, agregar más de la red con más comentarios
        if len(df_filtered) < 800:
            remaining = 800 - len(df_filtered)
            largest_network = counts.index[0]
            extra = df[df['Red Social'] == largest_network].head(remaining + len(filtered_dfs[0]))
            df_filtered = pd.concat([df_filtered, extra.tail(remaining)], ignore_index=True)
        
        # Asegurar exactamente 800
        df_filtered = df_filtered.head(800)
        
        # Guardar
        output_file = f"formato_investigacion_800_{query_slug}.csv"
        df_filtered.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ CSV filtrado guardado: {output_file}")
        print(f"📊 Comentarios finales: {len(df_filtered)}")
        
        # Mostrar distribución final
        final_counts = df_filtered['Red Social'].value_counts()
        print("\nDistribución final:")
        for network, count in final_counts.items():
            print(f"   {network}: {count} comentarios")
        
        print("\n" + "="*80)
        print("✅ COMPLETADO: 800 COMENTARIOS LISTOS PARA EL INGENIERO")
        print("="*80)
        print(f"\n📁 Archivo final: {output_file}")
        print("🎓 Listo para entregar en el artículo académico\n")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
