"""Motor de respuestas: política → Ollama (intención) → reglas/ORM."""
from __future__ import annotations

import logging

from core.chatbot.assistant_config import AsistenteConfig, get_asistente_config
from core.chatbot.llm.intent_extractor import extraer_intencion_ollama, intent_llm_activo
from core.chatbot.llm.router import ejecutar_ruta_llm
from core.chatbot.policy import solicita_datos_sensibles
from core.chatbot.armado_builder_chat import intentar_confirmar_accion
from core.chatbot.reglas_engine import ejecutar_motor_reglas
from core.chatbot.response_finalize import finalizar_respuesta

logger = logging.getLogger(__name__)


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
        return {'reply': config.mensaje_vacio, 'motor': 'reglas'}

    confirmado = intentar_confirmar_accion(texto, build_context)
    if confirmado:
        confirmado.setdefault('motor', 'reglas')
        return finalizar_respuesta(confirmado, texto, historial=historial, config=config)

    if solicita_datos_sensibles(texto, config):
        return {
            'reply': config.mensaje_privacidad,
            'rechazado': True,
            'motivo': 'privacidad',
            'motor': 'reglas',
        }

    if intent_llm_activo():
        try:
            extraido = extraer_intencion_ollama(texto, historial=historial)
            if extraido is not None:
                resultado = ejecutar_ruta_llm(
                    extraido,
                    texto,
                    usuario=usuario,
                    config=config,
                    build_context=build_context,
                    builder_componentes=builder_componentes,
                )
                return finalizar_respuesta(
                    resultado, texto, historial=historial, extraido=extraido, config=config
                )
        except Exception:
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
    return finalizar_respuesta(resultado, texto, historial=historial, config=config)
