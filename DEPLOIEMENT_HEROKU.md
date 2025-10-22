# 🚀 Guide de Déploiement sur Heroku

## 📋 Prérequis

1. **Compte Heroku** : Créez un compte sur [heroku.com](https://heroku.com)
2. **Heroku CLI** : Installez Heroku CLI
   - Windows : Téléchargez depuis [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
   - Ou avec `npm` : `npm install -g heroku`

3. **Git** : Assurez-vous que Git est installé

---

## 🔧 Étape 1 : Préparation du Projet

### 1.1 - Vérifier les fichiers créés

Vérifiez que ces fichiers existent :
- ✅ `Procfile`
- ✅ `runtime.txt`
- ✅ `requirements.txt` (avec gunicorn, whitenoise, etc.)
- ✅ `.gitignore`

### 1.2 - Initialiser Git (si pas encore fait)

```bash
git init
git add .
git commit -m "Préparation pour déploiement Heroku"
```

---

## 🌐 Étape 2 : Créer l'Application Heroku

### 2.1 - Connexion à Heroku

```bash
heroku login
```

Cela ouvrira votre navigateur pour vous connecter.

### 2.2 - Créer une nouvelle application

```bash
heroku create medical-search-app-2025
```

**Note :** Remplacez `medical-search-app-2025` par un nom unique.

Heroku va vous donner :
- URL de l'app : `https://medical-search-app-2025.herokuapp.com`
- URL Git : `https://git.heroku.com/medical-search-app-2025.git`

---

## 🔐 Étape 3 : Configuration des Variables d'Environnement

### 3.1 - SECRET_KEY

Générez une nouvelle clé secrète :

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Puis configurez-la sur Heroku :

```bash
heroku config:set SECRET_KEY="votre-nouvelle-cle-secrete-generee"
```

### 3.2 - Autres Variables

```bash
# Debug mode (False en production)
heroku config:set DEBUG=False

# Hosts autorisés (ajoutez votre domaine Heroku)
heroku config:set ALLOWED_HOSTS=medical-search-app-2025.herokuapp.com,.herokuapp.com

# OpenAI API Key
heroku config:set OPENAI_API_KEY="sk-proj-votre-cle-openai"

# Modèle d'embedding
heroku config:set EMBEDDING_MODEL="text-embedding-ada-002"
```

### 3.3 - Dossier Embeddings

**⚠️ IMPORTANT :** Le dossier `Embedding/` avec vos fichiers `.npy` est trop volumineux pour Git.

**Solution 1 - Utiliser AWS S3 ou Google Cloud Storage :**

```bash
# Configurer S3
heroku config:set EMBEDDINGS_FOLDER="https://votre-bucket-s3.amazonaws.com/Embedding"
```

**Solution 2 - Heroku Slugs (pour petits fichiers) :**

Si vos embeddings sont < 500MB :

```bash
# Ajouter au git
git add Embedding/
git commit -m "Add embeddings"
```

**Solution 3 - Recommandée : Upload vers un service cloud**

1. Uploadez vos fichiers `Embedding/` vers **AWS S3**, **Google Cloud Storage**, ou **Dropbox**
2. Configurez l'URL dans Heroku :

```bash
heroku config:set EMBEDDINGS_FOLDER="/app/Embedding"
```

---

## 🗄️ Étape 4 : Ajouter PostgreSQL

Heroku fournit PostgreSQL gratuitement :

```bash
heroku addons:create heroku-postgresql:essential-0
```

Cela configure automatiquement `DATABASE_URL`.

---

## 📤 Étape 5 : Déploiement

### 5.1 - Push vers Heroku

```bash
git push heroku main
```

Ou si votre branche s'appelle `master` :

```bash
git push heroku master
```

### 5.2 - Migrations de la base de données

```bash
heroku run python manage.py migrate
```

### 5.3 - Collecter les fichiers statiques

```bash
heroku run python manage.py collectstatic --noinput
```

### 5.4 - Créer un superutilisateur (optionnel)

```bash
heroku run python manage.py createsuperuser
```

---

## ✅ Étape 6 : Vérification

### 6.1 - Ouvrir l'application

```bash
heroku open
```

### 6.2 - Voir les logs

```bash
heroku logs --tail
```

### 6.3 - Test de l'application

Visitez :
- Page d'accueil : `https://votre-app.herokuapp.com/`
- Recherche : Testez une recherche de pathologie
- Validation : Testez le mode validation avec génération IA

---

## 🔧 Étape 7 : Dépannage

### Erreur : "Application Error"

```bash
# Voir les logs détaillés
heroku logs --tail

# Redémarrer l'application
heroku restart
```

### Erreur : "No module named 'X'"

```bash
# Vérifier que requirements.txt est à jour
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push heroku main
```

### Erreur : "collectstatic failed"

```bash
# Désactiver temporairement collectstatic
heroku config:set DISABLE_COLLECTSTATIC=1

# Puis redéployer
git push heroku main

# Ensuite réactiver
heroku config:unset DISABLE_COLLECTSTATIC
heroku run python manage.py collectstatic --noinput
```

### Problème avec les embeddings

Si les fichiers `.npy` ne se chargent pas :

1. **Vérifier les logs** :
```bash
heroku logs --tail | grep "embedding"
```

2. **Vérifier la variable d'environnement** :
```bash
heroku config:get EMBEDDINGS_FOLDER
```

3. **Solution recommandée** : Utilisez AWS S3
   - Créez un bucket S3
   - Uploadez le dossier `Embedding/`
   - Modifiez `services.py` pour charger depuis S3

---

## 📊 Surveillance et Maintenance

### Voir les ressources utilisées

```bash
heroku ps
```

### Voir les addons

```bash
heroku addons
```

### Scaler l'application

```bash
# Augmenter les dynos (payant)
heroku ps:scale web=2

# Revenir à 1 dyno (gratuit)
heroku ps:scale web=1
```

### Mise à jour de l'application

```bash
# Après modifications locales
git add .
git commit -m "Description des changements"
git push heroku main

# Relancer les migrations si nécessaire
heroku run python manage.py migrate
```

---

## 💰 Coûts Heroku

### Plan Gratuit (Eco Dynos)
- ✅ 1000 heures/mois gratuites
- ✅ PostgreSQL Essential-0 gratuit (jusqu'à 10,000 lignes)
- ⚠️ L'app s'endort après 30 min d'inactivité

### Plan Basique (~$7/mois)
- Always-on (ne s'endort pas)
- Plus de puissance

### Pour la Production
- Utilisez au minimum le plan **Basic** ($7/mois)
- Ajoutez un domaine personnalisé
- Configurez SSL (automatique avec Heroku)

---

## 🔒 Sécurité en Production

1. **Générez une vraie SECRET_KEY** (fait à l'étape 3.1)
2. **DEBUG=False** (fait à l'étape 3.2)
3. **HTTPS seulement** :
   ```bash
   heroku config:set SECURE_SSL_REDIRECT=True
   ```

4. **CSRF Protection** (déjà configuré dans Django)

5. **Mettez à jour régulièrement** :
   ```bash
   pip list --outdated
   pip install --upgrade django openai
   ```

---

## 🎯 Checklist Finale

Avant de déployer en production :

- [ ] Fichiers créés : `Procfile`, `runtime.txt`, `.gitignore`
- [ ] `requirements.txt` à jour avec gunicorn, whitenoise, psycopg2
- [ ] `settings.py` configuré pour Heroku (DEBUG, ALLOWED_HOSTS, DATABASE)
- [ ] Variables d'environnement configurées sur Heroku
- [ ] PostgreSQL addon ajouté
- [ ] Embeddings accessibles (S3 ou inclus dans le slug)
- [ ] Git repository initialisé
- [ ] Push vers Heroku effectué
- [ ] Migrations exécutées
- [ ] Application testée en ligne

---

## 📞 Support

Si vous rencontrez des problèmes :

1. **Logs Heroku** : `heroku logs --tail`
2. **Documentation Heroku** : [devcenter.heroku.com](https://devcenter.heroku.com)
3. **Django sur Heroku** : [devcenter.heroku.com/articles/django-app-configuration](https://devcenter.heroku.com/articles/django-app-configuration)

---

## 🚀 Commandes Utiles

```bash
# État de l'app
heroku ps

# Logs en temps réel
heroku logs --tail

# Ouvrir le shell Django sur Heroku
heroku run python manage.py shell

# Ouvrir la console PostgreSQL
heroku pg:psql

# Redémarrer l'app
heroku restart

# Info sur l'app
heroku info

# Liste des variables d'env
heroku config
```

---

**Votre application médicale est maintenant prête pour Heroku ! 🎉**

