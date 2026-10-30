"""Respuestas FAQ del chatbot (fuente: core.faq_tienda)."""
from __future__ import annotations

from django.conf import settings

from core.faq_tienda import faq_respuesta_chat


def obtener_faq(clave: str) -> str | None:
    overrides = getattr(settings, 'HARDWAREHOUSE_CHAT_FAQ', None) or {}
    if isinstance(overrides, dict) and clave in overrides:
        return str(overrides[clave])
    return faq_respuesta_chat(clave)
