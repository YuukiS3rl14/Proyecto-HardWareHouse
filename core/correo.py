"""Avisos por EmailJS. Las claves salen solo en la petición del servidor."""
import logging
import uuid
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import AvisoCorreoPedido, PagoBoleta, Pedido

logger = logging.getLogger('hardwarehouse.correo')

EMAILJS_URL = 'https://api.emailjs.com/api/v1.0/email/send'


def ip_cliente(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    partes = [parte.strip() for parte in forwarded.split(',') if parte.strip()]
    if partes:
        return partes[-1]
    return request.META.get('REMOTE_ADDR') or 'desconocida'


def contacto_bloqueado(request):
    """True cuando esta IP ya usó el cupo y el formulario no debe llamar a EmailJS."""
    limite = int(getattr(settings, 'CONTACTO_CORREO_LIMITE', 5))
    ventana = int(getattr(settings, 'CONTACTO_CORREO_VENTANA', 600))
    if limite <= 0:
        return False
    clave = f'hw_contacto:{ip_cliente(request)}'
    actual = cache.get(clave)
    if actual is None:
        cache.set(clave, 1, ventana)
        return False
    if int(actual) >= limite:
        return True
    try:
        nuevo = cache.incr(clave)
    except ValueError:
        cache.set(clave, 1, ventana)
        return False
    return int(nuevo) > limite


def enviar_contacto(datos):
    parametros = {
        'from_name': datos['nombre'],
        'nombre': datos['nombre'],
        'from_email': datos['email'],
        'email': datos['email'],
        'correo': datos['email'],
        'reply_to': datos['email'],
        'telefono': datos.get('telefono') or 'No indicado',
        'asunto': datos['asunto'],
        'subject': datos['asunto'],
        'mensaje': datos['mensaje'],
        'message': datos['mensaje'],
        'to_name': 'HardWareHouse',
    }
    return _enviar(settings.EMAILJS_TEMPLATE_CONTACTO, parametros)


def notificar_pedido_pagado(pedido_id):
    """Envía el detalle guardado en PostgreSQL. No modifica el estado del pedido."""
    try:
        return _notificar_pedido_pagado(pedido_id)
    except Exception:
        logger.exception('El aviso del pedido #%s falló sin tocar el pago.', pedido_id)
        return 'error'


def _notificar_pedido_pagado(pedido_id):
    token = uuid.uuid4()
    ahora = timezone.now()
    ventana = timedelta(seconds=int(getattr(settings, 'EMAILJS_RECLAMO_SEGUNDOS', 120)))
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().filter(pk=pedido_id).first()
        if pedido is None or pedido.estado != 'PAGADO':
            return 'omitido'
        boleta = PagoBoleta.objects.select_for_update().filter(pedido_id=pedido.pk).first()
        if boleta is None:
            return 'omitido'
        aviso = _aviso_bloqueado(pedido)
        if aviso.enviado_en is not None:
            return 'omitido'
        if _reclamo_vigente(aviso, ahora, ventana):
            return 'omitido'
        aviso.reclamo = token
        aviso.reclamo_en = ahora
        aviso.save(update_fields=['reclamo', 'reclamo_en'])
        parametros = _parametros_pedido(pedido, boleta)

    enviado = _enviar(settings.EMAILJS_TEMPLATE_PEDIDO, parametros)
    with transaction.atomic():
        aviso = AvisoCorreoPedido.objects.select_for_update().get(pedido_id=pedido_id)
        if aviso.reclamo != token:
            return 'omitido'
        if enviado:
            aviso.enviado_en = timezone.now()
        aviso.reclamo = None
        aviso.reclamo_en = None
        aviso.save(update_fields=['enviado_en', 'reclamo', 'reclamo_en'])
    return 'enviado' if enviado else 'error'


def _reclamo_vigente(aviso, ahora, ventana):
    return bool(aviso.reclamo and aviso.reclamo_en and aviso.reclamo_en > ahora - ventana)


def _aviso_bloqueado(pedido):
    try:
        return AvisoCorreoPedido.objects.select_for_update().get(pedido=pedido)
    except AvisoCorreoPedido.DoesNotExist:
        try:
            return AvisoCorreoPedido.objects.create(pedido=pedido)
        except IntegrityError:
            return AvisoCorreoPedido.objects.select_for_update().get(pedido=pedido)


def _parametros_pedido(pedido, boleta):
    lineas = []
    for item in pedido.items_pedido.order_by('id'):
        subtotal = item.precio_unitario * item.cantidad
        lineas.append(
            f'{item.cantidad} x {item.producto_nombre} ({item.producto_tipo}) '
            f'— {_clp(item.precio_unitario)} c/u — {_clp(subtotal)}'
        )
    detalle = '\n'.join(lineas) or 'Sin productos registrados.'
    total = _clp(boleta.monto_pagado)
    return {
        'to_email': boleta.email_comprador,
        'email': boleta.email_comprador,
        'to_name': boleta.nombre_comprador,
        'nombre': boleta.nombre_comprador,
        'pedido_id': str(pedido.id),
        'numero_pedido': f'#{pedido.id}',
        'order_id': str(pedido.id),
        'fecha_pedido': _fecha(pedido.fecha_pedido),
        'fecha_pago': _fecha(boleta.fecha_pago),
        'transaccion_id': boleta.transaccion_id,
        'transaccion': boleta.transaccion_id,
        'total': total,
        'total_clp': total,
        'direccion': pedido.direccion_envio or 'No especificada',
        'productos': detalle,
        'detalle': detalle,
        'items': detalle,
    }


def _clp(valor):
    entero = int(Decimal(valor).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    return f'{entero:,}'.replace(',', '.') + ' CLP'


def _fecha(momento):
    if momento is None:
        return ''
    return timezone.localtime(momento).strftime('%d/%m/%Y %H:%M')


def _enviar(template_id, parametros):
    servicio = (getattr(settings, 'EMAILJS_SERVICE_ID', '') or '').strip()
    publico = (getattr(settings, 'EMAILJS_PUBLIC_KEY', '') or '').strip()
    privado = (getattr(settings, 'EMAILJS_PRIVATE_KEY', '') or '').strip()
    plantilla = (template_id or '').strip()
    if not (servicio and publico and privado and plantilla):
        logger.error('EmailJS no está configurado. No se envió el correo.')
        return False
    cuerpo = {
        'service_id': servicio,
        'template_id': plantilla,
        'user_id': publico,
        'accessToken': privado,
        'template_params': parametros,
    }
    try:
        respuesta = requests.post(
            EMAILJS_URL,
            json=cuerpo,
            timeout=int(getattr(settings, 'EMAILJS_TIMEOUT', 10)),
        )
    except requests.RequestException:
        logger.exception('EmailJS no respondió.')
        return False
    if respuesta.status_code != 200:
        logger.error('EmailJS respondió HTTP %s.', respuesta.status_code)
        return False
    return True
