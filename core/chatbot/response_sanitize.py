"""Sanitiza textos de BD antes de enviarlos al LLM (anti-inyección de instrucciones)."""
from __future__ import annotations

import re

_MAX_CAMPO = 500


def sanitizar_dato_catalogo(texto: str) -> str:
    limpio = (texto or '').replace('\r', ' ').replace('\n', ' ')
    limpio = re.sub(r'\s+', ' ', limpio).strip()
    limpio = limpio[:_MAX_CAMPO]
    return limpio.replace('```', '').replace('<<<', '').replace('>>>', '')
