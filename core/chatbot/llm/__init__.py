"""Integraciones opcionales de LLM (p. ej. Ollama local). No requeridas para el chat."""
from core.chatbot.llm.base import MotorLLM, get_motor_llm_opcional

__all__ = ['MotorLLM', 'get_motor_llm_opcional']
