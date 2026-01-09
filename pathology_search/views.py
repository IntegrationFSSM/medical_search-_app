import json
import logging
import os
import re
import traceback
import urllib.parse
import uuid
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_http_methods

from openai import OpenAI
from weasyprint import HTML

from .models import Consultation, Medecin, Patient
from .services import PathologySearchService


def clean_pathology_name(text):
    if not text:
        return text
    text = str(text)
    
    # Enlever les crochets et guillemets
    text = text.strip('[]"\'')
    text = text.replace('["', '').replace('"]', '')
    text = text.replace("['", '').replace("']", '')
    
    # Enlever les emojis
    text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
    text = re.sub(r'[\u2600-\u26FF]', '', text)
    text = re.sub(r'[\u2700-\u27BF]', '', text)
    
    # Enlever les préfixes SubSection et Section avec leurs numéros
    text = re.sub(r'SubSection\s*\d+\.?\d*\s+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Section\s*\d+\.?\d*\s+', '', text, flags=re.IGNORECASE)
    
    # Enlever aussi les variantes avec tirets bas et points
    text = re.sub(r'SubSection\d+\.\d+[_\s]+', '', text)
    text = re.sub(r'Section\d+[_\s]+', '', text)
    
    # Enlever les "Section :" et "Sous-section :" en français
    text = re.sub(r'Section\s+\d+\s*:\s*', '', text)
    text = re.sub(r'Sous-section\s+[\d.]+\s*:\s*', '', text)
    
    # Remplacer les underscores par des espaces
    text = text.replace('_', ' ')
    
    return text.strip()


def clean_text_for_pdf(text):
    if not text:
        return text
    text = str(text)
    # Enlever les crochets et guillemets
    text = text.strip('[]"\'')
    text = text.replace('["', '').replace('"]', '')
    text = text.replace("['", '').replace("']", '')
    # Enlever les emojis
    text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
    text = re.sub(r'[\u2600-\u26FF]', '', text)
    text = re.sub(r'[\u2700-\u27BF]', '', text)
    return text.strip()


def format_plan_traitement_html(text):
    if not text:
        return text
    text = str(text)
    
    # Enlever les emojis
    text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
    text = re.sub(r'[\u2600-\u26FF]', '', text)
    text = re.sub(r'[\u2700-\u27BF]', '', text)
    
    # Convertir les titres markdown en HTML avec styles (non-gourmand pour éviter ReDoS)
    text = re.sub(r'^# (.+?)$', r'<div class="plan-h1">\1</div>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+?)$', r'<div class="plan-h2">\1</div>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+?)$', r'<div class="plan-h3">\1</div>', text, flags=re.MULTILINE)
    
    # Convertir le gras **texte** en <strong> (déjà sécurisé avec [^\*]+)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', text)
    
    # Convertir les listes à puces (non-gourmand pour éviter ReDoS)
    text = re.sub(r'^\- (.+?)$', r'<div class="plan-bullet">• \1</div>', text, flags=re.MULTILINE)
    text = re.sub(r'^\* (.+?)$', r'<div class="plan-bullet">• \1</div>', text, flags=re.MULTILINE)
    
    # Convertir les numéros de liste (non-gourmand pour éviter ReDoS)
    text = re.sub(r'^\d+\.\s+(.+?)$', r'<div class="plan-number">\1</div>', text, flags=re.MULTILINE)
    
    # Convertir les sauts de ligne en <br>
    text = text.replace('\n\n', '<br><br>')
    text = text.replace('\n', '<br>')
    
    return text


def index(request):
    return render(request, 'pathology_search/index.html')


@require_http_methods(["POST"])
def search(request):
    try:
       
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        top_k = int(data.get('top_k', 5))
        aggregation = data.get('aggregation', 'max')
        use_validation = data.get('use_validation', False)  
        patient_id = data.get('patient_id') 
        medecin_id = data.get('medecin_id') 
        historical_symptoms = data.get('historical_symptoms', [])  
        
        embedding_model = data.get('embedding_model', 'openai-ada')  
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'La requête ne peut pas être vide'
            }, status=400)
        
        
        if patient_id:
            request.session['current_patient_id'] = patient_id
        if medecin_id:
            request.session['current_medecin_id'] = medecin_id
        
        
        def clean_and_validate_symptom(symptom_text):
            if not symptom_text:
                return None
            
            symptom_text = str(symptom_text).strip()
            
            if len(symptom_text) < 2:
                return None
            
            
            if not re.search(r'[a-zA-ZÀ-ÿ]', symptom_text):
                return None
            
            
            words = symptom_text.split()
            if len(words) > 1 and len(set(words)) == 1:
                return None
            
            
            if symptom_text.lower().startswith('_metadata') or symptom_text.lower() == '_metadata':
                return None
            
            return symptom_text
        
        all_historical_symptoms = []
        
        request.session.modified = True
        enriched_query = query
        validation_client = OpenAI(api_key=settings.OPENAI_API_KEY)
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
        
        # Validation préalable simple
        if len(query.split()) < 5 and any(keyword in query_lower for keyword in medical_keywords):
            validation_result = {'is_valid': True, 'reason': 'Terme médical détecté'}
        else:
            # Validation avec GPT-4o
            try:
                # json et re sont déjà importés au niveau du module, pas besoin de les réimporter
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
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Tu es un assistant de validation strict qui répond uniquement en JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                
                result_text = response.choices[0].message.content
                json_match = re.search(r'\{[^}]*"is_valid"[^}]*\}', result_text)
                if json_match:
                    result_text = json_match.group(0)
                
                result = json.loads(result_text)
                validation_result = {
                    'is_valid': result.get('is_valid', False),
                    'reason': result.get('reason', 'Requête invalide')
                }
            except Exception as e:
                validation_result = {'is_valid': True, 'reason': 'Erreur de validation (fallback)'}
        
        if not validation_result['is_valid']:
            return JsonResponse({
                'success': False,
                'error': 'Requête non valide',
                'error_type': 'invalid_query',
                'reason': validation_result['reason']
            })
    
        service = PathologySearchService(model='chatgpt-5.1', embedding_model_type=embedding_model)
        search_results = service.find_best_match(
            query=enriched_query,  # Utiliser la requête originale (sans antécédents)
            top_k=top_k,
            aggregation=aggregation
        )
        
        if search_results.get('success') and search_results.get('results'):
            for result in search_results['results']:
                similarity = result.get('similarity', 0)
                result['similarity_percent'] = round(similarity * 100, 1)
        
        
        if use_validation and search_results.get('success'):
            request.session['search_results'] = search_results['results']
            request.session['search_query'] = query
            
            request.session['visited_diagnostic_indices'] = []
            request.session.modified = True
            return JsonResponse({
                'success': True,
                'use_validation': True,
                'redirect_url': '/results-selection/'
            })
        
        return JsonResponse(search_results)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la recherche: {str(e)}'
        }, status=500)


