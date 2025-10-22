# ✅ Configuration Heroku - RÉSUMÉ

## 📦 Fichiers Créés pour Heroku

Tous les fichiers nécessaires ont été créés et configurés :

### 1. **Procfile** ✅
```
web: gunicorn medical_search.wsgi --log-file -
```
→ Indique à Heroku comment démarrer l'application

### 2. **runtime.txt** ✅
```
python-3.11.9
```
→ Spécifie la version Python à utiliser

### 3. **requirements.txt** ✅ (mis à jour)
Ajout des dépendances Heroku :
- `gunicorn` - Serveur web WSGI
- `whitenoise` - Serveur de fichiers statiques
- `psycopg2-binary` - Driver PostgreSQL
- `dj-database-url` - Configuration DB simplifiée

### 4. **settings.py** ✅ (modifié)
Configurations ajoutées :
- ✅ `SECRET_KEY` depuis variables d'environnement
- ✅ `DEBUG` configurable (True en dev, False en prod)
- ✅ `ALLOWED_HOSTS` depuis variables d'environnement
- ✅ `WhiteNoise` middleware pour fichiers statiques
- ✅ Configuration PostgreSQL automatique avec `dj-database-url`
- ✅ `STATIC_ROOT` pour collectstatic
- ✅ Compression et cache des fichiers statiques

### 5. **.gitignore** ✅
Fichiers à exclure du repository Git

### 6. **Scripts de Déploiement** ✅
- `deploy_heroku.sh` (Linux/Mac)
- `deploy_heroku.ps1` (Windows PowerShell)

### 7. **Documentation Complète** ✅
- `DEPLOIEMENT_HEROKU.md` - Guide détaillé étape par étape

---

## 🚀 Prochaines Étapes (À FAIRE PAR VOUS)

### Étape 1 : Installer Heroku CLI

**Windows :**
```powershell
# Télécharger depuis :
https://devcenter.heroku.com/articles/heroku-cli
```

**Ou avec npm :**
```bash
npm install -g heroku
```

### Étape 2 : Initialiser Git

```bash
cd C:\Users\yassi\medical_search_app
git init
git add .
git commit -m "Initial commit - ready for Heroku"
```

### Étape 3 : Se Connecter à Heroku

```bash
heroku login
```

### Étape 4 : Créer l'Application

```bash
heroku create medical-search-app-yassi
```

**Note :** Changez le nom si celui-ci est déjà pris.

### Étape 5 : Configurer les Variables d'Environnement

```bash
# SECRET_KEY (générez-en une nouvelle)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Puis configurez-la
heroku config:set SECRET_KEY="VOTRE_CLE_GENEREE"

# DEBUG
heroku config:set DEBUG=False

# ALLOWED_HOSTS (remplacez par votre nom d'app Heroku)
heroku config:set ALLOWED_HOSTS=medical-search-app-yassi.herokuapp.com,.herokuapp.com

# OpenAI
heroku config:set OPENAI_API_KEY="sk-proj-VOTRE_CLE"
heroku config:set EMBEDDING_MODEL="text-embedding-ada-002"
```

### Étape 6 : ⚠️ IMPORTANT - Gestion des Embeddings

**PROBLÈME :** Le dossier `Embedding/` est trop volumineux pour Git/Heroku.

**SOLUTIONS :**

#### Option A : AWS S3 (Recommandée) 🌟

1. Créez un compte AWS
2. Créez un bucket S3
3. Uploadez le dossier `Embedding/` vers S3
4. Configurez dans Heroku :
   ```bash
   heroku config:set EMBEDDINGS_FOLDER="s3://votre-bucket/Embedding"
   ```
5. Modifiez `services.py` pour charger depuis S3 (code fourni ci-dessous)

#### Option B : Google Cloud Storage

Similaire à S3 mais avec Google Cloud.

#### Option C : Les inclure dans Git (Si < 500MB)

```bash
# Retirer Embedding/ du .gitignore
# Puis :
git add Embedding/
git commit -m "Add embeddings"
git push heroku main
```

**⚠️ Attention :** Heroku a une limite de slug de 500MB !

### Étape 7 : Ajouter PostgreSQL

```bash
heroku addons:create heroku-postgresql:essential-0
```

### Étape 8 : Déployer !

**Option Automatique (Windows) :**
```powershell
.\deploy_heroku.ps1
```

