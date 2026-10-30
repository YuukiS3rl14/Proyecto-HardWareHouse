"""Tipos de respuesta del asistente (generación controlada)."""
from __future__ import annotations

PRODUCT_NOT_FOUND = 'product_not_found'
PRODUCT_RESULTS = 'product_results'
CLARIFICATION = 'clarification'
OFF_TOPIC = 'off_topic'
FAQ = 'faq'
ORDER_STATUS = 'order_status'
ORDER_LOGIN = 'order_login'
GREETING = 'greeting'
BUDGET = 'budget'
PRIVACY = 'privacy'
GENERIC = 'generic'

# Solo estos tipos pueden pasar por redacción Ollama (nunca catálogo).
OLLAMA_POLISH_TIPOS = frozenset(
    {FAQ, CLARIFICATION, OFF_TOPIC, GREETING, ORDER_STATUS, ORDER_LOGIN, GENERIC}
)
