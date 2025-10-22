# Script de déploiement automatique sur Heroku (Windows PowerShell)
# Usage: .\deploy_heroku.ps1

Write-Host "🚀 Déploiement sur Heroku - Medical Search App" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si Heroku CLI est installé
try {
    heroku --version | Out-Null
    Write-Host "✅ Heroku CLI détecté" -ForegroundColor Green
} catch {
    Write-Host "❌ Heroku CLI n'est pas installé." -ForegroundColor Red
    Write-Host "📥 Installez-le depuis : https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Vérifier si Git est initialisé
if (-not (Test-Path ".git")) {
    Write-Host "📦 Initialisation de Git..." -ForegroundColor Yellow
    git init
}

# Ajouter tous les fichiers
Write-Host "📁 Ajout des fichiers..." -ForegroundColor Yellow
git add .

# Demander un message de commit
Write-Host ""
$commit_msg = Read-Host "💬 Message de commit (ou Entrée pour message par défaut)"

if ([string]::IsNullOrWhiteSpace($commit_msg)) {
    $commit_msg = "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

git commit -m $commit_msg

Write-Host ""
Write-Host "🔗 Connexion à Heroku..." -ForegroundColor Yellow
heroku login

Write-Host ""
Write-Host "📤 Déploiement vers Heroku..." -ForegroundColor Yellow

try {
    git push heroku main
} catch {
    Write-Host "Tentative avec la branche master..." -ForegroundColor Yellow
    git push heroku master
}

Write-Host ""
Write-Host "🗄️  Exécution des migrations..." -ForegroundColor Yellow
heroku run python manage.py migrate

Write-Host ""
Write-Host "📦 Collecte des fichiers statiques..." -ForegroundColor Yellow
heroku run python manage.py collectstatic --noinput

Write-Host ""
Write-Host "✅ Déploiement terminé !" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Votre application est en ligne :" -ForegroundColor Cyan
heroku open

Write-Host ""
Write-Host "📊 Pour voir les logs en temps réel :" -ForegroundColor Yellow
Write-Host "heroku logs --tail" -ForegroundColor White

