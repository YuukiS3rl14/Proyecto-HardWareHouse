"""Extracción de entidades desde lenguaje natural (sin APIs de IA)."""
from __future__ import annotations

import re

_MAX_PRESUPUESTO = 50_000_000
_UN_MILLON = re.compile(r'\b(?:un|una)\s+mill[oó]n(?:es)?\b', re.I)
_MILLON = re.compile(
    r'(\d+(?:[.,]\d+)?)\s*(?:m\b|mill[oó]n(?:es)?)\b',
    re.I,
)
_PALO = re.compile(r'\b(?:(\d+(?:[.,]\d+)?)|un|una)\s*palos?\b', re.I)
_LUCAS = re.compile(r'(\d{1,4})\s*(?:lucas|luca|gambas?)\b', re.I)
_MIL = re.compile(r'(\d{1,5}(?:[.,]\d+)?)\s*(?:mil|k)\b', re.I)
_PRESUPUESTO = re.compile(
    r'(?:presupuesto(?:\s+(?:hasta|máximo|maximo|bajo))?|hasta|máximo|maximo|bajo)'
    r'\s*\$?\s*([\d.\s]+)\s*(mil|k|palos?|m|mill[oó]n(?:es)?)?\b',
    re.I,
)

_STOPWORDS_BUSQUEDA = re.compile(
    r'\b(busco|quiero|necesito|precio de|cuánto cuesta|cuanto cuesta|hay|tienen|'
    r'me interesa|algún|algun|una|un|el|la|los|las|de|para|'
    r'stock|disponible|agotado)\b',
    re.I,
)


def _acotar_clp(valor: int) -> int | None:
    if valor <= 0 or valor > _MAX_PRESUPUESTO:
        return None
    return valor


def _numero_flexible(raw: str) -> float | None:
    limpio = (raw or '').strip().replace(' ', '')
    if not limpio:
        return None
    if re.fullmatch(r'\d+[.,]\d{1,2}', limpio):
        try:
            return float(limpio.replace(',', '.'))
        except ValueError:
            return None
    entero = limpio.replace('.', '').replace(',', '')
    if not entero.isdigit():
        return None
    return float(entero)


def _con_unidad(numero: float, unidad: str | None) -> int | None:
    unidad = (unidad or '').lower()
    if unidad in ('m', 'millon', 'millón', 'millones', 'palo', 'palos'):
        return _acotar_clp(int(round(numero * 1_000_000)))
    if unidad in ('mil', 'k', 'lucas', 'luca', 'gamba', 'gambas'):
        if numero < 10_000:
            return _acotar_clp(int(round(numero * 1000)))
        return _acotar_clp(int(round(numero)))
    return _acotar_clp(int(round(numero)))


def normalizar_presupuesto_clp(texto: str) -> int | None:
    """Montos chilenos: 1 palo/1m/un millón/1000 lucas = 1000000; 700 lucas/700 mil/700k = 700000."""
    fuente = texto or ''
    if _UN_MILLON.search(fuente):
        return 1_000_000
    match = _MILLON.search(fuente)
    if match:
        numero = _numero_flexible(match.group(1))
        if numero is not None:
            return _con_unidad(numero, 'm')
    match = _PALO.search(fuente)
    if match:
        numero = 1.0 if not match.group(1) else _numero_flexible(match.group(1))
        if numero is not None:
            return _con_unidad(numero, 'palo')
    match = _LUCAS.search(fuente)
    if match:
        return _con_unidad(int(match.group(1)), 'lucas')
    match = _MIL.search(fuente)
    if match:
        numero = _numero_flexible(match.group(1))
        if numero is not None:
            return _con_unidad(numero, 'mil')
    return parse_presupuesto_clp(fuente)


def parse_presupuesto_clp(texto: str) -> int | None:
    match = _PRESUPUESTO.search(texto or '')
    if not match:
        return None
    numero = _numero_flexible(match.group(1))
    if numero is None:
        return None
    unidad = match.group(2)
    if not unidad and re.search(r'\bmil\b|\bk\b', texto or '', re.I) and numero < 10000:
        unidad = 'mil'
    return _con_unidad(numero, unidad)


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
