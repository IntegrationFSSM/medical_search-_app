#!/usr/bin/env python3
"""Script pour vérifier les données d'un patient"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_search.settings')
django.setup()

from pathology_search.models import Patient

# Chercher le patient
print("Verification des patients avec email...")
patients = Patient.objects.filter(email__icontains='ennhili')

if not patients.exists():
    print("Aucun patient avec cet email")
    print("\nListe de tous les patients:")
    all_patients = Patient.objects.all()
    for p in all_patients:
        print(f"\n- ID: {p.id}")
        print(f"  Nom: {p.nom} {p.prenom}")
        print(f"  Dossier: {p.numero_dossier}")
        print(f"  Date naissance: {p.date_naissance}")
        print(f"  Telephone: {p.telephone}")
        print(f"  Email: {p.email}")
else:
    for patient in patients:
        print(f"\nPatient trouve:")
        print(f"  ID: {patient.id}")
        print(f"  Nom: {patient.nom} {patient.prenom}")
        print(f"  Dossier: {patient.numero_dossier}")
        print(f"  Date naissance: {patient.date_naissance}")
        print(f"  Telephone: {patient.telephone}")
        print(f"  Email: {patient.email}")

