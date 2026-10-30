"""Payload estructurado para el widget de chat (productos, pedidos)."""
from __future__ import annotations

from django.urls import reverse

from core.chatbot.response_types import (
    BUDGET,
    ORDER_LOGIN,
    ORDER_STATUS,
    PRODUCT_NOT_FOUND,
    PRODUCT_RESULTS,
)


def _productos_desde_presupuesto(presupuesto_data: dict) -> list[dict]:
    items: list[dict] = []
    for bloque in presupuesto_data.get('bloques') or []:
        for producto in bloque.get('productos') or []:
            items.append(producto)
    return items


def construir_ui_payload(resultado: dict, response_type: str) -> dict:
    ui: dict = {'kind': response_type}

    if response_type == PRODUCT_RESULTS:
        catalogo = resultado.get('catalogo') or {}
        productos = catalogo.get('results') or []
        if productos:
            ui['kind'] = 'products'
            ui['products'] = productos
            ui['total'] = catalogo.get('count', len(productos))
            consulta = resultado.get('consulta') or {}
            if consulta.get('categoria'):
                ui['categoria'] = consulta['categoria']
        return ui

    if response_type == PRODUCT_NOT_FOUND:
        ui['kind'] = 'products_empty'
        return ui

    if response_type == ORDER_STATUS:
        pedidos = resultado.get('pedidos') or []
        ui['kind'] = 'orders'
        ui['orders'] = pedidos
        ui['orders_url'] = reverse('core:mis_pedidos')
        return ui

    if response_type == ORDER_LOGIN:
        ui['kind'] = 'orders_login'
        ui['login_url'] = reverse('core:login')
        ui['orders_url'] = reverse('core:mis_pedidos')
        return ui

    if response_type == BUDGET:
        pres = resultado.get('presupuesto') or {}
        productos = _productos_desde_presupuesto(pres)
        if productos:
            ui['kind'] = 'products'
            ui['products'] = productos
            ui['presupuesto_max'] = pres.get('presupuesto_max')
        return ui

    if response_type in ('pc_build', 'build_analysis', 'build_applied'):
        armado = resultado.get('armado') or {}
        productos = armado.get('productos') or []
        if productos:
            ui['kind'] = 'products'
            ui['products'] = productos
            ui['warnings'] = list(armado.get('advertencias') or [])
            ui['armado'] = {
                'total_clp': armado.get('total_clp'),
                'presupuesto_clp': armado.get('presupuesto_clp'),
                'estado': armado.get('estado') or armado.get('evaluacion'),
            }
            if response_type == 'pc_build' and resultado.get('proposal_pending'):
                ui['apply_build'] = True
                ui['apply_path'] = reverse('core:armado') + '?aplicar=1'
        return ui

    return ui


def adjuntar_ui_al_resultado(resultado: dict, response_type: str) -> dict:
    ui = construir_ui_payload(resultado, response_type)
    if ui.get('kind') and ui.get('kind') != response_type:
        resultado['ui'] = ui
    elif ui.get('kind') in ('products_empty', 'orders_login'):
        resultado['ui'] = ui
    elif ui.get('products') or ui.get('orders'):
        resultado['ui'] = ui
    return resultado
