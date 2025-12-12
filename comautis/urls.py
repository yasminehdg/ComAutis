from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('authen.urls')),
    path('admin/', admin.site.urls),
    path('forum/', include('forum.urls')),        # ← AJOUTÉ
    path('paiement/', include('paiement.urls')),  # ← AJOUTÉ
    path('accounts/', include('django.contrib.auth.urls')),  # ← AJOUTÉ
]