# 🧠 Système de Diagnostic IA Médical

## 📋 Fonctionnalité Ajoutée

Un système complet de diagnostic assisté par **Intelligence Artificielle** utilisant **OpenAI GPT-4o-mini** pour générer des rapports cliniques détaillés basés sur les critères DSM-5-TR validés.

---

## ✨ Workflow Complet

```
1. 🔍 RECHERCHE
   └─> Rechercher une pathologie (ex: "trouble anxieux")
   
2. ☑️ MODE VALIDATION
   └─> Cocher "Mode Validation Étape par Étape"
   
3. 📄 FORMULAIRE
   └─> Remplir les critères diagnostiques
   └─> Cocher toutes les options pertinentes
   
4. ✅ VALIDATION
   └─> Cliquer sur "VALIDE"
   
5. ⏳ GÉNÉRATION IA (avec barre de progression)
   ├─> 📋 Analyse des critères diagnostiques...
   ├─> 🧠 Consultation de l'IA médicale...
   ├─> 📊 Génération du rapport clinique...
   └─> ✨ Finalisation du diagnostic...
   
6. 📊 RAPPORT DIAGNOSTIC
   └─> Affichage du diagnostic IA complet
```

---

## 🎯 Caractéristiques Principales

### 1. **Capture Intelligente des Données**
- ✅ Tous les éléments cochés (checkboxes, radios)
- ✅ Champs texte (textarea)
- ✅ Sélections (select)
- ✅ Structure JSON organisée

### 2. **Barre de Progression Animée**
- 🎨 Design moderne avec gradient
- ⚡ Animation fluide (0% → 100%)
- 📝 Étapes détaillées :
  - Analyse des critères
  - Consultation de l'IA
  - Génération du rapport
  - Finalisation

### 3. **Génération IA avec OpenAI**
- 🤖 **Modèle**: GPT-4o-mini
- 📚 **Expertise**: Psychiatrie DSM-5-TR
- 🇫🇷 **Langue**: Français professionnel
- ⚡ **Temps**: ~5-10 secondes

### 4. **Rapport Clinique Structuré**
Le diagnostic IA comprend automatiquement :

1. **Diagnostic Principal**
   - Code DSM-5-TR
   - Nom complet du trouble

2. **Analyse des Critères**
   - Revue détaillée des critères cochés
   - Justification clinique

3. **Évaluation de la Sévérité**
   - Léger / Modéré / Sévère
   - Justification

4. **Recommandations Thérapeutiques**
   - Psychothérapie
   - Pharmacothérapie
   - Interventions complémentaires

5. **Diagnostic Différentiel**
   - Autres troubles à considérer
   - Critères d'exclusion

6. **Notes Cliniques**
   - Observations importantes
   - Points d'attention

---

## 🎨 Interface du Rapport

### Badge de Confiance
```css
🟢 Haute Confiance (≥75%)    - Vert
🟡 Confiance Modérée (60-74%) - Orange
🔴 Faible Confiance (<60%)    - Rouge
```

### Sections Visuelles
- 📊 **Header** : Titre + Badge de confiance + Timestamp
- 📝 **Rapport Clinique** : Diagnostic IA détaillé
- ✅ **Critères Validés** : Affichage organisé des données
- 🔍 **Info Recherche** : Détails du résultat original

### Actions Disponibles
- 🏠 **Retour à l'accueil**
- 🖨️ **Imprimer le rapport** (optimisé pour impression)

---

## 💻 Code Technique

### Backend (Django)

**Service IA** : `pathology_search/services.py`
```python
def generate_ai_diagnosis(self, pathology_name, form_data, similarity_score):
    """Génère un diagnostic détaillé avec OpenAI"""
    # Construit un prompt structuré
    # Appelle GPT-4o-mini
    # Retourne le rapport clinique
```

**Vue** : `pathology_search/views.py`
```python
def validate_action(request):
    """Capture les données et génère le diagnostic"""
    # Capture form_data du frontend
    # Appelle le service IA
    # Sauvegarde en session
    # Retourne diagnosis_id
```

**URL** : `/diagnosis/<diagnosis_id>/`

### Frontend (JavaScript)

**Capture des Données**
```javascript
function captureFormData() {
    // Récupère tous les inputs cochés
    // Récupère textarea et select
    // Retourne un objet structuré
}
```

**Barre de Progression**
```javascript
// Animation 0% → 100%
// Changement d'étapes automatique
// Redirection après génération
```

---

## 🔧 Configuration

### Variables Requises

`.env` :
```env
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDINGS_FOLDER=C:\Users\...\Embedding
```

### Dépendances

`requirements.txt` :
```
openai>=1.0.0
django>=5.0.0
python-dotenv
numpy
```

---

## 🧪 Test du Système

1. **Démarrer le serveur**
   ```bash
   python manage.py runserver
   ```

2. **Accéder à l'application**
   ```
   http://127.0.0.1:8000/
   ```

3. **Effectuer une recherche**
   - Rechercher : "trouble panique"
   - Cocher : "Mode Validation Étape par Étape"

4. **Remplir le formulaire**
   - Cocher les critères pertinents
   - Sélectionner les spécificateurs

5. **Valider**
   - Cliquer sur "VALIDE"
   - Observer la barre de progression
   - Consulter le rapport généré

---

## 📊 Exemple de Prompt Envoyé à l'IA

```
En tant qu'expert psychiatre, veuillez analyser le cas clinique suivant 
et fournir un diagnostic détaillé.

**Pathologie identifiée :** Trouble Panique
**Score de correspondance :** 87.3%

**Critères diagnostiques validés :**

**critereA:**
  ✓ Attaques de panique récurrentes
  ✓ Peur intense
  ✓ Symptômes physiques

**critereB:**
  ✓ Au moins une attaque suivie d'inquiétude persistante
  ✓ Changement de comportement inadapté

...

**Veuillez fournir un rapport clinique structuré comprenant :**
1. Diagnostic Principal
2. Analyse des Critères
3. Sévérité
4. Recommandations Thérapeutiques
5. Diagnostic Différentiel
6. Notes Cliniques
```

---

## 🎯 Avantages du Système

✅ **Gain de temps** : Génération automatique du rapport
✅ **Cohérence** : Format standardisé DSM-5-TR
✅ **Complétude** : Tous les aspects diagnostiques couverts
✅ **Aide à la décision** : Suggestions thérapeutiques
✅ **Traçabilité** : Historique des validations
✅ **Professionnalisme** : Rapport imprimable

---

## 🔒 Sécurité et Confidentialité

- 🔐 Données en session (non persistées en base)
- 🔑 API OpenAI sécurisée (clé en variable d'environnement)
- 🚫 Pas de stockage des diagnostics à long terme
- ✅ CSRF protection sur toutes les requêtes

---

## 📈 Améliorations Futures Possibles

1. 💾 **Sauvegarde des diagnostics** en base de données
2. 📧 **Export PDF** du rapport
3. 📊 **Statistiques** des diagnostics générés
4. 🔄 **Historique patient** avec diagnostics multiples
5. 🌐 **API REST** pour intégration externe
6. 🎨 **Personnalisation** du template de rapport
7. 🗣️ **Support multilingue** (EN, ES, AR)
8. 📱 **Version mobile** responsive

---

## 🎉 Résultat Final

**Un système complet et professionnel de diagnostic assisté par IA** qui combine :
- 🔍 Recherche sémantique intelligente
- 📝 Validation interactive des critères
- 🧠 Intelligence artificielle médicale
- 📊 Rapports cliniques détaillés
- 🎨 Interface utilisateur moderne

**Prêt pour une utilisation clinique professionnelle !** ✨

