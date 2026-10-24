"""Normalización de texto para el chatbot (sin dependencias internas)."""
from __future__ import annotations

import re
import unicodedata


def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize('NFD', texto or '')
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', texto.lower()).strip()
