import os
import json
from pathlib import Path

def verify_substance_recursive(base_path, relative_base="", stats=None):
    """Recursively verify html_page field in JSON files."""
    if stats is None:
        stats = {'total': 0, 'ok': 0, 'missing': 0}
    
    for item in sorted(base_path.iterdir()):
        if item.is_dir():
            sub_relative = f"{relative_base}/{item.name}" if relative_base else item.name
            verify_substance_recursive(item, sub_relative, stats)
        elif item.suffix == '.json':
            try:
                with open(item, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                stats['total'] += 1
                if 'html_page' in data:
                    stats['ok'] += 1
                else:
                    stats['missing'] += 1
                    
            except Exception as e:
                pass
    
    return stats

def verify_substance_disorders():
    """Verify Substance_Related_Disorders_out for all three embedding folders."""
    
    folders = [
        "Embedding/Substance_Related_Disorders_out",
        "Embedding_Gemini_3072/Substance_Related_Disorders_out",
        "Embedding_OpenAI_3072/Substance_Related_Disorders_out"
    ]
    
    print("=" * 80)
    print("VERIFICATION - SUBSTANCE-RELATED DISORDERS (structure recursive)")
    print("=" * 80)
    print()
    
    for folder_path in folders:
        print(f"\n[DOSSIER] {folder_path}")
        print("-" * 80)
        
        base_path = Path(folder_path)
        if not base_path.exists():
            print(f"  [WARN] Dossier non trouve!")
            continue
        
        stats = verify_substance_recursive(base_path)
        print(f"  Fichiers JSON: {stats['total']}")
        print(f"  OK: {stats['ok']}")
        print(f"  Manquants: {stats['missing']}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    verify_substance_disorders()
