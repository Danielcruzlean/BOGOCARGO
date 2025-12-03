# FRONTEND/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
# Importa tus modelos desde BACKEND
from BACKEND.models import Pedidos

# Obtener tu modelo de usuario personalizado
Usuarios = get_user_model()

# =======================================================
# 1. Formulario para el CRUD de Usuarios (Admin)
# =======================================================

class UsuarioForm(forms.ModelForm):
    """
    Formulario para crear y editar el modelo de Usuarios.
    Maneja el hasheo de la contraseña automáticamente en el método save().
    """
    # Campo de contraseña personalizado para manejar la actualización
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        required=False,
        help_text="Déjalo vacío para no cambiar la contraseña. **Obligatorio para nuevos usuarios.**"
    )
    
    class Meta:
        model = Usuarios
        fields = [
            'nombre', 
            'apellido', 
            'email', 
            'tipo', # Minorista, Conductor, Admin
            'is_active', 
            'telefono',
            'disponibilidad', # Para el conductor
            'password' # El campo personalizado aquí
        ]
        
    def clean_password(self):
        """Valida que la contraseña sea obligatoria en la creación."""
        password = self.cleaned_data.get('password')
        # Verifica si el formulario NO tiene una instancia (es decir, es una CREACIÓN)
        if not self.instance.pk and not password:
            # Si es creación y no hay contraseña, lanza error
            raise ValidationError("La contraseña es obligatoria para la creación de un nuevo usuario.")
        return password
        
    def save(self, commit=True):
        """
        Sobreescribe save para hashear la contraseña solo si se proporciona.
        """
        user = super().save(commit=False)
        
        # Hashea la contraseña si se proporcionó en el formulario
        if self.cleaned_data.get("password"):
            user.set_password(self.cleaned_data["password"])
        # Si NO se proporcionó contraseña, la mantiene sin cambios (esto solo funciona en UPDATE)
        
        if commit:
            user.save()
        return user


# =======================================================
# 2. Formulario para el CRUD de Pedidos (Admin/Minorista)
# =======================================================

class PedidoForm(forms.ModelForm):
    """
    Formulario para crear y editar el modelo de Pedidos.
    """
    peso_total_kg = forms.DecimalField(
        label='Peso total de la carga (kg)',
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': 'Ej: 15.50 kg', 'min': 0.01})
    )
    
    class Meta:
        model = Pedidos
        fields = [
            # ForeignKeys
            'minorista', 
            'conductor', 
            
            'estado', 
            
            # Campos de texto y ubicación
            'origen',
            'destino',
            
            'descripcion_carga', 
            'peso_total_kg', 
        ]
        
        widgets = {
            'descripcion_carga': forms.TextInput(attrs={'placeholder': 'Ej: 10 cajas, Paquetes pequeños'}),
        }