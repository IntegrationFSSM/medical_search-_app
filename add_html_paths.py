import json
import os
from pathlib import Path

def get_html_mapping():
    """Create a mapping from JSON file names to HTML file paths from the Embedding folder."""
    embedding_dir = Path("Embedding")
    html_mapping = {}
    
    # Scan all subdirectories in Embedding folder
    for disorder_dir in embedding_dir.iterdir():
        if disorder_dir.is_dir():
            # Find all HTML files in this disorder directory
            for html_file in disorder_dir.glob("*.html"):
                # Store the relative path from the project root
                relative_path = str(html_file).replace("\\", "/")
                html_mapping[html_file.stem] = relative_path
    
    return html_mapping

def find_matching_html(json_file_stem, html_mapping):
    """Find the matching HTML file for a given JSON file."""
    # Try direct match first
    if json_file_stem in html_mapping:
        return html_mapping[json_file_stem]
    
    # Try to match based on the disorder name in the JSON
    # The JSON files are named like "SubSection1_Separation_Anxiety_Disorder"
    # The HTML files are named like "separation-anxiety-disorder"
    
    # Extract the disorder name part (after SubSectionX_)
    if "_" in json_file_stem:
        parts = json_file_stem.split("_", 1)
        if len(parts) > 1 and parts[0].startswith("SubSection"):
            disorder_name = parts[1]
            # Convert to lowercase and replace underscores with hyphens
            html_name = disorder_name.lower().replace("_", "-")
            
            # Search for matching HTML file
            for html_stem, html_path in html_mapping.items():
                if html_stem.lower() == html_name:
                    return html_path
    
    return None

def update_json_files(base_dir, html_mapping):
    """Update all JSON files in the given directory with html_page field."""
    base_path = Path(base_dir)
    updated_count = 0
    not_found_count = 0
    
    # Scan all subdirectories
    for disorder_dir in base_path.iterdir():
        if disorder_dir.is_dir():
            # Find all JSON files in this disorder directory
            for json_file in disorder_dir.glob("*.json"):
                try:
                    # Read the JSON file
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check if html_page field already exists
                    if 'html_page' in data:
                        print(f"Skipping {json_file.name} - html_page already exists")
                        continue
                    
                    # Find matching HTML file
                    html_path = find_matching_html(json_file.stem, html_mapping)
                    
                    if html_path:
                        # Add the html_page field
                        data['html_page'] = html_path
                        
                        # Write back to the JSON file
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        
                        print(f"[OK] Updated {json_file.name} with html_page: {html_path}")
                        updated_count += 1
                    else:
                        print(f"[WARN] No matching HTML found for {json_file.name}")
                        not_found_count += 1
                
                except Exception as e:
                    print(f"Error processing {json_file}: {e}")
    
    return updated_count, not_found_count

def main():
    print("=" * 80)
    print("Adding html_page field to JSON files in Embedding_Gemini_3072 and Embedding_OpenAI_3072")
    print("=" * 80)
    
    # Get HTML mapping from Embedding folder
    print("\n1. Scanning Embedding folder for HTML files...")
    html_mapping = get_html_mapping()
    print(f"   Found {len(html_mapping)} HTML files")
    
    # Update Embedding_Gemini_3072
    print("\n2. Updating JSON files in Embedding_Gemini_3072...")
    gemini_updated, gemini_not_found = update_json_files("Embedding_Gemini_3072", html_mapping)
    print(f"   Updated: {gemini_updated}, Not found: {gemini_not_found}")
    
    # Update Embedding_OpenAI_3072
    print("\n3. Updating JSON files in Embedding_OpenAI_3072...")
    openai_updated, openai_not_found = update_json_files("Embedding_OpenAI_3072", html_mapping)
    print(f"   Updated: {openai_updated}, Not found: {openai_not_found}")
    
    print("\n" + "=" * 80)
    print(f"TOTAL: Updated {gemini_updated + openai_updated} files")
    print("=" * 80)

if __name__ == "__main__":
    main()
