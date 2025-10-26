from django.core.management.base import BaseCommand
from pathology_search.models import Patient

class Command(BaseCommand):
    help = 'Supprime le patient ENNHILI YASSINE'
    
    def handle(self, *args, **kwargs):
        # Chercher le patient (ID 17: YASSINE Ennhili)
        self.stdout.write('🔍 Recherche du patient YASSINE Ennhili (ID: 17)...')
        
        patients = Patient.objects.filter(id=17)
        
        if not patients.exists():
            self.stdout.write(self.style.ERROR('❌ Aucun patient trouvé avec ce nom'))
            self.stdout.write('\n📋 Liste de tous les patients:')
            all_patients = Patient.objects.all()
            for p in all_patients:
                self.stdout.write(f'  - {p.id}: {p.nom} {p.prenom} ({p.numero_dossier})')
        else:
            for patient in patients:
                self.stdout.write(self.style.SUCCESS(f'Patient trouve: {patient.nom} {patient.prenom} (ID: {patient.id}, Dossier: {patient.numero_dossier})'))
                
                # Vérifier les consultations
                consultations_count = patient.consultations.count()
                self.stdout.write(f'   Nombre de consultations associees: {consultations_count}')
                
                # Supprimer
                patient_name = f"{patient.nom} {patient.prenom}"
                patient.delete()
                self.stdout.write(self.style.SUCCESS(f'Patient {patient_name} supprime avec succes (ainsi que ses {consultations_count} consultations)!'))

