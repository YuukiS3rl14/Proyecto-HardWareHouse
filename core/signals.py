import logging

from django.dispatch import receiver
from paypal.standard.ipn.signals import invalid_ipn_received, valid_ipn_received

from .payments import confirmar_pago_paypal

paypal_logger = logging.getLogger('paypal.ipn')


@receiver(valid_ipn_received)
def paypal_payment_receiver(sender, **kwargs):
    confirmar_pago_paypal(sender)


@receiver(invalid_ipn_received)
def paypal_ipn_rechazada(sender, **kwargs):
    paypal_logger.warning(
        'IPN rechazada por PayPal. id=%s txn=%s invoice=%s codigo=%s.',
        sender.pk,
        (getattr(sender, 'txn_id', None) or '').strip() or 'sin id',
        (getattr(sender, 'invoice', None) or '').strip() or 'sin invoice',
        (getattr(sender, 'flag_code', None) or '').strip() or 'sin codigo',
    )
