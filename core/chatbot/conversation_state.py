"""Último intent y presupuesto que el chat puede reutilizar en el turno siguiente."""
from __future__ import annotations

INTENTS_PUBLICOS = frozenset(
    {
        'pc_build',
        'build_upgrade',
        'build_downgrade',
        'budget_adjustment',
        'product_search',
        'faq',
        'orders',
        'clarification',
        'off_topic',
        'greeting',
        'compatibility',
    }
)

_FAQ = frozenset(
    {
        'faq',
        'store_faq',
        'company_info',
        'despacho',
        'retiro',
        'ubicacion_horario',
        'pago',
        'compra',
        'armado',
        'contacto',
        'empresa',
        'stock',
        'garantia',
    }
)
_ORDERS = frozenset({'orders', 'order_status', 'mis_pedidos'})
_BUILD = frozenset(
    {
        'pc_build',
        'pc_build_modify',
        'pc_build_analyze',
        'pc_build_replace',
        'build_upgrade',
        'build_downgrade',
        'budget_adjustment',
    }
)


def clasificar_intent_publico(intent: str | None, texto: str = '', resultado: dict | None = None) -> str:
    """Traduce intents internos al conjunto estable que ve el log y el contexto."""
    nombre = (intent or '').strip().lower()
    resultado = resultado or {}
    bajo = (texto or '').lower()
    if nombre in INTENTS_PUBLICOS:
        return nombre
    if nombre in _ORDERS:
        return 'orders'
    if nombre in _FAQ:
        return 'faq'
    if nombre in ('greeting', 'saludo'):
        return 'greeting'
    if nombre in ('off_topic', 'desconocido'):
        return 'off_topic' if resultado.get('rechazado') else 'clarification'
    if nombre in ('clarification',):
        return 'clarification'
    if nombre in ('product_search', 'buscar_producto', 'presupuesto', 'product_recommendation'):
        if resultado.get('armado') or nombre == 'pc_build':
            return 'pc_build'
        return 'product_search'
    if nombre in _BUILD or resultado.get('response_type') in (
        'pc_build',
        'pc_build_failed',
        'build_analysis',
        'build_pending_change',
        'build_applied',
    ):
        if any(p in bajo for p in ('mas barato', 'más barato', 'downgrade', 'cheaper', 'más económico', 'mas economico')):
            return 'build_downgrade' if resultado.get('response_type') == 'build_pending_change' else 'budget_adjustment'
        if any(p in bajo for p in ('mas caro', 'más caro', 'upgrade', 'más potente', 'mas potente', 'mejor')):
            return 'build_upgrade'
        if nombre in ('build_upgrade', 'pc_build_replace') and 'barat' in bajo:
            return 'build_downgrade'
        if nombre == 'budget_adjustment' or resultado.get('armado_context', {}).get('ajuste') == 'cheaper':
            return 'budget_adjustment'
        if nombre == 'pc_build_replace':
            return 'build_upgrade' if 'barat' not in bajo else 'build_downgrade'
        return 'pc_build'
    if nombre == 'compatibilidad' or resultado.get('response_type') == 'compatibility':
        return 'compatibility'
    if resultado.get('necesita_clarificacion'):
        return 'clarification'
    return 'clarification'


def sugerencia_contextual(intent_previo: str | None, presupuesto_clp: int | None = None) -> str:
    previo = intent_previo or ''
    monto = ''
    if presupuesto_clp:
        monto = f' con el presupuesto de ${int(presupuesto_clp):,} CLP'.replace(',', '.')
    if previo in ('pc_build', 'budget_adjustment', 'build_upgrade', 'build_downgrade'):
        return f'ajustar el armado{monto}, cambiar una pieza o armar otro PC'
    if previo == 'product_search':
        return 'buscar otro producto del catálogo, ver stock o comparar precios'
    if previo == 'faq':
        return 'una duda de la tienda, el retiro o los pagos'
    if previo == 'orders':
        return 'revisar el estado de tu pedido'
    return 'un producto del catálogo, un armado de PC o una duda de la tienda'


def recordar_turno(resultado: dict, build_context: dict | None, texto: str) -> dict:
    """Conserva intent y presupuesto. Una aclaración no borra el intent anterior."""
    base: dict = {}
    if isinstance(build_context, dict):
        base.update(build_context)
    nuevo = resultado.get('armado_context')
    if isinstance(nuevo, dict):
        base.update(nuevo)
    base.pop('pedidos', None)

    clasificado = clasificar_intent_publico(resultado.get('intent'), texto, resultado)
    resultado['intent_clasificado'] = clasificado
    if clasificado not in ('clarification', 'greeting', 'off_topic'):
        base['ultimo_intent'] = clasificado
    elif not base.get('ultimo_intent'):
        base['ultimo_intent'] = clasificado

    from core.chatbot.armado_optimizar import menciona_resto
    from core.chatbot.nlp import normalizar_presupuesto_clp

    monto = normalizar_presupuesto_clp(texto)
    armado = resultado.get('armado') if isinstance(resultado.get('armado'), dict) else {}
    if not base.get('presupuesto_original_clp') and base.get('presupuesto_clp'):
        base['presupuesto_original_clp'] = base['presupuesto_clp']
    if monto and not menciona_resto(texto):
        base['presupuesto_clp'] = monto
    elif not base.get('presupuesto_clp') and armado.get('presupuesto_clp'):
        base['presupuesto_clp'] = armado.get('presupuesto_clp')
    if not base.get('presupuesto_original_clp') and base.get('presupuesto_clp'):
        base['presupuesto_original_clp'] = base['presupuesto_clp']

    from core.chatbot.catalogo_contexto import snapshot_busqueda

    if resultado.get('conservar_busqueda'):
        pass
    elif clasificado == 'product_search':
        busqueda = snapshot_busqueda(resultado)
        if busqueda:
            base['catalogo_busqueda'] = busqueda
        else:
            base.pop('catalogo_busqueda', None)
    elif clasificado != 'clarification':
        base.pop('catalogo_busqueda', None)

    if resultado.get('necesita_clarificacion') or clasificado == 'clarification':
        resultado['sugerencia'] = sugerencia_contextual(
            (build_context or {}).get('ultimo_intent') if isinstance(build_context, dict) else None,
            base.get('presupuesto_clp'),
        )

    if base:
        resultado['armado_context'] = base
    return resultado
