"""Presupuesto chileno, propósito y ajustes de armado en lenguaje natural."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from core.chatbot.nlp import parse_presupuesto_clp

_LUCAS = re.compile(
    r'(\d{1,4})\s*(?:lucas|luca|palos|gamba|gambas)\b',
    re.I,
)
_PROPOSITO = re.compile(
    r'\b(gaming|gamer|juegos|oficina|office|edici[oó]n|edicion|video|streaming|trabajo)\b',
    re.I,
)
_MAS_BARATO = re.compile(
    r'\b(mas barato|más barato|mas economico|más económico|bajar presupuesto|achicar)\b',
    re.I,
)
_AMD = re.compile(r'\b(amd|ryzen)\b', re.I)
_INTEL = re.compile(r'\b(intel|core i\d)\b', re.I)


@dataclass
class SolicitudArmadoNL:
    presupuesto_clp: int | None = None
    proposito: str = 'general'
    preferencia_cpu: str | None = None
    indice_economico: int = 0
    ajuste: str | None = None


def _parse_lucas(texto: str) -> int | None:
    match = _LUCAS.search(texto or '')
    if not match:
        return None
    return int(match.group(1)) * 1000


def _detectar_proposito(texto: str) -> str:
    bajo = (texto or '').lower()
    if _PROPOSITO.search(bajo):
        m = _PROPOSITO.search(bajo)
        palabra = m.group(1).lower()
        if palabra in ('gaming', 'gamer', 'juegos', 'streaming'):
            return 'gaming'
        if palabra in ('oficina', 'office', 'trabajo'):
            return 'office'
        if 'edic' in palabra or palabra == 'video':
            return 'editing'
    return 'general'


def parsear_solicitud_armado(
    texto: str,
    build_context: dict[str, Any] | None = None,
    extraido_budget: int | None = None,
) -> SolicitudArmadoNL:
    ctx = build_context or {}
    presupuesto = extraido_budget or _parse_lucas(texto) or parse_presupuesto_clp(texto)
    if presupuesto is None and ctx.get('presupuesto_clp'):
        presupuesto = int(ctx['presupuesto_clp'])

    proposito = _detectar_proposito(texto) if texto else 'general'
    if proposito == 'general' and ctx.get('proposito'):
        proposito = str(ctx['proposito'])

    preferencia = None
    if _AMD.search(texto or ''):
        preferencia = 'amd'
    elif _INTEL.search(texto or ''):
        preferencia = 'intel'
    elif ctx.get('preferencia_cpu'):
        preferencia = str(ctx['preferencia_cpu'])

    indice = int(ctx.get('indice_economico') or 0)
    ajuste = None
    if _MAS_BARATO.search(texto or ''):
        ajuste = 'cheaper'
        indice = min(indice + 1, 4)
        if presupuesto is None and ctx.get('presupuesto_clp'):
            presupuesto = int(int(ctx['presupuesto_clp']) * 0.88)
        elif presupuesto is not None:
            presupuesto = int(presupuesto * 0.88)

    return SolicitudArmadoNL(
        presupuesto_clp=presupuesto,
        proposito=proposito,
        preferencia_cpu=preferencia,
        indice_economico=indice,
        ajuste=ajuste,
    )
