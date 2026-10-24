"""Manejadores por intención (catálogo ORM + FAQ)."""
from __future__ import annotations

from django.urls import reverse

from core.chatbot.assistant_config import AsistenteConfig, get_asistente_config
from core.chatbot.budget import ConsultaPresupuesto, buscar_por_presupuesto
from core.chatbot.catalog_nl import ConsultaCatalogoNL, extraer_consulta_catalogo
from core.chatbot.faq_rules import obtener_faq
from core.chatbot.intents import Intent
from core.chatbot.nlp import extraer_termino_busqueda, termino_busqueda_especifico
from core.chatbot.private_data import respuesta_mis_pedidos
from core.chatbot.search import FiltrosCatalogo, buscar_catalogo


def _path(name: str, **kwargs) -> str:
    if kwargs:
        return reverse(name, kwargs=kwargs)
    return reverse(name)


def _formato_clp(valor: int) -> str:
    return f'${valor:,}'.replace(',', '.')


def _linea_producto(item: dict) -> str:
    specs = item.get('especificaciones') or []
    spec_txt = ''
    if specs:
        primera = specs[0]
        spec_txt = f' | {primera["etiqueta"]}: {primera["valor"]}'
    return (
        f'• {item["nombre_completo"]} ({item["categoria"]}) — '
        f'{_formato_clp(item["precio_clp"])} CLP, stock {item["stock"]}{spec_txt}. '
        f'Ver: {item["url_detalle"]}'
    )


def _texto_desde_resultados(
    resultado: dict,
    config: AsistenteConfig,
    consulta: ConsultaCatalogoNL | None = None,
) -> str:
    productos = resultado.get('results') or []
    if not productos:
        return f'{config.mensaje_sin_resultados_catalogo} {_path("core:tienda")}.'

    consulta = consulta or ConsultaCatalogoNL()
    if consulta.orden == 'precio_asc' and consulta.categoria and len(productos) == 1:
        item = productos[0]
        return (
            f'La opción más económica en {consulta.categoria} con stock disponible:\n'
            f'{_linea_producto(item)}'
        )
    if consulta.orden == 'precio_desc' and consulta.categoria and len(productos) == 1:
        item = productos[0]
        return (
            f'La opción de mayor precio en {consulta.categoria} en catálogo:\n'
            f'{_linea_producto(item)}'
        )

    lineas = ['Esto hay en el catálogo (datos en tiempo real):']
    for item in productos[:6]:
        lineas.append(_linea_producto(item))
    if resultado.get('total_coincidencias', 0) > len(productos):
        lineas.append(f'Hay más resultados en {_path("core:tienda")}.')
    return '\n'.join(lineas)


def manejar_presupuesto(presupuesto_clp: int) -> dict:
    consulta = ConsultaPresupuesto(
        presupuesto_max=presupuesto_clp,
        solo_con_stock=True,
        limit_por_categoria=2,
    )
    data = buscar_por_presupuesto(consulta)
    lineas = [f'Opciones hasta {_formato_clp(presupuesto_clp)} CLP por categoría (catálogo real):']
    for bloque in data['bloques']:
        if not bloque.get('productos'):
            lineas.append(f'— {bloque["categoria"]}: sin coincidencias.')
            continue
        for p in bloque['productos'][:2]:
            lineas.append(
                f'— {p["categoria"]}: {p["nombre_completo"]} '
                f'({_formato_clp(p["precio_clp"])} CLP, stock {p["stock"]})'
            )
    return {'reply': '\n'.join(lineas), 'presupuesto': data}


def manejar_buscar_producto(
    texto: str,
    config: AsistenteConfig | None = None,
    consulta_nl: ConsultaCatalogoNL | None = None,
) -> dict:
    config = config or get_asistente_config()
    consulta = consulta_nl or extraer_consulta_catalogo(texto)

    if consulta.requiere_orm_estructurado():
        limit = 1 if consulta.orden in ('precio_asc', 'precio_desc') and consulta.categoria else 6
        catalogo = buscar_catalogo(consulta.a_filtros(limit=limit))
    else:
        if not termino_busqueda_especifico(texto):
            return {
                'intent': 'clarification',
                'necesita_clarificacion': True,
                'motor': 'reglas',
            }
        termino = extraer_termino_busqueda(texto)
        catalogo = buscar_catalogo(
            FiltrosCatalogo(q=termino, limit=6, solo_con_stock=False, orden='relevancia')
        )

    if catalogo['count'] > 0:
        return {
            'reply': _texto_desde_resultados(catalogo, config, consulta),
            'catalogo': catalogo,
            'busqueda_catalogo': True,
            'consulta': {
                'categoria': consulta.categoria,
                'orden': consulta.orden,
                'solo_con_stock': consulta.solo_con_stock,
            },
        }
    return {
        'reply': (
            f'{config.mensaje_sin_resultados_catalogo} {_path("core:tienda")}.'
        ),
        'catalogo': catalogo,
        'busqueda_catalogo': True,
    }


_FAQ_MAP = {
    Intent.DESPACHO: 'despacho',
    Intent.RETIRO: 'retiro',
    Intent.UBICACION_HORARIO: 'ubicacion_horario',
    Intent.ARMADO: 'armado',
    Intent.PAGO: 'pago',
    Intent.COMPRA: 'compra',
    Intent.CONTACTO: 'contacto',
    Intent.EMPRESA: 'empresa',
    Intent.STOCK: 'stock',
    Intent.GARANTIA: 'garantia',
}


def manejar_faq(intent: Intent) -> dict | None:
    clave = _FAQ_MAP.get(intent)
    if not clave:
        return None
    texto = obtener_faq(clave)
    if not texto:
        return None
    return {'reply': texto}


def manejar_intent(
    intent: Intent,
    texto: str,
    presupuesto_clp: int | None,
    usuario=None,
    config: AsistenteConfig | None = None,
    consulta_nl: ConsultaCatalogoNL | None = None,
) -> dict:
    config = config or get_asistente_config()
    consulta_nl = consulta_nl or extraer_consulta_catalogo(texto)

    if intent == Intent.SALUDO:
        return {'reply': config.mensaje_bienvenida}

    if intent == Intent.PRESUPUESTO and presupuesto_clp is not None:
        return manejar_presupuesto(presupuesto_clp)

    if intent == Intent.MIS_PEDIDOS:
        resultado = respuesta_mis_pedidos(usuario)
        resultado['intent'] = intent.value
        return resultado

    if intent == Intent.STOCK:
        termino = extraer_termino_busqueda(texto)
        if len(termino) >= 3:
            out = manejar_buscar_producto(texto, config, consulta_nl=consulta_nl)
            if out.get('catalogo', {}).get('count', 0) > 0:
                out['intent'] = intent.value
                return out

    faq = manejar_faq(intent)
    if faq:
        faq['intent'] = intent.value
        return faq

    if intent == Intent.BUSCAR_PRODUCTO:
        out = manejar_buscar_producto(texto, config, consulta_nl=consulta_nl)
        out['intent'] = intent.value
        return out

    return {
        'reply': (
            f'{config.mensaje_sin_informacion} '
            f'Tienda: {_path("core:tienda")} · Armado: {_path("core:armado")} · '
            f'Contacto: {_path("core:contacto")}.'
        ),
        'intent': Intent.DESCONOCIDO.value,
    }
