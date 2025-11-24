import os
import json

def extract_html_paths(folder):
    """Extract html_page paths from all JSON files in a folder."""
    json_files = [f for f in os.listdir(folder) if f.endswith('.json')]
    
    print(f"Extraction des chemins HTML depuis: {folder}")
    print("=" * 80)
    print()
    
    results = []
    for jf in sorted(json_files):
        path = os.path.join(folder, jf)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            html_page = data.get('html_page', 'NON TROUVE')
            results.append((jf, html_page))
            print(f"{jf}:")
            print(f'  "html_page": "{html_page}"')
            print()
        except Exception as e:
            print(f"ERREUR avec {jf}: {e}")
            print()
    
    print("=" * 80)
    print(f"Total: {len(results)} fichiers JSON traites")
    return results

if __name__ == "__main__":
    # Extract from Anxiety_Disorders_out
    extract_html_paths("Embedding/Anxiety_Disorders_out")
