from django.shortcuts import get_object_or_404
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from .models import Pedido
from django.db import transaction

@receiver(valid_ipn_received)
def paypal_payment_receiver(sender, **kwargs):
    """
    Esta función se ejecuta cuando PayPal envía una notificación de pago (IPN) válida.
    """
    ipn_obj = sender
    
    # 1. Verificamos que el pago se haya completado
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        
        # 2. Verificamos que la moneda y el receptor del pago sean correctos
        # (Añade más validaciones si es necesario, como el monto)
        if ipn_obj.receiver_email != sender.business:
            # Correo del receptor no coincide, podría ser un intento de fraude.
            return

        # 3. Usamos una transacción para asegurar que la actualización del pedido y el descuento de stock ocurran juntos
        with transaction.atomic():
            try:
                # Obtenemos el pedido usando el 'invoice' que enviamos a PayPal
                pedido = Pedido.objects.select_for_update().get(id=ipn_obj.invoice)

                # Si el pedido ya está pagado, no hacemos nada más para evitar dobles descuentos.
                if pedido.estado == 'PAGADO':
                    return

                # 4. Descontar el stock de cada producto
                for item in pedido.items_pedido.all():
                    producto_original = item.get_related_product()
                    if producto_original:
                        # Usamos select_for_update para bloquear la fila del producto y evitar condiciones de carrera
                        producto_a_actualizar = producto_original.__class__.objects.select_for_update().get(id=producto_original.id)
                        producto_a_actualizar.stock -= item.cantidad
                        producto_a_actualizar.save()

                # 5. Actualizamos el estado del pedido
                pedido.estado = 'PAGADO'
                pedido.paypal_transaccion_id = ipn_obj.txn_id
                pedido.save()
            except Pedido.DoesNotExist:
                print(f"Error: Pedido con ID {ipn_obj.invoice} no encontrado para IPN {ipn_obj.txn_id}")