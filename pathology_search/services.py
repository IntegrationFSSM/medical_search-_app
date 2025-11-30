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
    
    def __init__(self, model='chatgpt-5.1', embedding_model_type='openai-ada'):
        """
        Initialiser le service avec le modèle spécifié.
        
        Args:
            model: Modèle de génération de texte ('chatgpt-5.1', 'claude-4.5')
            embedding_model_type: Modèle d'embedding ('openai-ada', 'openai-3-large', 'gemini')
        """
        self.model = model
        self.embedding_model_type = embedding_model_type
        
        # Définir le dossier d'embeddings selon le modèle choisi
        if embedding_model_type == 'openai-3-large':
            self.embeddings_folder = settings.BASE_DIR / 'Embedding_OpenAI_3072'
            self.embedding_model_name = 'text-embedding-3-large'
            self.embedding_dim = 3072
        elif embedding_model_type == 'gemini':
            self.embeddings_folder = settings.BASE_DIR / 'Embedding_Gemini_3072'
            self.embedding_model_name = 'models/gemini-embedding-001' # Ou text-embedding-004 selon dispo
            self.embedding_dim = 3072
            
            # Configurer Gemini pour les embeddings si nécessaire
            import google.generativeai as genai
            if not settings.GEMINI_API_KEY:
                print("⚠️ Clé API Gemini manquante dans les settings")
            else:
                genai.configure(api_key=settings.GEMINI_API_KEY)
        else:
            # Par défaut: OpenAI ada-002
            self.embeddings_folder = settings.EMBEDDINGS_FOLDER
            self.embedding_model_name = settings.EMBEDDING_MODEL
            self.embedding_dim = 1536
            
        # Ne pas afficher les logs d'embeddings si on ne fait que générer (pas de recherche)
        # Les logs seront affichés uniquement lors de l'utilisation de find_best_match
        # print(f"📂 Dossier embeddings utilisé: {self.embeddings_folder}")
        # print(f"🧠 Modèle embedding: {self.embedding_model_type} ({self.embedding_model_name})")
        
        # Initialiser le client OpenAI (toujours nécessaire pour certaines fonctions ou fallback)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialiser le client Claude si nécessaire
        if model == 'claude-4.5':
            try:
                from anthropic import Anthropic
                if not settings.CLAUDE_API_KEY:
                    raise ValueError("La clé API Claude n'est pas configurée dans les variables d'environnement (.env)")
                
                self.claude_client = Anthropic(api_key=settings.CLAUDE_API_KEY)
                self.claude_model = getattr(settings, 'CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')
                print(f"✅ Client Claude initialisé avec modèle: {self.claude_model}")
            except ImportError:
                raise ImportError("La bibliothèque 'anthropic' n'est pas installée. Installez-la avec: pip install anthropic")
        
        # 🆕 Gemini supprimé pour la génération - seulement Model 1 (ChatGPT) et Model 2 (Claude) sont disponibles

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
            'drogue', 'cannabis', 'cocaïne', 'héroïne', 'opiacés',
            'anxiété', 'anxieux', 'peur', 'panique', 'stress', 'phobie',
            'dépression', 'déprimé', 'triste', 'suicide', 'humeur',
            'bipolaire', 'manie', 'maniaque',
            'schizophrénie', 'psychose', 'hallucination', 'délire',
            'trouble', 'syndrome', 'maladie', 'pathologie', 'symptôme',
            'douleur', 'fatigue', 'insomnie', 'sommeil',
            'manger', 'appétit', 'poids', 'boulimie', 'anorexie',
            'mémoire', 'concentration', 'attention', 'hyperactif', 'tdah',
            'toc', 'obsession', 'compulsion',
            'trauma', 'ptsd', 'stress post-traumatique',
            'personnalité', 'bordeline', 'limite', 'antisocial',
            'sexuel', 'sexuelle', 'libido', 'érection', 'éjaculation',
            'enfant', 'adolescent', 'adulte', 'femme', 'homme',
            'patient', 'patiente', 'sujet', 'cas',
            'diagnostic', 'traitement', 'médicament', 'thérapie'
        ]
        
        # Si la requête est très courte et contient un mot clé, on accepte
        if len(query.split()) < 5 and any(keyword in query_lower for keyword in medical_keywords):
            return {'is_valid': True, 'reason': 'Terme médical détecté'}

        try:
            # Utiliser un client OpenAI dédié pour la validation (indépendant du modèle choisi pour le reste)
            validation_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = f"""Tu es un validateur médical EXPERT. Analyse la requête suivante et détermine si elle contient un réel contenu médical.

Requête: "{query}"

RÈGLE PRINCIPALE: SOIS TRÈS PERMISSIF ! Accepte TOUTE description qui mentionne un problème de santé, un comportement, un symptôme ou une condition médicale, même de manière simple ou informelle.

ACCEPTE (is_valid = true) si la requête:
- Mentionne des symptômes, troubles, comportements ou conditions médicales (même vagues)
- Décrit un état psychologique ou physique problématique
- Raconte une histoire de patient ou un cas clinique
- Pose une question sur une maladie ou un traitement
- Contient des mots-clés médicaux ou psychologiques

REFUSE (is_valid = false) UNIQUEMENT si la requête est:
- Totalement incohérente ou vide de sens (gibberish)
- Clairement du spam ou du contenu malveillant
- Une demande de code informatique, de recette de cuisine, ou autre sujet 100% non médical
- Une simple salutation sans suite ("bonjour", "salut")

Réponds UNIQUEMENT au format JSON:
{{
    "is_valid": true/false,
    "reason": "Explication très brève (1 phrase)"
}}
"""

            response = validation_client.chat.completions.create(
                model="gpt-4o",  # Utiliser un modèle rapide et performant pour la validation
                messages=[
                    {"role": "system", "content": "Tu es un assistant de validation strict qui répond uniquement en JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            
            # Essayer de trouver un JSON dans le texte
            import re
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
            print(f"⚠️ Erreur de décodage JSON lors de la validation: {e}")
            # En cas d'erreur de parsing, on est permissif
            return {'is_valid': True, 'reason': 'Validation technique échouée (fallback)'}
        except Exception as e:
            print(f"⚠️ Erreur lors de la validation médicale: {e}")
            # En cas d'erreur API, on est permissif pour ne pas bloquer l'utilisateur
            return {'is_valid': True, 'reason': 'Erreur de validation (fallback)'}
    
    def get_embedding(self, text):
        """
        Obtenir l'embedding d'un texte via l'API du modèle sélectionné.
        
        Args:
            text: Texte à convertir en embedding
            
        Returns:
            np.array: Vecteur d'embedding
        """
        text = text.replace("\n", " ")
        
        try:
            if self.embedding_model_type == 'gemini':
                import google.generativeai as genai
                # Gemini Embedding
                result = genai.embed_content(
                    model=self.embedding_model_name,
                    content=text,
                    task_type="retrieval_query"
                )
                return np.array(result['embedding'])
                
            elif self.embedding_model_type == 'openai-3-large':
                # OpenAI text-embedding-3-large
                print(f"🔍 DEBUG - Génération embedding avec text-embedding-3-large")
                response = self.client.embeddings.create(
                    input=[text], 
                    model=self.embedding_model_name
                )
                embedding = np.array(response.data[0].embedding)
                print(f"✅ Embedding généré - Dimension: {len(embedding)} (attendu: {self.embedding_dim})")
                return embedding
                
            else:
                # OpenAI text-embedding-ada-002 (Défaut)
                print(f"🔍 DEBUG - Génération embedding avec {self.embedding_model_name}")
                response = self.client.embeddings.create(
                    input=[text], 
                    model=self.embedding_model_name
                )
                embedding = np.array(response.data[0].embedding)
                print(f"✅ Embedding généré - Dimension: {len(embedding)} (attendu: {self.embedding_dim})")
                return embedding
                
        except Exception as e:
            print(f"❌ Erreur génération embedding ({self.embedding_model_type}): {str(e)}")
            raise
    
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
        
        # Afficher les informations d'embedding uniquement lors de la recherche
        print(f"📂 Dossier embeddings utilisé: {self.embeddings_folder}")
        print(f"🧠 Modèle embedding: {self.embedding_model_type} ({self.embedding_model_name})")
        
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
        
        # Obtenir l'embedding de la requête avec le modèle sélectionné
        query_embedding = self.get_embedding(query)
        query_dimension = len(query_embedding)
        
        print(f"🔍 DEBUG - Modèle embedding sélectionné: {self.embedding_model_type}")
        print(f"🔍 DEBUG - Dimension embedding requête: {query_dimension}")
        print(f"🔍 DEBUG - Dimension attendue: {self.embedding_dim}")
        
        # Vérifier la dimension des embeddings stockés (prendre le premier fichier comme référence)
        stored_dimension = None
        if len(npy_files) > 0:
            sample_embeddings = np.load(npy_files[0])
            if len(sample_embeddings) > 0:
                stored_dimension = len(sample_embeddings[0])
                print(f"🔍 DEBUG - Dimension embeddings stockés: {stored_dimension}")
        
        # 🆕 Si les dimensions ne correspondent pas, c'est un problème critique
        # Ne PAS utiliser de fallback automatique - cela masque le problème
        if stored_dimension and query_dimension != stored_dimension:
            print(f"❌ ERREUR CRITIQUE: Dimension incompatible!")
            print(f"   - Modèle sélectionné: {self.embedding_model_type} ({self.embedding_model_name})")
            print(f"   - Dimension requête: {query_dimension}")
            print(f"   - Dimension stockée: {stored_dimension}")
            print(f"   - Dimension attendue: {self.embedding_dim}")
            print(f"⚠️ Le modèle d'embedding sélectionné ne correspond pas aux embeddings stockés!")
            print(f"⚠️ Vérifiez que le dossier {self.embeddings_folder} contient des embeddings générés avec {self.embedding_model_name}")
            
            # Retourner une erreur explicite au lieu d'un fallback silencieux
            return {
                'success': False,
                'error': f'Dimension incompatible: le modèle {self.embedding_model_type} génère des embeddings de {query_dimension} dimensions, mais les fichiers stockés ont {stored_dimension} dimensions. Vérifiez que les embeddings ont été générés avec le bon modèle.',
                'error_type': 'dimension_mismatch',
                'query_dimension': query_dimension,
                'stored_dimension': stored_dimension,
                'embedding_model': self.embedding_model_name,
                'results': []
            }
        
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
                
                # 🆕 Vérifier le modèle d'embedding utilisé pour générer ces embeddings (si disponible)
                # Les fichiers peuvent avoir 'embedding_model' ou 'model' comme clé
                embedding_model_used = metadata.get('embedding_model') or metadata.get('model', 'unknown')
                if embedding_model_used != 'unknown':
                    # Vérifier si le modèle correspond au modèle sélectionné
                    expected_model = self.embedding_model_name
                    if embedding_model_used != expected_model:
                        print(f"⚠️ ATTENTION - Fichier {Path(emb_file).name}: embeddings générés avec '{embedding_model_used}' mais modèle sélectionné est '{expected_model}'")
                    else:
                        print(f"✅ Fichier {Path(emb_file).name}: embeddings générés avec {embedding_model_used} (correspond au modèle sélectionné)")
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
                    # 🆕 Vérifier que 'chunks' existe dans les métadonnées
                    chunks = metadata.get('chunks', [])
                    if i < len(chunks) and isinstance(chunks[i], dict):
                        best_chunk_text = chunks[i].get('text_preview', '')
                    else:
                        best_chunk_text = ''
            
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
            
            # 🆕 Gérer le cas où 'hierarchy' n'existe pas dans les métadonnées
            hierarchy = metadata.get('hierarchy', {})
            location = None
            
            # Essayer de récupérer le location depuis hierarchy
            if isinstance(hierarchy, dict) and 'location' in hierarchy:
                location = hierarchy.get('location')
            
            # Si location n'est pas disponible, le construire à partir du chemin du fichier
            if not location or location == 'N/A':
                try:
                    # Obtenir le chemin relatif du fichier JSON par rapport au dossier embeddings
                    emb_file_path = Path(emb_file)
                    embeddings_folder_path = Path(self.embeddings_folder)
                    
                    # Calculer le chemin relatif
                    try:
                        relative_path = emb_file_path.relative_to(embeddings_folder_path)
                    except ValueError:
                        # Si le fichier n'est pas dans le dossier embeddings, utiliser le nom du fichier
                        relative_path = emb_file_path.name
                    
                    # Construire le location à partir du chemin relatif
                    # Exemple: "Anxiety_Disorders_out/SubSection1_Separation_Anxiety_Disorder.json" 
                    # -> "Anxiety_Disorders_out > SubSection1_Separation_Anxiety_Disorder"
                    path_parts = relative_path.parts[:-1]  # Exclure le nom du fichier
                    file_stem = relative_path.stem  # Nom sans extension
                    
                    if path_parts:
                        location = ' > '.join(path_parts) + ' > ' + file_stem
                    else:
                        location = file_stem
                except Exception as e:
                    # En dernier recours, utiliser le nom du fichier
                    location = Path(metadata.get('source_file', emb_file)).stem
            
            file_results[str(emb_file)] = {
                'file': metadata['source_file'],
                'file_name': Path(metadata['source_file']).name,
                'location': location,
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
        
        # 🆕 Afficher directement les résultats sans seuil minimum
        # Ajouter des informations diagnostiques
        diagnostic_info = self._generate_diagnostic_info(results) if results else {
            'suspected_pathology': None,
            'confidence': 0,
            'confidence_level': 'none',
            'message': 'Aucun résultat trouvé'
        }
        
        return {
            'success': True,
            'results': results if results else [],
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
        Générer uniquement le plan de traitement avec OpenAI (Model 1) ou Claude (Model 2)
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
            print(f"🔍 DEBUG - Longueur du prompt: {len(treatment_prompt)} caractères")
            print(f"🔍 DEBUG - Longueur du medical_text: {len(medical_text) if medical_text else 0} caractères")
            print(f"🔍 DEBUG - Nombre de historical_symptoms: {len(historical_symptoms) if historical_symptoms else 0}")
            
            treatment_plan_text = ""
            
            # Appeler l'API selon le modèle sélectionné
            if self.model == 'chatgpt-5.1':
                # OpenAI / ChatGPT
                response = self.client.chat.completions.create(
                    model="gpt-4o",
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
                    max_completion_tokens=2000  # Limité pour éviter les timeouts Heroku (30s) avec GPT-4oduit pour des rponses plus rapides (Heroku timeout 30s)
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
                    
                    response = self.claude_client.messages.create(
                        model=self.claude_model,  # Claude Sonnet 4.5
                        max_tokens=1200,  # Réduit pour éviter timeout Heroku (30s) - Claude prend ~30s avec 2000 tokens
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
            
            if not treatment_plan_text:
                raise ValueError("Le plan de traitement généré est vide")
            
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
        
        # Charger le fichier complet de la pathologie depuis le dossier disorders
        complete_pathology_text = self._load_complete_pathology_file(pathology_name)
        
        prompt = f"""Élabore un RÉSUMÉ DIAGNOSTIQUE (sans plan thérapeutique) pour un patient évalué selon le DSM-5-TR.

Consignes obligatoires :
- Baser l'analyse UNIQUEMENT sur les critères cochés ci-dessous et sur l'extrait médical fourni.
- Ne jamais prescrire ni décrire un traitement médicamenteux ou une posologie.
- Utiliser un ton clinique, structuré et concis en français.

Informations de référence :
• Pathologie suspectée : {pathology_name}
• Niveau de correspondance : {similarity_score:.1f}%

DOCUMENTATION COMPLÈTE DE LA PATHOLOGIE (DSM-5-TR) :
{complete_pathology_text if complete_pathology_text else "Documentation complète non disponible."}

Extrait DSM-5-TR disponible (extrait de recherche) :
{medical_text if medical_text else "Aucun extrait supplémentaire. S'appuyer uniquement sur les critères cochés et la documentation complète ci-dessus."}

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
                    model="gpt-4o",
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
                    max_completion_tokens=2000  # Limité pour éviter les timeouts Heroku (30s) avec GPT-4o�duit pour des r�ponses plus rapides (Heroku timeout 30s)
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
        # Charger le fichier complet de la pathologie depuis le dossier disorders
        complete_pathology_text = self._load_complete_pathology_file(pathology_name)
        
        prompt = f"""Génère un PLAN DE TRAITEMENT détaillé et structuré en français pour un patient.

INFORMATIONS DU PATIENT :
• Pathologie identifiée : {pathology_name}

DOCUMENTATION COMPLÈTE DE LA PATHOLOGIE (DSM-5-TR) :
{complete_pathology_text if complete_pathology_text else "Documentation complète non disponible."}

TEXTE MÉDICAL DE RÉFÉRENCE (extrait de recherche) :
{medical_text[:1000] + "..." if medical_text and len(medical_text) > 1000 else (medical_text if medical_text else "Aucun extrait supplémentaire.")}

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
        
        # Ajouter l'historique si disponible (limiter pour éviter les prompts trop longs - réduit à 3 pour GPT-5)
        if historical_symptoms and len(historical_symptoms) > 0:
            # Limiter à 3 symptômes les plus récents pour éviter les prompts trop longs avec GPT-5
            limited_symptoms = historical_symptoms[:3]
            prompt += f"\n📋 **ANTÉCÉDENTS MÉDICAUX (3 symptômes les plus récents sur {len(historical_symptoms)}):**\n"
            for symptom in limited_symptoms:
                # Limiter la longueur de chaque symptôme à 50 caractères pour GPT-5
                symptom_short = symptom[:50] + "..." if len(symptom) > 50 else symptom
                prompt += f"  • {symptom_short}\n"
        
        prompt += """

STRUCTURE ATTENDUE DU PLAN DE TRAITEMENT :

## 1. Traitements Médicamenteux
- **OBLIGATOIRE** : Inclure TOUS les médicaments recommandés pour cette pathologie selon la documentation DSM-5-TR
- Pour chaque médicament : nom générique, indications, posologie recommandée (doses de départ et d'entretien)
- Durée du traitement médicamenteux
- Précautions et contre-indications importantes
- Interactions médicamenteuses à surveiller

## 2. Interventions Psychothérapeutiques
- Type de psychothérapie recommandée (CBT, TCC, thérapie d'exposition, etc.)
- Objectifs thérapeutiques spécifiques
- Durée et fréquence des séances
- Techniques thérapeutiques à utiliser

## 3. Suivi Thérapeutique (Activités Thérapeutiques)
- Indiquer le type de suivi recommandé (fréquence, durée)
- Modalités de suivi (consultations, téléconsultations, etc.)
- Points de contrôle et évaluations périodiques

## 4. Prise en Charge Médicale (si nécessaire)
- Recommandations médicales générales
- Suivi des comorbidités physiques si présentes
- Examens complémentaires nécessaires

## 5. Suivi à Long Terme
- Planification du suivi sur plusieurs mois
- Points de vigilance
- Critères d'amélioration attendus
- Stratégies de prévention des rechutes

IMPORTANT : 
- **OBLIGATOIRE** : Base-toi sur la DOCUMENTATION COMPLÈTE DE LA PATHOLOGIE fournie ci-dessus
- **OBLIGATOIRE** : Inclure TOUS les médicaments et traitements mentionnés dans la documentation DSM-5-TR
- Utilise un langage médical professionnel
- Sois précis et détaillé pour les médicaments (noms, posologies, durées)
- Sois précis mais adapté au cas du patient
- NE PAS ajouter de phrases de conclusion, de disclaimer ou de note sur l'ajustement du plan
- Terminer directement après la section 5 sans phrase de clôture
"""
        
        return prompt
    
    def _get_timestamp(self):
        """Obtenir le timestamp actuel."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _load_complete_pathology_file(self, pathology_name):
        """
        Charger le fichier .txt complet depuis le dossier disorders.
        
        Args:
            pathology_name: Nom de la pathologie (ex: "Agoraphobia", "Separation Anxiety Disorder")
            
        Returns:
            str: Contenu complet du fichier .txt, ou chaîne vide si non trouvé
        """
        try:
            disorders_folder = settings.BASE_DIR / 'disorders'
            
            if not disorders_folder.exists():
                print(f"⚠️ Dossier disorders non trouvé: {disorders_folder}")
                return ""
            
            # Nettoyer le nom de la pathologie pour la recherche
            # Convertir en format de nom de fichier (ex: "Agoraphobia" -> "SubSection*_Agoraphobia.txt")
            pathology_clean = pathology_name.strip()
            
            # Chercher dans tous les sous-dossiers
            for txt_file in disorders_folder.rglob('*.txt'):
                file_name = txt_file.stem  # Nom sans extension
                
                # Vérifier si le nom du fichier contient le nom de la pathologie
                # ou si le nom de la pathologie correspond au début du fichier
                if pathology_clean.lower() in file_name.lower() or file_name.lower().endswith(pathology_clean.lower().replace(' ', '_')):
                    # Lire le contenu complet
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"✅ Fichier pathologie complet chargé: {txt_file.name} ({len(content)} caractères)")
                    return content
                
                # Vérifier aussi le contenu du fichier (première ligne contient souvent le nom)
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if pathology_clean.lower() in first_line.lower():
                            # Relire tout le fichier
                            with open(txt_file, 'r', encoding='utf-8') as f2:
                                content = f2.read()
                            print(f"✅ Fichier pathologie complet chargé (par première ligne): {txt_file.name} ({len(content)} caractères)")
                            return content
                except:
                    continue
            
            print(f"⚠️ Fichier pathologie non trouvé pour: {pathology_name}")
            return ""
            
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement du fichier pathologie: {e}")
            import traceback
            print(traceback.format_exc())
            return ""

