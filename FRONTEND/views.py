from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from FRONTEND.models import Empresas
from .forms import MayoristaForm

# Importaciones de Python para cálculos y fechas
from decimal import Decimal
import math
from datetime import date, timedelta
import random

# Importaciones añadidas para reCAPTCHA y CONFIGURACIÓN
from django.conf import settings
import requests 

# Modelos y Formularios
from FRONTEND.models import Pedidos, Factura
from .forms import UsuarioForm, PedidoForm, CrearPedidoMinoristaForm, RegistroForm

# 5pm no deja hacer pedidos hoy sino mañama
from datetime import date, datetime, timedelta
import json

from django.views.decorators.http import require_POST
from .forms import RegistroForm, VehiculoForm
# Modelo de usuario personalizado
Usuarios = get_user_model()


# ============================================================
# ROLES Y CONFIGURACIÓN GENERAL
# ============================================================

# Asumiendo que esta configuración está en settings.py, pero la mantenemos aquí para referencia
CUSTOM_AUTH_BACKEND = 'BACKEND.backends.EmailAuthBackend' 

DASHBOARD_URLS = {
    'MINORISTA': 'frontend:dashboard_minorista',
    'CONDUCTOR': 'frontend:dashboard_conductor',
    'ADMIN': 'frontend:dashboard_admin',
}

ESTADOS_PEDIDO = [
    ('PENDIENTE', 'Pendiente'),
    ('ASIGNADO', 'Asignado'),
    ('EN_RUTA', 'En Ruta'),
    ('ENTREGADO', 'Entregado'),
    ('CANCELADO', 'Cancelado')
]


def get_user_role(user):
    """Devuelve el rol del usuario, asegurando que el superusuario sea ADMIN."""
    if not user.is_authenticated:
        return 'ANÓNIMO'
        
    # CORRECCIÓN/MEJORA: Si es superusuario de Django, siempre es ADMIN.
    if user.is_superuser:
        return 'ADMIN'
        
    # Fallback al atributo 'tipo'
    return getattr(user, 'tipo', 'SIN_ROL').upper()


def is_admin(user):
    # Ya cubierta por get_user_role
    return user.is_authenticated and get_user_role(user) == 'ADMIN'


def is_minorista(user):
    return user.is_authenticated and get_user_role(user) == 'MINORISTA'


def is_conductor(user):
    return user.is_authenticated and get_user_role(user) == 'CONDUCTOR'


def get_base_dashboard_context(user):
    """Genera el contexto básico para todos los dashboards."""
    full_name = f"{user.nombre} {user.apellido}".strip()
    return {
        'nombre': full_name or 'Usuario',
        'email': user.email,
        'role': get_user_role(user),
    }


def get_dashboard_url_by_role(user):
    """Obtiene la URL del dashboard según el rol del usuario."""
    # Si el rol no está en el mapa, redirige a una cuenta genérica, aunque la lógica del if/else debería cubrirlo
    return DASHBOARD_URLS.get(get_user_role(user), 'frontend:mi_cuenta')


# ============================================================
# 1. VISTAS PÚBLICAS
# ============================================================

def index_view(request):
    """
    Página de inicio pública. 
    Redirige al dashboard apropiado si el usuario ya está autenticado.
    """
    if request.user.is_authenticated:
        # Reutiliza la función de utilidad para la redirección basada en el rol
        return redirect(get_dashboard_url_by_role(request.user))
        
    # Si no está autenticado, muestra la página de inicio pública
    return render(request, 'FRONTEND/index.html')

def servicios_view(request):
    """
    Vista de la página de servicios públicos de BOGOCARGO.
    Renderiza la plantilla que describe los roles (Mayorista, Minorista, Conductor).
    """
    return render(request, 'FRONTEND/servicios.html')


