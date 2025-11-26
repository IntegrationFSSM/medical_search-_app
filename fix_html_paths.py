import os
import json
from pathlib import Path

def fix_html_paths():
    """Fix html_page paths in Embedding_Gemini_3072 and Embedding_OpenAI_3072 by removing the 'Embedding/' prefix."""
    
    target_dirs = [
        Path("Embedding_Gemini_3072"),
        Path("Embedding_OpenAI_3072")
    ]
    
    total_fixed = 0
    total_already_correct = 0
    total_errors = 0
    
    print("=" * 80)
    print("Correction des chemins HTML dans Embedding_Gemini_3072 et Embedding_OpenAI_3072")
    print("=" * 80)
    print()
    
    for target_dir in target_dirs:
        print(f"\n{'='*80}")
        print(f"Traitement du dossier: {target_dir}")
        print(f"{'='*80}\n")
        
        # Parcourir tous les sous-dossiers
        for root, dirs, files in os.walk(target_dir):
            root_path = Path(root)
            
            for file in files:
                if not file.endswith('.json'):
                    continue
                
                json_file = root_path / file
                
                try:
                    # Lire le fichier JSON
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Vérifier si le champ html_page existe
                    if 'html_page' not in data:
                        continue
                    
                    html_page = data['html_page']
                    
                    # Vérifier si le chemin commence par "Embedding/"
                    if html_page.startswith('Embedding/'):
                        # Supprimer le préfixe "Embedding/"
                        new_html_page = html_page.replace('Embedding/', '', 1)
                        
                        # Mettre à jour
                        data['html_page'] = new_html_page
                        
                        # Écrire le fichier JSON mis à jour
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        
                        print(f"✓ {json_file.relative_to(target_dir.parent)}")
                        print(f"  Ancien: {html_page}")
                        print(f"  Nouveau: {new_html_page}")
                        print()
                        total_fixed += 1
                    else:
                        total_already_correct += 1
                        
                except Exception as e:
                    print(f"✗ ERREUR {json_file.relative_to(target_dir.parent)}: {e}")
                    print()
                    total_errors += 1
    
    print()
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"Fichiers corrigés: {total_fixed}")
    print(f"Fichiers déjà corrects: {total_already_correct}")
    print(f"Erreurs: {total_errors}")
    print("=" * 80)

if __name__ == "__main__":
    fix_html_paths()
