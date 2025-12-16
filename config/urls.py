# config/urls.py

from django.contrib import admin
from django.urls import path, include 

urlpatterns = [
    # Rutas de administración de Django (panel automático)
    path('admin/', admin.site.urls),
    
    # Rutas de autenticación de Django 
    path('auth/', include('django.contrib.auth.urls')),
    
    # Rutas del Frontend
    # ✅ CORRECCIÓN APLICADA: 'FRONTEND.urls' cambiado a 'frontend.urls'
    path('', include('FRONTEND.urls')),
    
    # Rutas del Backend/API 
    # Mantengo 'BACKEND.urls', asumiendo que el nombre de esa app es en mayúsculas.
    path('api/', include('BACKEND.urls')), 
]
