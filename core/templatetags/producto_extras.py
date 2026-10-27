from django import template

from core.demo_catalog import nombre_comercial

register = template.Library()


@register.filter
def nombre_visible(producto):
    marca = getattr(getattr(producto, "proveedor", None), "nombre", "") or ""
    return nombre_comercial(marca, producto.nombre)
