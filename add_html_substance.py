import os
import json
from pathlib import Path

def get_html_mapping_recursive(base_path, relative_base="", mapping=None):
    """Recursively build mapping of JSON files to HTML files."""
    if mapping is None:
        mapping = {}
    
    for item in sorted(base_path.iterdir()):
        if item.is_dir():
            sub_relative = f"{relative_base}/{item.name}" if relative_base else item.name
            get_html_mapping_recursive(item, sub_relative, mapping)
        elif item.suffix == '.json':
            # Find HTML file in same directory
            html_files = list(item.parent.glob("*.html"))
            if html_files:
                html_file = html_files[0]
                relative_html_path = f"Substance_Related_Disorders_out/{relative_base}/{html_file.name}"
                # Use relative path as key
                json_relative = f"{relative_base}/{item.name}"
                mapping[json_relative] = relative_html_path
    
    return mapping

def update_json_recursive(base_path, html_mapping, relative_base="", updated_count=0):
    """Recursively update JSON files with html_page field."""
    
    for item in sorted(base_path.iterdir()):
        if item.is_dir():
            sub_relative = f"{relative_base}/{item.name}" if relative_base else item.name
            updated_count = update_json_recursive(item, html_mapping, sub_relative, updated_count)
        elif item.suffix == '.json':
            try:
                # Read JSON
                with open(item, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if already has html_page
                json_relative = f"{relative_base}/{item.name}"
                if json_relative in html_mapping:
                    html_path = html_mapping[json_relative]
                    
                    if 'html_page' in data and data['html_page'] == html_path:
                        continue
                    
                    data['html_page'] = html_path
                    
                    # Write back
                    with open(item, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    print(f"  [OK] {json_relative}")
                    updated_count += 1
                    
            except Exception as e:
                print(f"  [ERROR] {item.name}: {e}")
    
    return updated_count

def process_substance_disorders():
    """Process Substance_Related_Disorders_out."""
    
    print("=" * 80)
    print("AJOUT DES CHEMINS HTML - SUBSTANCE-RELATED DISORDERS")
    print("=" * 80)
    print()
    
    # Build HTML mapping from source
    print("[1] Construction du mapping HTML depuis Embedding...")
    source_path = Path("Embedding/Substance_Related_Disorders_out")
    html_mapping = get_html_mapping_recursive(source_path)
    print(f"    Trouve {len(html_mapping)} fichiers JSON avec HTML")
    
    # Update Gemini
    print("\n[2] Mise a jour Embedding_Gemini_3072...")
    gemini_path = Path("Embedding_Gemini_3072/Substance_Related_Disorders_out")
    gemini_updated = update_json_recursive(gemini_path, html_mapping)
    print(f"    Total mis a jour: {gemini_updated}")
    
    # Update OpenAI
    print("\n[3] Mise a jour Embedding_OpenAI_3072...")
    openai_path = Path("Embedding_OpenAI_3072/Substance_Related_Disorders_out")
    openai_updated = update_json_recursive(openai_path, html_mapping)
    print(f"    Total mis a jour: {openai_updated}")
    
    print("\n" + "=" * 80)
    print(f"TOTAL: {gemini_updated + openai_updated} fichiers mis a jour")
    print("=" * 80)

if __name__ == "__main__":
    process_substance_disorders()
