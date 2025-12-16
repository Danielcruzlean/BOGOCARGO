from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from decimal import Decimal

# ============================================================
# ROLES & CONSTANTES
# ============================================================

TIPOS_USUARIO = (
    ('ADMIN', 'Administrador'),
    ('MINORISTA', 'Minorista'),
    ('CONDUCTOR', 'Conductor'),
)

ESTADOS_PEDIDO = (
    ('PENDIENTE', 'Pendiente'),
    ('ASIGNADO', 'Asignado'),
    ('EN_RUTA', 'En Ruta'),
    ('ENTREGADO', 'Entregado'),
    ('CANCELADO', 'Cancelado')
)

ESTADOS_FACTURA = (
    ('PENDIENTE_PAGO', 'Pendiente de Pago'),
    ('PAGADA', 'Pagada'),
    ('VENCIDA', 'Vencida'),
    ('ANULADA', 'Anulada')
)

TIPO_MERCANCIA_CHOICES = [
    ('PERECEDEROS', 'Perecederos'),
    ('REFRIGERADOS', 'Refrigerados'),
    ('CONTROLADOS', 'Controlados (Químicos, Medicamentos)'),
    ('PELIGROSOS', 'Mercancías Peligrosas'),
    ('FRAGIL', 'Frágil (Vidrio, Cerámica)'),
    ('VOLUMINOSO', 'Voluminoso'),
    ('PESADO', 'Pesado'),
    ('SECAS', 'Carga Seca General'),
    ('BEBIDAS', 'Bebidas'),
    ('EMPAQUETADOS', 'Empaquetados'),
    ('ALIMENTOS_PROCESADOS', 'Alimentos Procesados'),
    ('ELECTRONICOS', 'Electrónicos'),
    ('REPUESTOS', 'Repuestos'),
    ('MUEBLES', 'Muebles'),
    ('DECORACION', 'Decoración'),
    ('TEXTIL', 'Textil'),
    ('ROPA', 'Ropa'),
    ('PRENDAS', 'Prendas'),
    ('FARMACEUTICOS', 'Farmacéuticos'),
    ('HERRAMIENTAS', 'Herramientas'),
    ('MATERIALES', 'Materiales'),
    ('VIDRIO', 'Vidrio'),
    ('PLASTICOS', 'Plásticos'),
    ('ENVASES', 'Envases'),
    ('BATERIAS', 'Baterías'),
    ('CONGELADOS', 'Congelados'),
    ('GRANEL', 'Granel'),
    ('PAPEL', 'Papel'),
    ('CARTON', 'Cartón'),
    ('QUIMICOS', 'Químicos'),
    ('LIQUIDOS', 'Líquidos'),
    ('DEPORTIVO', 'Deportivo'),
]

TIPO_VEHICULO_CHOICES = (
    ('CAMIONETA', 'Camioneta'),
    ('FURGON', 'Furgón'),
    ('CAMION_PEQUEÑO', 'Camión Pequeño'),
    ('CAMION_GRANDE', 'Camión Grande'),
    ('MOTO', 'Motocicleta'),
)

ESTADOS_ASIGNACION = (
    ('PENDIENTE', 'Pendiente'),
    ('ACEPTADA', 'Aceptada'),
    ('RECHAZADA', 'Rechazada')
)

ESTADOS_ENVIO = (
    ('ASIGNADO', 'Asignado'),
    ('EN_RUTA', 'En Ruta'),
    ('ENTREGADO', 'Entregado'),
    ('FALLIDO', 'Fallido')
)


# ============================================================
# CUSTOM USER MANAGER
# ============================================================

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email debe ser configurado')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


# ============================================================
# MODELO DE USUARIO PERSONALIZADO (Usuarios)
# ============================================================

class Usuarios(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPOS_USUARIO, default='MINORISTA')
    
    # Datos del Vehículo del Conductor
    placas = models.CharField(max_length=10, blank=True, null=True, help_text="Placa del vehículo de transporte.")
    marca_vehiculo = models.CharField(max_length=50, blank=True, null=True, help_text="Marca del vehículo.")
    referencia_vehiculo = models.CharField(max_length=50, blank=True, null=True, help_text="Referencia/Modelo del vehículo.")
    tipo_vehiculo = models.CharField(max_length=20, choices=TIPO_VEHICULO_CHOICES, blank=True, null=True, help_text="Tipo de vehículo (Ej: Camión, Furgón).")
    
    # Campos requeridos por Django
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    objects = CustomUserManager()
    
    class Meta:
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.email} ({self.get_tipo_display()})"


# ============================================================
# MODELOS DE SOPORTE (Empresas, Productos)
# (Añadidos para resolver la ImportError de otros archivos)
# ============================================================

class Empresas(models.Model):
    TIPOS_EMPRESA = (
        ('MAYORISTA', 'Mayorista'),
        ('MINORISTA', 'Minorista')
    )
    nombre = models.CharField(max_length=150)
    nit = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPOS_EMPRESA)
    usuario = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.nombre