def mi_cuenta_view(request):
    """Muestra el formulario de Login y Registro."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_by_role(request.user))
    # Para mostrar los formularios de login y registro en la misma página
    ctx = {
        'registro_form': RegistroForm(),
    }
    return render(request, 'FRONTEND/mi_cuenta.html', ctx)

def registrar_vehiculo_view(request):
    """Maneja el registro y edición del vehículo para conductores."""
    if not request.user.is_authenticated or request.user.tipo != 'CONDUCTOR':
        messages.error(request, "Acceso denegado. Debes ser conductor.")
        return redirect('frontend:mi_cuenta')

    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Vehículo guardado correctamente!")
            return redirect('frontend:dashboard_conductor')
        else:
            messages.error(request, "Error en los datos. Por favor verifica.")
    else:
        # Cargamos el formulario con los datos actuales del usuario (si existen)
        form = VehiculoForm(instance=request.user)

    ctx = {
        'form': form,
    }
    return render(request, 'FRONTEND/registrar_vehiculo.html', ctx)

@require_http_methods(["GET", "POST"])
def register_view(request):
    """Maneja el registro de nuevos usuarios (solo POST es útil aquí)."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_by_role(request.user))

    if request.method == "GET":
        return redirect('frontend:mi_cuenta')

    form = RegistroForm(request.POST)

    if form.is_valid():
        try:
            # El form.save() en RegistroForm crea el usuario y establece la contraseña/rol.
            user = form.save()
            
            # Loguear y redirigir
            # Usamos el backend personalizado para asegurar la compatibilidad
            login(request, user, backend=CUSTOM_AUTH_BACKEND) 
            messages.success(request, "¡Registro exitoso! Bienvenido a BogoCargo.")
            return redirect(get_dashboard_url_by_role(user))
            
        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar el registro: {e}")
            
    else:
        # Mejor manejo de errores antes de la redirección.
        for field, errors in form.errors.items():
            field_name = field
            # Intentamos obtener un nombre de campo más legible
            if field == 'nombre': field_name = 'Nombre'
            elif field == 'apellido': field_name = 'Apellido'
            elif field == 'tipo': field_name = 'Tipo de Usuario'
            elif field == 'email': field_name = 'Email'
            elif field == 'password2': field_name = 'Confirmación de Contraseña'
            
            for error in errors:
                messages.error(request, f"Error en {field_name}: {error}")
                break # Mostrar solo el primer error por campo
            
    # Redirigir siempre a mi_cuenta si falla para mostrar los mensajes de error
    return redirect("frontend:mi_cuenta")


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Maneja el proceso de inicio de sesión."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_by_role(request.user))

    if request.method == "GET":
        return redirect("frontend:mi_cuenta")

    # Usamos 'email' como nombre de campo para el login.
    username_or_email = request.POST.get("email", "").lower().strip()
    password = request.POST.get("password")

    # CORRECCIÓN CLAVE: Cambiar 'username=' a 'email=' para que coincida con el
    # USERNAME_FIELD del modelo y el CustomUserManager.
    user = authenticate(request, email=username_or_email, password=password) 

    if user:
        # Autenticación Exitosa
        # CORRECCIÓN: Siempre usar el backend personalizado
        login(request, user, backend=CUSTOM_AUTH_BACKEND) 
        # Redirigir al dashboard apropiado
        return redirect(get_dashboard_url_by_role(user)) 

    # Se ejecuta si authenticate devolvió None 
    messages.error(request, "Credenciales incorrectas o usuario inactivo.")
    return redirect("frontend:mi_cuenta")
    
    # --- FIN DE LA SECCIÓN CRÍTICA ---


def logout_view(request):
    """Cierra la sesión del usuario."""
    logout(request)
    return redirect("frontend:index")


# ============================================================
# 2. DASHBOARDS POR ROL
# ============================================================

@login_required
def dashboard_view(request):
    """Redirige al dashboard apropiado según el rol."""
    return redirect(get_dashboard_url_by_role(request.user))


@login_required
@user_passes_test(is_minorista)
def dashboard_minorista(request):
    """Dashboard para el rol MINORISTA."""
    pedidos = Pedidos.objects.filter(minorista=request.user).order_by("-fecha_creacion")
    ctx = get_base_dashboard_context(request.user)
    ctx["pedidos"] = pedidos
    return render(request, "FRONTEND/dashboard_minorista.html", ctx)


@login_required
@user_passes_test(is_conductor)
def dashboard_conductor(request):
    """Dashboard para el rol CONDUCTOR."""
    
    conductor = request.user
    
    # 1. Validar que el conductor tenga TODOS los datos obligatorios del vehículo.
    # Los campos están definidos directamente en el modelo Usuarios:
    # placas, tipo_vehiculo, marca_vehiculo, referencia_vehiculo
    
    vehiculo_valido = all([
        conductor.placas, 
        conductor.tipo_vehiculo, 
        conductor.marca_vehiculo, 
        conductor.referencia_vehiculo,
        # Si tienes más campos obligatorios en Usuarios, añádelos aquí.
    ])

    # 2. Obtener TODOS los pedidos relevantes (PENDIENTES, ASIGNADOS, EN_RUTA)
    todos_los_pedidos_relevantes = Pedidos.objects.filter(
        Q(conductor=conductor, estado__in=["ASIGNADO", "EN_RUTA"]) |
        Q(estado="PENDIENTE")
    ).order_by("-fecha_creacion")

    # 3. Separar los pedidos
    pedidos_pendientes = todos_los_pedidos_relevantes.filter(estado="PENDIENTE")
    pedidos_activos = todos_los_pedidos_relevantes.filter(estado__in=["ASIGNADO", "EN_RUTA"])
    
    # 4. Crear el contexto
    ctx = get_base_dashboard_context(conductor)
    ctx["titulo_dashboard"] = "Dashboard del Conductor"
    
    # --- NUEVAS VARIABLES DE VEHÍCULO ---
    # Ya no pasamos un objeto 'vehiculo', sino los campos individuales y la validez.
    # La plantilla ahora debe acceder a estos campos vía 'request.user' (si está en el template context)
    # o directamente a las propiedades del conductor si la función get_base_dashboard_context lo incluye.
    
    # Opcional: Para simplificar el acceso en el template, podemos pasar los campos de vehículo directamente.
    # Pero el acceso 'request.user.placas' debería funcionar si el User está en el contexto.
    
    # El más importante:
    ctx["vehiculo_valido"] = vehiculo_valido  
    
    # Y los campos del vehículo (para mostrarlos en la sección de "Mi Vehículo")
    ctx["placas"] = conductor.placas
    ctx["tipo_vehiculo"] = conductor.tipo_vehiculo
    ctx["marca_vehiculo"] = conductor.marca_vehiculo
    ctx["referencia_vehiculo"] = conductor.referencia_vehiculo
    # -----------------------------------
    
    # Pasamos las listas separadas y conteos al contexto:
    ctx["pedidos_pendientes"] = pedidos_pendientes
    ctx["pedidos_activos"] = pedidos_activos
    ctx["num_pedidos_activos"] = pedidos_activos.count()
    ctx["rutas_pendientes"] = pedidos_pendientes.count()
    
    return render(request, "FRONTEND/dashboard_conductor.html", ctx)