**Option Manuelle :**
```bash
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py collectstatic --noinput
heroku open
```

---

## 📝 Code pour Charger depuis S3 (si vous choisissez Option A)

Ajoutez à `pathology_search/services.py` :

```python
import boto3
from botocore.exceptions import NoCredentialsError

class PathologySearchService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.EMBEDDING_MODEL
        self.embeddings_folder = settings.EMBEDDINGS_FOLDER
        
        # Si c'est une URL S3, initialiser boto3
        if self.embeddings_folder.startswith('s3://'):
            self.s3_client = boto3.client('s3')
            # Extraire bucket et prefix
            s3_path = self.embeddings_folder.replace('s3://', '')
            self.s3_bucket = s3_path.split('/')[0]
            self.s3_prefix = '/'.join(s3_path.split('/')[1:])
    
    def _load_from_s3(self, file_key):
        """Charger un fichier depuis S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=file_key
            )
            return response['Body'].read()
        except NoCredentialsError:
            print("Erreur: AWS credentials non trouvées")
            return None
```

Puis configurez les credentials AWS sur Heroku :
```bash
heroku config:set AWS_ACCESS_KEY_ID="votre-access-key"
heroku config:set AWS_SECRET_ACCESS_KEY="votre-secret-key"
heroku config:set AWS_DEFAULT_REGION="us-east-1"
```

---

## 🔍 Vérification Post-Déploiement

### Tester l'application :

1. **Page d'accueil :**
   ```
   https://votre-app.herokuapp.com/
   ```

2. **Recherche :**
   - Entrez une pathologie
   - Vérifiez que les résultats s'affichent

3. **Mode Validation :**
   - Activez le mode validation
   - Remplissez le formulaire
   - Cliquez sur VALIDE
   - Vérifiez que le plan de traitement se génère

### Voir les logs :

```bash
heroku logs --tail
```

### Redémarrer si nécessaire :

```bash
heroku restart
```

---

## 💰 Coûts Estimés

### Gratuit (Plan Eco Dynos)
- ✅ Application web de base
- ✅ PostgreSQL Essential-0 (10k lignes)
- ⚠️ S'endort après 30min d'inactivité
- ⚠️ 1000 heures/mois

### ~$7/mois (Plan Basic)
- ✅ Always-on (ne s'endort pas)
- ✅ SSL automatique
- ✅ Domaine personnalisé

### Extras
- **AWS S3** : ~$0.023/GB/mois (très peu si petit usage)
- **OpenAI API** : Selon utilisation (comptez ~$5-20/mois)

---

## 📊 Checklist Complète

Avant de déployer :

- [ ] Heroku CLI installé
- [ ] Git initialisé
- [ ] Tous les fichiers créés (Procfile, runtime.txt, etc.)
- [ ] requirements.txt à jour
- [ ] Application Heroku créée
- [ ] Variables d'environnement configurées
- [ ] PostgreSQL addon ajouté
- [ ] **Embeddings gérés** (S3 ou inclus dans Git)
- [ ] Premier déploiement effectué
- [ ] Migrations exécutées
- [ ] Fichiers statiques collectés
- [ ] Application testée en ligne

---

## 🆘 Support et Dépannage

### Problème courant 1 : "Application Error"

```bash
heroku logs --tail
# Cherchez l'erreur spécifique
```

### Problème courant 2 : Embeddings non trouvés

Vérifiez :
```bash
heroku config:get EMBEDDINGS_FOLDER
```

### Problème courant 3 : OpenAI API ne fonctionne pas

Vérifiez :
```bash
heroku config:get OPENAI_API_KEY
```

---

## 🎯 Commandes Utiles

```bash
# État de l'application
heroku ps

# Variables d'environnement
heroku config

# Logs en temps réel
heroku logs --tail

# Shell Django sur Heroku
heroku run python manage.py shell

# Redémarrer
heroku restart

# Info sur l'app
heroku info

# Ouvrir l'app dans le navigateur
heroku open
```

---

## 📚 Ressources

- [Heroku Dev Center](https://devcenter.heroku.com/)
- [Django sur Heroku](https://devcenter.heroku.com/articles/django-app-configuration)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)

---

**Votre application est prête pour le déploiement ! 🚀**

**Suivez le guide `DEPLOIEMENT_HEROKU.md` pour les instructions détaillées.**

