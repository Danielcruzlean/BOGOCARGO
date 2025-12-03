# BACKEND/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _ 

# === Custom User Manager (Gestor de Usuarios) ===
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El Email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        # 💡 ROL ADMINISTRADOR ASIGNADO AL SUPERUSUARIO
        extra_fields.setdefault('tipo', 'ADMIN') 
        
        # Validaciones de superusuario
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

# ==============================================================================
# 1. TABLA USUARIOS (MODELO DE AUTENTICACIÓN)
# ==============================================================================
class Usuarios(AbstractBaseUser, PermissionsMixin):
    TIPO_CHOICES = [
        ('MINORISTA', 'Minorista'),
        ('CONDUCTOR', 'Conductor'),
        ('ADMIN', 'Administrador'),
    ]
    DISPONIBILIDAD_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('EN_RUTA', 'En Ruta'),
        ('DESCANSO', 'Descanso'),
    ]

    email = models.EmailField(max_length=120, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='MINORISTA')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    disponibilidad = models.CharField(max_length=20, choices=DISPONIBILIDAD_CHOICES, default='DISPONIBLE')
    fecha_registro = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'tipo']
    
    # CORRECCIÓN DE CONFLICTO E304 (Custom User Model)
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
        related_name="custom_user_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_permissions",
        related_query_name="user",
    )

    class Meta:
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.nombre} {self.apellido}"

# ==============================================================================
# OTRAS TABLAS
# ==============================================================================

class Localidades(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Localidades"
    
    def __str__(self):
        return self.nombre

class Empresas(models.Model):
    TIPO_CHOICES = [
        ('MAYORISTA', 'Mayorista'),
        ('MINORISTA', 'Minorista'),
    ]
    nombre = models.CharField(max_length=150)
    nit = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    usuario = models.ForeignKey(
        Usuarios, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='empresas_asociadas'
    ) 
    
    class Meta:
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.nombre

class Productos(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    peso_kg = models.DecimalField(max_digits=10, decimal_places=2)
    
    altura_cm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ancho_cm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    largo_cm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    empresa = models.ForeignKey(Empresas, on_delete=models.CASCADE, related_name='productos_ofrecidos')

    class Meta:
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre

# ==============================================================================
# MODELOS DE PEDIDOS Y LOGÍSTICA
# ==============================================================================

class Pedidos(models.Model):
    # ⚠️ IMPORTANTE: Ejecutar makemigrations y migrate después de cualquier cambio en este modelo.
    
    # Renombrado de la variable para que coincida con el uso en views.py
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('ASIGNADO', 'Asignado'), 
        ('EN_TRANSITO', 'En Tránsito'), 
        ('COMPLETADO', 'Completado'), 
        ('CANCELADO', 'Cancelado'),
    ]
    
    minorista = models.ForeignKey(
        Usuarios, 
        on_delete=models.CASCADE, 
        related_name='pedidos_creados',
        help_text="Usuario minorista que solicita la carga."
    )
    
    conductor = models.ForeignKey(
        Usuarios, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pedidos_asignados',
        help_text="Conductor asignado al pedido."
    )
    
    origen = models.CharField(max_length=255, help_text="Dirección de recolección.")
    destino = models.CharField(max_length=255, help_text="Dirección de entrega.")
    
    # 📝 Nombre de campo CONFIRMADO: peso_total_kg
    peso_total_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.0, # <-- 🟢 CORRECCIÓN
        help_text="Peso total estimado de la carga en kg."
    )
    # 📝 Nombre de campo CONFIRMADO: descripcion_carga
    descripcion_carga = models.CharField(
        max_length=100, 
        default='Carga no especificada', # <-- 🟢 CORRECCIÓN
        help_text="Descripción general de la carga (ej: tipo, bultos)."
    ) 
    
    fecha_creacion = models.DateTimeField(default=timezone.now) 
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    

    class Meta:
        verbose_name_plural = "Pedidos"
        
    def __str__(self):
        return f"Pedido #{self.id} ({self.estado})"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedidos, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Productos, on_delete=models.CASCADE, related_name='detalles_en_pedidos')
    cantidad = models.IntegerField()

    class Meta:
        verbose_name_plural = "Detalles de Pedido"
        unique_together = ('pedido', 'producto')

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en Pedido #{self.pedido.id}"

class Vehiculos(models.Model):
    TIPO_CHOICES = [
        ('MOTO', 'Moto'),
        ('CAMIONETA', 'Camioneta'),
        ('CAMION', 'Camión'),
    ]
    placa = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    capacidad_kg = models.IntegerField()
    conductor = models.OneToOneField(
        Usuarios, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='vehiculo_asignado'
    ) 

    class Meta:
        verbose_name_plural = "Vehículos"
        
    def __str__(self):
        return f"{self.placa} ({self.tipo})"

