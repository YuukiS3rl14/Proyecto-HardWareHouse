"""Memoria de la última búsqueda de catálogo dentro de la misma conversación."""
from __future__ import annotations

import re

from core.catalogo.registry import MODEL_BY_API_NAME, categorias_disponibles
from core.chatbot.catalog_nl import ConsultaCatalogoNL, extraer_consulta_catalogo
from core.chatbot.texto import normalizar_texto

_REFERENCIA = re.compile(
    r'\b(?:cual|cuales)\s+de\s+(?:esas|esos|estas|estos)\b'
    r'|\b(?:entre|de)\s+(?:esas|esos|estas|estos)\b',
    re.I,
)
_MAX_PRODUCTOS = 12
_CATEGORIAS = frozenset(categorias_disponibles())
_MODELOS = frozenset(MODEL_BY_API_NAME)


def _norm(texto: str) -> str:
    return normalizar_texto(texto or '')


def sanear_busqueda_catalogo(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    categoria = raw.get('categoria')
    if categoria is not None:
        categoria = str(categoria).strip()
        if categoria not in _CATEGORIAS:
            categoria = None
    productos = []
    vistos = set()
    for item in raw.get('productos') or []:
        if not isinstance(item, dict):
            continue
        modelo = str(item.get('modelo') or '').strip()
        if modelo not in _MODELOS:
            continue
        try:
            pk = int(item.get('id'))
        except (TypeError, ValueError):
            continue
        if pk <= 0 or (modelo, pk) in vistos:
            continue
        vistos.add((modelo, pk))
        productos.append({'modelo': modelo, 'id': pk})
        if len(productos) >= _MAX_PRODUCTOS:
            break
    if not productos:
        return None

    def _monto(clave):
        valor = raw.get(clave)
        if valor is None or valor == '':
            return None
        try:
            return max(0, min(int(valor), 50_000_000))
        except (TypeError, ValueError):
            return None

    orden = str(raw.get('orden') or 'relevancia')
    if orden not in ('relevancia', 'precio_asc', 'precio_desc', 'stock_desc'):
        orden = 'relevancia'
    return {
        'categoria': categoria,
        'precio_min': _monto('precio_min'),
        'precio_max': _monto('precio_max'),
        'solo_con_stock': bool(raw.get('solo_con_stock')),
        'orden': orden,
        'productos': productos,
    }


def snapshot_busqueda(resultado: dict) -> dict | None:
    catalogo = resultado.get('catalogo') if isinstance(resultado.get('catalogo'), dict) else {}
    filas = catalogo.get('results') or []
    if not filas:
        return None
    filtros = catalogo.get('filtros') if isinstance(catalogo.get('filtros'), dict) else {}
    consulta = resultado.get('consulta') if isinstance(resultado.get('consulta'), dict) else {}
    return sanear_busqueda_catalogo(
        {
            'categoria': consulta.get('categoria') or filtros.get('categoria'),
            'precio_min': filtros.get('precio_min'),
            'precio_max': filtros.get('precio_max'),
            'solo_con_stock': filtros.get('solo_con_stock'),
            'orden': consulta.get('orden') or filtros.get('orden') or 'relevancia',
            'productos': [
                {'modelo': item.get('modelo'), 'id': item.get('producto_pk')}
                for item in filas
                if isinstance(item, dict)
            ],
        }
    )


def _pide_recorte(texto: str, consulta: ConsultaCatalogoNL) -> bool:
    if consulta.categoria:
        return False
    if consulta.orden in ('precio_asc', 'precio_desc'):
        return True
    return bool(_REFERENCIA.search(_norm(texto)))


def responder_seguimiento_catalogo(texto: str, build_context: dict | None) -> dict | None:
    consulta = extraer_consulta_catalogo(texto)
    if not _pide_recorte(texto, consulta):
        return None
    guardado = sanear_busqueda_catalogo((build_context or {}).get('catalogo_busqueda'))
    if guardado is None:
        return {
            'intent': 'clarification',
            'necesita_clarificacion': True,
            'motor': 'reglas',
            'reply': '¿De qué categoría quieres que compare? Puedo usar la lista anterior si me muestras productos primero.',
        }
    pks: dict[str, list[int]] = {}
    for item in guardado['productos']:
        pks.setdefault(item['modelo'], []).append(item['id'])
    orden = consulta.orden if consulta.orden != 'relevancia' else 'precio_asc'
    acotada = ConsultaCatalogoNL(
        categoria=guardado.get('categoria'),
        orden=orden,
        precio_min=consulta.precio_min if consulta.precio_min is not None else guardado.get('precio_min'),
        precio_max=consulta.precio_max if consulta.precio_max is not None else guardado.get('precio_max'),
        solo_con_stock=bool(guardado.get('solo_con_stock') or consulta.solo_con_stock or orden == 'precio_asc'),
        pks_por_modelo=pks,
    )
    from core.chatbot.handlers import manejar_buscar_producto

    out = manejar_buscar_producto(texto, consulta_nl=acotada)
    out['conservar_busqueda'] = True
    out['intent'] = 'buscar_producto'
    return out
