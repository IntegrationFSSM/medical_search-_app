from django.contrib import admin
from .models import Medecin, Patient, Consultation


@admin.register(Medecin)
class MedecinAdmin(admin.ModelAdmin):
    list_display = ('numero_ordre', 'nom', 'prenom', 'specialite', 'telephone', 'email', 'date_creation')
    list_filter = ('specialite', 'date_creation')
    search_fields = ('nom', 'prenom', 'numero_ordre', 'specialite')
    ordering = ('nom', 'prenom')


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('numero_dossier', 'nom', 'prenom', 'date_naissance', 'telephone', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('nom', 'prenom', 'numero_dossier', 'telephone')
    ordering = ('nom', 'prenom')


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medecin', 'date_consultation', 'pathologie_identifiee', 'score_similarite', 'statut')
    list_filter = ('statut', 'date_consultation', 'medecin')
    search_fields = ('patient__nom', 'patient__prenom', 'medecin__nom', 'medecin__prenom', 'pathologie_identifiee', 'description_clinique')
    readonly_fields = ('id', 'date_creation', 'date_modification')
    ordering = ('-date_consultation',)
