from django.shortcuts import get_object_or_404
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from .models import Pedido
from django.db import transaction
import logging

paypal_logger = logging.getLogger('paypal.ipn')

@receiver(valid_ipn_received)
def paypal_payment_receiver(sender, **kwargs):
    ipn_obj = sender
    paypal_logger.info(f"Señal de IPN recibida. ID de transacción: {ipn_obj.txn_id}, Estado: {ipn_obj.payment_status}")
    
    # 1. Verificamos que el pago se haya completado
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        paypal_logger.info(f"Pago COMPLETADO para el pedido #{ipn_obj.invoice}.")
        
        # 2. Verificamos que la moneda y el receptor del pago sean correctos
        if ipn_obj.receiver_email != sender.business:
            paypal_logger.warning(f"¡ALERTA DE SEGURIDAD! El email del receptor no coincide. Esperado: {sender.business}, Recibido: {ipn_obj.receiver_email}")
            return

        # 3. Usamos una transacción para asegurar que la actualización del pedido y el descuento de stock ocurran juntos
        with transaction.atomic():
            try:
                paypal_logger.info(f"Iniciando transacción para el pedido #{ipn_obj.invoice}.")
                pedido = Pedido.objects.select_for_update().get(id=ipn_obj.invoice)

                if pedido.estado == 'PAGADO':
                    paypal_logger.warning(f"El pedido #{ipn_obj.invoice} ya estaba marcado como PAGADO. No se realizarán más acciones.")
                    return

                # 4. Descontar el stock de cada producto
                for item in pedido.items_pedido.all():
                    producto_original = item.get_related_product()
                    if producto_original:
                        producto_a_actualizar = producto_original.__class__.objects.select_for_update().get(id=producto_original.id)
                        
                        paypal_logger.info(f"Descontando stock para '{producto_original.nombre}' (ID: {producto_original.id}). Stock actual: {producto_a_actualizar.stock}, Cantidad: {item.cantidad}")
                        producto_a_actualizar.stock -= item.cantidad
                        producto_a_actualizar.save()
                        paypal_logger.info(f"Nuevo stock para '{producto_original.nombre}': {producto_a_actualizar.stock}")

                # 5. Actualizamos el estado del pedido
                pedido.estado = 'PAGADO'
                pedido.paypal_transaccion_id = ipn_obj.txn_id
                pedido.save()
                paypal_logger.info(f"¡ÉXITO! El pedido #{pedido.id} ha sido actualizado a PAGADO.")

            except Pedido.DoesNotExist:
                paypal_logger.error(f"¡ERROR CRÍTICO! Pedido con ID {ipn_obj.invoice} no encontrado en la base de datos para la IPN con ID de transacción {ipn_obj.txn_id}")
    else:
        paypal_logger.warning(f"El estado del pago no es 'Completed'. Estado recibido: {ipn_obj.payment_status}. No se procesará el pedido.")