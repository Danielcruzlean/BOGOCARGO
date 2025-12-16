from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
# Importamos Pedidos y Factura desde la ubicación correcta: FRONTEND
from FRONTEND.models import Pedidos, Factura 


# 1. Obtener el modelo de usuario personalizado.
# Nota: Si el AUTH_USER_MODEL en settings.py dice 'FRONTEND.Usuarios', 
# get_user_model() ahora buscará y encontrará el modelo en FRONTEND.
Usuarios = get_user_model()


# 2. Clases para mostrar el detalle del Usuario en el Admin (Customización)
class CustomUsuariosAdmin(UserAdmin):
    # Definir los campos que se muestran en el listado
    list_display = ('email', 'nombre', 'apellido', 'tipo', 'is_staff', 'is_active')
    
    # Definir los campos para la edición/creación del usuario
    # ¡IMPORTANTE! Debes añadir los campos de vehículo para que se muestren aquí si los quieres administrar.
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'apellido', 'tipo')}),
        # --- NUEVOS CAMPOS DEL VEHÍCULO ---
        ('Datos del Vehículo', {'fields': ('placas', 'marca_vehiculo', 'referencia_vehiculo', 'tipo_vehiculo')}),
        # ----------------------------------
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'tipo')
    search_fields = ('email', 'nombre', 'apellido')
    ordering = ('email',)


# 3. Registrar los modelos
# Desregistrar el UserAdmin por defecto si ya lo registraste
try:
    admin.site.unregister(Usuarios)
except admin.sites.NotRegistered:
    pass

# Registra tu modelo Usuarios con la configuración personalizada
admin.site.register(Usuarios, CustomUsuariosAdmin) 

# Registrar Pedidos y Factura
admin.site.register(Pedidos)
admin.site.register(Factura)