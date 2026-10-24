"""Inferencia de tipo, hechos verificados y generación final de respuesta."""
from __future__ import annotations

from core.chatbot.assistant_config import AsistenteConfig, get_asistente_config
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
    if extraido.intent == 'order_status':
        partes.append('estado de tu pedido')
    if extraido.intent in ('pc_build', 'pc_build_modify'):
        partes.append('armado de PC')
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
    if pre in ('pc_build', 'pc_build_failed', 'build_analysis', 'build_pending_change', 'build_applied'):
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
        'product_recommendation',
    ) and resultado.get('armado'):
        return 'pc_build' if resultado.get('armado', {}).get('ok') else 'pc_build_failed'
    if intent in ('pc_build', 'pc_build_modify'):
        return CLARIFICATION
    if intent in ('order_status', 'mis_pedidos'):
        return ORDER_LOGIN if resultado.get('requiere_login') else ORDER_STATUS
    if resultado.get('presupuesto') is not None:
        return BUDGET

    cat = resultado.get('catalogo')
    if cat is not None:
        if _es_busqueda_con_cero_resultados(resultado, intent):
            return PRODUCT_NOT_FOUND
        if cat.get('count', 0) > 0:
            return PRODUCT_RESULTS

    if intent in ('store_faq',) or intent in (
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
        resultado['reply'] = renderizar(
            tipo,
            producto_lineas=_lineas_producto_orm(resultado, config),
            config=config,
        )
        resultado['response_type'] = tipo
        return adjuntar_ui_al_resultado(resultado, tipo)

    if tipo in ('pc_build', 'pc_build_failed', 'build_analysis', 'build_pending_change', 'build_applied'):
        resultado['response_type'] = tipo
        return adjuntar_ui_al_resultado(resultado, tipo)

    if tipo == PRODUCT_NOT_FOUND:
        resultado['reply'] = renderizar(PRODUCT_NOT_FOUND, config=config)
        resultado['response_type'] = tipo
        return adjuntar_ui_al_resultado(resultado, tipo)

    if tipo == GREETING:
        reply = renderizar(GREETING, config=config)
    elif tipo == OFF_TOPIC:
        reply = renderizar(OFF_TOPIC, config=config)
    elif tipo == CLARIFICATION:
        reply = renderizar(CLARIFICATION, interpretacion=interpretacion, config=config)
    elif tipo == FAQ:
        reply = renderizar(FAQ, faq_texto=resultado.get('reply', ''), config=config)
    elif tipo in (ORDER_STATUS, ORDER_LOGIN):
        reply = renderizar(tipo, pedidos_texto=resultado.get('reply', ''), config=config)
    elif tipo == BUDGET:
        reply = renderizar(BUDGET, presupuesto_texto=resultado.get('reply', ''), config=config)
    else:
        reply = renderizar(GENERIC, generico=resultado.get('reply', ''), config=config)

    if response_llm_activo() and tipo in OLLAMA_POLISH_TIPOS:
        pulido = componer_con_ollama(
            tipo=tipo,
            hechos_verificados=reply,
            mensaje_usuario=mensaje_usuario,
            historial=historial,
            interpretacion=interpretacion,
        )
        if pulido:
            reply = pulido

    resultado['reply'] = reply
    resultado['response_type'] = tipo
    return adjuntar_ui_al_resultado(resultado, tipo)
