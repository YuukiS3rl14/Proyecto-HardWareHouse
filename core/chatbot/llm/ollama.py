"""Cliente Ollama local o remoto. Si no responde, el motor de reglas sigue igual."""
from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from django.conf import settings

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

logger = logging.getLogger(__name__)
debug_log = logging.getLogger('hardwarehouse.chat')

_SALUD: dict[str, tuple[float, bool]] = {}
_SALUD_TTL = 60.0
_HOSTS_LOCALES = frozenset({'127.0.0.1', 'localhost', '::1'})
_MODELO_LOCAL = 'qwen3:4b-instruct'


def olvidar_salud_ollama() -> None:
    """Limpia la caché de /api/tags para que un test no herede el resultado anterior."""
    _SALUD.clear()


def _host(url: str) -> str:
    return (urlparse(url).hostname or '').lower()


def _es_loopback(url: str) -> bool:
    return _host(url) in _HOSTS_LOCALES


class OllamaClient:
    def __init__(self) -> None:
        cfg = getattr(settings, 'HARDWAREHOUSE_CHAT_OLLAMA', None) or {}
        if not isinstance(cfg, dict):
            cfg = {}
        self.base_url = (
            getattr(settings, 'OLLAMA_BASE_URL', None)
            or cfg.get('base_url')
            or 'http://127.0.0.1:11434'
        ).rstrip('/')
        explicito = getattr(settings, 'OLLAMA_MODEL', None)
        if explicito is None:
            explicito = cfg.get('model')
        explicito = (explicito or '').strip()
        if explicito:
            self.model = explicito
        elif _es_loopback(self.base_url):
            self.model = _MODELO_LOCAL
        else:
            self.model = ''
        self.api_key = (getattr(settings, 'OLLAMA_API_KEY', '') or '').strip()
        self.timeout = int(getattr(settings, 'OLLAMA_TIMEOUT', None) or cfg.get('timeout') or 10)
        self.tags_timeout = int(cfg.get('tags_timeout') or 2)
        self._remoto = bool(self.base_url) and not _es_loopback(self.base_url)

    def _headers(self) -> dict[str, str]:
        if urlparse(self.base_url).scheme != 'https' or not self.api_key:
            return {}
        return {'Authorization': f'Bearer {self.api_key}'}

    def disponible(self) -> bool:
        if requests is None or not self.base_url or not self.model:
            debug_log.info('ollama api=tags ok=false model=%s reason=unavailable', self.model or '-')
            return False
        if self._remoto:
            return True
        ahora = time.monotonic()
        guardado = _SALUD.get(self.base_url)
        if guardado and ahora - guardado[0] < _SALUD_TTL:
            return guardado[1]
        ok = False
        status = None
        try:
            r = requests.get(
                f'{self.base_url}/api/tags',
                timeout=self.tags_timeout,
                allow_redirects=False,
            )
            status = r.status_code
            ok = status == 200
        except requests.RequestException as exc:
            debug_log.info(
                'ollama api=tags ok=false model=%s reason=%s',
                self.model,
                type(exc).__name__,
            )
            ok = False
        else:
            debug_log.info(
                'ollama api=tags ok=%s model=%s status=%s',
                str(ok).lower(),
                self.model,
                status,
            )
        if not ok:
            logger.info('Ollama local no disponible')
        _SALUD[self.base_url] = (ahora, ok)
        return ok

    def _chat(self, messages: list[dict], *, json_mode: bool) -> str | None:
        modo = 'chat_json' if json_mode else 'chat_text'
        if requests is None or not self.disponible():
            debug_log.info(
                'ollama api=%s ok=false model=%s reason=unavailable',
                modo,
                self.model or '-',
            )
            return None
        payload = {
            'model': self.model,
            'stream': False,
            'messages': messages,
            'options': {'temperature': 0.1},
        }
        if json_mode:
            payload['format'] = 'json'
        try:
            r = requests.post(
                f'{self.base_url}/api/chat',
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
                allow_redirects=False,
            )
        except requests.Timeout:
            debug_log.info(
                'ollama api=%s ok=false model=%s reason=timeout timeout_s=%s',
                modo,
                self.model,
                self.timeout,
            )
            logger.warning('Timeout al llamar a Ollama (%ss)', self.timeout)
            return None
        except requests.RequestException as exc:
            debug_log.info(
                'ollama api=%s ok=false model=%s reason=%s',
                modo,
                self.model,
                type(exc).__name__,
            )
            logger.warning('Ollama no respondió: %s', type(exc).__name__)
            return None
        if r.status_code in (401, 429) or r.status_code >= 300:
            debug_log.info(
                'ollama api=%s ok=false model=%s reason=http_status status=%s',
                modo,
                self.model,
                r.status_code,
            )
            logger.warning('Ollama rechazó la solicitud (estado %s)', r.status_code)
            return None
        try:
            data = r.json()
        except ValueError:
            debug_log.info(
                'ollama api=%s ok=false model=%s reason=invalid_json',
                modo,
                self.model,
            )
            logger.warning('Ollama devolvió una respuesta ilegible')
            return None
        if not isinstance(data, dict):
            return None
        msg = data.get('message') or {}
        content = (msg.get('content') or '').strip()
        debug_log.info(
            'ollama api=%s ok=%s model=%s status=%s chars=%s',
            modo,
            'true' if content else 'false',
            self.model,
            r.status_code,
            len(content),
        )
        return content or None

    def chat_json(self, messages: list[dict]) -> str | None:
        return self._chat(messages, json_mode=True)

    def chat_texto(self, messages: list[dict]) -> str | None:
        return self._chat(messages, json_mode=False)


class OllamaMotor(OllamaClient):
    """Alias retrocompatible con la interfaz MotorLLM."""

    def completar(
        self,
        mensaje: str,
        historial: list | None,
        contexto_sistema: dict,
    ) -> str | None:
        from core.chatbot.security import historial_para_llm, texto_para_llm

        mensajes = [{'role': 'system', 'content': texto_para_llm(str(contexto_sistema.get('rol', '')), limite=800)}]
        for item in historial_para_llm(historial):
            mensajes.append(item)
        usuario = texto_para_llm(mensaje or '', limite=500)
        if not usuario:
            return None
        mensajes.append({'role': 'user', 'content': usuario})
        return self.chat_json(mensajes)
