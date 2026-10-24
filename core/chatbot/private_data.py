"""Consultas que requieren usuario autenticado (sin exponer datos de terceros)."""
from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser
from django.urls import reverse

from core.models import Pedido


def _formato_clp(valor) -> str:
    entero = int(valor)
    return f'${entero:,}'.replace(',', '.')


def respuesta_mis_pedidos(usuario: AbstractBaseUser | None, limite: int = 5) -> dict:
    if usuario is None or not usuario.is_authenticated:
        login_url = reverse('core:login')
        pedidos_url = reverse('core:mis_pedidos')
        return {
            'reply': (
                'Para ver el estado de tus pedidos necesitas iniciar sesión en tu cuenta. '
                f'Entra en {login_url} y luego revisa {pedidos_url}.'
            ),
            'requiere_login': True,
        }

    qs = (
        Pedido.objects.filter(usuario=usuario)
        .order_by('-fecha_pedido')[: max(1, min(limite, 10))]
    )
    if not qs:
        return {
            'reply': (
                'No tienes pedidos registrados con esta cuenta. '
                f'Cuando compres, aparecerán en {reverse("core:mis_pedidos")}.'
            ),
            'pedidos': [],
        }

    lineas = ['Tus pedidos más recientes (solo tu cuenta):']
    pedidos_json = []
    for pedido in qs:
        lineas.append(
            f'• Pedido #{pedido.id} — {pedido.get_estado_display()} — '
            f'{_formato_clp(pedido.total_monto)} CLP — '
            f'{pedido.fecha_pedido.strftime("%d-%m-%Y %H:%M")}'
        )
        pedidos_json.append(
            {
                'id': pedido.id,
                'estado': pedido.estado,
                'estado_etiqueta': pedido.get_estado_display(),
                'total_clp': int(pedido.total_monto),
                'fecha': pedido.fecha_pedido.isoformat(),
            }
        )
    lineas.append(f'Detalle completo: {reverse("core:mis_pedidos")}.')
    return {'reply': '\n'.join(lineas), 'pedidos': pedidos_json}
