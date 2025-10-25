#!/usr/bin/env python
"""
Script pour supprimer tous les patients avec numéro PAT-2025-XXX
"""
import os
import sys
import django

# Configuration Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_search.settings')
django.setup()

from pathology_search.models import Patient

def delete_pat_patients():
    """Supprimer tous les patients avec numéro PAT-2025-XXX"""
    
    # Trouver tous les patients avec PAT
    pat_patients = Patient.objects.filter(numero_dossier__startswith='PAT-2025-')
    
    count = pat_patients.count()
    
    if count == 0:
        print("✓ Aucun patient PAT trouvé")
        return
    
    print(f"🔍 {count} patient(s) PAT trouvé(s):")
    for patient in pat_patients:
        print(f"   - {patient.nom_complet} ({patient.numero_dossier})")
    
    # Supprimer
    pat_patients.delete()
    print(f"\n✅ {count} patient(s) PAT supprimé(s) avec succès!")
    
    # Vérifier les patients restants
    remaining = Patient.objects.all()
    print(f"\n📊 Patients restants: {remaining.count()}")
    for patient in remaining:
        print(f"   ✓ {patient.nom_complet} ({patient.numero_dossier})")

if __name__ == '__main__':
    delete_pat_patients()

