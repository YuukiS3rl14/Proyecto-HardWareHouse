"""
Preguntas frecuentes compartidas: chatbot y página Sobre nosotros.

La fuente verificada es core/knowledge/hardwarehouse.json.
"""
from __future__ import annotations

from core.knowledge.service import faq_items_pagina, texto_faq


def faq_respuesta_chat(clave: str) -> str | None:
    return texto_faq(clave)


def faq_items_acordeon() -> list[dict]:
    return faq_items_pagina()
