# FRONTEND/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # <-- Importación necesaria

# El nombre de la aplicación (namespace) es crucial para las redirecciones.
app_name = 'frontend'

urlpatterns = [
    # ----------------------------------------------------
    # --- 1. Vistas Públicas y Autenticación Custom ---
    # ----------------------------------------------------
    path('', views.index, name='index'), 
    
    # Vistas de autenticación personalizadas
    path('mi-cuenta/', views.mi_cuenta_view, name='mi_cuenta'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'), 

    # ----------------------------------------------------
    # --- 2. FLUJO DE RESTABLECIMIENTO DE CONTRASEÑA ---
    # ----------------------------------------------------
    # (Usando las vistas preconstruidas de Django)
    
    # 2.1. Formulario para ingresar el correo 
    path('password-reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='FRONTEND/password_reset_form.html',
            email_template_name='FRONTEND/password_reset_email.html',
            subject_template_name='FRONTEND/password_reset_subject.txt',
            success_url='/password-reset/done/' # Debe coincidir con el paso 2.2
        ), 
        name='password_reset'),

    # 2.2. Pantalla de confirmación después de enviar el correo (Usa tu plantilla 'Instrucciones Enviadas')
    path('password-reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='FRONTEND/password_reset_done.html' # Tu plantilla
        ), 
        name='password_reset_done'),

    # 2.3. Vínculo que llega al correo para ingresar la nueva contraseña
    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='FRONTEND/password_reset_confirm.html',
            success_url='/password-reset/complete/' # Debe coincidir con el paso 2.4
        ), 
        name='password_reset_confirm'),

    # 2.4. Pantalla de éxito después de cambiar la contraseña
    path('password-reset/complete/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='FRONTEND/password_reset_complete.html'
        ), 
        name='password_reset_complete'),
        
    # ----------------------------------------------------
    # --- 3. Rutas de Dashboards (Redirección por Rol) ---
    # ----------------------------------------------------
    
    # URL: /dashboard/ (Función de redirección principal)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # RUTAS ESPECÍFICAS 
    path('dashboard/minorista/', views.dashboard_minorista, name='dashboard_minorista'),
    path('dashboard/conductor/', views.dashboard_conductor, name='dashboard_conductor'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    
    # 3.1. CRUD para el Dashboard de Admin (Gestión de Usuarios)
    # R (Listar/Leer Todos)
    path('dashboard/admin/usuarios/', views.usuarios_list, name='usuarios_list'), 
    # C (Crear)
    path('dashboard/admin/usuarios/crear/', views.usuarios_create, name='usuarios_create'),
    # U (Actualizar/Editar)
    path('dashboard/admin/usuarios/<int:pk>/editar/', views.usuarios_update, name='usuarios_update'),
    # D (Eliminar)
    path('dashboard/admin/usuarios/<int:pk>/eliminar/', views.usuarios_delete, name='usuarios_delete'),
    
    # ----------------------------------------------------
    # --- 4. Gestión de Pedidos (General y CRUD Admin) ---
    # ----------------------------------------------------
    
    # Minorista/Conductor Vistas de Acción
    path('crear-pedido/', views.crear_pedido, name='crear_pedido'),
    path('listar-pedidos/', views.listar_pedidos, name='listar_pedidos'), # Minorista/Conductor lista relevante
    path('pedido/<int:pedido_id>/action/', views.manejar_pedido_action, name='manejar_pedido_action'),

    # 4.1. CRUD Administrativo de Pedidos (NUEVAS RUTAS)
    # R (Listar Todos) - Usada por el enlace del dashboard
    path('dashboard/admin/pedidos/', views.pedidos_crud_admin, name='pedidos_crud_admin'), 
    # U (Actualizar/Editar)
    path('dashboard/admin/pedidos/<int:pk>/editar/', views.pedidos_update, name='pedidos_update'),
    # D (Eliminar)
    path('dashboard/admin/pedidos/<int:pk>/eliminar/', views.pedidos_delete, name='pedidos_delete'),
]
