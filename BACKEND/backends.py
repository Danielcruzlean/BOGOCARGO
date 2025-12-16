# BACKEND/backends.py

from django.contrib.auth.backends import BaseBackend 
from django.contrib.auth import get_user_model
from django.db.models import Q 

UserModel = get_user_model()

class EmailAuthBackend(BaseBackend): 
    """
    Backend de autenticación personalizado, puro.
    Autentica usuarios usando el campo 'email' como identificador.
    """
    def authenticate(self, request, email=None, password=None, **kwargs):
        
        # Unificar el identificador, que siempre debería ser 'email'
        if email is None:
            email = kwargs.get('email')
        
        if not email:
            return None
        
        try:
            # Buscar al usuario por el email (case-insensitive)
            # Nota: Si usas Q, debes importar Q de django.db.models
            user = UserModel.objects.get(email__iexact=email) 
        except UserModel.DoesNotExist:
            return None

        # 1. Verificar la contraseña
        if user.check_password(password):
            
            # 2. Verificar el estado de la cuenta (is_active)
            if user.is_active:
                # 🎯 ÉXITO: Credenciales correctas y usuario activo.
                return user
            else:
                # Usuario inactivo (credenciales correctas, pero no puede iniciar sesión)
                return None
        
        # 3. Contraseña incorrecta
        return None
        
    def get_user(self, user_id):
        """Método necesario para la gestión de sesiones."""
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None