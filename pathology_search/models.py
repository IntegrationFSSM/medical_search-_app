from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
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
    
    # Identifiants
    patient_identifier = models.CharField(
        max_length=50, 
        unique=True, 
        null=True, 
        blank=True, 
        verbose_name="Identifiant patient"
    )
    
    cin_validator = RegexValidator(
        regex=r'^[A-Z]{1,2}\d{5,10}$',
        message="Format CIN invalide (ex: AB123456)"
    )
    cin = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True, 
        validators=[cin_validator],
        verbose_name="N° CIN"
    )
    
    passport_number = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True, 
        verbose_name="N° de passeport"
    )
    
    # Informations personnelles
    last_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="Nom"
    )
    
    first_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="Prénom"
    )
    
    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES, 
        null=True, 
        blank=True, 
        verbose_name="Sexe"
    )
    
    birth_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Date de naissance"
    )
    
    nationality = models.CharField(
        max_length=2, 
        blank=True, 
        default='MA',
        verbose_name="Nationalité (code ISO)"
    )
    
    profession = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Profession"
    )
    
    city = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Ville"
    )
    
    email = models.EmailField(
        max_length=254, 
        blank=True, 
        verbose_name="Email"
    )
    
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="Téléphone fixe"
    )
    
    mobile_number = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="GSM"
    )
    
    spouse_name = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Conjoint(e)"
    )
    
    # Informations médicales
    treating_physician = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="Médecin traitant"
    )
    
    referring_physician = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="Médecin correspondant"
    )
    
    disease_speciality = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="Type maladie"
    )
    
    # Assurance
    has_insurance = models.BooleanField(
        default=False, 
        verbose_name="A une mutuelle/assurance"
    )
    
    insurance_number = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name="N° immatriculation"
    )
    
    affiliation_number = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name="N° affiliation"
    )
    
    # Champs de compatibilité (anciens noms)
    nom = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nom (compatibilité)")
    prenom = models.CharField(max_length=100, null=True, blank=True, verbose_name="Prénom (compatibilité)")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance (compatibilité)")
    numero_dossier = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro de dossier (compatibilité)")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone (compatibilité)")
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        nom = self.last_name or self.nom or ''
        prenom = self.first_name or self.prenom or ''
        dossier = self.patient_identifier or self.numero_dossier or 'N/A'
        return f"{prenom} {nom} ({dossier})"
    
    @property
    def nom_complet(self):
        nom = self.last_name or self.nom or ''
        prenom = self.first_name or self.prenom or ''
        return f"{prenom} {nom}"


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
    
    # Plan de traitement validé par le médecin (version finale pour le rapport)
    plan_traitement_valide = models.TextField(blank=True, verbose_name="Plan de traitement validé")
    
    # Notes optionnelles du médecin pour le rapport
    notes_medecin = models.TextField(blank=True, verbose_name="Notes du médecin")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    statut = models.CharField(
        max_length=20, 
        choices=[
            ('en_cours', 'En cours'),
            ('valide', 'Validé'),
            ('non_valide', 'Non validé'),
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
