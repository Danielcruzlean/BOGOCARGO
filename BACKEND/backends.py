from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailAuthBackend(ModelBackend):
    """
    Backend de autenticación personalizado.
    Permite autenticar usuarios usando el campo 'email' como identificador
    en lugar del campo 'username' por defecto.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        # El valor que recibimos como 'username' es en realidad el email.
        email = username 

        if email is None:
            email = kwargs.get(UserModel.USERNAME_FIELD)
        
        try:
            # 1. Buscar al usuario por el email (que es la clave de autenticación)
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            # Si el usuario no existe con ese email, retornamos None
            return None

        # 2. Verificar la contraseña
        if user.check_password(password):
            return user
        return None
        
    def get_user(self, user_id):
        """Método necesario para la gestión de sesiones."""
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None