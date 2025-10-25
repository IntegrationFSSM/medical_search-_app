"""
Script pour générer une SECRET_KEY Django sécurisée
Usage: python generate_secret_key.py
"""
from django.core.management.utils import get_random_secret_key

secret_key = get_random_secret_key()
print("\n" + "="*70)
print("🔑 Votre nouvelle SECRET_KEY Django :")
print("="*70)
print(secret_key)
print("="*70)
print("\n📝 Copiez cette clé dans votre fichier .env :")
print(f"SECRET_KEY={secret_key}")
print("\n⚠️  NE PARTAGEZ JAMAIS CETTE CLÉ !")
print("="*70 + "\n")

