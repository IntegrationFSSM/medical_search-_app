#!/bin/bash

echo "========================================"
echo "Application Django - Recherche Pathologies"
echo "========================================"
echo ""

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
    echo ""
fi

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate
echo ""

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt --quiet
echo ""

# Vérifier si .env existe
if [ ! -f ".env" ]; then
    echo "ERREUR: Fichier .env manquant!"
    echo "Copiez .env.example vers .env et configurez vos paramètres."
    echo ""
    exit 1
fi

# Appliquer les migrations
echo "Application des migrations..."
python manage.py migrate
echo ""

# Lancer le serveur
echo "========================================"
echo "Démarrage du serveur..."
echo "Accès: http://127.0.0.1:8000/"
echo "Appuyez sur Ctrl+C pour arrêter"
echo "========================================"
echo ""
python manage.py runserver

