"""
Commande Django pour créer des patients de test
Usage: python manage.py create_test_patients
"""
from django.core.management.base import BaseCommand
from pathology_search.models import Patient
from datetime import date


class Command(BaseCommand):
    help = 'Crée des patients de test dans la base de données'

    def handle(self, *args, **options):
        patients_data = [
            {
                'nom': 'ALAMI',
                'prenom': 'Mohammed',
                'date_naissance': date(1985, 3, 15),
                'numero_dossier': 'PAT-2025-001',
                'telephone': '0612345678',
                'email': 'mohammed.alami@email.com'
            },
            {
                'nom': 'BENJELLOUN',
                'prenom': 'Fatima',
                'date_naissance': date(1992, 7, 22),
                'numero_dossier': 'PAT-2025-002',
                'telephone': '0623456789',
                'email': 'fatima.benjelloun@email.com'
            },
            {
                'nom': 'CHAKIR',
                'prenom': 'Ahmed',
                'date_naissance': date(1978, 11, 8),
                'numero_dossier': 'PAT-2025-003',
                'telephone': '0634567890',
                'email': 'ahmed.chakir@email.com'
            },
            {
                'nom': 'EL IDRISSI',
                'prenom': 'Samira',
                'date_naissance': date(2000, 2, 14),
                'numero_dossier': 'PAT-2025-004',
                'telephone': '0645678901',
                'email': 'samira.elidrissi@email.com'
            },
            {
                'nom': 'FASSI',
                'prenom': 'Youssef',
                'date_naissance': date(1995, 5, 30),
                'numero_dossier': 'PAT-2025-005',
                'telephone': '0656789012',
                'email': 'youssef.fassi@email.com'
            },
            {
                'nom': 'GHARBI',
                'prenom': 'Laila',
                'date_naissance': date(1988, 9, 19),
                'numero_dossier': 'PAT-2025-006',
                'telephone': '0667890123',
                'email': 'laila.gharbi@email.com'
            },
            {
                'nom': 'HAJJI',
                'prenom': 'Karim',
                'date_naissance': date(1982, 12, 3),
                'numero_dossier': 'PAT-2025-007',
                'telephone': '0678901234',
                'email': 'karim.hajji@email.com'
            },
            {
                'nom': 'IDRISSI',
                'prenom': 'Nadia',
                'date_naissance': date(1990, 4, 25),
                'numero_dossier': 'PAT-2025-008',
                'telephone': '0689012345',
                'email': 'nadia.idrissi@email.com'
            }
        ]

        created_count = 0
        skipped_count = 0

        for patient_data in patients_data:
            patient, created = Patient.objects.get_or_create(
                numero_dossier=patient_data['numero_dossier'],
                defaults=patient_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Patient créé: {patient.nom_complet} ({patient.numero_dossier})'
                    )
                )
            else:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'○ Patient existe déjà: {patient.nom_complet} ({patient.numero_dossier})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Terminé ! {created_count} patients créés, {skipped_count} existants.'
            )
        )

