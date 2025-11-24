import os
import json
from pathlib import Path

def verify_neurodevelopmental_html_paths():
    """Verify html_page paths in Neurodevelopmental_Disorders_out (with subdirectories)."""
    
    base_folders = [
        "Embedding/Neurodevelopmental_Disorders_out",
        "Embedding_Gemini_3072/Neurodevelopmental_Disorders_out",
        "Embedding_OpenAI_3072/Neurodevelopmental_Disorders_out"
    ]
    
    print("=" * 80)
    print("VERIFICATION - NEURODEVELOPMENTAL DISORDERS (avec sous-dossiers)")
    print("=" * 80)
    print()
    
    for base_folder in base_folders:
        print(f"\n[DOSSIER PRINCIPAL] {base_folder}")
        print("=" * 80)
        
        if not os.path.exists(base_folder):
            print(f"  [WARN] Dossier non trouve!")
            continue
        
        # Parcourir tous les sous-dossiers
        subdirs = sorted([d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))])
        
        total_files = 0
        total_ok = 0
        total_missing = 0
        
        for subdir in subdirs:
            subdir_path = os.path.join(base_folder, subdir)
            print(f"\n  [SOUS-DOSSIER] {subdir}")
            print("  " + "-" * 76)
            
            json_files = sorted([f for f in os.listdir(subdir_path) if f.endswith('.json')])
            
            if not json_files:
                print(f"    [WARN] Aucun fichier JSON trouve!")
                continue
            
            for jf in json_files:
                json_path = os.path.join(subdir_path, jf)
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    html_page = data.get('html_page', '[NON TROUVE]')
                    
                    if html_page == '[NON TROUVE]':
                        print(f"    [X] {jf}")
                        print(f"        html_page: {html_page}")
                        total_missing += 1
                    else:
                        print(f"    [OK] {jf}")
                        print(f"        html_page: \"{html_page}\"")
                        total_ok += 1
                    
                    total_files += 1
                    
                except Exception as e:
                    print(f"    [ERROR] {jf}: {e}")
        
        print(f"\n  TOTAL pour {base_folder}:")
        print(f"    Fichiers JSON: {total_files}")
        print(f"    OK: {total_ok}")
        print(f"    Manquants: {total_missing}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    verify_neurodevelopmental_html_paths()
