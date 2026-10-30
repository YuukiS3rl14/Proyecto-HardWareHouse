"""Consultas de presupuesto sobre el catálogo (ORM)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

from core.catalogo.registry import CATALOGO_MODELOS, categorias_disponibles
from core.chatbot.search import FiltrosCatalogo, buscar_catalogo
from core.chatbot.serializers import precio_a_entero, producto_a_dict

ModoPresupuesto = Literal['mejor_por_precio', 'mas_economico']


@dataclass
class ConsultaPresupuesto:
    presupuesto_max: int
    categorias: list[str] | None = None
    solo_con_stock: bool = True
    limit_por_categoria: int = 3
    modo: ModoPresupuesto = 'mejor_por_precio'

    @classmethod
    def desde_dict(cls, data: dict) -> 'ConsultaPresupuesto | None':
        maximo = data.get('presupuesto_max')
        if maximo is None:
            return None
        try:
            presupuesto = int(Decimal(str(maximo)))
        except (InvalidOperation, ValueError, TypeError):
            return None
        if presupuesto < 0:
            return None
        categorias = data.get('categorias')
        if categorias is not None and not isinstance(categorias, list):
            categorias = None
        if categorias:
            validas = set(categorias_disponibles())
            categorias = [c for c in categorias if c in validas]
        limit = int(data.get('limit_por_categoria') or 3)
        limit = max(1, min(limit, 10))
        modo = data.get('modo') or 'mejor_por_precio'
        if modo not in ('mejor_por_precio', 'mas_economico'):
            modo = 'mejor_por_precio'
        return cls(
            presupuesto_max=presupuesto,
            categorias=categorias or None,
            solo_con_stock=bool(data.get('solo_con_stock', True)),
            limit_por_categoria=limit,
            modo=modo,
        )


def buscar_por_presupuesto(consulta: ConsultaPresupuesto) -> dict:
    categorias = consulta.categorias or categorias_disponibles()
    orden = 'precio_desc' if consulta.modo == 'mejor_por_precio' else 'precio_asc'
    bloques: list[dict] = []
    total_estimado_min = 0

    for categoria in categorias:
        resultado = buscar_catalogo(
            FiltrosCatalogo(
                categoria=categoria,
                precio_max=consulta.presupuesto_max,
                solo_con_stock=consulta.solo_con_stock,
                limit=consulta.limit_por_categoria,
                orden=orden,
            )
        )
        productos = resultado['results']
        if not productos:
            bloques.append(
                {
                    'categoria': categoria,
                    'count': 0,
                    'productos': [],
                    'nota': 'No hay productos en esta categoría dentro del presupuesto.',
                }
            )
            continue
        bloques.append(
            {
                'categoria': categoria,
                'count': len(productos),
                'productos': productos,
            }
        )
        if consulta.modo == 'mas_economico' and productos:
            total_estimado_min += productos[0]['precio_clp']

    return {
        'presupuesto_max': consulta.presupuesto_max,
        'modo': consulta.modo,
        'categorias_consultadas': categorias,
        'total_referencia_economico': total_estimado_min if consulta.modo == 'mas_economico' else None,
        'bloques': bloques,
    }


def presupuesto_armado_simple(items: list[dict]) -> dict:
    """
    Suma precios de productos ya elegidos (modelo + producto_pk).
    Solo datos ORM; ignora ítems desconocidos.
    """
    from core.catalogo.registry import MODEL_BY_API_NAME

    detalle = []
    total = 0
    for item in items:
        model_name = item.get('modelo')
        pk = item.get('producto_pk')
        if not model_name or pk is None:
            continue
        modelo = MODEL_BY_API_NAME.get(model_name)
        if modelo is None:
            continue
        producto = modelo.objects.select_related('proveedor').filter(pk=pk).first()
        if producto is None:
            continue
        precio = precio_a_entero(producto.precio)
        total += precio
        detalle.append(producto_a_dict(producto, model_name))

    return {
        'items': detalle,
        'total_clp': total,
        'count': len(detalle),
    }
