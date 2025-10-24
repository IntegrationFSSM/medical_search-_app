"""
Script pour traduire automatiquement les pages HTML avec Google Translate
(Gratuit, sans utiliser OpenAI)
"""
import os
from pathlib import Path
from bs4 import BeautifulSoup
import time

# Installation requise: pip install googletrans==4.0.0rc1
try:
    from googletrans import Translator
    translator = Translator()
except ImportError:
    print("❌ Erreur: googletrans n'est pas installé!")
    print("   Installez-le avec: pip install googletrans==4.0.0rc1")
    exit(1)

# Dossiers
EMBEDDING_DIR = Path('Embedding')
FR_DIR = EMBEDDING_DIR / 'fr'
EN_DIR = EMBEDDING_DIR / 'en'
ES_DIR = EMBEDDING_DIR / 'es'

def translate_text(text, dest_lang):
    """Traduire un texte avec Google Translate"""
    try:
        result = translator.translate(text, src='fr', dest=dest_lang)
        return result.text
    except Exception as e:
        print(f"      ⚠️  Erreur de traduction: {e}")
        return text  # Retourner le texte original si erreur

def translate_html_content(html_content, dest_lang):
    """
    Traduire le contenu textuel d'un fichier HTML
    en préservant la structure, CSS, JavaScript
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Traduire les éléments textuels
        for element in soup.find_all(text=True):
            # Ignorer les scripts, styles, et textes vides
            if element.parent.name in ['script', 'style'] or not element.strip():
                continue
            
            # Traduire le texte
            original_text = element.strip()
            if len(original_text) > 2:  # Ignorer les textes trop courts
                translated_text = translate_text(original_text, dest_lang)
                element.replace_with(translated_text)
                
                # Pause pour éviter de surcharger l'API
                time.sleep(0.1)
        
        return str(soup)
    except Exception as e:
        print(f"      ❌ Erreur parsing HTML: {e}")
        return html_content

def translate_file(fr_path, dest_lang, dest_dir):
    """Traduire un fichier HTML"""
    # Calculer le chemin de destination
    relative_path = fr_path.relative_to(FR_DIR)
    dest_path = dest_dir / relative_path
    
    # Si le fichier traduit existe déjà, le sauter
    if dest_path.exists():
        print(f"      ⏭️  Déjà traduit: {relative_path}")
        return True
    
    try:
        # Lire le fichier français
        with open(fr_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Traduire
        print(f"      🌍 Traduction: {relative_path}")
        translated_html = translate_html_content(html_content, dest_lang)
        
        # Créer les sous-dossiers si nécessaire
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
        
        print(f"      ✅ Sauvegardé: {dest_path}")
        return True
    
    except Exception as e:
        print(f"      ❌ Erreur avec {relative_path}: {e}")
        return False

def translate_all_to_language(dest_lang, dest_dir):
    """Traduire tous les fichiers vers une langue"""
    lang_name = {'en': 'Anglais', 'es': 'Espagnol'}[dest_lang]
    print(f"\n{'='*60}")
    print(f"🌍 TRADUCTION VERS {lang_name.upper()} ({dest_lang})")
    print(f"{'='*60}")
    
    # Trouver tous les fichiers français
    fr_files = list(FR_DIR.glob('**/*.html'))
    total = len(fr_files)
    
    print(f"   📊 {total} fichiers à traduire")
    
    success = 0
    skipped = 0
    failed = 0
    
    for i, fr_file in enumerate(fr_files, 1):
        print(f"\n   [{i}/{total}] {fr_file.name}")
        
        if translate_file(fr_file, dest_lang, dest_dir):
            if (dest_dir / fr_file.relative_to(FR_DIR)).exists():
                success += 1
            else:
                skipped += 1
        else:
            failed += 1
    
    print(f"\n   ✅ Réussis: {success}")
    print(f"   ⏭️  Ignorés: {skipped}")
    print(f"   ❌ Échecs: {failed}")

def main():
    """Fonction principale"""
    print("🌍 TRADUCTION AUTOMATIQUE DES PAGES HTML")
    print("   Utilise Google Translate (gratuit, sans OpenAI)")
    print("="*60)
    
    # Vérifier que le dossier fr/ existe
    if not FR_DIR.exists():
        print(f"❌ Erreur: Le dossier {FR_DIR} n'existe pas!")
        print("   Exécutez d'abord: python organize_html_i18n.py")
        return
    
    # Demander confirmation
    print("\n⚠️  ATTENTION:")
    print("   • La traduction automatique peut prendre du temps")
    print("   • Environ 5-10 secondes par page")
    print("   • Total estimé: 15-30 minutes pour 157 pages × 2 langues")
    
    response = input("\n▶️  Continuer? (o/n): ")
    if response.lower() != 'o':
        print("❌ Annulé par l'utilisateur")
        return
    
    # Traduire vers l'anglais
    translate_all_to_language('en', EN_DIR)
    
    # Traduire vers l'espagnol
    translate_all_to_language('es', ES_DIR)
    
    print("\n" + "="*60)
    print("✅ TRADUCTION TERMINÉE!")
    print("="*60)
    print("\n📁 Structure finale:")
    print(f"   • Embedding/fr/ - {len(list(FR_DIR.glob('**/*.html')))} fichiers (français)")
    print(f"   • Embedding/en/ - {len(list(EN_DIR.glob('**/*.html')))} fichiers (anglais)")
    print(f"   • Embedding/es/ - {len(list(ES_DIR.glob('**/*.html')))} fichiers (espagnol)")
    
    print("\n📝 PROCHAINES ÉTAPES:")
    print("   1. Vérifier quelques traductions manuellement")
    print("   2. Corriger les erreurs si nécessaire")
    print("   3. Tester l'application avec le changement de langue")

if __name__ == '__main__':
    main()

