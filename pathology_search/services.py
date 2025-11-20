"""
Service pour la recherche de pathologies basée sur les embeddings OpenAI
"""
import numpy as np
from pathlib import Path
import json
from openai import OpenAI
from django.conf import settings


class PathologySearchService:
    """Service de recherche de pathologies médicales via embeddings."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.EMBEDDING_MODEL
        self.embeddings_folder = settings.EMBEDDINGS_FOLDER
    
    def validate_medical_query(self, query):
        """
        Valider si une requête est une description médicale valide en utilisant GPT-4o.
        
        Args:
            query: Texte de la requête à valider
            
        Returns:
            dict: {
                'is_valid': bool,
                'reason': str (si non valide)
            }
        """
        try:
            prompt = f"""Tu es un validateur médical. Analyse la requête suivante et détermine si elle contient un réel contenu médical OU du texte sans sens.

Requête: "{query}"

ACCEPTE (is_valid = true) si la requête:
- Mentionne des symptômes, troubles, comportements ou conditions médicales
- Décrit une situation clinique (même simple)
- Est liée à la santé mentale ou comportementale
- Contient des mots français/anglais normaux avec du sens médical
- Exemples VALIDES: "homme alcoolique", "enfant anxieux", "troubles du sommeil", "dépression", "patient agressif"

REJETTE (is_valid = false) SEULEMENT si:
- Mots répétitifs sans sens: "blabla blabla", "test test test", "aaaa aaaa"
- Uniquement des symboles: ".....", "????", "!!!!"
- Mots aléatoires sans rapport médical: "voiture maison arbre"
- Texte incohérent ou spam évident

IMPORTANT: Si la requête mentionne un terme médical/psychologique réel (même court), accepte-la !

