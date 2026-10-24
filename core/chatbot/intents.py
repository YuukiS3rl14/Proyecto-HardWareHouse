"""Detección de intención por reglas configurables (motor local)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from django.conf import settings

from core.chatbot.catalog_nl import extraer_consulta_catalogo
from core.chatbot.nlp import termino_busqueda_especifico
from core.chatbot.texto import normalizar_texto


class Intent(str, Enum):
    SALUDO = 'saludo'
    DESPACHO = 'despacho'
    RETIRO = 'retiro'
    UBICACION_HORARIO = 'ubicacion_horario'
    ARMADO = 'armado'
    PAGO = 'pago'
    COMPRA = 'compra'
    CONTACTO = 'contacto'
    EMPRESA = 'empresa'
    STOCK = 'stock'
    GARANTIA = 'garantia'
    PRESUPUESTO = 'presupuesto'
    MIS_PEDIDOS = 'mis_pedidos'
    BUSCAR_PRODUCTO = 'buscar_producto'
    DESCONOCIDO = 'desconocido'


@dataclass(frozen=True)
class ReglaIntent:
    intent: Intent
    patrones: tuple[str, ...]
    prioridad: int = 50
    max_longitud: int | None = None

    def coincide(self, texto: str, bajo: str) -> bool:
        if self.max_longitud is not None and len(texto) > self.max_longitud:
            return False
        norm = normalizar_texto(bajo)
        return any(re.search(p, norm, re.I) for p in self.patrones)


def _reglas_por_defecto() -> tuple[ReglaIntent, ...]:
    return (
        ReglaIntent(
            Intent.SALUDO,
            (r'\b(hola|buenas|buenos dias|buenas tardes|buenas noches|hey|hi)\b',),
            prioridad=10,
            max_longitud=40,
        ),
        ReglaIntent(
            Intent.MIS_PEDIDOS,
            (
                r'\b(mis pedidos|mi pedido|estado de (mi|el) pedido|seguimiento)\b',
                r'\b(ultimo pedido|último pedido|historial de compras)\b',
            ),
            prioridad=12,
        ),
        ReglaIntent(
            Intent.DESPACHO,
            (
                r'\b(envio|envios|envío|envíos|despacho|delivery|deliveries|deliveris|'
                r'courier|domicilio|shipping|envian|envían|mandan a casa)\b',
            ),
            18,
        ),
        ReglaIntent(
            Intent.RETIRO,
            (
                r'\b(retiro en tienda|retirar en tienda|pickup|recoger en tienda|'
                r'pasar a buscar|retiro local)\b',
            ),
            19,
        ),
        ReglaIntent(
            Intent.UBICACION_HORARIO,
            (
                r'\b(ubicacion|ubicación|direccion|dirección|donde estan|dónde están|'
                r'donde quedan|local|sucursal)\b',
            ),
            22,
        ),
        ReglaIntent(Intent.UBICACION_HORARIO, (r'\b(horario|hora|abierto|atienden)\b',), 22),
        ReglaIntent(
            Intent.ARMADO,
            (r'\b(armado|armar pc|compatibilidad|compatibles|builder)\b',),
            28,
        ),
        ReglaIntent(Intent.PAGO, (r'\b(pago|paypal|pagar|checkout|metodos de pago)\b',), 28),
        ReglaIntent(
            Intent.COMPRA,
            (r'\b(como compro|cómo compro|comprar en la web|carrito|finalizar compra)\b',),
            32,
        ),
        ReglaIntent(Intent.CONTACTO, (r'\b(contacto|correo|email|telefono|teléfono|whatsapp)\b',), 34),
        ReglaIntent(
            Intent.EMPRESA,
            (
                r'\b(mision|misión|vision|visión|valores|historia|servicios|quienes son|quiénes son|'
                r'quienes somos|sobre nosotros|sobre la tienda|acerca de la tienda|'
                r'que es hardwarehouse|años|antiguedad|antigüedad)\b',
            ),
            34,
        ),
        ReglaIntent(Intent.GARANTIA, (r'\b(garantia|garantía|devolucion|devolución|cambio)\b',), 36),
        ReglaIntent(
            Intent.STOCK,
            (r'\b(stock|disponible|agotado)\b',),
            42,
        ),
    )


def _cargar_reglas_extra() -> tuple[ReglaIntent, ...]:
    raw = getattr(settings, 'HARDWAREHOUSE_CHAT_INTENT_RULES', None) or []
    if not isinstance(raw, list):
        return ()
    reglas: list[ReglaIntent] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        nombre = item.get('intent')
        try:
            intent = Intent(nombre)
        except (ValueError, TypeError):
            continue
        patrones = item.get('patrones') or item.get('patterns')
        if not patrones:
            continue
        reglas.append(
            ReglaIntent(
                intent=intent,
                patrones=tuple(str(p) for p in patrones),
                prioridad=int(item.get('prioridad', 50)),
                max_longitud=item.get('max_longitud'),
            )
        )
    return tuple(reglas)


_VERBO_BUSQUEDA = re.compile(
    r'\b(busco|buscar|b[uú]squeda|precio de|cuesta|cuanto cuesta|cuánto cuesta|'
    r'tienen|hay stock|stock de|mu[eé]strame|me muestras)\b',
    re.I,
)
_MODELO_PRODUCTO = re.compile(
    r'\b(?=[a-z0-9-]*\d)(?=[a-z0-9-]*[a-z])[a-z0-9][a-z0-9-]{2,}\b',
    re.I,
)


def _consulta_catalogo_prevalece(texto: str) -> bool:
    consulta = extraer_consulta_catalogo(texto)
    return consulta.requiere_orm_estructurado()


def _busqueda_producto_explicita(texto: str) -> bool:
    if _VERBO_BUSQUEDA.search(texto or '') and termino_busqueda_especifico(texto):
        return True
    return bool(_MODELO_PRODUCTO.search(texto or ''))


def detectar_intent(texto: str, presupuesto_clp: int | None = None) -> Intent:
    limpio = (texto or '').strip()
    if not limpio:
        return Intent.DESCONOCIDO

    if presupuesto_clp is not None:
        return Intent.PRESUPUESTO

    consulta_cat = extraer_consulta_catalogo(limpio)
    bajo = limpio.lower()
    reglas = sorted(
        (*_reglas_por_defecto(), *_cargar_reglas_extra()),
        key=lambda r: r.prioridad,
    )
    for regla in reglas:
        if not regla.coincide(limpio, bajo):
            continue
        if regla.intent == Intent.STOCK and _consulta_catalogo_prevalece(limpio):
            continue
        if regla.intent == Intent.COMPRA and consulta_cat.categoria:
            continue
        return regla.intent

    if _consulta_catalogo_prevalece(limpio) or _busqueda_producto_explicita(limpio):
        return Intent.BUSCAR_PRODUCTO
    return Intent.DESCONOCIDO
