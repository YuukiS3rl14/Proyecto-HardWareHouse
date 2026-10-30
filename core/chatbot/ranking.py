"""Puntuación de relevancia para resultados de catálogo."""
from __future__ import annotations

import re

from core.chatbot.texto import normalizar_texto

_TOKEN = re.compile(r'[\wáéíóúñ]+', re.I)


def _tokens(texto: str) -> list[str]:
    norm = normalizar_texto(texto or '')
    return [t for t in _TOKEN.findall(norm) if len(t) > 1]


def puntuar_producto(
    producto,
    consulta: str,
    *,
    categoria_filtro: str | None = None,
    marca_filtro: str | None = None,
) -> float:
    q = (consulta or '').strip().lower()
    tokens = _tokens(q)
    nombre = (producto.nombre or '').lower()
    marca = (producto.proveedor.nombre or '').lower()
    categoria = (producto.categoria or '').lower()
    score = 0.0

    if q:
        if q in nombre:
            score += 12.0
        if q in marca:
            score += 6.0
        if q in categoria:
            score += 3.0
        for token in tokens:
            if token in nombre:
                score += 2.5
            if token in marca:
                score += 1.5
            if token in categoria:
                score += 0.5

    if categoria_filtro and producto.categoria == categoria_filtro:
        score += 4.0
    if marca_filtro and producto.proveedor.nombre.lower() == marca_filtro.lower():
        score += 4.0
    if producto.stock > 0:
        score += 1.0
    return score
