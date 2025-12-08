from django.contrib import admin
from django.urls import path, include   # <-- IMPORT ESSENTIEL

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authen.urls')),
]
