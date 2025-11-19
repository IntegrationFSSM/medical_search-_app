"""
Vues pour l'application de recherche de pathologies
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.clickjacking import xframe_options_exempt
from .services import PathologySearchService
import json
import re


def clean_pathology_name(text):
    """Nettoyer le nom de la pathologie en enlevant les préfixes Section/SubSection"""
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
    """Nettoyer le texte simple (pour critères)"""
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
    """Formater le plan de traitement avec HTML sophistiqué"""
    if not text:
        return text
    text = str(text)
    
    # Enlever les emojis
    text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
    text = re.sub(r'[\u2600-\u26FF]', '', text)
    text = re.sub(r'[\u2700-\u27BF]', '', text)
    
    # Convertir les titres markdown en HTML avec styles
    text = re.sub(r'^# (.+)$', r'<div class="plan-h1">\1</div>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<div class="plan-h2">\1</div>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<div class="plan-h3">\1</div>', text, flags=re.MULTILINE)
    
    # Convertir le gras **texte** en <strong>
    text = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', text)
    
    # Convertir les listes à puces
    text = re.sub(r'^\- (.+)$', r'<div class="plan-bullet">• \1</div>', text, flags=re.MULTILINE)
    text = re.sub(r'^\* (.+)$', r'<div class="plan-bullet">• \1</div>', text, flags=re.MULTILINE)
    
    # Convertir les numéros de liste
    text = re.sub(r'^\d+\.\s+(.+)$', r'<div class="plan-number">\1</div>', text, flags=re.MULTILINE)
    
    # Convertir les sauts de ligne en <br>
    text = text.replace('\n\n', '<br><br>')
    text = text.replace('\n', '<br>')
    
    return text


def index(request):
    """Page d'accueil avec le formulaire de recherche."""
    return render(request, 'pathology_search/index.html')


@require_http_methods(["POST"])
def search(request):
    """
    Endpoint de recherche pour les requêtes cliniques.
    """
    try:
        # Récupérer les données de la requête
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        top_k = int(data.get('top_k', 5))
        aggregation = data.get('aggregation', 'max')
        use_validation = data.get('use_validation', False)  # Mode validation ou affichage normal
        patient_id = data.get('patient_id')  # Récupérer l'ID du patient
        medecin_id = data.get('medecin_id')  # Récupérer l'ID du médecin
        historical_symptoms = data.get('historical_symptoms', [])  # 🆕 Symptômes historiques
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'La requête ne peut pas être vide'
            }, status=400)
        
        # Sauvegarder l'ID du patient, du médecin et les symptômes historiques dans la session
        if patient_id:
            request.session['current_patient_id'] = patient_id
        if medecin_id:
            request.session['current_medecin_id'] = medecin_id
        if historical_symptoms:
            request.session['patient_historical_symptoms'] = historical_symptoms
            print(f"📊 {len(historical_symptoms)} symptômes historiques sauvegardés dans la session")
        request.session.modified = True
        
        # 🆕 ÉTAPE 1: ENRICHIR LA REQUÊTE AVEC L'HISTORIQUE DU PATIENT (BACKEND)
        enriched_query = query
        if patient_id and historical_symptoms and len(historical_symptoms) > 0:
            # Limiter à 10 symptômes pour ne pas surcharger la recherche
            symptoms_for_search = historical_symptoms[:10]
            symptoms_text = ', '.join(symptoms_for_search)
            enriched_query = f"{query}. Antécédents patient: {symptoms_text}"
            print(f"🔍 Requête enrichie avec {len(symptoms_for_search)} symptômes: {enriched_query[:100]}...")
        
        # ÉTAPE 2: Valider la requête ORIGINALE avec GPT-4o (pas la requête enrichie)
        service = PathologySearchService()
        validation_result = service.validate_medical_query(query)
        
        if not validation_result['is_valid']:
            return JsonResponse({
                'success': False,
                'error': 'Requête non valide',
                'error_type': 'invalid_query',
                'reason': validation_result['reason']
            })
        
        # ÉTAPE 3: Effectuer la recherche avec la REQUÊTE ENRICHIE
        search_results = service.find_best_match(
            query=enriched_query,  # 🆕 Utiliser la requête enrichie
            top_k=top_k,
            aggregation=aggregation
        )
        
        # Si mode validation, sauvegarder dans la session
        if use_validation and search_results.get('success'):
            request.session['search_results'] = search_results['results']
            request.session['search_query'] = query
            # Réinitialiser la liste des indices visités pour une nouvelle recherche
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
    """
    Afficher les 5 résultats de recherche pour que le médecin choisisse lequel valider.
    Affiche seulement les diagnostics non visités.
    """
    results = request.session.get('search_results', [])
    query = request.session.get('search_query', '')
    
    if not results:
        return render(request, 'pathology_search/index.html', {
            'error': 'Aucun résultat trouvé. Veuillez effectuer une nouvelle recherche.'
        })
    
    # Récupérer les indices visités depuis la session
    visited_indices = set(request.session.get('visited_diagnostic_indices', []))
    
    # Préparer les résultats pour l'affichage (seulement les non visités)
    prepared_results = []
    for i, result in enumerate(results):
        # Ne pas afficher si déjà visité
        if i in visited_indices:
            continue
            
        pathology_name = clean_pathology_name(result.get('file_name', '').replace('.txt', ''))
        similarity = result.get('similarity', 0)
        similarity_percent = int(similarity * 100)
        
        prepared_results.append({
            'index': i,
            'pathology_name': pathology_name,
            'location': result.get('location', ''),
            'similarity': similarity,
            'similarity_percent': similarity_percent,
            'html_page': result.get('html_page', '')
        })
    
    # Si tous les diagnostics ont été visités, retourner à la page principale
    if len(visited_indices) >= len(results):
        # Sauvegarder les symptômes avant de retourner
        # Les symptômes sont déjà sauvegardés dans les consultations
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


