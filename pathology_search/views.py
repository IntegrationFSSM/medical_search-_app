"""
Vues pour l'application de recherche de pathologies
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .services import PathologySearchService
import json


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
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'La requête ne peut pas être vide'
            }, status=400)
        
        # Effectuer la recherche
        service = PathologySearchService()
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


def view_pathology(request, html_path):
    """
    Afficher le contenu HTML d'une pathologie avec support i18n Django.
    """
    from django.conf import settings
    from django.http import HttpResponse, Http404
    from django.utils.translation import get_language
    import os
    
    try:
        # Détecter la langue active
        current_lang = get_language()  # 'fr', 'en', 'es', etc.
        
        # Construire le chemin avec la langue
        # Structure: Embedding/fr/..., Embedding/en/..., Embedding/es/...
        if current_lang and current_lang != 'fr':
            # Essayer d'abord avec la langue spécifique
            lang_path = os.path.join(settings.EMBEDDINGS_FOLDER, current_lang, html_path)
            if os.path.exists(lang_path):
                full_path = lang_path
            else:
                # Fallback sur français si traduction non disponible
                full_path = os.path.join(settings.EMBEDDINGS_FOLDER, 'fr', html_path)
                if not os.path.exists(full_path):
                    # Fallback final sur le chemin original (sans sous-dossier langue)
                    full_path = os.path.join(settings.EMBEDDINGS_FOLDER, html_path)
        else:
            # Français : chercher dans fr/ puis à la racine
            full_path = os.path.join(settings.EMBEDDINGS_FOLDER, 'fr', html_path)
            if not os.path.exists(full_path):
                full_path = os.path.join(settings.EMBEDDINGS_FOLDER, html_path)
        
        # Vérifier que le fichier existe
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
                
                # Injecter un bandeau de navigation en haut (sans bouton "Passer au suivant")
                navigation_header = f"""
                <div style="position: sticky; top: 0; z-index: 1000; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0; font-size: 18px;">
                                <i class="fas fa-clipboard-check"></i> Validation - Résultat {current_index + 1}/{len(results)}
                            </h3>
                            <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Requête: {query}</p>
                        </div>
                        <a href="/" style="background: rgba(255,255,255,0.2); color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                            <i class="fas fa-home"></i> Accueil
                        </a>
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
    pathology_name = current_result.get('file_name', '').replace('.txt', '').replace('_', ' ')
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
    
    results = request.session.get('search_results', [])
    
    if action == 'validate':
        # L'utilisateur a validé ce résultat
        result = results[current_index]
        pathology_name = result.get('file_name', '').replace('.txt', '').replace('_', ' ')
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
    
    context = {
        'diagnosis_id': diagnosis_id,
        'diagnosis': diagnosis_text,
        'pathology_name': diagnosis_result.get('pathology', ''),
        'confidence': diagnosis_result.get('confidence', 0),
        'timestamp': diagnosis_result.get('timestamp', ''),
        'result': result,
        'form_data': form_data,
        'success': diagnosis_result.get('success', False)
    }
    
    return render(request, 'pathology_search/diagnosis.html', context)