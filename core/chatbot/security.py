"""Validación de entrada, rate limiting y decoradores para APIs del chat."""
from __future__ import annotations

import json
import re
from functools import wraps
from typing import Callable

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, JsonResponse

MAX_MENSAJE = 2000
MAX_HISTORIAL_ITEMS = 20
MAX_HISTORIAL_ITEM_CHARS = 4000
MAX_HISTORIAL_LLM = 4
MAX_TEXTO_LLM = 400

_EMAIL = re.compile(r'[\w.+-]+@[\w.-]+\.\w+', re.IGNORECASE)
_RUT = re.compile(r'\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b')
_TELEFONO = re.compile(r'(?:\+?56\s*)?(?:\(?\d\)?[\s.-]*){8,}\d')
_LINEA_PERSONAL = re.compile(
    r'\b(?:e-?mail|correo|direcci[oó]n|tel[eé]fono|rut|contrase[nñ]a|password|clave)\b',
    re.IGNORECASE,
)


def texto_para_llm(texto: str, limite: int = MAX_TEXTO_LLM) -> str:
    """Quita datos personales antes de salir del servidor. El texto local no cambia."""
    if not texto:
        return ''
    lineas = []
    for linea in texto.splitlines():
        if _LINEA_PERSONAL.search(linea):
            continue
        if 'pedido #' in linea.lower():
            continue
        lineas.append(linea)
    limpio = '\n'.join(lineas)
    limpio = _EMAIL.sub('[correo]', limpio)
    limpio = _RUT.sub('[rut]', limpio)
    limpio = _TELEFONO.sub('[telefono]', limpio)
    return limpio.strip()[:limite]


def historial_para_llm(historial: list | None) -> list[dict]:
    """Recorte seguro del historial enviado a Ollama."""
    if not historial:
        return []
    saneado: list[dict] = []
    for item in historial[-MAX_HISTORIAL_LLM:]:
        if not isinstance(item, dict):
            continue
        role = item.get('role')
        content = item.get('content')
        if role not in ('user', 'assistant') or not isinstance(content, str):
            continue
        limpio = texto_para_llm(content)
        if not limpio:
            continue
        saneado.append({'role': role, 'content': limpio})
    return saneado


def _rate_limit_config(scope: str) -> tuple[int, int]:
    defaults = {
        'chat': (30, 60),
        'catalogo': (60, 60),
        'metadata': (120, 60),
    }
    cfg = getattr(settings, 'HARDWAREHOUSE_CHAT_RATE_LIMIT', None) or {}
    if isinstance(cfg, dict) and scope in cfg:
        item = cfg[scope]
        if isinstance(item, dict):
            return int(item.get('requests', defaults.get(scope, (30, 60))[0])), int(
                item.get('window_seconds', defaults.get(scope, (30, 60))[1])
            )
    return defaults.get(scope, (30, 60))


def cliente_ip(request: HttpRequest) -> str:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or 'unknown'


def verificar_rate_limit(request: HttpRequest, scope: str) -> JsonResponse | None:
    limite, ventana = _rate_limit_config(scope)
    if limite <= 0:
        return None
    clave = f'hw_chat_rl:{scope}:{cliente_ip(request)}'
    actual = cache.get(clave, 0)
    if actual >= limite:
        return JsonResponse(
            {'error': 'Demasiadas solicitudes. Espera un momento e intenta de nuevo.'},
            status=429,
        )
    if actual == 0:
        cache.set(clave, 1, ventana)
    else:
        cache.incr(clave)
    return None


def validar_payload_chat(payload: dict) -> tuple[str | None, list | None, JsonResponse | None]:
    mensaje = (payload.get('message') or '').strip()
    if not mensaje:
        return None, None, JsonResponse({'error': 'El mensaje está vacío.'}, status=400)
    if len(mensaje) > MAX_MENSAJE:
        return None, None, JsonResponse(
            {'error': 'El mensaje es demasiado largo.'},
            status=400,
        )

    historial = payload.get('history')
    if historial is None:
        return mensaje, None, None
    if not isinstance(historial, list):
        return mensaje, None, None
    if len(historial) > MAX_HISTORIAL_ITEMS:
        historial = historial[-MAX_HISTORIAL_ITEMS:]
    saneado = []
    for item in historial:
        if not isinstance(item, dict):
            continue
        role = item.get('role')
        content = item.get('content')
        if role not in ('user', 'assistant') or not isinstance(content, str):
            continue
        saneado.append(
            {'role': role, 'content': content[:MAX_HISTORIAL_ITEM_CHARS]}
        )
    return mensaje, saneado or None, None


