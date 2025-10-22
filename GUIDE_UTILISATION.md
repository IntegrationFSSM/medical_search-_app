# Guide d'Utilisation - Recherche de Pathologies Médicales

## 🚀 Démarrage Rapide

### Installation en 5 étapes

1. **Activer l'environnement virtuel**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Installer les dépendances** (si ce n'est pas déjà fait)
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer le fichier .env**
   - Ouvrez le fichier `.env`
   - Vérifiez que votre clé API OpenAI est correcte
   - Ajustez le chemin `EMBEDDINGS_FOLDER` selon votre système

4. **Appliquer les migrations**
   ```bash
   python manage.py migrate
   ```

5. **Lancer le serveur**
   ```bash
   python manage.py runserver
   ```

Accédez à : **http://127.0.0.1:8000/**

## 📝 Exemples de Requêtes

### Requêtes Cliniques

#### Exemple 1 : Encoprésie
```
Un enfant de 7 ans sans maladie médicale continue de passer les selles 
dans des endroits inappropriés malgré avoir été entraîné à la propreté 
depuis 3 ans.
```

#### Exemple 2 : Questions Diagnostiques
```
Quels sont les critères diagnostiques pour l'encoprésie selon le DSM-5?
```

#### Exemple 3 : Mécanismes Physiopathologiques
```
Comment la constipation chronique conduit-elle à une incontinence 
de débordement chez les enfants?
```

#### Exemple 4 : Symptômes Généraux
```
Un patient présente des difficultés à contrôler ses sphincters et 
souille régulièrement ses vêtements.
```

## 🎯 Interprétation des Résultats

### Niveaux de Confiance

| Score | Couleur | Signification |
|-------|---------|---------------|
| ≥ 75% | 🟢 Vert | **Forte correspondance** - Diagnostic très probable |
| 60-74% | 🟡 Jaune | **Correspondance modérée** - Envisager diagnostic différentiel |
| < 60% | 🔴 Rouge | **Faible correspondance** - Informations supplémentaires nécessaires |

### Éléments Affichés

1. **Pathologie Suspectée** : Le nom de la pathologie la plus probable
2. **Score de Similarité** : Pourcentage de correspondance (0-100%)
3. **Extrait Pertinent** : Section la plus pertinente du document
4. **Localisation** : Système ou région anatomique concerné
5. **Nombre de Chunks** : Sections du document analysées

## ⚙️ Configuration des Paramètres

### Nombre de Résultats

- **3 résultats** : Pour une réponse rapide et ciblée
- **5 résultats** : Équilibre entre précision et couverture (recommandé)
- **10 résultats** : Pour explorer plusieurs diagnostics différentiels

### Méthodes d'Agrégation

#### Maximum (Recommandé)
- Utilise le meilleur score par fichier
- **Idéal pour** : Recherche de correspondances précises
- **Avantages** : Trouve les sections les plus pertinentes

#### Moyenne
- Calcule la moyenne de tous les chunks
- **Idéal pour** : Vue d'ensemble du document
- **Avantages** : Équilibre les informations

#### Moyenne Pondérée
- Privilégie les premiers chunks du document
- **Idéal pour** : Documents structurés (introduction importante)
- **Avantages** : Valorise les définitions et critères principaux

## 💡 Conseils d'Optimisation

### Pour de Meilleurs Résultats

1. **Soyez spécifique**
   - ✅ "Enfant de 6 ans avec passages répétés de selles hors toilettes depuis 4 mois"
   - ❌ "Problème de toilette"

2. **Incluez le contexte**
   - Âge du patient
   - Durée des symptômes
   - Contexte médical
   - Fréquence

3. **Utilisez un langage médical**
   - ✅ "Incontinence fécale avec constipation chronique"
   - ❌ "Il fait caca dans son pantalon"

4. **Posez des questions précises**
   - ✅ "Quels sont les critères DSM-5 pour..."
   - ❌ "Qu'est-ce que c'est?"

