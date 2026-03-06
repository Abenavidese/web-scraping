# -*- coding: utf-8 -*-
"""
Data Cleaner - Phase 2 ETL Pipeline
Provides normalization, deduplication, text cleaning (semantic & intensity views),
feature extraction, and data quality reporting.
"""

import os
import re
import string
import hashlib
import pandas as pd
from typing import List, Dict, Any, Tuple
import datetime

try:
    import emoji
except ImportError:
    print("WARNING: 'emoji' library not installed. Emoji features will be limited.")

try:
    from langdetect import detect
    import langdetect.DetectorFactory
    # Set seed for reproducible language detection
    langdetect.DetectorFactory.seed = 0
except ImportError:
    print("WARNING: 'langdetect' library not installed. Language detection will be skipped.")


class ETLProcessor:
    """Handles Phase 2 Data Cleaning and Staging Pipelines"""
    
    def __init__(self):
        # Basic Spanish stopwords to optionally remove
        self.stopwords = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber',
            'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le', 'lo', 'todo',
            'pero', 'más', 'hacer', 'o', 'poder', 'decir', 'este', 'ir', 'otro', 'ese',
            'la', 'si', 'me', 'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy',
            'sin', 'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno', 'mismo',
            'yo', 'también', 'hasta', 'año', 'dos', 'querer', 'entre', 'así', 'primero',
            'desde', 'grande', 'eso', 'ni', 'nos', 'llegar', 'pasar', 'tiempo', 'ella'
        }
        
        # Advanced URL pattern to catch broken URLs with spaces (e.g. "https:// site.com/page?id=1 1234&b=2 ...")
        self.url_pattern = re.compile(
            r'(?:https?:\/\/\s*|www\.)[^\s]+(?:\s+[^\s]*[\&\?\=\.\/][^\s]*)*\s*(?:…|\.\.\.)?', 
            re.IGNORECASE
        )
        
    def _normalize_timestamps(self, df: pd.DataFrame, time_col: str = 'timestamp') -> pd.DataFrame:
        """Normalizes timestamps to UTC ISO-8601 and derives year/month"""
        df = df.copy()
        
        if time_col not in df.columns:
            return df
            
        def convert_to_utc_iso(ts):
            if pd.isna(ts) or not str(ts).strip():
                return None
            try:
                # Parse robustly using pandas
                dt = pd.to_datetime(ts, utc=True)
                return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            except Exception:
                return None
                
        # Create normalized timestamp
        df['normalized_timestamp'] = df[time_col].apply(convert_to_utc_iso)
        
        # Derive year and month from the robustly converted dt
        def extract_year(ts):
            try: return pd.to_datetime(ts).year if pd.notna(ts) else None
            except: return None
            
        def extract_month(ts):
            try: return pd.to_datetime(ts).month if pd.notna(ts) else None
            except: return None
            
        # Inoculate year and month only if they don't exist
        if 'year' not in df.columns or df['year'].isna().all():
            df['year'] = df['normalized_timestamp'].apply(extract_year)
        if 'month' not in df.columns or df['month'].isna().all():
            df['month'] = df['normalized_timestamp'].apply(extract_month)
            
        return df

    def _hash_for_dedup(self, text: str) -> str:
        """Creates a normalized hash for exact deduplication"""
        if not isinstance(text, str) or not text.strip():
            return ""
        
        # normalize for hash
        t = text.lower()
        t = self.url_pattern.sub('', t)
        t = re.sub(r'@\w+', '', t) # remove mentions
        t = re.sub(r'\s+', ' ', t).strip() # normalize whitespace
        
        return hashlib.sha1(t.encode('utf-8')).hexdigest()

    def deduplicate(self, df: pd.DataFrame, text_col: str = 'text') -> pd.DataFrame:
        """Identifies exact duplicates and marks them"""
        df = df.copy()
        if text_col not in df.columns:
            df['is_duplicate'] = False
            return df
            
        df['text_hash'] = df[text_col].apply(self._hash_for_dedup)
        
        # Mark duplicates (keep first)
        # Empty hash means empty text, we shouldn't consider them "duplicates" of each other in the exact same way or maybe we drop them. 
        # But let's follow the standard rule.
        df['is_duplicate'] = df.duplicated(subset=['text_hash'], keep='first')
        
        # Unmark empty hashes just in case
        df.loc[df['text_hash'] == "", 'is_duplicate'] = False
        
        return df
        
    def _extract_features(self, text: str) -> Dict[str, Any]:
        """Extracts text metadata features"""
        if pd.isna(text) or not isinstance(text, str):
            return {
                'len_chars': 0, 'len_tokens': 0, 'num_exclamations': 0, 
                'num_questions': 0, 'caps_ratio': 0.0, 'emoji_count': 0, 
                'url_count': 0, 'profanity_flag': False
            }
            
        char_len = len(text)
        tokens = text.split()
        tok_len = len(tokens)
        
        excl_count = text.count('!')
        ques_count = text.count('?')
        
        # Caps ratio
        alpha_chars = sum(1 for c in text if c.isalpha())
        upper_chars = sum(1 for c in text if c.isupper())
        caps_ratio = upper_chars / alpha_chars if alpha_chars > 0 else 0.0
        
        # Emojis processing
        emo_count = 0
        try:
            emo_count = emoji.emoji_count(text)
        except NameError:
            pass # emoji library not loaded
            
        # URL count
        urls = self.url_pattern.findall(text)
        url_count = len(urls)
        
        # Quick heuristic profanity check (expand based on needs)
        profane_words = {'mierda', 'puta', 'puto', 'verga', 'pendejo', 'carajo', 'cojudo'}
        text_lower = text.lower()
        profane_flag = any(pw in text_lower for pw in profane_words)
        
        return {
            'len_chars': char_len,
            'len_tokens': tok_len,
            'num_exclamations': excl_count,
            'num_questions': ques_count,
            'caps_ratio': round(caps_ratio, 3),
            'emoji_count': emo_count,
            'url_count': url_count,
            'profanity_flag': profane_flag
        }

    def _clean_semantic(self, text: str) -> str:
        """
        Clean text for semantic analysis (valence/emotion).
        Lowercase, remove URLs, remove mentions, keep hashtags (text only), normalize space.
        """
        if pd.isna(text) or not isinstance(text, str):
            return ""
            
        # Lowercase
        t = text.lower()
        
        # Remove URLs using strict robust pattern
        t = self.url_pattern.sub('', t)
        
        # Remove Mentions
        t = re.sub(r'@\w+', '', t)
        
        # Remove '#' from hashtags but keep the term
        t = t.replace('#', '')
        
        # Normalize spaces
        t = re.sub(r'\s+', ' ', t).strip()
        
        return t

    def _clean_intensity(self, text: str) -> str:
        """
        Clean text for intensity/arousal analysis.
        Keep CAPS, !!! ???, elongations, and repetition. Emphasize intensity features.
        """
        if pd.isna(text) or not isinstance(text, str):
            return ""
            
        t = text
        # Remove URLs
        t = self.url_pattern.sub('', t)
        
        # Remove Mentions
        t = re.sub(r'@\w+', '', t)
        
        # Map emojis to text if possible to maintain intensity signal
        try:
            t = emoji.demojize(t, language='es')
        except NameError:
            pass # keep as is
            
        # Normalize spaces
        t = re.sub(r'\s+', ' ', t).strip()
        
        return t

    def _detect_language(self, text: str) -> str:
        """Detect language using langdetect"""
        if pd.isna(text) or not isinstance(text, str) or not text.strip():
            return "unknown"
        
        # Only use top 100 chars for speed
        short_text = text[:100]
        try:
            return detect(short_text)
        except:
            return "unknown"

    def _detect_spam(self, features: Dict[str, Any], text: str) -> bool:
        """Detect obvious spam based on extracted features and text"""
        if pd.isna(text) or not isinstance(text, str):
            return False
            
        # Too many URLs
        if features['url_count'] > 2:
            return True
            
        # Text is ONLY links
        t_no_links = self.url_pattern.sub('', text).strip()
        if features['url_count'] > 0 and len(t_no_links) < 5:
            return True
            
        # Too many hashtags
        if text.count('#') > 5:
            return True
            
        # Extreme repetition (very long single words "haaaaaaaaahahahahha" or repeated chunks)
        # We can implement a simple heuristic: if max word len > 40 chars
        words = text.split()
        if words and max([len(w) for w in words]) > 40:
            if not any(url in text for url in ["http", "www"]): # URLs can be long
                return True
                
        return False

    def _detect_noise(self, features: Dict[str, Any], text: str) -> bool:
        """Detect extreme noise: < 3 words, only laughs, only emojis, only short insults"""
        if pd.isna(text) or not isinstance(text, str):
            return True
            
        text_clean = text.strip()
        if not text_clean:
            return True
        
        # 1. Less than 3 words
        if features['len_tokens'] < 3:
            return True
            
        # 2. Only laughs (match jaja, haha, ksks, hjhj)
        text_lower = text_clean.lower()
        laughs = re.compile(r'(ja|ha|he|je|ka|ks|js)+')
        no_laugh = laughs.sub('', text_lower).strip()
        if len(no_laugh) < 5:
            return True
            
        # 3. Only emojis
        if features['len_chars'] > 0 and features['emoji_count'] > 0:
            try:
                import emoji
                no_emoji = emoji.replace_emoji(text_clean, replace='').strip()
                if len(no_emoji) < 5:
                    return True
            except NameError:
                pass
                
        # 4. Only short insults
        if features['profanity_flag'] and features['len_tokens'] < 5:
            return True
            
        return False

    def run_etl_pipeline(self, df_raw: pd.DataFrame, platform: str, run_id: str = "default_run", topic_keywords: List[str] = None) -> pd.DataFrame:
        """
        Runs the full Phase 2 ETL pipeline on the raw DataFrame.
        """
        print(f"Starting Phase 2 ETL Pipeline for {platform}...")
        df = df_raw.copy()
        
        n_raw = len(df)
        
        # 1. Normalization & Timestamps
        print("  - Normalizing timestamps...")
        df = self._normalize_timestamps(df, time_col='timestamp')
        
        # 2. Deduplication
        print("  - Deduplicating...")
        text_column = 'text' if 'text' in df.columns else 'content'
        df = self.deduplicate(df, text_col=text_column)
        n_after_dedupe = len(df[~df['is_duplicate']])
        
        # 3. Cleaning & Feature Extraction
        print("  - Applying Text Cleaning & Feature Extraction...")
        # Add tracking dicts
        features_list = []
        clean_semantic_list = []
        clean_intensity_list = []
        lang_list = []
        spam_list = []
        noise_list = []
        rel_list = []
        
        for idx, row in df.iterrows():
            text = str(row.get(text_column, ''))
            
            # Features
            feats = self._extract_features(text)
            features_list.append(feats)
            
            # Cleaning Views
            clean_sem = self._clean_semantic(text)
            clean_int = self._clean_intensity(text)
            clean_semantic_list.append(clean_sem)
            clean_intensity_list.append(clean_int)
            
            # Language (on semantic text is faster/better)
            lang = self._detect_language(clean_sem)
            lang_list.append(lang)
            
            # Spam & Noise
            is_spam = self._detect_spam(feats, text)
            spam_list.append(is_spam)
            
            is_noise = self._detect_noise(feats, text)
            noise_list.append(is_noise)
            
            # Relevance
            is_rel = True
            if topic_keywords:
                # Check if any keyword matches semantic text (or the original text)
                is_rel = any(kw.lower() in clean_sem for kw in topic_keywords)
            rel_list.append(is_rel)
            
        # Merge lists into DataFrame
        if len(features_list) > 0:
            feats_df = pd.DataFrame(features_list)
            for col in feats_df.columns:
                df[col] = feats_df[col]
        else:
            df['len_chars'] = []
            df['len_tokens'] = []
            df['caps_ratio'] = []
            df['num_emojis'] = []
            df['num_urls'] = []
            df['num_mentions'] = []
            df['num_hashtags'] = []
            
        df['text_clean_semantic'] = clean_semantic_list
        df['text_clean_intensity'] = clean_intensity_list
        df['language'] = lang_list
        df['is_spam'] = spam_list
        df['is_noise'] = noise_list
        df['is_relevant'] = rel_list
        
        # Calculate Quality Metrics
        n_after_lang_filter = len(df[(~df['is_duplicate']) & (df['language'] == 'es')]) if n_raw > 0 else 0
        n_after_spam = len(df[(~df['is_duplicate']) & (df['language'] == 'es') & (~df['is_spam'])]) if n_raw > 0 else 0
        n_after_noise = len(df[(~df['is_duplicate']) & (df['language'] == 'es') & (~df['is_spam']) & (~df['is_noise'])]) if n_raw > 0 else 0
        
        perc_dupes = (n_raw - n_after_dedupe) / n_raw * 100 if n_raw > 0 else 0
        perc_non_es = len(df[df['language'] != 'es']) / n_raw * 100 if n_raw > 0 else 0
        perc_spam = len(df[df['is_spam']]) / n_raw * 100 if n_raw > 0 else 0
        perc_noise = len(df[df['is_noise']]) / n_raw * 100 if n_raw > 0 else 0
        
        median_len_tokens = df['len_tokens'].median() if n_raw > 0 and len(df['len_tokens']) > 0 else 0.0
        
        report_row = {
            'run_id': run_id,
            'platform': platform,
            'timestamp': datetime.datetime.now().isoformat(),
            'N_raw': n_raw,
            'N_after_dedupe': n_after_dedupe,
            'N_after_lang_filter': n_after_lang_filter,
            'N_after_spam_filter': n_after_spam,

            'N_after_noise_filter': n_after_noise,
            'percent_duplicates': round(perc_dupes, 2),
            'percent_non_es': round(perc_non_es, 2),
            'percent_spam': round(perc_spam, 2),
            'percent_noise': round(perc_noise, 2),
            'median_len_tokens': round(median_len_tokens, 2)
        }
        
        # Save Report
        report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
        os.makedirs(report_dir, exist_ok=True)
        
        report_df = pd.DataFrame([report_row])
        report_path = os.path.join(report_dir, f'data_quality_{run_id}.csv')
        
        # Append to existing or create new
        if os.path.exists(report_path):
            existing_df = pd.read_csv(report_path)
            report_df = pd.concat([existing_df, report_df], ignore_index=True)
            
        report_df.to_csv(report_path, index=False, encoding='utf-8')
        print(f"  - Quality report saved to {report_path}")
        
        return df