def results_selection(request):
    results = request.session.get('search_results', [])
    query = request.session.get('search_query', '')
    
    if not results:
        return render(request, 'pathology_search/index.html', {
            'error': 'Aucun résultat trouvé. Veuillez effectuer une nouvelle recherche.'
        })
    

    visited_indices = set(request.session.get('visited_diagnostic_indices', []))

    prepared_results = []
    for i, result in enumerate(results):
        if i in visited_indices:
            continue
            
        pathology_name = clean_pathology_name(result.get('file_name', '').replace('.txt', ''))
        similarity = result.get('similarity', 0)
        similarity_percent = round(similarity * 100, 1)
        
        prepared_results.append({
            'index': i,
            'pathology_name': pathology_name,
            'location': result.get('location', ''),
            'similarity': similarity,
            'similarity_percent': similarity_percent,
            'html_page': result.get('html_page', '')
        })
    
    if len(visited_indices) >= len(results):
        return render(request, 'pathology_search/index.html', {
            'message': 'Tous les diagnostics ont été évalués. Retour à la page principale.'
        })
    
    context = {
        'results': prepared_results,
        'results_json': json.dumps(prepared_results),
        'query': query,
        'total_visited': len(visited_indices),
        'total_results': len(results)
    }
    
    return render(request, 'pathology_search/results_selection.html', context)


def create_patient_page(request):

    return render(request, 'pathology_search/create_patient.html')


def _generate_patient_identifier():
    """Generate unique patient identifier."""
    last_patient = Patient.objects.order_by('-id').first()
    if last_patient and last_patient.patient_identifier and last_patient.patient_identifier.startswith('EE-2025-'):
        try:
            last_num = int(last_patient.patient_identifier.split('-')[-1])
            return f'EE-2025-{last_num + 1:03d}'
        except (ValueError, IndexError):
            pass
    return 'EE-2025-001'


