from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DetallePedido, Pedidos

def calcular_peso_total(instance):
    pedido = instance.pedido
    
    total_peso = sum(
        (detalle.producto.peso_kg * detalle.cantidad)
        for detalle in DetallePedido.objects.filter(pedido=pedido).select_related('producto')
    )
    
    Pedidos.objects.filter(pk=pedido.pk).update(peso_total=total_peso)

@receiver(post_save, sender=DetallePedido)
def update_peso_on_save(sender, instance, **kwargs):
    calcular_peso_total(instance)

@receiver(post_delete, sender=DetallePedido)
def update_peso_on_delete(sender, instance, **kwargs):
    calcular_peso_total(instance)