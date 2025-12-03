# FRONTEND/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model 
from django.contrib.auth.decorators import login_required, user_passes_test 
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q 
from django.db import IntegrityError 

# --- Importaciones de modelos y formularios ---
from BACKEND.models import Pedidos
from .forms import UsuarioForm, PedidoForm 

# Obtener tu modelo de usuario personalizado (BACKEND.Usuarios)
Usuarios = get_user_model()

# Definir el backend que usaremos para iniciar sesión/registro
CUSTOM_AUTH_BACKEND = 'BACKEND.backends.EmailAuthBackend'

# =================================================================
# Lógica de Rol y Redirección
# =================================================================

DASHBOARD_URLS = {
    'MINORISTA': 'frontend:dashboard_minorista',
    'CONDUCTOR': 'frontend:dashboard_conductor',
    'ADMIN': 'frontend:dashboard_admin',
}

ESTADOS_PEDIDO = Pedidos.ESTADOS if hasattr(Pedidos, 'ESTADOS') else [
    ('PENDIENTE', 'Pendiente'), 
    ('ASIGNADO', 'Asignado'), 
    ('EN_RUTA', 'En Ruta'), 
    ('ENTREGADO', 'Entregado'),
    ('CANCELADO', 'Cancelado')
]


def get_user_role(user):
    """Obtiene el rol del usuario directamente del campo 'tipo'."""
    if user.is_authenticated:
        return getattr(user, 'tipo', 'SIN_ROL').upper() 
    return 'ANÓNIMO'

def get_dashboard_url_by_role(user):
    """Determina la URL del dashboard basada en el usuario."""
    role = get_user_role(user)
    return DASHBOARD_URLS.get(role, 'frontend:mi_cuenta') 

# Funciones de prueba para restringir el acceso
def is_admin(user):
    """Verifica si el usuario es un administrador."""
    return user.is_authenticated and get_user_role(user) == 'ADMIN'

def is_minorista(user):
    """Verifica si el usuario es un minorista."""
    return user.is_authenticated and get_user_role(user) == 'MINORISTA'

def is_conductor(user):
    """Verifica si el usuario es un conductor."""
    return user.is_authenticated and get_user_role(user) == 'CONDUCTOR'

# ===============================================
# 1. Vistas Públicas (Index, Login, Registro, Logout)
# ===============================================

def index(request):
    """Página principal pública."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_by_role(request.user))
        
    return render(request, 'FRONTEND/index.html', {'message': 'Bienvenido a BOGOCARGO'})


def mi_cuenta_view(request):
    """Muestra la plantilla mi_cuenta.html (Login/Registro)."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_by_role(request.user))
        
    return render(request, 'FRONTEND/mi_cuenta.html')


