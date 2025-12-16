from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = 'frontend'

urlpatterns = [
    # ----------------------------------------------------
    # 1. Vistas Públicas y Autenticación
    # ----------------------------------------------------
    path('', views.index_view, name='index'), 
    path('servicios/', views.servicios_view, name='servicios'),
    path('mi-cuenta/', views.mi_cuenta_view, name='mi_cuenta'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # ----------------------------------------------------
    # 2. Recuperación de Contraseña (CORREGIDO)
    # ----------------------------------------------------
    path('password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='FRONTEND/password_reset_form.html',
            email_template_name='FRONTEND/password_reset_email.html',
            subject_template_name='FRONTEND/password_reset_subject.txt',
            success_url=reverse_lazy('frontend:password_reset_done')
        ),
        name='password_reset'),

    path('password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='FRONTEND/password_reset_done.html'
        ),
        name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='FRONTEND/password_reset_confirm.html',
            success_url=reverse_lazy('frontend:password_reset_complete')
        ),
        name='password_reset_confirm'),

    path('password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='FRONTEND/password_reset_complete.html'
        ),
        name='password_reset_complete'),

    # ----------------------------------------------------
    # 3. Dashboards por Rol
    # ----------------------------------------------------
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/minorista/', views.dashboard_minorista, name='dashboard_minorista'),
    path('dashboard/conductor/', views.dashboard_conductor, name='dashboard_conductor'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),

    # ----------------------------------------------------
    # 3.1 Perfil y Registro de Vehículo (CONDUCTOR)
    # ----------------------------------------------------
    path('dashboard/conductor/registrar-vehiculo/', views.registrar_vehiculo_view, name='registrar_vehiculo'),

    # ----------------------------------------------------
    # 3.2 CRUD Administración de Usuarios (Admin)
    # ----------------------------------------------------
    path('gestion/usuarios/', views.usuarios_list, name='usuarios_list'),
    path('gestion/usuarios/crear/', views.usuarios_create, name='usuarios_create'),
    path('gestion/usuarios/<int:pk>/editar/', views.usuarios_update, name='usuarios_update'),
    path('gestion/usuarios/<int:pk>/eliminar/', views.usuarios_delete, name='usuarios_delete'),

    # ----------------------------------------------------
    # 3.3 CRUD Administración de Mayoristas (Admin)
    # ----------------------------------------------------
    path('gestion/mayoristas/', views.MayoristaListView.as_view(), name='empresas_list'),
    path('gestion/mayoristas/crear/', views.MayoristaCreateView.as_view(), name='mayoristas_create'),
    path('gestion/mayoristas/<int:pk>/editar/', views.MayoristaUpdateView.as_view(), name='mayoristas_update'),
    path('gestion/mayoristas/<int:pk>/eliminar/', views.MayoristaDeleteView.as_view(), name='mayoristas_delete'),
    
    # ----------------------------------------------------
    # 4. Gestión de Pedidos (Minorista/Conductor/General)
    # ----------------------------------------------------
    path('pedidos/crear/', views.crear_pedido, name='crear_pedido'),
    path('pedidos/listar/', views.listar_pedidos, name='listar_pedidos'),
    path('pedidos/conductor/listar/', views.listar_pedidos_conductor, name='listar_pedidos_conductor'), 
    path('pedido/<int:pk>/', views.detalle_pedido, name='detalle_pedido'), 
    path('pedido/<int:pedido_id>/action/', views.manejar_pedido_action, name='manejar_pedido_action'),

    # ----------------------------------------------------
    # 4.1 CRUD Administrativo de Pedidos (Admin)
    # ----------------------------------------------------
    path('gestion/pedidos/', views.pedidos_crud_admin, name='pedidos_crud_admin'),
    path('gestion/pedidos/<int:pk>/editar/', views.pedidos_update, name='pedidos_update'),
    path('gestion/pedidos/<int:pk>/eliminar/', views.pedidos_delete, name='pedidos_delete'),
    
    # ----------------------------------------------------
    # 5. Pagos
    # ----------------------------------------------------
    path('pago/<int:factura_id>/', views.procesar_pago_view, name='procesar_pago_view'),
    path('pago/manejar/<int:factura_id>/', views.manejar_pago_action, name='manejar_pago_action'),
]