def _parse_birth_date(date_str):
    """Parse birth date string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _extract_patient_data(data):
    """Extract and prepare patient data from request."""
    birth_date = _parse_birth_date(data.get('birth_date'))
    has_insurance = data.get('has_insurance') in (True, 'true')
    
    return {
        'patient_identifier': data.get('patient_identifier', '').strip() or _generate_patient_identifier(),
        'cin': data.get('cin', '').strip() or None,
        'passport_number': data.get('passport_number', '').strip() or None,
        'last_name': data.get('last_name', '').strip().upper() or None,
        'first_name': data.get('first_name', '').strip().capitalize() or None,
        'gender': data.get('gender', '') or None,
        'birth_date': birth_date,
        'nationality': data.get('nationality', 'MA').strip() or 'MA',
        'profession': data.get('profession', '').strip() or '',
        'city': data.get('city', '').strip() or '',
        'email': data.get('email', '').strip() or '',
        'phone': data.get('phone', '').strip() or '',
        'mobile_number': data.get('mobile_number', '').strip() or '',
        'spouse_name': data.get('spouse_name', '').strip() or '',
        'treating_physician': data.get('treating_physician', '').strip() or None,
        'referring_physician': data.get('referring_physician', '').strip() or None,
        'disease_speciality': data.get('disease_speciality', '').strip() or None,
        'has_insurance': has_insurance,
        'insurance_number': data.get('insurance_number', '').strip() or None,
        'affiliation_number': data.get('affiliation_number', '').strip() or None,
        'nom': data.get('last_name', '').strip().upper() or None,
        'prenom': data.get('first_name', '').strip().capitalize() or None,
        'date_naissance': birth_date,
        'numero_dossier': data.get('patient_identifier', '').strip() or _generate_patient_identifier(),
        'telephone': data.get('mobile_number', '').strip() or data.get('phone', '').strip() or ''
    }


@require_http_methods(["POST"])
def create_patient_submit(request):
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST.dict()
        
        patient_data = _extract_patient_data(data)
        patient_identifier = patient_data['patient_identifier']
        
        if Patient.objects.filter(patient_identifier=patient_identifier).exists():
            return JsonResponse({
                'success': False,
                'error': f'L\'identifiant patient {patient_identifier} existe déjà'
            }, status=400)
        
        patient = Patient.objects.create(**patient_data)
        
        return JsonResponse({
            'success': True,
            'patient': {
                'id': patient.id,
                'patient_identifier': patient.patient_identifier,
                'last_name': patient.last_name,
                'first_name': patient.first_name,
                'nom_complet': patient.nom_complet,
                'cin': patient.cin,
                'passport_number': patient.passport_number
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la création du patient: {str(e)}',
            'detail': traceback.format_exc()
        }, status=500)


def print_report(request, consultation_id):
    try:
        
        
        logger = logging.getLogger(__name__)
        
        consultation = Consultation.objects.select_related('patient', 'medecin').get(id=consultation_id)
        
        logger.info(f"Generating PDF for consultation {consultation_id}")
        
        if not consultation.criteres_valides:
            consultation.criteres_valides = {}
        
        model_used = 'chatgpt-5.1'  # Par défaut
        model_display_name = 'Model 1'
        if consultation.criteres_valides and '_metadata' in consultation.criteres_valides:
            metadata = consultation.criteres_valides['_metadata']
            model_used = metadata.get('model_used', 'chatgpt-5.1')
            # Convertir le nom du modèle pour l'affichage
            model_names = {
                'chatgpt-5.1': 'Model 1',
                'claude-4.5': 'Model 2'
            }
            model_display_name = model_names.get(model_used, metadata.get('model_display_name', 'Model 1'))
        
        plan_traitement_a_utiliser = consultation.plan_traitement_valide if consultation.plan_traitement_valide else consultation.plan_traitement
        
        plan_traitement_clean = format_plan_traitement_html(plan_traitement_a_utiliser)
        
        pathologie_clean = clean_pathology_name(consultation.pathologie_identifiee)
        
        criteres_valides_clean = {}
        for key, value in consultation.criteres_valides.items():
            if key == '_metadata':  # Exclure les métadonnées de l'affichage
                continue
            clean_key = clean_text_for_pdf(key)
            clean_value = clean_text_for_pdf(value)
            criteres_valides_clean[clean_key] = clean_value
        
        notes_medecin_clean = consultation.notes_medecin if consultation.notes_medecin else ''
        
        is_direct_access = consultation.description_clinique.startswith('Accès direct à la pathologie')
        
        context = {
            'consultation': consultation,
            'patient': consultation.patient,
            'medecin': consultation.medecin,
            'date_impression': timezone.now(),
            'plan_traitement_clean': plan_traitement_clean,
            'pathologie_clean': pathologie_clean,
            'notes_medecin': notes_medecin_clean,  # 🆕 Notes du médecin
            'criteres_valides_clean': criteres_valides_clean,
            'model_used': model_used,  # 🆕 Modèle utilisé
            'model_display_name': model_display_name,  # 🆕 Nom formaté pour affichage
            'is_direct_access': is_direct_access,  # 🆕 Flag pour masquer la description clinique
        }
        
        try:
            # Rendre le template HTML simplifié pour PDF
            html = render_to_string('pathology_search/print_report_pdf.html', context)
            logger.info("HTML template rendered successfully")
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            return HttpResponse(f'Erreur lors du rendu du template: {str(e)}', status=500)
        
        # Créer le PDF avec WeasyPrint
        try:
            
            
            # Générer le PDF
            pdf_file = HTML(string=html).write_pdf()
            
            response = HttpResponse(pdf_file, content_type='application/pdf')
            # Nettoyer le nom de fichier pour éviter les caractères spéciaux
            filename = f'rapport_{consultation.patient.nom}_{consultation.patient.prenom}_{consultation.patient.numero_dossier}.pdf'
            filename = filename.replace(' ', '_').replace("'", '')
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            logger.info("PDF generated successfully with WeasyPrint")
            return response
        except Exception as e:
            logger.error(f"Error creating PDF: {str(e)}")
            return HttpResponse(f'Erreur lors de la création du PDF: {str(e)}', status=500)
        
    except Consultation.DoesNotExist:
        return render(request, 'pathology_search/index.html', {
            'error': 'Consultation non trouvée.'
        })
    except Exception as e:
        
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in print_report: {str(e)}")
        return HttpResponse(f'Erreur inattendue: {str(e)}', status=500)


def patient_history(request, patient_id):

    try:
        
        
        patient = Patient.objects.get(id=patient_id)
        consultations = Consultation.objects.filter(patient=patient).order_by('-date_consultation')
        
        context = {
            'patient': patient,
            'consultations': consultations,
        }
        
        return render(request, 'pathology_search/patient_history.html', context)
        
    except Patient.DoesNotExist:
        return render(request, 'pathology_search/index.html', {
            'error': 'Patient non trouvé.'
        })


@require_http_methods(["GET"])
def get_patients(request):
    
    
    try:
        patients = Patient.objects.all()
        patients_data = [
            {
                'id': patient.id,
                'nom': patient.nom,
                'prenom': patient.prenom,
                'nom_complet': patient.nom_complet,
                'numero_dossier': patient.numero_dossier,
                'date_naissance': patient.date_naissance.isoformat() if patient.date_naissance else None,
                'telephone': patient.telephone,
                'email': patient.email
            }
            for patient in patients
        ]
        return JsonResponse({'success': True, 'patients': patients_data})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la récupération des patients: {str(e)}'
        }, status=500)


def get_patient_history(request, patient_id):
   
    
    
    try:
        patient = Patient.objects.get(id=patient_id)
        consultations = Consultation.objects.filter(patient=patient).select_related('medecin').order_by('-date_consultation')
        
        # Collecter TOUS les symptômes/critères de l'historique
        all_symptoms = []
        
        consultations_data = []
        for consultation in consultations:
            # Extraire les critères validés
            criteria_list = []
            if consultation.criteres_valides:
                for key, value in consultation.criteres_valides.items():
                    if isinstance(value, list):
                        criteria_list.extend(value)
                    else:
                        criteria_list.append(str(value))
                
                # Ajouter à la liste globale des symptômes
                all_symptoms.extend(criteria_list)
            
            consultations_data.append({
                'id': str(consultation.id),
                'date_consultation': consultation.date_consultation.strftime('%d/%m/%Y à %H:%M'),
                'pathologie_identifiee': clean_pathology_name(consultation.pathologie_identifiee),
                'medecin': consultation.medecin.nom_complet if consultation.medecin else 'Non renseigné',
                'medecin_specialite': consultation.medecin.specialite if consultation.medecin else '',
                'statut': consultation.get_statut_display(),
                'description_clinique': consultation.description_clinique,
                'criteres_valides': criteria_list,
                'nombre_criteres': len(criteria_list)
            })
        
        # Dédupliquer les symptômes
        unique_symptoms = list(set(all_symptoms))
        
        return JsonResponse({
            'success': True,
            'consultations': consultations_data,
            'patient': {
                'nom_complet': patient.nom_complet,
                'numero_dossier': patient.numero_dossier,
                'date_naissance': patient.date_naissance.strftime('%d/%m/%Y') if patient.date_naissance else None,
                'telephone': patient.telephone,
                'email': patient.email
            },
            'all_symptoms': unique_symptoms,  # Tous les symptômes historiques
            'total_symptoms': len(unique_symptoms)
        })
    except Patient.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Patient non trouvé'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la récupération de l\'historique: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def create_patient(request):
    
    
    try:
        data = json.loads(request.body)
        
        # Générer un numéro de dossier unique
        last_patient = Patient.objects.order_by('-id').first()
        if last_patient and last_patient.numero_dossier.startswith('EE-2025-'):
            try:
                last_num = int(last_patient.numero_dossier.split('-')[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        numero_dossier = f'EE-2025-{new_num:03d}'
        
        # Convertir la date de naissance si fournie
        date_naissance = None
        if data.get('date_naissance'):
            try:
                date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
            except:
                pass
        
        patient = Patient.objects.create(
            nom=data.get('nom', '').strip().upper(),
            prenom=data.get('prenom', '').strip().capitalize(),
            date_naissance=date_naissance,
            numero_dossier=numero_dossier,
            telephone=data.get('telephone', '').strip(),
            email=data.get('email', '').strip()
        )
        
        return JsonResponse({
            'success': True,
            'patient': {
                'id': patient.id,
                'nom': patient.nom,
                'prenom': patient.prenom,
                'nom_complet': patient.nom_complet,
                'numero_dossier': patient.numero_dossier,
                'date_naissance': patient.date_naissance.isoformat() if patient.date_naissance else None,
                'telephone': patient.telephone,
                'email': patient.email
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la création du patient: {str(e)}'
        }, status=500)


def get_medecins(request):
    
    
    try:
        medecins = Medecin.objects.all()
        medecins_data = [
            {
                'id': medecin.id,
                'nom': medecin.nom,
                'prenom': medecin.prenom,
                'nom_complet': medecin.nom_complet,
                'specialite': medecin.specialite,
                'numero_ordre': medecin.numero_ordre,
                'telephone': medecin.telephone,
                'email': medecin.email
            }
            for medecin in medecins
        ]
        return JsonResponse({'success': True, 'medecins': medecins_data})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la récupération des médecins: {str(e)}'
        }, status=500)


def create_medecin(request):
    
    
    try:
        data = json.loads(request.body)
        
        # Générer un numéro d'ordre unique
        last_medecin = Medecin.objects.order_by('-id').first()
        if last_medecin and last_medecin.numero_ordre.startswith('MED-2025-'):
            try:
                last_num = int(last_medecin.numero_ordre.split('-')[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        numero_ordre = f'MED-2025-{new_num:03d}'
        
        medecin = Medecin.objects.create(
            nom=data.get('nom', '').strip().upper(),
            prenom=data.get('prenom', '').strip().capitalize(),
            specialite=data.get('specialite', '').strip(),
            numero_ordre=numero_ordre,
            telephone=data.get('telephone', '').strip(),
            email=data.get('email', '').strip()
        )
        
        return JsonResponse({
            'success': True,
            'medecin': {
                'id': medecin.id,
                'nom': medecin.nom,
                'prenom': medecin.prenom,
                'nom_complet': medecin.nom_complet,
                'specialite': medecin.specialite,
                'numero_ordre': medecin.numero_ordre,
                'telephone': medecin.telephone,
                'email': medecin.email
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la création du médecin: {str(e)}'
        }, status=500)


@xframe_options_exempt
def view_pathology(request, html_path):
    
    
    
    try:
        # Construire le chemin complet vers le fichier HTML
        full_path = os.path.join(settings.EMBEDDINGS_FOLDER, html_path)
        
        # Vérifier que le fichier existe et est dans le dossier autorisé
        if not os.path.exists(full_path):
            raise Http404("Page HTML non trouvée")
        
        # Vérifier que le chemin est bien dans le dossier embeddings (sécurité)
        if not os.path.abspath(full_path).startswith(os.path.abspath(settings.EMBEDDINGS_FOLDER)):
            raise Http404("Accès non autorisé")
        
        # Lire le contenu HTML
        with open(full_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Déterminer si on doit injecter les boutons de validation
        mode_validation = request.GET.get('mode') == 'validation'
        has_validate_referer = 'validate' in request.META.get('HTTP_REFERER', '')
        
        # Injecter les boutons de validation si en mode validation
        if mode_validation or has_validate_referer:
            top_buttons_html = """
            <!-- Charger Font Awesome pour les icônes -->
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            
            <style>
            #topValidationButtons {
                position: -webkit-sticky !important;
                position: sticky !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                z-index: 999999 !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                padding: 15px 20px !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
                display: flex !important;
                gap: 15px !important;
                justify-content: center !important;
                align-items: center !important;
                border-bottom: 3px solid rgba(255,255,255,0.2) !important;
                margin: 0 !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            .validation-btn {
                flex: 0 0 auto !important;
                min-width: 180px !important;
                color: white !important;
                font-weight: bold !important;
                padding: 14px 28px !important;
                border: none !important;
                border-radius: 10px !important;
                cursor: pointer !important;
                font-size: 16px !important;
                transition: all 0.3s ease !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 10px !important;
                font-family: Arial, sans-serif !important;
            }
            .validation-btn-valide {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
                box-shadow: 0 4px 10px rgba(16, 185, 129, 0.4) !important;
            }
            .validation-btn-valide:hover {
                transform: translateY(-3px) !important;
                box-shadow: 0 6px 15px rgba(16, 185, 129, 0.5) !important;
            }
            .validation-btn-non-valide {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
                box-shadow: 0 4px 10px rgba(239, 68, 68, 0.4) !important;
            }
            .validation-btn-non-valide:hover {
                transform: translateY(-3px) !important;
                box-shadow: 0 6px 15px rgba(239, 68, 68, 0.5) !important;
            }
            @media (max-width: 640px) {
                #topValidationButtons {
                    flex-direction: column;
                    padding: 12px 15px;
                    gap: 10px;
                }
                .validation-btn {
                    width: 100%;
                    min-width: auto;
                }
            }
            </style>
            
            <script>
            console.log('Boutons de validation sticky injectés !');
            console.log('Position: En haut de l\'iframe, sticky');
            </script>
            
            <div id="topValidationButtons">
                <button onclick="window.validerFormulaire()" class="validation-btn validation-btn-valide">
                    <i class="fas fa-check-circle" style="font-size: 20px;"></i>
                    <span>VALIDER</span>
                </button>
                <button onclick="window.nonValiderFormulaire()" class="validation-btn validation-btn-non-valide">
                    <i class="fas fa-times-circle" style="font-size: 20px;"></i>
                    <span>NON VALIDER</span>
                </button>
            </div>
            """
            

            body_match = re.search(r'<body[^>]*>', html_content, re.IGNORECASE)
            if body_match:
                insert_position = body_match.end()
                html_content = html_content[:insert_position] + top_buttons_html + html_content[insert_position:]
            else:
                html_content = top_buttons_html + html_content
            

            if 'topValidationButtons' in html_content:
                print("CONFIRMATION: topValidationButtons présent dans le HTML final !")
            else:
                print("ERREUR: topValidationButtons NON présent dans le HTML final !")
            
            # Script pour REMPLACER les fonctions de validation et communiquer avec la page parent
            communication_script = """
            <script>
            // REMPLACER complètement les fonctions de validation pour communiquer avec la page parent
            console.log('Injection du script de communication parent-iframe');
            
            // Forcer le remplacement des fonctions
            window.validerFormulaire = function() {
                console.log('VALIDER cliqué dans iframe - envoi message au parent');
                // Envoyer message à la page parent
                if (window.parent && window.parent !== window) {
                    window.parent.postMessage({action: 'validate', source: 'pathology'}, '*');
                    console.log('Message "validate" envoyé au parent');
                } else {
                    console.warn('Pas de parent window détecté');
                    alert('Formulaire validé (mode standalone)');
                }
            };
            
            window.nonValiderFormulaire = function() {
                console.log('NON VALIDER cliqué dans iframe - envoi message au parent');
                // Envoyer message à la page parent
                if (window.parent && window.parent !== window) {
                    window.parent.postMessage({action: 'not_validate', source: 'pathology'}, '*');
                    console.log('Message "not_validate" envoyé au parent');
                } else {
                    console.warn('Pas de parent window détecté');
                    alert('Formulaire non validé (mode standalone)');
                }
            };
            
            console.log(' Fonctions de validation remplacées avec succès');
            </script>
            """
            # Injecter le script juste avant la fermeture du body (après tous les autres scripts)
            html_content = html_content.replace('</body>', communication_script + '</body>')
        
        return HttpResponse(html_content)
        
    except Exception as e:
        raise Http404(f"Erreur lors du chargement de la page: {str(e)}")


def validate_results(request):
    
    
    # Récupérer les résultats depuis la session
    results = request.session.get('search_results', [])
    current_index = int(request.GET.get('index', 0))
    query = request.session.get('search_query', '')
    patient_id = request.session.get('current_patient_id')
    medecin_id = request.session.get('current_medecin_id')
    
    
    
    # Marquer cet index comme visité
    if 'visited_diagnostic_indices' not in request.session:
        request.session['visited_diagnostic_indices'] = []
    if current_index not in request.session['visited_diagnostic_indices']:
        request.session['visited_diagnostic_indices'].append(current_index)
        request.session.modified = True
    
    # Récupérer les informations du patient
    patient = None
    if patient_id:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            pass
    
    if not results or current_index >= len(results):
        return render(request, 'pathology_search/index.html', {
            'error': 'Aucun résultat à valider. Veuillez effectuer une nouvelle recherche.'
        })
    
    current_result = results[current_index]
    is_last = current_index >= len(results) - 1
    
   
    
    # Charger le contenu HTML de la pathologie
    html_path = current_result.get('html_page', '')
    html_content = ''
    pathology_info = {}
    if not html_path and current_result.get('file_name'):
        file_name = current_result.get('file_name', '').replace('.txt', '')
        try:
            
            embeddings_folder = Path(settings.EMBEDDINGS_FOLDER)
            for json_file in embeddings_folder.rglob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        source_file = data.get('source_file', '')
                        if file_name in source_file or source_file.endswith(file_name + '.txt'):
                            html_page = data.get('html_page', '')
                            if html_page:
                                html_path = html_page
                                break
                except:
                    continue
        except Exception as e:
            pass
    if html_path:
        try:
            
            html_path_clean = html_path.lstrip('/')
            if html_path_clean.startswith(settings.EMBEDDINGS_FOLDER + '/'):
                html_path_clean = html_path_clean[len(settings.EMBEDDINGS_FOLDER) + 1:]
            elif html_path_clean.startswith(settings.EMBEDDINGS_FOLDER + '\\'):
                html_path_clean = html_path_clean[len(settings.EMBEDDINGS_FOLDER) + 1:]
            
            full_path = Path(settings.EMBEDDINGS_FOLDER) / html_path_clean
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Récupérer les informations de la pathologie depuis le JSON
                json_path = full_path.with_suffix('.json')
                
                if json_path.exists():
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        pathology_name = data.get('hierarchy', {}).get('parsed_name', '') or \
                                       data.get('hierarchy', {}).get('file_stem', '')
                        pathology_info = {
                            'name': clean_pathology_name(pathology_name),
                            'location': data.get('hierarchy', {}).get('location', ''),
                            'html_page': html_path,
                            'similarity': current_result.get('similarity', 0)
                        }
                else:
                    pathology_info = {
                        'name': clean_pathology_name(current_result.get('file_name', '').replace('.txt', '')),
                        'location': current_result.get('location', ''),
                        'html_page': html_path,
                        'similarity': current_result.get('similarity', 0)
                    }
                
        except Exception as e:
            print(f"Traceback: {traceback.format_exc()}")
    else:
        print(f"html_path est vide - impossible de charger le HTML")
    
    context = {
        'html_content': html_content,
        'pathology_info': pathology_info,
        'pathology_info_json': json.dumps(pathology_info),
        'patient_id': patient_id,
        'medecin_id': medecin_id,
        'patient': patient,
        'current_index': current_index,
        'total_results': len(results),
        'query': query,
        'is_last': is_last
    }
    
    return render(request, 'pathology_search/validate.html', context)


@require_http_methods(["POST"])
def validate_action(request):
    
    try:
        data = json.loads(request.body)
        action = data.get('action')  
        current_index = int(data.get('current_index', 0))
        form_data = data.get('form_data', {})  
        is_direct_access = data.get('direct_access', False)
        
        results = request.session.get('search_results', [])
        
        if action == 'validate':

            if not is_direct_access and current_index < len(results):
                if 'visited_diagnostic_indices' not in request.session:
                    request.session['visited_diagnostic_indices'] = []
                if current_index not in request.session['visited_diagnostic_indices']:
                    request.session['visited_diagnostic_indices'].append(current_index)
                    request.session.modified = True
            

            if is_direct_access:
                pathology_name_raw = data.get('pathology_name', '')
                pathology_name = clean_pathology_name(pathology_name_raw) if pathology_name_raw else ''
                html_page = data.get('html_page', '')
                
                if not html_page:
                    referer = request.META.get('HTTP_REFERER', '')
                    if 'html_page=' in referer:
                        
                        parsed = urllib.parse.urlparse(referer)
                        params = urllib.parse.parse_qs(parsed.query)
                similarity_score = 100  # Score de 100% pour accès direct
                
                
                best_chunk_text = ''
                try:
                    # Construire le chemin vers le fichier JSON
                    if html_page:
                        html_page_clean = html_page.lstrip('/')
                        # Corriger les problèmes d'encodage URL (décode %2F en /)
                        html_page_clean = urllib.parse.unquote(html_page_clean)
                        # Remplacer .html par .json
                        json_path = Path(settings.EMBEDDINGS_FOLDER) / html_page_clean.replace('.html', '.json')
                        print(f"DEBUG - html_page_clean: {html_page_clean}")
                        print(f"DEBUG - json_path: {json_path}")
                        
                        # Vérifier que c'est un fichier, pas un répertoire
                        if json_path.exists() and json_path.is_file():
                            with open(json_path, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)
                                # Récupérer le texte du premier chunk
                                if json_data.get('chunks') and len(json_data['chunks']) > 0:
                                    best_chunk_text = json_data['chunks'][0].get('text_preview', '')
                        else:
                            print(f"Fichier JSON non trouvé ou est un répertoire: {json_path}")
                    else:
                        print(f" html_page est vide")
                except Exception as e:
                    print(f"Erreur lors de la lecture du texte médical: {e}")
                    print(f"Traceback: {traceback.format_exc()}")
                
                # Créer un résultat factice pour l'accès direct
                result = {
                    'file_name': pathology_name + '.txt',
                    'similarity': 1.0,
                    'best_chunk_text': best_chunk_text,
                    'location': html_page
                }
            else:
                # Mode normal (via recherche)
                result = results[current_index]
                pathology_name = clean_pathology_name(result.get('file_name', '').replace('.txt', ''))
                similarity_score = result.get('similarity', 0) * 100
                
                best_chunk_text = result.get('best_chunk_text', '')
            
           
            selected_model = data.get('model', 'chatgpt-5.1')
        
            
            try:
                service = PathologySearchService(model=selected_model, embedding_model_type='openai-ada')
                historical_symptoms = request.session.get('patient_historical_symptoms', [])
                
                diagnosis_result = service.generate_ai_diagnosis(
                    pathology_name=pathology_name,
                    form_data=form_data,
                    similarity_score=similarity_score,
                    medical_text=best_chunk_text,
                    historical_symptoms=historical_symptoms  
                )
            except Exception as e:
                # Gérer les erreurs de l'API (Claude, ChatGPT, etc.) et retourner du JSON
                error_detail = str(e)
                error_traceback = traceback.format_exc()
                print(f"Erreur lors de la génération du diagnostic avec {selected_model}: {error_detail}")
                
                # Retourner une erreur JSON au lieu d'une page HTML
                return JsonResponse({
                    'success': False,
                    'error': f'Erreur lors de la génération du plan de traitement avec {selected_model}: {error_detail}',
                    'error_type': 'api_error',
                    'model': selected_model
                }, status=500)
            diagnosis_id = str(uuid.uuid4())
            
            if 'diagnoses' not in request.session:
                request.session['diagnoses'] = {}
            
            request.session['diagnoses'][diagnosis_id] = {
                'diagnosis': diagnosis_result,
                'result': result,
                'form_data': form_data,
                'model_used': selected_model  
            }
            request.session.modified = True
            try:
                patient_id = request.session.get('current_patient_id')
                medecin_id = request.session.get('current_medecin_id')
                query = request.session.get('search_query', '')
                
                # Pour l'accès direct, utiliser une description spécifique
                if is_direct_access:
                    query = f"Accès direct à la pathologie : {pathology_name}"
            
                if patient_id:
                    patient = Patient.objects.get(id=patient_id)
                    
                    medecin = None
                    form_data_with_model = form_data.copy() if form_data else {}
                    form_data_with_model['_metadata'] = {
                        'model_used': selected_model,
                        'model_display_name': {
                            'chatgpt-5.1': 'Model 1',
                            'claude-4.5': 'Model 2',
                        }.get(selected_model, selected_model)
                    }
                    
                    # Récupérer uniquement le plan de traitement (pas de diagnostic summary)
                    treatment_plan = diagnosis_result.get('treatment_plan', '')
                    
                    # Créer la consultation
                    consultation = Consultation.objects.create(
                        patient=patient,
                        medecin=medecin,
                        description_clinique=query,
                        pathologie_identifiee=pathology_name,
                        score_similarite=similarity_score / 100,  # Convertir en décimal (0-1)
                        fichier_source=result.get('file_name', ''),
                        criteres_valides=form_data_with_model,  # 🆕 Inclure le modèle dans les métadonnées
                        plan_traitement=treatment_plan,  # 🆕 Uniquement le plan de traitement
                        statut='valide'
                    )
                    
                    # Stocker l'ID de la consultation dans la session pour le rapport
                    request.session['diagnoses'][diagnosis_id]['consultation_id'] = str(consultation.id)
                    request.session.modified = True
            except Exception as e:
                # Si erreur, continuer quand même (ne pas bloquer l'utilisateur)
                print(f"Erreur lors de la sauvegarde de la consultation: {e}")
            
            return JsonResponse({
                'success': True,
                'action': 'validated',
                'message': f"Pathologie validée : {pathology_name}",
                'diagnosis_id': diagnosis_id
            })
        
        elif action == 'skip':
            
            if not is_direct_access and current_index < len(results):
                if 'visited_diagnostic_indices' not in request.session:
                    request.session['visited_diagnostic_indices'] = []
                if current_index not in request.session['visited_diagnostic_indices']:
                    request.session['visited_diagnostic_indices'].append(current_index)
                    request.session.modified = True
                   
            
            if is_direct_access:
                pathology_name_raw = data.get('pathology_name', '')
                pathology_name = clean_pathology_name(pathology_name_raw) if pathology_name_raw else ''
                html_page = data.get('html_page', '')
                similarity_score = 100
                
                result = {
                    'file_name': pathology_name + '.txt',
                    'similarity': 1.0,
                    'location': html_page
                }
            else:
                # Mode normal (via recherche)
                if current_index < len(results):
                    result = results[current_index]
                    pathology_name = clean_pathology_name(result.get('file_name', '').replace('.txt', ''))
                    similarity_score = result.get('similarity', 0) * 100
                else:
                    pathology_name = "Inconnue"
                    similarity_score = 0
                    result = {}
            
            # Sauvegarder la consultation NON VALIDÉE dans la base de données
            try:
                
                patient_id = request.session.get('current_patient_id')
                medecin_id = request.session.get('current_medecin_id')
                query = request.session.get('search_query', '')
                
                # Pour l'accès direct, utiliser une description spécifique
                if is_direct_access:
                    query = f"Accès direct à la pathologie (non validée) : {pathology_name}"
                
                # 🆕 Sauvegarder même s'il n'y a pas de critères cochés (enregistrer quand même)
                if patient_id:
                    patient = Patient.objects.get(id=patient_id)
                    
                    # Le nom du médecin est directement dans patient.treating_physician (champ texte)
                    # Le champ medecin dans Consultation est une ForeignKey optionnelle, on la laisse à None
                    # car le nom du médecin est déjà stocké dans le patient
                    medecin = None
                    if patient.treating_physician:
                        print(f"✅ Médecin principal du patient: {patient.treating_physician}")
                    
                    # Créer la consultation avec statut "non_valide" même si pas de critères
                    consultation = Consultation.objects.create(
                        patient=patient,
                        medecin=medecin,
                        description_clinique=query,
                        pathologie_identifiee=pathology_name,
                        score_similarite=similarity_score / 100,
                        fichier_source=result.get('file_name', ''),
                        criteres_valides=form_data if form_data else {},  # Sauvegarder les critères même si vide
                        plan_traitement='',  # Pas de plan de traitement car non validé
                        statut='non_valide'  # Statut spécial pour les pathologies rejetées
                    )
                    
                    print(f"✅ Consultation NON VALIDÉE sauvegardée (ID: {consultation.id}) avec {len(form_data) if form_data else 0} critères")
                    
                    # 🆕 Extraire TOUS les symptômes des critères cochés pour les sauvegarder dans l'historique
                    # Fonction pour nettoyer et valider un symptôme (réutilisée)
                    def clean_and_validate_symptom(symptom_text):
                        """Nettoyer et valider un symptôme avant de l'ajouter à l'historique"""
                        if not symptom_text:
                            return None
                        
                        symptom_text = str(symptom_text).strip()
                        
                        # Ignorer les chaînes trop courtes (moins de 2 caractères)
                        if len(symptom_text) < 2:
                            return None
                        
                        # Ignorer les chaînes qui ne contiennent que des symboles
                        if not re.search(r'[a-zA-ZÀ-ÿ]', symptom_text):
                            return None
                        
                        # Ignorer les chaînes répétitives (comme "aaaa", "test test test")
                        words = symptom_text.split()
                        if len(words) > 1 and len(set(words)) == 1:
                            return None
                        
                        # Ignorer les chaînes qui sont clairement des métadonnées
                        if symptom_text.lower().startswith('_metadata') or symptom_text.lower() == '_metadata':
                            return None
                        
                        return symptom_text
                    
                    symptoms = []
                    if form_data:
                        for key, value in form_data.items():
                            # Ignorer les métadonnées
                            if key == '_metadata':
                                continue
                            if isinstance(value, list):
                                # Si c'est une liste, extraire chaque symptôme
                                for item in value:
                                    cleaned = clean_and_validate_symptom(item)
                                    if cleaned:
                                        symptoms.append(cleaned)
                            elif isinstance(value, dict):
                                # Si c'est un dictionnaire, extraire les valeurs
                                for sub_key, sub_value in value.items():
                                    cleaned = clean_and_validate_symptom(sub_value)
                                    if cleaned:
                                        symptoms.append(cleaned)
                            else:
                                cleaned = clean_and_validate_symptom(value)
                                if cleaned:
                                    symptoms.append(cleaned)
                    
                    # Dédupliquer les symptômes
                    symptoms = list(set(symptoms))
                    
                    # Ajouter les symptômes à l'historique du patient dans la session (seulement les valides)
                    if 'patient_historical_symptoms' not in request.session:
                        request.session['patient_historical_symptoms'] = []
                    request.session['patient_historical_symptoms'].extend(symptoms)
                    # Dédupliquer l'historique complet
                    request.session['patient_historical_symptoms'] = list(set(request.session['patient_historical_symptoms']))
                    request.session.modified = True
                    print(f" {len(symptoms)} symptômes (critères cochés) ajoutés à l'historique du patient: {symptoms[:5]}...")
            except Exception as e:
                print(f"Erreur lors de la sauvegarde de la consultation non validée: {e}")
            
            #  Retourner aux résultats (excluant celui non validé) ou à la page principale si tous sont consommés
            visited_indices = set(request.session.get('visited_diagnostic_indices', []))
            total_results = len(results) if not is_direct_access else 0
            
            # Si tous les résultats ont été visités, retourner à la page principale
            if not is_direct_access and len(visited_indices) >= total_results:
                return JsonResponse({
                    'success': True,
                    'action': 'back_to_index',
                    'message': 'Tous les diagnostics ont été évalués. Retour à la page principale.',
                    'redirect_url': '/'
                })
            
            # Sinon, retourner aux résultats (celui non validé sera exclu)
            return JsonResponse({
                'success': True,
                'action': 'back_to_results',
                'message': 'Pathologie non validée. Retour aux résultats de similarité.',
                'redirect_url': '/results-selection/'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Action invalide'
            }, status=400)
    
    except Exception as global_error:
        error_detail = str(global_error)
        error_traceback = traceback.format_exc()
        print(f"❌ Erreur globale dans validate_action: {error_detail}")
        print(f"❌ Traceback complet:\n{error_traceback}")
        
        # TOUJOURS retourner du JSON, même en cas d'erreur système
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du traitement de la requête: {error_detail}',
            'error_type': 'system_error',
            'message': 'Une erreur est survenue. Veuillez réessayer.'
        }, status=500)


def show_diagnosis(request, diagnosis_id):
    """
    Afficher le diagnostic IA généré pour une pathologie validée.
    """
    diagnoses = request.session.get('diagnoses', {})
    
    if diagnosis_id not in diagnoses:
        return render(request, 'pathology_search/index.html', {
            'error': 'Diagnostic non trouvé. Veuillez effectuer une nouvelle recherche.'
        })
    
    diagnosis_data = diagnoses[diagnosis_id]
    diagnosis_result = diagnosis_data['diagnosis']
    result = diagnosis_data['result']
    form_data = diagnosis_data['form_data']
    model_used = diagnosis_data.get('model_used', 'chatgpt-5.1')  # 🆕 Récupérer le modèle utilisé
    
    # Récupérer uniquement le plan de traitement (pas de diagnostic summary)
    treatment_plan = diagnosis_result.get('treatment_plan', '')
    
    # Récupérer l'ID de consultation et du patient depuis la session
    consultation_id = diagnosis_data.get('consultation_id')
    patient_id = request.session.get('current_patient_id')
    
    # Récupérer les informations du patient
    patient_nom = ''
    patient_prenom = ''
    patient_identite = ''
    if consultation_id:
        try:
            consultation = Consultation.objects.select_related('patient').get(id=consultation_id)
            patient = consultation.patient
            patient_nom = patient.last_name or patient.nom or ''
            patient_prenom = patient.first_name or patient.prenom or ''
            patient_identite = patient.patient_identifier or patient.numero_dossier or ''
        except Exception as e:
            print(f"Erreur lors de la récupération du patient depuis la consultation: {e}")
    elif patient_id:
        try:
            patient = Patient.objects.get(id=patient_id)
            patient_nom = patient.last_name or patient.nom or ''
            patient_prenom = patient.first_name or patient.prenom or ''
            patient_identite = patient.patient_identifier or patient.numero_dossier or ''
        except Exception as e:
            print(f"Erreur lors de la récupération du patient: {e}")
    
    # Nom du modèle formaté pour l'affichage
    model_names = {
        'chatgpt-5.1': 'Model 1',
        'claude-4.5': 'Model 2'
    }
    model_display_name = model_names.get(model_used, model_used)

    # Récupérer le statut de la consultation, le plan validé et les notes
    consultation_statut = 'en_cours'
    plan_valide = ''
    notes_medecin = ''  # Initialiser par défaut
    if consultation_id:
        try:
            consultation = Consultation.objects.get(id=consultation_id)
            consultation_statut = consultation.statut
            plan_valide = consultation.plan_traitement_valide if consultation.plan_traitement_valide else ''
            notes_medecin = consultation.notes_medecin if consultation.notes_medecin else ''
        except Exception as e:
            print(f"Erreur lors de la récupération de la consultation: {e}")
            notes_medecin = ''  # S'assurer que notes_medecin est défini même en cas d'erreur
    
    context = {
        'diagnosis_id': diagnosis_id,
        'diagnosis': '',  # Pas de diagnostic summary
        'treatment_plan': treatment_plan,  # Uniquement le plan de traitement
        'pathology_name': diagnosis_result.get('pathology', ''),
        'confidence': diagnosis_result.get('confidence', 0),
        'timestamp': diagnosis_result.get('timestamp', ''),
        'result': result,
        'form_data': form_data,
        'success': diagnosis_result.get('success', False),
        'consultation_id': consultation_id,
        'patient_id': patient_id,
        'patient_nom': patient_nom,  # Nom du patient
        'patient_prenom': patient_prenom,  #  Prénom du patient
        'patient_identite': patient_identite,  #  Identité du patient
        'model_used': model_used,  # Modèle utilisé
        'model_display_name': model_display_name,  # Nom formaté pour affichage
        'diagnosis_result': diagnosis_result,  # Pour accéder à error et error_detail
        'consultation_statut': consultation_statut,  # Statut de la consultation
        'plan_valide': plan_valide,  # Plan validé
        'notes_medecin': notes_medecin  # Notes du médecin
    }
    
    return render(request, 'pathology_search/diagnosis.html', context)


@require_http_methods(["POST"])
def validate_treatment_plan(request, consultation_id):
    try:

        data = json.loads(request.body)
        notes_medecin = data.get('notes_medecin', '')
        plan_traitement_modifie = data.get('plan_traitement', '')  # 🆕 Récupérer le plan modifié depuis l'interface
        
        consultation = Consultation.objects.get(id=consultation_id)
        
        # 🆕 Si le plan modifié est fourni, l'utiliser, sinon utiliser le plan actuel
        if plan_traitement_modifie:
            # Sauvegarder le plan modifié dans plan_traitement ET plan_traitement_valide
            consultation.plan_traitement = plan_traitement_modifie
            consultation.plan_traitement_valide = plan_traitement_modifie
            print(f"✅ Plan de traitement modifié validé - Longueur: {len(plan_traitement_modifie)} caractères")
        else:
            # Si pas de plan modifié fourni, utiliser le plan actuel
            consultation.plan_traitement_valide = consultation.plan_traitement
            print(f"✅ Plan de traitement actuel validé - Longueur: {len(consultation.plan_traitement)} caractères")
        
        consultation.notes_medecin = notes_medecin  # Sauvegarder aussi les notes
        consultation.statut = 'valide'
        consultation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Plan de traitement validé avec succès'
        })
    except Consultation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Consultation non trouvée'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def modify_treatment_plan(request, consultation_id):
    try:
        data = json.loads(request.body)
        new_plan = data.get('plan_traitement', '')
        notes_medecin = data.get('notes_medecin', '')
        
        consultation = Consultation.objects.get(id=consultation_id)
        consultation.plan_traitement = new_plan
        consultation.notes_medecin = notes_medecin
        consultation.statut = 'en_cours'  # Remettre en cours après modification
        consultation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Plan de traitement et notes modifiés avec succès'
        })
    except Consultation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Consultation non trouvée'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def delete_consultation(request, consultation_id):
    try:
        consultation = Consultation.objects.get(id=consultation_id)
        consultation.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Consultation supprimée avec succès'
        })
    except Consultation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Consultation non trouvée'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def direct_pathology_access(request):
    
    
    html_path = request.GET.get('html_page', '')
    patient_id = request.GET.get('patient_id')
    medecin_id = request.GET.get('medecin_id')
    
    # Stocker les IDs dans la session
    if patient_id:
        request.session['current_patient_id'] = int(patient_id)
    if medecin_id:
        request.session['current_medecin_id'] = int(medecin_id)
    
    if not html_path:
        return render(request, 'pathology_search/index.html', {
            'error': 'Aucune pathologie spécifiée.'
        })
    
    try:
        # Construire le chemin complet
        full_path = Path(settings.EMBEDDINGS_FOLDER) / html_path
        
        # Vérifier que le fichier existe
        if not full_path.exists():
            raise Http404("Page HTML non trouvée")
        
        # Vérifier la sécurité
        if not str(full_path.resolve()).startswith(str(Path(settings.EMBEDDINGS_FOLDER).resolve())):
            raise Http404("Accès non autorisé")
        
        # Lire le contenu HTML
        with open(full_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        patient = None
        if patient_id:
            try:
                patient = Patient.objects.get(id=int(patient_id))
            except:
                pass
        
        # Récupérer les informations de la pathologie depuis le JSON
        json_path = full_path.with_suffix('.json')
        pathology_info = {}
        
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                pathology_name = data.get('hierarchy', {}).get('parsed_name', '') or \
                               data.get('hierarchy', {}).get('file_stem', '')
                pathology_info = {
                    'name': clean_pathology_name(pathology_name),
                    'location': data.get('hierarchy', {}).get('location', ''),
                    'html_page': html_path
                }
        
        context = {
            'html_content': html_content,
            'pathology_info': pathology_info,
            'pathology_info_json': json.dumps(pathology_info),
            'patient_id': request.session.get('current_patient_id'),
            'medecin_id': request.session.get('current_medecin_id'),
            'patient': patient
        }
        
        return render(request, 'pathology_search/direct_access.html', context)
    
    except Exception as e:
        return render(request, 'pathology_search/index.html', {
            'error': f'Erreur lors du chargement de la pathologie: {str(e)}'
        })


def get_all_pathologies(request):
    
    
    try:
        embeddings_folder = settings.EMBEDDINGS_FOLDER
        
        if isinstance(embeddings_folder, str):
            folder_path = Path(embeddings_folder)
        else:
            folder_path = embeddings_folder
        
        pathologies = []
        
        # Parcourir récursivement tous les fichiers JSON
        for json_file in folder_path.rglob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Vérifier si le fichier a un html_page
                    if 'html_page' in data and data['html_page']:
                        # Extraire le nom de la pathologie depuis hierarchy
                        pathology_name = data.get('hierarchy', {}).get('parsed_name', '') or \
                                       data.get('hierarchy', {}).get('file_stem', '')
                        
                        if pathology_name:
                            # Nettoyer le nom de la pathologie
                            clean_name = clean_pathology_name(pathology_name)
                            
                            pathologies.append({
                                'name': clean_name,
                                'original_name': pathology_name,
                                'html_page': data['html_page'],
                                'location': data.get('hierarchy', {}).get('location', '')
                            })
            except Exception as e:
                # Ignorer les fichiers JSON invalides
                continue
        
        # Trier les pathologies par nom
        pathologies.sort(key=lambda x: x['name'])
        
        return JsonResponse({
            'success': True,
            'pathologies': pathologies,
            'count': len(pathologies)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la récupération des pathologies: {str(e)}'
        }, status=500)