"""Motor de reglas (intenciones regex + ORM). Fallback si Ollama no está disponible."""
from __future__ import annotations

from core.chatbot.assistant_config import AsistenteConfig, get_asistente_config
from core.chatbot.catalog_nl import extraer_consulta_catalogo
from core.chatbot.handlers import manejar_intent
from core.chatbot.intents import Intent, detectar_intent
from core.chatbot.nlp import normalizar_presupuesto_clp
from core.chatbot.armado_builder_chat import comando_armado_por_reglas
from core.chatbot.armado_chat import ejecutar_armado_chat
from core.chatbot.nlp_armado import parsear_solicitud_armado
from core.chatbot.policy import consulta_en_alcance, solicita_datos_sensibles


def ejecutar_motor_reglas(
    mensaje: str,
    historial: list | None = None,
    usuario=None,
    config: AsistenteConfig | None = None,
    *,
    omitir_alcance: bool = False,
    build_context: dict | None = None,
    builder_componentes: list | None = None,
) -> dict:
    config = config or get_asistente_config()
    texto = (mensaje or '').strip()
    if not texto:
        return {'reply': config.mensaje_vacio, 'motor': 'reglas'}

    if solicita_datos_sensibles(texto, config):
        return {
            'reply': config.mensaje_privacidad,
            'rechazado': True,
            'motivo': 'privacidad',
            'motor': 'reglas',
        }

    if not omitir_alcance and not consulta_en_alcance(texto, config):
        return {
            'reply': config.mensaje_fuera_de_alcance,
            'rechazado': True,
            'motivo': 'fuera_de_alcance',
            'motor': 'reglas',
        }

    comando = comando_armado_por_reglas(texto, build_context, builder_componentes)
    if comando:
        comando['motor'] = 'reglas'
        return comando

    solicitud_armado = parsear_solicitud_armado(texto, build_context)
    bajo = texto.lower()
    es_armado = (
        solicitud_armado.ajuste
        or (build_context and build_context.get('componentes'))
        or 'lucas' in bajo
        or 'luca' in bajo
        or any(
            frase in bajo
            for frase in (
                'armar pc',
                'armar un pc',
                'armado de pc',
                'montar pc',
                'arma un pc',
                'armame un pc',
                'ármame un pc',
            )
        )
        or (solicitud_armado.presupuesto_clp and 'pc' in bajo and solicitud_armado.proposito != 'general')
    )
    if solicitud_armado.presupuesto_clp and es_armado:
        out = ejecutar_armado_chat(
            texto,
            build_context=build_context,
            presupuesto_llm=solicitud_armado.presupuesto_clp,
            proposito_llm=solicitud_armado.proposito,
        )
        out['motor'] = 'reglas'
        return out

    consulta_nl = extraer_consulta_catalogo(texto)
    presupuesto = normalizar_presupuesto_clp(texto)
    if presupuesto is not None and consulta_nl.categoria:
        if consulta_nl.precio_max is None:
            consulta_nl.precio_max = presupuesto
        presupuesto = None

    intent = detectar_intent(texto, presupuesto_clp=presupuesto)
    resultado = manejar_intent(
        intent,
        texto,
        presupuesto,
        usuario=usuario,
        config=config,
        consulta_nl=consulta_nl,
    )
    resultado.setdefault('intent', intent.value)
    resultado['motor'] = 'reglas'
    return resultado
