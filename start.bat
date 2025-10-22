@echo off
echo ========================================
echo Application Django - Recherche Pathologies
echo ========================================
echo.

REM Vérifier si l'environnement virtuel existe
if not exist "venv\" (
    echo Creation de l'environnement virtuel...
    python -m venv venv
    echo.
)

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo.

REM Installer les dépendances
echo Installation des dependances...
pip install -r requirements.txt --quiet
echo.

REM Vérifier si .env existe
if not exist ".env" (
    echo ERREUR: Fichier .env manquant!
    echo Copiez .env.example vers .env et configurez vos parametres.
    echo.
    pause
    exit /b 1
)

REM Appliquer les migrations
echo Application des migrations...
python manage.py migrate
echo.

REM Lancer le serveur
echo ========================================
echo Demarrage du serveur...
echo Acces: http://127.0.0.1:8000/
echo Appuyez sur Ctrl+C pour arreter
echo ========================================
echo.
python manage.py runserver

