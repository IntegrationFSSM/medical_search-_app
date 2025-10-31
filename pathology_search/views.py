"""
Vues pour l'application de recherche de pathologies
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
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
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'La requête ne peut pas être vide'
            }, status=400)
        
        # Sauvegarder l'ID du patient et du médecin dans la session
        if patient_id:
            request.session['current_patient_id'] = patient_id
        if medecin_id:
            request.session['current_medecin_id'] = medecin_id
            request.session.modified = True
        
        # ÉTAPE 1: Valider la requête avec GPT-4o AVANT la recherche
        service = PathologySearchService()
        validation_result = service.validate_medical_query(query)
        
        if not validation_result['is_valid']:
            return JsonResponse({
                'success': False,
                'error': 'Requête non valide',
                'error_type': 'invalid_query',
                'reason': validation_result['reason']
            })
        
        # ÉTAPE 2: Si valide, effectuer la recherche
        search_results = service.find_best_match(
            query=query,
            top_k=top_k,
            aggregation=aggregation
        )
        
        # Si mode validation, sauvegarder dans la session
        if use_validation and search_results.get('success'):
            request.session['search_results'] = search_results['results']
            request.session['search_query'] = query
            return JsonResponse({
                'success': True,
                'use_validation': True,
                'redirect_url': '/validate/?index=0'
            })
        
        return JsonResponse(search_results)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la recherche: {str(e)}'
        }, status=500)


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
    """Récupérer l'historique des consultations d'un patient"""
    from .models import Patient, Consultation
    
    try:
        patient = Patient.objects.get(id=patient_id)
        consultations = Consultation.objects.filter(patient=patient).order_by('-date_consultation')
        
        consultations_data = [
            {
                'id': str(consultation.id),
                'date_consultation': consultation.date_consultation.strftime('%d/%m/%Y à %H:%M'),
                'pathologie_identifiee': clean_pathology_name(consultation.pathologie_identifiee),
                'medecin': consultation.medecin.nom_complet if consultation.medecin else 'Non renseigné',
                'statut': consultation.get_statut_display()
            }
            for consultation in consultations
        ]
        
        return JsonResponse({
            'success': True,
            'consultations': consultations_data,
            'patient': {
                'nom_complet': patient.nom_complet,
                'numero_dossier': patient.numero_dossier
            }
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


def view_pathology(request, html_path):
    """
    Afficher le contenu HTML d'une pathologie.
    """
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
        
        # Si chargé dans une iframe (mode validation), injecter le script de communication
        if request.GET.get('mode') == 'validation' or 'validate' in request.META.get('HTTP_REFERER', ''):
            # Script pour communiquer avec la page parent
            communication_script = """
            <script>
            // Intercepter les fonctions de validation pour communiquer avec la page parent
            (function() {
                const originalValider = window.validerFormulaire;
                const originalNonValider = window.nonValiderFormulaire;
                
                window.validerFormulaire = function() {
                    if (originalValider) originalValider();
                    // Envoyer message à la page parent
                    window.parent.postMessage({action: 'validate', source: 'pathology'}, '*');
                };
                
                window.nonValiderFormulaire = function() {
                    if (originalNonValider) originalNonValider();
                    // Envoyer message à la page parent
                    window.parent.postMessage({action: 'not_validate', source: 'pathology'}, '*');
                };
            })();
            </script>
            """
            # Injecter le script juste avant la fermeture du body
            html_content = html_content.replace('</body>', communication_script + '</body>')
        
        return HttpResponse(html_content)
        
    except Exception as e:
        raise Http404(f"Erreur lors du chargement de la page: {str(e)}")


def validate_results(request):
    """
    Page de validation des résultats avec navigation étape par étape.
    Affiche la page HTML complète de la pathologie avec injection des boutons de navigation.
    """
    from django.conf import settings
    from django.http import Http404
    import os
    
    # Récupérer les résultats depuis la session
    results = request.session.get('search_results', [])
    current_index = int(request.GET.get('index', 0))
    query = request.session.get('search_query', '')
    patient_id = request.session.get('current_patient_id')
    
    # Récupérer les informations du patient
    patient = None
    if patient_id:
        from .models import Patient
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
    if html_path:
        try:
            full_path = os.path.join(settings.EMBEDDINGS_FOLDER, html_path)
            
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Injecter un bandeau de navigation en haut avec informations patient
                patient_info_html = ""
                if patient:
                    patient_date_naissance = patient.date_naissance.strftime('%d/%m/%Y') if patient.date_naissance else 'Non renseignée'
                    patient_info_html = f"""
                    <div style="background: rgba(255,255,255,0.15); padding: 10px 15px; border-radius: 8px; margin-top: 10px;">
                        <div style="display: flex; gap: 20px; flex-wrap: wrap; font-size: 13px;">
                            <div><i class="fas fa-user"></i> <strong>Nom:</strong> {patient.nom}</div>
                            <div><i class="fas fa-user"></i> <strong>Prénom:</strong> {patient.prenom}</div>
                            <div><i class="fas fa-id-card"></i> {patient.numero_dossier}</div>
                            <div><i class="fas fa-calendar"></i> {patient_date_naissance}</div>
                            <div><i class="fas fa-phone"></i> {patient.telephone or 'Non renseigné'}</div>
                        </div>
                    </div>
                    """
                
                navigation_header = f"""
                <div style="position: sticky; top: 0; z-index: 1000; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="max-width: 1200px; margin: 0 auto;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <h3 style="margin: 0; font-size: 18px;">
                                    <i class="fas fa-clipboard-check"></i> Validation - Résultat {current_index + 1}/{len(results)}
                                </h3>
                                <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Requête: {query}</p>
                                {patient_info_html}
                            </div>
                            <a href="/" style="background: rgba(255,255,255,0.2); color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                                <i class="fas fa-home"></i> Accueil
                            </a>
                        </div>
                    </div>
                </div>
                """
                
                # Modifier les fonctions JavaScript pour rediriger vers Django
                if is_last:
                    # Dernier résultat : afficher message et retourner à l'accueil
                    next_action = """
                    Swal.fire({
                        icon: 'info',
                        title: 'Tous les résultats examinés',
                        html: '<p class="text-gray-600">Vous avez examiné tous les <strong>5 résultats</strong> disponibles.</p><p class="mt-2 text-gray-700">Aucune correspondance trouvée.</p>',
                        confirmButtonText: 'Retour à l\\'accueil',
                        confirmButtonColor: '#667eea',
                        showClass: {
                            popup: 'animate__animated animate__fadeInDown'
                        },
                        hideClass: {
                            popup: 'animate__animated animate__fadeOutUp'
                        }
                    }).then(() => {
                        window.location.href = '/';
                    });
                    """
                else:
                    # Passer au résultat suivant
                    next_action = f"""
                    Swal.fire({{
                        icon: 'warning',
                        title: 'Résultat non validé',
                        html: '<p class="text-gray-600">Passage au résultat suivant...</p><p class="mt-2 text-sm text-gray-500">Résultat <strong>{current_index + 2}/{len(results)}</strong></p>',
                        timer: 1500,
                        timerProgressBar: true,
                        showConfirmButton: false,
                        willClose: () => {{
                            window.location.href = '/validate/?index={current_index + 1}';
                        }}
                    }});
                    """
                
                script_modification = f"""
                <!-- SweetAlert2 CDN -->
                <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
                
                <script>
                // Cookie helper
                function getCookie(name) {{
                    let cookieValue = null;
                    if (document.cookie && document.cookie !== '') {{
                        const cookies = document.cookie.split(';');
                        for (let i = 0; i < cookies.length; i++) {{
                            const cookie = cookies[i].trim();
                            if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                break;
                            }}
                        }}
                    }}
                    return cookieValue;
                }}
                
                // Fonction pour capturer toutes les données du formulaire
                function captureFormData() {{
                    const formData = {{}};
                    
                    // Capturer tous les inputs cochés (checkboxes et radios)
                    const checkedInputs = document.querySelectorAll('input:checked');
                    checkedInputs.forEach(input => {{
                        const name = input.name || input.id || 'unnamed';
                        const value = input.value || input.nextSibling?.textContent?.trim() || 'checked';
                        
                        if (!formData[name]) {{
                            formData[name] = [];
                        }}
                        formData[name].push(value);
                    }});
                    
                    // Capturer les textarea
                    const textareas = document.querySelectorAll('textarea');
                    textareas.forEach(textarea => {{
                        if (textarea.value) {{
                            formData[textarea.name || textarea.id || 'notes'] = textarea.value;
                        }}
                    }});
                    
                    // Capturer les select
                    const selects = document.querySelectorAll('select');
                    selects.forEach(select => {{
                        if (select.value) {{
                            formData[select.name || select.id] = select.selectedOptions[0].text;
                        }}
                    }});
                    
                    return formData;
                }}
                
                // Remplacer les fonctions IMMÉDIATEMENT (avant DOMContentLoaded)
                window.validerFormulaire = function() {{
                    // Capturer les données du formulaire
                    const formData = captureFormData();
                    
                    // Étape 1: Confirmation de validation
                    Swal.fire({{
                        icon: 'success',
                        title: 'Validation confirmée !',
                        html: '<p class="text-gray-600">Préparation de la génération du diagnostic...</p>',
                        timer: 800,
                        timerProgressBar: true,
                        showConfirmButton: false,
                        didOpen: () => {{
                            Swal.showLoading();
                        }}
                    }}).then(() => {{
                        // Étape 2: Génération du diagnostic avec barre de progression
                        let progress = 0;
                        let progressText = [
                            '📋 Analyse des critères diagnostiques...',
                            '📚 Consultation de la documentation DSM-5-TR...',
                            '💊 Génération du plan de traitement...',
                            '✨ Finalisation des recommandations médicales...'
                        ];
                        let currentStep = 0;
                        
                        Swal.fire({{
                            title: 'Génération du Plan de Traitement',
                            html: `
                                <div style="padding: 20px;">
                                    <div id="progress-text" style="font-size: 16px; margin-bottom: 20px; color: #667eea; font-weight: bold;">
                                        ${{progressText[0]}}
                                    </div>
                                    <div style="background: #e5e7eb; border-radius: 10px; height: 30px; overflow: hidden;">
                                        <div id="progress-bar" style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: 0%; transition: width 0.5s ease; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px;">
                                            <span id="progress-percent">0%</span>
                                        </div>
                                    </div>
                                    <div style="margin-top: 15px; font-size: 14px; color: #6b7280;">
                                        <i class="fas fa-pills"></i> Génération basée sur la documentation médicale DSM-5-TR...
                                    </div>
                                </div>
                            `,
                            allowOutsideClick: false,
                            allowEscapeKey: false,
                            showConfirmButton: false,
                            didOpen: () => {{
                                const progressBar = document.getElementById('progress-bar');
                                const progressPercent = document.getElementById('progress-percent');
                                const progressTextEl = document.getElementById('progress-text');
                                
                                // Animation de progression
                                const progressInterval = setInterval(() => {{
                                    progress += 2;
                                    if (progress > 95) {{
                                        clearInterval(progressInterval);
                                    }}
                                    
                                    progressBar.style.width = progress + '%';
                                    progressPercent.textContent = progress + '%';
                                    
                                    // Changer le texte selon la progression
                                    if (progress > 75 && currentStep < 3) {{
                                        currentStep = 3;
                                        progressTextEl.textContent = progressText[3];
                                    }} else if (progress > 50 && currentStep < 2) {{
                                        currentStep = 2;
                                        progressTextEl.textContent = progressText[2];
                                    }} else if (progress > 25 && currentStep < 1) {{
                                        currentStep = 1;
                                        progressTextEl.textContent = progressText[1];
                                    }}
                                }}, 150);
                            }}
                        }});
                        
                        // Envoi de la requête au backend
                        fetch('/validate/action/', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCookie('csrftoken')
                            }},
                            body: JSON.stringify({{
                                action: 'validate',
                                current_index: {current_index},
                                form_data: formData
                            }})
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success && data.action === 'validated') {{
                                // Compléter la barre à 100%
                                const progressBar = document.getElementById('progress-bar');
                                const progressPercent = document.getElementById('progress-percent');
                                const progressTextEl = document.getElementById('progress-text');
                                
                                if (progressBar) {{
                                    progressBar.style.width = '100%';
                                    progressPercent.textContent = '100%';
                                    progressTextEl.innerHTML = '✅ Plan de traitement généré avec succès !';
                                }}
                                
                                // Attendre un peu avant de rediriger
                                setTimeout(() => {{
                                    window.location.href = '/diagnosis/' + data.diagnosis_id + '/';
                                }}, 1000);
                            }} else {{
                                Swal.fire({{
                                    icon: 'error',
                                    title: 'Erreur',
                                    text: 'Une erreur est survenue lors de la génération du plan de traitement.',
                                    confirmButtonColor: '#667eea'
                                }});
                            }}
                        }})
                        .catch(error => {{
                            console.error('Erreur:', error);
                            Swal.fire({{
                                icon: 'error',
                                title: 'Erreur de Connexion',
                                text: 'Impossible de se connecter au serveur. Vérifiez votre connexion internet.',
                                confirmButtonColor: '#667eea'
                            }});
                        }});
                    }});
                }};
                
                window.nonValiderFormulaire = function() {{
                    {next_action}
                }};
                </script>
                """
                
                # Injecter le header après <body> et le script avant </body>
                html_content = html_content.replace('<body>', '<body>' + navigation_header, 1)
                html_content = html_content.replace('</body>', script_modification + '</body>', 1)
                
                from django.http import HttpResponse
                return HttpResponse(html_content)
                
        except Exception as e:
            pass
    
    # Si pas de HTML, afficher le template de base
    pathology_name = clean_pathology_name(current_result.get('file_name', '').replace('.txt', ''))
    context = {
        'result': current_result,
        'pathology_name': pathology_name,
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
        
        # Générer le diagnostic IA avec OpenAI en incluant le texte médical
        from .services import PathologySearchService
        service = PathologySearchService()
        
        diagnosis_result = service.generate_ai_diagnosis(
            pathology_name=pathology_name,
            form_data=form_data,
            similarity_score=similarity_score,
            medical_text=best_chunk_text
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
        # Passer au résultat suivant
        next_index = current_index + 1
        
        if next_index >= len(results):
            # Plus de résultats
            return JsonResponse({
                'success': True,
                'action': 'completed',
                'message': 'Tous les résultats ont été examinés.'
            })
        
        return JsonResponse({
            'success': True,
            'action': 'next',
            'next_index': next_index
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
            'medecin_id': request.session.get('current_medecin_id')
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