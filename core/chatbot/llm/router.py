"""Enruta intenciones LLM a servicios Django existentes (ORM / FAQ / pedidos)."""
from __future__ import annotations

from core.chatbot.assistant_config import AsistenteConfig, get_asistente_config
from core.chatbot.catalog_nl import ConsultaCatalogoNL
from core.chatbot.handlers import manejar_buscar_producto, manejar_faq, manejar_presupuesto
from core.chatbot.intents import Intent, _busqueda_producto_explicita
from core.chatbot.llm.intent_schema import IntentoLLM
from core.armado_servicio import detectar_categoria_armado
from core.chatbot.armado_builder_chat import ejecutar_intent_armado_builder
from core.chatbot.armado_builder_chat import intentar_confirmar_accion
from core.chatbot.nlp import normalizar_presupuesto_clp, termino_busqueda_especifico
from core.chatbot.private_data import respuesta_mis_pedidos

_FAQ_TOPIC_A_INTENT: dict[str, Intent] = {
    'despacho': Intent.DESPACHO,
    'retiro': Intent.RETIRO,
    'ubicacion_horario': Intent.UBICACION_HORARIO,
    'pago': Intent.PAGO,
    'compra': Intent.COMPRA,
    'armado': Intent.ARMADO,
    'stock': Intent.STOCK,
    'contacto': Intent.CONTACTO,
    'empresa': Intent.EMPRESA,
    'garantia': Intent.GARANTIA,
}


def _respuesta_clarificacion(extraido: IntentoLLM) -> dict:
    return {
        'intent': 'clarification',
        'necesita_clarificacion': True,
        'fallback_reason': 'needs_clarification',
        'motor': 'ollama',
        'confidence': extraido.confidence,
    }


def _presupuesto_efectivo(extraido: IntentoLLM, texto: str) -> int | None:
    return normalizar_presupuesto_clp(texto) or extraido.budget_clp


def _busqueda_catalogo_ejecutable(consulta: ConsultaCatalogoNL, texto: str) -> bool:
    if consulta.requiere_orm_estructurado():
        return True
    if not termino_busqueda_especifico(texto):
        return False
    return _busqueda_producto_explicita(texto)


def _consulta_desde_llm(extraido: IntentoLLM, texto_usuario: str) -> ConsultaCatalogoNL:
    filtros = extraido.filters or {}
    orden = extraido.price_sort or 'relevancia'
    solo_stock = bool(filtros.get('solo_stock'))
    if extraido.intent == 'product_search' and orden == 'precio_asc':
        solo_stock = True

    precio_max = filtros.get('precio_max')
    precio_min = filtros.get('precio_min')
    if extraido.budget_clp and precio_max is None and extraido.intent == 'product_search':
        precio_max = extraido.budget_clp

    q = extraido.query_text or filtros.get('query') or ''
    if not q and extraido.brand and not extraido.category:
        q = extraido.brand.lower()

    return ConsultaCatalogoNL(
        categoria=extraido.category,
        marca=extraido.brand if extraido.brand and extraido.brand.lower() not in ('intel', 'amd', 'nvidia') else None,
        orden=orden,
        precio_min=precio_min,
        precio_max=precio_max,
        solo_con_stock=solo_stock,
        q=q if isinstance(q, str) else '',
    )


