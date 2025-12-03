from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

# Obtener el modelo de usuario personalizado (Usuarios)
Usuarios = get_user_model()

# Define las opciones de roles (Se asumen los mismos roles que Usuarios.tipo)
ROLE_CHOICES = (
    ('MINORISTA', 'Minorista (Necesito hacer envíos)'),
    ('CONDUCTOR', 'Transportista (Ofrezco servicios de carga)'),
    ('ADMIN', 'Administrador de Cuenta'),
)

class PerfilUsuario(models.Model):
    """
    Modelo que extiende el modelo de usuario con campos adicionales y gestiona el rol.
    Se sincroniza con el campo 'tipo' del modelo Usuarios.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfilusuario'
    )

    # El campo 'role' almacena la misma información que Usuarios.tipo, pero centralizada aquí.
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='MINORISTA',
        verbose_name="Rol del Usuario"
    )

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

    def __str__(self):
        # Muestra el email del usuario y la descripción legible de su rol
        return f'{self.user.email} - {self.get_role_display()}'

# -------------------------------------------------------------
# --- Señales para asegurar la creación y sincronización del perfil ---
# -------------------------------------------------------------

@receiver(post_save, sender=Usuarios)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """
    Crea un PerfilUsuario automáticamente cuando se crea un objeto Usuarios,
    o guarda/sincroniza el perfil si el usuario se actualiza.
    """
    initial_role = getattr(instance, 'tipo', 'MINORISTA')
    
    # 1. Lógica de creación (Usuario nuevo o perfil faltante)
    if created:
        PerfilUsuario.objects.create(user=instance, role=initial_role)
    
    # 2. Lógica de actualización (Usuario existente)
    try:
        # Sincronizar el campo 'role' con el campo 'tipo' del usuario
        profile = instance.perfilusuario
        if profile.role != initial_role:
            profile.role = initial_role
            profile.save(update_fields=['role'])
            
    except PerfilUsuario.DoesNotExist:
        # 3. Lógica de recreación (El perfil fue borrado, pero el usuario no)
        # Esto soluciona el bloque de código que preguntaste:
        PerfilUsuario.objects.create(user=instance, role=initial_role)