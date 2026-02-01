# -*- coding: utf-8 -*-
"""Test rápido de progreso en multiprocessing"""
import sys
import io
import multiprocessing
import time

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def worker(name, queue):
    """Simula un scraper"""
    queue.put(('start', name))
    time.sleep(2)  # Simular trabajo
    queue.put(('success', name))

if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    print("🧪 Probando comunicación entre procesos...\n")
    
    queue = multiprocessing.Queue()
    
    # Crear procesos
    processes = []
    for name in ['Twitter', 'Instagram', 'Facebook', 'LinkedIn']:
        p = multiprocessing.Process(target=worker, args=(name, queue))
        processes.append(p)
        p.start()
    
    # Monitorear progreso
    completed = 0
    total = len(processes)
    
    while completed < total:
        try:
            msg = queue.get(timeout=1)
            msg_type, name = msg
            
            if msg_type == 'start':
                print(f"[{name}] ▶️  Iniciando...", flush=True)
            elif msg_type == 'success':
                print(f"[{name}] ✅ Completado!", flush=True)
                completed += 1
        except:
            # Timeout
            all_done = all(not p.is_alive() for p in processes)
            if all_done:
                break
    
    # Esperar a que terminen
    for p in processes:
        p.join()
    
    print("\n✅ Prueba completada!")
