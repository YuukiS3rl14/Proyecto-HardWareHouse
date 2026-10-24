"""
Preguntas frecuentes compartidas: chatbot y página Sobre nosotros.
"""
from __future__ import annotations

from django.urls import reverse


def _p(name: str) -> str:
    return reverse(name)


def _faq_entries() -> dict[str, tuple[str, str]]:
    return {
        'ubicacion_horario': (
            '¿Dónde están ubicados?',
            (
                'Nuestro punto de referencia para retiro en tienda es '
                'Av. Tecnología 123, Santiago, Región Metropolitana (ejemplo del sitio). '
                'Te confirmamos horario al coordinar tu pedido. '
                f'Escríbenos en {_p("core:contacto")}.'
            ),
        ),
        'despacho': (
            '¿Realizan despachos o envíos a domicilio?',
            (
                'No. HardWareHouse no ofrece despacho, delivery ni envíos a domicilio. '
                'La entrega es solo mediante retiro en tienda una vez confirmado el pago. '
                'Los datos de región y comuna en el checkout son para el pedido, no implican envío. '
                f'Más información en {_p("core:sobrenosotros")}.'
            ),
        ),
        'retiro': (
            '¿Cómo funciona el retiro en tienda?',
            (
                'Solo entregamos con retiro en tienda tras confirmar el pago con PayPal. '
                'No hay despacho a domicilio. Coordinamos día y hora al confirmar tu compra.'
            ),
        ),
        'compra': (
            '¿Cómo compro en la web?',
            (
                f'Explora {_p("core:tienda")}, agrega al carrito e inicia sesión. '
                'En el checkout completas tus datos y pagas con PayPal. '
                'Cuando el pago queda confirmado, coordinamos el retiro en tienda.'
            ),
        ),
        'armado': (
            '¿Qué es el armado de PC en HardWareHouse?',
            (
                f'En {_p("core:armado")} eliges componentes paso a paso y revisas compatibilidad '
                '(socket, RAM, gabinete, fuente, etc.) antes de agregar al carrito o exportar un presupuesto.'
            ),
        ),
        'stock': (
            '¿El stock de la web es en tiempo real?',
            (
                'Mostramos el stock del catálogo en cada ficha. Si un producto se agota durante la compra, '
                'te avisamos al confirmar el pedido. Ante dudas, escríbenos antes de pagar.'
            ),
        ),
        'pago': (
            '¿Qué métodos de pago aceptan?',
            (
                'Las compras en línea se procesan con PayPal. '
                'El pago debe quedar confirmado antes de preparar tu pedido para retiro en tienda.'
            ),
        ),
        'contacto': (
            '¿Puedo recibir ayuda para elegir componentes?',
            (
                f'Sí. Usa el armador de PC y el formulario de {_p("core:contacto")}. '
                'Te orientamos con criterio técnico, sin presión de venta.'
            ),
        ),
        'empresa': (
            '¿Quiénes son?',
            (
                'HardWareHouse es una pyme con cinco años en el mercado chileno, especializada en '
                'componentes de PC y armado de computadores a medida. '
                f'Conoce más en {_p("core:sobrenosotros")}.'
            ),
        ),
        'garantia': (
            'Garantías y devoluciones',
            (
                'Para garantías o cambios, contáctanos con tu número de pedido y el detalle del producto. '
                f'Revisa {_p("core:sobrenosotros")} o {_p("core:contacto")}.'
            ),
        ),
    }


def faq_respuesta_chat(clave: str) -> str | None:
    par = _faq_entries().get(clave)
    return par[1] if par else None


def faq_items_acordeon() -> list[dict]:
    orden = [
        'ubicacion_horario',
        'despacho',
        'retiro',
        'compra',
        'armado',
        'stock',
        'pago',
        'contacto',
    ]
    entries = _faq_entries()
    items = []
    for clave in orden:
        if clave not in entries:
            continue
        titulo, respuesta = entries[clave]
        items.append({'clave': clave, 'titulo': titulo, 'respuesta': respuesta})
    return items
