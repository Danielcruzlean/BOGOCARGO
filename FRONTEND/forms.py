from django import forms
from django.core.exceptions import ValidationError
from django_recaptcha.fields import ReCaptchaField
from FRONTEND.models import Pedidos, TIPO_MERCANCIA_CHOICES, Usuarios, Empresas, TIPOS_USUARIO 
from decimal import Decimal
from datetime import datetime, time, timedelta 

# Constante de la hora de corte para el formulario
RECOLECCION_CUTOFF_HOUR = 17 # 5 PM (17:00)

# =======================================================
# 0. FORMULARIO PARA LA ADMINISTRACIÓN DE MAYORISTAS (CRUD)
# =======================================================

class MayoristaForm(forms.ModelForm):
    """Formulario para la gestión de empresas Mayoristas (CRUD Admin)."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Empresas
        exclude = ['usuario', 'tipo'] 
        
        labels = {
            'nombre': 'Nombre Comercial',
            'nit': 'NIT / Identificación',
            'direccion': 'Dirección de Recolección (Mapa Origen)',
            'ciudad': 'Localidad/Ciudad',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm'}),
            'nit': forms.TextInput(attrs={'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm'}),
            'direccion': forms.TextInput(attrs={'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm'}),
        }


# =======================================================
# 1. FORMULARIO DE USUARIO (ADMIN)
# =======================================================

class UsuarioForm(forms.ModelForm):
    """Formulario para la gestión de usuarios por parte de un Admin."""

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
        help_text="Déjalo vacío para no cambiar la contraseña. Obligatorio para nuevos usuarios."
    )

    class Meta:
        model = Usuarios
        fields = [
            "nombre", "apellido", "email", "tipo", "is_active", 
            "password", "placas", "marca_vehiculo", "referencia_vehiculo", "tipo_vehiculo",
        ]

        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "placas": forms.TextInput(attrs={"class": "form-control"}),
            "marca_vehiculo": forms.TextInput(attrs={"class": "form-control"}),
            "referencia_vehiculo": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_vehiculo": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not self.instance.pk and not password:
            raise ValidationError("La contraseña es obligatoria para nuevos usuarios.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password"):
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# =======================================================
# 2. FORMULARIO DE PEDIDOS PARA ADMIN
# =======================================================

class PedidoForm(forms.ModelForm):
    """Formulario completo para gestionar pedidos (uso Admin)."""
    
    class Meta:
        model = Pedidos
        fields = "__all__"
        widgets = {
            "fecha_recoleccion": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "hora_recoleccion": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "tipo_mercancia": forms.Select(attrs={"class": "form-select"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
            "minorista": forms.Select(attrs={"class": "form-select"}),
            "conductor": forms.Select(attrs={"class": "form-select"}),
        }


# =======================================================
# 3. FORMULARIO PARA CREAR PEDIDO (MINORISTA)
# =======================================================

class CrearPedidoMinoristaForm(forms.ModelForm):
    """Formulario para que un usuario Minorista cree un pedido."""
    
    mayorista_origen_id = forms.ChoiceField(
        label="Empresa Mayorista (Distribuidor)",
        choices=[('', '--- Seleccione Mayorista ---')], 
        widget=forms.Select(attrs={"class": "form-select"})
    )

    fecha_recoleccion = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    
    hora_recoleccion = forms.TimeField(
        label="Hora de Recolección",
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"})
    )
    
    tipo_mercancia = forms.ChoiceField(
        label="Tipo de Mercancía",
        choices=TIPO_MERCANCIA_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Pedidos
        fields = [
            "origen", "destino", "tipo_mercancia", "valor_declarado",
            "peso_total", "unidades", "largo", "alto", "ancho", "observaciones",
        ]
        
        field_order = [
            'mayorista_origen_id', 'fecha_recoleccion', 'hora_recoleccion', 
            'origen', 'destino', 'tipo_mercancia', 'valor_declarado',
            'peso_total', 'unidades', 'largo', 'alto', 'ancho', 'observaciones',
        ]

        widgets = {
            "origen": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "destino": forms.TextInput(attrs={"placeholder": "Ej: Calle 26 # 68B-50, Bogotá", "class": "form-control"}),
            "valor_declarado": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "peso_total": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "min": Decimal('0.01')}),
            "unidades": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "largo": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "min": Decimal('0.01')}),
            "alto": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "min": Decimal('0.01')}),
            "ancho": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "min": Decimal('0.01')}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        mayorista_choices = kwargs.pop('mayorista_choices', None)
        super().__init__(*args, **kwargs)
        if mayorista_choices is not None:
            self.fields['mayorista_origen_id'].choices = mayorista_choices

    def clean_origen(self):
        origen = self.cleaned_data.get('origen')
        if not origen or origen.strip() == '':
            raise ValidationError("La dirección de origen es obligatoria.")
        return origen
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_recoleccion = cleaned_data.get('fecha_recoleccion')
        hora_recoleccion = cleaned_data.get('hora_recoleccion')
        
        if fecha_recoleccion and hora_recoleccion:
            now = datetime.now()
            today = now.date()
            if fecha_recoleccion < today:
                self.add_error('fecha_recoleccion', "La fecha no puede ser en el pasado.")
            elif fecha_recoleccion == today:
                recoleccion_datetime = datetime.combine(fecha_recoleccion, hora_recoleccion)
                cutoff_time = time(RECOLECCION_CUTOFF_HOUR, 0, 0)
                cutoff_datetime = datetime.combine(today, cutoff_time)
                if recoleccion_datetime > cutoff_datetime:
                    self.add_error('hora_recoleccion', f"No puede ser posterior a las {RECOLECCION_CUTOFF_HOUR}:00.")
                elif recoleccion_datetime < now:
                    self.add_error('hora_recoleccion', "La hora seleccionada ya ha pasado.")
        return cleaned_data


# =======================================================
# 4. FORMULARIO DE REGISTRO PÚBLICO
# =======================================================

class RegistroForm(forms.ModelForm):
    PUBLIC_CHOICES = [c for c in TIPOS_USUARIO if c[0] not in ['ADMIN']] 
        
    tipo = forms.ChoiceField(
        label="Selecciona tu Rol",
        choices=PUBLIC_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        initial='MINORISTA'
    )
    
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        min_length=8
    )
    
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    captcha = ReCaptchaField(label="")

    class Meta:
        model = Usuarios
        fields = ["nombre", "apellido", "email", "tipo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password2") 
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = True
        if commit:
            user.save()
        return user


# =======================================================
# 5. FORMULARIO ESPECÍFICO PARA REGISTRAR VEHÍCULO
# =======================================================

class VehiculoForm(forms.ModelForm):
    """Formulario para que el Conductor registre/edite su vehículo."""
    
    class Meta:
        model = Usuarios
        fields = ['placas', 'tipo_vehiculo', 'marca_vehiculo', 'referencia_vehiculo']
        
        widgets = {
            'placas': forms.TextInput(attrs={
                'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 uppercase',
                'placeholder': 'Ej: ABC123'
            }),
            'tipo_vehiculo': forms.Select(attrs={
                'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'marca_vehiculo': forms.TextInput(attrs={
                'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Ej: Chevrolet'
            }),
            'referencia_vehiculo': forms.TextInput(attrs={
                'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Ej: NHR 2024'
            }),
        }

    def clean_placas(self):
        placas = self.cleaned_data.get('placas')
        if placas:
            return placas.upper().strip()
        return placas