class Productos(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    peso_kg = models.DecimalField(max_digits=10, decimal_places=2)
    altura_cm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ancho_cm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    largo_cm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    empresa = models.ForeignKey(Empresas, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre


# ============================================================
# MODELO DE PEDIDOS/ORDENES
# ============================================================

class Pedidos(models.Model):
    # Relaciones
    minorista = models.ForeignKey(Usuarios, on_delete=models.PROTECT, limit_choices_to={'tipo': 'MINORISTA'}, related_name='pedidos_creados')
    conductor = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'tipo': 'CONDUCTOR'}, related_name='pedidos_asignados')

    # Datos del Vehículo ASIGNADO (Copia del conductor al aceptar)
    placas_asignadas = models.CharField(max_length=10, blank=True, null=True)
    marca_asignada = models.CharField(max_length=50, blank=True, null=True)
    referencia_asignada = models.CharField(max_length=50, blank=True, null=True)
    tipo_vehiculo_asignado = models.CharField(max_length=20, choices=TIPO_VEHICULO_CHOICES, blank=True, null=True)

    # Datos de la Carga
    tipo_mercancia = models.CharField(max_length=50, choices=TIPO_MERCANCIA_CHOICES)
    peso_total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Peso en Kg")
    volumen = models.DecimalField(max_digits=10, decimal_places=2, help_text="Volumen en m³") 
    valor_declarado = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    
    # Dimensiones
    unidades = models.PositiveIntegerField(default=1)
    largo = models.DecimalField(max_digits=5, decimal_places=2, default=0.1, help_text="Largo de la unidad (metros)")
    alto = models.DecimalField(max_digits=5, decimal_places=2, default=0.1, help_text="Alto de la unidad (metros)")
    ancho = models.DecimalField(max_digits=5, decimal_places=2, default=0.1, help_text="Ancho de la unidad (metros)")

    # Datos del Envío
    empresa_mayorista = models.CharField(max_length=50, null=True, blank=True, help_text="Clave del mayorista seleccionada")
    origen = models.CharField(max_length=255)
    destino = models.CharField(max_length=255)
    fecha_recoleccion = models.DateField()
    hora_recoleccion = models.TimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    
    # Estado y Trazabilidad
    estado = models.CharField(max_length=50, choices=ESTADOS_PEDIDO, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Campo crucial añadido para la lógica de facturación
    precio_estimado = models.DecimalField(max_digits=10, decimal_places=0, default=Decimal('0'))

    class Meta:
        verbose_name = "Pedido/Orden"
        verbose_name_plural = "Pedidos/Ordenes"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Pedido BOCG-{self.id:05d} - {self.get_estado_display()}"

# ============================================================
# MODELO DE DETALLE DE PEDIDO (Resuelve ImportError en signals.py)
# ============================================================
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedidos, on_delete=models.CASCADE)
    producto = models.ForeignKey(Productos, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = "Detalles de Pedidos"
        unique_together = ('pedido', 'producto') # Un producto por pedido
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en Pedido {self.pedido.id}"

# ============================================================
# MODELO DE FACTURAS
# ============================================================

class Factura(models.Model):
    # Relación uno a uno con Pedidos
    orden = models.OneToOneField(Pedidos, on_delete=models.CASCADE, related_name='factura') 
    
    # Campos Monetarios
    monto_total = models.DecimalField(max_digits=10, decimal_places=0)
    
    # Fechas
    fecha_emision = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(null=True, blank=True)
    
    # Estado
    estado = models.CharField(max_length=50, choices=ESTADOS_FACTURA, default='PENDIENTE_PAGO') 
    
    # Referencia Única
    referencia = models.CharField(max_length=100, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"Factura #{self.id} de BOCG-{self.orden.id:05d}"
    
# ============================================================
# OTROS MODELOS ASOCIADOS AL FLUJO
# ============================================================

class Asignaciones(models.Model):
    pedido = models.ForeignKey(Pedidos, on_delete=models.CASCADE)
    conductor = models.ForeignKey(Usuarios, on_delete=models.CASCADE, limit_choices_to={'tipo': 'CONDUCTOR'})
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADOS_ASIGNACION, default='PENDIENTE')
    
    class Meta:
        verbose_name_plural = "Asignaciones"
        unique_together = ('pedido', 'conductor')

    def __str__(self):
        return f"Asignación de {self.conductor.nombre} para Pedido {self.pedido.id}"

class Envios(models.Model):
    pedido = models.OneToOneField(Pedidos, on_delete=models.CASCADE, related_name='envio')
    conductor = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, null=True, limit_choices_to={'tipo': 'CONDUCTOR'})
    fecha_salida = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_ENVIO, default='ASIGNADO')

    class Meta:
        verbose_name_plural = "Envios"

    def __str__(self):
        return f"Envío de Pedido {self.pedido.id} ({self.get_estado_display()})"

class RastreoEnvio(models.Model):
    envio = models.ForeignKey(Envios, on_delete=models.CASCADE, related_name='rastreos')
    ubicacion = models.CharField(max_length=255)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=30)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Rastreo de Envíos"
        ordering = ['fecha_hora']

    def __str__(self):
        return f"Rastreo {self.estado} para Envío {self.envio.id}"
