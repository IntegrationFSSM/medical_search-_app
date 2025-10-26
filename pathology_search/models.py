from django.db import models
from django.utils import timezone
import uuid


class Medecin(models.Model):
    """Modèle pour stocker les informations des médecins"""
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    specialite = models.CharField(max_length=100, verbose_name="Spécialité")
    numero_ordre = models.CharField(max_length=50, unique=True, verbose_name="Numéro d'ordre")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Médecin"
        verbose_name_plural = "Médecins"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"Dr. {self.nom} {self.prenom} - {self.specialite}"
    
    @property
    def nom_complet(self):
        return f"Dr. {self.prenom} {self.nom}"


class Patient(models.Model):
    """Modèle pour stocker les informations des patients"""
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    numero_dossier = models.CharField(max_length=50, unique=True, verbose_name="Numéro de dossier")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.numero_dossier})"
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class Consultation(models.Model):
    """Modèle pour stocker les consultations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    medecin = models.ForeignKey(Medecin, on_delete=models.SET_NULL, null=True, related_name='consultations', verbose_name="Médecin")
    date_consultation = models.DateTimeField(default=timezone.now, verbose_name="Date de consultation")
    description_clinique = models.TextField(verbose_name="Description clinique")
    
    # Résultats de la recherche
    pathologie_identifiee = models.CharField(max_length=200, verbose_name="Pathologie identifiée")
    score_similarite = models.FloatField(verbose_name="Score de similarité")
    fichier_source = models.CharField(max_length=500, blank=True)
    
    # Critères validés (stocké en JSON)
    criteres_valides = models.JSONField(default=dict, verbose_name="Critères diagnostiques validés")
    
    # Plan de traitement généré par IA
    plan_traitement = models.TextField(blank=True, verbose_name="Plan de traitement")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    statut = models.CharField(
        max_length=20, 
        choices=[
            ('en_cours', 'En cours'),
            ('valide', 'Validé'),
            ('archive', 'Archivé')
        ],
        default='en_cours'
    )
    
    class Meta:
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"
        ordering = ['-date_consultation']
    
    def __str__(self):
        return f"Consultation {self.patient.nom_complet} - {self.date_consultation.strftime('%d/%m/%Y')}"
