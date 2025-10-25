from django import template
import re

register = template.Library()

@register.filter(name='clean_text')
def clean_text(value):
    """
    Nettoie le texte en enlevant les crochets, guillemets, markdown et autres caractères indésirables.
    """
    if not value:
        return value
    
    # Convertir en string si ce n'est pas déjà le cas
    text = str(value)
    
    # Enlever les crochets [ ]
    text = text.strip('[]')
    
    # Enlever les guillemets simples et doubles
    text = text.strip('"\'')
    
    # Enlever les guillemets à l'intérieur du texte si nécessaire
    text = text.replace('["', '').replace('"]', '')
    text = text.replace("['", '').replace("']", '')
    
    # Enlever les markdown
    # Enlever les titres markdown (## Titre)
    text = re.sub(r'#{1,6}\s*', '', text)
    
    # Enlever le gras markdown (**texte** ou __texte__)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    
    # Enlever l'italique markdown (*texte* ou _texte_)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Enlever les liens markdown [texte](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Nettoyer les espaces multiples mais garder les sauts de ligne
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

