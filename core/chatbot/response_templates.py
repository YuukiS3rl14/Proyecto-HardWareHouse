"""Plantillas en español (fuente de verdad cuando no hay redacción LLM)."""
from __future__ import annotations

from django.urls import reverse

from core.chatbot.assistant_config import AsistenteConfig, get_asistente_config
from core.chatbot.response_sanitize import sanitizar_dato_catalogo
from core.chatbot.response_types import (
    BUDGET,
    CLARIFICATION,
    FAQ,
    GENERIC,
    GREETING,
    OFF_TOPIC,
    ORDER_LOGIN,
    ORDER_STATUS,
    PRODUCT_NOT_FOUND,
    PRODUCT_RESULTS,
)


def _path(name: str) -> str:
    return reverse(name)


def plantilla_producto_no_encontrado(config: AsistenteConfig | None = None) -> str:
    config = config or get_asistente_config()
    return f'{config.mensaje_sin_resultados_catalogo} {_path("core:tienda")}.'


def plantilla_fuera_de_tema(config: AsistenteConfig | None = None) -> str:
    config = config or get_asistente_config()
    return (
        f'{config.mensaje_fuera_de_alcance} '
        f'Si necesitas ayuda humana, escríbenos en {_path("core:contacto")}.'
    )


def plantilla_aclaracion(
    interpretacion: str | None = None,
    config: AsistenteConfig | None = None,
    sugerencia: str | None = None,
) -> str:
    config = config or get_asistente_config()
    pista = interpretacion or sugerencia or 'un producto del catálogo, un armado de PC o una duda de la tienda'
    return f'No entendí bien, ¿quisiste decir {pista}?'


def plantilla_saludo(config: AsistenteConfig | None = None) -> str:
    return (config or get_asistente_config()).mensaje_bienvenida


def plantilla_faq(texto_verificado: str) -> str:
    return sanitizar_dato_catalogo(texto_verificado)


def plantilla_productos_desde_lineas(lineas: list[str]) -> str:
    """Solo líneas generadas desde ORM (handlers)."""
    return '\n'.join(lineas)


def renderizar(
    tipo: str,
    *,
    config: AsistenteConfig | None = None,
    faq_texto: str | None = None,
    producto_lineas: list[str] | None = None,
    interpretacion: str | None = None,
    sugerencia: str | None = None,
    pedidos_texto: str | None = None,
    presupuesto_texto: str | None = None,
    generico: str | None = None,
) -> str:
    config = config or get_asistente_config()

    if tipo == PRODUCT_NOT_FOUND:
        return plantilla_producto_no_encontrado(config)
    if tipo == OFF_TOPIC:
        return plantilla_fuera_de_tema(config)
    if tipo == CLARIFICATION:
        return plantilla_aclaracion(interpretacion, config, sugerencia=sugerencia)
    if tipo == GREETING:
        return plantilla_saludo(config)
    if tipo == FAQ and faq_texto:
        return plantilla_faq(faq_texto)
    if tipo == PRODUCT_RESULTS and producto_lineas:
        return plantilla_productos_desde_lineas(producto_lineas)
    if tipo == ORDER_STATUS and pedidos_texto:
        return pedidos_texto
    if tipo == ORDER_LOGIN and pedidos_texto:
        return pedidos_texto
    if tipo == BUDGET and presupuesto_texto:
        return presupuesto_texto
    if generico:
        return generico
    return config.mensaje_sin_informacion