@require_http_methods(["GET", "POST"])
def register_view(request):
    """Maneja la lógica del formulario de registro (POST)."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_by_role(request.user))
        
    if request.method == 'GET':
        return redirect('frontend:mi_cuenta')

    # Si es POST, procesamos el registro
    full_name = request.POST.get('full_name', '').strip()
    email = request.POST.get('email', '').lower().strip()
    password = request.POST.get('password')
    role = request.POST.get('role', '').upper()
    
    if role not in ['MINORISTA', 'CONDUCTOR']:
        messages.error(request, 'Rol de usuario inválido. Solo se permite Minorista o Conductor.')
        return redirect('frontend:mi_cuenta')
    
    if not (full_name and email and password and role):
        messages.error(request, 'Todos los campos son obligatorios.')
        return redirect('frontend:mi_cuenta')

    name_parts = full_name.split(' ', 1)
    nombre = name_parts[0]
    apellido = name_parts[1] if len(name_parts) > 1 else ''

    if Usuarios.objects.filter(email=email).exists():
        messages.error(request, 'Este correo electrónico ya está registrado. Intenta iniciar sesión.')
        return redirect('frontend:mi_cuenta')
    
    try:
        user = Usuarios.objects.create_user(
            email=email,
            password=password,
            nombre=nombre,
            apellido=apellido,
            tipo=role 
        )
        
        login(request, user, backend=CUSTOM_AUTH_BACKEND) 
        
        messages.success(request, f'¡Registro exitoso! Bienvenido(a), {user.nombre}.')
        
        return redirect(get_dashboard_url_by_role(user))
        
    except Exception as e:
        messages.error(request, f'Error inesperado al registrar: {e}')
        return redirect('frontend:mi_cuenta')


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Maneja la lógica del formulario de inicio de sesión (POST)."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_by_role(request.user))
        
    if request.method == 'GET':
        return redirect('frontend:mi_cuenta')

    # Si es POST, procesamos el inicio de sesión
    username_or_email = request.POST.get('username', '')
    password = request.POST.get('password')

    if username_or_email:
        username_or_email = username_or_email.lower().strip()
    
    user = authenticate(request, username=username_or_email, password=password)
    
    if user is not None:
        login(request, user, backend=CUSTOM_AUTH_BACKEND)
        
        messages.success(request, f'Bienvenido(a), {user.nombre}!') 
        
        return redirect(get_dashboard_url_by_role(user))
        
    else:
        messages.error(request, 'Credenciales inválidas. Por favor, verifica tu email y contraseña.')
        return redirect('frontend:mi_cuenta')

def logout_view(request):
    """Cierra la sesión del usuario."""
    logout(request)
    messages.info(request, 'Sesión cerrada. ¡Vuelve pronto!')
    return redirect('frontend:index')

# ===============================================
# 2. Vistas de Redirección y Dashboard Específicas
# ===============================================

@login_required
def dashboard_view(request):
    """
    Función principal llamada por la URL '/dashboard/'. 
    Redirige inmediatamente al dashboard específico basado en el rol del usuario.
    """
    return redirect(get_dashboard_url_by_role(request.user))

@login_required
@user_passes_test(is_minorista, login_url='/mi-cuenta/')
def dashboard_minorista(request):
    """Dashboard para usuarios Minoristas."""
    pedidos = Pedidos.objects.filter(minorista=request.user).order_by('-fecha_creacion')
    context = {'pedidos': pedidos}
    return render(request, 'FRONTEND/dashboard_minorista.html', context)

@login_required
@user_passes_test(is_conductor, login_url='/mi-cuenta/')
def dashboard_conductor(request):
    """Dashboard para usuarios Conductores."""
    pedidos_asignados = Pedidos.objects.filter(conductor=request.user, estado__in=['ASIGNADO', 'EN_RUTA']).order_by('-fecha_creacion')
    context = {'pedidos': pedidos_asignados}
    return render(request, 'FRONTEND/dashboard_conductor.html', context)

@login_required
@user_passes_test(is_admin, login_url='/mi-cuenta/')
def dashboard_admin(request):
    """Dashboard para usuarios Administradores."""
    total_usuarios = Usuarios.objects.count()
    total_pedidos = Pedidos.objects.count()
    context = {
        'total_usuarios': total_usuarios,
        'total_pedidos': total_pedidos,
        'usuarios_list_url': 'frontend:usuarios_list',
        'pedidos_crud_admin_url': 'frontend:pedidos_crud_admin',
    }
    return render(request, 'FRONTEND/dashboard_admin.html', context)


# ===============================================
# 3. Vistas CRUD (Admin) - Gestión de Usuarios
# ===============================================

@login_required
@user_passes_test(is_admin, login_url='/mi-cuenta/')
def usuarios_list(request):
    """Listado de todos los usuarios (R del CRUD)."""
    usuarios = Usuarios.objects.all().order_by('tipo', 'email')
    context = {'usuarios': usuarios, 'titulo': 'Gestión de Usuarios'}
    # RUTA CORREGIDA
    return render(request, 'FRONTEND/admin_crud/usuarios_list.html', context) 

@login_required
@user_passes_test(is_admin, login_url='/mi-cuenta/')
@require_http_methods(["GET", "POST"])
def usuarios_create(request):
    """Creación de un nuevo usuario (C del CRUD)."""
    if request.method == 'POST':
        form = UsuarioForm(request.POST) 
        if form.is_valid():
            try:
                # 🚨 CORRECCIÓN CLAVE: Usar form.save() para que la lógica de UsuarioForm (hasheo) se ejecute
                form.save()
                messages.success(request, 'Usuario creado exitosamente.')
                return redirect('frontend:usuarios_list')
            except IntegrityError:
                messages.error(request, 'Ya existe un usuario con este correo.')
            except Exception as e:
                messages.error(request, f'Error al crear el usuario: {e}')
        else:
            messages.error(request, 'Error en el formulario. Revisa los datos.')
    else:
        try:
            form = UsuarioForm()
        except NameError:
            messages.error(request, "Error: La clase 'UsuarioForm' no ha sido importada o definida.")
            return redirect('frontend:dashboard_admin') 
            
    context = {'form': form, 'titulo': 'Crear Nuevo Usuario'}
    # RUTA CORREGIDA
    return render(request, 'FRONTEND/admin_crud/usuarios_form.html', context)


@login_required
@user_passes_test(is_admin, login_url='/mi-cuenta/')
@require_http_methods(["GET", "POST"])
def usuarios_update(request, pk):
    """Edición de un usuario existente (U del CRUD)."""
    usuario = get_object_or_404(Usuarios, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario) 
        if form.is_valid():
            # Esta línea estaba bien, ya usa el save() del formulario para manejar la contraseña
            form.save()
            messages.success(request, f'Usuario {usuario.email} actualizado exitosamente.')
            return redirect('frontend:usuarios_list')
        else:
            messages.error(request, 'Error en el formulario. Revisa los datos.')
    else:
        form = UsuarioForm(instance=usuario)
        
    context = {'form': form, 'usuario': usuario, 'titulo': f'Editar Usuario: {usuario.email}'}
    # RUTA CORREGIDA
    return render(request, 'FRONTEND/admin_crud/usuarios_form.html', context)

@login_required
@user_passes_test(is_admin, login_url='/mi-cuenta/')
@require_http_methods(["POST"])
def usuarios_delete(request, pk):
    """Eliminación de un usuario (D del CRUD)."""
    usuario = get_object_or_404(Usuarios, pk=pk)
    
    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta de administrador.')
        return redirect('frontend:usuarios_list')
        
    usuario.delete()
    messages.success(request, f'Usuario {usuario.email} eliminado exitosamente.')
    return redirect('frontend:usuarios_list')


# ===============================================
# 4. Vistas CRUD (Admin) - Gestión de Pedidos
# ===============================================

@login_required
@user_passes_test(is_admin, login_url='/mi-cuenta/')
def pedidos_crud_admin(request):
    """Listado de todos los pedidos para el Admin."""
    pedidos = Pedidos.objects.all().order_by('-fecha_creacion')
    context = {'pedidos': pedidos, 'estados': ESTADOS_PEDIDO, 'titulo': 'Gestión de Pedidos'}
    return render(request, 'FRONTEND/admin_crud/pedidos_list_admin.html', context)

@login_required
@user_passes_test(is_admin, login_url='/mi-cuenta/')
@require_http_methods(["GET", "POST"])
def pedidos_update(request, pk):
    """Edición de un pedido existente (U del CRUD)."""
    pedido = get_object_or_404(Pedidos, pk=pk)
    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            messages.success(request, f'Pedido #{pedido.pk} actualizado exitosamente.')
            return redirect('frontend:pedidos_crud_admin')
        else:
            messages.error(request, 'Error en el formulario. Revisa los datos.')
    else:
        form = PedidoForm(instance=pedido)
        
    context = {'form': form, 'pedido': pedido, 'titulo': f'Editar Pedido: #{pedido.pk}'}
    return render(request, 'FRONTEND/pedidos_form.html', context)

@login_required
@user_passes_test(is_admin, login_url='/mi-cuenta/')
@require_http_methods(["POST"])
def pedidos_delete(request, pk):
    """Eliminación de un pedido (D del CRUD)."""
    pedido = get_object_or_404(Pedidos, pk=pk)
    pedido.delete()
    messages.success(request, f'Pedido #{pedido.pk} eliminado exitosamente.')
    return redirect('frontend:pedidos_crud_admin')


# ===============================================
# 5. Vistas de Acción (Minorista y Conductor)
# ===============================================

@login_required
@user_passes_test(lambda u: is_minorista(u) or is_admin(u), login_url='/mi-cuenta/')
@require_http_methods(["GET", "POST"])
def crear_pedido(request):
    """Permite al Minorista crear un nuevo pedido."""
    if request.method == 'POST':
        form = PedidoForm(request.POST) 
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.minorista = request.user
            pedido.save()
            messages.success(request, f'Pedido #{pedido.pk} creado y en estado Pendiente.')
            return redirect('frontend:listar_pedidos')
        else:
            messages.error(request, 'Error al crear el pedido. Revise los datos.')
    else:
        form = PedidoForm()
        
    context = {'form': form, 'titulo': 'Crear Nuevo Pedido'}
    return render(request, 'FRONTEND/crear_pedido.html', context)


@login_required
def listar_pedidos(request):
    """Lista pedidos relevantes según el rol (Minorista ve los suyos, Conductor los asignados)."""
    role = get_user_role(request.user)
    
    if role == 'MINORISTA':
        pedidos = Pedidos.objects.filter(minorista=request.user).order_by('-fecha_creacion')
        titulo = 'Mis Pedidos'
    elif role == 'CONDUCTOR':
        pedidos = Pedidos.objects.filter(
            Q(conductor=request.user, estado__in=['ASIGNADO', 'EN_RUTA']) | Q(estado='PENDIENTE')
        ).order_by('-fecha_creacion')
        titulo = 'Pedidos Asignados/Disponibles'
    else:
        return redirect('frontend:pedidos_crud_admin')
        
    context = {'pedidos': pedidos, 'titulo': titulo, 'role': role}
    return render(request, 'FRONTEND/listar_pedidos.html', context)


@login_required
@require_http_methods(["POST"])
def manejar_pedido_action(request, pedido_id):
    """Maneja las acciones específicas del Minorista/Conductor (Cancelar, Aceptar, Finalizar)."""
    pedido = get_object_or_404(Pedidos, pk=pedido_id)
    action = request.POST.get('action')
    user = request.user
    role = get_user_role(user)

    try:
        if role == 'MINORISTA':
            if action == 'cancelar' and pedido.minorista == user and pedido.estado == 'PENDIENTE':
                pedido.estado = 'CANCELADO'
                pedido.save()
                messages.success(request, f'Pedido #{pedido.pk} cancelado exitosamente.')
            else:
                messages.error(request, 'Acción no permitida para este pedido/rol.')
        
        elif role == 'CONDUCTOR':
            if action == 'aceptar' and pedido.estado == 'PENDIENTE':
                pedido.conductor = user
                pedido.estado = 'ASIGNADO'
                pedido.save()
                messages.success(request, f'Pedido #{pedido.pk} asignado a ti. ¡A recoger!')
            
            elif action == 'en_ruta' and pedido.conductor == user and pedido.estado == 'ASIGNADO':
                pedido.estado = 'EN_RUTA'
                pedido.save()
                messages.success(request, 'Pedido en ruta.')

            elif action == 'finalizar' and pedido.conductor == user and pedido.estado == 'EN_RUTA':
                pedido.estado = 'ENTREGADO'
                pedido.save()
                messages.success(request, 'Entrega completada exitosamente.')
            else:
                messages.error(request, 'Acción no válida o pedido no asignado a ti.')

        else:
            messages.error(request, 'Tu rol no puede realizar esta acción.')
            
    except Exception as e:
        messages.error(request, f'Ocurrió un error al procesar la acción: {e}')

    return redirect('frontend:listar_pedidos')