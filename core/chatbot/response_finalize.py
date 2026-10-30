"""Inferencia de tipo, hechos verificados y generación final de respuesta."""
from __future__ import annotations

from core.chatbot.assistant_config import AsistenteConfig, get_asistente_config
from core.chatbot.fallbacks import (
    INCOMPATIBLE,
    INVALID_BUDGET,
    MENSAJES,
    MISSING_BUILD,
    MISSING_PRODUCT,
    OFF_TOPIC,
    UNAVAILABLE_STOCK,
    UNKNOWN_INTENT,
    canonico,
    clasificar_motivo_armado,
)
from core.chatbot.handlers import _texto_desde_resultados
from core.chatbot.llm.intent_schema import IntentoLLM
from core.chatbot.llm.response_composer import componer_con_ollama, response_llm_activo
from core.chatbot.response_templates import renderizar
from core.chatbot.response_ui import adjuntar_ui_al_resultado
from core.chatbot.response_types import (
    BUDGET,
    CLARIFICATION,
    FAQ,
    GENERIC,
    GREETING,
    OFF_TOPIC,
    OLLAMA_POLISH_TIPOS,
    ORDER_LOGIN,
    ORDER_STATUS,
    PRIVACY,
    PRODUCT_NOT_FOUND,
    PRODUCT_RESULTS,
)

_TIPOS_ARMADO = frozenset(
    {
        'pc_build',
        'pc_build_failed',
        'build_analysis',
        'build_pending_change',
        'build_applied',
        'build_rejected',
    }
)
_FALLBACKS_CON_TEXTO = frozenset({MISSING_BUILD, INVALID_BUDGET, INCOMPATIBLE, UNAVAILABLE_STOCK})


def _interpretacion_desde_llm(extraido: IntentoLLM | None) -> str | None:
    if extraido is None:
        return None
    partes = []
    if extraido.category:
        partes.append(f'productos de {extraido.category}')
    if extraido.brand:
        partes.append(f'marca {extraido.brand}')
    if extraido.budget_clp:
        partes.append(f'presupuesto hasta ${extraido.budget_clp:,}'.replace(',', '.'))
    if extraido.faq_topic:
        partes.append(f'información de tienda ({extraido.faq_topic})')
    if extraido.intent in (
        'pc_build',
        'pc_build_modify',
        'build_upgrade',
        'build_downgrade',
        'budget_adjustment',
    ):
        partes.append('armado de PC')
    if extraido.intent in ('orders', 'order_status'):
        partes.append('estado de tu pedido')
    return ', '.join(partes) if partes else None


_INTENTS_BUSQUEDA_PRODUCTO = frozenset(
    {
        'product_search',
        'product_recommendation',
        'buscar_producto',
        'stock',
    }
)


def _es_busqueda_con_cero_resultados(resultado: dict, intent: str) -> bool:
    cat = resultado.get('catalogo')
    if not cat or cat.get('count', 0) != 0:
        return False
    if intent in _INTENTS_BUSQUEDA_PRODUCTO:
        return True
    return bool(resultado.get('busqueda_catalogo'))


