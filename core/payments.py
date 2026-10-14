import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.models import ST_PP_COMPLETED

from .models import PagoBoleta, Pedido

paypal_logger = logging.getLogger('paypal.ipn')


class PagoNoConfirmado(Exception):
    def __init__(self, motivo):
        self.motivo = motivo
        super().__init__(motivo)


def clp_a_usd(total_clp):
    tasa = Decimal(str(settings.CLP_TO_USD_RATE))
    return (Decimal(total_clp) / tasa).quantize(Decimal('0.01'))


def formulario_paypal(pedido):
    total_usd = clp_a_usd(pedido.total_monto)
    datos = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': f'{total_usd:.2f}',
        'item_name': f'Pedido #{pedido.id} - HardWareHouse',
        'invoice': str(pedido.id),
        'currency_code': 'USD',
        'notify_url': settings.SITE_URL + reverse('paypal-ipn'),
        'return': settings.SITE_URL + reverse('core:payment_success'),
        'cancel_return': settings.SITE_URL + reverse('core:payment_failed'),
    }
    return PayPalPaymentsForm(initial=datos), total_usd


def confirmar_pago_paypal(ipn_obj):
    """Marca el pedido como pagado solo con un IPN Completed ya verificado por PayPal."""
    txn_id = (getattr(ipn_obj, 'txn_id', None) or '').strip()
    paypal_logger.info(
        'IPN recibida. Transacción: %s. Estado: %s. Invoice: %s.',
        txn_id or 'sin id',
        ipn_obj.payment_status,
        ipn_obj.invoice,
    )

    if ipn_obj.payment_status != ST_PP_COMPLETED:
        paypal_logger.warning(
            'Pago no confirmado (%s) para la transacción %s. El pedido sigue pendiente y el stock no cambia.',
            ipn_obj.payment_status,
            txn_id or 'sin id',
        )
        return 'ignorado'

    if bool(ipn_obj.test_ipn) != bool(settings.PAYPAL_TEST):
        paypal_logger.warning(
            'IPN de otro entorno (test_ipn=%s, PAYPAL_TEST=%s). No se confirma el pedido.',
            ipn_obj.test_ipn,
            settings.PAYPAL_TEST,
        )
        return 'rechazado'

    if not txn_id:
        paypal_logger.error('IPN Completed sin txn_id. No se confirma el pedido.')
        return 'rechazado'

    receptor = (ipn_obj.receiver_email or '').strip().casefold()
    esperado = (settings.PAYPAL_RECEIVER_EMAIL or '').strip().casefold()
    if not esperado or receptor != esperado:
        paypal_logger.warning(
            'El receptor del pago no es la cuenta configurada. Recibido: %s.',
            ipn_obj.receiver_email,
        )
        return 'rechazado'

    if (ipn_obj.mc_currency or '').upper() != 'USD':
        paypal_logger.warning('Moneda inesperada: %s.', ipn_obj.mc_currency)
        return 'rechazado'

    try:
        pedido_id = int(str(ipn_obj.invoice).strip())
    except (TypeError, ValueError):
        paypal_logger.error('Invoice inválido: %s.', ipn_obj.invoice)
        return 'pedido_invalido'

    try:
        with transaction.atomic():
            try:
                pedido = Pedido.objects.select_for_update().get(id=pedido_id)
            except Pedido.DoesNotExist:
                paypal_logger.error('No existe el pedido #%s para la transacción %s.', pedido_id, txn_id)
                return 'pedido_invalido'

            if pedido.estado != 'PENDIENTE' or pedido.paypal_transaccion_id:
                paypal_logger.warning(
                    'El pedido #%s ya no está pendiente (%s, transacción %s). No se vuelve a descontar stock.',
                    pedido.id,
                    pedido.estado,
                    pedido.paypal_transaccion_id,
                )
                return 'ya_procesado'

            if PagoBoleta.objects.filter(transaccion_id=txn_id).exists():
                paypal_logger.warning('La transacción %s ya tiene una boleta. No se descuenta stock otra vez.', txn_id)
                return 'ya_procesado'

            try:
                pagado = Decimal(ipn_obj.mc_gross).quantize(Decimal('0.01'))
            except (InvalidOperation, TypeError):
                raise PagoNoConfirmado('monto')

            if pagado != clp_a_usd(pedido.total_monto):
                paypal_logger.warning(
                    'El monto de la transacción %s (%s USD) no coincide con el pedido #%s.',
                    txn_id,
                    pagado,
                    pedido.id,
                )
                raise PagoNoConfirmado('monto')

            items = list(pedido.items_pedido.select_for_update().order_by('id'))
            if not items:
                raise PagoNoConfirmado('sin_items')

            reservados = []
            for item in items:
                producto = item.get_related_product()
                if producto is None:
                    paypal_logger.error(
                        'El ítem %s del pedido #%s no apunta a un producto con stock.',
                        item.id,
                        pedido.id,
                    )
                    raise PagoNoConfirmado('producto')
                reservados.append((item, producto))

            reservados.sort(key=lambda par: (par[1]._meta.label, par[1].pk, par[0].pk))
            for item, producto in reservados:
                bloqueado = producto.__class__.objects.select_for_update().get(pk=producto.pk)
                if bloqueado.stock < item.cantidad:
                    paypal_logger.error(
                        'Stock insuficiente de %s (hay %s, se piden %s). El pedido #%s sigue pendiente.',
                        bloqueado.nombre,
                        bloqueado.stock,
                        item.cantidad,
                        pedido.id,
                    )
                    raise PagoNoConfirmado('stock')
                bloqueado.stock -= item.cantidad
                bloqueado.save(update_fields=['stock'])

            pedido.estado = 'PAGADO'
            pedido.paypal_transaccion_id = txn_id
            pedido.save(update_fields=['estado', 'paypal_transaccion_id'])
            PagoBoleta.objects.create(
                pedido=pedido,
                monto_pagado=pedido.total_monto,
                metodo_pago='PayPal',
                transaccion_id=txn_id,
                nombre_comprador=_nombre_comprador(ipn_obj, pedido),
                email_comprador=_correo_comprador(ipn_obj, pedido),
            )
        paypal_logger.info('Pedido #%s pagado con la transacción %s.', pedido_id, txn_id)
        return 'pagado'
    except PagoNoConfirmado as exc:
        paypal_logger.error('Pago no aplicado (%s) para la transacción %s.', exc.motivo, txn_id)
        return 'rechazado'
    except IntegrityError:
        paypal_logger.error('No se pudo guardar la transacción %s sin duplicarla.', txn_id)
        return 'rechazado'


def _nombre_comprador(ipn_obj, pedido):
    nombre = f'{ipn_obj.first_name or ""} {ipn_obj.last_name or ""}'.strip()
    if not nombre:
        nombre = pedido.usuario.get_full_name() or pedido.usuario.username
    return nombre[:200]


def _correo_comprador(ipn_obj, pedido):
    for candidato in (ipn_obj.payer_email, pedido.usuario.email):
        if not candidato:
            continue
        try:
            validate_email(candidato)
        except ValidationError:
            continue
        return candidato
    return 'comprador@sandbox.paypal.com'
