"""
URLs pour l'application pathology_search
"""
from django.urls import path
from . import views

app_name = 'pathology_search'

urlpatterns = [
    path('', views.index, name='index'),
    path('patient/new/', views.create_patient_page, name='create_patient_page'),
    path('patient/create/', views.create_patient_submit, name='create_patient_submit'),
    path('search/', views.search, name='search'),
    path('about/', views.about, name='about'),
    path('results-selection/', views.results_selection, name='results_selection'),
    path('validate/', views.validate_results, name='validate_results'),
    path('validate/action/', views.validate_action, name='validate_action'),
    path('pathology/<path:html_path>/', views.view_pathology, name='view_pathology'),
    path('diagnosis/<str:diagnosis_id>/', views.show_diagnosis, name='show_diagnosis'),
    # Actions sur le plan de traitement
    path('consultation/<uuid:consultation_id>/validate/', views.validate_treatment_plan, name='validate_treatment_plan'),
    path('consultation/<uuid:consultation_id>/modify/', views.modify_treatment_plan, name='modify_treatment_plan'),
    path('consultation/<uuid:consultation_id>/delete/', views.delete_consultation, name='delete_consultation'),
    # API Patients
    path('api/patients/', views.get_patients, name='get_patients'),
    path('api/patients/create/', views.create_patient, name='create_patient'),
    path('api/patients/<int:patient_id>/history/', views.get_patient_history, name='get_patient_history'),
    # API Médecins
    path('api/medecins/', views.get_medecins, name='get_medecins'),
    path('api/medecins/create/', views.create_medecin, name='create_medecin'),
    # API Pathologies
    path('api/pathologies/', views.get_all_pathologies, name='get_all_pathologies'),
    path('direct-access/', views.direct_pathology_access, name='direct_pathology_access'),
    # Rapports et historique
    path('print/<uuid:consultation_id>/', views.print_report, name='print_report'),
    path('patient/<int:patient_id>/history/', views.patient_history, name='patient_history'),
]

