"""Cantidades de carrito: entero positivo y tope de stock en el servidor."""
from __future__ import annotations

import re

from django.db import transaction

MENSAJE_ENTERO = 'La cantidad debe ser un número entero positivo.'
MENSAJE_VACIA = 'Ingresa una cantidad.'
MENSAJE_MINIMO = 'La cantidad mínima es 1.'
MENSAJE_SIN_STOCK = 'Este producto no tiene stock disponible.'
_DIGITOS = re.compile(r'[0-9]+')


class CantidadInvalida(Exception):
    def __init__(self, mensaje: str):
        self.mensaje = mensaje
        super().__init__(mensaje)


def mensaje_stock(stock: int) -> str:
    return f'Solo hay {stock} unidades disponibles.'


def parsear_cantidad(valor, stock_disponible: int) -> int:
    """Acepta un entero >= 1 que no supere el stock. El precio no se lee aquí."""
    if isinstance(valor, bool) or not isinstance(valor, (str, int)):
        raise CantidadInvalida(MENSAJE_ENTERO)
    texto = str(valor).strip()
    if texto == '':
        raise CantidadInvalida(MENSAJE_VACIA)
    if _DIGITOS.fullmatch(texto) is None:
        raise CantidadInvalida(MENSAJE_ENTERO)
    cantidad = int(texto)
    if cantidad < 1:
        raise CantidadInvalida(MENSAJE_MINIMO)
    disponible = int(stock_disponible or 0)
    if disponible < 1:
        raise CantidadInvalida(MENSAJE_SIN_STOCK)
    if cantidad > disponible:
        raise CantidadInvalida(mensaje_stock(disponible))
    return cantidad


def revalidar_lineas(items) -> list[str]:
    """Lee el stock actual con bloqueo. No descuenta ni reescribe pedidos."""
    pares = []
    errores = []
    for item in items:
        producto = item.get_related_product()
        if producto is None:
            errores.append('Un producto del carrito ya no está disponible.')
            continue
        pares.append((item, producto))
    pares.sort(key=lambda par: (par[1]._meta.label, par[1].pk, par[0].pk))
    with transaction.atomic():
        for item, producto in pares:
            bloqueado = producto.__class__.objects.select_for_update().get(pk=producto.pk)
            if item.cantidad < 1 or bloqueado.stock < item.cantidad:
                errores.append(
                    f"No hay suficiente stock para '{bloqueado.nombre}'. "
                    f'Solo quedan {bloqueado.stock} unidades. Por favor, ajusta tu carrito.'
                )
    return errores
