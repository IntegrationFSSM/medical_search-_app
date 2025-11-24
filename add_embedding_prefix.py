import os
import json
from pathlib import Path

def update_html_paths_recursive(base_path, updated_count=0):
    """Recursively update html_page paths to add 'Embedding/' prefix."""
    
    for item in sorted(base_path.iterdir()):
        if item.is_dir():
            updated_count = update_html_paths_recursive(item, updated_count)
        elif item.suffix == '.json':
            try:
                # Read JSON
                with open(item, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if html_page exists and doesn't already start with 'Embedding/'
                if 'html_page' in data:
                    html_path = data['html_page']
                    
                    if not html_path.startswith('Embedding/'):
                        # Add 'Embedding/' prefix
                        data['html_page'] = f"Embedding/{html_path}"
                        
                        # Write back
                        with open(item, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        
                        updated_count += 1
                        
            except Exception as e:
                print(f"  [ERROR] {item.name}: {e}")
    
    return updated_count

def add_embedding_prefix():
    """Add 'Embedding/' prefix to all html_page paths in Gemini and OpenAI folders."""
    
    folders = [
        "Embedding_Gemini_3072",
        "Embedding_OpenAI_3072"
    ]
    
    print("=" * 80)
    print("AJOUT DU PREFIXE 'Embedding/' AUX CHEMINS HTML")
    print("=" * 80)
    print()
    
    total_updated = 0
    
    for folder_name in folders:
        print(f"\n[DOSSIER] {folder_name}")
        print("-" * 80)
        
        folder_path = Path(folder_name)
        if not folder_path.exists():
            print(f"  [WARN] Dossier non trouve!")
            continue
        
        updated = update_html_paths_recursive(folder_path)
        total_updated += updated
        print(f"  Total mis a jour: {updated}")
    
    print("\n" + "=" * 80)
    print(f"TOTAL: {total_updated} fichiers mis a jour")
    print("=" * 80)

if __name__ == "__main__":
    add_embedding_prefix()
