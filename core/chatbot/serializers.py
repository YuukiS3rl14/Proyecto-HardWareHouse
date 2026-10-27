"""Serialización de instancias ORM a JSON (sin inventar datos)."""
from __future__ import annotations

from decimal import Decimal

from django.urls import reverse

from core.catalogo.registry import model_name_for
from core.demo_catalog import nombre_comercial
from core.excel_armado import especificaciones_de


def precio_a_entero(precio) -> int:
    return int(Decimal(precio).to_integral_value())


def especificaciones_producto(producto) -> list[dict[str, str | int | float | bool]]:
    if producto._meta.model_name == 'ventilador':
        return [
            {'etiqueta': 'Tamaño (mm)', 'valor': producto.tamanho_mm},
            {'etiqueta': 'Velocidad (RPM)', 'valor': producto.velocidad_rpm},
            {'etiqueta': 'RGB', 'valor': producto.rgb},
        ]
    return [
        {'etiqueta': etiqueta, 'valor': valor}
        for etiqueta, valor in especificaciones_de(producto)
    ]


def producto_a_dict(producto, model_name: str | None = None, score: float | None = None) -> dict:
    model_name = model_name or model_name_for(producto.__class__)
    marca = producto.proveedor.nombre
    payload = {
        'id': f'{model_name}:{producto.pk}',
        'modelo': model_name,
        'producto_pk': producto.pk,
        'categoria': producto.categoria,
        'marca': marca,
        'nombre': producto.nombre,
        'nombre_completo': nombre_comercial(marca, producto.nombre),
        'descripcion': (producto.descripcion or '').strip(),
        'precio_clp': precio_a_entero(producto.precio),
        'stock': producto.stock,
        'disponible': producto.stock > 0,
        'especificaciones': especificaciones_producto(producto),
        'url_detalle': reverse(
            'core:detalle',
            kwargs={'model_name': model_name, 'pk': producto.pk},
        ),
    }
    if score is not None:
        payload['score'] = round(score, 4)
    return payload
