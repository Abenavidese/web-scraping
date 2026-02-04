# -*- coding: utf-8 -*-
"""
Migration Script - Move existing data to user-based structure
Migrates data from old output folders to new users/{user_id}/{network}/{query}/ structure
"""

import os
import shutil
import json
import re
from pathlib import Path

def slugify(text):
    """Convert text to slug format"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')

def detect_queries_from_files(directory):
    """Detect queries from metrics file names"""
    queries = set()
    
    if not os.path.exists(directory):
        return queries
    
    for file in os.listdir(directory):
        if file.startswith('metrics_') and file.endswith('.json'):
            # Extract query from filename: metrics_Nicolas Muñoz.json -> Nicolas Muñoz
            query = file.replace('metrics_', '').replace('.json', '')
            queries.add(query)
    
    return queries

def migrate_network_data(network_name, old_output_dir, default_user_dir):
    """Migrate data from a network's output directory"""
    
    if not os.path.exists(old_output_dir):
        print(f"   ⚠️ Directory not found: {old_output_dir}")
        return 0
    
    print(f"\n   📁 Processing {network_name}...")
    
    # Detect queries from metrics files
    queries = detect_queries_from_files(old_output_dir)
    
    if not queries:
        print(f"      No queries detected in {old_output_dir}")
        return 0
    
    migrated_count = 0
    
    for query in queries:
        query_slug = slugify(query)
        
        # Create destination directory
        dest_dir = os.path.join(default_user_dir, network_name, query_slug)
        os.makedirs(dest_dir, exist_ok=True)
        
        print(f"      📝 Query: '{query}' -> {query_slug}/")
        
        # Files to migrate
        files_to_migrate = {
            f'metrics_{query}.json': 'metrics.json',
            'sentiment_results.csv': 'sentiment_results.csv',
            'sentiment_input.csv': 'sentiment_input.csv',
            f'results_{query}.json': 'results.json',
            f'processed_{query}.csv': 'processed.csv',
            f'processed_{query}.json': 'processed.json',
        }
        
        # Migrate files
        for old_name, new_name in files_to_migrate.items():
            old_path = os.path.join(old_output_dir, old_name)
            new_path = os.path.join(dest_dir, new_name)
            
            if os.path.exists(old_path):
                shutil.copy2(old_path, new_path)
                print(f"         ✅ {old_name} -> {new_name}")
                migrated_count += 1
        
        # Migrate visualizations if they exist
        viz_files = [
            f'frecuencia_{query}.png',
            f'frecuencia_{query}_wordcloud.png',
            'frecuencia_palabras.png'
        ]
        
        viz_dir = os.path.join(dest_dir, 'visualizations')
        for viz_file in viz_files:
            old_viz = os.path.join(old_output_dir, viz_file)
            if os.path.exists(old_viz):
                os.makedirs(viz_dir, exist_ok=True)
                shutil.copy2(old_viz, os.path.join(viz_dir, viz_file))
                print(f"         ✅ {viz_file} -> visualizations/")
                migrated_count += 1
    
    return migrated_count

def main():
    """Main migration process"""
    print("=" * 70)
    print("🔄 MIGRATION TO USER-BASED STRUCTURE")
    print("=" * 70)
    
    # Define default user
    default_user = "default"
    default_user_dir = os.path.join("users", default_user)
    
    print(f"\n📦 Creating user directory structure...")
    print(f"   Target: users/{default_user}/")
    
    # Create base structure
    os.makedirs(default_user_dir, exist_ok=True)
    
    # Create profile.json for default user
    profile_path = os.path.join(default_user_dir, "profile.json")
    if not os.path.exists(profile_path):
        profile = {
            "user_id": default_user,
            "username": "Default User",
            "email": "",
            "created_at": "2026-02-03T19:00:00Z",
            "description": "Default user for migrated data"
        }
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Created profile.json")
    
    # Track migration stats
    total_migrated = 0
    
    # Migrate X/Twitter data
    print("\n" + "-" * 70)
    print("1. X/TWITTER")
    print("-" * 70)
    count = migrate_network_data(
        'x',
        'x_scrapper/output',
        default_user_dir
    )
    total_migrated += count
    
    # Migrate Instagram data
    print("\n" + "-" * 70)
    print("2. INSTAGRAM")
    print("-" * 70)
    count = migrate_network_data(
        'instagram',
        'App_Paralela_Instagram/Resultados',
        default_user_dir
    )
    total_migrated += count
    
    # Migrate Facebook data
    print("\n" + "-" * 70)
    print("3. FACEBOOK")
    print("-" * 70)
    count = migrate_network_data(
        'facebook',
        'App_Paralela_facebook/Resultados',
        default_user_dir
    )
    total_migrated += count
    
    # Migrate LinkedIn data
    print("\n" + "-" * 70)
    print("4. LINKEDIN")
    print("-" * 70)
    count = migrate_network_data(
        'linkedin',
        'linkedin_scraper/output',
        default_user_dir
    )
    total_migrated += count
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ MIGRATION COMPLETED")
    print("=" * 70)
    print(f"\n📊 Total files migrated: {total_migrated}")
    print(f"📁 New structure: users/{default_user}/")
    
    # Show directory tree
    print("\n📂 Directory structure:")
    for root, dirs, files in os.walk(default_user_dir):
        level = root.replace(default_user_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:3]:  # Show first 3 files
            print(f"{subindent}{file}")
        if len(files) > 3:
            print(f"{subindent}... ({len(files) - 3} more files)")
    
    print("\n💡 Next steps:")
    print("   1. Run database migration: python migrate_database.py")
    print("   2. Update .env with USER_ID=default")
    print("   3. Re-import data: python import_data.py")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
