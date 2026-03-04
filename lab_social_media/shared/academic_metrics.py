# -*- coding: utf-8 -*-
"""
Academic Metrics Collector
Comprehensive metrics collection system for academic paper publication
"""

import os
import sys
import json
import uuid
import platform
import psutil
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class AcademicMetricsCollector:
    """
    Comprehensive metrics collector for academic research.
    Tracks experiment identification, data volume, timing, performance,
    quality, robustness, and execution environment.
    """
    
    def __init__(self, base_dir: str = None):
        """
        Initialize metrics collector.
        
        Args:
            base_dir: Base directory for saving run files (default: ./runs)
        """
        self.base_dir = base_dir or os.path.join(os.getcwd(), 'runs')
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Generate unique run ID
        self.run_id = str(uuid.uuid4())
        
        # 1. Experiment Identification
        self.experiment_id = {
            'run_id': self.run_id,
            'query': None,
            'date_time_start': None,
            'date_time_end': None,
            'mode': None,  # "parallel" or "sequential"
            'n_processes': None,
            'platforms_enabled': []
        }
        
        # 2. Data Volume
        self.data_volume = {
            'total_comments_extracted': 0,
            'comments_per_platform': {},
            'total_posts_scraped': 0,
            'posts_per_platform': {},
            'duplicates_removed': 0,
            'comments_after_cleaning': 0,
            'failed_items': {}
        }
        
        # 3. Timing (all in seconds)
        self.timing = {
            'time_total_s': 0.0,
            'time_scraping_total_s': 0.0,
            'time_scraping_per_platform_s': {},
            'time_preprocess_s': 0.0,
            'time_llm_inference_s': 0.0,
            'avg_time_per_comment_s': 0.0
        }
        
        # 4. Performance & Scalability
        self.performance = {
            'throughput_comments_per_min': 0.0,
            'throughput_comments_per_hour': 0.0,
            'speedup': None,  # Only if sequential time is available
            'efficiency': None  # Only if speedup is calculated
        }
        
        # 5. Classification Quality
        self.quality = {
            'sentiment_counts': {
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'mixed': 0,
                'unknown': 0
            },
            'sentiment_percentages': {},
            'manual_validation': None  # Optional
        }
        
        # 6. Scraping Robustness
        self.robustness = {
            'errors_per_platform': {},
            'error_types': [],
            'retries_per_platform': {},
            'blocked_detected': False
        }
        
        # 7. Execution Environment
        self.environment = self._capture_environment()
        
        # Internal tracking
        self._platform_start_times = {}
        self._log_entries = []
        self._sequential_time = None  # For speedup calculation
        
        # Dataset storage
        self._dataset = []
        
        self._log(f"RUN_START run_id={self.run_id}")
    
    def _capture_environment(self) -> Dict[str, Any]:
        """Capture execution environment information."""
        try:
            cpu_info = platform.processor() or "Unknown"
            num_cores = psutil.cpu_count(logical=False) or os.cpu_count()
            num_logical = psutil.cpu_count(logical=True) or os.cpu_count()
            ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
        except:
            cpu_info = platform.processor() or "Unknown"
            num_cores = os.cpu_count()
            num_logical = os.cpu_count()
            ram_gb = "Unknown"
        
        return {
            'cpu_info': cpu_info,
            'num_cores': num_cores,
            'num_logical_cores': num_logical,
            'ram_gb': ram_gb,
            'os': f"{platform.system()} {platform.release()}",
            'python_version': platform.python_version(),
            'machine': platform.machine()
        }
    
    def _log(self, message: str, level: str = "INFO"):
        """Add entry to log."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        entry = f"[{timestamp}] [{level}] {message}"
        self._log_entries.append(entry)
        print(entry)
    
    def start_run(self, query: str, mode: str, platforms: List[str], n_processes: int = None):
        """
        Start a new experimental run.
        
        Args:
            query: Search query/topic
            mode: "parallel" or "sequential"
            platforms: List of enabled platforms
            n_processes: Number of parallel processes (if applicable)
        """
        self.experiment_id['query'] = query
        self.experiment_id['date_time_start'] = datetime.now().isoformat()
        self.experiment_id['mode'] = mode
        self.experiment_id['platforms_enabled'] = platforms
        self.experiment_id['n_processes'] = n_processes or len(platforms)
        
        # Initialize platform tracking
        for platform in platforms:
            self.data_volume['comments_per_platform'][platform] = 0
            self.data_volume['posts_per_platform'][platform] = 0
            self.timing['time_scraping_per_platform_s'][platform] = 0.0
            self.robustness['errors_per_platform'][platform] = 0
            self.robustness['retries_per_platform'][platform] = 0
        
        self._log(f"RUN_START query='{query}' mode={mode} platforms={platforms}")
    
    def end_run(self):
        """End the experimental run and calculate final metrics."""
        self.experiment_id['date_time_end'] = datetime.now().isoformat()
        
        # Calculate total time
        if self.experiment_id['date_time_start'] and self.experiment_id['date_time_end']:
            start = datetime.fromisoformat(self.experiment_id['date_time_start'])
            end = datetime.fromisoformat(self.experiment_id['date_time_end'])
            self.timing['time_total_s'] = (end - start).total_seconds()
        
        # Calculate average time per comment
        if self.data_volume['total_comments_extracted'] > 0:
            self.timing['avg_time_per_comment_s'] = round(
                self.timing['time_total_s'] / self.data_volume['total_comments_extracted'], 4
            )
        
        # Calculate throughput
        if self.timing['time_total_s'] > 0:
            self.performance['throughput_comments_per_min'] = round(
                self.data_volume['total_comments_extracted'] / (self.timing['time_total_s'] / 60), 2
            )
            self.performance['throughput_comments_per_hour'] = round(
                self.performance['throughput_comments_per_min'] * 60, 2
            )
        
        # Calculate speedup and efficiency
        if self._sequential_time and self.experiment_id['mode'] == 'parallel':
            self.performance['speedup'] = round(
                self._sequential_time / self.timing['time_total_s'], 2
            )
            if self.experiment_id['n_processes']:
                self.performance['efficiency'] = round(
                    (self.performance['speedup'] / self.experiment_id['n_processes']) * 100, 2
                )
        
        # Calculate sentiment percentages
        total_sentiments = sum(self.quality['sentiment_counts'].values())
        if total_sentiments > 0:
            for sentiment, count in self.quality['sentiment_counts'].items():
                self.quality['sentiment_percentages'][sentiment] = round(
                    (count / total_sentiments) * 100, 2
                )
        
        self._log(f"RUN_END total_time={self.timing['time_total_s']:.2f}s comments={self.data_volume['total_comments_extracted']}")
    
    def record_platform_start(self, platform: str):
        """Record start time for a platform scraper."""
        self._platform_start_times[platform] = datetime.now()
        self._log(f"PLATFORM_START platform={platform}")
    
    def record_platform_end(self, platform: str, posts: int = 0, comments: int = 0, 
                           errors: int = 0, retries: int = 0):
        """
        Record end time and results for a platform scraper.
        
        Args:
            platform: Platform name
            posts: Number of posts scraped
            comments: Number of comments scraped
            errors: Number of errors encountered
            retries: Number of retries performed
        """
        if platform in self._platform_start_times:
            elapsed = (datetime.now() - self._platform_start_times[platform]).total_seconds()
            self.timing['time_scraping_per_platform_s'][platform] = round(elapsed, 2)
            self.timing['time_scraping_total_s'] += elapsed
        
        # Update data volume
        self.data_volume['posts_per_platform'][platform] = posts
        self.data_volume['comments_per_platform'][platform] = comments
        self.data_volume['total_posts_scraped'] += posts
        self.data_volume['total_comments_extracted'] += comments
        
        # Update robustness
        self.robustness['errors_per_platform'][platform] = errors
        self.robustness['retries_per_platform'][platform] = retries
        
        self._log(f"PLATFORM_END platform={platform} posts={posts} comments={comments} errors={errors}")
    
    def record_preprocessing_time(self, seconds: float):
        """Record text preprocessing time."""
        self.timing['time_preprocess_s'] += seconds
        self._log(f"PREPROCESS_TIME time={seconds:.2f}s")
    
    def record_llm_time(self, seconds: float):
        """Record LLM inference time."""
        self.timing['time_llm_inference_s'] += seconds
        self._log(f"LLM_TIME time={seconds:.2f}s")
    
    def record_error(self, platform: str, error_type: str, message: str = ""):
        """
        Record an error occurrence.
        
        Args:
            platform: Platform where error occurred
            error_type: Type of error (timeout, blocked, selector_not_found, etc.)
            message: Optional error message
        """
        if platform in self.robustness['errors_per_platform']:
            self.robustness['errors_per_platform'][platform] += 1
        
        if error_type not in self.robustness['error_types']:
            self.robustness['error_types'].append(error_type)
        
        if 'blocked' in error_type.lower() or 'captcha' in error_type.lower():
            self.robustness['blocked_detected'] = True
        
        self._log(f"ERROR platform={platform} type={error_type} message='{message}'", level="ERROR")
    
    def add_sentiment_result(self, sentiment: str):
        """
        Add a sentiment classification result.
        
        Args:
            sentiment: Sentiment label (positive, negative, neutral, mixed, unknown)
        """
        sentiment_normalized = sentiment.lower()
        
        # Map Spanish to English
        sentiment_map = {
            'positivo': 'positive',
            'positive': 'positive',
            'negativo': 'negative',
            'negative': 'negative',
            'neutro': 'neutral',
            'neutral': 'neutral',
            'mixto': 'mixed',
            'mixed': 'mixed'
        }
        
        sentiment_key = sentiment_map.get(sentiment_normalized, 'unknown')
        
        if sentiment_key in self.quality['sentiment_counts']:
            self.quality['sentiment_counts'][sentiment_key] += 1
    
    def add_dataset_row(self, platform: str, post_id: str, comment_id: str, 
                       text: str, sentiment: str, sentiment_score: float,
                       reasoning: str, terms: str = "", timestamp: str = None):
        """
        Add a row to the dataset.
        
        Args:
            platform: Social media platform
            post_id: Post identifier
            comment_id: Comment identifier
            text: Comment text
            sentiment: Sentiment classification
            sentiment_score: Confidence score
            reasoning: Explanation/reasoning
            terms: Key terms (optional)
            timestamp: Timestamp (optional, uses current time if None)
        """
        self._dataset.append({
            'run_id': self.run_id,
            'platform': platform,
            'post_id': post_id,
            'comment_id': comment_id,
            'text': text,
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'reasoning': reasoning,
            'terms': terms,
            'timestamp': timestamp or datetime.now().isoformat()
        })
    
    def set_sequential_time(self, seconds: float):
        """
        Set sequential execution time for speedup calculation.
        
        Args:
            seconds: Total sequential execution time
        """
        self._sequential_time = seconds
        self._log(f"SEQUENTIAL_TIME time={seconds:.2f}s")
    
    def set_manual_validation(self, sample_size: int, precision: Dict[str, float],
                             recall: Dict[str, float], f1: Dict[str, float]):
        """
        Set manual validation metrics.
        
        Args:
            sample_size: Number of samples validated
            precision: Precision per class
            recall: Recall per class
            f1: F1 score per class
        """
        self.quality['manual_validation'] = {
            'sample_size': sample_size,
            'precision_per_class': precision,
            'recall_per_class': recall,
            'f1_per_class': f1
        }
        self._log(f"VALIDATION sample_size={sample_size}")
    
    def export_metrics_json(self, custom_path: str = None) -> str:
        """
        Export metrics to JSON file.
        
        Args:
            custom_path: Custom file path (optional)
        
        Returns:
            Path to exported file
        """
        if custom_path:
            filepath = custom_path
        else:
            filename = f"run_{self.run_id}_metrics.json"
            filepath = os.path.join(self.base_dir, filename)
        
        metrics = {
            'experiment_id': self.experiment_id,
            'data_volume': self.data_volume,
            'timing': self.timing,
            'performance': self.performance,
            'quality': self.quality,
            'robustness': self.robustness,
            'environment': self.environment
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        self._log(f"EXPORT_METRICS path={filepath}")
        print(f"📊 Metrics exported to: {filepath}")
        return filepath
    
    def export_dataset_csv(self, custom_path: str = None) -> str:
        """
        Export dataset to CSV file.
        
        Args:
            custom_path: Custom file path (optional)
        
        Returns:
            Path to exported file
        """
        if custom_path:
            filepath = custom_path
        else:
            filename = f"run_{self.run_id}_dataset.csv"
            filepath = os.path.join(self.base_dir, filename)
        
        if not self._dataset:
            self._log("EXPORT_DATASET skipped (no data)", level="WARNING")
            return None
        
        fieldnames = ['run_id', 'platform', 'post_id', 'comment_id', 'text', 
                     'sentiment', 'sentiment_score', 'reasoning', 'terms', 'timestamp']
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self._dataset)
        
        self._log(f"EXPORT_DATASET path={filepath} rows={len(self._dataset)}")
        print(f"📄 Dataset exported to: {filepath}")
        return filepath
    
    def export_log(self, custom_path: str = None) -> str:
        """
        Export log to text file.
        
        Args:
            custom_path: Custom file path (optional)
        
        Returns:
            Path to exported file
        """
        if custom_path:
            filepath = custom_path
        else:
            filename = f"run_{self.run_id}.log"
            filepath = os.path.join(self.base_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self._log_entries))
        
        print(f"📝 Log exported to: {filepath}")
        return filepath
    
    def export_all(self) -> Dict[str, str]:
        """
        Export all three files (metrics, dataset, log).
        
        Returns:
            Dictionary with paths to all exported files
        """
        return {
            'metrics': self.export_metrics_json(),
            'dataset': self.export_dataset_csv(),
            'log': self.export_log()
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the run."""
        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║              ACADEMIC METRICS SUMMARY                        ║
