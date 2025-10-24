"""
Script pour mettre à jour manuellement les fichiers de traduction
Ajoute les nouveaux textes qui manquent
"""
import polib

# Nouvelles chaînes à traduire
new_strings = {
    # Page validate.html
    "Validation des Résultats": {
        "en": "Results Validation",
        "es": "Validación de Resultados"
    },
    "Requête": {
        "en": "Query",
        "es": "Consulta"
    },
    "Résultat": {
        "en": "Result",
        "es": "Resultado"
    },
    
    # Barre de progression
    "Recherche en cours...": {
        "en": "Search in progress...",
        "es": "Búsqueda en curso..."
    },
    "Initialisation...": {
        "en": "Initializing...",
        "es": "Inicializando..."
    },
    "Chargement": {
        "en": "Loading",
        "es": "Cargando"
    },
    "Embedding": {
        "en": "Embedding",
        "es": "Embedding"
    },
    "Analyse": {
        "en": "Analysis",
        "es": "Análisis"
    },
    "Résultats": {
        "en": "Results",
        "es": "Resultados"
    },
    "fichiers analysés": {
        "en": "files analyzed",
        "es": "archivos analizados"
    },
    "Chargement des fichiers d&#39;embeddings...": {
        "en": "Loading embedding files...",
        "es": "Cargando archivos de embedding..."
    },
    "Génération de l&#39;embedding de la requête...": {
        "en": "Generating query embedding...",
        "es": "Generando embedding de la consulta..."
    },
    "Calcul des similarités...": {
        "en": "Calculating similarities...",
        "es": "Calculando similaridades..."
    },
    "Finalisation des résultats...": {
        "en": "Finalizing results...",
        "es": "Finalizando resultados..."
    },
}

def update_po_file(lang_code):
    """Mettre à jour un fichier .po avec les nouvelles traductions"""
    po_file_path = f'locale/{lang_code}/LC_MESSAGES/django.po'
    
    try:
        # Charger le fichier .po existant
        po = polib.pofile(po_file_path)
        print(f"\n📝 Mise à jour de {po_file_path}")
        
        added_count = 0
        updated_count = 0
        
        # Parcourir les nouvelles chaînes
        for msgid, translations in new_strings.items():
            # Chercher si l'entrée existe déjà
            entry = po.find(msgid)
            
            if entry:
                # Si l'entrée existe mais n'a pas de traduction
                if not entry.msgstr:
                    entry.msgstr = translations[lang_code]
                    updated_count += 1
                    print(f"   ✏️  Mis à jour: '{msgid}' → '{translations[lang_code]}'")
            else:
                # Ajouter une nouvelle entrée
                new_entry = polib.POEntry(
                    msgid=msgid,
                    msgstr=translations[lang_code],
                    occurrences=[]
                )
                po.append(new_entry)
                added_count += 1
                print(f"   ➕ Ajouté: '{msgid}' → '{translations[lang_code]}'")
        
        # Sauvegarder le fichier .po
        po.save(po_file_path)
        print(f"\n   ✅ {added_count} nouvelles entrées, {updated_count} mises à jour")
        
        # Compiler le fichier .mo
        po.save_as_mofile(po_file_path.replace('.po', '.mo'))
        print(f"   ✅ Fichier .mo compilé")
        
    except FileNotFoundError:
        print(f"   ❌ Fichier {po_file_path} non trouvé")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("🌍 MISE À JOUR DES TRADUCTIONS")
    print("="*60)
    
    # Mettre à jour pour l'anglais
    update_po_file('en')
    
    # Mettre à jour pour l'espagnol
    update_po_file('es')
    
    print("\n" + "="*60)
    print("✅ MISE À JOUR TERMINÉE!")
    print("\n📝 Prochaines étapes:")
    print("   1. Redémarrer le serveur Django")
    print("   2. Tester le changement de langue")
    print("   3. Vérifier que tous les textes sont traduits")
    print("\n🚀 Pour déployer:")
    print("   git add locale/")
    print("   git commit -m \"Update translations for validation and progress bar\"")
    print("   git push heroku master")

if __name__ == '__main__':
    main()

