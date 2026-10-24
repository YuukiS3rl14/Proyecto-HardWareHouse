"""Contrato para motores opcionales (Ollama, etc.)."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from django.conf import settings


@runtime_checkable
class MotorLLM(Protocol):
    def disponible(self) -> bool: ...

    def completar(
        self,
        mensaje: str,
        historial: list | None,
        contexto_sistema: dict,
    ) -> str | None:
        """Texto sugerido o None si no aplica / falla."""


def get_motor_llm_opcional() -> MotorLLM | None:
    backend = getattr(settings, 'HARDWAREHOUSE_CHAT_LLM_BACKEND', '') or ''
    if backend.lower() == 'ollama' or getattr(settings, 'OLLAMA_BASE_URL', ''):
        from core.chatbot.llm.ollama import OllamaMotor

        motor = OllamaMotor()
        return motor if motor.disponible() else None
    return None
