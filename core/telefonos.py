"""Prefijos telefónicos del formulario de contacto.

Chile es el valor inicial. Cada país declara su propio largo: la regla
de 9 dígitos que empiezan con 9 solo aplica a los móviles de Chile.
"""
import re

from django.core.exceptions import ValidationError

PAISES = (
    {'codigo': 'CL', 'nombre': 'Chile', 'prefijo': '56', 'bandera': '🇨🇱', 'min': 9, 'max': 9, 'inicio': '9', 'ejemplo': '912345678'},
    {'codigo': 'AR', 'nombre': 'Argentina', 'prefijo': '54', 'bandera': '🇦🇷', 'min': 10, 'max': 11, 'inicio': '', 'ejemplo': '9112345678'},
    {'codigo': 'PE', 'nombre': 'Perú', 'prefijo': '51', 'bandera': '🇵🇪', 'min': 9, 'max': 9, 'inicio': '', 'ejemplo': '912345678'},
    {'codigo': 'BO', 'nombre': 'Bolivia', 'prefijo': '591', 'bandera': '🇧🇴', 'min': 8, 'max': 8, 'inicio': '', 'ejemplo': '71234567'},
    {'codigo': 'BR', 'nombre': 'Brasil', 'prefijo': '55', 'bandera': '🇧🇷', 'min': 10, 'max': 11, 'inicio': '', 'ejemplo': '11912345678'},
    {'codigo': 'CO', 'nombre': 'Colombia', 'prefijo': '57', 'bandera': '🇨🇴', 'min': 10, 'max': 10, 'inicio': '', 'ejemplo': '3001234567'},
    {'codigo': 'EC', 'nombre': 'Ecuador', 'prefijo': '593', 'bandera': '🇪🇨', 'min': 9, 'max': 9, 'inicio': '', 'ejemplo': '991234567'},
    {'codigo': 'PY', 'nombre': 'Paraguay', 'prefijo': '595', 'bandera': '🇵🇾', 'min': 9, 'max': 9, 'inicio': '', 'ejemplo': '981123456'},
    {'codigo': 'UY', 'nombre': 'Uruguay', 'prefijo': '598', 'bandera': '🇺🇾', 'min': 8, 'max': 8, 'inicio': '', 'ejemplo': '94123456'},
    {'codigo': 'MX', 'nombre': 'México', 'prefijo': '52', 'bandera': '🇲🇽', 'min': 10, 'max': 10, 'inicio': '', 'ejemplo': '5512345678'},
    {'codigo': 'US', 'nombre': 'Estados Unidos', 'prefijo': '1', 'bandera': '🇺🇸', 'min': 10, 'max': 10, 'inicio': '', 'ejemplo': '2025550123'},
    {'codigo': 'ES', 'nombre': 'España', 'prefijo': '34', 'bandera': '🇪🇸', 'min': 9, 'max': 9, 'inicio': '', 'ejemplo': '612345678'},
)


def pais_por_codigo(codigo):
    buscado = (codigo or 'CL').upper()
    for pais in PAISES:
        if pais['codigo'] == buscado:
            return pais
    return None


def reglas_publicas():
    return {
        pais['codigo']: {
            'prefijo': pais['prefijo'],
            'min': pais['min'],
            'max': pais['max'],
            'inicio': pais['inicio'],
            'ejemplo': pais['ejemplo'],
            'nombre': pais['nombre'],
        }
        for pais in PAISES
    }


def _digitos(texto):
    return re.sub(r'[\s().\-]', '', texto or '')


def normalizar_telefono(codigo, texto):
    """Devuelve E.164 (+56912345678) o cadena vacía si no hay número."""
    crudo = _digitos(texto)
    if not crudo:
        return ''
    pais = pais_por_codigo(codigo)
    if pais is None:
        raise ValidationError('Selecciona un país de la lista.')
    if crudo.startswith('+'):
        crudo = crudo[1:]
    if crudo.startswith('00'):
        crudo = crudo[2:]
    if not crudo.isdigit():
        raise ValidationError('El teléfono solo puede incluir números y el prefijo del país.')

    prefijo = pais['prefijo']
    if crudo.startswith(prefijo):
        resto = crudo[len(prefijo):]
        if _largo_valido(pais, resto):
            crudo = resto
    if not _largo_valido(pais, crudo) or (pais['inicio'] and not crudo.startswith(pais['inicio'])):
        raise ValidationError(_mensaje(pais))
    return f'+{prefijo}{crudo}'


def _largo_valido(pais, numero):
    return numero.isdigit() and pais['min'] <= len(numero) <= pais['max']


def _mensaje(pais):
    if pais['codigo'] == 'CL':
        return 'Ingresa un móvil chileno de 9 dígitos que empiece con 9, sin repetir el +56.'
    if pais['min'] == pais['max']:
        largo = f'{pais["min"]} dígitos'
    else:
        largo = f'entre {pais["min"]} y {pais["max"]} dígitos'
    return (
        f'El número de {pais["nombre"]} debe tener {largo}, '
        f'sin repetir el prefijo +{pais["prefijo"]}.'
    )