@login_required
@user_passes_test(is_admin)
def dashboard_admin(request):
    """Dashboard para el rol ADMINISTRADOR."""
    ctx = get_base_dashboard_context(request.user)
    
    # --- CORRECCIÓN AQUÍ: Se añade el contador de Mayoristas (Empresas) ---
    ctx.update({
        "total_usuarios": Usuarios.objects.count(),
        "total_mayoristas": Empresas.objects.count(), # <-- LÍNEA AÑADIDA/CORREGIDA
        "total_pedidos": Pedidos.objects.count(),
        
        # Opcional: Para completar todas las métricas de pedidos en el dashboard
        "num_pedidos_solicitados": Pedidos.objects.filter(estado='SOLICITADO').count(),
        "num_pedidos_asignados": Pedidos.objects.filter(estado='ASIGNADO').count(),
        "num_pedidos_completados": Pedidos.objects.filter(estado='COMPLETADO').count(),
    })
    
    # NOTA: Asegúrate de que tu plantilla se llame "FRONTEND/dashboard_admin.html" o el nombre que uses.
    return render(request, "FRONTEND/dashboard_admin.html", ctx)


# ============================================================
# 3. CRUD USUARIOS (ADMIN)
# ============================================================

@login_required
@user_passes_test(is_admin)
def usuarios_list(request):
    """Lista de usuarios para el Admin."""
    usuarios = Usuarios.objects.all().order_by("tipo", "email")
    return render(request, "FRONTEND/admin_crud/usuarios_list.html", {"usuarios": usuarios})


@login_required
@user_passes_test(is_admin)
def usuarios_create(request):
    """Creación de usuarios por el Admin."""
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado exitosamente.")
            return redirect("frontend:usuarios_list")
        else:
            # Aquí también se genera el mismo tipo de error si los campos son nulos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
                    break
            
    else:
        form = UsuarioForm()

    return render(request, "FRONTEND/admin_crud/usuarios_form.html", {"form": form})


@login_required
@user_passes_test(is_admin)
def usuarios_update(request, pk):
    """Actualización de usuarios por el Admin."""
    usuario = get_object_or_404(Usuarios, pk=pk)
    
    # CORRECCIÓN: Impedir que un admin (incluso si no es el superuser principal) se edite a sí mismo
    if usuario == request.user:
        messages.warning(request, "No puedes editar tu propio perfil de administrador desde esta vista.")
        return redirect("frontend:usuarios_list")

    if request.method == "POST":
        # Usamos `instance` para actualizar
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuario {usuario.email} actualizado exitosamente.")
            return redirect("frontend:usuarios_list")
        else:
            messages.error(request, "Error al actualizar el usuario. Revise los datos.")
    else:
        form = UsuarioForm(instance=usuario)

    return render(request, "FRONTEND/admin_crud/usuarios_form.html", {"form": form, "is_update": True})


@login_required
@user_passes_test(is_admin)
def usuarios_delete(request, pk):
    """Eliminación de usuarios por el Admin."""
    usuario = get_object_or_404(Usuarios, pk=pk)
    
    # CORRECCIÓN: Evitar que un admin se elimine a sí mismo
    if usuario == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta de administrador.")
        return redirect("frontend:usuarios_list")

    usuario.delete()
    messages.success(request, f"Usuario {usuario.email} eliminado exitosamente.")
    return redirect("frontend:usuarios_list")


# ============================================================
# 4. CRUD ADMIN DE PEDIDOS
# ============================================================

@login_required
@user_passes_test(is_admin)
def pedidos_crud_admin(request):
    """Lista de pedidos para el Admin (CRUD)."""
    pedidos = Pedidos.objects.all().order_by("-fecha_creacion")
    return render(request, "FRONTEND/admin_crud/pedidos_list_admin.html", {
        "pedidos": pedidos,
        "estados": ESTADOS_PEDIDO,
    })


@login_required
@user_passes_test(is_admin)
def pedidos_update(request, pk):
    """Actualización de pedidos por el Admin."""
    pedido = get_object_or_404(Pedidos, pk=pk)

    if request.method == "POST":
        form = PedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            messages.success(request, f"Pedido BOCG-{pedido.id:05d} actualizado por Admin.")
            return redirect("frontend:pedidos_crud_admin")
        else:
            messages.error(request, "Error al actualizar el pedido.")
    else:
        form = PedidoForm(instance=pedido)
    
    # Soluciona el error 'Invalid filter: replace'
    estado_display_limpio = pedido.estado.replace('_', ' ').title()

    # LÍNEA CORREGIDA: Se usa SOLAMENTE la ruta correcta 'admin_crud/pedidos_form.html'
    return render(request, "FRONTEND/admin_crud/pedidos_form.html", {
        "form": form, 
        "is_update": True,
        "pedido": pedido, 
        "estado_display_limpio": estado_display_limpio,
    })


# views.py (Asegúrate de tener esta importación al inicio de tu archivo)

# ... otras importaciones

