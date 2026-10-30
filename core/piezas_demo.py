"""Identifica las piezas ficticias del comando cargar_demo_armado.

No hace falta una columna nueva: la marca es el proveedor DEMO y el nombre
empieza por «DEMO ». La tienda pública las excluye siempre. El armador local
puede verlas solo con DEBUG, porque el comando no se ejecuta en producción.
"""
from django.db.models import Q

MARCA_DEMO = 'DEMO'
PREFIJO_DEMO = 'DEMO '


def consulta_demo():
    return Q(proveedor__nombre=MARCA_DEMO) | Q(nombre__startswith=PREFIJO_DEMO)


def es_demo(producto):
    marca = getattr(getattr(producto, 'proveedor', None), 'nombre', '')
    return marca == MARCA_DEMO or str(producto.nombre).startswith(PREFIJO_DEMO)


def sin_demo(consulta):
    return (
        consulta.exclude(proveedor__nombre=MARCA_DEMO)
        .exclude(nombre__startswith=PREFIJO_DEMO)
        .distinct()
    )
