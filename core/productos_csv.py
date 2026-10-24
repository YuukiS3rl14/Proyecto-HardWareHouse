"""Exportación CSV del catálogo de componentes (p. ej. base de conocimiento de un asistente)."""
from __future__ import annotations

import csv
import io
from decimal import Decimal

from django.conf import settings
from django.urls import reverse

from core.catalogo.registry import CATALOGO_MODELOS

from .excel_armado import especificaciones_de

CSV_COLUMNS = (
    'id',
    'modelo',
    'categoria',
    'marca',
    'nombre',
    'descripcion',
    'precio_clp',
    'stock',
    'especificaciones',
    'url_detalle',
    'titulo',
    'contenido',
)


def _especificaciones_texto(producto) -> str:
    if producto._meta.model_name == 'ventilador':
        partes = [
            f'Tamaño (mm): {producto.tamanho_mm}',
            f'Velocidad (RPM): {producto.velocidad_rpm}',
            f'RGB: {"Sí" if producto.rgb else "No"}',
        ]
        return '; '.join(partes)
    return '; '.join(f'{etiqueta}: {valor}' for etiqueta, valor in especificaciones_de(producto))


def _precio_entero(precio) -> int:
    monto = Decimal(precio)
    return int(monto.to_integral_value())


def _url_detalle(model_name: str, pk: int) -> str:
    base = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')
    path = reverse('core:detalle', kwargs={'model_name': model_name, 'pk': pk})
    return f'{base}{path}'


def _contenido_fila(row: dict) -> str:
    lineas = [
        f"Producto: {row['marca']} {row['nombre']}",
        f"Categoría: {row['categoria']}",
        f"ID interno: {row['id']}",
        f"Precio (CLP): {row['precio_clp']}",
        f"Stock disponible: {row['stock']}",
    ]
    if row['descripcion']:
        lineas.append(f"Descripción: {row['descripcion']}")
    if row['especificaciones']:
        lineas.append(f"Especificaciones: {row['especificaciones']}")
    lineas.append(f"Más información: {row['url_detalle']}")
    return '\n'.join(lineas)


def iter_filas_producto():
    for modelo, model_name in CATALOGO_MODELOS:
        for producto in modelo.objects.select_related('proveedor').order_by('id'):
            marca = producto.proveedor.nombre
            descripcion = (producto.descripcion or '').strip()
            specs = _especificaciones_texto(producto)
            fila = {
                'id': f'{model_name}:{producto.pk}',
                'modelo': model_name,
                'categoria': producto.categoria,
                'marca': marca,
                'nombre': producto.nombre,
                'descripcion': descripcion,
                'precio_clp': _precio_entero(producto.precio),
                'stock': producto.stock,
                'especificaciones': specs,
                'url_detalle': _url_detalle(model_name, producto.pk),
                'titulo': f'{marca} {producto.nombre} ({producto.categoria})',
                'contenido': '',
            }
            fila['contenido'] = _contenido_fila(fila)
            yield fila


def generar_csv_bytes() -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction='ignore')
    writer.writeheader()
    for fila in iter_filas_producto():
        writer.writerow(fila)
    return buffer.getvalue().encode('utf-8-sig')
