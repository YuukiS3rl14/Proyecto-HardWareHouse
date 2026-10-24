"""Alcance, privacidad y tono del asistente (reglas centralizadas)."""
from __future__ import annotations

import re
from functools import lru_cache

from core.chatbot.assistant_config import AsistenteConfig, get_asistente_config

_SALUDOS = re.compile(
    r'\b(hola|buenas|buenos días|buenas tardes|buenas noches|hey|hi|gracias)\b',
    re.I,
)


@lru_cache(maxsize=1)
def _compilar_patrones(config: AsistenteConfig) -> tuple:
    en_alcance = tuple(
        re.compile(p, re.I) for p in config.patrones_en_alcance
    )
    fuera = tuple(re.compile(p, re.I) for p in config.patrones_fuera_de_alcance)
    sensible = tuple(re.compile(p, re.I) for p in config.patrones_datos_sensibles)
    return en_alcance, fuera, sensible


def solicita_datos_sensibles(texto: str, config: AsistenteConfig | None = None) -> bool:
    config = config or get_asistente_config()
    _, _, sensible = _compilar_patrones(config)
    return any(p.search(texto) for p in sensible)


def consulta_en_alcance(texto: str, config: AsistenteConfig | None = None) -> bool:
    """
    True si la consulta puede atenderse dentro del rol del asistente.
    """
    config = config or get_asistente_config()
    limpio = (texto or '').strip()
    if not limpio:
        return False
    bajo = limpio.lower()
    en_alcance, fuera, _ = _compilar_patrones(config)

    if _SALUDOS.search(bajo) and len(limpio) < 60:
        return True

    coincide_alcance = any(p.search(bajo) for p in en_alcance)
    coincide_fuera = any(p.search(bajo) for p in fuera)

    if coincide_fuera and not coincide_alcance:
        return False
    if coincide_alcance:
        return True

    # Presupuesto numérico implícito
    if re.search(
        r'(?:presupuesto|hasta|máximo|maximo|bajo)\s*\$?\s*[\d.\s]+',
        bajo,
        re.I,
    ):
        return True

    # Posible nombre de producto / modelo (letras y números)
    if len(limpio) >= 3 and re.search(r'[a-záéíóúñ]', bajo, re.I) and re.search(r'\d', limpio):
        return True

    if len(limpio) >= 4 and re.search(r'[a-záéíóúñ]{4,}', bajo, re.I):
        return True

    return False


def metadata_sistema(config: AsistenteConfig | None = None) -> dict:
    """Metadatos para APIs o futuros integraciones LLM (sin datos privados)."""
    config = config or get_asistente_config()
    return {
        'nombre': config.nombre,
        'idioma': config.idioma,
        'rol': config.rol,
        'tono': config.tono,
        'temas_permitidos': list(config.temas_permitidos),
        'reglas': list(config.reglas_comportamiento),
    }
