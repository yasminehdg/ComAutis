from django.db import models
from django.contrib.auth.models import User
import random

ICON_CHOICES = ['book', 'love', 'chat', 'star', 'autumn', 'pencil']

class Topic(models.Model):
    title = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    icon = models.CharField(max_length=20, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.icon:
            self.icon = random.choice(ICON_CHOICES)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.created_by} - {self.content[:30]}'
