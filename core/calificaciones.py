"""Calificaciones de reseña en medios puntos, de 0,5 a 5.

Lo usan core/models.py (campo Comentario.calificacion), core/forms.py,
core/widgets.py y core/templatetags/producto_extras.py. No existe otro
módulo de medios puntos. El usuario pidió: "Si el modelo utiliza únicamente
enteros, modificarlo de manera compatible para aceptar medios puntos,
preferentemente con DecimalField".
"""
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError

PASO = Decimal('0.5')
MINIMO = Decimal('0.5')
MAXIMO = Decimal('5.0')
PASOS = tuple(
    (Decimal(indice) * PASO).quantize(Decimal('0.1'))
    for indice in range(1, 11)
)


def a_decimal(valor):
    try:
        return Decimal(str(valor)).quantize(Decimal('0.1'))
    except Exception as error:
        raise ValidationError('La calificación no es válida.') from error


def validar_media_estrella(valor):
    numero = a_decimal(valor)
    if numero not in PASOS:
        raise ValidationError(
            'La calificación debe ir de 0,5 a 5, en medios puntos.'
        )
    return numero


def texto_calificacion(valor):
    numero = Decimal(str(valor or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    visible = format(numero, 'f').rstrip('0').rstrip('.') or '0'
    return f'{visible.replace(".", ",")} de 5 estrellas'


def estados_estrella(valor):
    """Estrellas completas, medias o vacías, redondeadas al medio punto más cercano."""
    try:
        numero = Decimal(str(valor or 0))
    except Exception:
        numero = Decimal('0')
    medios = (numero * 2).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    visual = medios / 2
    estados = []
    for indice in range(1, 6):
        if visual >= indice:
            estados.append('full')
        elif visual >= Decimal(indice) - PASO:
            estados.append('half')
        else:
            estados.append('empty')
    return estados
