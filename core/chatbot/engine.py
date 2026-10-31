"""Motor de respuestas: política → Ollama (intención) → reglas/ORM."""
from __future__ import annotations

import logging

from django.conf import settings

from core.chatbot.assistant_config import AsistenteConfig, get_asistente_config
from core.chatbot.llm.intent_extractor import extraer_intencion_ollama, intent_llm_activo
from core.chatbot.llm.router import ejecutar_ruta_llm
from core.chatbot.policy import solicita_datos_sensibles
from core.chatbot.armado_builder_chat import intentar_confirmar_accion
from core.chatbot.catalogo_contexto import responder_seguimiento_catalogo
from core.chatbot.compatibilidad_chat import responder_si_compatibilidad
from core.chatbot.reglas_engine import ejecutar_motor_reglas
from core.knowledge.service import responder_conocimiento
from core.chatbot.armado_optimizar import detectar_optimizacion, optimizar_armado_chat, responder_sin_armado
from core.chatbot.conversation_state import recordar_turno
from core.armado_servicio import fusionar_componentes_activos
from core.chatbot.response_finalize import finalizar_respuesta

logger = logging.getLogger(__name__)
debug_log = logging.getLogger('hardwarehouse.chat')


def _cerrar(resultado: dict, texto: str, historial, config, build_context, extraido=None) -> dict:
    resultado = recordar_turno(resultado, build_context, texto)
    cerrado = finalizar_respuesta(resultado, texto, historial=historial, extraido=extraido, config=config)
    debug_log.info(
        'chat classified=%s route=%s reason=%s',
        cerrado.get('intent_clasificado') or '-',
        cerrado.get('motor') or '-',
        cerrado.get('fallback') or cerrado.get('fallback_reason') or 'matched',
    )
    return cerrado


def ejecutar_motor(
    mensaje: str,
    historial: list | None = None,
    usuario=None,
    config: AsistenteConfig | None = None,
    build_context: dict | None = None,
    builder_componentes: list | None = None,
) -> dict:
    config = config or get_asistente_config()
    texto = (mensaje or '').strip()
    if not texto:
        debug_log.info('chat route=reglas intent=- model=- ollama=skipped reason=empty_message')
        return {'reply': config.mensaje_vacio, 'motor': 'reglas'}

    confirmado = intentar_confirmar_accion(texto, build_context)
    if confirmado:
        confirmado.setdefault('motor', 'reglas')
        debug_log.info(
            'chat route=reglas intent=%s model=- ollama=skipped reason=pending_confirmation chars=%s',
            confirmado.get('intent') or 'pc_build_modify',
            len(texto),
        )
        return _cerrar(confirmado, texto, historial, config, build_context)

    if solicita_datos_sensibles(texto, config):
        debug_log.info(
            'chat route=reglas intent=privacy model=- ollama=skipped reason=sensitive_request chars=%s',
            len(texto),
        )
        return {
            'reply': config.mensaje_privacidad,
            'rechazado': True,
            'motivo': 'privacidad',
            'motor': 'reglas',
        }

    compatibilidad = responder_si_compatibilidad(texto)
    if compatibilidad:
        debug_log.info(
            'chat route=reglas intent=compatibilidad model=- ollama=skipped reason=compatibility_question chars=%s',
            len(texto),
        )
        return _cerrar(compatibilidad, texto, historial, config, build_context)

    seguimiento = responder_seguimiento_catalogo(texto, build_context)
    if seguimiento:
        debug_log.info(
            'chat route=reglas intent=product_search model=- ollama=skipped reason=catalog_followup chars=%s',
            len(texto),
        )
        return _cerrar(seguimiento, texto, historial, config, build_context)

    conocimiento = responder_conocimiento(texto, historial=historial)
    if conocimiento:
        debug_log.info(
            'chat route=conocimiento intent=%s model=- ollama=context_first reason=company_knowledge id=%s',
            conocimiento.get('intent') or '-',
            (conocimiento.get('conocimiento') or {}).get('id') or '-',
        )
        return _cerrar(conocimiento, texto, historial, config, build_context)

    pedido_armado = detectar_optimizacion(texto)
    if pedido_armado:
        if fusionar_componentes_activos(build_context, builder_componentes):
            optimizado = optimizar_armado_chat(texto, build_context, builder_componentes)
            optimizado.setdefault('motor', 'reglas')
            optimizado.setdefault('fallback_reason', 'build_optimization')
            debug_log.info(
                'chat route=reglas intent=%s model=- ollama=skipped reason=build_optimization chars=%s',
                optimizado.get('intent') or '-',
                len(texto),
            )
            return _cerrar(optimizado, texto, historial, config, build_context)
        sin_armado = responder_sin_armado(build_context, pedido_armado.get('modo') or '')
        debug_log.info(
            'chat route=reglas intent=%s model=- ollama=skipped reason=%s chars=%s',
            sin_armado.get('intent') or '-',
            sin_armado.get('fallback') or sin_armado.get('fallback_reason') or 'followup_without_build',
            len(texto),
        )
        return _cerrar(sin_armado, texto, historial, config, build_context)

    if intent_llm_activo():
        try:
            extraido = extraer_intencion_ollama(
                texto,
                historial=historial,
                build_context=build_context,
            )
            if extraido is not None:
                resultado = ejecutar_ruta_llm(
                    extraido,
                    texto,
                    usuario=usuario,
                    config=config,
                    build_context=build_context,
                    builder_componentes=builder_componentes,
                )
                debug_log.info(
                    'chat route=ollama intent=%s model=used response_type=%s motor=%s',
                    extraido.intent,
                    resultado.get('response_type') or '-',
                    resultado.get('motor') or 'ollama',
                )
                return _cerrar(resultado, texto, historial, config, build_context, extraido)
        except Exception as exc:
            debug_log.info(
                'chat route=reglas intent=- model=- ollama=failed reason=exception:%s',
                type(exc).__name__,
            )
            logger.exception('Fallo inesperado en extracción Ollama; usando reglas')

    resultado = ejecutar_motor_reglas(
        texto,
        historial=historial,
        usuario=usuario,
        config=config,
        build_context=build_context,
        builder_componentes=builder_componentes,
    )
    if intent_llm_activo() and resultado.get('motor') == 'reglas':
        resultado['fallback'] = 'reglas'
        debug_log.info(
            'chat route=reglas intent=%s model=%s ollama=fallback reason=rules_after_ollama',
            resultado.get('intent') or '-',
            getattr(settings, 'OLLAMA_MODEL', '-') or '-',
        )
    else:
        debug_log.info(
            'chat route=reglas intent=%s model=%s ollama=skipped reason=rules_only',
            resultado.get('intent') or '-',
            getattr(settings, 'OLLAMA_MODEL', '-') or '-',
        )
    return _cerrar(resultado, texto, historial, config, build_context)
