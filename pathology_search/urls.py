"""
URLs pour l'application pathology_search
"""
from django.urls import path
from . import views

app_name = 'pathology_search'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('about/', views.about, name='about'),
    path('validate/', views.validate_results, name='validate_results'),
    path('validate/action/', views.validate_action, name='validate_action'),
    path('pathology/<path:html_path>/', views.view_pathology, name='view_pathology'),
    path('diagnosis/<str:diagnosis_id>/', views.show_diagnosis, name='show_diagnosis'),
    # API Patients
    path('api/patients/', views.get_patients, name='get_patients'),
    path('api/patients/create/', views.create_patient, name='create_patient'),
]