def ejecutar_ruta_llm(
    extraido: IntentoLLM,
    texto: str,
    usuario=None,
    config: AsistenteConfig | None = None,
    build_context: dict | None = None,
    builder_componentes: list | None = None,
) -> dict:
    config = config or get_asistente_config()

    confirmado = intentar_confirmar_accion(texto, build_context)
    if confirmado:
        confirmado['motor'] = 'ollama'
        confirmado['confidence'] = extraido.confidence
        return confirmado

    if extraido.intent == 'off_topic':
        return {
            'reply': config.mensaje_fuera_de_alcance,
            'rechazado': True,
            'motivo': 'fuera_de_alcance',
            'intent': 'off_topic',
            'motor': 'ollama',
            'confidence': extraido.confidence,
        }

    if extraido.intent == 'greeting':
        return {
            'reply': config.mensaje_bienvenida,
            'intent': 'greeting',
            'motor': 'ollama',
            'confidence': extraido.confidence,
        }

    if extraido.intent == 'clarification':
        return _respuesta_clarificacion(extraido)

    if extraido.intent in ('order_status', 'orders'):
        out = respuesta_mis_pedidos(usuario)
        out['intent'] = 'orders' if extraido.intent == 'orders' else 'order_status'
        out['motor'] = 'ollama'
        out['confidence'] = extraido.confidence
        return out

    if extraido.intent in (
        'pc_build',
        'pc_build_modify',
        'pc_build_analyze',
        'pc_build_replace',
        'build_upgrade',
        'build_downgrade',
        'budget_adjustment',
    ):
        categoria = extraido.filters.get('build_category') or detectar_categoria_armado(texto)
        preferencia = None
        intent_ruta = extraido.intent
        if extraido.intent == 'build_upgrade':
            intent_ruta = 'pc_build_replace'
            preferencia = 'better'
        elif extraido.intent == 'build_downgrade':
            intent_ruta = 'pc_build_replace'
            preferencia = 'cheaper'
        elif extraido.intent == 'budget_adjustment':
            intent_ruta = 'pc_build_modify'
        out = ejecutar_intent_armado_builder(
            intent_ruta,
            texto,
            build_context,
            builder_componentes,
            categoria_llm=categoria,
            presupuesto_llm=_presupuesto_efectivo(extraido, texto),
            proposito_llm=extraido.filters.get('purpose'),
            preferencia=preferencia,
        )
        out['intent'] = extraido.intent
        out['motor'] = 'ollama'
        out['confidence'] = extraido.confidence
        return out

    if extraido.intent in ('store_faq', 'company_info', 'faq'):
        from core.knowledge.service import responder_conocimiento

        tema = extraido.faq_topic or extraido.filters.get('faq_topic')
        conocido = responder_conocimiento(texto, tema=tema if isinstance(tema, str) else None)
        if conocido is None and not tema:
            conocido = responder_conocimiento(texto)
        if conocido:
            conocido['motor'] = 'ollama'
            conocido['confidence'] = extraido.confidence
            return conocido
        if extraido.intent == 'company_info':
            return _respuesta_clarificacion(extraido)

    if extraido.intent in ('store_faq', 'faq'):
        topic = extraido.faq_topic or extraido.filters.get('faq_topic')
        if topic is None and extraido.intent == 'faq':
            return _respuesta_clarificacion(extraido)
        intent_faq = _FAQ_TOPIC_A_INTENT.get(topic or '', Intent.DESPACHO)
        if topic is None:
            bajo = texto.lower()
            if any(w in bajo for w in ('delivery', 'envio', 'envío', 'despacho', 'domicilio')):
                intent_faq = Intent.DESPACHO
            elif 'paypal' in bajo or 'pago' in bajo:
                intent_faq = Intent.PAGO
            elif 'retiro' in bajo or 'tienda' in bajo:
                intent_faq = Intent.RETIRO
        faq = manejar_faq(intent_faq)
        if faq:
            faq['intent'] = 'store_faq'
            faq['motor'] = 'ollama'
            faq['confidence'] = extraido.confidence
            return faq
        return _respuesta_clarificacion(extraido)

    if extraido.intent == 'product_recommendation' and _presupuesto_efectivo(extraido, texto):
        if extraido.category or extraido.filters.get('purpose') in ('gaming', 'office', 'editing'):
            out = ejecutar_intent_armado_builder(
                'pc_build',
                texto,
                build_context,
                builder_componentes,
                presupuesto_llm=_presupuesto_efectivo(extraido, texto),
                proposito_llm=extraido.filters.get('purpose'),
            )
            out['intent'] = 'product_recommendation'
        else:
            out = manejar_presupuesto(_presupuesto_efectivo(extraido, texto) or extraido.budget_clp)
            out['intent'] = 'product_recommendation'
        out['motor'] = 'ollama'
        out['confidence'] = extraido.confidence
        return out

    if extraido.intent in ('product_search', 'product_recommendation'):
        consulta = _consulta_desde_llm(extraido, texto)
        if not consulta.requiere_orm_estructurado() and texto.strip():
            from core.chatbot.catalog_nl import extraer_consulta_catalogo

            consulta = extraer_consulta_catalogo(texto)
        if not _busqueda_catalogo_ejecutable(consulta, texto):
            return _respuesta_clarificacion(extraido)
        out = manejar_buscar_producto(texto, config, consulta_nl=consulta)
        out['intent'] = extraido.intent
        out['busqueda_catalogo'] = True
        out['motor'] = 'ollama'
        out['confidence'] = extraido.confidence
        return out

    return {
        'intent': 'clarification',
        'necesita_clarificacion': True,
        'fallback_reason': 'unrecognized_not_product_search',
        'motor': 'ollama',
        'confidence': extraido.confidence,
    }
