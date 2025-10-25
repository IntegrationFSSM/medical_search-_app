from django.contrib import admin
from .models import Patient, Consultation


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('numero_dossier', 'nom', 'prenom', 'date_naissance', 'telephone', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('nom', 'prenom', 'numero_dossier', 'telephone')
    ordering = ('nom', 'prenom')


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'date_consultation', 'pathologie_identifiee', 'score_similarite', 'statut')
    list_filter = ('statut', 'date_consultation')
    search_fields = ('patient__nom', 'patient__prenom', 'pathologie_identifiee', 'description_clinique')
    readonly_fields = ('id', 'date_creation', 'date_modification')
    ordering = ('-date_consultation',)
