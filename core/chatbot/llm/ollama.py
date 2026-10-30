"""Cliente Ollama local (clasificación JSON y chat)."""
from __future__ import annotations

import logging

from django.conf import settings

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

logger = logging.getLogger(__name__)
debug_log = logging.getLogger('hardwarehouse.chat')


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
        self.model = (
            getattr(settings, 'OLLAMA_MODEL', None) or cfg.get('model') or 'qwen3:4b-instruct'
        )
        self.timeout = int(
            cfg.get('timeout') or getattr(settings, 'OLLAMA_TIMEOUT', 25)
        )
        self.tags_timeout = int(cfg.get('tags_timeout') or 2)
        self._tags_ok: bool | None = None

    def disponible(self) -> bool:
        if self._tags_ok is not None:
            return self._tags_ok
        if requests is None:
            debug_log.info('ollama api=tags ok=false model=%s reason=requests_missing', self.model)
            self._tags_ok = False
            return False
        if not self.base_url:
            debug_log.info('ollama api=tags ok=false model=%s reason=base_url_empty', self.model)
            self._tags_ok = False
            return False
        try:
            r = requests.get(f'{self.base_url}/api/tags', timeout=self.tags_timeout)
            ok = r.status_code == 200
            debug_log.info(
                'ollama api=tags ok=%s model=%s status=%s',
                str(ok).lower(),
                self.model,
                r.status_code,
            )
            self._tags_ok = ok
            return ok
        except requests.RequestException as exc:
            debug_log.info(
                'ollama api=tags ok=false model=%s reason=%s',
                self.model,
                type(exc).__name__,
            )
            self._tags_ok = False
            return False

    def _chat(self, messages: list[dict], *, json_mode: bool) -> str | None:
        modo = 'chat_json' if json_mode else 'chat_text'
        if requests is None or not self.disponible():
            debug_log.info(
                'ollama api=%s ok=false model=%s reason=unavailable',
                modo,
                self.model,
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
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
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
            status = getattr(getattr(exc, 'response', None), 'status_code', None)
            debug_log.info(
                'ollama api=%s ok=false model=%s reason=%s status=%s',
                modo,
                self.model,
                type(exc).__name__,
                status,
            )
            logger.warning('Error Ollama: %s', type(exc).__name__)
            return None

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
        mensajes = [{'role': 'system', 'content': contexto_sistema.get('rol', '')}]
        if historial:
            for item in historial[-6:]:
                if isinstance(item, dict) and item.get('role') in ('user', 'assistant'):
                    mensajes.append(
                        {'role': item['role'], 'content': str(item.get('content', ''))[:2000]}
                    )
        mensajes.append({'role': 'user', 'content': mensaje})
        return self.chat_json(mensajes)
