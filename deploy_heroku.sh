#!/bin/bash

# Script de déploiement automatique sur Heroku
# Usage: ./deploy_heroku.sh

echo "🚀 Déploiement sur Heroku - Medical Search App"
echo "================================================"
echo ""

# Vérifier si Heroku CLI est installé
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI n'est pas installé."
    echo "📥 Installez-le depuis : https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

echo "✅ Heroku CLI détecté"
echo ""

# Vérifier si Git est initialisé
if [ ! -d ".git" ]; then
    echo "📦 Initialisation de Git..."
    git init
fi

# Ajouter tous les fichiers
echo "📁 Ajout des fichiers..."
git add .

# Demander un message de commit
echo ""
read -p "💬 Message de commit (ou Entrée pour message par défaut): " commit_msg

if [ -z "$commit_msg" ]; then
    commit_msg="Update: $(date '+%Y-%m-%d %H:%M:%S')"
fi

git commit -m "$commit_msg"

echo ""
echo "🔗 Connexion à Heroku..."
heroku login

echo ""
echo "📤 Déploiement vers Heroku..."
git push heroku main || git push heroku master

echo ""
echo "🗄️  Exécution des migrations..."
heroku run python manage.py migrate

echo ""
echo "📦 Collecte des fichiers statiques..."
heroku run python manage.py collectstatic --noinput

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "🌐 Votre application est en ligne :"
heroku open

echo ""
echo "📊 Pour voir les logs en temps réel :"
echo "heroku logs --tail"

