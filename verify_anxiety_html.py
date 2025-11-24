import os
import json

def verify_anxiety_disorder_html_paths():
    """Verify html_page paths in Trauma_Stress_Disorders_out for all three embedding folders."""
    
    folders = [
        "Embedding/Trauma_Stress_Disorders_out",
        "Embedding_Gemini_3072/Trauma_Stress_Disorders_out",
        "Embedding_OpenAI_3072/Trauma_Stress_Disorders_out"
    ]
    
    print("=" * 80)
    print("VERIFICATION - TRAUMA AND STRESSOR-RELATED DISORDERS")
    print("=" * 80)
    print()
    
    for folder in folders:
        print(f"\n[DOSSIER] {folder}")
        print("-" * 80)
        
        if not os.path.exists(folder):
            print(f"  [WARN] Dossier non trouve!")
            continue
        
        json_files = sorted([f for f in os.listdir(folder) if f.endswith('.json')])
        
        if not json_files:
            print(f"  [WARN] Aucun fichier JSON trouve!")
            continue
        
        for jf in json_files:
            path = os.path.join(folder, jf)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                html_page = data.get('html_page', '[NON TROUVE]')
                
                if html_page == '[NON TROUVE]':
                    print(f"  [X] {jf}")
                    print(f"      html_page: {html_page}")
                else:
                    print(f"  [OK] {jf}")
                    print(f"      html_page: \"{html_page}\"")
                
            except Exception as e:
                print(f"  ⚠️  ERREUR avec {jf}: {e}")
        
        print(f"\n  Total: {len(json_files)} fichiers JSON")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    verify_anxiety_disorder_html_paths()