@require_POST
@login_required
@user_passes_test(is_admin)
def pedidos_delete(request, pk):
    """Eliminación de pedidos por el Admin. Solo acepta el método POST."""
    
    # Si la solicitud no fuera POST, el decorador @require_POST ya devolvería un 405.
    # Por lo tanto, podemos ejecutar la lógica de eliminación directamente.
    
    pedido = get_object_or_404(Pedidos, pk=pk)
    
    try:
        # Se elimina el objeto
        pedido_id_display = f"BOCG-{pedido.id:05d}"
        pedido.delete()
        
        # Envía mensaje de éxito
        messages.success(request, f"Pedido {pedido_id_display} eliminado por Admin.")
        
    except Exception as e:
        # Manejo de error si la eliminación falla (ej. restricciones de FK)
        messages.error(request, f"Error al eliminar el pedido {pedido_id_display}: {e}")
    
    # Redirige a la lista CRUD de pedidos del administrador
    return redirect("frontend:pedidos_crud_admin")


# ============================================================
# 5. LÓGICA DE CÁLCULO DE PRECIO EN EL BACKEND
# ============================================================

# Constantes de cálculo (Deben coincidir con las del JS)
BASE_RATE_COP = Decimal(15000)
WEIGHT_COST_PER_KG_COP = Decimal(1200)
VOLUME_COST_PER_M3_COP = Decimal(80000)
MIN_VALOR_DECLARADO = Decimal(100000)

# CORRECCIÓN: Factores de riesgo de mercancía completos y normalizados
RISK_FACTOR_MAP = {
    'PERECEDEROS': Decimal('1.10'), 
    'REFRIGERADOS': Decimal('1.15'),
    'CONTROLADOS': Decimal('1.25'), 
    'PELIGROSOS': Decimal('1.30'),
    'FRAGIL': Decimal('1.10'), 
    'VOLUMINOSO': Decimal('1.05'),
    'PESADO': Decimal('1.05'),
    'SECAS': Decimal('1.0'),
    'BEBIDAS': Decimal('1.05'),
    'EMPAQUETADOS': Decimal('1.0'),
    'ALIMENTOS_PROCESADOS': Decimal('1.05'),
    'ELECTRONICOS': Decimal('1.10'),
    'REPUESTOS': Decimal('1.05'),
    'MUEBLES': Decimal('1.05'),
    'DECORACION': Decimal('1.05'),
    'TEXTIL': Decimal('1.0'),
    'ROPA': Decimal('1.0'),
    'PRENDAS': Decimal('1.0'),
    'FARMACEUTICOS': Decimal('1.15'),
    'HERRAMIENTAS': Decimal('1.05'),
    'MATERIALES': Decimal('1.05'),
    'VIDRIO': Decimal('1.10'),
    'PLASTICOS': Decimal('1.0'),
    'ENVASES': Decimal('1.0'),
    'BATERIAS': Decimal('1.20'), 
    'CONGELADOS': Decimal('1.15'),
    'GRANEL': Decimal('1.05'),
    'PAPEL': Decimal('1.0'),
    'CARTON': Decimal('1.0'),
    'QUIMICOS': Decimal('1.25'),
    'LIQUIDOS': Decimal('1.10'),
    'DEPORTIVO': Decimal('1.05'), 
}

def _safe_decimal_conversion(value, default_val=Decimal(0)):
    """Convierte un valor a Decimal de forma segura, usando un valor por defecto en caso de error o None/vacio."""
    try:
        if value is None or str(value).strip() == '':
            return default_val
        return Decimal(value)
    except Exception:
        return default_val

def _calcular_precio_envio(data):
    """Calcula el precio del envío en el servidor de forma segura y devuelve el precio y el volumen calculado."""
    
    # 1. Extracción de datos y conversión segura a Decimal
    peso = _safe_decimal_conversion(data.get('peso_total'), default_val=Decimal(0))
    unidades = _safe_decimal_conversion(data.get('unidades'), default_val=Decimal(1))
    
    # Usar un mínimo de 0.01 metros (1cm) para evitar volumen cero
    largo = _safe_decimal_conversion(data.get('largo'), default_val=Decimal('0.01'))
    alto = _safe_decimal_conversion(data.get('alto'), default_val=Decimal('0.01'))
    ancho = _safe_decimal_conversion(data.get('ancho'), default_val=Decimal('0.01'))
    
    # Aseguramos que el tipo de mercancía siempre sea uppercase para el lookup
    tipo_mercancia = data.get('tipo_mercancia', 'SECAS').upper()

    # Simulación del Factor de Distancia (replicando el 1.0 + random() * 0.5 del JS)
    distance_factor = Decimal(1.0 + random.random() * 0.5).quantize(Decimal('0.01'))
    
    # 2. Cálculos de Costo
    # Calcular volumen total (Largo * Alto * Ancho * Unidades)
    volumen_total = (largo * alto * ancho * unidades).quantize(Decimal('0.01'))
    
    total_cost = BASE_RATE_COP
    
    # Costo por peso (por kg)
    total_cost += peso * WEIGHT_COST_PER_KG_COP
    
    # Costo por volumen (por m³)
    total_cost += volumen_total * VOLUME_COST_PER_M3_COP

    # Factor de riesgo
    risk_factor = RISK_FACTOR_MAP.get(tipo_mercancia, Decimal('1.0'))
    total_cost *= risk_factor
    
    # Factor de distancia (simulación)
    total_cost *= distance_factor

    # 3. Redondeo al 500 más cercano (COP)
    rounded_price = Decimal(math.ceil(float(total_cost) / 500) * 500).quantize(Decimal('0'))
    
    if rounded_price < BASE_RATE_COP:
        rounded_price = BASE_RATE_COP

    # Devolvemos el precio y el volumen calculado
    return rounded_price, volumen_total

