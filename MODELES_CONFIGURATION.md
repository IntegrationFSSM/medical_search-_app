# Configuration des Modèles d'Embedding

Ce projet supporte maintenant trois modèles pour calculer la similarité :
- **ChatGPT 5.1** (OpenAI) - ✅ Déjà configuré
- **Claude 4.5** (Anthropic) - ⚠️ Nécessite configuration
- **Gemini 3** (Google) - ⚠️ Nécessite configuration

## 📋 Structure Actuelle

### 1. Interface HTML
L'interface permet de sélectionner le modèle **avant** de lancer la recherche de similarité.
Le sélecteur se trouve sur la page principale, juste avant le formulaire de recherche.

### 2. Service Backend
Le fichier `pathology_search/services.py` contient la classe `PathologySearchService` qui supporte les 3 modèles.

## 🔧 Configuration des Modèles

### ChatGPT 5.1 (OpenAI) - ✅ Déjà configuré
- **Fichier** : `medical_search/settings.py`
- **Variable d'environnement** : `OPENAI_API_KEY`
- **Status** : Fonctionnel directement

### Claude Sonnet 4.5 (Anthropic) - ✅ Utilisation directe (sans embeddings)

**Statut** : ✅ Bibliothèque installée, ✅ Code implémenté, ✅ API directe disponible

**IMPORTANT** : 
- Claude est utilisé **directement** pour la génération de texte (diagnostics)
- Pour les embeddings (recherche de similarité), le système utilise automatiquement OpenAI comme fallback
- Claude ne supporte pas d'API d'embeddings, mais est excellent pour la génération de texte

1. **Bibliothèque déjà installée** :
   - `anthropic>=0.34.0` est déjà dans `requirements.txt`
   - Installée avec `pip install -r requirements.txt`

2. **Clé API dans `settings.py`** (déjà configuré) :
```python
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')
```

3. **Fonctionnement** :
   - ✅ **Génération de diagnostics** : Utilise Claude directement (excellent pour le texte)
   - ✅ **Recherche de similarité** : Utilise OpenAI automatiquement (fallback)
   - ✅ **Pas besoin de configuration supplémentaire**

4. **Obtenir et configurer la clé API** :
   - Obtenez votre clé API depuis [Anthropic Console](https://console.anthropic.com/)
   - Ajoutez-la dans votre fichier `.env` :
   ```
   CLAUDE_API_KEY=votre_clé_api_anthropic
   ```

5. **Modèle Claude Sonnet 4.5** :
   - **Modèle utilisé par défaut** : `claude-sonnet-4-5-20250929` (Claude Sonnet 4.5 - le plus récent)
   - **Configuration** : Défini dans `settings.py` via `CLAUDE_MODEL`
   - **Personnalisation** : Vous pouvez changer le modèle dans `.env` :
     ```
     CLAUDE_MODEL=claude-sonnet-4-5-20250929  # Claude Sonnet 4.5 (par défaut, le plus récent) ⭐
     # ou
     CLAUDE_MODEL=claude-3-opus-20240229       # Claude 3 Opus (plus puissant)
     # ou
     CLAUDE_MODEL=claude-3-sonnet-20240229     # Équilibre performance/prix
     # ou
     CLAUDE_MODEL=claude-3-haiku-20240307      # Plus rapide et moins cher
     ```
   - **Important** : Le modèle disponible dépend de votre clé API et de votre abonnement Anthropic

**Note** : Claude Sonnet 4.5 est maintenant complètement fonctionnel pour la génération de textes médicaux. Les embeddings utilisent automatiquement OpenAI en arrière-plan.

### Gemini 3 (Google) - ✅ Prêt à utiliser

**Statut** : ✅ Bibliothèque installée, ✅ Code implémenté, ⚠️ Nécessite clé API

1. **Bibliothèque déjà installée** :
   - `google-generativeai>=0.8.0` est déjà dans `requirements.txt`
   - Installée avec `pip install -r requirements.txt`

2. **Clé API dans `settings.py`** (déjà configuré) :
```python
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
```

3. **Code déjà implémenté** :
   - Le code est déjà fonctionnel dans `pathology_search/services.py`
   - Utilise `genai.GenerativeModel()` avec le modèle configuré (par défaut: `gemini-1.5-pro`)
   - Pour les embeddings, utilise `models/embedding-001`

4. **Obtenir et configurer la clé API** :
   - Obtenez votre clé API depuis [Google AI Studio](https://ai.google.dev/)
   - Ajoutez-la dans votre fichier `.env` :
   ```
   GEMINI_API_KEY=votre_clé_api_google
   GEMINI_MODEL=gemini-1.5-pro
   ```

5. **Modèle Gemini 3** :
   - **Modèle utilisé par défaut** : `gemini-3-pro-preview` (Google Generative AI - le plus récent) ⭐
   - **Configuration** : Défini dans `settings.py` via `GEMINI_MODEL`
   - **Personnalisation** : Vous pouvez changer le modèle dans `.env` :
     ```
     GEMINI_MODEL=gemini-3-pro-preview  # Gemini 3 Pro Preview (par défaut, le plus récent) ⭐
     # ou
     GEMINI_MODEL=gemini-2.5-pro        # Version stable récente
     # ou
     GEMINI_MODEL=gemini-2.5-flash      # Plus rapide et moins cher
     # ou
     GEMINI_MODEL=gemini-2.0-flash      # Version précédente
     # ou
     GEMINI_MODEL=gemini-1.5-pro        # Version précédente
     ```
   - **Note** : Le préfixe `models/` est ajouté automatiquement dans le code, ne l'incluez pas dans `.env`

6. **Tester** :
   - Sélectionnez "Gemini 3" dans le SweetAlert après validation du formulaire
   - Le diagnostic sera généré avec l'API Google

## 📝 Notes Importantes

1. **Validation** : La validation des requêtes médicales utilise toujours ChatGPT (OpenAI) pour des raisons de cohérence.

2. **Embeddings** : Chaque modèle génère des embeddings de dimensions différentes. Le code actuel utilise la similarité cosinus, qui devrait fonctionner tant que les dimensions sont compatibles.

3. **Performance** : Les embeddings doivent avoir des dimensions compatibles pour le calcul de similarité cosinus. Vérifiez les dimensions de chaque modèle.

4. **Tests** : Testez chaque modèle séparément pour vous assurer que les embeddings sont correctement générés.

## 🚀 Utilisation

1. Sélectionnez le modèle dans l'interface HTML avant de lancer la recherche
2. Le modèle sélectionné sera utilisé pour générer l'embedding de la requête
3. La similarité sera calculée avec les embeddings pré-existants de la base de données

## ⚠️ Important

- ChatGPT 5.1 est déjà fonctionnel
- Pour Claude 4.5 et Gemini 3, vous devez :
  1. Installer les bibliothèques respectives
  2. Obtenir les clés API
  3. Décommenter et adapter le code dans `services.py`
  4. Ajouter les clés dans votre fichier `.env`

