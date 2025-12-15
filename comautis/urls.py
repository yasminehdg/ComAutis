from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('authen.urls')),
    path('admin/', admin.site.urls),
    path('forum/', include('forum.urls')),
    path('paiement/', include('paiement.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)