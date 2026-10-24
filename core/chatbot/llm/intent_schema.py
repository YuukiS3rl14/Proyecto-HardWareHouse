"""Validación server-side de la extracción de intención (JSON del LLM)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.catalogo.registry import categorias_disponibles
from core.chatbot.catalog_nl import extraer_consulta_catalogo

INTENTS_LLM = frozenset(
    {
        'product_search',
        'product_recommendation',
        'pc_build',
        'pc_build_modify',
        'pc_build_analyze',
        'pc_build_replace',
        'store_faq',
        'company_info',
        'order_status',
        'greeting',
        'clarification',
        'off_topic',
        'build_upgrade',
        'build_downgrade',
        'budget_adjustment',
        'faq',
        'orders',
    }
)

ORDENES_VALIDOS = frozenset({'relevancia', 'precio_asc', 'precio_desc', 'stock_desc'})

FAQ_TOPICS = frozenset(
    {
        'despacho',
        'retiro',
        'ubicacion_horario',
        'pago',
        'compra',
        'armado',
        'stock',
        'contacto',
        'empresa',
        'garantia',
    }
)

_CATEGORIAS = {c.lower(): c for c in categorias_disponibles()}
_MAX_BUDGET = 50_000_000
_MIN_CONFIDENCE = 0.35


@dataclass
class IntentoLLM:
    intent: str
    category: str | None = None
    brand: str | None = None
    budget_clp: int | None = None
    price_sort: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    faq_topic: str | None = None
    query_text: str | None = None

    def confiable(self) -> bool:
        return self.confidence >= _MIN_CONFIDENCE and self.intent in INTENTS_LLM


def _entero_opcional(valor) -> int | None:
    if valor is None or valor == '':
        return None
    try:
        entero = int(float(valor))
    except (TypeError, ValueError):
        return None
    if entero < 0 or entero > _MAX_BUDGET:
        return None
    return entero


def _normalizar_categoria(valor: str | None) -> str | None:
    if not valor or not isinstance(valor, str):
        return None
    limpio = valor.strip()
    if limpio in categorias_disponibles():
        return limpio
    clave = limpio.lower()
    if clave in _CATEGORIAS:
        return _CATEGORIAS[clave]
    consulta = extraer_consulta_catalogo(limpio)
    return consulta.categoria


def _normalizar_marca(valor: str | None) -> str | None:
    if not valor or not isinstance(valor, str):
        return None
    marca = valor.strip()[:80]
    return marca or None


def _normalizar_orden(valor: str | None) -> str | None:
    if not valor or not isinstance(valor, str):
        return None
    orden = valor.strip().lower()
    if orden in ORDENES_VALIDOS:
        return orden
    if orden in ('barato', 'barata', 'asc', 'menor_precio', 'cheap'):
        return 'precio_asc'
    if orden in ('caro', 'cara', 'desc', 'mayor_precio', 'expensive'):
        return 'precio_desc'
    return None


def _filtros_dict(raw) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    limpio: dict[str, Any] = {}
    for clave in ('solo_stock', 'solo_con_stock', 'in_stock'):
        if clave in raw:
            limpio['solo_stock'] = bool(raw[clave])
    if 'precio_min' in raw:
        limpio['precio_min'] = _entero_opcional(raw.get('precio_min'))
    if 'precio_max' in raw:
        limpio['precio_max'] = _entero_opcional(raw.get('precio_max'))
    if 'faq_topic' in raw and isinstance(raw['faq_topic'], str):
        topic = raw['faq_topic'].strip().lower()
        if topic in FAQ_TOPICS:
            limpio['faq_topic'] = topic
    if 'query' in raw and isinstance(raw['query'], str):
        q = raw['query'].strip()[:200]
        if q:
            limpio['query'] = q
    if 'purpose' in raw and isinstance(raw['purpose'], str):
        p = raw['purpose'].strip().lower()
        if p in ('gaming', 'office', 'editing', 'general'):
            limpio['purpose'] = p
    if 'cpu_brand' in raw and isinstance(raw['cpu_brand'], str):
        b = raw['cpu_brand'].strip().lower()
        if b in ('amd', 'intel'):
            limpio['cpu_brand'] = b
    if 'build_category' in raw and isinstance(raw['build_category'], str):
        cat = raw['build_category'].strip().lower()[:40]
        if cat:
            limpio['build_category'] = cat
    return limpio


def validar_intento_llm(data: dict | None) -> IntentoLLM | None:
    if not isinstance(data, dict):
        return None
    intent = data.get('intent')
    if not isinstance(intent, str):
        return None
    intent = intent.strip().lower()
    if intent not in INTENTS_LLM:
        return None

    try:
        confidence = float(data.get('confidence', 0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    filtros = _filtros_dict(data.get('filters'))
    faq_topic = filtros.get('faq_topic')
    if isinstance(data.get('faq_topic'), str):
        t = data['faq_topic'].strip().lower()
        if t in FAQ_TOPICS:
            faq_topic = t

    query_text = filtros.get('query')
    if isinstance(data.get('query_text'), str) and data['query_text'].strip():
        query_text = data['query_text'].strip()[:200]

    return IntentoLLM(
        intent=intent,
        category=_normalizar_categoria(data.get('category')),
        brand=_normalizar_marca(data.get('brand')),
        budget_clp=_entero_opcional(data.get('budget_clp')),
        price_sort=_normalizar_orden(data.get('price_sort')),
        filters=filtros,
        confidence=confidence,
        faq_topic=faq_topic,
        query_text=query_text,
    )
