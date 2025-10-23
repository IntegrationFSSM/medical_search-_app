from django import template
import re

register = template.Library()

@register.filter(name='clean_text')
def clean_text(value):
    """
    Nettoie le texte en enlevant les crochets, guillemets, et autres caractères indésirables.
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
    
    # Nettoyer les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

