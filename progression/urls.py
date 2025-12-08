from django.urls import path
from . import views

app_name = "progression"

urlpatterns = [
    path("enfant/", views.progression_enfant, name="progression_enfant"),
]
