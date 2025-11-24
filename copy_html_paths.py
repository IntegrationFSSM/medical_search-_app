import os
import json
from pathlib import Path

def copy_html_paths():
    """Copy html_page field from Embedding JSONs to Embedding_Gemini_3072 and Embedding_OpenAI_3072 JSONs."""
    
    source_dir = Path("Embedding")
    target_dirs = [
        Path("Embedding_Gemini_3072"),
        Path("Embedding_OpenAI_3072")
    ]
    
    total_updated = 0
    total_not_found = 0
    total_skipped = 0
    
    print("=" * 80)
    print("Copie des chemins HTML depuis Embedding vers Embedding_Gemini_3072 et Embedding_OpenAI_3072")
    print("=" * 80)
    print()
    
    # Parcourir tous les sous-dossiers de Embedding
    for disorder_dir in sorted(source_dir.iterdir()):
        if not disorder_dir.is_dir():
            continue
        
        print(f"\nTraitement du dossier: {disorder_dir.name}")
        print("-" * 80)
        
        # Trouver tous les fichiers JSON dans ce dossier
        json_files = list(disorder_dir.glob("*.json"))
        
        for json_file in sorted(json_files):
            try:
                # Lire le fichier JSON source
                with open(json_file, 'r', encoding='utf-8') as f:
                    source_data = json.load(f)
                
                # Vérifier si le champ html_page existe
                if 'html_page' not in source_data:
                    print(f"  [SKIP] {json_file.name} - pas de champ html_page")
                    total_skipped += 1
                    continue
                
                html_page = source_data['html_page']
                
                # Mettre à jour dans les deux dossiers cibles
                for target_dir in target_dirs:
                    target_file = target_dir / disorder_dir.name / json_file.name
                    
                    if not target_file.exists():
                        print(f"  [WARN] {target_file.relative_to(target_dir.parent)} - fichier non trouvé")
                        total_not_found += 1
                        continue
                    
                    # Lire le fichier JSON cible
                    with open(target_file, 'r', encoding='utf-8') as f:
                        target_data = json.load(f)
                    
                    # Ajouter ou mettre à jour le champ html_page
                    if 'html_page' in target_data and target_data['html_page'] == html_page:
                        # Déjà à jour
                        continue
                    
                    target_data['html_page'] = html_page
                    
                    # Écrire le fichier JSON mis à jour
                    with open(target_file, 'w', encoding='utf-8') as f:
                        json.dump(target_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"  [OK] {target_file.relative_to(target_dir.parent)}")
                    print(f"       -> html_page: {html_page}")
                    total_updated += 1
                    
            except Exception as e:
                print(f"  [ERROR] {json_file.name}: {e}")
    
    print()
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"Fichiers mis à jour: {total_updated}")
    print(f"Fichiers non trouvés: {total_not_found}")
    print(f"Fichiers ignorés (pas de html_page): {total_skipped}")
    print("=" * 80)

if __name__ == "__main__":
    copy_html_paths()
