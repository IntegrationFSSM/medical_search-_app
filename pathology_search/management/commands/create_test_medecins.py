from django.core.management.base import BaseCommand
from pathology_search.models import Medecin


class Command(BaseCommand):
    help = 'Créer des médecins de test'

    def handle(self, *args, **options):
        medecins_data = [
            {
                'nom': 'BENNANI',
                'prenom': 'Ahmed',
                'specialite': 'Psychiatrie',
                'numero_ordre': 'MED-2025-001',
                'telephone': '+212 6 12 34 56 78',
                'email': 'a.bennani@clinique-lavallee.ma'
            },
            {
                'nom': 'ALAOUI',
                'prenom': 'Fatima',
                'specialite': 'Psychologie Clinique',
                'numero_ordre': 'MED-2025-002',
                'telephone': '+212 6 23 45 67 89',
                'email': 'f.alaoui@clinique-lavallee.ma'
            },
            {
                'nom': 'TAZI',
                'prenom': 'Mohammed',
                'specialite': 'Psychiatrie',
                'numero_ordre': 'MED-2025-003',
                'telephone': '+212 6 34 56 78 90',
                'email': 'm.tazi@clinique-lavallee.ma'
            },
            {
                'nom': 'KADIRI',
                'prenom': 'Sanaa',
                'specialite': 'Neuropsychiatrie',
                'numero_ordre': 'MED-2025-004',
                'telephone': '+212 6 45 67 89 01',
                'email': 's.kadiri@clinique-lavallee.ma'
            },
            {
                'nom': 'IDRISSI',
                'prenom': 'Karim',
                'specialite': 'Psychiatrie',
                'numero_ordre': 'MED-2025-005',
                'telephone': '+212 6 56 78 90 12',
                'email': 'k.idrissi@clinique-lavallee.ma'
            },
        ]

        created_count = 0
        for data in medecins_data:
            medecin, created = Medecin.objects.get_or_create(
                numero_ordre=data['numero_ordre'],
                defaults=data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Médecin créé: Dr. {medecin.nom} {medecin.prenom}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'○ Médecin existant: Dr. {medecin.nom} {medecin.prenom}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n{created_count} nouveaux médecins créés sur {len(medecins_data)} au total')
        )

