"""Presentación de montos CLP. No interviene en cálculos ni en pagos."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def formatear_pesos(valor):
    """Devuelve un monto entero con símbolo y puntos de miles: ``$1.250.654``."""
    if valor is None or valor == '':
        return '$0'
    try:
        monto = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return '$0'
    if not monto.is_finite():
        return '$0'
    entero = int(monto.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    signo = '-' if entero < 0 else ''
    texto = f'{abs(entero):,}'.replace(',', '.')
    return f'{signo}${texto}'


def miles_clp(valor):
    """Misma cifra que ``formatear_pesos``, sin el símbolo ``$``."""
    texto = formatear_pesos(valor)
    if texto.startswith('-$'):
        return '-' + texto[2:]
    return texto[1:]
