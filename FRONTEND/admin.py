from django.contrib import admin
from .models import PerfilUsuario

# Opcional: Para mostrar el perfil junto al usuario en el Admin
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'

# Opcional: Si quieres modificar cómo se ve tu modelo de Usuario en el admin,
# puedes añadir PerfilUsuarioInline a la clase Admin de tu modelo Usuarios.
# Ejemplo (asumiendo que tu usuario personalizado se llama 'Usuarios'):

# from django.contrib.auth.admin import UserAdmin
# from django.contrib.auth import get_user_model
# Usuarios = get_user_model()

# class UsuariosAdmin(UserAdmin):
#     inlines = (PerfilUsuarioInline,)

# admin.site.register(Usuarios, UsuariosAdmin)

# Alternativa simple: Registrar solo el PerfilUsuario
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'get_role_display')
    search_fields = ('user__email', 'role')
    list_filter = ('role',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
