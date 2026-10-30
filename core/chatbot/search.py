"""Búsqueda y filtrado de catálogo vía ORM."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

from django.db.models import Q

from core.catalogo.registry import CATALOGO_MODELOS, categorias_disponibles
from core.chatbot.ranking import puntuar_producto
from core.chatbot.serializers import producto_a_dict
from core.models import Proveedor

OrdenCatalogo = Literal['relevancia', 'precio_asc', 'precio_desc', 'stock_desc']


@dataclass
class FiltrosCatalogo:
    q: str = ''
    categoria: str | None = None
    marca: str | None = None
    proveedor_id: int | None = None
    precio_min: int | None = None
    precio_max: int | None = None
    solo_con_stock: bool = False
    modelos: list[str] | None = None
    limit: int = 20
    orden: OrdenCatalogo = 'relevancia'

    @classmethod
    def desde_dict(cls, data: dict) -> 'FiltrosCatalogo':
        limit = int(data.get('limit') or 20)
        limit = max(1, min(limit, 50))
        orden = data.get('orden') or 'relevancia'
        if orden not in ('relevancia', 'precio_asc', 'precio_desc', 'stock_desc'):
            orden = 'relevancia'
        proveedor_id = data.get('proveedor_id')
        if proveedor_id is not None:
            proveedor_id = int(proveedor_id)
        precio_min = _entero_opcional(data.get('precio_min'))
        precio_max = _entero_opcional(data.get('precio_max'))
        modelos = data.get('modelos')
        if modelos is not None and not isinstance(modelos, list):
            modelos = None
        return cls(
            q=(data.get('q') or '').strip(),
            categoria=_vacio_a_none(data.get('categoria')),
            marca=_vacio_a_none(data.get('marca')),
            proveedor_id=proveedor_id,
            precio_min=precio_min,
            precio_max=precio_max,
            solo_con_stock=bool(data.get('solo_con_stock')),
            modelos=modelos,
            limit=limit,
            orden=orden,
        )


def _vacio_a_none(valor):
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _entero_opcional(valor) -> int | None:
    if valor is None or valor == '':
        return None
    try:
        entero = int(Decimal(str(valor)))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return max(0, entero)


def _filtros_sin_texto(filtros: FiltrosCatalogo, marca_nombre: str | None) -> bool:
    return bool(
        filtros.categoria
        or filtros.proveedor_id
        or marca_nombre
        or filtros.precio_min is not None
        or filtros.precio_max is not None
        or filtros.solo_con_stock
        or filtros.modelos
    )


def _resolver_marca(marca: str | None, proveedor_id: int | None) -> str | None:
    if proveedor_id is not None:
        nombre = Proveedor.objects.filter(pk=proveedor_id).values_list('nombre', flat=True).first()
        return nombre
    return marca


def buscar_catalogo(filtros: FiltrosCatalogo) -> dict:
    marca_nombre = _resolver_marca(filtros.marca, filtros.proveedor_id)
    if filtros.categoria and filtros.categoria not in categorias_disponibles():
        return {
            'count': 0,
            'results': [],
            'filtros': _filtros_respuesta(filtros, marca_nombre),
            'error': 'La categoría indicada no existe en el catálogo.',
        }

    candidatos: list[tuple[object, str, float]] = []

    for modelo, model_name in CATALOGO_MODELOS:
        if filtros.modelos and model_name not in filtros.modelos:
            continue
        categoria_modelo = modelo._meta.get_field('categoria').default
        if filtros.categoria and categoria_modelo != filtros.categoria:
            continue

        qs = modelo.objects.select_related('proveedor').all()

        if filtros.q:
            qs = qs.filter(
                Q(nombre__icontains=filtros.q)
                | Q(proveedor__nombre__icontains=filtros.q)
                | Q(descripcion__icontains=filtros.q)
                | Q(categoria__icontains=filtros.q)
            )
        if filtros.proveedor_id is not None:
            qs = qs.filter(proveedor_id=filtros.proveedor_id)
        elif marca_nombre:
            qs = qs.filter(proveedor__nombre__iexact=marca_nombre)
        if filtros.precio_min is not None:
            qs = qs.filter(precio__gte=filtros.precio_min)
        if filtros.precio_max is not None:
            qs = qs.filter(precio__lte=filtros.precio_max)
        if filtros.solo_con_stock:
            qs = qs.filter(stock__gt=0)

        for producto in qs[:200]:
            score = puntuar_producto(
                producto,
                filtros.q,
                categoria_filtro=filtros.categoria,
                marca_filtro=marca_nombre,
            )
            if filtros.q and score <= 0 and not _filtros_sin_texto(filtros, marca_nombre):
                continue
            candidatos.append((producto, model_name, score))

    candidatos = _ordenar(candidatos, filtros.orden)
    recorte = candidatos[: filtros.limit]
    resultados = [
        producto_a_dict(producto, model_name, score=score)
        for producto, model_name, score in recorte
    ]
    return {
        'count': len(resultados),
        'total_coincidencias': len(candidatos),
        'results': resultados,
        'filtros': _filtros_respuesta(filtros, marca_nombre),
    }


def _ordenar(
    candidatos: list[tuple[object, str, float]],
    orden: OrdenCatalogo,
) -> list[tuple[object, str, float]]:
    if orden == 'precio_asc':
        return sorted(candidatos, key=lambda t: (t[0].precio, -t[2]))
    if orden == 'precio_desc':
        return sorted(candidatos, key=lambda t: (-t[0].precio, -t[2]))
    if orden == 'stock_desc':
        return sorted(candidatos, key=lambda t: (t[0].stock, -t[2]), reverse=True)
    return sorted(candidatos, key=lambda t: (-t[2], t[0].precio))


def _filtros_respuesta(filtros: FiltrosCatalogo, marca_nombre: str | None) -> dict:
    return {
        'q': filtros.q,
        'categoria': filtros.categoria,
        'marca': marca_nombre or filtros.marca,
        'proveedor_id': filtros.proveedor_id,
        'precio_min': filtros.precio_min,
        'precio_max': filtros.precio_max,
        'solo_con_stock': filtros.solo_con_stock,
        'orden': filtros.orden,
        'limit': filtros.limit,
    }
