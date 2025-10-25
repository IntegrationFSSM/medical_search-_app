# 🔐 Guide de Configuration du fichier .env

## ⚠️ IMPORTANT : Ce fichier est OBLIGATOIRE

Le fichier `.env` contient vos configurations **secrètes** et **personnelles**.

---

## 📝 Étape 1 : Créer le fichier .env

À la racine du projet (`C:\Users\yassi\medical_search_app\`), créez un fichier nommé **`.env`** (avec le point au début !)

---

## 🔑 Étape 2 : Générer votre SECRET_KEY Django

Exécutez :

```bash
python generate_secret_key.py
```

Cela va générer une clé secrète unique. **Copiez-la !**

---

## 🐘 Étape 3 : Récupérer votre mot de passe PostgreSQL

Vous avez défini ce mot de passe lors de l'installation de PostgreSQL.

**Si vous l'avez oublié** :
1. Ouvrez **pgAdmin**
2. Clic droit sur "PostgreSQL" → "Properties"
3. Ou réinitialisez le mot de passe via pgAdmin

**Mot de passe par défaut souvent utilisé** : `postgres` ou `admin`

---

## 📄 Étape 4 : Créer le fichier .env

Créez le fichier `.env` avec ce contenu :

```env
# OpenAI API Key
OPENAI_API_KEY=sk-proj-votre-clé-openai-ici

# PostgreSQL Configuration
DB_NAME=medical_search_db
DB_USER=postgres
DB_PASSWORD=VOTRE_MOT_DE_PASSE_POSTGRES_ICI
DB_HOST=localhost
DB_PORT=5432

# Django Secret Key (généré avec generate_secret_key.py)
SECRET_KEY=collez-ici-la-cle-generee-par-le-script

# Embeddings folder
EMBEDDINGS_FOLDER=Embedding
EMBEDDING_MODEL=text-embedding-3-small
```

---

## ✅ Étape 5 : Vérifier que ça fonctionne

### 1. Créer la base de données PostgreSQL

Ouvrez **pgAdmin** ou **psql** et exécutez :

```sql
CREATE DATABASE medical_search_db;
```

### 2. Tester la connexion

```bash
python manage.py check
```

Si ça fonctionne, vous verrez : `System check identified no issues`

### 3. Appliquer les migrations

```bash
python manage.py migrate
```

### 4. Créer les patients de test

```bash
python manage.py create_test_patients
```

### 5. Lancer le serveur

```bash
python manage.py runserver
```

---

## 🔧 Dépannage

### Erreur : "password authentication failed for user postgres"

**Solution** : Le mot de passe dans `.env` est incorrect.

Vérifiez votre mot de passe PostgreSQL :

```bash
# Dans psql ou pgAdmin, essayez de vous connecter avec :
psql -U postgres -W
# Il va demander le mot de passe
```

### Erreur : "database medical_search_db does not exist"

**Solution** : Créez la base de données :

```sql
CREATE DATABASE medical_search_db;
```

### Erreur : "could not connect to server"

**Solution** : PostgreSQL n'est pas démarré.

- **Windows** : Services → PostgreSQL → Démarrer
- Ou via pgAdmin

---

## 🚫 SÉCURITÉ

### ❌ NE FAITES JAMAIS :
- ❌ Commit le fichier `.env` sur Git
- ❌ Partager votre SECRET_KEY
- ❌ Partager votre OPENAI_API_KEY
- ❌ Publier ces informations en ligne

### ✅ TOUJOURS :
- ✅ Garder le `.env` en local uniquement
- ✅ Utiliser `.env.example` pour documenter (sans valeurs réelles)
- ✅ Ajouter `.env` dans `.gitignore`

---

## 📁 Structure des fichiers

```
medical_search_app/
├── .env                 ← VOTRE FICHIER SECRET (ne pas commit)
├── .env.example         ← Exemple sans vraies valeurs (peut être commit)
├── .gitignore           ← Contient ".env" pour ne pas le commit
├── generate_secret_key.py  ← Script pour générer SECRET_KEY
└── ...
```

---

## 💡 Exemple complet de .env

```env
# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx

# PostgreSQL
DB_NAME=medical_search_db
DB_USER=postgres
DB_PASSWORD=MonMotDePasse123!
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=django-insecure-p8f7x#q2m@n5v!k9w$h3y&j6r1t*u4z8

# Embeddings
EMBEDDINGS_FOLDER=Embedding
EMBEDDING_MODEL=text-embedding-3-small
```

**Remplacez TOUTES les valeurs par les vôtres !**

