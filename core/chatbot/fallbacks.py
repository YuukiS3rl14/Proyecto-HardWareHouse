"""Fallbacks distintos del chat. El texto de "sin productos" solo aplica a una búsqueda real."""

UNKNOWN_INTENT = 'unknown_intent'
MISSING_PRODUCT = 'missing_product'
UNAVAILABLE_STOCK = 'unavailable_stock'
MISSING_BUILD = 'missing_pc_build'
INVALID_BUDGET = 'invalid_budget'
INCOMPATIBLE = 'incompatible_components'
OFF_TOPIC = 'off_topic'

_ALIASES = {
    'unrecognized_not_product_search': UNKNOWN_INTENT,
    'missing_build_context': MISSING_BUILD,
    'fuera_de_alcance': OFF_TOPIC,
    'product_not_found': MISSING_PRODUCT,
    'no_products': MISSING_PRODUCT,
    'revalidation_stock': UNAVAILABLE_STOCK,
    'revalidation_incompatible': INCOMPATIBLE,
    'presupuesto_insuficiente': INVALID_BUDGET,
}

MENSAJES = {
    UNKNOWN_INTENT: 'No entendí bien esa frase.',
    MISSING_PRODUCT: (
        'No encontré productos en el catálogo con esos criterios. '
        'Prueba con otra marca, categoría o un rango de precio.'
    ),
    UNAVAILABLE_STOCK: 'Esa pieza está en el catálogo, pero ahora no tiene stock suficiente.',
    MISSING_BUILD: (
        'No tengo un PC armado en esta conversación. Dime el presupuesto '
        '(por ejemplo, 700 lucas) o abre el armador.'
    ),
    INVALID_BUDGET: 'Ese presupuesto no alcanza para un PC compatible con el catálogo actual.',
    INCOMPATIBLE: 'Esas piezas no pasan las reglas de compatibilidad del armador.',
    OFF_TOPIC: 'Puedo ayudarte con productos, armados, pedidos y preguntas de HardWareHouse.',
}

SUGERENCIAS = {
    UNKNOWN_INTENT: 'un producto, un armado o una duda de la tienda',
    MISSING_BUILD: 'armar un PC con un presupuesto',
}


def canonico(reason: str | None) -> str:
    if not reason:
        return ''
    return _ALIASES.get(reason, reason)


def mensaje(reason: str | None, sugerencia: str = '') -> str:
    codigo = canonico(reason)
    base = MENSAJES.get(codigo, '')
    if codigo == UNKNOWN_INTENT and sugerencia:
        return f'{base} ¿Quisiste decir {sugerencia}?'
    return base


def etiquetar(resultado: dict, reason: str, reply: str | None = None) -> dict:
    codigo = canonico(reason)
    resultado['fallback'] = codigo
    resultado['fallback_reason'] = codigo
    if reply:
        resultado['reply'] = reply
    elif not (resultado.get('reply') or '').strip():
        resultado['reply'] = mensaje(codigo, resultado.get('sugerencia') or SUGERENCIAS.get(codigo, ''))
    return resultado


def clasificar_motivo_armado(motivo: str) -> str:
    """Elige el fallback a partir de un motivo ya calculado por Django."""
    bajo = (motivo or '').lower()
    if 'sin stock' in bajo or 'no tiene stock' in bajo or 'stock suficiente' in bajo:
        return UNAVAILABLE_STOCK
    if 'muy bajo' in bajo or 'no alcanza el presupuesto' in bajo:
        return INVALID_BUDGET
    if 'no encontré pieza' in bajo or 'ya no están disponibles' in bajo:
        return UNAVAILABLE_STOCK
    if 'compatib' in bajo:
        return INCOMPATIBLE
    return ''
