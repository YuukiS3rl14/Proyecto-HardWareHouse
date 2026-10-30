"""Datos de sesión del chat permitidos en el cliente (sin pedidos ni credenciales)."""
from __future__ import annotations

from core.chatbot.security import validar_build_context


def build_context_persistible(raw: dict | None) -> dict | None:
    if not raw or not isinstance(raw, dict):
        return None
    limpio = validar_build_context({'build_context': raw})
    if not limpio:
        return None
    if 'pedidos' in limpio:
        limpio.pop('pedidos', None)
    return limpio
