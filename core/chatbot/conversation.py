"""Capa conversacional pública (delega en el motor local)."""
from __future__ import annotations

from core.chatbot.assistant_config import get_asistente_config
from core.chatbot.engine import ejecutar_motor


def mensaje_bienvenida() -> str:
    return get_asistente_config().mensaje_bienvenida


def generar_respuesta(
    mensaje: str,
    historial: list | None = None,
    usuario=None,
    build_context: dict | None = None,
    builder_componentes: list | None = None,
) -> dict:
    """Devuelve reply (texto) y metadatos opcionales. Solo información verificable."""
    return ejecutar_motor(
        mensaje,
        historial=historial,
        usuario=usuario,
        build_context=build_context,
        builder_componentes=builder_componentes,
    )