def about(request):
    """Page À propos."""
    return render(request, 'pathology_search/about.html')


def print_report(request, consultation_id):
    """
    Générer un rapport PDF de la consultation avec en-tête CLINIQUE LA VALLÉE.
    """
    try:
        from .models import Consultation
        from django.utils import timezone
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        import logging
        
        logger = logging.getLogger(__name__)
        
        consultation = Consultation.objects.select_related('patient', 'medecin').get(id=consultation_id)
        
        logger.info(f"Generating PDF for consultation {consultation_id}")
        
        # S'assurer que les données sont présentes
        if not consultation.criteres_valides:
            consultation.criteres_valides = {}
        
        # Formater le plan de traitement de manière sophistiquée
        plan_traitement_clean = format_plan_traitement_html(consultation.plan_traitement)
        
        # Nettoyer le nom de la pathologie (enlever sections/sous-sections)
        pathologie_clean = clean_pathology_name(consultation.pathologie_identifiee)
        
        # Nettoyer les critères validés
        criteres_valides_clean = {}
        for key, value in consultation.criteres_valides.items():
            clean_key = clean_text_for_pdf(key)
            clean_value = clean_text_for_pdf(value)
            criteres_valides_clean[clean_key] = clean_value
        
        context = {
            'consultation': consultation,
            'patient': consultation.patient,
            'medecin': consultation.medecin,
            'date_impression': timezone.now(),
            'plan_traitement_clean': plan_traitement_clean,
            'pathologie_clean': pathologie_clean,
            'criteres_valides_clean': criteres_valides_clean,
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
            from weasyprint import HTML
            
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
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in print_report: {str(e)}")
        return HttpResponse(f'Erreur inattendue: {str(e)}', status=500)


def patient_history(request, patient_id):
    """
    Afficher l'historique des consultations d'un patient.
    """
    try:
        from .models import Patient, Consultation
        
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
    """Récupérer la liste de tous les patients"""
    from .models import Patient
    
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
    """Récupérer l'historique des consultations d'un patient avec tous les symptômes"""
    from .models import Patient, Consultation
    
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
    """Créer un nouveau patient"""
    from .models import Patient
    from datetime import datetime
    
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
    """Récupérer la liste de tous les médecins"""
    from .models import Medecin
    
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
    """Créer un nouveau médecin"""
    from .models import Medecin
    
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
    """
    Afficher le contenu HTML d'une pathologie.
    Autorise l'affichage dans une iframe.
    """
    print("="*80)
    print(f"🎯 view_pathology APPELÉE !")
    print(f"📄 HTML path: {html_path}")
    print(f"🔗 Full URL: {request.build_absolute_uri()}")
    print("="*80)
    
    from django.conf import settings
    from django.http import HttpResponse, Http404
    import os
    
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
        
        # TOUJOURS injecter les boutons (pour déboguer)
        mode_validation = request.GET.get('mode') == 'validation'
        has_validate_referer = 'validate' in request.META.get('HTTP_REFERER', '')
        
        print(f"🔍 view_pathology appelé pour: {html_path}")
        print(f"🔍 mode GET parameter: {request.GET.get('mode')}")
        print(f"🔍 HTTP_REFERER: {request.META.get('HTTP_REFERER', 'NONE')}")
        print(f"🔍 Injection prévue: {mode_validation or has_validate_referer}")
        
        # TEMPORAIRE: Toujours injecter pour tester
        if True:  # Forcer à True pour tester
            print("🚀 INJECTION FORCÉE DES BOUTONS POUR TEST")
            # 🆕 Boutons VALIDER et NON VALIDER en haut (sticky) - VERSION AMÉLIORÉE
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
            console.log('🎨 Boutons de validation sticky injectés !');
            console.log('📍 Position: En haut de l\'iframe, sticky');
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
            
            print(f"✅ Boutons injectés dans le HTML pour {html_path}")
            
            # Injecter les boutons juste après l'ouverture du <body>
            import re
            body_match = re.search(r'<body[^>]*>', html_content, re.IGNORECASE)
            if body_match:
                insert_position = body_match.end()
                print(f"✅ Balise <body> trouvée à la position {insert_position}")
                html_content = html_content[:insert_position] + top_buttons_html + html_content[insert_position:]
                print(f"✅ Boutons injectés ! Longueur ajoutée: {len(top_buttons_html)} caractères")
            else:
                print("⚠️ Pas de balise <body> trouvée, injection au début")
                # Si pas de balise body, injecter au début
                html_content = top_buttons_html + html_content
            
            # Vérifier que l'injection a réussi
            if 'topValidationButtons' in html_content:
                print("✅✅✅ CONFIRMATION: topValidationButtons présent dans le HTML final !")
            else:
                print("❌❌❌ ERREUR: topValidationButtons NON présent dans le HTML final !")
            
            # Script pour REMPLACER les fonctions de validation et communiquer avec la page parent
            communication_script = """
            <script>
            // REMPLACER complètement les fonctions de validation pour communiquer avec la page parent
            console.log('🔧 Injection du script de communication parent-iframe');
            
            // Forcer le remplacement des fonctions
            window.validerFormulaire = function() {
                console.log('✅ VALIDER cliqué dans iframe - envoi message au parent');
                // Envoyer message à la page parent
                if (window.parent && window.parent !== window) {
                    window.parent.postMessage({action: 'validate', source: 'pathology'}, '*');
                    console.log('📤 Message "validate" envoyé au parent');
                } else {
                    console.warn('⚠️ Pas de parent window détecté');
                    alert('Formulaire validé (mode standalone)');
                }
            };
            
            window.nonValiderFormulaire = function() {
                console.log('❌ NON VALIDER cliqué dans iframe - envoi message au parent');
                // Envoyer message à la page parent
                if (window.parent && window.parent !== window) {
                    window.parent.postMessage({action: 'not_validate', source: 'pathology'}, '*');
                    console.log('📤 Message "not_validate" envoyé au parent');
                } else {
                    console.warn('⚠️ Pas de parent window détecté');
                    alert('Formulaire non validé (mode standalone)');
                }
            };
            
            console.log('✅ Fonctions de validation remplacées avec succès');
            </script>
            """
            # Injecter le script juste avant la fermeture du body (après tous les autres scripts)
            html_content = html_content.replace('</body>', communication_script + '</body>')
        
        return HttpResponse(html_content)
        
    except Exception as e:
        raise Http404(f"Erreur lors du chargement de la page: {str(e)}")


def validate_results(request):
    """
    Page de validation des résultats avec navigation étape par étape.
    Affiche le formulaire HTML directement dans la page (même structure que direct_access.html).
    """
    print("="*80)
    print("🎯 validate_results APPELÉE !")
    print(f"Index: {request.GET.get('index', 0)}")
    print("="*80)
    
    from django.conf import settings
    from django.http import Http404
    import os
    
    # Récupérer les résultats depuis la session
    results = request.session.get('search_results', [])
    current_index = int(request.GET.get('index', 0))
    query = request.session.get('search_query', '')
    patient_id = request.session.get('current_patient_id')
    medecin_id = request.session.get('current_medecin_id')
    
    print(f"🔍 Nombre de résultats: {len(results)}")
    print(f"📊 Index actuel: {current_index}")
    print(f"🔎 Query: {query}")
    print(f"👤 Patient ID: {patient_id}")
    
    # Marquer cet index comme visité
    if 'visited_diagnostic_indices' not in request.session:
        request.session['visited_diagnostic_indices'] = []
    if current_index not in request.session['visited_diagnostic_indices']:
        request.session['visited_diagnostic_indices'].append(current_index)
        request.session.modified = True
        print(f"✅ Index {current_index} marqué comme visité")
    
    # Récupérer les informations du patient
    patient = None
    if patient_id:
        from .models import Patient
        try:
            patient = Patient.objects.get(id=patient_id)
            print(f"✅ Patient trouvé: {patient.nom} {patient.prenom}")
        except Patient.DoesNotExist:
            print("❌ Patient non trouvé")
            pass
    
    if not results or current_index >= len(results):
        print("⚠️ Aucun résultat ou index hors limites")
        return render(request, 'pathology_search/index.html', {
            'error': 'Aucun résultat à valider. Veuillez effectuer une nouvelle recherche.'
        })
    
    current_result = results[current_index]
    is_last = current_index >= len(results) - 1
    
    print(f"📄 Résultat actuel: {current_result.get('file_name', 'N/A')}")
    print(f"🏁 Est dernier: {is_last}")
    
    # Charger le contenu HTML de la pathologie
    html_path = current_result.get('html_page', '')
    html_content = ''
    pathology_info = {}
    if html_path:
        try:
            from pathlib import Path
            full_path = Path(settings.EMBEDDINGS_FOLDER) / html_path
            
            if full_path.exists():
                # Lire le contenu HTML
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
                print(f"✅ HTML chargé: {html_path}")
        except Exception as e:
            print(f"❌ Erreur chargement HTML: {e}")
            pass
    
    # Préparer le contexte pour le template
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
    """
    Gérer les actions de validation (valider ou ne pas valider).
    """
    data = json.loads(request.body)
    action = data.get('action')  # 'validate' ou 'skip'
    current_index = int(data.get('current_index', 0))
    form_data = data.get('form_data', {})  # Données du formulaire
    is_direct_access = data.get('direct_access', False)
    
    results = request.session.get('search_results', [])
    
    if action == 'validate':
        # Marquer l'index comme visité lors de la validation
        if not is_direct_access and current_index < len(results):
            if 'visited_diagnostic_indices' not in request.session:
                request.session['visited_diagnostic_indices'] = []
            if current_index not in request.session['visited_diagnostic_indices']:
                request.session['visited_diagnostic_indices'].append(current_index)
                request.session.modified = True
                print(f"✅ Index {current_index} marqué comme visité (validation)")
        
        # Gérer l'accès direct (sans recherche préalable)
        if is_direct_access:
            pathology_name = data.get('pathology_name', '')
            html_page = data.get('html_page', '')
            similarity_score = 100  # Score de 100% pour accès direct
            
            # Charger le texte médical depuis le fichier .npy correspondant
            from django.conf import settings
            from pathlib import Path
            
            best_chunk_text = ''
            try:
                # Construire le chemin vers le fichier JSON
                json_path = Path(settings.EMBEDDINGS_FOLDER) / html_page.replace('.html', '.json')
                if json_path.exists():
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        # Récupérer le texte du premier chunk
                        if json_data.get('chunks') and len(json_data['chunks']) > 0:
                            best_chunk_text = json_data['chunks'][0].get('text_preview', '')
            except Exception as e:
                print(f"Erreur lors de la lecture du texte médical: {e}")
            
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
            
            # Extraire le texte médical du meilleur chunk
            best_chunk_text = result.get('best_chunk_text', '')
        
        # Générer le diagnostic IA avec OpenAI en incluant le texte médical ET l'historique
        from .services import PathologySearchService
        service = PathologySearchService()
        
        # 🆕 Récupérer les symptômes historiques depuis la session
        historical_symptoms = request.session.get('patient_historical_symptoms', [])
        
        diagnosis_result = service.generate_ai_diagnosis(
            pathology_name=pathology_name,
            form_data=form_data,
            similarity_score=similarity_score,
            medical_text=best_chunk_text,
            historical_symptoms=historical_symptoms  # 🆕 Inclure l'historique
        )
        
        # Sauvegarder le diagnostic en session
        import uuid
        diagnosis_id = str(uuid.uuid4())
        
        if 'diagnoses' not in request.session:
            request.session['diagnoses'] = {}
        
        request.session['diagnoses'][diagnosis_id] = {
            'diagnosis': diagnosis_result,
            'result': result,
            'form_data': form_data
        }
        request.session.modified = True
        
        # Sauvegarder la consultation dans la base de données PostgreSQL
        try:
            from .models import Patient, Consultation
            
            # Récupérer l'ID du patient depuis la session
            patient_id = request.session.get('current_patient_id')
            medecin_id = request.session.get('current_medecin_id')
            query = request.session.get('search_query', '')
            
            # Pour l'accès direct, utiliser une description spécifique
            if is_direct_access:
                query = f"Accès direct à la pathologie : {pathology_name}"
            
            if patient_id:
                patient = Patient.objects.get(id=patient_id)
                
                # Récupérer le médecin si disponible
                medecin = None
                if medecin_id:
                    try:
                        from .models import Medecin
                        medecin = Medecin.objects.get(id=medecin_id)
                    except Medecin.DoesNotExist:
                        pass
                
                # Créer la consultation
                consultation = Consultation.objects.create(
                    patient=patient,
                    medecin=medecin,
                    description_clinique=query,
                    pathologie_identifiee=pathology_name,
                    score_similarite=similarity_score / 100,  # Convertir en décimal (0-1)
                    fichier_source=result.get('file_name', ''),
                    criteres_valides=form_data,
                    plan_traitement=diagnosis_result.get('diagnosis', ''),
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
        # IMPORTANT: Même si NON VALIDE, sauvegarder les critères cochés pour les antécédents
        
        # Gérer l'accès direct vs recherche normale
        if is_direct_access:
            pathology_name = data.get('pathology_name', '')
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
            from .models import Patient, Consultation
            
            patient_id = request.session.get('current_patient_id')
            medecin_id = request.session.get('current_medecin_id')
            query = request.session.get('search_query', '')
            
            # Pour l'accès direct, utiliser une description spécifique
            if is_direct_access:
                query = f"Accès direct à la pathologie (non validée) : {pathology_name}"
            
            if patient_id and form_data:  # Sauvegarder seulement s'il y a des critères cochés
                patient = Patient.objects.get(id=patient_id)
                
                # Récupérer le médecin si disponible
                medecin = None
                if medecin_id:
                    try:
                        from .models import Medecin
                        medecin = Medecin.objects.get(id=medecin_id)
                    except Medecin.DoesNotExist:
                        pass
                
                # Créer la consultation avec statut "non_valide"
                consultation = Consultation.objects.create(
                    patient=patient,
                    medecin=medecin,
                    description_clinique=query,
                    pathologie_identifiee=pathology_name,
                    score_similarite=similarity_score / 100,
                    fichier_source=result.get('file_name', ''),
                    criteres_valides=form_data,  # Sauvegarder les critères cochés même si non validé
                    plan_traitement='',  # Pas de plan de traitement car non validé
                    statut='non_valide'  # Statut spécial pour les pathologies rejetées
                )
                
                print(f"✅ Consultation NON VALIDÉE sauvegardée (ID: {consultation.id}) avec {len(form_data)} critères")
                
                # Extraire les symptômes des critères pour les sauvegarder dans l'historique
                symptoms = []
                for key, value in form_data.items():
                    if isinstance(value, list):
                        symptoms.extend([f"{key}: {item}" for item in value])
                    else:
                        symptoms.append(f"{key}: {value}")
                
                # Ajouter les symptômes à l'historique du patient dans la session
                if 'patient_historical_symptoms' not in request.session:
                    request.session['patient_historical_symptoms'] = []
                request.session['patient_historical_symptoms'].extend(symptoms)
                request.session.modified = True
                print(f"📊 {len(symptoms)} symptômes ajoutés à l'historique du patient")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde de la consultation non validée: {e}")
        
        # Retourner à la page des résultats au lieu de passer au suivant
        return JsonResponse({
            'success': True,
            'action': 'back_to_results',
            'message': 'Pathologie non validée. Retour à la liste des résultats.'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Action invalide'
    }, status=400)


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
    
    # Formater le diagnostic pour l'affichage
    diagnosis_text = diagnosis_result.get('diagnosis', '')
    
    # Récupérer l'ID de consultation et du patient depuis la session
    consultation_id = diagnosis_data.get('consultation_id')
    patient_id = request.session.get('current_patient_id')
    
    context = {
        'diagnosis_id': diagnosis_id,
        'diagnosis': diagnosis_text,
        'pathology_name': diagnosis_result.get('pathology', ''),
        'confidence': diagnosis_result.get('confidence', 0),
        'timestamp': diagnosis_result.get('timestamp', ''),
        'result': result,
        'form_data': form_data,
        'success': diagnosis_result.get('success', False),
        'consultation_id': consultation_id,
        'patient_id': patient_id
    }
    
    return render(request, 'pathology_search/diagnosis.html', context)


def direct_pathology_access(request):
    """
    Accès direct à une pathologie avec validation intégrée.
    """
    from django.conf import settings
    from django.http import Http404
    from pathlib import Path
    
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
        
        # Récupérer les informations du patient pour le header
        from .models import Patient
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
    """
    Récupérer la liste de toutes les pathologies disponibles avec leurs pages HTML.
    """
    from pathlib import Path
    from django.conf import settings
    import os
    
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