from django.shortcuts import render

def progression_enfant(request):
    context = {
        "nom_enfant": "Lina",
        "niveau_actuel": "Niveau 2",
        "activites_terminees": 5,
        "activites_totales": 10,
    }
    return render(request, "progression/progression_enfant.html", context)
