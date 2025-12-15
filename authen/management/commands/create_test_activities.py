from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from authen.models import Enfant, Activite

class Command(BaseCommand):
    help = 'Crée des activités de test pour tous les enfants'

    def handle(self, *args, **kwargs):
        enfants = Enfant.objects.all()
        
        if not enfants.exists():
            self.stdout.write(self.style.ERROR('Aucun enfant trouvé !'))
            return
        
        jeux_disponibles = [
            'memory', 'compter_3', 'compter_10', 'couleurs', 
            'emotions', 'animaux', 'fruits', 'puzzle', 'labyrinthe'
        ]
        
        for enfant in enfants:
            self.stdout.write(f'\n📊 Création d\'activités pour {enfant.prenom}...')
            
            # Créer 20 activités sur les 7 derniers jours
            for i in range(20):
                jours_avant = random.randint(0, 7)
                heures_avant = random.randint(0, 23)
                
                date_debut = timezone.now() - timedelta(days=jours_avant, hours=heures_avant)
                duree = random.randint(5, 30)  # Entre 5 et 30 minutes
                date_fin = date_debut + timedelta(minutes=duree)
                
                jeu = random.choice(jeux_disponibles)
                reussi = random.choice([True, True, True, False])  # 75% de réussite
                score = random.randint(60, 100) if reussi else random.randint(30, 60)
                
                Activite.objects.create(
                    enfant=enfant,
                    jeu=jeu,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    duree_minutes=duree,
                    score=score,
                    reussi=reussi
                )
            
            self.stdout.write(self.style.SUCCESS(f'✅ 20 activités créées pour {enfant.prenom}'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Toutes les activités de test ont été créées !'))