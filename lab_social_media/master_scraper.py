"""
Master Script para Ejecución Paralela de Scrapers de Redes Sociales
Práctica de Laboratorio - Computación Paralela
Ejecuta simultáneamente los scrapers de X, Instagram, Facebook y LinkedIn
"""
# -*- coding: utf-8 -*-

import multiprocessing
import subprocess
import time
import os
from datetime import datetime
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import platform
try:
    import psutil
except ImportError:
    psutil = None

# Import academic metrics collector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.academic_metrics import AcademicMetricsCollector

# Fix Windows encoding issues for emojis
if sys.platform == 'win32':
    import io
    # Only wrap if not already wrapped
    if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except:
            pass
    if not isinstance(sys.stderr, io.TextIOWrapper) or sys.stderr.encoding != 'utf-8':
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except:
            pass

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
                'dir': os.path.join(self.base_dir, 'linkedin_scraper'),
                'script': 'main.py',
                'color': '\033[92m'  # Verde
            }
        }
        self.reset_color = '\033[0m'
        self.start_time = None
        self.end_time = None
        
    def get_system_info(self):
        """Obtiene información básica del hardware"""
        info = {
            "system": platform.system(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "cpu_count": multiprocessing.cpu_count(),
            "ram": "Unknown"
        }
        
        if psutil:
            try:
                ram = psutil.virtual_memory()
                info["ram"] = f"{round(ram.total / (1024**3), 1)} GB"
            except:
                pass
        
        return info
    
    def run_sequential(self, query=None, posts=None, comments=None, target_comments=None, max_posts=None):
        """Ejecuta todos los scrapers secuencialmente (para comparación)"""
        self.print_header(mode="SECUENCIAL")
        
        # RECOGER PARÁMETROS UNA SOLA VEZ (Si no se pasaron)
        if not query:
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
        else:
            search_query = query
            num_posts = posts
            num_comments = comments
            
        print(f"✅ Configuración establecida:")
        print(f"   • Tema: {search_query}")
        if target_comments:
            print(f"   • MODO: Basado en comentarios")
            print(f"   • Objetivo de comentarios: {target_comments}")
            print(f"   • Máximo de posts: {max_posts}")
        else:
            print(f"   • Posts por red social: {num_posts}")
            print(f"   • Comentarios por post: {num_comments}")
        print("="*80 + "\n")
        
        # Initialize academic metrics collector
        academic_metrics = AcademicMetricsCollector()
        platform_names = ['x', 'instagram', 'facebook', 'linkedin']
        academic_metrics.start_run(
            query=search_query,
            mode="sequential",
            platforms=platform_names,
            n_processes=1  # Sequential = 1 process at a time
        )
        
        self.start_time = time.time()
        
        print("🚀 Iniciando extracción SECUENCIAL de datos...\n")
        
        results = []
        
        for name, config in self.scrapers.items():
            print(f"{config['color']}[{name}] ▶️  Iniciando scraper (Modo Secuencial)...{self.reset_color}")
            
            # Record platform start
            network_name = self._get_platform_key(name)
            academic_metrics.record_platform_start(network_name)
            
            # Ejecutar scraper (usando la misma función run_scraper pero síncronamente)
            # Pasamos None como queue porque no necesitamos comunicación entre procesos
            result = self.run_scraper(name, config, search_query, num_posts, num_comments, target_comments, max_posts, None)
            
            if result['status'] == 'success':
                execution_time = result['execution_time']
                print(f"{config['color']}[{name}] ✅ Completado exitosamente en {execution_time:.2f}s{self.reset_color}")
                
                # Collect metrics
                if result.get('metrics'):
                    metrics = result['metrics']
                    data_metrics = metrics.get('data_metrics', {})
                    exec_times = metrics.get('execution_times', {})
                    sentiment_dist = metrics.get('sentiment_distribution', {})
                    
                    posts = data_metrics.get('posts_extracted', 0)
                    comments = data_metrics.get('comments_extracted', 0)
                    
                    academic_metrics.record_platform_end(
                        platform=network_name,
                        posts=posts,
                        comments=comments,
                        errors=0,
                        retries=0
                    )
                    
                    academic_metrics.record_preprocessing_time(exec_times.get('text_processing', 0))
                    academic_metrics.record_llm_time(exec_times.get('sentiment_analysis', 0))
                    
                    for sentiment, count in sentiment_dist.items():
                        for _ in range(count):
                            academic_metrics.add_sentiment_result(sentiment)
            else:
                print(f"{config['color']}[{name}] ❌ Falló o tuvo errores{self.reset_color}")
                if 'stderr' in result:
                     print(f"{config['color']}[{name}] Error: {result['stderr'][:200]}...{self.reset_color}")
                academic_metrics.record_error(network_name, "execution_failed", result.get('error', ''))
            
            results.append(result)
        
        self.end_time = time.time()
        total_time = self.end_time - self.start_time
        
        # End academic metrics
        academic_metrics.end_run()
        
        # Consolidar métricas
        consolidated_metrics = self.consolidate_metrics(results, total_time, search_query)
        # Forzar modo secuencial en métricas
        consolidated_metrics['parallel_execution']['mode'] = 'SEQUENTIAL'
        consolidated_metrics['parallel_execution']['speedup'] = 1.0
        consolidated_metrics['parallel_execution']['efficiency'] = 100.0
        
        # Mostrar resumen de resultados
        self.print_summary(results, total_time)
        
        # Generar reportes de métricas
        self.generate_metrics_reports(consolidated_metrics)
        
        # Export academic metrics
        print("\n" + "="*80)
        print("📊 EXPORTANDO MÉTRICAS ACADÉMICAS (SECUENCIAL)")
        print("="*80)
        files = academic_metrics.export_all()
        print(f"\n✅ Archivos académicos generados:")
        print(f"   📊 Métricas: {files['metrics']}")
        if files['dataset']:
            print(f"   📄 Dataset: {files['dataset']}")
        print(f"   📝 Log: {files['log']}")
        print("\n" + academic_metrics.get_summary())
        
        return results, total_time # Return tuple for comparison
    
    
    def generate_validation_sample(self, search_query):
        """Genera un archivo de validación con muestras aleatorias"""
        import random
        
        user_id = str(os.getenv("USER_ID", "default"))
        query_slug = search_query.lower() # Simple approximation, better to import slugify if needed
        query_slug = ''.join(c if c.isalnum() else '_' for c in query_slug).strip('_')
        
        output_data = []
        
        # Paths to check based on scraper structure
        paths = {
            "Facebook": os.path.join("..", "users", user_id, "facebook", query_slug, f"metrics.json"),
            "Instagram": os.path.join("..", "users", user_id, "instagram", query_slug, f"metrics.json"),
            "X (Twitter)": os.path.join("..", "users", user_id, "x", query_slug, f"metrics.json"),
            "LinkedIn": os.path.join("..", "users", user_id, "linkedin", query_slug, f"metrics.json")
        }
        
        # We need to find the CSVs really, metrics.json tells us it worked
        # Facebook: datos_extraidos_deepseek.csv
        # Instagram: sentiment_results_{query}.csv or processed_{query}.csv containing sentiments?
        # Actually each scraper saves a final result.
        
        print("\n🔍 Generando muestra de validación...")
        
        sample_file = os.path.join(self.base_dir, 'logs', f'validation_sample_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(f"MUESTRA DE VALIDACIÓN MANUAL\n")
            f.write(f"Fecha: {datetime.now()}\n")
            f.write(f"Query: {search_query}\n")
            f.write("="*80 + "\n\n")
            
            for network, metrics_path in paths.items():
                # Construct data path based on known structure from scrapers
                base_path = os.path.dirname(metrics_path)
                data_path = ""
                
                # Intentar adivinar el nombre del archivo de resultados de cada red
                if "facebook" in network.lower():
                    data_path = os.path.join(base_path, "datos_extraidos_deepseek.csv")
                elif "instagram" in network.lower():
                    data_path = os.path.join(base_path, f"sentiment_results_{query_slug}.csv") 
                elif "twitter" in network.lower() or "x" in network.lower():
                     data_path = os.path.join(base_path, "sentiment_results.csv")
                elif "linkedin" in network.lower():
                    data_path = os.path.join(base_path, "datos_extraidos_deepseek.csv")
                
                full_path = os.path.abspath(os.path.join(self.base_dir, data_path))
                
                if os.path.exists(full_path):
                     try:
                         import csv
                         with open(full_path, 'r', encoding='utf-8', errors='replace') as csvfile:
                             reader = list(csv.DictReader(csvfile))
                             if reader:
                                 # Select 5 random samples
                                 samples = random.sample(reader, min(5, len(reader)))
                                 
                                 f.write(f"--- {network} (Muestras: {len(samples)}) ---\n")
                                 for i, row in enumerate(samples):
                                     # Extract sentiment and text
                                     # Column names vary: 'sentiment', 'sentiment_deepseek', 'content', 'text', 'caption_snippet'
                                     
                                     sentiment = row.get('sentiment') or row.get('sentiment_deepseek') or "N/A"
                                     text = row.get('content') or row.get('text') or row.get('caption_snippet') or row.get('clean_text') or "N/A"
                                     explanation = row.get('explanation_deepseek') or row.get('sentiment_reasoning') or row.get('reasoning') or ""
                                     
                                     f.write(f"[{i+1}] Sentimiento: {sentiment}\n")
                                     if explanation:
                                         f.write(f"    Explicación: {explanation[:100]}...\n")
                                     f.write(f"    Texto: {text[:150].replace(chr(10), ' ')}...\n\n")
                             else:
                                 f.write(f"--- {network}: Archivo CSV vacío ---\n\n")
                     except Exception as e:
                         f.write(f"--- {network}: Error leyendo CSV ({str(e)}) ---\n\n")
                else:
                    f.write(f"--- {network}: No se encontró archivo de resultados ({data_path}) ---\n\n")
        
        print(f"📄 Muestra de validación guardada en: {sample_file}")

    def _run_scraper_wrapper(self, index, name, config, search_query, num_posts, num_comments, target_comments, max_posts, progress_queue, results_dict):
        """
        Wrapper para ejecutar un scraper y guardar su resultado
        
        Args:
            index (int): Índice del scraper
            name (str): Nombre de la red social
            config (dict): Configuración del scraper
            search_query (str): Tema de búsqueda
            num_posts (int): Número de posts (modo antiguo)
            num_comments (int): Número de comentarios (modo antiguo)
            target_comments (int): Número objetivo de comentarios (modo nuevo)
            max_posts (int): Máximo de posts (modo nuevo)
            progress_queue (Queue): Cola para comunicar progreso
            results_dict (dict): Diccionario compartido para guardar resultados
        """
        result = self.run_scraper(name, config, search_query, num_posts, num_comments, target_comments, max_posts, progress_queue)
        results_dict[index] = result
        
    def print_header(self, mode="PARALELO"):
        """Imprime el encabezado del programa"""
        info = self.get_system_info()
        
        print("\n" + "="*80)
        print(f"  EXTRACCIÓN DE DATOS DE REDES SOCIALES - MODO {mode}")
        print("  Práctica de Laboratorio - Computación Paralela y Avanzada")
        print("="*80)
        print(f"\n📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💻 Sistema: {info['system']} {info['machine']}")
        print(f"🧠 CPU: {info['processor']} ({info['cpu_count']} núcleos)")
        print(f"💾 RAM: {info['ram']}")
        print(f"🔧 Procesos: {len(self.scrapers)} | Modo: {mode}")
        print("="*80 + "\n")
    
    def _get_platform_key(self, display_name: str) -> str:
        """
        Convert display name to platform key.
        
        Args:
            display_name: Display name like 'X (Twitter)', 'Instagram', etc.
        
        Returns:
            Platform key like 'x', 'instagram', 'facebook', 'linkedin'
        """
        mapping = {
            'X (Twitter)': 'x',
            'Instagram': 'instagram',
            'Facebook': 'facebook',
            'LinkedIn': 'linkedin'
        }
        return mapping.get(display_name, display_name.lower())
    
    def run_scraper(self, name, config, search_query, num_posts, num_comments, target_comments, max_posts, progress_queue=None):
        """
        Ejecuta un scraper individual en un proceso separado
        
        Args:
            name (str): Nombre de la red social
            config (dict): Configuración del scraper (directorio y script)
            search_query (str): Tema de búsqueda
            num_posts (int): Número de posts a extraer (modo antiguo)
            num_comments (int): Número de comentarios por post (modo antiguo)
            target_comments (int): Número objetivo de comentarios (modo nuevo)
            max_posts (int): Máximo de posts (modo nuevo)
            progress_queue (Queue): Cola para comunicar progreso (opcional)
        
        Returns:
            dict: Resultado de la ejecución con tiempos y estado
        """
        process_start = time.time()
        color = config['color']
        reset = self.reset_color
        
        # Enviar mensaje de inicio
        if progress_queue:
            progress_queue.put(('start', name, color, reset))
        
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
                '--query', search_query
            ]
            
            # Agregar parámetros según el modo
            if target_comments is not None:
                # Modo NUEVO: Basado en comentarios
                command.extend(['--target-comments', str(target_comments)])
                command.extend(['--max-posts', str(max_posts)])
            else:
                # Modo ANTIGUO: Basado en posts
                command.extend(['--posts', str(num_posts)])
                command.extend(['--comments', str(num_comments)])
            
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
                # Enviar mensaje de éxito
                if progress_queue:
                    progress_queue.put(('success', name, execution_time, color, reset))
                
                # Parse metrics JSON from stdout
                metrics = self.parse_metrics_from_output(result.stdout)
                
                return {
                    'name': name,
                    'status': 'success',
                    'execution_time': execution_time,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'metrics': metrics
                }
            else:
                # Enviar mensaje de error
                if progress_queue:
                    progress_queue.put(('error', name, result.returncode, result.stderr[:1000], color, reset))
                
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
            
            # Enviar mensaje de excepción
            if progress_queue:
                progress_queue.put(('exception', name, str(e), color, reset))
            
            return {
                'name': name,
                'status': 'exception',
                'execution_time': execution_time,
                'error': str(e)
            }
    
    def parse_metrics_from_output(self, stdout):
        """
        Extrae el JSON de métricas desde la salida del scraper
        
        Args:
            stdout (str): Salida estándar del scraper
        
        Returns:
            dict: Métricas parseadas o None si no se encontraron
        """
        import json
        import re
        
        try:
            # Buscar el JSON entre los marcadores
            pattern = r'### METRICS_JSON_START ###\s*(.+?)\s*### METRICS_JSON_END ###'
            match = re.search(pattern, stdout, re.DOTALL)
            
            if match:
                json_str = match.group(1).strip()
                metrics = json.loads(json_str)
                return metrics
            else:
                return None
        except Exception as e:
            print(f"Error parsing metrics: {e}")
            return None
    def run_parallel(self, query=None, posts=None, comments=None, target_comments=None, max_posts=None):
        """Ejecuta todos los scrapers en paralelo usando multiprocessing"""
        self.print_header()
        
        # RECOGER PARÁMETROS UNA SOLA VEZ
        if not query:
            print("📝 CONFIGURACIÓN DE BÚSQUEDA")
            print("-" * 80)
            
            search_query = input("Ingrese el tema de búsqueda (Tema): ").strip()
            if not search_query:
                search_query = "Inteligencia Artificial"
                print(f"   Usando tema por defecto: {search_query}")
            
            # Preguntar modo de scraping
            mode = input("Modo de scraping: [1] Por posts (antiguo) [2] Por comentarios (nuevo, recomendado): ").strip()
            
            if mode == "2":
                # Modo basado en comentarios
                try:
                    num_target_comments = int(input("Número objetivo de comentarios totales (recomendado 800): ").strip())
                except ValueError:
                    num_target_comments = 800
                    print(f"   Usando valor por defecto: {num_target_comments} comentarios")
                
                try:
                    num_max_posts = int(input("Máximo de posts a scrapear (límite de seguridad, default 200): ").strip())
                except ValueError:
                    num_max_posts = 200
                    print(f"   Usando valor por defecto: {num_max_posts} posts")
                
                target_comments = num_target_comments
                max_posts = num_max_posts
                num_posts = None
                num_comments = None
            else:
                # Modo antiguo basado en posts
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
        else:
            search_query = query
            num_posts = posts
            num_comments = comments
        
        print(f"✅ Configuración establecida:")
        print(f"   • Tema: {search_query}")
        if target_comments:
            print(f"   • MODO: Basado en comentarios")
            print(f"   • Objetivo de comentarios: {target_comments}")
            print(f"   • Máximo de posts: {max_posts}")
        else:
            print(f"   • Posts por red social: {num_posts}")
            print(f"   • Comentarios por post: {num_comments}")
        print("="*80 + "\n")
        
        # Initialize academic metrics collector
        academic_metrics = AcademicMetricsCollector()
        platform_names = ['x', 'instagram', 'facebook', 'linkedin']
        academic_metrics.start_run(
            query=search_query,
            mode="parallel",
            platforms=platform_names,
            n_processes=len(self.scrapers)
        )
        
        self.start_time = time.time()
        
        print("🚀 Iniciando extracción paralela de datos...\n")
        
        # Crear cola para comunicar progreso
        progress_queue = multiprocessing.Queue()
        
        # Crear procesos para cada scraper
        processes = []
        manager = multiprocessing.Manager()
        results_dict = manager.dict()
        
        for i, (name, config) in enumerate(self.scrapers.items()):
            p = multiprocessing.Process(
                target=self._run_scraper_wrapper,
                args=(i, name, config, search_query, num_posts, num_comments, target_comments, max_posts, progress_queue, results_dict)
            )
            processes.append((name, p))
            p.start()
        
        # Monitorear progreso en el proceso principal
        completed = 0
        total = len(processes)
        
        while completed < total:
            try:
                msg = progress_queue.get(timeout=1)
                msg_type = msg[0]
                
                if msg_type == 'start':
                    _, name, color, reset = msg
                    print(f"{color}[{name}] ▶️  Iniciando scraper...{reset}", flush=True)
                
                elif msg_type == 'success':
                    _, name, execution_time, color, reset = msg
                    print(f"{color}[{name}] ✅ Completado exitosamente en {execution_time:.2f}s{reset}", flush=True)
                    completed += 1
                
                elif msg_type == 'error':
                    _, name, returncode, stderr, color, reset = msg
                    print(f"{color}[{name}] ❌ Error en la ejecución (código: {returncode}){reset}", flush=True)
                    print(f"{color}[{name}] Error: {stderr}{reset}", flush=True)
                    completed += 1
                
                elif msg_type == 'exception':
                    _, name, error, color, reset = msg
                    print(f"{color}[{name}] ❌ Excepción: {error}{reset}", flush=True)
                    completed += 1
                    
            except:
                # Timeout - verificar si todos los procesos siguen vivos
                all_done = all(not p.is_alive() for _, p in processes)
                if all_done:
                    break
        
        # Esperar a que todos los procesos terminen
        for name, p in processes:
            p.join()
        
        # Convertir resultados del dict a lista
        results = [results_dict[i] for i in range(len(self.scrapers))]
        
        self.end_time = time.time()
        total_time = self.end_time - self.start_time
        
        # Collect metrics from each scraper
        for result in results:
            if result['status'] == 'success' and result.get('metrics'):
                metrics = result['metrics']
                network_name = self._get_platform_key(result['name'])
                
                # Extract data from metrics
                data_metrics = metrics.get('data_metrics', {})
                exec_times = metrics.get('execution_times', {})
                sentiment_dist = metrics.get('sentiment_distribution', {})
                
                posts = data_metrics.get('posts_extracted', 0)
                comments = data_metrics.get('comments_extracted', 0)
                
                # Record platform results
                academic_metrics.record_platform_end(
                    platform=network_name,
                    posts=posts,
                    comments=comments,
                    errors=0,  # Could be extracted from metrics if available
                    retries=0
                )
                
                # Record timing
                academic_metrics.timing['time_scraping_per_platform_s'][network_name] = exec_times.get('scraping', 0)
                academic_metrics.record_preprocessing_time(exec_times.get('text_processing', 0))
                academic_metrics.record_llm_time(exec_times.get('sentiment_analysis', 0))
                
                # Record sentiments
                for sentiment, count in sentiment_dist.items():
                    for _ in range(count):
                        academic_metrics.add_sentiment_result(sentiment)
            elif result['status'] != 'success':
                network_name = self._get_platform_key(result['name'])
                academic_metrics.record_error(network_name, "execution_failed", result.get('error', ''))
        
        # End the run
        academic_metrics.end_run()
        
        # Consolidar métricas
        consolidated_metrics = self.consolidate_metrics(results, total_time, search_query)
        
        # Mostrar resumen de resultados
        self.print_summary(results, total_time)
        
        # Generar reportes de métricas
        self.generate_metrics_reports(consolidated_metrics)
        
        # Generar gráficas de paralelización
        self.generate_parallelization_charts(results, total_time)
        
        # Generar muestra de validación
        self.generate_validation_sample(search_query)
        
        # Export academic metrics
        print("\n" + "="*80)
        print("📊 EXPORTANDO MÉTRICAS ACADÉMICAS")
        print("="*80)
        files = academic_metrics.export_all()
        print(f"\n✅ Archivos académicos generados:")
        print(f"   📊 Métricas: {files['metrics']}")
        if files['dataset']:
            print(f"   📄 Dataset: {files['dataset']}")
        print(f"   📝 Log: {files['log']}")
        print("\n" + academic_metrics.get_summary())
        
        return results, total_time
    
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
    
    def consolidate_metrics(self, results, total_time, query):
        """
        Consolida las métricas de todos los scrapers
        
        Args:
            results (list): Lista de resultados de cada scraper
            total_time (float): Tiempo total de ejecución paralela
            query (str): Query de búsqueda
        
        Returns:
            dict: Métricas consolidadas
        """
        import json
        from datetime import datetime
        
        # Calcular tiempo secuencial estimado
        total_sequential = sum(r['execution_time'] for r in results)
        speedup = total_sequential / total_time if total_time > 0 else 0
        efficiency = (speedup / len(results)) * 100 if len(results) > 0 else 0
        
        # Recopilar métricas de cada scraper
        scrapers_metrics = {}
        llm_comparison = {}
        global_sentiment = {"positive": 0, "negative": 0, "neutral": 0}
        total_items = 0
        
        for result in results:
            if result['status'] == 'success' and result.get('metrics'):
                metrics = result['metrics']
                network = metrics.get('social_network', result['name'])
                scrapers_metrics[network] = metrics
                
                # Agregar a comparación de LLMs
                llm = metrics.get('llm_used', 'Unknown')
                data_metrics = metrics.get('data_metrics', {})
                exec_times = metrics.get('execution_times', {})
                
                total_llm_items = data_metrics.get('total_text_items', 0)
                sentiment_time = exec_times.get('sentiment_analysis', 0)
                
                if llm not in llm_comparison:
                    llm_comparison[llm] = {
                        'total_items': 0,
                        'total_time': 0,
                        'items_per_second': 0
                    }
                
                llm_comparison[llm]['total_items'] += total_llm_items
                llm_comparison[llm]['total_time'] += sentiment_time
                
                # Agregar a sentimiento global
                sent_dist = metrics.get('sentiment_distribution', {})
                global_sentiment['positive'] += sent_dist.get('positive', 0)
                global_sentiment['negative'] += sent_dist.get('negative', 0)
                global_sentiment['neutral'] += sent_dist.get('neutral', 0)
                
                total_items += total_llm_items
        
        # Calcular items por segundo para cada LLM
        for llm in llm_comparison:
            total_time_llm = llm_comparison[llm]['total_time']
            total_items_llm = llm_comparison[llm]['total_items']
            llm_comparison[llm]['items_per_second'] = round(
                total_items_llm / total_time_llm if total_time_llm > 0 else 0, 2
            )
        
        consolidated = {
            "execution_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "query": query,
            "parallel_execution": {
                "total_time": round(total_time, 2),
                "sequential_estimated": round(total_sequential, 2),
                "speedup": round(speedup, 2),
                "efficiency": round(efficiency, 2),
                "num_processes": len(results)
            },
            "scrapers": scrapers_metrics,
            "llm_comparison": llm_comparison,
            "global_sentiment": global_sentiment,
            "total_items_processed": total_items
        }
        
        return consolidated
    
    def generate_metrics_reports(self, metrics):
        """
        Genera reportes detallados de métricas
        
        Args:
            metrics (dict): Métricas consolidadas
        """
        import json
        from datetime import datetime
        
        log_dir = os.path.join(self.base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. Guardar JSON consolidado
        json_file = os.path.join(log_dir, f'metrics_consolidated_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=4, ensure_ascii=False)
        
        # 2. Generar reporte de texto
        report_file = os.path.join(log_dir, f'metrics_report_{timestamp}.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("REPORTE DE MÉTRICAS DE RENDIMIENTO - SCRAPERS PARALELOS\n")
            f.write("Práctica de Laboratorio 7 - Computación Paralela\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Fecha de ejecución: {metrics['execution_date']}\n")
            f.write(f"Query de búsqueda: {metrics['query']}\n\n")
            
            # Sección 1: Rendimiento del procesamiento paralelo
            f.write("-" * 80 + "\n")
            f.write("1. RENDIMIENTO DEL PROCESAMIENTO CONCURRENTE\n")
            f.write("-" * 80 + "\n")
            parallel = metrics['parallel_execution']
            f.write(f"Tiempo de ejecución paralela:    {parallel['total_time']:.2f} segundos\n")
            f.write(f"Tiempo secuencial estimado:      {parallel['sequential_estimated']:.2f} segundos\n")
            f.write(f"Speedup logrado:                 {parallel['speedup']:.2f}x\n")
            f.write(f"Eficiencia:                      {parallel['efficiency']:.2f}%\n")
            f.write(f"Número de procesos paralelos:    {parallel['num_processes']}\n\n")
            
            # Sección 2: Tiempos de ejecución por scraper
            f.write("-" * 80 + "\n")
            f.write("2. TIEMPOS DE EJECUCIÓN POR RED SOCIAL\n")
            f.write("-" * 80 + "\n")
            for network, data in metrics['scrapers'].items():
                f.write(f"\n{network}:\n")
                exec_times = data['execution_times']
                f.write(f"  - Scraping:           {exec_times.get('scraping', 0):.2f}s\n")
                f.write(f"  - Procesamiento:      {exec_times.get('text_processing', 0):.2f}s\n")
                f.write(f"  - Análisis Sentiment: {exec_times.get('sentiment_analysis', 0):.2f}s\n")
                f.write(f"  - TOTAL:              {exec_times.get('total', 0):.2f}s\n")
            
            # Sección 3: Comparación de LLMs
            f.write("\n" + "-" * 80 + "\n")
            f.write("3. ANÁLISIS COMPARATIVO DE LLMs\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'LLM':<20} {'Items':<15} {'Tiempo (s)':<15} {'Items/seg':<15}\n")
            f.write("-" * 80 + "\n")
            for llm, data in metrics['llm_comparison'].items():
                f.write(f"{llm:<20} {data['total_items']:<15} {data['total_time']:<15.2f} {data['items_per_second']:<15.2f}\n")
            
            # Sección 4: Distribución de sentimientos
            f.write("\n" + "-" * 80 + "\n")
            f.write("4. DISTRIBUCIÓN GLOBAL DE SENTIMIENTOS\n")
            f.write("-" * 80 + "\n")
            sentiment = metrics['global_sentiment']
            total_sent = sentiment['positive'] + sentiment['negative'] + sentiment['neutral']
            f.write(f"Total de items analizados: {total_sent}\n\n")
            if total_sent > 0:
                f.write(f"Positivos: {sentiment['positive']} ({sentiment['positive']/total_sent*100:.1f}%)\n")
                f.write(f"Negativos: {sentiment['negative']} ({sentiment['negative']/total_sent*100:.1f}%)\n")
                f.write(f"Neutros:   {sentiment['neutral']} ({sentiment['neutral']/total_sent*100:.1f}%)\n")
            
            # Sección 5: Capacidad de clasificación
            f.write("\n" + "-" * 80 + "\n")
            f.write("5. CAPACIDAD DE CLASIFICACIÓN A GRAN ESCALA\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total de items procesados: {metrics['total_items_processed']}\n")
            f.write(f"Tiempo total de procesamiento: {parallel['total_time']:.2f}s\n")
            throughput = metrics['total_items_processed'] / parallel['total_time'] if parallel['total_time'] > 0 else 0
            f.write(f"Throughput global: {throughput:.2f} items/segundo\n")
            
            f.write("\n" + "="*80 + "\n")
        
        print(f"\n📊 Reportes de métricas generados:")
        print(f"   - JSON: {json_file}")
        print(f"   - Reporte: {report_file}")
    
    def generate_parallelization_charts(self, results, total_time):
        """
        Genera gráficas visuales de las métricas de paralelización
        
        Args:
            results (list): Lista de resultados de cada scraper
            total_time (float): Tiempo total de ejecución
        """
        log_dir = os.path.join(self.base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Calcular métricas
        total_sequential = sum(r['execution_time'] for r in results)
        speedup = total_sequential / total_time if total_time > 0 else 0
        efficiency = (speedup / len(results)) * 100 if len(results) > 0 else 0
        
        # Crear figura con múltiples subplots
        fig = plt.figure(figsize=(16, 10))
        fig.suptitle('Métricas de Paralelización - Lab Social Media', fontsize=16, fontweight='bold')
        
        # 1. Gráfica de barras: Tiempo Secuencial vs Paralelo
        ax1 = plt.subplot(2, 3, 1)
        times = [total_sequential, total_time]
        bars = ax1.bar(['Tiempo\nSecuencial\nEstimado', 'Tiempo\nParalelo\nReal'], times, 
                       color=['#FF6B6B', '#4ECDC4'], width=0.6)
        ax1.set_ylabel('Tiempo (segundos)', fontsize=11, fontweight='bold')
        ax1.set_title('Comparación de Tiempos', fontsize=12, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Agregar valores en las barras
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}s',
                    ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        # 2. Gráfica de indicadores: Speedup
        ax2 = plt.subplot(2, 3, 2)
        ax2.text(0.5, 0.6, f'{speedup:.2f}x', 
                ha='center', va='center', fontsize=60, fontweight='bold', color='#4ECDC4')
        ax2.text(0.5, 0.25, 'SPEEDUP', 
                ha='center', va='center', fontsize=20, fontweight='bold', color='#333')
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.axis('off')
        
        # Agregar un rectángulo de fondo
        rect = mpatches.FancyBboxPatch((0.15, 0.15), 0.7, 0.7,
                                       boxstyle="round,pad=0.05",
                                       edgecolor='#4ECDC4', facecolor='#E8F8F5',
                                       linewidth=3)
        ax2.add_patch(rect)
        
        # 3. Gráfica de indicadores: Eficiencia
        ax3 = plt.subplot(2, 3, 3)
        ax3.text(0.5, 0.6, f'{efficiency:.1f}%', 
                ha='center', va='center', fontsize=60, fontweight='bold', color='#FFD93D')
        ax3.text(0.5, 0.25, 'EFICIENCIA', 
                ha='center', va='center', fontsize=20, fontweight='bold', color='#333')
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)
        ax3.axis('off')
        
        # Agregar un rectángulo de fondo
        rect2 = mpatches.FancyBboxPatch((0.15, 0.15), 0.7, 0.7,
                                        boxstyle="round,pad=0.05",
                                        edgecolor='#FFD93D', facecolor='#FFFAED',
                                        linewidth=3)
        ax3.add_patch(rect2)
        
        # 4. Gráfica de barras horizontales: Tiempo por scraper
        ax4 = plt.subplot(2, 3, 4)
        names = [r['name'] for r in results]
        times = [r['execution_time'] for r in results]
        colors_map = ['#FF6B6B', '#4ECDC4', '#95E1D3', '#F38181']
        
        bars = ax4.barh(names, times, color=colors_map[:len(names)])
        ax4.set_xlabel('Tiempo (segundos)', fontsize=11, fontweight='bold')
        ax4.set_title('Tiempo de Ejecución por Red Social', fontsize=12, fontweight='bold')
        ax4.grid(axis='x', alpha=0.3, linestyle='--')
        
        # Agregar valores en las barras
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax4.text(width, bar.get_y() + bar.get_height()/2.,
                    f' {width:.2f}s',
                    ha='left', va='center', fontweight='bold', fontsize=9)
        
        # 5. Gráfica de pastel: Estado de los scrapers
        ax5 = plt.subplot(2, 3, 5)
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = len(results) - successful
        
        if failed > 0:
            sizes = [successful, failed]
            labels = [f'Exitosos\n({successful})', f'Errores\n({failed})']
            colors = ['#4ECDC4', '#FF6B6B']
            explode = (0.05, 0.05)
        else:
            sizes = [successful]
            labels = [f'Exitosos\n({successful})']
            colors = ['#4ECDC4']
            explode = (0.05,)
        
        ax5.pie(sizes, explode=explode, labels=labels, colors=colors,
               autopct='%1.1f%%', shadow=True, startangle=90,
               textprops={'fontsize': 11, 'fontweight': 'bold'})
        ax5.set_title('Estado de Ejecución', fontsize=12, fontweight='bold')
        
        # 6. Tabla de resumen
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        # Datos de la tabla
        table_data = [
            ['Métrica', 'Valor'],
            ['─' * 25, '─' * 15],
            ['Procesos Paralelos', f'{len(results)}'],
            ['Tiempo Secuencial', f'{total_sequential:.2f}s'],
            ['Tiempo Paralelo', f'{total_time:.2f}s'],
            ['Speedup', f'{speedup:.2f}x'],
            ['Eficiencia', f'{efficiency:.2f}%'],
            ['Scrapers Exitosos', f'{successful}/{len(results)}'],
        ]
        
        table = ax6.table(cellText=table_data, cellLoc='left',
                         loc='center', colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.5)
        
        # Estilizar la tabla
        for i in range(len(table_data)):
            if i == 0:  # Header
                for j in range(2):
                    table[(i, j)].set_facecolor('#4ECDC4')
                    table[(i, j)].set_text_props(weight='bold', color='white')
            elif i == 1:  # Separator
                for j in range(2):
                    table[(i, j)].set_facecolor('#F0F0F0')
            else:
                table[(i, 0)].set_facecolor('#F8F8F8')
                table[(i, 1)].set_facecolor('#FFFFFF')
        
        ax6.set_title('Resumen de Métricas', fontsize=12, fontweight='bold', pad=20)
        
        # Ajustar layout y guardar
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        
        chart_file = os.path.join(log_dir, f'parallelization_metrics_{timestamp}.png')
        plt.savefig(chart_file, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"   - Gráfica: {chart_file}")
        
        # Mostrar la gráfica
        try:
            plt.show(block=False)
            plt.pause(0.1)
        except:
            pass  # Si falla al mostrar, no importa


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Master Scraper - Ejecución Paralela de Scrapers")
    parser.add_argument("--sequential", action="store_true", help="Ejecutar en modo secuencial (1 proceso a la vez)")
    parser.add_argument("--compare", action="store_true", help="Ejecutar modo Secuencial Y Paralelo para comparar Speedup real")
    # Argumentos para automatización
    parser.add_argument("--query", type=str, default=None, help="Tema de búsqueda (Evita input interactivo)")
    parser.add_argument("--posts", type=int, default=None, help="Número de posts por red (DEPRECADO: usar --target-comments)")
    parser.add_argument("--comments", type=int, default=None, help="Número de comentarios por post (DEPRECADO: usar --target-comments)")
    # NUEVO: Argumentos basados en comentarios
    parser.add_argument("--target-comments", type=int, default=None, help="Número objetivo de comentarios totales (recomendado: 800)")
    parser.add_argument("--max-posts", type=int, default=200, help="Máximo de posts a scrapear (límite de seguridad)")
    
    args = parser.parse_args()
    
    # Defaults para automatización
    if args.target_comments:
        # Modo NUEVO: Basado en comentarios
        if not args.max_posts:
            args.max_posts = 200  # Límite de seguridad
        print(f"ℹ️  MODO: Scraping basado en comentarios (Objetivo: {args.target_comments} comentarios)")
    else:
        # Modo ANTIGUO: Basado en posts (compatibilidad)
        if args.query and not args.posts:
            args.posts = 5
        if args.query and args.comments is None:
            args.comments = 2
    
    # Verificar que estamos en Windows (para soporte de colores)
    if os.name == 'nt':
        os.system('color')
    
    print("\n🎯 Iniciando Master Scraper...")
    if args.sequential:
        print("ℹ️  MODO: SECUENCIAL FORZADO")
    if args.compare:
        print("ℹ️  MODO: COMPARACIÓN DE RENDIMIENTO (Secuencial vs Paralelo)")
    
    # Crear instancia del gestor
    manager = SocialMediaScraperManager()
    
    try:
        results = []
        
        if args.compare:
            print("\n" + "!"*80)
            print("  FASE 1: EJECUCIÓN SECUENCIAL (LÍNEA BASE)")
            print("!"*80 + "\n")
            # Forzar paso de argumentos si existen
            results_seq, time_seq = manager.run_sequential(query=args.query, posts=args.posts, comments=args.comments, target_comments=args.target_comments, max_posts=args.max_posts)
            
            print("\n" + "!"*80)
            print("  FASE 2: EJECUCIÓN PARALELA (OPTIMIZADA)")
            print("!"*80 + "\n")
            results_par, time_par = manager.run_parallel(query=args.query, posts=args.posts, comments=args.comments, target_comments=args.target_comments, max_posts=args.max_posts)
            
            # Calcular Speedup Real
            speedup_real = time_seq / time_par if time_par > 0 else 0
            
            print("\n" + "★"*80)
            print(f"🚀 RESULTADOS DE LA COMPARACIÓN")
            print("★"*80)
            print(f"⏱️  Tiempo Secuencial: {time_seq:.2f}s")
            print(f"⏱️  Tiempo Paralelo:   {time_par:.2f}s")
            print(f"⚡ SPEEDUP REAL:      {speedup_real:.2f}x")
            print(f"   (El sistema es {speedup_real:.1f} veces más rápido en paralelo)")
            print("★"*80 + "\n")
            
            results = results_par # Usamos resultados paralelos para validación final
            
        elif args.sequential:
            results, _ = manager.run_sequential(query=args.query, posts=args.posts, comments=args.comments, target_comments=args.target_comments, max_posts=args.max_posts)
        else:
            results, _ = manager.run_parallel(query=args.query, posts=args.posts, comments=args.comments, target_comments=args.target_comments, max_posts=args.max_posts)
        
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
        # import traceback
        # traceback.print_exc()
        return 3


if __name__ == "__main__":
    # Configurar multiprocessing para Windows
    multiprocessing.freeze_support()
    
    # Ejecutar programa principal
    exit_code = main()
    
    # Esperar antes de cerrar
    input("\n\nPresione ENTER para salir...")
    sys.exit(exit_code)
