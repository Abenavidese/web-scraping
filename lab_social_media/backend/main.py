import os
import sys
import asyncio
import json
import glob
import threading
import subprocess
import time
from typing import List, Optional
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Force standard loop just in case, though we won't use async subprocess anymore
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="SocialPulse Nexus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    query: str
    posts: int = 10
    comments: int = 5

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Global State
output_buffer = []
is_running = False
log_lock = threading.Lock()

def scrape_worker(query, posts, comments):
    global is_running
    is_running = True
    
    script_path = os.path.join(BASE_DIR, "master_scraper.py")
    python_exe = sys.executable
    
    cmd = [
        python_exe,
        script_path,
        "--query", query,
        "--posts", str(posts),
        "--comments", str(comments),
        "--no-wait"
    ]
    
    with log_lock:
        output_buffer.append(f"🚀 Iniciando extracción de datos...")
        output_buffer.append(f"📊 Búsqueda: {query}")
        output_buffer.append(f"📈 Posts: {posts} | Comentarios: {comments}")
    
    try:
        # Use Popen with unbuffered output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr into stdout
            cwd=BASE_DIR,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1, # Line buffered
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        
        # Filter logs to show only important messages
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                # Only show user-friendly messages
                if any(keyword in line.lower() for keyword in [
                    'iniciando', 'ejecutando', 'completado', 'error', 
                    'extrayendo', 'analizando', 'guardando', 'finalizado',
                    'scraper', 'éxito', 'fallido'
                ]):
                    with log_lock:
                        # Clean up the message
                        clean_msg = line.replace('🎯', '').replace('✅', '').replace('❌', '').strip()
                        if clean_msg:
                            output_buffer.append(f"⚡ {clean_msg}")
                            # Keep buffer size manageable
                            if len(output_buffer) > 100:
                                output_buffer.pop(0)

        process.stdout.close()
        return_code = process.wait()
        
        with log_lock:
            if return_code == 0:
                output_buffer.append("✅ Proceso completado exitosamente")
            else:
                output_buffer.append(f"⚠️ Proceso finalizado con código {return_code}")
                
    except Exception as e:
        with log_lock:
            output_buffer.append(f"❌ Error crítico: {str(e)}")
    finally:
        is_running = False


@app.get("/")
def read_root():
    return {"status": "SocialPulse Nexus Online", "version": "2.0.0 (Sync)"}

@app.post("/start-scraping")
def start_scraping(request: ScrapeRequest):
    global is_running, output_buffer
    
    if is_running:
        return {"status": "busy", "message": "Scraping already in progress."}

    # Clear previous logs
    with log_lock:
        output_buffer = []

    # Start independent thread
    t = threading.Thread(
        target=scrape_worker, 
        args=(request.query, request.posts, request.comments),
        daemon=True
    )
    t.start()
    
    return {"status": "started"}


@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_idx = 0
    try:
        while True:
            # Check for new logs
            current_len = 0
            new_lines = []
            
            with log_lock:
                current_len = len(output_buffer)
                if current_len > last_idx:
                    new_lines = output_buffer[last_idx:]
                    last_idx = current_len

            for line in new_lines:
                await websocket.send_text(line)
            
            await asyncio.sleep(0.2)
            
    except Exception as e:
        print(f"WebSocket disconnected: {e}")

@app.get("/results")
def get_results():
    results = {
        "summary": {},
        "networks": {}
    }
    
    def read_json(path):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return None
        return None

    logs_dir = os.path.join(BASE_DIR, "logs")
    metrics_files = sorted(glob.glob(os.path.join(logs_dir, "metrics_consolidated_*.json")), reverse=True)
    if metrics_files:
        results["summary"] = read_json(metrics_files[0])
    
    # Twitter/X - Parse sentiment_results.csv with correct columns
    x_path = os.path.join(BASE_DIR, "x_scrapper", "output", "sentiment_results.csv")
    if os.path.exists(x_path):
        import pandas as pd
        try:
            df = pd.read_csv(x_path)
            # Map columns: text_content -> text, sentiment_reasoning -> reasoning
            twitter_data = []
            for _, row in df.iterrows():
                twitter_data.append({
                    'text': row.get('text_content', ''),
                    'sentiment': row.get('sentiment', 'NEUTRAL'),
                    'reasoning': row.get('sentiment_reasoning', ''),
                    'score': row.get('sentiment_score', 0),
                    'type': row.get('item_type', 'comment')
                })
            results["networks"]["twitter"] = twitter_data
        except Exception as e:
            print(f"Error reading Twitter data: {e}")

    # Instagram
    ig_path = os.path.join(BASE_DIR, "App_Paralela_Instagram", "data", "processed_comments.json")
    ig_data = read_json(ig_path)
    if ig_data: results["networks"]["instagram"] = ig_data

    # Facebook
    fb_dir = os.path.join(BASE_DIR, "App_Paralela_facebook", "Resultados")
    fb_files = sorted(glob.glob(os.path.join(fb_dir, "results_facebook_*.json")), reverse=True)
    if fb_files:
        fb_data = read_json(fb_files[0])
        if fb_data:
            # Extract comments from Facebook structure
            fb_comments = []
            if isinstance(fb_data, dict) and 'posts' in fb_data:
                for post in fb_data['posts']:
                    if 'comments' in post:
                        for comment in post['comments']:
                            fb_comments.append({
                                'text': comment.get('text', comment.get('content', '')),
                                'sentiment': comment.get('sentiment', 'NEUTRAL'),
                                'reasoning': comment.get('reasoning', ''),
                                'author': comment.get('author', 'Unknown')
                            })
            results["networks"]["facebook"] = fb_comments

    # LinkedIn
    li_path = os.path.join(BASE_DIR, "linkedin_scraper", "output", "datos_extraidos_deepseek.csv")
    if os.path.exists(li_path):
        import pandas as pd
        try:
            df = pd.read_csv(li_path)
            linkedin_data = []
            for _, row in df.iterrows():
                linkedin_data.append({
                    'text': row.get('text', row.get('content', '')),
                    'sentiment': row.get('sentiment_deepseek', 'NEUTRAL'),
                    'reasoning': row.get('explanation_deepseek', ''),
                    'author': row.get('author', 'Unknown')
                })
            results["networks"]["linkedin"] = linkedin_data
        except Exception as e:
            print(f"Error reading LinkedIn data: {e}")
        
    return results
```