╚══════════════════════════════════════════════════════════════╝

Run ID: {self.run_id}
Query: {self.experiment_id['query']}
Mode: {self.experiment_id['mode']}
Platforms: {', '.join(self.experiment_id['platforms_enabled'])}

📊 DATA VOLUME
  • Total Posts: {self.data_volume['total_posts_scraped']}
  • Total Comments: {self.data_volume['total_comments_extracted']}
  • Comments per platform:
"""
        for platform, count in self.data_volume['comments_per_platform'].items():
            summary += f"    - {platform}: {count}\n"
        
        summary += f"""
⏱️  TIMING
  • Total Time: {self.timing['time_total_s']:.2f}s
  • Scraping Time: {self.timing['time_scraping_total_s']:.2f}s
  • Preprocessing: {self.timing['time_preprocess_s']:.2f}s
  • LLM Inference: {self.timing['time_llm_inference_s']:.2f}s
  • Avg per Comment: {self.timing['avg_time_per_comment_s']:.4f}s

🚀 PERFORMANCE
  • Throughput: {self.performance['throughput_comments_per_min']:.2f} comments/min
  • Throughput: {self.performance['throughput_comments_per_hour']:.2f} comments/hour
"""
        
        if self.performance['speedup']:
            summary += f"  • Speedup: {self.performance['speedup']:.2f}x\n"
            summary += f"  • Efficiency: {self.performance['efficiency']:.2f}%\n"
        
        summary += f"""
