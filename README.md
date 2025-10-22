# Application Django de Recherche de Pathologies Médicales

Application web Django pour identifier des pathologies médicales basées sur des descriptions cliniques en utilisant les embeddings OpenAI et la recherche par similarité cosinus.

## 🌟 Fonctionnalités

- **Recherche intelligente** : Analysez des descriptions cliniques pour trouver les pathologies correspondantes
- **Interface moderne** : Interface utilisateur intuitive avec Tailwind CSS
- **Embeddings OpenAI** : Utilise le modèle `text-embedding-ada-002` pour des recherches précises
- **Résultats détaillés** : Affichage des scores de confiance et extraits pertinents
- **Diagnostic automatisé** : Suggestions de pathologies avec niveaux de confiance

## 📋 Prérequis

- Python 3.8 ou supérieur
- Clé API OpenAI
- Fichiers d'embeddings pré-calculés (`.npy` et `.json`)

## 🚀 Installation

### 1. Cloner ou télécharger le projet

```bash
cd medical_search_app
```

### 2. Créer un environnement virtuel

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration des variables d'environnement

Créez un fichier `.env` à la racine du projet :

```bash
cp .env.example .env
```

Modifiez le fichier `.env` avec vos informations :

```env
OPENAI_API_KEY=sk-votre_clé_api_ici
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDINGS_FOLDER=C:/chemin/vers/vos/embeddings
```

**Important** : Assurez-vous que le dossier `EMBEDDINGS_FOLDER` contient :
- Fichiers `.npy` : embeddings vectoriels
- Fichiers `.json` : métadonnées correspondantes

### 5. Appliquer les migrations

```bash
python manage.py migrate
```

### 6. Créer un superutilisateur (optionnel)

```bash
python manage.py createsuperuser
```

### 7. Lancer le serveur de développement

```bash
python manage.py runserver
```

L'application sera accessible à : **http://127.0.0.1:8000/**

## 📁 Structure du Projet

```
medical_search_app/
├── medical_search/           # Configuration du projet Django
│   ├── settings.py          # Paramètres Django
│   ├── urls.py              # URLs principales
│   └── wsgi.py              # Configuration WSGI
├── pathology_search/         # Application principale
│   ├── services.py          # Service de recherche d'embeddings
│   ├── views.py             # Vues Django
│   ├── urls.py              # URLs de l'application
│   ├── templates/           # Templates HTML
│   │   └── pathology_search/
│   │       ├── base.html
│   │       ├── index.html
│   │       └── about.html
│   └── static/              # Fichiers statiques
├── manage.py                # Script de gestion Django
├── requirements.txt         # Dépendances Python
├── .env.example            # Exemple de configuration
└── README.md               # Ce fichier
```

## 🎯 Utilisation

### Interface Web

1. Accédez à **http://127.0.0.1:8000/**
2. Entrez une description clinique ou une question dans le formulaire
3. Sélectionnez le nombre de résultats souhaités (3, 5 ou 10)
4. Choisissez la méthode d'agrégation :
   - **Maximum** : Utilise le score le plus élevé par fichier
   - **Moyenne** : Calcule la moyenne des scores
   - **Moyenne pondérée** : Privilégie les premiers chunks
5. Cliquez sur "Rechercher"
6. Consultez les résultats avec :
   - Pathologie suspectée
   - Score de confiance
   - Extraits pertinents
   - Localisation anatomique

### Exemples de requêtes

```
"Un enfant sans maladie médicale continue de passer les selles 
dans des endroits inappropriés malgré avoir été entraîné à la propreté"

"Quels sont les critères diagnostiques pour l'encoprésie?"

"Comment la constipation conduit-elle à l'incontinence de débordement?"
```

## ⚙️ Configuration Avancée

### Personnalisation des Settings

Modifiez `medical_search/settings.py` pour :
- Changer la langue : `LANGUAGE_CODE = 'fr-fr'`
- Modifier le fuseau horaire : `TIME_ZONE = 'Europe/Paris'`
- Ajuster les paramètres de sécurité pour la production

### Méthodes d'Agrégation

- **max** : Meilleure pour des correspondances précises
- **mean** : Meilleure pour une vue d'ensemble
- **weighted_mean** : Privilégie le début des documents

## 🔒 Sécurité

⚠️ **Important pour la production** :

1. Ne jamais commiter le fichier `.env`
2. Changer la `SECRET_KEY` dans `settings.py`
3. Définir `DEBUG = False`
4. Configurer `ALLOWED_HOSTS`
5. Utiliser HTTPS
6. Configurer un serveur web (nginx, Apache)
7. Utiliser un WSGI server (Gunicorn, uWSGI)

## 🐛 Dépannage

### Erreur "Aucun fichier d'embedding trouvé"

- Vérifiez que le chemin `EMBEDDINGS_FOLDER` est correct
- Assurez-vous que les fichiers `.npy` et `.json` existent
- Vérifiez les permissions d'accès au dossier

### Erreur d'API OpenAI

- Vérifiez que votre clé API est valide
- Vérifiez que vous avez des crédits disponibles
- Vérifiez votre connexion Internet

### Erreur de module

```bash
pip install -r requirements.txt --upgrade
```

## 📝 Script Original

Cette application Django est basée sur le script Python original de recherche d'embeddings. Le code original a été restructuré en :
- Service réutilisable (`services.py`)
- Vues Django (`views.py`)
- Templates modernes avec interface utilisateur
- Configuration via variables d'environnement

## 🤝 Contribution

Pour contribuer à ce projet :

1. Fork le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Committez vos changements (`git commit -m 'Ajout fonctionnalité'`)
4. Pushez vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.

## 👨‍⚕️ Support

Pour toute question ou problème :
- Consultez la page "À propos" de l'application
- Vérifiez la documentation Django : https://docs.djangoproject.com/
- Documentation OpenAI : https://platform.openai.com/docs/

## 🔄 Mises à jour futures

- [ ] Ajout d'un système de cache pour les recherches
- [ ] Historique des recherches
- [ ] Export des résultats en PDF
- [ ] Authentification utilisateur
- [ ] API REST pour l'intégration avec d'autres systèmes
- [ ] Support multilingue
- [ ] Visualisation des scores de similarité

