import os
import json
from pathlib import Path

def add_html_paths_personality():
    """Add html_page field to Personality_Disorders JSON files in Gemini and OpenAI folders."""
    
    source_base = Path("Embedding/Personality_Disorders_out")
    target_bases = [
        Path("Embedding_Gemini_3072/Personality_Disorders_out"),
        Path("Embedding_OpenAI_3072/Personality_Disorders_out")
    ]
    
    print("=" * 80)
    print("AJOUT DES CHEMINS HTML - PERSONALITY DISORDERS")
    print("=" * 80)
    print()
    
    total_updated = 0
    total_not_found = 0
    
    # Parcourir tous les sous-dossiers du dossier source
    for subdir in sorted(source_base.iterdir()):
        if not subdir.is_dir():
            continue
        
        print(f"\n[SOUS-DOSSIER] {subdir.name}")
        print("-" * 80)
        
        # Trouver tous les fichiers JSON dans ce sous-dossier
        for json_file in sorted(subdir.glob("*.json")):
            try:
                # Lire le fichier JSON source
                with open(json_file, 'r', encoding='utf-8') as f:
                    source_data = json.load(f)
                
                # Vérifier si le champ html_page existe
                if 'html_page' not in source_data:
                    # Chercher le fichier HTML correspondant
                    html_files = list(subdir.glob("*.html"))
                    
                    if not html_files:
                        print(f"  [WARN] Aucun fichier HTML trouve dans {subdir.name}")
                        continue
                    
                    # Prendre le premier fichier HTML (normalement il n'y en a qu'un par sous-dossier)
                    html_file = html_files[0]
                    
                    # Créer le chemin relatif
                    relative_html_path = f"Personality_Disorders_out/{subdir.name}/{html_file.name}"
                    
                    # Ajouter le champ html_page au fichier source
                    source_data['html_page'] = relative_html_path
                    
                    # Écrire le fichier JSON source mis à jour
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(source_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"  [OK] Source: {json_file.name}")
                    print(f"       -> html_page: {relative_html_path}")
                else:
                    relative_html_path = source_data['html_page']
                    print(f"  [SKIP] Source: {json_file.name} - html_page deja present")
                
                # Mettre à jour dans les deux dossiers cibles
                for target_base in target_bases:
                    target_file = target_base / subdir.name / json_file.name
                    
                    if not target_file.exists():
                        print(f"  [WARN] {target_file.relative_to(target_base.parent)} - fichier non trouve")
                        total_not_found += 1
                        continue
                    
                    # Lire le fichier JSON cible
                    with open(target_file, 'r', encoding='utf-8') as f:
                        target_data = json.load(f)
                    
                    # Ajouter ou mettre à jour le champ html_page
                    if 'html_page' in target_data and target_data['html_page'] == relative_html_path:
                        # Déjà à jour
                        continue
                    
                    target_data['html_page'] = relative_html_path
                    
                    # Écrire le fichier JSON mis à jour
                    with open(target_file, 'w', encoding='utf-8') as f:
                        json.dump(target_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"  [OK] {target_file.relative_to(target_base.parent)}")
                    print(f"       -> html_page: {relative_html_path}")
                    total_updated += 1
                    
            except Exception as e:
                print(f"  [ERROR] {json_file.name}: {e}")
    
    print()
    print("=" * 80)
    print("RESUME")
    print("=" * 80)
    print(f"Fichiers mis a jour: {total_updated}")
    print(f"Fichiers non trouves: {total_not_found}")
    print("=" * 80)

if __name__ == "__main__":
    add_html_paths_personality()