# ============================================================
# FUNCIONES DE UTILIDAD (Colocar arriba de crear_pedido)
# ============================================================

def _get_minorista_direccion(user):
    if user.is_authenticated and get_user_role(user) == 'MINORISTA':
        try:
            # NOTA: Asegúrate de que el campo ForeignKey en Empresas se llama 'usuario' o ajústalo
            empresa = Empresas.objects.filter(usuario=user, tipo='MINORISTA').first() 
            
            if empresa and empresa.direccion and empresa.ciudad:
                return f"{empresa.direccion}, {empresa.ciudad}, {empresa.pais}" 
            
            return "" 
            
        except Exception as e:
            return ""
    return ""

# ============================================================
# 6. CREAR PEDIDO MINORISTA (CON FACTURACIÓN AUTOMÁTICA)
# ============================================================

RECOLECCION_CUTOFF_HOUR = 17 # 5 PM

@login_required
@user_passes_test(lambda u: is_minorista(u) or is_admin(u))
def crear_pedido(request):
    # 1. Preparación de datos iniciales
    mayoristas = Empresas.objects.filter(tipo='MAYORISTA').order_by('nombre')
    address_map = {str(e.pk): f"{e.direccion}, {e.ciudad}" for e in mayoristas}
    mayorista_choices = [('', '--- Seleccione un Origen ---')] + [(str(e.pk), f"{e.nombre}") for e in mayoristas]
    destino_minorista = _get_minorista_direccion(request.user)

    if request.method == "POST":
        form = CrearPedidoMinoristaForm(request.POST, mayorista_choices=mayorista_choices)
        
        if form.is_valid():
            try:
                pedido = form.save(commit=False)
                
                # --- CAPTURA Y VALIDACIÓN DE CAMPOS MANUALES ---
                
                # Capturamos el precio estimado calculado por JS (evita el $0)
                precio_raw = request.POST.get('precio_estimado')
                try:
                    pedido.precio_estimado = float(precio_raw) if precio_raw else 0
                except ValueError:
                    pedido.precio_estimado = 0
                
                # Capturamos fechas y horas directamente del POST
                pedido.fecha_recoleccion = request.POST.get('fecha_recoleccion')
                pedido.hora_recoleccion = request.POST.get('hora_recoleccion')
                
                # Capturamos peso y volumen asegurando valores numéricos
                raw_peso = request.POST.get('peso_total')
                raw_volumen = request.POST.get('volumen')
                
                pedido.peso_total = float(raw_peso) if raw_peso else 0
                # Si el volumen no viene, usamos el peso como referencia o 0
                pedido.volumen = float(raw_volumen) if raw_volumen else pedido.peso_total
                
                # Asignar dirección de origen basada en el mayorista seleccionado
                id_may = form.cleaned_data.get('mayorista_origen_id')
                pedido.origen = address_map.get(str(id_may), "Dirección no encontrada")
                
                # Datos de usuario y estado inicial
                pedido.minorista = request.user
                pedido.estado = "PENDIENTE"
                
                # Guardamos el pedido para obtener el ID
                pedido.save()

                # --- CREACIÓN DE FACTURA ASOCIADA ---
                try:
                    Factura.objects.create(
                        orden=pedido,
                        monto_total=pedido.precio_estimado, # Monto real capturado
                        fecha_emision=date.today(),
                        fecha_vencimiento=date.today() + timedelta(days=15),
                        estado='PENDIENTE_PAGO'
                    )
                except Exception as e_fact:
                    print(f"Error al crear factura: {e_fact}")

                messages.success(request, "¡Pedido y factura generados exitosamente!")
                return redirect("frontend:detalle_pedido", pk=pedido.pk)

            except Exception as e:
                messages.error(request, f"Error crítico al procesar la orden: {e}")
        else:
            # Manejo de errores de validación del formulario
            for field, errors in form.errors.items():
                messages.error(request, f"Error en {field}: {errors[0]}")
    else:
        form = CrearPedidoMinoristaForm(mayorista_choices=mayorista_choices)

    # Lógica de fecha mínima para el calendario
    now = datetime.now()
    fecha_minima = now.date() + timedelta(days=1) if now.hour >= 17 else now.date()

    ctx = {
        "form": form,
        "address_map_json": json.dumps(address_map),
        "destino_minorista": destino_minorista,
        "fecha_recoleccion_min": fecha_minima,
    }
    
    return render(request, "FRONTEND/crear_pedido.html", ctx)

# ============================================================
# 7. LISTAR PEDIDOS
# ============================================================
@login_required
def listar_pedidos_conductor(request):
    """
    Muestra solo los pedidos que han sido asignados al conductor actualmente logueado.
    """
    if request.user.is_authenticated and request.user.tipo == 'CONDUCTOR':
        # 1. Filtra los pedidos:
        #    - Donde el campo 'conductor' del Pedido sea igual al usuario logueado.
        #    - Opcionalmente, puedes filtrar por estado (ej: 'ASIGNADO', 'EN_RUTA').
        
        pedidos = Pedidos.objects.filter(
            conductor=request.user 
        ).order_by('-fecha_creacion')
        
    else:
        # Si no es conductor o no está logueado (aunque ya lo asegura @login_required)
        # Puedes redirigir a un dashboard general o mostrar una lista vacía.
        pedidos = Pedidos.objects.none()
        
    # El conductor usa la misma plantilla que el listado general, 
    # pero solo con los datos filtrados.
    context = {
        'pedidos': pedidos,
        'user': request.user # Necesario para la lógica del header/título en la plantilla
    }
    return render(request, 'FRONTEND/listar_pedidos.html', context)

