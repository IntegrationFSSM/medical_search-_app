"""
Service de traduction intelligente pour les pages HTML de pathologies
avec système de cache pour économiser les tokens OpenAI
"""
import os
import json
import hashlib
from pathlib import Path
from django.conf import settings
from django.core.cache import cache
from openai import OpenAI


class HTMLTranslationService:
    """Service pour traduire les pages HTML de pathologies"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.cache_dir = Path(settings.BASE_DIR) / 'translation_cache'
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_key(self, html_path, target_lang):
        """Générer une clé de cache unique pour le fichier et la langue"""
        # Utiliser le chemin + langue + hash du contenu
        file_path = Path(settings.EMBEDDINGS_FOLDER) / html_path
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            return f"html_trans_{html_path.replace('/', '_')}_{target_lang}_{content_hash}"
        return None
    
    def get_cached_translation(self, cache_key):
        """Récupérer une traduction du cache"""
        # Essayer d'abord le cache Django (rapide, en mémoire)
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Sinon, essayer le cache fichier (persistant)
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Remettre en cache Django pour les prochaines requêtes
                    cache.set(cache_key, data['translated_html'], 60 * 60 * 24)  # 24h
                    return data['translated_html']
            except Exception as e:
                print(f"Erreur lecture cache: {e}")
        
        return None
    
    def save_to_cache(self, cache_key, translated_html):
        """Sauvegarder une traduction dans le cache"""
        # Cache Django (rapide)
        cache.set(cache_key, translated_html, 60 * 60 * 24)  # 24h
        
        # Cache fichier (persistant)
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'translated_html': translated_html,
                    'timestamp': str(Path(cache_file).stat().st_mtime) if cache_file.exists() else None
                }, f, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde cache: {e}")
    
    def extract_translatable_content(self, html_content):
        """Extraire le contenu traduisible (en évitant les balises HTML/CSS/JS)"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Retirer les scripts et styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extraire le texte visible
            text_content = soup.get_text(separator='\n', strip=True)
            
            return text_content, soup
        except Exception as e:
            print(f"Erreur extraction contenu: {e}")
            return None, None
    
    def translate_with_openai(self, text_content, target_lang):
        """Traduire le texte avec OpenAI GPT-4"""
        lang_names = {
            'en': 'English',
            'es': 'Spanish (Español)',
            'fr': 'French (Français)'
        }
        
        target_lang_name = lang_names.get(target_lang, target_lang)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional medical translator. Translate the following psychiatric/medical content from French to {target_lang_name}. "
                                   f"Preserve all medical terminology accuracy. Keep HTML structure intact. "
                                   f"Maintain professional medical language. Do not translate: DSM-5, DSM-5-TR, ICD codes, medical abbreviations."
                    },
                    {
                        "role": "user",
                        "content": f"Translate this medical content to {target_lang_name}:\n\n{text_content[:15000]}"  # Limiter à 15000 chars pour économiser
                    }
                ],
                temperature=0.3,  # Traduction précise
                max_tokens=8000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Erreur traduction OpenAI: {e}")
            return None
    
    def apply_translation_to_html(self, original_html, original_text, translated_text):
        """Appliquer la traduction au HTML en préservant la structure"""
        from bs4 import BeautifulSoup
        import re
        
        try:
            soup = BeautifulSoup(original_html, 'html.parser')
            
            # Créer un mapping ligne par ligne (simplifié)
            original_lines = [line.strip() for line in original_text.split('\n') if line.strip()]
            translated_lines = [line.strip() for line in translated_text.split('\n') if line.strip()]
            
            # Créer un dictionnaire de traduction
            translation_map = {}
            for orig, trans in zip(original_lines, translated_lines):
                if orig and trans and len(orig) > 3:  # Ignorer les lignes trop courtes
                    translation_map[orig] = trans
            
            # Parcourir tous les éléments textuels et remplacer
            for element in soup.find_all(text=True):
                if element.parent.name not in ['script', 'style']:
                    text = element.strip()
                    if text and len(text) > 3:
                        # Chercher la traduction correspondante
                        for orig, trans in translation_map.items():
                            if orig in text or text in orig:
                                element.replace_with(trans)
                                break
            
            return str(soup)
        except Exception as e:
            print(f"Erreur application traduction: {e}")
            return original_html
    
    def translate_html_page(self, html_path, target_lang='en'):
        """
        Traduire une page HTML complète
        
        Args:
            html_path: Chemin relatif vers le fichier HTML (ex: "Anxiety_Disorders_out/agoraphobia.html")
            target_lang: Langue cible ('en', 'es', 'fr')
        
        Returns:
            str: HTML traduit ou original si français ou erreur
        """
        # Si français, retourner l'original
        if target_lang == 'fr':
            full_path = Path(settings.EMBEDDINGS_FOLDER) / html_path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        
        # Vérifier le cache
        cache_key = self.get_cache_key(html_path, target_lang)
        if cache_key:
            cached_translation = self.get_cached_translation(cache_key)
            if cached_translation:
                print(f"✅ Traduction {target_lang} trouvée en cache pour {html_path}")
                return cached_translation
        
        # Charger le HTML original
        full_path = Path(settings.EMBEDDINGS_FOLDER) / html_path
        if not full_path.exists():
            return None
        
        with open(full_path, 'r', encoding='utf-8') as f:
            original_html = f.read()
        
        print(f"🌍 Traduction {target_lang} de {html_path} avec OpenAI...")
        
        # Extraire le contenu traduisible
        text_content, soup = self.extract_translatable_content(original_html)
        if not text_content:
            return original_html
        
        # Traduire avec OpenAI
        translated_text = self.translate_with_openai(text_content, target_lang)
        if not translated_text:
            return original_html
        
        # Appliquer la traduction au HTML
        translated_html = self.apply_translation_to_html(original_html, text_content, translated_text)
        
        # Sauvegarder en cache
        if cache_key:
            self.save_to_cache(cache_key, translated_html)
            print(f"✅ Traduction sauvegardée en cache")
        
        return translated_html

