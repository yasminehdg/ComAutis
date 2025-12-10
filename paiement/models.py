from django.db import models
from django.contrib.auth.models import User

class Level(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.price}€"

    class Meta:
        verbose_name = "Niveau d'abonnement"
        verbose_name_plural = "Niveaux d'abonnement"


class Subscription(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    simulated_payment_id = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.parent.username} - {self.level.name} - {'Actif' if self.active else 'Inactif'}"

    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['-start_date']