"""Respuestas de chat para armado de PC (ORM + reglas de compatibilidad)."""
from __future__ import annotations

from django.urls import reverse

from core.armado_recomendacion import ResultadoArmadoAutomatico, construir_armado_automatico
from core.armado_servicio import crear_propuesta_pendiente_armado
from core.chatbot.nlp_armado import SolicitudArmadoNL, parsear_solicitud_armado
from core.chatbot.serializers import producto_a_dict
from core.models import (
    AlmacenamientoHDD,
    AlmacenamientoSSD,
    FuenteDePoder,
    Gabinete,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    RefrigeracionCooler,
    TarjetaGrafica,
)

_MODELO_POR_TIPO = {
    'procesador': Procesador,
    'placa_madre': PlacaMadre,
    'memoria_ram': MemoriaRam,
    'tarjeta_grafica': TarjetaGrafica,
    'almacenamiento_ssd': AlmacenamientoSSD,
    'almacenamiento_hdd': AlmacenamientoHDD,
    'gabinete': Gabinete,
    'refrigeracion': RefrigeracionCooler,
    'fuente_de_poder': FuenteDePoder,
}


def _formato_clp(valor: int) -> str:
    return f'${valor:,}'.replace(',', '.')


def _cargar_productos_armado(resultado: ResultadoArmadoAutomatico) -> list[dict]:
    items = []
    for comp in resultado.componentes:
        tipo = comp['tipo']
        modelo = _MODELO_POR_TIPO.get(tipo)
        if modelo is None:
            continue
        producto = modelo.objects.filter(pk=comp['id']).select_related('proveedor').first()
        if producto is None:
            continue
        items.append(producto_a_dict(producto, tipo))
    return items


def ejecutar_armado_chat(
    texto: str,
    build_context: dict | None = None,
    presupuesto_llm: int | None = None,
    proposito_llm: str | None = None,
) -> dict:
    solicitud = parsear_solicitud_armado(texto, build_context, extraido_budget=presupuesto_llm)
    if proposito_llm and solicitud.proposito == 'general':
        if proposito_llm in ('gaming', 'office', 'editing', 'general'):
            solicitud.proposito = proposito_llm

    if solicitud.presupuesto_clp is None:
        return {
            'intent': 'pc_build',
            'response_type': 'clarification',
            'reply': (
                'Para recomendarte un armado con piezas reales del catálogo, indica tu presupuesto en CLP '
                '(por ejemplo: 700 lucas o presupuesto hasta 800000). También puedes decir si es para gaming, '
                'oficina o edición.'
            ),
        }

    resultado = construir_armado_automatico(
        solicitud.presupuesto_clp,
        proposito=solicitud.proposito,
        preferencia_cpu=solicitud.preferencia_cpu,
        indice_economico=solicitud.indice_economico,
    )

    if not resultado.ok:
        lineas = [
            'No pude armar un PC compatible dentro de esas condiciones.',
            resultado.motivo_fallo or 'Revisa el presupuesto o las preferencias.',
        ]
        if resultado.tradeoffs:
            lineas.extend(resultado.tradeoffs)
        lineas.append(
            f'Puedes afinar piezas manualmente en {reverse("core:armado")} o escribirnos por '
            f'{reverse("core:contacto")}.'
        )
        return {
            'intent': 'pc_build',
            'response_type': 'pc_build_failed',
            'reply': '\n'.join(lineas),
            'armado': {'ok': False, 'motivo': resultado.motivo_fallo},
            'armado_context': resultado.armado_context() if resultado.componentes else None,
        }

    productos = _cargar_productos_armado(resultado)
    lineas = [
        f'Armado sugerido ({solicitud.proposito}) — total {_formato_clp(resultado.total_clp)} CLP '
        f'(presupuesto {_formato_clp(resultado.presupuesto_clp)} CLP). Datos del catálogo con stock verificado:',
    ]
    for p in productos:
        lineas.append(
            f'• {p["nombre_completo"]} ({p["categoria"]}) — {_formato_clp(p["precio_clp"])} CLP, '
            f'stock {p["stock"]}. Ver: {p["url_detalle"]}'
        )
    if resultado.tradeoffs:
        lineas.append('Notas: ' + '; '.join(resultado.tradeoffs))
    if resultado.advertencias:
        lineas.append('Advertencias de compatibilidad: ' + '; '.join(resultado.advertencias[:3]))
    lineas.append(
        f'Revisa y ajusta el armado en {reverse("core:armado")}. '
        'No agregué nada al carrito; tú decides cuándo comprar.'
    )

    ctx = resultado.armado_context()
    ctx['preferencia_cpu'] = solicitud.preferencia_cpu
    ctx['indice_economico'] = solicitud.indice_economico

    propuesta = crear_propuesta_pendiente_armado(
        ctx['componentes'] if 'componentes' in ctx else resultado.componentes,
        meta={'proposito': solicitud.proposito, 'presupuesto_clp': resultado.presupuesto_clp},
    )

    return {
        'intent': 'pc_build',
        'response_type': 'pc_build',
        'reply': '\n'.join(lineas),
        'proposal_pending': propuesta,
        'armado': {
            'ok': True,
            'total_clp': resultado.total_clp,
            'presupuesto_clp': resultado.presupuesto_clp,
            'proposito': solicitud.proposito,
            'evaluacion': resultado.evaluacion_estado,
            'productos': productos,
        },
        'armado_context': ctx,
    }
