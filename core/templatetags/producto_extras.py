from django import template

from core.calificaciones import estados_estrella, texto_calificacion
from core.demo_catalog import nombre_comercial
from core.imagenes import url_imagen_producto

register = template.Library()


@register.filter
def imagen_producto(producto):
    return url_imagen_producto(producto)


@register.inclusion_tag('core/includes/estrellas_lectura.html')
def estrellas(valor):
    return {'estados': estados_estrella(valor), 'texto': texto_calificacion(valor)}


@register.filter
def nombre_visible(producto):
    marca = getattr(getattr(producto, "proveedor", None), "nombre", "") or ""
    return nombre_comercial(marca, producto.nombre)
