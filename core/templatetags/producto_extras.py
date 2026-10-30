from django import template

from core.demo_catalog import nombre_comercial
from core.imagenes import url_imagen_producto

register = template.Library()


@register.filter
def imagen_producto(producto):
    return url_imagen_producto(producto)


@register.filter
def nombre_visible(producto):
    marca = getattr(getattr(producto, "proveedor", None), "nombre", "") or ""
    return nombre_comercial(marca, producto.nombre)