Réponds UNIQUEMENT par un JSON:
{{
    "is_valid": true/false,
    "reason": "Explication courte si non valide (sinon null)"
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu es un validateur médical expert. Réponds uniquement en JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"🔍 Validation GPT-4o response: {result_text}")
            
            # Extraire le JSON si le texte contient du texte avant/après
            import json
            import re
            
            # Essayer de trouver un JSON dans le texte
            json_match = re.search(r'\{[^}]*"is_valid"[^}]*\}', result_text)
            if json_match:
                result_text = json_match.group(0)
            
            result = json.loads(result_text)
            
            is_valid = result.get('is_valid', False)
            reason = result.get('reason', 'Requête invalide')
            
            print(f"✅ Validation result: is_valid={is_valid}, reason={reason}")
            
            return {
                'is_valid': is_valid,
                'reason': reason
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON parsing: {e}")
            print(f"❌ Response text: {result_text}")
            # En cas d'erreur de parsing, considérer comme invalide par sécurité
            return {
                'is_valid': False,
                'reason': 'Erreur de validation - veuillez réessayer'
            }
        except Exception as e:
            print(f"❌ Erreur validation GPT: {e}")
            # En cas d'erreur API, considérer comme invalide par sécurité
            return {
                'is_valid': False,
                'reason': 'Service de validation temporairement indisponible'
            }
    
    def get_embedding(self, text):
        """Obtenir l'embedding d'un texte via l'API OpenAI."""
        text = text.replace("\n", " ")
        response = self.client.embeddings.create(
            input=[text], 
            model=self.embedding_model
        )
        return np.array(response.data[0].embedding)
    
    def find_best_match(self, query, top_k=5, aggregation='max'):
        """
        Trouver les meilleurs fichiers correspondant à une requête.
        
        Args:
            query: Requête texte
            top_k: Nombre de résultats à retourner
            aggregation: Méthode d'agrégation ('max', 'mean', 'weighted_mean')
        
        Returns:
            Liste des meilleurs résultats avec scores de similarité
        """
        import os
        folder_path = Path(self.embeddings_folder)
        
        # Debug: afficher les informations
        print(f"🔍 DEBUG: embeddings_folder configuré = {self.embeddings_folder}")
        print(f"🔍 DEBUG: folder_path = {folder_path}")
        print(f"🔍 DEBUG: folder_path absolu = {folder_path.absolute()}")
        print(f"🔍 DEBUG: folder_path existe? = {folder_path.exists()}")
        print(f"🔍 DEBUG: répertoire courant = {os.getcwd()}")
        
        # Lister le contenu du répertoire parent
        try:
            parent = folder_path.parent
            print(f"🔍 DEBUG: contenu de {parent}:")
            for item in os.listdir(parent):
                print(f"  - {item}")
        except Exception as e:
            print(f"❌ DEBUG: Erreur lors du listage: {e}")
        
        if not folder_path.exists():
            return {
                'success': False,
                'error': f"Le dossier d'embeddings n'existe pas: {self.embeddings_folder} (chemin absolu: {folder_path.absolute()})",
                'results': []
            }
        
        # Rechercher les fichiers .npy
        npy_files = list(folder_path.rglob("*.npy"))
        
        if len(npy_files) == 0:
            return {
                'success': False,
                'error': "Aucun fichier d'embedding trouvé (.npy)",
                'results': []
            }
        
        # Obtenir l'embedding de la requête
        query_embedding = self.get_embedding(query)
        
        # Rechercher dans tous les fichiers
        file_results = {}
        
        for emb_file in npy_files:
            # Charger les embeddings
            embeddings = np.load(emb_file)
            
            # Charger les métadonnées
            metadata_file = str(Path(emb_file).with_suffix('.json'))
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                continue
            
            # Calculer la similarité cosinus pour chaque chunk
            chunk_similarities = []
            best_chunk_id = 0
            best_chunk_text = ""
            best_similarity = 0
            
            for i, chunk_emb in enumerate(embeddings):
                similarity = np.dot(query_embedding, chunk_emb) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(chunk_emb)
                )
                chunk_similarities.append(similarity)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_chunk_id = i
                    best_chunk_text = metadata['chunks'][i].get('text_preview', '')
            
            # Agréger les scores par fichier
            if aggregation == 'max':
                file_score = max(chunk_similarities)
            elif aggregation == 'mean':
                file_score = np.mean(chunk_similarities)
            elif aggregation == 'weighted_mean':
                weights = np.array([1.0 / (i + 1) for i in range(len(chunk_similarities))])
                weights = weights / weights.sum()
                file_score = np.sum(np.array(chunk_similarities) * weights)
            else:
                file_score = max(chunk_similarities)
            
            file_results[str(emb_file)] = {
                'file': metadata['source_file'],
                'file_name': Path(metadata['source_file']).name,
                'location': metadata['hierarchy'].get('location', 'N/A'),
                'similarity': float(file_score),
                'num_chunks': len(embeddings),
                'best_chunk_id': best_chunk_id,
                'best_chunk_text': best_chunk_text,
                'all_chunk_scores': [float(s) for s in chunk_similarities],
                'html_page': metadata.get('html_page', '')  # Ajouter le chemin HTML
            }
        
        # Trier par similarité
        results = sorted(
            file_results.values(), 
            key=lambda x: x['similarity'], 
            reverse=True
        )[:top_k]
        
        # Vérifier la qualité des résultats - seuil minimum de 60% (plus strict)
        if not results or results[0]['similarity'] < 0.6:
            return {
                'success': False,
                'error': 'Aucune correspondance trouvée. Veuillez vérifier que votre description est complète et précise.',
                'error_type': 'low_similarity',
                'best_score': results[0]['similarity'] * 100 if results else 0,
                'results': []
            }
        
        # Ajouter des informations diagnostiques
        diagnostic_info = self._generate_diagnostic_info(results)
        
        return {
            'success': True,
            'results': results,
            'diagnostic_info': diagnostic_info,
            'total_files_searched': len(file_results)
        }
    
    def _generate_diagnostic_info(self, results):
        """Générer des informations diagnostiques basées sur les résultats."""
        if not results:
            return {
                'suspected_pathology': None,
                'confidence': 0,
                'confidence_level': 'none'
            }
        
        top_match = results[0]
        similarity_percent = top_match['similarity'] * 100
        
        pathology = top_match['file_name'].replace('.txt', '').replace('_', ' ')
        
        if similarity_percent >= 75:
            confidence_level = 'high'
            message = "Forte correspondance diagnostique"
        elif similarity_percent >= 60:
            confidence_level = 'moderate'
            message = "Correspondance modérée - Envisager un diagnostic différentiel"
        else:
            confidence_level = 'low'
            message = "Faible confiance - Informations cliniques supplémentaires nécessaires"
        
        return {
            'suspected_pathology': pathology,
            'confidence': similarity_percent,
            'confidence_level': confidence_level,
            'message': message
        }
    
    def generate_ai_diagnosis(self, pathology_name, form_data, similarity_score, medical_text="", historical_symptoms=None):
        """
        Générer un résumé diagnostique structuré (sans plan de traitement) avec OpenAI
        basé sur les données du formulaire, le texte médical et l'historique.
        
        Args:
            pathology_name: Nom de la pathologie validée
            historical_symptoms: Liste des symptômes/critères des consultations précédentes (optionnel)
            form_data: Données du formulaire (dict avec tous les critères cochés)
            similarity_score: Score de similarité de la recherche
            medical_text: Texte médical extrait du fichier source (documentation DSM-5-TR)
        
        Returns:
            dict: Plan de traitement généré par l'IA
        """
        try:
            # Construire le prompt pour OpenAI avec le texte médical et l'historique
            prompt = self._build_diagnosis_prompt(pathology_name, form_data, similarity_score, medical_text, historical_symptoms)
            
            # Appeler OpenAI GPT-4
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Vous êtes un psychiatre clinicien expert du DSM-5-TR. "
                            "Vous rédigez des résumés diagnostiques structurés et concis en français, "
                            "en citant uniquement les critères réellement cochés. "
                            "INTERDIT : prescrire ou détailler un plan de traitement ou des posologies."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=1800
            )
            
            diagnosis_text = response.choices[0].message.content
            
            return {
                'success': True,
                'pathology': pathology_name,
                'diagnosis': diagnosis_text,
                'confidence': similarity_score,
                'timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'pathology': pathology_name
            }
    
    def _build_diagnosis_prompt(self, pathology_name, form_data, similarity_score, medical_text="", historical_symptoms=None):
        """Construire le prompt pour OpenAI avec le texte médical et l'historique du patient."""
        
        prompt = f"""Élabore un RÉSUMÉ DIAGNOSTIQUE (sans plan thérapeutique) pour un patient évalué selon le DSM-5-TR.

Consignes obligatoires :
- Baser l'analyse UNIQUEMENT sur les critères cochés ci-dessous et sur l'extrait médical fourni.
- Ne jamais prescrire ni décrire un traitement médicamenteux ou une posologie.
- Utiliser un ton clinique, structuré et concis en français.

Informations de référence :
• Pathologie suspectée : {pathology_name}
• Niveau de correspondance : {similarity_score:.1f}%

Extrait DSM-5-TR disponible :
{medical_text if medical_text else "Aucun extrait supplémentaire. S'appuyer uniquement sur les critères cochés."}

Critères et éléments cliniques déclarés :
"""
        
        # 🆕 AJOUTER L'HISTORIQUE MÉDICAL
        if historical_symptoms and len(historical_symptoms) > 0:
            prompt += f"\n📋 **ANTÉCÉDENTS MÉDICAUX DU PATIENT ({len(historical_symptoms)} symptômes enregistrés):**\n"
            prompt += "Le patient présente également les antécédents cliniques suivants, issus de consultations précédentes:\n"
            for i, symptom in enumerate(historical_symptoms[:15], 1):  # Limiter à 15 pour ne pas surcharger
                prompt += f"  • {symptom}\n"
            if len(historical_symptoms) > 15:
                prompt += f"  • ... et {len(historical_symptoms) - 15} autres symptômes enregistrés\n"
            prompt += "\n**⚠️ IMPORTANT : Intégrer ces antécédents dans l'analyse diagnostique.**\n\n"
        
        prompt += """
"""
        
        # Ajouter les données du formulaire
        if isinstance(form_data, dict):
            for key, value in form_data.items():
                if value:  # Si la valeur n'est pas vide
                    if isinstance(value, list):
                        prompt += f"\n**{key}:**\n"
                        for item in value:
                            prompt += f"  ✓ {item}\n"
                    else:
                        prompt += f"\n**{key}:** {value}\n"
        
        prompt += """

Structure attendue (respecter EXACTEMENT ces titres) :

## 1. Synthèse clinique
- 2 à 3 phrases résumant la présentation clinique et le niveau de confiance.

## 2. Critères DSM-5 confirmés
- Reprendre les critères cochés (par blocs si possible) avec le nombre total validé.

## 3. Diagnostic différentiel prioritaire
- 3 à 5 hypothèses maximum, chacune justifiée brièvement.

## 4. Comorbidités / facteurs associés
- Éléments issus du formulaire ou traditionnellement liés à la pathologie, avec lien clinique.

## 5. Recommandations cliniques immédiates
- Étapes de suivi, examens complémentaires, coordination interdisciplinaire ou psychoéducation.
- INTERDIT : citer des molécules, dosages, ou protocoles thérapeutiques.
"""
        
        return prompt
    
    def _get_timestamp(self):
        """Obtenir le timestamp actuel."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

