import logging
import uuid
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.models import ST_PP_COMPLETED

from .models import Carrito, ItemPedido, PagoBoleta, Pedido

SESION_VERIFICANDO = 'paypal_verificando'

paypal_logger = logging.getLogger('paypal.ipn')


class PagoNoConfirmado(Exception):
    def __init__(self, motivo):
        self.motivo = motivo
        super().__init__(motivo)


def clp_a_usd(total_clp):
    tasa = Decimal(str(settings.CLP_TO_USD_RATE))
    return (Decimal(total_clp) / tasa).quantize(Decimal('0.01'))


def _dinero(valor):
    return Decimal(valor).quantize(Decimal('0.01'))


def _firma_carrito(items):
    filas = []
    for item in items:
        producto = item.get_related_product()
        modelo = item.get_model_name()
        if producto is None or not modelo:
            return None
        filas.append((modelo, producto.pk, item.cantidad, _dinero(item.precio_unitario)))
    return tuple(sorted(filas))


def _firma_pedido(pedido):
    filas = []
    for item in pedido.items_pedido.all():
        if not item.producto_modelo or not item.producto_pk:
            return None
        filas.append((
            item.producto_modelo,
            item.producto_pk,
            item.cantidad,
            _dinero(item.precio_unitario),
        ))
    return tuple(sorted(filas))


def preparar_pedido_checkout(usuario, items_carrito):
    """Reutiliza un pendiente del mismo usuario solo si el carrito coincide exactamente."""
    items = list(items_carrito)
    firma_nueva = _firma_carrito(items)
    total = _dinero(sum((item.get_total() for item in items), Decimal('0')))
    with transaction.atomic():
        candidatos = (
            Pedido.objects.select_for_update()
            .filter(usuario=usuario, estado='PENDIENTE')
            .order_by('-id')
        )
        for pedido in candidatos:
            if (pedido.paypal_transaccion_id or '').strip():
                continue
            if PagoBoleta.objects.filter(pedido_id=pedido.id).exists():
                continue
            if firma_nueva is None or _firma_pedido(pedido) != firma_nueva:
                continue
            if _dinero(pedido.total_monto) != total:
                continue
            paypal_logger.info(
                'Checkout reutiliza el pedido pendiente #%s del usuario %s (%s líneas).',
                pedido.id,
                usuario.pk,
                len(firma_nueva),
            )
            return pedido

        pedido = Pedido.objects.create(
            usuario=usuario,
            estado='PENDIENTE',
            total_monto=total,
            direccion_envio='Por definir',
            paypal_invoice=uuid.uuid4(),
        )
        for item in items:
            producto = item.get_related_product()
            ItemPedido.objects.create(
                pedido=pedido,
                producto_nombre=producto.nombre,
                producto_tipo=producto.categoria,
                precio_unitario=item.precio_unitario,
                cantidad=item.cantidad,
                producto_modelo=item.get_model_name() or '',
                producto_pk=producto.pk,
            )
        paypal_logger.info(
            'Checkout crea el pedido pendiente #%s del usuario %s (%s líneas).',
            pedido.id,
            usuario.pk,
            pedido.items_pedido.count(),
        )
        return pedido


def retirar_carrito_si_coincide(pedido):
    """Quita del carrito solo las líneas que siguen siendo exactamente el pedido ya pagado."""
    carrito = Carrito.objects.filter(usuario_id=pedido.usuario_id).first()
    if carrito is None:
        return
    items = list(carrito.items.all())
    if not items or _firma_carrito(items) != _firma_pedido(pedido):
        paypal_logger.info(
            'El carrito del usuario %s no coincide con el pedido #%s. Se conserva.',
            pedido.usuario_id,
            pedido.id,
        )
        return
    carrito.items.all().delete()
    paypal_logger.info(
        'Carrito del usuario %s vaciado al confirmar el pedido #%s.',
        pedido.usuario_id,
        pedido.id,
    )


def formulario_paypal(pedido):
    total_usd = clp_a_usd(pedido.total_monto)
    regreso = settings.SITE_URL + reverse('core:payment_success') + f'?pedido={pedido.id}'
    cancelacion = settings.SITE_URL + reverse('core:payment_failed') + f'?pedido={pedido.id}'
    datos = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': f'{total_usd:.2f}',
        'item_name': f'Pedido #{pedido.id} - HardWareHouse',
        'invoice': str(pedido.paypal_invoice),
        'currency_code': 'USD',
        'notify_url': settings.SITE_URL + reverse('paypal-ipn'),
        'return': regreso,
        'cancel_return': cancelacion,
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
            'El receptor del pago no es la cuenta configurada. Transacción %s. Invoice: %s.',
            txn_id or 'sin id',
            ipn_obj.invoice,
        )
        return 'rechazado'

    if (ipn_obj.mc_currency or '').upper() != 'USD':
        paypal_logger.warning('Moneda inesperada: %s.', ipn_obj.mc_currency)
        return 'rechazado'

    invoice = str(getattr(ipn_obj, 'invoice', '') or '').strip()
    identificador = _uuid_o_nada(invoice)
    if identificador is None and not invoice.isdigit():
        paypal_logger.error(
            'Invoice desconocido: %s. No se confirma ningún pedido.',
            invoice or 'vacío',
        )
        return 'invoice_desconocido'

    try:
        with transaction.atomic():
            if identificador is not None:
                pedido = Pedido.objects.select_for_update().filter(paypal_invoice=identificador).first()
                if pedido is None:
                    paypal_logger.error(
                        'Invoice desconocido: %s. No se confirma ningún pedido.',
                        invoice,
                    )
                    return 'invoice_desconocido'
            else:
                pedido = (
                    Pedido.objects.select_for_update()
                    .filter(paypal_invoice_legado=invoice)
                    .first()
                )
                if pedido is None:
                    paypal_logger.error(
                        'Invoice legado numérico %s rechazado. No coincide con un invoice guardado '
                        'y no se usa el número de pedido. Si PayPal cobró ese invoice, requiere conciliación manual.',
                        invoice,
                    )
                    return 'invoice_desconocido'
                paypal_logger.info(
                    'IPN con invoice legado %s asociado al pedido #%s por el invoice guardado.',
                    invoice,
                    pedido.id,
                )

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
        paypal_logger.info('Pedido #%s pagado con la transacción %s.', pedido.id, txn_id)
        try:
            retirar_carrito_si_coincide(pedido)
        except Exception:
            paypal_logger.exception(
                'El pedido #%s quedó pagado, pero no se pudo actualizar el carrito.',
                pedido.id,
            )
        return 'pagado'
    except PagoNoConfirmado as exc:
        paypal_logger.error('Pago no aplicado (%s) para la transacción %s.', exc.motivo, txn_id)
        return 'rechazado'
    except IntegrityError:
        paypal_logger.error('No se pudo guardar la transacción %s sin duplicarla.', txn_id)
        return 'rechazado'


def _uuid_o_nada(valor):
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError, TypeError):
        return None


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
