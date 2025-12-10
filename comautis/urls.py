from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authen.urls')),
    path('forum/', include('forum.urls')),        # ← AJOUTÉ
    path('paiement/', include('paiement.urls')),  # ← AJOUTÉ
    path('accounts/', include('django.contrib.auth.urls')),  # ← AJOUTÉ
]