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


@register.filter(name='clean_pathology')
def clean_pathology(value):
    """
    Nettoie le nom d'une pathologie en enlevant les préfixes Section/SubSection.
    """
    if not value:
        return value
    
    text = str(value)
    
    # Enlever les crochets et guillemets
    text = text.strip('[]"\'')
    text = text.replace('["', '').replace('"]', '')
    text = text.replace("['", '').replace("']", '')
    
    # Enlever les emojis
    text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
    text = re.sub(r'[\u2600-\u26FF]', '', text)
    text = re.sub(r'[\u2700-\u27BF]', '', text)
    
    # Enlever les préfixes SubSection et Section avec leurs numéros
    # Par exemple: "SubSection2.1 Language Disorder" -> "Language Disorder"
    text = re.sub(r'SubSection\s*\d+\.?\d*\s+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Section\s*\d+\.?\d*\s+', '', text, flags=re.IGNORECASE)
    
    # Enlever aussi les variantes avec tirets bas et points
    text = re.sub(r'SubSection\d+\.\d+[_\s]+', '', text)
    text = re.sub(r'Section\d+[_\s]+', '', text)
    
    # Enlever les "Section :" et "Sous-section :" en français
    text = re.sub(r'Section\s+\d+\s*:\s*', '', text)
    text = re.sub(r'Sous-section\s+[\d.]+\s*:\s*', '', text)
    
    # Remplacer les underscores par des espaces
    text = text.replace('_', ' ')
    
    return text.strip()