💭 SENTIMENT DISTRIBUTION
"""
        for sentiment, count in self.quality['sentiment_counts'].items():
            pct = self.quality['sentiment_percentages'].get(sentiment, 0)
            summary += f"  • {sentiment.capitalize()}: {count} ({pct:.1f}%)\n"
        
        summary += f"""
🛡️  ROBUSTNESS
  • Total Errors: {sum(self.robustness['errors_per_platform'].values())}
  • Blocked Detected: {self.robustness['blocked_detected']}

💻 ENVIRONMENT
  • CPU: {self.environment['cpu_info']}
  • Cores: {self.environment['num_cores']} physical, {self.environment['num_logical_cores']} logical
  • RAM: {self.environment['ram_gb']} GB
  • OS: {self.environment['os']}
  • Python: {self.environment['python_version']}

═══════════════════════════════════════════════════════════════
"""
        return summary


if __name__ == "__main__":
    # Example usage
    print("=== Academic Metrics Collector - Test ===\n")
    
    collector = AcademicMetricsCollector()
    
    # Start run
    collector.start_run(
        query="Inteligencia Artificial",
        mode="parallel",
        platforms=["x", "instagram", "facebook", "linkedin"],
        n_processes=4
    )
    
    # Simulate platform scraping
    import time
    
    for platform in ["x", "instagram", "facebook", "linkedin"]:
        collector.record_platform_start(platform)
        time.sleep(0.5)  # Simulate work
        collector.record_platform_end(platform, posts=10, comments=50, errors=1)
    
    # Simulate preprocessing and LLM
    collector.record_preprocessing_time(2.5)
    collector.record_llm_time(8.3)
    
    # Add some sentiment results
    for _ in range(150):
        collector.add_sentiment_result("positive")
    for _ in range(50):
        collector.add_sentiment_result("negative")
    for _ in range(100):
        collector.add_sentiment_result("neutral")
    
    # Add dataset rows
    collector.add_dataset_row(
        platform="x",
        post_id="123",
        comment_id="456",
        text="Great product!",
        sentiment="positive",
        sentiment_score=0.95,
        reasoning="Expresses satisfaction"
    )
    
    # End run
    collector.end_run()
    
    # Print summary
    print(collector.get_summary())
    
    # Export all files
    files = collector.export_all()
    print(f"\n✅ All files exported successfully!")
    print(f"   Metrics: {files['metrics']}")
    print(f"   Dataset: {files['dataset']}")
    print(f"   Log: {files['log']}")
