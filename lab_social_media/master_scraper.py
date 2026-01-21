"""
Master Script para Ejecución Paralela de Scrapers de Redes Sociales
Práctica de Laboratorio - Computación Paralela
Ejecuta simultáneamente los scrapers de X, Instagram, Facebook y LinkedIn
"""

import multiprocessing
import subprocess
import time
import os
from datetime import datetime
import sys

class SocialMediaScraperManager:
    """Gestor principal para la ejecución paralela de scrapers"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.scrapers = {
            'X (Twitter)': {
                'dir': os.path.join(self.base_dir, 'x_scrapper'),
                'script': 'main.py',
                'color': '\033[94m'  # Azul
            },
            'Instagram': {
                'dir': os.path.join(self.base_dir, 'App_Paralela_Instagram'),
                'script': 'scraper.py',
                'color': '\033[95m'  # Magenta
            },
            'Facebook': {
                'dir': os.path.join(self.base_dir, 'App_Paralela_facebook'),
                'script': 'scraper.py',
                'color': '\033[96m'  # Cyan
            },
            'LinkedIn': {
                'dir': os.path.join(self.base_dir, 'linkedin_scrapper'),
                'script': 'main.py',
                'color': '\033[92m'  # Verde
            }
        }
        self.reset_color = '\033[0m'
        self.start_time = None
        self.end_time = None
        
    def print_header(self):
        """Imprime el encabezado del programa"""
        print("\n" + "="*80)
        print("  EXTRACCIÓN PARALELA DE DATOS DE REDES SOCIALES")
        print("  Práctica de Laboratorio - Computación Paralela")
        print("="*80)
        print(f"\n📅 Fecha de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Número de procesos paralelos: {len(self.scrapers)}")
        print(f"🌐 Redes sociales a procesar: {', '.join(self.scrapers.keys())}\n")
        print("="*80 + "\n")
    
    def run_scraper(self, name, config, search_query, num_posts, num_comments):
        """
        Ejecuta un scraper individual en un proceso separado
        
        Args:
            name (str): Nombre de la red social
            config (dict): Configuración del scraper (directorio y script)
            search_query (str): Tema de búsqueda
            num_posts (int): Número de posts a extraer
            num_comments (int): Número de comentarios por post
        
        Returns:
            dict: Resultado de la ejecución con tiempos y estado
        """
        process_start = time.time()
        color = config['color']
        reset = self.reset_color
        
        print(f"{color}[{name}] ▶️  Iniciando scraper...{reset}")
        
        try:
            # Cambiar al directorio del scraper
            script_path = os.path.join(config['dir'], config['script'])
            
            # Verificar que el script existe
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"Script no encontrado: {script_path}")
            
            # Construir comando con argumentos
            command = [
                sys.executable,
                config['script'],
                '--query', search_query,
                '--posts', str(num_posts),
                '--comments', str(num_comments)
            ]
            
            # Ejecutar el scraper
            result = subprocess.run(
                command,
                cwd=config['dir'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            process_end = time.time()
            execution_time = process_end - process_start
            
            if result.returncode == 0:
                print(f"{color}[{name}] ✅ Completado exitosamente en {execution_time:.2f}s{reset}")
                return {
                    'name': name,
                    'status': 'success',
                    'execution_time': execution_time,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                print(f"{color}[{name}] ❌ Error en la ejecución (código: {result.returncode}){reset}")
                print(f"{color}[{name}] Error: {result.stderr[:200]}{reset}")
                return {
                    'name': name,
                    'status': 'error',
                    'execution_time': execution_time,
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            process_end = time.time()
            execution_time = process_end - process_start
            print(f"{color}[{name}] ❌ Excepción: {str(e)}{reset}")
            return {
                'name': name,
                'status': 'exception',
                'execution_time': execution_time,
                'error': str(e)
            }
    
    def run_parallel(self):
        """Ejecuta todos los scrapers en paralelo usando multiprocessing"""
        self.print_header()
        
        # RECOGER PARÁMETROS UNA SOLA VEZ
        print("📝 CONFIGURACIÓN DE BÚSQUEDA")
        print("-" * 80)
        
        search_query = input("Ingrese el tema de búsqueda (Tema): ").strip()
        if not search_query:
            search_query = "Inteligencia Artificial"
            print(f"   Usando tema por defecto: {search_query}")
        
        try:
            num_posts = int(input("Número de posts a extraer por red social: ").strip())
        except ValueError:
            num_posts = 10
            print(f"   Usando valor por defecto: {num_posts} posts")
        
        try:
            num_comments = int(input("Número de comentarios por post: ").strip())
        except ValueError:
            num_comments = 5
            print(f"   Usando valor por defecto: {num_comments} comentarios")
        
        print("\n" + "="*80)
        print(f"✅ Configuración establecida:")
        print(f"   • Tema: {search_query}")
        print(f"   • Posts por red social: {num_posts}")
        print(f"   • Comentarios por post: {num_comments}")
        print("="*80 + "\n")
        
        self.start_time = time.time()
        
        print("🚀 Iniciando extracción paralela de datos...\n")
        
        # Crear un pool de procesos
        with multiprocessing.Pool(processes=len(self.scrapers)) as pool:
            # Ejecutar todos los scrapers en paralelo con los mismos parámetros
            results = pool.starmap(
                self.run_scraper,
                [(name, config, search_query, num_posts, num_comments) 
                 for name, config in self.scrapers.items()]
            )
        
        self.end_time = time.time()
        total_time = self.end_time - self.start_time
        
        # Mostrar resumen de resultados
        self.print_summary(results, total_time)
        
        return results
    
    def print_summary(self, results, total_time):
        """
        Imprime un resumen de los resultados de la ejecución
        
        Args:
            results (list): Lista de resultados de cada scraper
            total_time (float): Tiempo total de ejecución
        """
        print("\n" + "="*80)
        print("  RESUMEN DE EJECUCIÓN")
        print("="*80 + "\n")
        
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = len(results) - successful
        
        print(f"⏱️  Tiempo total de ejecución: {total_time:.2f} segundos")
        print(f"✅ Scrapers exitosos: {successful}/{len(results)}")
        print(f"❌ Scrapers con errores: {failed}/{len(results)}\n")
        
        print("-" * 80)
        print(f"{'Red Social':<15} {'Estado':<15} {'Tiempo (s)':<15}")
        print("-" * 80)
        
        for result in results:
            status_icon = "✅" if result['status'] == 'success' else "❌"
            status_text = result['status'].upper()
            exec_time = f"{result['execution_time']:.2f}"
            
            print(f"{result['name']:<15} {status_icon} {status_text:<13} {exec_time:<15}")
        
        print("-" * 80)
        
        # Calcular speedup teórico
        total_sequential = sum(r['execution_time'] for r in results)
        speedup = total_sequential / total_time if total_time > 0 else 0
        efficiency = (speedup / len(results)) * 100 if len(results) > 0 else 0
        
        print(f"\n📊 MÉTRICAS DE PARALELIZACIÓN:")
        print(f"   • Tiempo secuencial estimado: {total_sequential:.2f}s")
        print(f"   • Tiempo paralelo real: {total_time:.2f}s")
        print(f"   • Speedup: {speedup:.2f}x")
        print(f"   • Eficiencia: {efficiency:.2f}%")
        
        print("\n" + "="*80)
        print(f"📅 Fecha de finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        # Guardar log de resultados
        self.save_log(results, total_time)
    
    def save_log(self, results, total_time):
        """
        Guarda un log detallado de la ejecución
        
        Args:
            results (list): Lista de resultados de cada scraper
            total_time (float): Tiempo total de ejecución
        """
        log_dir = os.path.join(self.base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'execution_log_{timestamp}.txt')
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("LOG DE EJECUCIÓN PARALELA - SCRAPERS DE REDES SOCIALES\n")
            f.write("="*80 + "\n\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tiempo total: {total_time:.2f} segundos\n\n")
            
            for result in results:
                f.write("-" * 80 + "\n")
                f.write(f"RED SOCIAL: {result['name']}\n")
                f.write(f"Estado: {result['status']}\n")
                f.write(f"Tiempo de ejecución: {result['execution_time']:.2f}s\n")
                
                if result['status'] == 'success':
                    f.write(f"\nSalida:\n{result.get('stdout', 'N/A')[:500]}\n")
                elif result['status'] == 'error':
                    f.write(f"\nCódigo de error: {result.get('returncode', 'N/A')}\n")
                    f.write(f"Error:\n{result.get('stderr', 'N/A')[:500]}\n")
                else:
                    f.write(f"\nExcepción:\n{result.get('error', 'N/A')}\n")
                
                f.write("-" * 80 + "\n\n")
        
        print(f"📝 Log guardado en: {log_file}")


def main():
    """Función principal"""
    print("\n🎯 Iniciando Master Scraper...")
    
    # Verificar que estamos en Windows (para soporte de colores)
    if os.name == 'nt':
        os.system('color')
    
    # Crear instancia del gestor
    manager = SocialMediaScraperManager()
    
    # Ejecutar scrapers en paralelo
    try:
        results = manager.run_parallel()
        
        # Verificar si todos fueron exitosos
        all_success = all(r['status'] == 'success' for r in results)
        
        if all_success:
            print("🎉 ¡Todos los scrapers se ejecutaron exitosamente!")
            return 0
        else:
            print("⚠️  Algunos scrapers tuvieron errores. Revise el log para más detalles.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución interrumpida por el usuario.")
        return 2
    except Exception as e:
        print(f"\n\n❌ Error crítico: {str(e)}")
        return 3


if __name__ == "__main__":
    # Configurar multiprocessing para Windows
    multiprocessing.freeze_support()
    
    # Ejecutar programa principal
    exit_code = main()
    
    # Esperar antes de cerrar
    input("\n\nPresione ENTER para salir...")
    sys.exit(exit_code)
