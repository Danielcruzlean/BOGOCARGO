from django.contrib import admin
# Importamos todos los modelos
from .models import (
    Usuarios, Localidades, Empresas, Productos, Pedidos, DetallePedido, 
    Vehiculos, ConductoresZonas, Envios, RastreoEnvio, Asignaciones
)
from django.contrib.auth.admin import UserAdmin

# ==============================================================================
# 1. MODELO USUARIOS (Custom User)
# ==============================================================================

class CustomUserAdmin(UserAdmin):
    # Campos a mostrar en la lista del administrador
    list_display = (
        'email', 'nombre', 'apellido', 'tipo', 'disponibilidad', 
        'is_staff', 'is_active'
    )
    # Campos para filtrar la lista
    list_filter = ('is_staff', 'is_active', 'tipo', 'disponibilidad')
    # Campos de búsqueda
    search_fields = ('email', 'nombre', 'apellido', 'telefono')
    
    # Campo para la contraseña debe usarse un widget de password
    # Nota: Si omites 'password' de add_fieldsets, Django lo agregará automáticamente.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'nombre', 'apellido', 'tipo', 'telefono'),
        }),
    )
    
    # Campos para editar un usuario existente
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'apellido', 'telefono', 'tipo', 'disponibilidad')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'fecha_registro')}),
    )
    ordering = ('email',)

# Registro del Custom User Admin
admin.site.register(Usuarios, CustomUserAdmin)

# ==============================================================================
# 2. OTROS MODELOS
# ==============================================================================

@admin.register(Localidades)
class LocalidadesAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_postal')
    search_fields = ('nombre',)

@admin.register(Empresas)
class EmpresasAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nit', 'tipo', 'usuario')
    list_filter = ('tipo', 'ciudad')
    search_fields = ('nombre', 'nit', 'usuario__email')
    # Optimización para FK que apuntan a modelos grandes
    raw_id_fields = ('usuario',) 

@admin.register(Productos)
class ProductosAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'peso_kg', 'precio')
    list_filter = ('empresa__tipo',)
    search_fields = ('nombre', 'empresa__nombre')
    raw_id_fields = ('empresa',)


# 3. Modelos con Inlines (Relaciones uno a muchos)

# Inline para DetallePedido, permite editar el detalle DENTRO del formulario de Pedidos
class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0 # Inicia con 0