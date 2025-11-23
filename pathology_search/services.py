"""
Service pour la recherche de pathologies basée sur les embeddings OpenAI et Claude
"""
import numpy as np
from pathlib import Path
import json
from openai import OpenAI
from django.conf import settings


class PathologySearchService:
    """Service de recherche de pathologies médicales via embeddings."""
    
    def __init__(self, model='chatgpt-5.1'):
        """
        Initialiser le service avec le modèle spécifié.
        
        Args:
            model: Modèle à utiliser ('chatgpt-5.1', 'claude-4.5')
        """
        self.model = model
        self.embeddings_folder = settings.EMBEDDINGS_FOLDER
        
        # Initialiser le client selon le modèle choisi
        if model == 'chatgpt-5.1':
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.embedding_model = settings.EMBEDDING_MODEL
        elif model == 'claude-4.5':
            try:
                from anthropic import Anthropic
                if not settings.CLAUDE_API_KEY:
                    raise ValueError(
                        "CLAUDE_API_KEY n'est pas configuré dans le fichier .env. "
                        "Ajoutez votre clé API Claude dans le fichier .env : CLAUDE_API_KEY=votre_clé_ici"
                    )
                if len(settings.CLAUDE_API_KEY.strip()) == 0:
                    raise ValueError("CLAUDE_API_KEY est vide dans le fichier .env")
                
                # Vérifier le format de la clé (doit commencer par sk-ant-)
                if not settings.CLAUDE_API_KEY.startswith('sk-ant-'):
                    print(f"⚠️ ATTENTION: La clé API Claude ne semble pas avoir le bon format (devrait commencer par 'sk-ant-')")
                
                # Configurer le client Claude avec un timeout de 25 secondes (sous la limite Heroku de 30s)
                import httpx
                self.client = Anthropic(
                    api_key=settings.CLAUDE_API_KEY,
                    timeout=httpx.Timeout(25.0, connect=5.0)  # 90s total, 10s pour la connexion
                )
                # Claude Sonnet 4.5 - modèle pour la génération de texte
                # Par défaut: claude-sonnet-4-5-20250929 (Claude Sonnet 4.5)
                self.claude_model = getattr(settings, 'CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')
                self.embedding_model = 'claude-sonnet-4-5-20250929'  # Modèle Claude pour embeddings (fallback OpenAI)
                print(f"✅ Client Claude initialisé avec modèle: {self.claude_model}")
            except ImportError:
                raise ImportError("La bibliothèque 'anthropic' n'est pas installée. Installez-la avec: pip install anthropic")
        else:
            raise ValueError(f"Modèle non supporté: {model}")
    
    def validate_medical_query(self, query):
        """
        Valider si une requête est une description médicale valide en utilisant GPT-4o.
        Note: La validation utilise toujours OpenAI (ChatGPT) pour des raisons de cohérence.
        
        Args:
            query: Texte de la requête à valider
            
        Returns:
            dict: {
                'is_valid': bool,
                'reason': str (si non valide)
            }
        """
        # Validation préalable simple pour les termes médicaux courants
        query_lower = query.lower().strip()
        medical_keywords = [
            'alcool', 'alcoolique', 'alcoolisme', 'dépendance', 'addiction',
            'anxieux', 'anxiété', 'anxieté', 'panique', 'phobie',
            'dépression', 'dépressif', 'déprime', 'tristesse',
            'trouble', 'symptôme', 'symptome', 'pathologie', 'maladie',
            'patient', 'personne', 'homme', 'femme', 'enfant',
            'sommeil', 'insomnie', 'agressif', 'agression', 'violence',
            'psychiatrie', 'psychologique', 'mental', 'comportement',
            'hallucination', 'délire', 'paranoïa', 'paranoia',
            'bipolaire', 'schizophrénie', 'schizophrenie', 'autisme',
            'toc', 'obsession', 'compulsion', 'trauma', 'stress',
            'suicide', 'suicidaire', 'automutilation', 'mutilation'
        ]
        
        # Si la requête contient un mot-clé médical, accepter directement
        if any(keyword in query_lower for keyword in medical_keywords):
            print(f"✅ Validation préalable: requête acceptée (contient mot-clé médical)")
            return {
                'is_valid': True,
                'reason': None
            }
        
        # Toujours utiliser OpenAI pour la validation, indépendamment du modèle d'embedding
        validation_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        try:
            prompt = f"""Tu es un validateur médical EXPERT. Analyse la requête suivante et détermine si elle contient un réel contenu médical.

Requête: "{query}"

RÈGLE PRINCIPALE: SOIS TRÈS PERMISSIF ! Accepte TOUTE description qui mentionne un problème de santé, un comportement, un symptôme ou une condition médicale, même de manière simple ou informelle.

ACCEPTE (is_valid = true) si la requête:
- Mentionne des symptômes, troubles, comportements ou conditions médicales (même un seul mot)
- Décrit une situation clinique (même très simple ou courte)
- Est liée à la santé mentale, comportementale, ou physique
- Contient des termes médicaux, psychologiques ou psychiatriques
- Décrit un patient, une personne avec un problème de santé
- Exemples VALIDES (accepte TOUS ces cas):
  * "personne trop alcoolique" ✅
  * "homme alcoolique" ✅
  * "alcoolique" ✅
  * "personne alcoolique" ✅
  * "enfant anxieux" ✅
  * "troubles du sommeil" ✅
  * "dépression" ✅
  * "patient agressif" ✅
  * "anxiété" ✅
  * "dépendance alcool" ✅
  * "trop alcoolique" ✅
  * Toute description contenant "alcool", "anxieux", "dépression", "trouble", "symptôme", etc. ✅

REJETTE (is_valid = false) UNIQUEMENT si:
- Mots répétitifs sans sens: "blabla blabla", "test test test", "aaaa aaaa"
- Uniquement des symboles: ".....", "????", "!!!!"
- Mots aléatoires sans rapport médical: "voiture maison arbre"
- Texte incohérent ou spam évident
- Chaîne de caractères aléatoires: "asdfghjkl", "qwerty"

IMPORTANT: 
- Si la requête contient UN SEUL terme médical valide, ACCEPTE-la !
- Les descriptions courtes sont acceptables: "alcoolique", "anxieux", "dépression"
- Les descriptions informelles sont acceptables: "personne trop alcoolique", "trop anxieux"
- En cas de doute, ACCEPTE plutôt que de rejeter

Réponds UNIQUEMENT par un JSON valide:
{{
    "is_valid": true/false,
    "reason": "Explication courte si non valide (sinon null)"
}}"""

            response = validation_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "Tu es un validateur médical expert. Réponds uniquement en JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"🔍 Validation GPT-4o response: {result_text}")
            
            # Extraire le JSON si le texte contient du texte avant/après
            # json already imported at module level (line 6)
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
        """
        Obtenir l'embedding d'un texte via l'API du modèle sélectionné.
        
        Args:
            text: Texte à convertir en embedding
            
        Returns:
            np.array: Vecteur d'embedding
        """
        text = text.replace("\n", " ")
        
        if self.model == 'chatgpt-5.1':
            # OpenAI / ChatGPT
            response = self.client.embeddings.create(
                input=[text], 
                model=self.embedding_model
            )
            return np.array(response.data[0].embedding)
        
        elif self.model == 'claude-4.5':
            # IMPORTANT: Anthropic Claude ne supporte pas actuellement d'API d'embeddings directe
            # Pour les embeddings, on utilise OpenAI (fallback)
            # Mais Claude peut être utilisé directement pour la génération de texte (generate_ai_diagnosis)
            try:
                # Utiliser OpenAI pour les embeddings même si le modèle choisi est Claude
                # (Claude est utilisé uniquement pour la génération de texte)
                openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = openai_client.embeddings.create(
                    input=[text], 
                    model=settings.EMBEDDING_MODEL
                )
                return np.array(response.data[0].embedding)
            except Exception as e:
                raise RuntimeError(
                    f"Erreur lors de la génération de l'embedding (fallback OpenAI): {str(e)}. "
                    f"Claude ne supporte pas les embeddings, donc OpenAI est utilisé pour cette partie."
                )
            
        else:
            raise ValueError(f"Modèle non supporté pour les embeddings: {self.model}")
    
    def find_best_match(self, query, top_k=5, aggregation='max', model=None):
        # Note: paramètre 'model' conservé pour compatibilité mais non utilisé
        # (le modèle est déjà défini dans __init__)
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
        query_dimension = len(query_embedding)
        
        # Vérifier la dimension des embeddings stockés (prendre le premier fichier comme référence)
        stored_dimension = None
        if len(npy_files) > 0:
            sample_embeddings = np.load(npy_files[0])
            if len(sample_embeddings) > 0:
                stored_dimension = len(sample_embeddings[0])
        
        # Si les dimensions ne correspondent pas, utiliser OpenAI en fallback
        if stored_dimension and query_dimension != stored_dimension:
            print(f"⚠️ Dimension incompatible: requête={query_dimension}, stocké={stored_dimension}")
            print(f"⚠️ Utilisation d'OpenAI en fallback pour les embeddings (modèle sélectionné: {self.model})")
            
            # Utiliser OpenAI pour les embeddings même si un autre modèle est sélectionné
            openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = openai_client.embeddings.create(
                input=[query], 
                model=settings.EMBEDDING_MODEL
            )
            query_embedding = np.array(response.data[0].embedding)
            query_dimension = len(query_embedding)
            print(f"✅ Embedding OpenAI généré avec dimension: {query_dimension}")
        
        # Rechercher dans tous les fichiers
        file_results = {}
        
        for emb_file in npy_files:
            # Charger les embeddings
            embeddings = np.load(emb_file)
            
            # Vérifier que la dimension correspond toujours
            if len(embeddings) > 0 and len(embeddings[0]) != query_dimension:
                print(f"⚠️ Fichier {emb_file} ignoré: dimension {len(embeddings[0])} != {query_dimension}")
                continue
            
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
                # Vérification supplémentaire de la dimension
                if len(chunk_emb) != query_dimension:
                    continue
                    
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
        Générer uniquement le plan de traitement avec OpenAI ou Claude
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
            # Message système pour le PLAN DE TRAITEMENT
            system_message_treatment = (
                "Vous êtes un psychiatre clinicien expert du DSM-5-TR. "
                "Vous rédigez un plan de traitement détaillé et structuré en français pour le patient. "
                "Incluez : activités thérapeutiques (suivi thérapeutique), prise en charge médicale si nécessaire, "
                "recommandations psychothérapeutiques, et suivi à long terme. "
                "Basez-vous sur les recommandations officielles (HAS, OMS, sociétés savantes). "
                "Si une information manque pour établir un plan sûr, indiquez-le clairement."
            )
            
            # 🆕 Construire le prompt pour le plan de traitement directement
            treatment_prompt = self._build_treatment_prompt(
                pathology_name, 
                form_data, 
                "",  # Pas de diagnostic text, on génère directement le plan
                medical_text, 
                historical_symptoms
            )
            
            # 🆕 GÉNÉRER UNIQUEMENT LE PLAN DE TRAITEMENT
            print("🔄 Génération du plan de traitement...")
            
            # Appeler l'API selon le modèle sélectionné
            if self.model == 'chatgpt-5.1':
                # OpenAI / ChatGPT
                response = self.client.chat.completions.create(
                    model="gpt-5",
                    messages=[
                        {
                            "role": "system",
                            "content": system_message_treatment
                        },
                        {
                            "role": "user",
                            "content": treatment_prompt
                        }
                    ],
                    max_completion_tokens=1200  # R�duit pour des r�ponses plus rapides (Heroku timeout 30s)
                )
                # Debug: afficher la réponse complète
                print(f"🔍 DEBUG ChatGPT response type: {type(response)}")
                print(f"🔍 DEBUG ChatGPT response.choices: {response.choices if hasattr(response, 'choices') else 'N/A'}")
                if hasattr(response, 'choices') and response.choices:
                    print(f"🔍 DEBUG ChatGPT response.choices[0]: {response.choices[0]}")
                    if hasattr(response.choices[0], 'message'):
                        print(f"🔍 DEBUG ChatGPT response.choices[0].message: {response.choices[0].message}")
                        if hasattr(response.choices[0].message, 'content'):
                            print(f"🔍 DEBUG ChatGPT content type: {type(response.choices[0].message.content)}")
                            print(f"🔍 DEBUG ChatGPT content length: {len(response.choices[0].message.content) if response.choices[0].message.content else 0}")
                
                # Extraire le contenu de la réponse
                if response.choices and len(response.choices) > 0:
                    treatment_plan_text = response.choices[0].message.content
                    if not treatment_plan_text:
                        treatment_plan_text = ""
                        print(f"⚠️ Réponse ChatGPT vide - response.choices[0].message.content est None ou vide")
                        # Afficher plus de détails pour le débogage
                        print(f"🔍 DEBUG - response.choices[0].message: {response.choices[0].message}")
                        print(f"🔍 DEBUG - response.choices[0].finish_reason: {response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else 'N/A'}")
                else:
                    treatment_plan_text = ""
                    print(f"⚠️ Réponse ChatGPT sans choix - response.choices est vide")
                    print(f"🔍 DEBUG - response complet: {response}")
                
            elif self.model == 'claude-4.5':
                # Claude Sonnet 4.5 - utilisation directe (sans embeddings)
                try:
                    # Vérifier que la clé API est configurée
                    if not settings.CLAUDE_API_KEY:
                        raise ValueError("CLAUDE_API_KEY n'est pas configuré dans le fichier .env")
                    
                    print(f"🔍 Appel API Claude avec modèle: {self.claude_model}")
                    print(f"🔍 Clé API présente: {'Oui' if settings.CLAUDE_API_KEY else 'Non'}")
                    
                    response = self.client.messages.create(
                        model=self.claude_model,  # Claude Sonnet 4.5
                        max_tokens=1200,  # R�duit pour des r�ponses plus rapides (Heroku timeout 30s)
                        temperature=0.4,
                        system=system_message_treatment,
                        messages=[
                            {
                                "role": "user",
                                "content": treatment_prompt
                            }
                        ]
                    )
                    
                    print(f"✅ Réponse Claude reçue: type={type(response)}")
                    print(f"✅ Response.content: {response.content if hasattr(response, 'content') else 'N/A'}")
                    
                    # Claude retourne response.content qui est une liste de TextBlock
                    # Le premier bloc contient le texte (format: TextBlock avec attribut .text)
                    if hasattr(response, 'content') and response.content and len(response.content) > 0:
                        first_content = response.content[0]
                        
                        # Claude SDK retourne un objet TextBlock avec attribut .text
                        if hasattr(first_content, 'text'):
                            treatment_plan_text = first_content.text
                            print(f"✅ Plan de traitement extrait: {len(treatment_plan_text)} caractères")
                        else:
                            # Fallback si format différent
                            treatment_plan_text = str(first_content)
                            print(f"⚠️ Format inattendu, conversion en string: {len(treatment_plan_text)} caractères")
                    else:
                        error_msg = f"Réponse Claude vide - response.content: {getattr(response, 'content', 'N/A')}"
                        print(f"❌ {error_msg}")
                        raise ValueError(error_msg)
                    
                    if not treatment_plan_text or len(treatment_plan_text.strip()) == 0:
                        raise ValueError("Le plan de traitement généré par Claude est vide")
                    
                except Exception as claude_error:
                    # Afficher l'erreur détaillée pour le débogage
                    import traceback
                    error_detail = traceback.format_exc()
                    error_msg = f"Erreur API Claude: {str(claude_error)}"
                    print(f"❌ {error_msg}")
                    print(f"❌ Modèle utilisé: {self.claude_model}")
                    print(f"❌ Clé API configurée: {'Oui' if settings.CLAUDE_API_KEY else 'Non'}")
                    print(f"❌ Détails de l'erreur:\n{error_detail}")
                    raise RuntimeError(f"{error_msg}\n\nDétails: {error_detail}")
                
            else:
                raise ValueError(f"Modèle non supporté pour la génération: {self.model}")
            
            print(f"✅ Plan de traitement généré: {len(treatment_plan_text)} caractères")
            
            return {
                'success': True,
                'pathology': pathology_name,
                'diagnosis': '',  # Pas de diagnostic summary
                'treatment_plan': treatment_plan_text,  # Uniquement le plan de traitement
                'confidence': similarity_score,
                'timestamp': self._get_timestamp(),
                'model_used': self.model
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'pathology': pathology_name,
                'model_used': self.model
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
    
    def _generate_treatment_plan(self, pathology_name, form_data, diagnosis_text, medical_text="", historical_symptoms=None, system_message=None):
        """
        Générer un plan de traitement détaillé pour le patient.
        
        Args:
            pathology_name: Nom de la pathologie
            form_data: Données du formulaire
            diagnosis_text: Texte du diagnostic généré
            medical_text: Texte médical extrait
            historical_symptoms: Historique des symptômes
            system_message: Message système pour le plan de traitement
            
        Returns:
            str: Plan de traitement généré
        """
        try:
            # Construire le prompt pour le plan de traitement
            treatment_prompt = self._build_treatment_prompt(
                pathology_name, 
                form_data, 
                diagnosis_text, 
                medical_text, 
                historical_symptoms
            )
            
            # Générer le plan de traitement avec le même modèle
            if self.model == 'chatgpt-5.1':
                response = self.client.chat.completions.create(
                    model="gpt-5",
                    messages=[
                        {
                            "role": "system",
                            "content": system_message
                        },
                        {
                            "role": "user",
                            "content": treatment_prompt
                        }
                    ],
                    max_completion_tokens=1200  # R�duit pour des r�ponses plus rapides (Heroku timeout 30s)
                )
                # Debug: afficher la réponse complète
                print(f"🔍 DEBUG ChatGPT response type: {type(response)}")
                print(f"🔍 DEBUG ChatGPT response.choices: {response.choices if hasattr(response, 'choices') else 'N/A'}")
                if hasattr(response, 'choices') and response.choices:
                    print(f"🔍 DEBUG ChatGPT response.choices[0]: {response.choices[0]}")
                    if hasattr(response.choices[0], 'message'):
                        print(f"🔍 DEBUG ChatGPT response.choices[0].message: {response.choices[0].message}")
                        if hasattr(response.choices[0].message, 'content'):
                            print(f"🔍 DEBUG ChatGPT content type: {type(response.choices[0].message.content)}")
                            print(f"🔍 DEBUG ChatGPT content length: {len(response.choices[0].message.content) if response.choices[0].message.content else 0}")
                
                # Extraire le contenu de la réponse
                if response.choices and len(response.choices) > 0:
                    treatment_plan_text = response.choices[0].message.content
                    if not treatment_plan_text:
                        treatment_plan_text = ""
                        print(f"⚠️ Réponse ChatGPT vide - response.choices[0].message.content est None ou vide")
                        # Afficher plus de détails pour le débogage
                        print(f"🔍 DEBUG - response.choices[0].message: {response.choices[0].message}")
                        print(f"🔍 DEBUG - response.choices[0].finish_reason: {response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else 'N/A'}")
                else:
                    treatment_plan_text = ""
                    print(f"⚠️ Réponse ChatGPT sans choix - response.choices est vide")
                    print(f"🔍 DEBUG - response complet: {response}")
                
            elif self.model == 'claude-4.5':
                response = self.client.messages.create(
                    model=self.claude_model,
                    max_tokens=1200,  # R�duit pour des r�ponses plus rapides (Heroku timeout 30s)
                    temperature=0.4,
                    system=system_message,
                    messages=[
                        {
                            "role": "user",
                            "content": treatment_prompt
                        }
                    ]
                )
                if hasattr(response, 'content') and response.content and len(response.content) > 0:
                    treatment_plan_text = response.content[0].text
                else:
                    raise ValueError("Réponse Claude vide pour le plan de traitement")
            else:
                raise ValueError(f"Modèle non supporté pour le plan de traitement: {self.model}")
            
            print(f"✅ Plan de traitement généré: {len(treatment_plan_text)} caractères")
            return treatment_plan_text
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la génération du plan de traitement: {str(e)}")
            return f"Erreur lors de la génération du plan de traitement: {str(e)}"
    
    def _build_treatment_prompt(self, pathology_name, form_data, diagnosis_text="", medical_text="", historical_symptoms=None):
        """
        Construire le prompt pour générer le plan de traitement.
        """
        prompt = f"""Génère un PLAN DE TRAITEMENT détaillé et structuré en français pour un patient.

INFORMATIONS DU PATIENT :
• Pathologie identifiée : {pathology_name}

TEXTE MÉDICAL DE RÉFÉRENCE :
{medical_text if medical_text else "Aucun extrait supplémentaire."}

CRITÈRES VALIDÉS :
"""
        
        # Ajouter les données du formulaire
        if isinstance(form_data, dict):
            for key, value in form_data.items():
                if key != '_metadata' and value:  # Exclure les métadonnées
                    if isinstance(value, list):
                        prompt += f"\n**{key}:**\n"
                        for item in value:
                            prompt += f"  ✓ {item}\n"
                    else:
                        prompt += f"\n**{key}:** {value}\n"
        
        # Ajouter l'historique si disponible
        if historical_symptoms and len(historical_symptoms) > 0:
            prompt += f"\n📋 **ANTÉCÉDENTS MÉDICAUX ({len(historical_symptoms)} symptômes enregistrés):**\n"
            for symptom in historical_symptoms[:10]:  # Limiter à 10
                prompt += f"  • {symptom}\n"
        
        prompt += """

STRUCTURE ATTENDUE DU PLAN DE TRAITEMENT :

## 1. Suivi Thérapeutique (Activités Thérapeutiques)
- Indiquer le type de suivi recommandé (fréquence, durée)
- Modalités de suivi (consultations, téléconsultations, etc.)

## 2. Prise en Charge Médicale (si nécessaire)
- Recommandations médicales générales
- Suivi des comorbidités physiques si présentes

## 3. Interventions Psychothérapeutiques
- Type de psychothérapie recommandée
- Objectifs thérapeutiques
- Durée et fréquence

## 4. Suivi à Long Terme
- Planification du suivi sur plusieurs mois
- Points de vigilance
- Critères d'amélioration attendus

IMPORTANT : 
- Base-toi uniquement sur les informations fournies
- Utilise un langage médical professionnel
- Inclus le suivi thérapeutique (activités thérapeutiques) comme demandé
- Sois précis mais adapté au cas du patient
- NE PAS ajouter de phrases de conclusion, de disclaimer ou de note sur l'ajustement du plan
- Terminer directement après la section 4 sans phrase de clôture
"""
        
        return prompt
    
    def _get_timestamp(self):
        """Obtenir le timestamp actuel."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