@login_required
def listar_pedidos(request):
    """Lista los pedidos relevantes según el rol del usuario logueado."""
    role = get_user_role(request.user)

    if role == "MINORISTA":
        pedidos = Pedidos.objects.filter(minorista=request.user)

    elif role == "CONDUCTOR":
        # Muestra pedidos asignados y pendientes
        pedidos = Pedidos.objects.filter(
            Q(conductor=request.user, estado__in=["ASIGNADO", "EN_RUTA"]) |
            Q(estado="PENDIENTE")
        )

    elif role == "ADMIN":
        # Administrador, lo enviamos al CRUD de pedidos
        return redirect("frontend:pedidos_crud_admin")
    
    else:
        # Rol no reconocido o anónimo (aunque @login_required lo previene)
        messages.error(request, "Rol de usuario no válido para listar pedidos.")
        return redirect(get_dashboard_url_by_role(request.user))


    return render(request, "FRONTEND/listar_pedidos.html", {
        "pedidos": pedidos.order_by("-fecha_creacion"),
        "role": role
    })


# ============================================================
# 8. DETALLE DE PEDIDO + GOOGLE MAPS
# ============================================================

@login_required
def detalle_pedido(request, pk):
    """Muestra el detalle de un pedido, restringido a los usuarios pertinentes."""
    pedido = get_object_or_404(Pedidos, pk=pk)
    
    role = get_user_role(request.user)
    
    # Restricción de acceso: Solo el minorista, el conductor asignado o el admin pueden ver el detalle
    if not (pedido.minorista == request.user or pedido.conductor == request.user or role == "ADMIN"):
        messages.error(request, "No tienes permiso para ver este pedido.")
        return redirect(get_dashboard_url_by_role(request.user))

    # **********************************************
    # CORRECCIÓN CLAVE: Pasamos la clave API al template
    # **********************************************
    
    # NOTA: Asegúrate de que settings.MAPS_API_KEY esté configurado en tu settings.py
    google_maps_api_key = getattr(settings, 'MAPS_API_KEY', None)
    
    # La variable mapa_url simulada se ELIMINA, ya que el mapa se renderizará con JavaScript/Google Maps API
    # mapa_url = f"http://googleusercontent.com/maps.google.com/{pedido.origen}/{pedido.destino}"


    return render(request, "FRONTEND/detalle_pedido.html", {
        "pedido": pedido,
        # Ya no se usa "mapa_url"
        "google_maps_api_key": 'AIzaSyCYfQz3T3BuQqa9Qf-MUbG5rpdXSYkSlYM', # <--- La clave API real
        "role": role,
    })


# ============================================================
# 9. ACCIONES DEL CONDUCTOR + MINORISTA + CORREOS AUTOMÁTICOS
# ============================================================

# --- Asunciones / Placeholder de funciones que debes tener ---
# Reemplaza estas con tus implementaciones reales
def get_user_role(user):
    return user.tipo # Asumiendo que el campo 'tipo' existe en el modelo User

def is_minorista(user):
    return user.is_authenticated and user.tipo == 'MINORISTA'

def is_conductor(user):
    return user.is_authenticated and user.tipo == 'CONDUCTOR'
# -----------------------------------------------------------


