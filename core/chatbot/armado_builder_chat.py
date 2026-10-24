"""Comandos de chat sobre el armado activo (analizar, reemplazar, confirmar)."""
from __future__ import annotations

import re

from core.armado_servicio import (
    analizar_armado,
    crear_propuesta_pendiente_armado,
    detectar_categoria_armado,
    fusionar_componentes_activos,
    proponer_reemplazo,
    sanitizar_lista_componentes,
)
from core.chatbot.armado_chat import ejecutar_armado_chat

_CONFIRMAR = re.compile(
    r'\b(s[ií]|confirmo|confirmar|aplicar|dale|ok|de acuerdo|acepto)\b',
    re.I,
)
_ANALIZAR = re.compile(
    r'\b(analiz|analiza|revis(a|ar)|eval[uú]a|mi armado|mi build|estado del armado|'
    r'compatibilidad de mi)\b',
    re.I,
)
_REEMPLAZAR = re.compile(
    r'\b(reemplaz|cambiar|sustitu|pon(?:er)?\s+otra)\b',
    re.I,
)
_MAS_BARATO_PIEZA = re.compile(r'\b(más barat|mas barat)\w*\b', re.I)


def _mensaje_confirmacion_pendiente(pending: dict) -> str:
    return (
        f'{pending.get("resumen", "Cambio propuesto.")}\n\n'
        '¿Aplico este cambio a tu armado en el armador? '
        'Responde "sí, confirmar" para aplicarlo (no modifica el carrito).'
    )


def intentar_confirmar_accion(
    texto: str,
    build_context: dict | None,
) -> dict | None:
    if not build_context or not _CONFIRMAR.search(texto or ''):
        return None
    pending = build_context.get('pending_action')
    if not isinstance(pending, dict) or not pending.get('id'):
        return None
    componentes = sanitizar_lista_componentes(pending.get('componentes'))
    if not componentes:
        return None
    analisis = analizar_armado(componentes)
    propuesta = crear_propuesta_pendiente_armado(
        componentes,
        meta={'origen': 'chat_confirm', 'accion': pending.get('tipo')},
    )
    nuevo_ctx = {
        **{k: v for k, v in build_context.items() if k != 'pending_action'},
        'componentes': componentes,
        'total_clp': analisis.get('total_clp'),
        'proposito': build_context.get('proposito') or 'general',
        'presupuesto_clp': build_context.get('presupuesto_clp'),
    }
    lineas = [
        'Cambio aplicado a tu armado en el chat (revisa en /armado/).',
        analisis.get('texto', ''),
    ]
    return {
        'intent': 'pc_build_modify',
        'response_type': 'build_applied',
        'reply': '\n'.join(lineas),
        'armado_context': nuevo_ctx,
        'applied_build': {'componentes': componentes},
        'proposal_pending': propuesta,
        'armado': {'ok': analisis.get('ok', True), 'estado': analisis.get('estado')},
    }


def ejecutar_analisis_armado_chat(
    texto: str,
    build_context: dict | None = None,
    builder_componentes: list | None = None,
) -> dict:
    componentes = fusionar_componentes_activos(build_context, builder_componentes)
    if not componentes:
        return {
            'intent': 'pc_build_analyze',
            'response_type': 'clarification',
            'reply': (
                'Para analizar tu armado necesito las piezas seleccionadas. '
                'Ábrelas en /armado/ con el chat en la misma página, o pídeme un armado nuevo con presupuesto.'
            ),
        }
    analisis = analizar_armado(componentes)
    if not analisis.get('ok'):
        return {
            'intent': 'pc_build_analyze',
            'response_type': 'clarification',
            'reply': analisis.get('mensaje', 'No pude analizar el armado.'),
        }
    ctx = dict(build_context or {})
    ctx['componentes'] = componentes
    ctx['total_clp'] = analisis.get('total_clp')
    return {
        'intent': 'pc_build_analyze',
        'response_type': 'build_analysis',
        'reply': analisis['texto'],
        'armado_context': ctx,
        'armado': {
            'ok': True,
            'estado': analisis.get('estado'),
            'total_clp': analisis.get('total_clp'),
            'advertencias': analisis.get('advertencias'),
            'piezas': analisis.get('piezas'),
        },
    }


def ejecutar_reemplazo_armado_chat(
    texto: str,
    build_context: dict | None = None,
    builder_componentes: list | None = None,
    categoria_llm: str | None = None,
) -> dict:
    componentes = fusionar_componentes_activos(build_context, builder_componentes)
    categoria = categoria_llm or detectar_categoria_armado(texto)
    if not categoria:
        return {
            'intent': 'pc_build_replace',
            'response_type': 'clarification',
            'reply': (
                '¿Qué pieza quieres reemplazar? Por ejemplo: GPU, CPU, fuente de poder o RAM.'
            ),
        }
    preferencia = 'cheaper' if re.search(r'barat', texto or '', re.I) else 'default'
    propuesta = proponer_reemplazo(componentes, categoria, preferencia=preferencia)
    if not propuesta.get('ok'):
        return {
            'intent': 'pc_build_replace',
            'response_type': 'clarification',
            'reply': propuesta.get('mensaje', 'No pude proponer un reemplazo.'),
        }
    ctx = dict(build_context or {})
    ctx['componentes'] = componentes
    ctx['pending_action'] = propuesta['pending_action']
    return {
        'intent': 'pc_build_replace',
        'response_type': 'build_pending_change',
        'reply': _mensaje_confirmacion_pendiente(propuesta['pending_action']),
        'armado_context': ctx,
        'pending_build_action': propuesta['pending_action'],
        'armado': {'ok': True, 'preview': propuesta.get('analisis', {}).get('estado')},
    }


def comando_armado_por_reglas(
    texto: str,
    build_context: dict | None,
    builder_componentes: list | None,
) -> dict | None:
    confirmado = intentar_confirmar_accion(texto, build_context)
    if confirmado:
        return confirmado
    if _ANALIZAR.search(texto or ''):
        return ejecutar_analisis_armado_chat(texto, build_context, builder_componentes)
    activo = fusionar_componentes_activos(build_context, builder_componentes)
    if activo and (
        _REEMPLAZAR.search(texto or '')
        or (_MAS_BARATO_PIEZA.search(texto or '') and detectar_categoria_armado(texto))
    ):
        return ejecutar_reemplazo_armado_chat(texto, build_context, builder_componentes)
    return None


def ejecutar_intent_armado_builder(
    intent: str,
    texto: str,
    build_context: dict | None,
    builder_componentes: list | None,
    *,
    categoria_llm: str | None = None,
    presupuesto_llm: int | None = None,
    proposito_llm: str | None = None,
) -> dict:
    if intent == 'pc_build_analyze':
        return ejecutar_analisis_armado_chat(texto, build_context, builder_componentes)
    if intent in ('pc_build_replace', 'pc_build_modify'):
        if intent == 'pc_build_modify' and not _REEMPLAZAR.search(texto or '') and not categoria_llm:
            return ejecutar_armado_chat(
                texto,
                build_context=build_context,
                presupuesto_llm=presupuesto_llm,
                proposito_llm=proposito_llm,
            )
        return ejecutar_reemplazo_armado_chat(
            texto,
            build_context,
            builder_componentes,
            categoria_llm=categoria_llm,
        )
    return ejecutar_armado_chat(
        texto,
        build_context=build_context,
        presupuesto_llm=presupuesto_llm,
        proposito_llm=proposito_llm,
    )
