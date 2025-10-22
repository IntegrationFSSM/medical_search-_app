# 🚀 Installation Rapide

## Windows

### Méthode 1 : Script Automatique (Recommandé)

Double-cliquez sur `start.bat` ou exécutez :
```cmd
start.bat
```

### Méthode 2 : Manuel

```cmd
# 1. Créer et activer l'environnement virtuel
python -m venv venv
venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Vérifier/Créer le fichier .env
# Assurez-vous que .env existe avec votre clé API

# 4. Appliquer les migrations
python manage.py migrate

# 5. Lancer le serveur
python manage.py runserver
```

Accédez à : **http://127.0.0.1:8000/**

---

## macOS / Linux

### Méthode 1 : Script Automatique (Recommandé)

```bash
chmod +x start.sh
./start.sh
```

### Méthode 2 : Manuel

```bash
# 1. Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Vérifier/Créer le fichier .env
# Assurez-vous que .env existe avec votre clé API

# 4. Appliquer les migrations
python manage.py migrate

# 5. Lancer le serveur
python manage.py runserver
```

Accédez à : **http://127.0.0.1:8000/**

---

## ⚠️ Points Importants

### 1. Fichier .env

Le fichier `.env` doit contenir :

```env
OPENAI_API_KEY=votre_clé_api_ici
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDINGS_FOLDER=chemin/vers/vos/embeddings
```

**Note** : Le fichier `.env` est déjà créé avec votre clé API. Modifiez seulement le chemin `EMBEDDINGS_FOLDER` si nécessaire.

### 2. Dossier Embeddings

Assurez-vous que le dossier contient :
- Fichiers `.npy` (embeddings vectoriels)
- Fichiers `.json` (métadonnées)

### 3. Formats de Chemins

**Windows** :
```env
EMBEDDINGS_FOLDER=C:/Users/VotreNom/embeddings
# OU
EMBEDDINGS_FOLDER=C:\\Users\\VotreNom\\embeddings
```

**macOS/Linux** :
```env
EMBEDDINGS_FOLDER=/home/utilisateur/embeddings
```

**Google Drive (Colab)** :
```env
EMBEDDINGS_FOLDER=/content/drive/MyDrive/Embedding
```

---

## 🧪 Test de l'Application

Une fois le serveur démarré :

1. Ouvrez **http://127.0.0.1:8000/** dans votre navigateur
2. Entrez une requête de test :
   ```
   Un enfant sans maladie médicale continue de passer les selles 
   dans des endroits inappropriés malgré avoir été entraîné à la propreté.
   ```
3. Cliquez sur "Rechercher"
4. Vérifiez que les résultats s'affichent

---

## 🔧 Résolution de Problèmes Rapide

### Erreur : "No module named 'django'"
```bash
pip install -r requirements.txt
```

### Erreur : "OPENAI_API_KEY not found"
Vérifiez que le fichier `.env` existe et contient votre clé API.

### Erreur : "Aucun fichier d'embedding trouvé"
Vérifiez le chemin `EMBEDDINGS_FOLDER` dans `.env`.

### Port 8000 déjà utilisé
```bash
python manage.py runserver 8001
```

---

## 📚 Documentation Complète

Pour plus de détails, consultez :
- `README.md` - Documentation complète
- `GUIDE_UTILISATION.md` - Guide d'utilisation détaillé

---

**Prêt à démarrer !** 🎉