### Quand Utiliser Chaque Format

| Type de Requête | Format Recommandé | Exemple |
|-----------------|-------------------|---------|
| Cas clinique | Description narrative | "Un enfant de..." |
| Critères diagnostiques | Question directe | "Quels sont les critères..." |
| Physiopathologie | Question mécanisme | "Comment... conduit à..." |
| Symptômes isolés | Liste de symptômes | "Patient avec X, Y, Z" |

## 🔍 Analyse des Résultats

### Que Faire avec les Résultats?

1. **Score ≥ 80%** 
   - Diagnostic très probable
   - Lire les extraits pour confirmation
   - Vérifier les critères diagnostiques

2. **Score 60-79%**
   - Diagnostic possible
   - Comparer avec les autres résultats
   - Considérer un diagnostic différentiel
   - Rechercher des informations complémentaires

3. **Score < 60%**
   - Correspondance faible
   - Reformuler la requête
   - Ajouter plus de détails cliniques
   - Essayer une autre méthode d'agrégation

### Interpréter les Extraits

Les extraits montrent :
- Les sections les plus pertinentes du document source
- Les critères diagnostiques correspondants
- Les descriptions symptomatiques similaires

**Conseil** : Lisez toujours les extraits pour valider la pertinence du résultat.

## 🛠️ Résolution de Problèmes

### Problème : "Aucun fichier d'embedding trouvé"

**Solutions** :
1. Vérifiez le chemin dans `.env` :
   ```env
   EMBEDDINGS_FOLDER=C:/Users/VotreNom/embeddings
   ```
2. Vérifiez que les fichiers `.npy` et `.json` existent
3. Sur Windows, utilisez `/` ou `\\` dans les chemins

### Problème : "Erreur API OpenAI"

**Solutions** :
1. Vérifiez votre clé API dans `.env`
2. Vérifiez vos crédits OpenAI
3. Vérifiez votre connexion Internet

### Problème : Résultats non pertinents

**Solutions** :
1. Reformulez votre requête avec plus de détails
2. Essayez une autre méthode d'agrégation
3. Augmentez le nombre de résultats
4. Utilisez un langage médical plus précis

### Problème : Serveur ne démarre pas

**Solutions** :
```bash
# Vérifiez que le port 8000 n'est pas utilisé
python manage.py runserver 8001

# Vérifiez les migrations
python manage.py migrate

# Vérifiez les dépendances
pip install -r requirements.txt --upgrade
```

## 📊 Cas d'Usage

### Cas 1 : Identification de Pathologie
**Objectif** : Identifier une pathologie à partir de symptômes

**Étapes** :
1. Entrez la description clinique complète
2. Utilisez 5 résultats avec méthode "Maximum"
3. Analysez le score du premier résultat
4. Lisez l'extrait pertinent
5. Comparez avec les diagnostics différentiels

### Cas 2 : Vérification de Critères
**Objectif** : Confirmer les critères diagnostiques

**Étapes** :
1. Posez une question précise sur les critères
2. Utilisez 3 résultats avec méthode "Maximum"
3. Lisez les extraits des meilleurs résultats
4. Notez les critères listés

### Cas 3 : Exploration Diagnostique
**Objectif** : Explorer plusieurs diagnostics possibles

**Étapes** :
1. Entrez une description générale
2. Utilisez 10 résultats avec méthode "Moyenne"
3. Comparez les scores de tous les résultats
4. Identifiez les tendances communes
5. Affinez avec une recherche plus précise

## 📚 Ressources Complémentaires

- [Documentation Django](https://docs.djangoproject.com/)
- [API OpenAI](https://platform.openai.com/docs/)
- [Guide des Embeddings](https://platform.openai.com/docs/guides/embeddings)

## 💬 Support

Pour toute question :
1. Consultez ce guide
2. Vérifiez le README.md
3. Consultez la page "À propos" de l'application

---

**Dernière mise à jour** : Octobre 2025