def validar_builder_componentes(payload: dict) -> list[dict] | None:
    raw = payload.get('builder_componentes')
    if raw is None:
        return None
    if not isinstance(raw, list):
        return None
    from core.armado_servicio import sanitizar_lista_componentes

    items = sanitizar_lista_componentes(raw)
    return items or None


def validar_build_context(payload: dict) -> dict | None:
    raw = payload.get('build_context')
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return None
    from core.armado_servicio import sanitizar_lista_componentes

    limpio: dict = {}
    if 'presupuesto_original_clp' in raw:
        try:
            limpio['presupuesto_original_clp'] = max(0, min(int(raw['presupuesto_original_clp']), 50_000_000))
        except (TypeError, ValueError):
            pass
    if 'presupuesto_clp' in raw:
        try:
            limpio['presupuesto_clp'] = max(0, min(int(raw['presupuesto_clp']), 50_000_000))
        except (TypeError, ValueError):
            pass
    if isinstance(raw.get('proposito'), str):
        p = raw['proposito'].strip().lower()
        if p in ('gaming', 'office', 'editing', 'general'):
            limpio['proposito'] = p
    if isinstance(raw.get('preferencia_cpu'), str):
        b = raw['preferencia_cpu'].strip().lower()
        if b in ('amd', 'intel'):
            limpio['preferencia_cpu'] = b
    try:
        limpio['indice_economico'] = max(0, min(int(raw.get('indice_economico', 0)), 10))
    except (TypeError, ValueError):
        limpio['indice_economico'] = 0
    if isinstance(raw.get('componentes'), list):
        limpio['componentes'] = sanitizar_lista_componentes(raw['componentes'])
    if isinstance(raw.get('snapshot'), list):
        fotos = []
        for item in raw['snapshot'][:12]:
            if not isinstance(item, dict):
                continue
            try:
                fotos.append(
                    {
                        'tipo': str(item.get('tipo') or '')[:40],
                        'id': int(item.get('id')),
                        'cantidad': max(1, min(int(item.get('cantidad') or 1), 99)),
                        'precio_clp': max(0, int(item.get('precio_clp') or 0)),
                        'nombre': str(item.get('nombre') or '')[:120],
                    }
                )
            except (TypeError, ValueError):
                continue
        if fotos:
            limpio['snapshot'] = fotos
    pending = raw.get('pending_action')
    if isinstance(pending, dict) and isinstance(pending.get('id'), str):
        accion = {
            'id': pending['id'][:64],
            'tipo': str(pending.get('tipo') or '')[:40],
            'categoria': str(pending.get('categoria') or '')[:40],
            'resumen': str(pending.get('resumen') or '')[:500],
        }
        if isinstance(pending.get('componentes'), list):
            accion['componentes'] = sanitizar_lista_componentes(pending['componentes'])
        if accion.get('componentes'):
            limpio['pending_action'] = accion
    intent_previo = raw.get('ultimo_intent')
    if isinstance(intent_previo, str):
        from core.chatbot.conversation_state import INTENTS_PUBLICOS

        intent_limpio = intent_previo.strip().lower()[:40]
        if intent_limpio in INTENTS_PUBLICOS:
            limpio['ultimo_intent'] = intent_limpio
    if 'total_clp' in raw:
        try:
            limpio['total_clp'] = int(raw['total_clp'])
        except (TypeError, ValueError):
            pass
    return limpio or None


def cargar_json(request: HttpRequest) -> tuple[dict | None, JsonResponse | None]:
    if request.content_type and 'application/json' not in request.content_type:
        return None, JsonResponse({'error': 'Content-Type debe ser application/json.'}, status=415)
    try:
        body = request.body.decode('utf-8') or '{}'
        if len(body) > 500_000:
            return None, JsonResponse({'error': 'Cuerpo de solicitud demasiado grande.'}, status=413)
        return json.loads(body), None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({'error': 'JSON no válido.'}, status=400)


def chat_api_protegida(scope: str = 'chat') -> Callable:
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped(request: HttpRequest, *args, **kwargs):
            bloqueo = verificar_rate_limit(request, scope)
            if bloqueo:
                return bloqueo
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