class ConductoresZonas(models.Model):
    conductor = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name='zonas_asignadas')
    localidad = models.ForeignKey(Localidades, on_delete=models.CASCADE, related_name='conductores_asignados') 

    class Meta:
        verbose_name_plural = "Zonas de Conductores"
        unique_together = ('conductor', 'localidad')

    def __str__(self):
        return f"{self.conductor.nombre} -> {self.localidad.nombre}"

# ==============================================================================
# 💡 MODELO DE ASIGNACIONES (SOLUCIÓN DEL ERROR)
# ==============================================================================

class Asignaciones(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Asignación Pendiente'),
        ('ACEPTADA', 'Asignación Aceptada por Conductor'),
        ('RECHAZADA', 'Asignación Rechazada por Conductor'),
    ]
    
    pedido = models.ForeignKey(
        'Pedidos', 
        on_delete=models.CASCADE, 
        related_name='historial_asignaciones'
    )
    conductor = models.ForeignKey(
        'Usuarios', 
        on_delete=models.PROTECT, 
        limit_choices_to={'tipo': 'CONDUCTOR'}, # Solo permite conductores
        related_name='asignaciones_recibidas'
    )
    fecha_asignacion = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    
    class Meta:
        verbose_name_plural = "Asignaciones"
        ordering = ['-fecha_asignacion'] 
        
    def __str__(self):
        return f"Asignación {self.id} de Pedido {self.pedido.id} a {self.conductor.nombre}"


# ==============================================================================
# MODELOS DE LOGÍSTICA
# ==============================================================================

class Envios(models.Model):
    ESTADO_CHOICES = [
        ('ASIGNADO', 'Asignado'),
        ('EN_RUTA', 'En Ruta'),
        ('ENTREGADO', 'Entregado'),
        ('FALLIDO', 'Fallido'),
    ]
    # Un Envío está asociado a un Pedido de forma 1 a 1
    pedido = models.OneToOneField(Pedidos, on_delete=models.CASCADE, related_name='envio_asociado') 
    
    # Se recomienda SET_NULL para no perder el registro del envío si se elimina un conductor o vehículo
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.SET_NULL, null=True, blank=True, related_name='envios_por_vehiculo') 
    conductor = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, null=True, blank=True, related_name='envios_conducidos')
    
    fecha_salida = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ASIGNADO')

    class Meta:
        verbose_name_plural = "Envíos"

    def __str__(self):
        return f"Envío de Pedido #{self.pedido.id} - {self.estado}"


# ==============================================================================
# MODELO DE RASTREO DE ENVÍO
# ==============================================================================

class RastreoEnvio(models.Model):
    ESTADO_CHOICES = [
        ('RECOLECCIÓN', 'Recolección Iniciada'),
        ('EN_CAMINO', 'En Camino al Destino'),
        ('EN_ENTREGA', 'Intentando Entrega'),
        ('COMPLETADO', 'Entregado Exitosamente'),
    ]
    
    envio = models.ForeignKey(Envios, on_delete=models.CASCADE, related_name='rastreos')
    estado = models.CharField(
        max_length=30, 
        choices=ESTADO_CHOICES,
        default='RECOLECCIÓN' # <-- 🟢 CORRECCIÓN
    )
    ubicacion = models.CharField(
        max_length=255, 
        default='Ubicación no registrada', # <-- 🟢 CORRECCIÓN
        help_text="Ciudad o dirección actual."
    )
    fecha_hora = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Rastreo de Envíos"
        ordering = ['fecha_hora'] # Para que el historial de rastreo esté ordenado

    def __str__(self):
        return f"Rastreo de Envío {self.envio.id} - {self.estado}"


# ==============================================================================
# 📢 Señales (Signals)
# ==============================================================================

# Se activa cuando un Envío es guardado/actualizado.
@receiver(post_save, sender=Envios)
def actualizar_estado_pedido(sender, instance, **kwargs):
    """
    Actualiza el estado del Pedido asociado cuando el estado del Envío cambia.
    """
    if instance.estado in ['ENTREGADO', 'FALLIDO']:
        # Mapea el estado del Envío al estado final del Pedido
        nuevo_estado_pedido = 'COMPLETADO' if instance.estado == 'ENTREGADO' else 'CANCELADO'
        
        # Solo actualiza si el estado actual es diferente para evitar recursion
        if instance.pedido.estado != nuevo_estado_pedido:
            instance.pedido.estado = nuevo_estado_pedido
            instance.pedido.save(update_fields=['estado'])