def inferir_tipo_respuesta(resultado: dict, extraido: IntentoLLM | None = None) -> str:
    pre = resultado.get('response_type')
    if pre == CLARIFICATION or pre == 'clarification':
        return CLARIFICATION
    if pre in (
        'pc_build',
        'pc_build_failed',
        'build_analysis',
        'build_pending_change',
        'build_applied',
        'build_rejected',
    ):
        return pre

    if resultado.get('motivo') == 'privacidad':
        return PRIVACY
    if resultado.get('rechazado') and resultado.get('motivo') == 'fuera_de_alcance':
        return OFF_TOPIC

    intent = (extraido.intent if extraido else None) or resultado.get('intent') or ''
    if intent in ('greeting', 'saludo'):
        return GREETING
    if intent in ('clarification',) or resultado.get('necesita_clarificacion'):
        return CLARIFICATION
    if intent in ('off_topic',):
        return OFF_TOPIC
    if intent in (
        'pc_build',
        'pc_build_modify',
        'pc_build_analyze',
        'pc_build_replace',
        'build_upgrade',
        'build_downgrade',
        'budget_adjustment',
        'product_recommendation',
    ) and resultado.get('armado'):
        return 'pc_build' if resultado.get('armado', {}).get('ok') else 'pc_build_failed'
    if intent in ('pc_build', 'pc_build_modify', 'build_upgrade', 'build_downgrade', 'budget_adjustment'):
        return CLARIFICATION
    if intent in ('order_status', 'mis_pedidos', 'orders'):
        return ORDER_LOGIN if resultado.get('requiere_login') else ORDER_STATUS
    if resultado.get('presupuesto') is not None:
        return BUDGET

    cat = resultado.get('catalogo')
    if cat is not None:
        if _es_busqueda_con_cero_resultados(resultado, intent):
            return PRODUCT_NOT_FOUND
        if cat.get('count', 0) > 0:
            return PRODUCT_RESULTS

    if intent in ('store_faq', 'faq', 'company_info') or intent in (
        'despacho',
        'pago',
        'compra',
        'armado',
        'contacto',
        'empresa',
        'ubicacion_horario',
        'retiro',
        'garantia',
    ):
        return FAQ
    if intent == 'stock' and not cat:
        return FAQ
    if intent in _INTENTS_BUSQUEDA_PRODUCTO:
        return CLARIFICATION
    return GENERIC


def _lineas_producto_orm(resultado: dict, config: AsistenteConfig) -> list[str]:
    catalogo = resultado.get('catalogo') or {}
    productos = catalogo.get('results') or []
    if not productos:
        return []
    consulta_meta = resultado.get('consulta') or {}
    from core.chatbot.catalog_nl import ConsultaCatalogoNL

    consulta = ConsultaCatalogoNL(
        categoria=consulta_meta.get('categoria'),
        orden=consulta_meta.get('orden') or 'relevancia',
        solo_con_stock=bool(consulta_meta.get('solo_con_stock')),
    )
    texto = _texto_desde_resultados(catalogo, config, consulta)
    return texto.split('\n')


def _marcar_fallback(resultado: dict, codigo: str) -> None:
    if codigo in MENSAJES:
        resultado['fallback'] = codigo
        resultado['fallback_reason'] = codigo


def _codigo_fallback(resultado: dict) -> str:
    return canonico(resultado.get('fallback') or resultado.get('fallback_reason'))


def _nota_contexto(resultado: dict) -> str:
    ctx = resultado.get('armado_context') if isinstance(resultado.get('armado_context'), dict) else {}
    partes = []
    if ctx.get('proposito'):
        partes.append(f'proposito={ctx.get("proposito")}')
    for clave in ('presupuesto_original_clp', 'presupuesto_clp'):
        try:
            monto = int(ctx.get(clave) or 0)
        except (TypeError, ValueError):
            monto = 0
        if monto:
            partes.append(f'{clave}={monto}')
            break
    if not partes:
        return ''
    return 'CONTEXTO_VERIFICADO: ' + ', '.join(partes)


def _pulir(
    tipo: str,
    reply: str,
    mensaje_usuario: str,
    historial: list | None,
    interpretacion: str | None,
    resultado: dict,
) -> str:
    if tipo == PRODUCT_RESULTS or tipo == PRODUCT_NOT_FOUND or not reply:
        return reply
    if not response_llm_activo():
        return reply
    if tipo not in OLLAMA_POLISH_TIPOS and tipo not in _TIPOS_ARMADO and tipo not in _FALLBACKS_CON_TEXTO:
        return reply
    nota = _nota_contexto(resultado)
    hechos = f'{reply}\n{nota}' if nota else reply
    pulido = componer_con_ollama(
        tipo=tipo,
        hechos_verificados=hechos,
        mensaje_usuario=mensaje_usuario,
        historial=historial,
        interpretacion=interpretacion,
    )
    return pulido or reply