@login_required
@require_http_methods(["POST"])
def manejar_pedido_action(request, pedido_id):
    """Permite al conductor cambiar el estado del pedido o al minorista cancelarlo."""
    
    # 1. Inicialización de datos
    pedido = get_object_or_404(Pedidos, pk=pedido_id)
    action = request.POST.get("action")
    role = getattr(request.user, 'tipo', None) 
    is_state_changed = False
    
    # ----------------------------------------------------
    # 🎯 LÓGICA DE CANCELACIÓN (MINORISTA)
    # ----------------------------------------------------
    if action == "cancelar":
        if role == "MINORISTA" and pedido.minorista == request.user and pedido.estado == "PENDIENTE":
            pedido.estado = "CANCELADO"
            pedido.save()
            messages.success(request, f"Pedido BOCG-{pedido.id:05d} cancelado exitosamente.")
            return redirect('frontend:listar_pedidos')
        else:
            messages.error(request, "No tienes permiso para cancelar este pedido o el estado actual no lo permite.")
            return redirect("frontend:detalle_pedido", pk=pedido.id)

    # ----------------------------------------------------
    # 🚚 LÓGICA DE ACCIONES DEL CONDUCTOR
    # ----------------------------------------------------
    if role != "CONDUCTOR":
        messages.error(request, "No autorizado para realizar acciones de conductor.")
        return redirect("frontend:detalle_pedido", pk=pedido.id)
    
    # ACEPTAR: PENDIENTE -> ASIGNADO
    if action == "aceptar" and pedido.estado == "PENDIENTE":
        pedido.estado = "ASIGNADO"
        pedido.conductor = request.user
        
        # --- ADICIÓN CRUCIAL: COPIA DE DATOS DEL VEHÍCULO ---
        # Guardamos una 'foto' de los datos del vehículo en el pedido
        pedido.placas_asignadas = request.user.placas
        pedido.marca_asignada = request.user.marca_vehiculo
        pedido.referencia_asignada = request.user.referencia_vehiculo
        pedido.tipo_vehiculo_asignado = request.user.tipo_vehiculo
        
        messages.success(request, f"Pedido BOCG-{pedido.id:05d} asignado con vehículo {pedido.placas_asignadas or 'N/A'}.")
        is_state_changed = True
        
    # RECHAZAR: Devuelve el pedido a la bolsa global
    elif action == "rechazar" and pedido.conductor == request.user:
        if pedido.estado in ["ASIGNADO", "EN_RUTA"]:
            pedido.estado = "PENDIENTE"
            pedido.conductor = None
            
            # --- CORRECCIÓN: LIMPIEZA DE DATOS ASIGNADOS ---
            pedido.placas_asignadas = None
            pedido.marca_asignada = None
            pedido.referencia_asignada = None
            pedido.tipo_vehiculo_asignado = None
            
            pedido.save()
            messages.warning(request, f"Pedido BOCG-{pedido.id:05d} devuelto a la lista de pendientes.")
            return redirect("frontend:listar_pedidos") # Redirige al listado pues ya no es suyo
        else:
            messages.error(request, "Solo puedes rechazar pedidos que estén asignados o en ruta.")

    # INICIAR RUTA: ASIGNADO -> EN_RUTA
    elif action == "en_ruta" and pedido.estado == "ASIGNADO" and pedido.conductor == request.user:
        pedido.estado = "EN_RUTA"
        messages.success(request, f"Pedido BOCG-{pedido.id:05d} ahora está EN RUTA.")
        is_state_changed = True

    # FINALIZAR: EN_RUTA -> ENTREGADO
    elif action == "finalizar" and pedido.estado == "EN_RUTA" and pedido.conductor == request.user:
        pedido.estado = "ENTREGADO"
        messages.success(request, f"Pedido BOCG-{pedido.id:05d} marcado como ENTREGADO.")
        is_state_changed = True

    # 2. Validación de seguridad (si no es el conductor asignado y no es para aceptar)
    elif action != "aceptar" and pedido.conductor != request.user:
        messages.error(request, "No tienes permiso sobre este pedido asignado a otro usuario.")
        return redirect("frontend:detalle_pedido", pk=pedido.id)

    # 3. Persistencia y Notificaciones
    if is_state_changed:
        pedido.save()

        # Envío de correos automáticos al minorista
        if pedido.estado in ["ASIGNADO", "EN_RUTA", "ENTREGADO"]:
            destinatario = pedido.minorista.email
            subject_map = {
                "ASIGNADO": f"Tu pedido BOCG-{pedido.id:05d} ha sido ASIGNADO",
                "EN_RUTA": f"Tu pedido BOCG-{pedido.id:05d} ya está EN RUTA",
                "ENTREGADO": f"Tu pedido BOCG-{pedido.id:05d} ha sido ENTREGADO",
            }
            
            # Cuerpo del mensaje adaptado con info del vehículo
            vehiculo_info = f"Vehículo: {pedido.marca_asignada} {pedido.referencia_asignada} (Placa: {pedido.placas_asignadas})" if pedido.placas_asignadas else ""
            
            msg = (
                f"Hola {pedido.minorista.nombre},\n\n"
                f"Te informamos que el estado de tu pedido ha cambiado a: {pedido.get_estado_display()}.\n"
                f"Conductor: {pedido.conductor.get_full_name() if hasattr(pedido.conductor, 'get_full_name') else pedido.conductor.nombre}\n"
                f"{vehiculo_info}\n\n"
                f"Gracias por confiar en BogoCargo."
            )

            send_mail(
                subject=subject_map.get(pedido.estado, "Actualización de Pedido"),
                message=msg,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                fail_silently=True 
            )
            
    return redirect("frontend:detalle_pedido", pk=pedido.id)


# ============================================================
# 10. VISTAS DE PAGO (NUEVAS)
# ============================================================

@login_required
@user_passes_test(is_minorista)
def procesar_pago_view(request, factura_id):
    """
    Muestra la página con los métodos de pago para una factura específica.
    Solo accesible por el minorista dueño de la factura.
    """
    # 1. Obtener la factura o devolver un 404 si no existe
    factura = get_object_or_404(Factura, pk=factura_id)
    
    # 2. Validar permisos: Que la factura pertenezca al usuario logueado
    if factura.orden.minorista != request.user:
        messages.error(request, "No tienes permiso para ver esta factura.")
        # Asumiendo que 'frontend:listar_pedidos' es el dashboard del minorista
        return redirect('frontend:listar_pedidos') 

    # 3. Validar estado: Si ya está pagada, redirigir al detalle del pedido
    if factura.estado == 'PAGADA':
        messages.success(request, "Esta factura ya ha sido pagada.")
        return redirect('frontend:detalle_pedido', pk=factura.orden.id)

    context = {
        'factura': factura,
    }
    return render(request, 'FRONTEND/procesar_pago.html', context)


