"""Extracción de intención vía Ollama (JSON estructurado)."""
from __future__ import annotations

import json
import logging

from django.conf import settings

from core.chatbot.llm.intent_schema import IntentoLLM, validar_intento_llm
from core.chatbot.llm.ollama import OllamaClient
from core.chatbot.security import historial_para_llm, texto_para_llm

logger = logging.getLogger(__name__)
debug_log = logging.getLogger('hardwarehouse.chat')

_SYSTEM_PROMPT = """Eres el clasificador de intenciones del asistente de HardWareHouse (tienda chilena de hardware y armado de PC).
Analiza el mensaje del usuario (y el contexto reciente) y responde SOLO con un objeto JSON válido, sin markdown ni texto extra.

Intents permitidos:
- pc_build: armar un PC nuevo (presupuesto, gaming/oficina/edición).
- build_upgrade: mejorar el armado o una pieza (más potente, mejor GPU, upgrade).
- build_downgrade: bajar una pieza o el armado (más barata, downgrade).
- budget_adjustment: cambiar el presupuesto del armado ("más barato", "súbelo a 800 lucas") sin buscar productos sueltos.
- product_search: buscar un producto concreto del catálogo (nombre, categoría, marca, precio).
- faq: políticas, despacho, retiro, pagos, garantía, historia, misión o contacto.
- orders: estado de pedidos del usuario.
- greeting: saludo o despedida breve.
- clarification: mensaje vago, typo irreconocible o seguimiento sin datos suficientes. Úsalo si no estás seguro.
- off_topic: temas ajenos a la tienda o al hardware.
Aliases aceptados si aparecen: product_recommendation, pc_build_modify, pc_build_analyze, pc_build_replace, store_faq, company_info, order_status.

Campos JSON:
{
  "intent": "...",
  "category": null o categoría (CPU, Tarjeta Gráfica, Memoria RAM, Placa Madre, SSD, etc.),
  "brand": null o marca,
  "budget_clp": null o entero CLP,
  "price_sort": null o relevancia|precio_asc|precio_desc|stock_desc,
  "filters": {"solo_stock": bool, "precio_min": null, "precio_max": null, "faq_topic": null, "query": null},
  "confidence": 0.0 a 1.0,
  "faq_topic": null o despacho|retiro|ubicacion_horario|pago|compra|armado|stock|contacto|empresa|garantia,
  "query_text": null o términos de búsqueda libres
}

Reglas:
- No inventes productos, precios ni stock.
- delivery/envío/despacho → store_faq con faq_topic despacho (NO product_search).
- retiro en tienda → store_faq retiro.
- "700 lucas", "700 mil" y "700k" → budget_clp 700000.
- "un millón", "1m", "1 palo" y "1000 lucas" → budget_clp 1000000. "1.5m" → 1500000.
- "1 palo" es un millón, no mil.
- Tolerá modismos, sinónimos, errores de tipeo y español informal chileno.
- Con ultimo_intent de armado, "más barato", "the cheaper one", "reduce the price" o "baja el precio" → build_downgrade.
- "prioriza gaming", "improve it", "mejóralo" o "upgrade the graphics card" → build_upgrade.
- "qué podemos mejorar" → pc_build_analyze.
- "ese PC", "that PC", "usa el resto" y "use the rest" continúan el armado anterior. No son product_search.
- "usa el restante" / "use the remaining 400k" ajusta el armado anterior dentro del presupuesto original. No reemplaces ese presupuesto por 400000.
- Si no hay armado en el contexto y el mensaje solo dice "ese PC" o "mejóralo", usa clarification.
- Nunca uses product_search para un mensaje desconocido, un saludo, una FAQ o un seguimiento de armado.
- Si no estás seguro del producto o tema, usa clarification.
- off_topic solo si claramente no es tienda ni hardware.
"""


def intent_llm_activo() -> bool:
    if not getattr(settings, 'HARDWAREHOUSE_CHAT_INTENT_LLM', False):
        return False
    return bool(getattr(settings, 'OLLAMA_BASE_URL', '') or '')


def _nota_contexto(build_context: dict | None) -> str | None:
    if not isinstance(build_context, dict):
        return None
    partes = []
    intent = build_context.get('ultimo_intent')
    if isinstance(intent, str) and intent:
        partes.append(f'ultimo_intent={intent[:40]}')
    presupuesto = build_context.get('presupuesto_clp')
    if isinstance(presupuesto, int):
        partes.append(f'presupuesto_clp={presupuesto}')
    proposito = build_context.get('proposito')
    if isinstance(proposito, str) and proposito:
        partes.append(f'proposito={proposito[:20]}')
    if build_context.get('componentes'):
        partes.append('tiene_armado=si')
    if not partes:
        return None
    return 'Contexto previo verificado (no inventes productos): ' + ', '.join(partes)


def extraer_intencion_ollama(
    mensaje: str,
    historial: list | None = None,
    build_context: dict | None = None,
) -> IntentoLLM | None:
    if not intent_llm_activo():
        debug_log.info(
            'chat route=reglas intent=- model=- ollama=skipped reason=intent_llm_disabled chars=%s',
            len(mensaje or ''),
        )
        return None

    cliente = OllamaClient()
    if not cliente.disponible():
        debug_log.info(
            'chat route=reglas intent=- model=%s ollama=failed reason=provider_unavailable chars=%s',
            cliente.model,
            len(mensaje or ''),
        )
        return None

    usuario = texto_para_llm((mensaje or '').strip(), limite=500)
    if not usuario:
        debug_log.info(
            'chat route=reglas intent=- model=%s ollama=skipped reason=context_redacted chars=0',
            cliente.model,
        )
        return None

    mensajes = [{'role': 'system', 'content': _SYSTEM_PROMPT}]
    nota = _nota_contexto(build_context)
    if nota:
        mensajes.append({'role': 'system', 'content': nota})
    for item in historial_para_llm(historial):
        mensajes.append({'role': item['role'], 'content': item['content']})
    mensajes.append({'role': 'user', 'content': usuario})

    raw = cliente.chat_json(mensajes)
    if not raw:
        debug_log.info(
            'chat route=reglas intent=- model=%s ollama=failed reason=empty_chat_response chars=%s',
            cliente.model,
            len(mensaje or ''),
        )
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        debug_log.info(
            'chat route=reglas intent=- model=%s ollama=failed reason=invalid_json chars=%s',
            cliente.model,
            len(raw),
        )
        logger.warning('Ollama devolvió JSON inválido para intención')
        return None

    intento = validar_intento_llm(data)
    if intento is None:
        debug_log.info(
            'chat route=reglas intent=- model=%s ollama=failed reason=schema_rejected',
            cliente.model,
        )
        return None
    if not intento.confiable():
        debug_log.info(
            'chat route=reglas intent=%s model=%s ollama=ok reason=low_confidence confidence=%.2f',
            intento.intent,
            cliente.model,
            intento.confidence,
        )
        return None
    debug_log.info(
        'chat route=ollama intent=%s model=%s ollama=ok confidence=%.2f category=%s',
        intento.intent,
        cliente.model,
        intento.confidence,
        intento.category or '-',
    )
    return intento
