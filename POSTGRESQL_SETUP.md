# 🐘 Configuration PostgreSQL pour Medical Search App

## ✅ Étape 1 : Installer PostgreSQL

Si vous n'avez pas encore PostgreSQL installé :
- **Windows** : Téléchargez depuis https://www.postgresql.org/download/windows/
- **Pendant l'installation**, notez bien le **mot de passe** que vous définissez pour l'utilisateur `postgres`

## ✅ Étape 2 : Créer la base de données

Ouvrez **pgAdmin** ou **SQL Shell (psql)** et exécutez :

```sql
CREATE DATABASE medical_search_db;
```

## ✅ Étape 3 : Configurer le fichier .env

Créez un fichier `.env` à la racine du projet avec le contenu suivant :

```env
# OpenAI API Configuration
OPENAI_API_KEY=votre-clé-api-openai

# PostgreSQL Database Configuration
DB_NAME=medical_search_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe_postgres_ici
DB_HOST=localhost
DB_PORT=5432

# Django Secret Key
SECRET_KEY=votre-secret-key-django
```

**⚠️ Important** : Remplacez `votre_mot_de_passe_postgres_ici` par le mot de passe que vous avez défini lors de l'installation de PostgreSQL !

## ✅ Étape 4 : Appliquer les migrations

```bash
python manage.py migrate
```

## ✅ Étape 5 : Créer les patients de test

```bash
python manage.py create_test_patients
```

## ✅ Étape 6 : Lancer le serveur

```bash
python manage.py runserver
```

## 🎉 C'est terminé !

Votre application utilise maintenant PostgreSQL au lieu de SQLite.

---

## 🔧 Commandes utiles PostgreSQL

### Se connecter à PostgreSQL via psql :
```bash
psql -U postgres
```

### Lister les bases de données :
```sql
\l
```

### Se connecter à la base medical_search_db :
```sql
\c medical_search_db
```

### Lister les tables :
```sql
\dt
```

### Voir les patients :
```sql
SELECT * FROM pathology_search_patient;
```

### Voir les consultations :
```sql
SELECT * FROM pathology_search_consultation;
```

