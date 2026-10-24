"""Extracción de entidades desde lenguaje natural (sin APIs de IA)."""
from __future__ import annotations

import re

_PRESUPUESTO = re.compile(
    r'(?:presupuesto(?:\s+(?:hasta|máximo|maximo|bajo))?|hasta|máximo|maximo|bajo)'
    r'\s*\$?\s*([\d.\s]+)\s*(?:mil|k\b)?',
    re.I,
)

_STOPWORDS_BUSQUEDA = re.compile(
    r'\b(busco|quiero|necesito|precio de|cuánto cuesta|cuanto cuesta|hay|tienen|'
    r'me interesa|algún|algun|una|un|el|la|los|las|de|para|'
    r'stock|disponible|agotado)\b',
    re.I,
)


def parse_presupuesto_clp(texto: str) -> int | None:
    match = _PRESUPUESTO.search(texto or '')
    if not match:
        return None
    raw = match.group(1).replace(' ', '').replace('.', '')
    if not raw.isdigit():
        return None
    valor = int(raw)
    if re.search(r'\bmil\b|\bk\b', texto, re.I) and valor < 10000:
        valor *= 1000
    return valor


def extraer_termino_busqueda(texto: str) -> str:
    """Quita verbos de intención y deja términos de producto."""
    bajo = (texto or '').strip().lower()
    consulta = _STOPWORDS_BUSQUEDA.sub('', bajo).strip()
    consulta = re.sub(r'[^\w\sáéíóúñü]+', ' ', consulta, flags=re.I)
    consulta = re.sub(r'\s+', ' ', consulta).strip()
    if len(consulta) >= 2:
        return consulta
    limpio = re.sub(r'[^\w\sáéíóúñü]+', ' ', (texto or '').lower(), flags=re.I)
    return re.sub(r'\s+', ' ', limpio).strip()


TERMINOS_BUSQUEDA_GENERICOS = frozenset(
    {'algo', 'alguno', 'producto', 'productos', 'cosa', 'cosas', 'uno', 'una', 'ayuda', 'info'}
)


def termino_busqueda_especifico(texto: str) -> bool:
    termino = extraer_termino_busqueda(texto).strip().lower()
    if len(termino) < 2:
        return False
    return termino not in TERMINOS_BUSQUEDA_GENERICOS
