from django import forms
from django.forms import inlineformset_factory
from .models import Pedidos, DetallePedido, Empresas, Localidades, Productos

# ==========================================================
# 1. PEDIDO FORM (Encabezado del Pedido)
# ==========================================================

class PedidoForm(forms.ModelForm):
    """
    Formulario para la creación o edición del encabezado de un pedido.
    Se excluyen campos que serán llenados automáticamente en la vista (minorista, mayorista, peso_total, estado).
    """

    class Meta:
        model = Pedidos
        # Campos que el Minorista debe ingresar manualmente:
        fields = [
            'direccion_entrega', 
            'localidad', 
            'fecha_entrega_estimada',
            'notas_adicionales'
        ]
        
        # Widgets para mejor control en el frontend (ej. selector de fecha)
        widgets = {
            'fecha_entrega_estimada': forms.DateInput(attrs={'type': 'date'}),
            'notas_adicionales': forms.Textarea(attrs={'rows': 3}),
        }

    # Sobreescribir el constructor para filtrar opciones de Localidades si es necesario
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Opcional: Si quieres que solo se muestren las Localidades de BOGOCARGO
        # self.fields['localidad'].queryset = Localidades.objects.filter(...)
        
        # Opcional: Ocultar el campo 'minorista' si se pasa en initial (como en views.py)
        # if 'minorista' in self.initial:
        #    self.fields['minorista'].widget = forms.HiddenInput()

# ==========================================================
# 2. DETALLE PEDIDO FORMSET (Líneas de Producto)
# ==========================================================

# Formulario base para una línea de detalle. Se puede usar para agregar validaciones específicas por línea.
class DetallePedidoBaseForm(forms.ModelForm):
    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad']

# Formset para manejar múltiples líneas de DetallePedido asociadas a un solo Pedido.
DetallePedidoFormset = inlineformset_factory(
    parent_model=Pedidos,                 # El modelo padre (el que contiene la clave foránea)
    model=DetallePedido,                  # El modelo hijo (las líneas que se crean)
    form=DetallePedidoBaseForm,           # El formulario a usar para cada línea
    fields=('producto', 'cantidad'),      # Campos visibles en el formulario
    extra=1,                              # Número inicial de formularios vacíos
    can_delete=True                       # Permite eliminar líneas
)

# ==========================================================
# 3. OTROS FORMULARIOS (Si los necesitas en el futuro)
# ==========================================================

# Ejemplo:
# class EmpresaForm(forms.ModelForm):
#    class Meta:
#        model = Empresas
#        fields = '__all__'