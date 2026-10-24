"""Extracción de intención vía Ollama (JSON estructurado)."""
from __future__ import annotations

import json
import logging

from django.conf import settings

from core.chatbot.llm.intent_schema import IntentoLLM, validar_intento_llm
from core.chatbot.llm.ollama import OllamaClient
from core.chatbot.security import historial_para_llm

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Eres el clasificador de intenciones del asistente de HardWareHouse (tienda chilena de hardware y armado de PC).
Analiza el mensaje del usuario (y el contexto reciente) y responde SOLO con un objeto JSON válido, sin markdown ni texto extra.

Intents permitidos:
- product_search: buscar productos concretos en catálogo (nombre, categoría, marca, precio).
- product_recommendation: sugerencias por presupuesto sin armar PC completo.
- pc_build: armar PC nuevo (presupuesto, gaming/oficina/edición, piezas compatibles).
- pc_build_modify: ajustar presupuesto/propósito de un armado sugerido (más barato, AMD/Intel).
- pc_build_analyze: revisar compatibilidad/costo del armado actual del usuario.
- pc_build_replace: cambiar una pieza (ej. GPU más barata) sobre armado existente.
- store_faq: políticas de tienda (envío, retiro, pagos, ubicación, garantía, cómo comprar).
- order_status: estado de pedidos del usuario.
- greeting: saludo o despedida breve.
- clarification: mensaje demasiado vago; falta presupuesto, producto o tema.
- off_topic: temas ajenos a la tienda o hardware.

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
- "700 lucas" / "lucas" / "palos" → budget_clp en miles (700 lucas = 700000).
- Tolerá modismos, errores de tipeo y español informal chileno; corrige mentalmente typos al clasificar.
- Mensajes cortos de seguimiento ("más barato", "usa AMD") con contexto de armado → pc_build_modify.
- Si no estás seguro del producto o tema, usa clarification (no product_search).
- off_topic solo si claramente no es tienda ni hardware.
"""


def intent_llm_activo() -> bool:
    if not getattr(settings, 'HARDWAREHOUSE_CHAT_INTENT_LLM', False):
        return False
    return bool(getattr(settings, 'OLLAMA_BASE_URL', '') or '')


def extraer_intencion_ollama(
    mensaje: str,
    historial: list | None = None,
) -> IntentoLLM | None:
    if not intent_llm_activo():
        return None

    cliente = OllamaClient()
    if not cliente.disponible():
        return None

    mensajes = [{'role': 'system', 'content': _SYSTEM_PROMPT}]
    for item in historial_para_llm(historial):
        mensajes.append({'role': item['role'], 'content': item['content']})
    mensajes.append({'role': 'user', 'content': mensaje})

    raw = cliente.chat_json(mensajes)
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning('Ollama devolvió JSON inválido para intención')
        return None

    intento = validar_intento_llm(data)
    if intento is None or not intento.confiable():
        return None
    return intento
