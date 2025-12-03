from django.contrib import admin
from django.urls import path, include 

urlpatterns = [
    # Rutas de administración de Django
    path('admin/', admin.site.urls),
    
    # Rutas de autenticación (login, logout, etc.)
    path('auth/', include('django.contrib.auth.urls')),
    
    # Rutas del Frontend (Interfaz de usuario del Minorista)
    # Accesibles desde la raíz del sitio (e.g., /crear-pedido/)
    path('', include('FRONTEND.urls')),
    
    # Rutas del Backend/API (Para servicios web y peticiones asíncronas)
    # Accesibles bajo el prefijo /api/
    path('api/', include('BACKEND.urls')),
]