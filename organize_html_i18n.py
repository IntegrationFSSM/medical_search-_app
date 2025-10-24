"""
Script pour organiser les pages HTML par langue pour Django i18n
Structure: Embedding/fr/, Embedding/en/, Embedding/es/
"""
import os
import shutil
from pathlib import Path

# Dossier principal
EMBEDDING_DIR = Path('Embedding')

# Créer les sous-dossiers par langue
LANG_DIRS = {
    'fr': EMBEDDING_DIR / 'fr',
    'en': EMBEDDING_DIR / 'en',
    'es': EMBEDDING_DIR / 'es',
}

def create_lang_directories():
    """Créer les répertoires par langue"""
    print("📁 Création des répertoires par langue...")
    for lang, path in LANG_DIRS.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {path} créé")

def organize_existing_html_files():
    """
    Déplacer les fichiers HTML existants dans le dossier fr/
    En préservant la structure des sous-dossiers
    """
    print("\n📦 Organisation des fichiers HTML français...")
    
    # Trouver tous les fichiers HTML à la racine de Embedding
    html_files = list(EMBEDDING_DIR.glob('**/*.html'))
    
    # Filtrer pour ne garder que ceux qui ne sont pas déjà dans fr/en/es
    html_files = [f for f in html_files if not any(lang in f.parts for lang in ['fr', 'en', 'es'])]
    
    print(f"   📊 {len(html_files)} fichiers HTML trouvés")
    
    moved_count = 0
    for html_file in html_files:
        # Calculer le chemin relatif
        relative_path = html_file.relative_to(EMBEDDING_DIR)
        
        # Créer le nouveau chemin dans fr/
        new_path = LANG_DIRS['fr'] / relative_path
        
        # Créer les sous-dossiers si nécessaire
        new_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Déplacer le fichier
        try:
            shutil.copy2(html_file, new_path)
            print(f"   ✅ {relative_path} → fr/{relative_path}")
            moved_count += 1
        except Exception as e:
            print(f"   ❌ Erreur avec {relative_path}: {e}")
    
    print(f"\n✅ {moved_count} fichiers copiés dans fr/")

def copy_to_other_languages():
    """
    Copier les fichiers français vers en/ et es/
    (Pour l'instant, ce sont des copies - à traduire manuellement ou avec un outil)
    """
    print("\n📋 Copie des fichiers vers EN et ES (à traduire)...")
    
    # Trouver tous les fichiers dans fr/
    fr_files = list(LANG_DIRS['fr'].glob('**/*.html'))
    
    print(f"   📊 {len(fr_files)} fichiers à copier")
    
    for lang in ['en', 'es']:
        print(f"\n   🌍 Copie vers {lang.upper()}...")
        copied = 0
        
        for fr_file in fr_files:
            # Calculer le chemin relatif par rapport à fr/
            relative_path = fr_file.relative_to(LANG_DIRS['fr'])
            
            # Créer le nouveau chemin dans la langue cible
            target_path = LANG_DIRS[lang] / relative_path
            
            # Créer les sous-dossiers si nécessaire
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copier le fichier
            try:
                shutil.copy2(fr_file, target_path)
                copied += 1
            except Exception as e:
                print(f"      ❌ Erreur avec {relative_path}: {e}")
        
        print(f"      ✅ {copied} fichiers copiés dans {lang}/")

def create_structure_summary():
    """Afficher un résumé de la structure créée"""
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DE LA STRUCTURE CRÉÉE")
    print("="*60)
    
    for lang, path in LANG_DIRS.items():
        if path.exists():
            html_count = len(list(path.glob('**/*.html')))
            print(f"   🌍 {lang.upper()}: {html_count} fichiers HTML")
            
            # Afficher les sous-dossiers
            subdirs = [d for d in path.iterdir() if d.is_dir()]
            if subdirs:
                print(f"      📁 Sous-dossiers: {', '.join([d.name for d in subdirs])}")
    
    print("\n" + "="*60)

def main():
    """Fonction principale"""
    print("🌍 ORGANISATION DES PAGES HTML POUR DJANGO i18n")
    print("="*60)
    
    # Vérifier que le dossier Embedding existe
    if not EMBEDDING_DIR.exists():
        print(f"❌ Erreur: Le dossier {EMBEDDING_DIR} n'existe pas!")
        return
    
    # Créer les répertoires
    create_lang_directories()
    
    # Organiser les fichiers existants
    organize_existing_html_files()
    
    # Copier vers les autres langues
    copy_to_other_languages()
    
    # Afficher le résumé
    create_structure_summary()
    
    print("\n✅ Organisation terminée!")
    print("\n📝 PROCHAINES ÉTAPES:")
    print("   1. Les fichiers français sont dans Embedding/fr/")
    print("   2. Les fichiers anglais (copies FR) sont dans Embedding/en/ - À TRADUIRE")
    print("   3. Les fichiers espagnols (copies FR) sont dans Embedding/es/ - À TRADUIRE")
    print("\n💡 OPTIONS DE TRADUCTION:")
    print("   • Manuelle: Éditer les fichiers en/ et es/ un par un")
    print("   • Automatique: Utiliser un script de traduction (Google Translate, DeepL, etc.)")
    print("   • Hybride: Traduction automatique puis révision manuelle")

if __name__ == '__main__':
    main()

