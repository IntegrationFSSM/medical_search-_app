# Guide de Déploiement sur Heroku

## 📋 Prérequis
- Compte Heroku créé
- Heroku CLI installé
- Application Heroku créée

## 🚀 Étapes de Déploiement

### 1. Vérifier les migrations
Toutes les migrations sont incluses dans le commit :
- `0004_consultation_plan_traitement_valide.py`
- `0005_consultation_notes_medecin.py`
- `0006_alter_patient_options_patient_affiliation_number_and_more.py`
- `0007_alter_patient_numero_dossier.py`

### 2. Ajouter tous les fichiers modifiés
```bash
git add .
```

### 3. Commiter les changements
```bash
git commit -m "Ajout fonctionnalités: création patient, gestion historique symptômes, amélioration navigation"
```

### 4. Push vers Heroku
```bash
git push heroku master
```

OU si vous utilisez `main` comme branche :
```bash
git push heroku main
```

### 5. Les migrations s'exécutent automatiquement
Le `Procfile` contient maintenant :
```
web: gunicorn medical_search.wsgi --log-file -
release: python manage.py migrate --noinput
```

Heroku exécutera automatiquement les migrations lors du déploiement grâce à la commande `release`.

### 6. Vérifier les migrations
Après le déploiement, vous pouvez vérifier :
```bash
heroku run python manage.py showmigrations
```

### 7. Vérifier les logs
```bash
heroku logs --tail
```

## ⚙️ Variables d'Environnement à Configurer sur Heroku

Assurez-vous que toutes les variables suivantes sont configurées dans Heroku :

```bash
heroku config:set SECRET_KEY="votre-secret-key"
heroku config:set DEBUG="False"
heroku config:set ALLOWED_HOSTS="votre-app.herokuapp.com"
heroku config:set OPENAI_API_KEY="votre-clé-openai"
heroku config:set CLAUDE_API_KEY="votre-clé-claude"
heroku config:set DATABASE_URL="(configuré automatiquement par Heroku)"
```

## 📝 Notes Importantes

- Les migrations s'exécutent automatiquement lors du déploiement grâce au `release` dans le Procfile
- Si une migration échoue, le déploiement sera annulé
- Vérifiez toujours les logs après le déploiement
- La base de données PostgreSQL est gérée automatiquement par Heroku

## 🔍 En cas de problème

Si les migrations ne s'exécutent pas automatiquement :
```bash
heroku run python manage.py migrate
```

Pour voir les migrations en attente :
```bash
heroku run python manage.py showmigrations
```