def finalizar_respuesta(
    resultado: dict,
    mensaje_usuario: str,
    historial: list | None = None,
    extraido: IntentoLLM | None = None,
    config: AsistenteConfig | None = None,
) -> dict:
    config = config or get_asistente_config()
    tipo = inferir_tipo_respuesta(resultado, extraido)
    interpretacion = _interpretacion_desde_llm(extraido)

    if tipo == PRIVACY:
        resultado['response_type'] = tipo
        return adjuntar_ui_al_resultado(resultado, tipo)

    if tipo == PRODUCT_RESULTS:
        cuerpo = renderizar(
            tipo,
            producto_lineas=_lineas_producto_orm(resultado, config),
            config=config,
        )
        productos = (resultado.get('catalogo') or {}).get('results') or []
        if productos and all(int(item.get('stock') or 0) <= 0 for item in productos):
            _marcar_fallback(resultado, UNAVAILABLE_STOCK)
            cuerpo = f'{MENSAJES[UNAVAILABLE_STOCK]}\n{cuerpo}'
        resultado['reply'] = cuerpo
        resultado['response_type'] = tipo
        return adjuntar_ui_al_resultado(resultado, tipo)

    if tipo in _TIPOS_ARMADO:
        codigo = _codigo_fallback(resultado)
        if tipo in ('pc_build_failed', 'build_rejected') and codigo not in MENSAJES:
            armado = resultado.get('armado') if isinstance(resultado.get('armado'), dict) else {}
            codigo = clasificar_motivo_armado(str(armado.get('motivo') or ''))
        if codigo in MENSAJES:
            _marcar_fallback(resultado, codigo)
        resultado['reply'] = _pulir(
            tipo,
            resultado.get('reply') or '',
            mensaje_usuario,
            historial,
            interpretacion,
            resultado,
        )
        resultado['response_type'] = tipo
        return adjuntar_ui_al_resultado(resultado, tipo)

    if tipo == PRODUCT_NOT_FOUND:
        _marcar_fallback(resultado, MISSING_PRODUCT)
        resultado['reply'] = renderizar(PRODUCT_NOT_FOUND, config=config)
        resultado['response_type'] = tipo
        return adjuntar_ui_al_resultado(resultado, tipo)

    if tipo == GREETING:
        reply = renderizar(GREETING, config=config)
    elif tipo == OFF_TOPIC:
        reply = renderizar(OFF_TOPIC, config=config)
        _marcar_fallback(resultado, OFF_TOPIC)
    elif tipo == CLARIFICATION:
        codigo = _codigo_fallback(resultado)
        propia = (resultado.get('reply') or '').strip()
        if propia:
            reply = propia
        else:
            reply = renderizar(
                CLARIFICATION,
                interpretacion=interpretacion,
                sugerencia=resultado.get('sugerencia'),
                config=config,
            )
            if codigo in ('', UNKNOWN_INTENT):
                codigo = UNKNOWN_INTENT
        if codigo in MENSAJES:
            _marcar_fallback(resultado, codigo)
    elif tipo == FAQ:
        reply = renderizar(FAQ, faq_texto=resultado.get('reply', ''), config=config)
    elif tipo in (ORDER_STATUS, ORDER_LOGIN):
        reply = renderizar(tipo, pedidos_texto=resultado.get('reply', ''), config=config)
    elif tipo == BUDGET:
        reply = renderizar(BUDGET, presupuesto_texto=resultado.get('reply', ''), config=config)
    else:
        reply = renderizar(GENERIC, generico=resultado.get('reply', ''), config=config)

    resultado['reply'] = _pulir(tipo, reply, mensaje_usuario, historial, interpretacion, resultado)
    resultado['response_type'] = tipo
    return adjuntar_ui_al_resultado(resultado, tipo)
