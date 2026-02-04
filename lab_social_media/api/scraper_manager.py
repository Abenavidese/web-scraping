# -*- coding: utf-8 -*-
"""
Scraper Manager - Subprocess Execution
Handles parallel execution of selected scrapers using direct subprocess Popen
"""

import subprocess
import time
import os
import sys
import json
import re
from datetime import datetime

class ScraperManager:
    """Manages parallel execution of social media scrapers"""
    
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.scrapers = {
            'x': {
                'name': 'X (Twitter)',
                'dir': os.path.join(base_dir, 'x_scrapper'),
                'script': 'main.py'
            },
            'instagram': {
                'name': 'Instagram',
                'dir': os.path.join(base_dir, 'App_Paralela_Instagram'),
                'script': 'scraper.py'
            },
            'facebook': {
                'name': 'Facebook',
                'dir': os.path.join(base_dir, 'App_Paralela_facebook'),
                'script': 'scraper.py'
            },
            'linkedin': {
                'name': 'LinkedIn',
                'dir': os.path.join(base_dir, 'linkedin_scraper'),
                'script': 'main.py'
            }
        }
    
    def _parse_metrics(self, stdout):
        """
        Extract metrics JSON from scraper output
        
        Args:
            stdout (str): Scraper stdout
            
        Returns:
            dict: Parsed metrics or None
        """
        try:
            pattern = r'### METRICS_JSON_START ###\s*(.+?)\s*### METRICS_JSON_END ###'
            match = re.search(pattern, stdout, re.DOTALL)
            
            if match:
                json_str = match.group(1).strip()
                return json.loads(json_str)
            return None
        except Exception:
            return None
    
    def run_scrapers(self, networks, query, num_posts=10, num_comments=5, user_id='default', limits=None, session_id=None):
        """
        Run selected scrapers in parallel using subprocess.Popen
        
        Args:
            networks (list): List of network keys to scrape (e.g., ['x', 'instagram'])
            query (str): Search query
            num_posts (int): Number of posts per network
            num_comments (int): Number of comments per post
            user_id (str): User ID for data isolation (default: 'default')
            limits (dict): Optional dictionary mapping network keys to post counts (e.g. {'x': 50})
            session_id (str): Optional session ID for progress tracking
            
        Returns:
            dict: Results from all scrapers
        """
        # Progress tracking
        from progress_tracker import progress_tracker
        
        def emit_progress(event_type, data):
            if session_id:
                progress_tracker.emit(session_id, event_type, data)
        
        # Validate networks
        valid_networks = [n for n in networks if n in self.scrapers]
        if not valid_networks:
            return {
                'success': False,
                'error': 'No valid networks specified',
                'valid_options': list(self.scrapers.keys())
            }
        
        print(f"🚀 Launching scrapers for: {', '.join(valid_networks)}", flush=True)
        emit_progress('launch', {'networks': valid_networks})
        
        # Launch all processes immediately
        running_processes = []
        for network_key in valid_networks:
            config = self.scrapers[network_key]
            
            # Determine number of posts for this network
            cnt_posts = num_posts
            if limits and network_key in limits:
                try:
                    cnt_posts = int(limits[network_key])
                except:
                    pass

            # Build command
            command = [
                sys.executable,
                config['script'],
                '--query', query,
                '--posts', str(cnt_posts),
                '--comments', str(num_comments)
            ]
            
            try:
                # Use Popen to start process without blocking
                # We need CREATE_NO_WINDOW on Windows to avoid popping up extra console windows if desired,
                # but for now we'll stick to default to ensure environment inheritance works well.
                process = subprocess.Popen(
                    command,
                    cwd=config['dir'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env={**os.environ, 'USER_ID': user_id}
                )
                
                running_processes.append({
                    'network': network_key,
                    'name': config['name'],
                    'process': process,
                    'start_time': time.time()
                })
                print(f"   ▶️ Started {config['name']} (PID: {process.pid})", flush=True)
                emit_progress('network_start', {'network': network_key, 'name': config['name'], 'pid': process.pid})
                
            except Exception as e:
                print(f"   ❌ Failed to start {config['name']}: {e}", flush=True)
                # Keep track of failed starts to report them
                running_processes.append({
                    'network': network_key,
                    'name': config['name'],
                    'error': str(e),
                    'status': 'error',
                    'execution_time': 0
                })

        # Wait for all processes to complete and collect results
        results = []
        
        for p_info in running_processes:
            # Skip if it failed to start
            if 'process' not in p_info:
                results.append(p_info)
                continue
                
            process = p_info['process']
            network_key = p_info['network']
            name = p_info['name']
            start_time = p_info['start_time']
            
            try:
                # communicate() waits for the process to finish and reads output
                # We set a timeout (e.g., 10 minutes)
                stdout, stderr = process.communicate(timeout=600)
                
                end_time = time.time()
                execution_time = end_time - start_time
                returncode = process.returncode
                
                # Emit completion event
                emit_progress('network_complete', {'network': network_key, 'name': name, 'execution_time': execution_time, 'status': 'success' if returncode == 0 else 'error'})
                
                # Parse metrics
                metrics = self._parse_metrics(stdout)
                
                status = 'success' if returncode == 0 else 'error'
                error_msg = stderr if returncode != 0 else None
                
                print(f"   ✅ Finished {name} in {execution_time:.2f}s (Status: {status})", flush=True)
                
                results.append({
                    'network': network_key,
                    'name': name,
                    'status': status,
                    'execution_time': round(execution_time, 2),
                    'returncode': returncode,
                    'metrics': metrics,
                    'error': error_msg
                })
                
            except subprocess.TimeoutExpired:
                # Kill the process if it times out
                process.kill()
                stdout, stderr = process.communicate()
                end_time = time.time()
                execution_time = end_time - start_time
                
                print(f"   ⏱️ Timeout {name} after {execution_time:.2f}s", flush=True)
                
                results.append({
                    'network': network_key,
                    'name': name,
                    'status': 'timeout',
                    'execution_time': round(execution_time, 2),
                    'error': 'Scraper exceeded 10 minute timeout'
                })
            
            except Exception as e:
                print(f"   ❌ Error waiting for {name}: {e}", flush=True)
                results.append({
                    'network': network_key,
                    'name': name,
                    'status': 'exception',
                    'execution_time': 0,
                    'error': str(e)
                })

        # Calculate summary
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = len(results) - successful
        total_time = max([r['execution_time'] for r in results]) if results else 0
        
        return {
            'success': True,
            'query': query,
            'num_posts': num_posts,
            'num_comments': num_comments,
            'networks_requested': valid_networks,
            'networks_completed': len(results),
            'successful': successful,
            'failed': failed,
            'total_execution_time': round(total_time, 2),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
