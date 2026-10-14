from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver

from .payments import confirmar_pago_paypal


@receiver(valid_ipn_received)
def paypal_payment_receiver(sender, **kwargs):
    confirmar_pago_paypal(sender)