@login_required
@user_passes_test(is_minorista)
@require_http_methods(["POST"])
def manejar_pago_action(request, factura_id):
    """
    Simula el procesamiento de un pago y actualiza el estado de la factura.
    """
    factura = get_object_or_404(Factura, pk=factura_id)
    # Convertimos a mayúsculas para asegurar coincidencia con los valores del formulario
    metodo = request.POST.get("metodo").upper() 
    
    # 1. Validar permisos (de nuevo, por seguridad)
    if factura.orden.minorista != request.user:
        messages.error(request, "No autorizado para realizar esta acción de pago.")
        return redirect('frontend:listar_pedidos') 

    # 2. Validar estado (Doble verificación antes de procesar)
    if factura.estado == 'PAGADA':
        messages.warning(request, "La factura ya estaba pagada.")
        return redirect('frontend:detalle_pedido', pk=factura.orden.id)

    # 3. Simulación del proceso de pago
    # Verificamos contra los posibles valores en MAYÚSCULAS del formulario
    valid_methods = ['TARJETA', 'PSE', 'EFECTIVO'] 

    if metodo in valid_methods:
        
        # Marcamos la factura como PAGADA
        factura.estado = 'PAGADA'
        factura.fecha_pago = date.today()
        factura.metodo_pago = metodo
        factura.save()
        
        # 4. Mensaje de éxito y redirección
        messages.success(request, f"¡Pago exitoso! Factura #{factura.id} por ${factura.monto_total} marcada como PAGADA.")
        
        # Redirigimos al detalle del pedido asociado
        return redirect('frontend:detalle_pedido', pk=factura.orden.id)

    else:
        # 5. Manejo de método no válido
        messages.error(request, "Método de pago no reconocido. Intente de nuevo.")
        return redirect('frontend:procesar_pago_view', factura_id=factura_id)
    
# ============================================================
# 8. CRUD DE MAYORISTAS (ADMIN) - Usando Clases Genéricas
# ============================================================

class MayoristaListView( ListView):
    # ...
    def get_queryset(self):
        # Asegura la ordenación por 'id' que es la clave primaria
        return Empresas.objects.filter(tipo='MAYORISTA').order_by('id')
    template_name = "FRONTEND/admin_crud/empresas_list.html"

    # 1. Asegurar que solo un Admin puede acceder
    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, "Acceso denegado. Se requiere rol de Administrador.")
            return redirect(get_dashboard_url_by_role(request.user))
        return super().dispatch(request, *args, **kwargs)

    # 2. Filtrar solo las empresas con tipo MAYORISTA
    def get_queryset(self):
        # Asumiendo que Empresas.TIPO_MAYORISTA es 'MAYORISTA'
        return Empresas.objects.filter(tipo='MAYORISTA').order_by('nombre') 
    
    # 3. Añadir el nombre de la página al contexto
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestión de Mayoristas'
        return context


class AdminRequiredMixin:
    """Mixin para asegurar que solo los administradores accedan."""
    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, "Acceso denegado. Se requiere rol de Administrador.")
            return redirect(get_dashboard_url_by_role(request.user))
        return super().dispatch(request, *args, **kwargs)
    
# ============================================================
# 10. CRUD MAYORISTAS (ADMIN) - VISTAS CORREGIDAS
# ============================================================

class MayoristaListView(AdminRequiredMixin, ListView):
    """Muestra el listado de Mayoristas ordenado por ID (pk)."""
    model = Empresas
    template_name = "FRONTEND/admin_crud/empresas_list.html"
    context_object_name = "mayoristas"

    def get_queryset(self):
        # 🟢 CORRECCIÓN 1: Filtro riguroso por 'MAYORISTA' y ordenación por 'id'.
        # Esto asegura que se vean los datos y que estén ordenados 1, 2, 3...
        return Empresas.objects.filter(tipo='MAYORISTA').order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Añadir el conteo total
        context['total_mayoristas'] = self.get_queryset().count()
        return context


class MayoristaCreateView(AdminRequiredMixin, CreateView):
    """Crea una nueva empresa Mayorista."""
    model = Empresas
    form_class = MayoristaForm
    template_name = "FRONTEND/admin_crud/empresas_form.html"
    success_url = reverse_lazy('frontend:empresas_list')

    def form_valid(self, form):
        # 🟢 CORRECCIÓN 2: Asegurar explícitamente que el campo 'tipo' se guarde como 'MAYORISTA'
        form.instance.tipo = 'MAYORISTA'
        messages.success(self.request, f"Mayorista '{form.instance.nombre}' creado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = False
        context['page_title'] = 'Crear Nuevo Mayorista'
        return context


class MayoristaUpdateView(AdminRequiredMixin, UpdateView):
    """Actualiza una empresa Mayorista existente."""
    model = Empresas
    form_class = MayoristaForm
    template_name = "FRONTEND/admin_crud/empresas_form.html"
    success_url = reverse_lazy('frontend:empresas_list')
    context_object_name = 'mayorista'

    def get_queryset(self):
        # Asegurar que solo se puedan actualizar empresas tipo MAYORISTA
        return Empresas.objects.filter(tipo='MAYORISTA')

    def form_valid(self, form):
        # Asegurarse de que el tipo no sea alterado al actualizar
        form.instance.tipo = 'MAYORISTA'
        messages.success(self.request, f"Mayorista '{form.instance.nombre}' actualizado exitosamente.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        context['page_title'] = f'Editar Mayorista: {self.object.nombre}'
        return context


class MayoristaDeleteView(AdminRequiredMixin, DeleteView):
    """Elimina una empresa Mayorista."""
    model = Empresas
    template_name = "FRONTEND/admin_crud/empresas_confirm_delete.html"
    success_url = reverse_lazy('frontend:empresas_list')
    context_object_name = 'mayorista'

    def get_queryset(self):
        # Asegurar que solo se puedan eliminar empresas tipo MAYORISTA
        return Empresas.objects.filter(tipo='MAYORISTA')

    def form_valid(self, form):
        messages.success(self.request, f"Mayorista '{self.object.nombre}' eliminado exitosamente.")
        # Usamos .delete() del modelo directamente para evitar problemas con form_valid en DeleteView
        self.object.delete()
        return redirect(self.success_url)