# Variables d'environnement (.env)

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

## 🔑 Variables obligatoires

### OpenAI (ChatGPT 5.1) - ✅ Obligatoire
```
OPENAI_API_KEY=sk-votre_clé_api_openai_ici
```
- **Où l'obtenir** : [OpenAI Platform](https://platform.openai.com/api-keys)
- **Utilisation** : 
  - Recherche de similarité (embeddings)
  - Validation des requêtes médicales
  - Fallback automatique pour les autres modèles si dimensions incompatibles

### Modèle d'embedding OpenAI (Optionnel)
```
EMBEDDING_MODEL=text-embedding-ada-002
```
- **Défaut** : `text-embedding-ada-002`
- **Alternatives** : `text-embedding-3-small`, `text-embedding-3-large`

---

## 🔑 Variables optionnelles

### Claude Sonnet 4.5 (Anthropic) - Optionnel
```
CLAUDE_API_KEY=sk-ant-votre_clé_api_anthropic_ici
```
- **Où l'obtenir** : [Anthropic Console](https://console.anthropic.com/)
- **Utilisation** : Génération de diagnostics médicaux (textes)
- **Note** : Pour les embeddings, OpenAI est utilisé automatiquement

### Modèle Claude (Optionnel)
```
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```
- **Défaut** : `claude-sonnet-4-5-20250929` (Claude Sonnet 4.5 - le plus récent) ⭐
- **Alternatives disponibles** :
  - `claude-sonnet-4-5-20250929` : Claude Sonnet 4.5 (par défaut, le plus récent)
  - `claude-3-opus-20240229` : Claude 3 Opus (plus puissant)
  - `claude-3-sonnet-20240229` : Équilibre performance/prix
  - `claude-3-haiku-20240307` : Plus rapide et moins cher
- **Note** : Le modèle exact dépend de votre clé API et de votre abonnement Anthropic

---

### Gemini 3 (Google) - Optionnel
```
GEMINI_API_KEY=votre_clé_api_google_ici
GEMINI_MODEL=gemini-3-pro-preview
```
- **Où l'obtenir** : [Google AI Studio](https://ai.google.dev/)
- **Modèle par défaut** : `gemini-3-pro-preview` (le plus récent) ⭐
- **Alternatives disponibles** :
  - `gemini-3-pro-preview` : Le plus récent et puissant (par défaut) ⭐
  - `gemini-2.5-pro` : Version stable récente
  - `gemini-2.5-flash` : Plus rapide et moins cher
  - `gemini-2.0-flash` : Version précédente
  - `gemini-1.5-pro` : Version précédente
  - **Note** : Le préfixe `models/` est ajouté automatiquement dans le code
- **Utilisation** : Génération de diagnostics médicaux (textes)
- **Note** : Pour les embeddings, OpenAI est utilisé automatiquement si dimensions incompatibles

---

## 📝 Exemple de fichier .env complet

```env
# ===== OPENAI (OBLIGATOIRE) =====
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EMBEDDING_MODEL=text-embedding-ada-002

# ===== CLAUDE SONNET 4.5 (OPTIONNEL) =====
CLAUDE_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# ===== GEMINI 3 (OPTIONNEL) =====
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-3-pro-preview

# ===== AUTRES CONFIGURATIONS =====
# Si vous utilisez une base de données PostgreSQL locale
DB_NAME=medical_search_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# Clé secrète Django (pour la production)
SECRET_KEY=votre_clé_secrète_django_ici

# Mode debug (True pour développement, False pour production)
DEBUG=True

# Dossier des embeddings (par défaut: Embedding/)
EMBEDDINGS_FOLDER=Embedding
```

---

## ⚠️ Notes importantes

1. **OPENAI_API_KEY est OBLIGATOIRE** :
   - Même si vous utilisez Claude ou Gemini, OpenAI est utilisé pour :
     - Les embeddings (recherche de similarité)
     - La validation des requêtes médicales
     - Le fallback automatique si dimensions incompatibles

2. **Gestion automatique des dimensions** :
   - Si Gemini génère des embeddings de dimension 768 mais que vos embeddings stockés sont de dimension 1536 (OpenAI), le système utilise automatiquement OpenAI pour les embeddings
   - Gemini/Claude seront utilisés uniquement pour la génération de textes

3. **Sécurité** :
   - ⚠️ **NE JAMAIS** commiter le fichier `.env` dans Git
   - Le fichier `.env` est normalement dans `.gitignore`
   - Gardez vos clés API secrètes

4. **Configuration minimale** :
   - Pour que l'application fonctionne, il suffit de configurer `OPENAI_API_KEY`
   - Les autres clés API sont optionnelles pour utiliser les modèles respectifs

---

## 🚀 Installation

1. Créez le fichier `.env` à la racine du projet
2. Copiez les variables ci-dessus dans le fichier
3. Remplacez les valeurs par vos vraies clés API
4. Redémarrez l'application Django

**Exemple de commande pour créer le fichier :**
```bash
# Windows
copy NUL .env
notepad .env

# Linux/Mac
touch .env
nano .env
```

