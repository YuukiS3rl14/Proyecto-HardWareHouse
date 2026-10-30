"""Ajustes de un armado ya propuesto, usando el catálogo y la compatibilidad existentes.

No escribe carrito ni stock. El cambio queda pendiente hasta que el usuario confirme.
"""
from __future__ import annotations

import re
import secrets
from decimal import Decimal

from core.armado_recomendacion import candidatos_para_categoria
from core.armado_servicio import (
    _clave_exclusion_categoria,
    _total_clp,
    analizar_armado,
    cargar_seleccion_items,
    fusionar_componentes_activos,
    productos_catalogo_desde_componentes,
)
from core.chatbot.fallbacks import MISSING_BUILD, etiquetar
from core.chatbot.nlp import normalizar_presupuesto_clp
from core.compatibilidad import ESTADO_DATOS_INSUFICIENTES, ESTADO_INCOMPATIBLE
from core.views import _UI_POR_TIPO

_RESTO = re.compile(
    r'\b(restante|lo que queda|lo que sobra|sobra|usa el resto|usar el resto|el resto|'
    r'use the remaining|use the rest|with the remaining|con lo que queda)\b',
    re.I,
)
_BAJAR_PRECIO = re.compile(
    r'\b(reduce the price|baja(?:r|le)? el precio|reduce el precio|bajale el precio|b[aá]jale el precio)\b',
    re.I,
)
_MEJORAR_REFERENCIA = re.compile(
    r'\b(improve it|improve that|mej[oó]ralo|mejorarlo|mejora eso|mejora ese|mejorar eso|mejorar ese)\b',
    re.I,
)
_REFERENCIA_SOLA = re.compile(
    r'^(?:y\s+|sobre\s+)?(?:ese|esa|aquel|aquella|that|the)\s+'
    r'(?:pc|armado|build|computador|computadora)\s*[?.!]*$',
    re.I,
)
_NUEVO_ARMADO = re.compile(
    r'\b(armame|ármame|armar(?:\s+un)?\s+pc|arma(?:me)?\s+un\s+pc|montar(?:\s+un)?\s+pc|montame)\b',
    re.I,
)
_MAS_BARATO = re.compile(
    r'\b(m[aá]s barat\w*|m[aá]s econ[oó]mic\w*|make it cheaper|cheaper|downgrade)\b',
    re.I,
)
_GAMING = re.compile(
    r'\b(prioriz\w*\s+(?:el\s+)?(?:gaming|juegos)|prioritize gaming|enfoc\w*\s+en\s+juegos)\b',
    re.I,
)
_MEJORAR = re.compile(
    r'\b(qu[eé] podemos mejorar|que se puede mejorar|what can we improve|'
    r'oportunidades de mejora|qu[eé] mejorar)\b',
    re.I,
)
_SUBIR_PIEZA = re.compile(
    r'\b(upgrade|mejora(?:r)?|mejor(?:ar)?|sube|subir|m[aá]s potent\w*)\b',
    re.I,
)
_ORDEN_MEJORA = {
    'gaming': ('tarjeta_grafica', 'procesador'),
    'editing': ('procesador', 'tarjeta_grafica', 'memoria_ram'),
    'office': ('procesador', 'memoria_ram'),
    'general': ('tarjeta_grafica', 'procesador'),
}
_ESENCIALES = {
    'gaming': {'tarjeta_grafica', 'procesador'},
    'editing': {'procesador', 'memoria_ram'},
    'office': {'procesador', 'memoria_ram'},
    'general': {'procesador'},
}
_ESTADOS_RECHAZADOS = {ESTADO_INCOMPATIBLE, ESTADO_DATOS_INSUFICIENTES}


def menciona_resto(texto: str) -> bool:
    return bool(_RESTO.search(texto or ''))


def detectar_optimizacion(texto: str) -> dict | None:
    from core.armado_servicio import detectar_categoria_armado

    fuente = texto or ''
    if not fuente.strip() or _NUEVO_ARMADO.search(fuente):
        return None
    if _MEJORAR.search(fuente):
        return {'modo': 'opportunities', 'categoria': None, 'monto_restante': None}
    if _REFERENCIA_SOLA.search(fuente):
        return {'modo': 'clarify_reference', 'categoria': None, 'monto_restante': None}
    if menciona_resto(fuente):
        return {
            'modo': 'spend_remaining',
            'categoria': None,
            'monto_restante': normalizar_presupuesto_clp(fuente),
        }
    if _GAMING.search(fuente):
        return {'modo': 'gaming', 'categoria': None, 'monto_restante': None}
    if _MEJORAR_REFERENCIA.search(fuente):
        return {'modo': 'spend_remaining', 'categoria': None, 'monto_restante': None}
    if _BAJAR_PRECIO.search(fuente) or (_MAS_BARATO.search(fuente) and not detectar_categoria_armado(fuente)):
        return {'modo': 'cheaper', 'categoria': None, 'monto_restante': None}
    if _SUBIR_PIEZA.search(fuente):
        categoria = detectar_categoria_armado(fuente)
        if categoria:
            return {'modo': 'upgrade_part', 'categoria': categoria, 'monto_restante': None}
    return None


def responder_sin_armado(build_context: dict | None = None, modo: str = '') -> dict:
    """Seguimiento que nombra un PC que esta conversación todavía no tiene."""
    previo = ''
    if isinstance(build_context, dict):
        previo = str(build_context.get('ultimo_intent') or '')
    if modo == 'cheaper' and previo == 'product_search':
        return {
            'intent': 'clarification',
            'response_type': 'clarification',
            'necesita_clarificacion': True,
            'fallback_reason': 'needs_clarification',
            'motor': 'reglas',
            'reply': (
                '¿El más barato de qué categoría? Puedo buscar CPU, GPU, RAM u otra pieza del catálogo.'
            ),
        }
    return etiquetar(
        {
            'intent': 'clarification',
            'response_type': 'clarification',
            'necesita_clarificacion': True,
            'motor': 'reglas',
        },
        MISSING_BUILD,
    )


def _puntaje(producto, categoria: str) -> float:
    if producto is None:
        return 0.0
    if categoria == 'tarjeta_grafica':
        return float(getattr(producto, 'vram_gb', 0) or 0)
    if categoria == 'procesador':
        nucleos = float(getattr(producto, 'nucleos', 0) or 0)
        frecuencia = float(getattr(producto, 'frecuencia_base', 0) or 0)
        return nucleos * (frecuencia or 1.0)
    if categoria in ('memoria_ram', 'almacenamiento'):
        return float(getattr(producto, 'capacidad_gb', 0) or 0)
    if categoria == 'fuente_de_poder':
        return float(getattr(producto, 'potencia_watts', 0) or 0)
    return 0.0


def _precio_entero(valor) -> int:
    if isinstance(valor, Decimal):
        return int(valor)
    return int(valor or 0)


def _pieza_de_categoria(items: list[dict], categoria: str) -> dict | None:
    for item in items:
        if _UI_POR_TIPO.get(item.get('tipo')) == categoria:
            return item
    return None


def _producto_actual(seleccion: dict, almacenamientos: list, categoria: str):
    clave = _clave_exclusion_categoria(categoria)
    if clave and clave in seleccion:
        return seleccion[clave]
    if categoria == 'almacenamiento' and almacenamientos:
        return almacenamientos[0]['producto']
    return None


def _snapshot(items: list[dict]) -> list[dict]:
    cantidades = {(item['tipo'], item['id']): int(item.get('cantidad') or 1) for item in items}
    filas = []
    for producto in productos_catalogo_desde_componentes(items):
        tipo = producto.get('modelo')
        pk = producto.get('producto_pk')
        filas.append(
            {
                'tipo': tipo,
                'id': pk,
                'cantidad': cantidades.get((tipo, pk), 1),
                'precio_clp': producto.get('precio_clp'),
                'nombre': producto.get('nombre_completo') or producto.get('nombre'),
            }
        )
    return filas


def _techo(build_context: dict, total: int, pedido: dict) -> int:
    original = build_context.get('presupuesto_original_clp') or build_context.get('presupuesto_clp')
    try:
        original = int(original) if original else None
    except (TypeError, ValueError):
        original = None
    nombrado = pedido.get('monto_restante')
    if pedido['modo'] == 'cheaper':
        return original or total
    if nombrado:
        techo = total + int(nombrado)
        if original:
            techo = min(techo, original)
        return techo
    if original:
        return original
    return total


def _candidatos(items: list[dict], categoria: str) -> tuple[list[dict], object | None, int]:
    completo, error = cargar_seleccion_items(items)
    if completo is None:
        return [], None, 0
    seleccion, almacenamientos, memorias = completo
    total = _total_clp(seleccion, almacenamientos, memorias)
    actual = _producto_actual(seleccion, almacenamientos, categoria)
    excluir = _clave_exclusion_categoria(categoria)
    parcial, error_parcial = cargar_seleccion_items(items, excluir_clave=excluir)
    if parcial is None:
        return [], actual, total
    seleccion_sin, _, memorias_sin = parcial
    return candidatos_para_categoria(categoria, seleccion_sin, memorias_sin or None), actual, total


def _opciones(items: list[dict], categoria: str, *, techo: int, total: int, modo: str, proposito: str) -> list[dict]:
    candidatos, actual, _ = _candidatos(items, categoria)
    if actual is None:
        return []
    pieza = _pieza_de_categoria(items, categoria) or {}
    cantidad = int(pieza.get('cantidad') or 1)
    precio_actual = _precio_entero(actual.precio) * cantidad
    puntaje_actual = _puntaje(actual, categoria)
    esenciales = _ESENCIALES.get(proposito, _ESENCIALES['general'])
    piso = 0.85 if categoria in esenciales else 0.70
    opciones = []
    for candidato in candidatos:
        if int(candidato.get('stock') or 0) < cantidad:
            continue
        if candidato.get('estado') in _ESTADOS_RECHAZADOS:
            continue
        if candidato.get('id') == actual.pk:
            continue
        precio = _precio_entero(candidato.get('precio')) * cantidad
        nuevo_total = total - precio_actual + precio
        if nuevo_total > techo:
            continue
        puntaje = _puntaje(candidato.get('producto'), categoria)
        if modo == 'cheaper':
            if precio >= precio_actual:
                continue
            if puntaje_actual and puntaje < puntaje_actual * piso:
                continue
        else:
            if precio <= precio_actual:
                continue
            if puntaje_actual and puntaje < puntaje_actual * 1.15:
                continue
        diferencia = precio - precio_actual
        ratio = 0.0
        if modo == 'cheaper':
            ratio = (precio_actual - precio) / max(puntaje_actual or 1, 1)
        elif diferencia > 0 and puntaje > puntaje_actual:
            ratio = (puntaje - puntaje_actual) / diferencia
        opciones.append(
            {
                'candidato': candidato,
                'cantidad': cantidad,
                'precio_actual': precio_actual,
                'precio_nuevo': precio,
                'puntaje_actual': puntaje_actual,
                'puntaje_nuevo': puntaje,
                'diferencia': diferencia,
                'ratio': ratio,
                'nuevo_total': nuevo_total,
                'nombre_actual': getattr(actual, 'nombre', ''),
                'id_actual': actual.pk,
                'tipo_actual': pieza.get('tipo'),
            }
        )
    if modo == 'cheaper':
        opciones.sort(key=lambda item: (-(item['precio_actual'] - item['precio_nuevo']), -item['ratio']))
    else:
        opciones.sort(key=lambda item: (-item['ratio'], item['diferencia']))
    return opciones


def _armar_cambio(items: list[dict], categoria: str, opcion: dict) -> tuple[list[dict], dict]:
    cantidad = opcion['cantidad']
    candidato = opcion['candidato']
    nuevos = [item for item in items if _UI_POR_TIPO.get(item.get('tipo')) != categoria]
    nuevos.append(
        {
            'tipo': candidato.get('model_name'),
            'id': candidato['id'],
            'cantidad': cantidad,
        }
    )
    return nuevos, analizar_armado(nuevos)


def _motivo(categoria: str, opcion: dict, modo: str) -> str:
    antes = opcion['puntaje_actual']
    despues = opcion['puntaje_nuevo']
    if modo == 'cheaper':
        return (
            f'{categoria}: baja el precio manteniendo la función esencial '
            f'({antes:g} → {despues:g} según la ficha del catálogo).'
        )
    return (
        f'{categoria}: mejora de rendimiento por peso '
        f'({antes:g} → {despues:g}) sin pasar el presupuesto original.'
    )


def _comparacion(antes_total: int, techo: int, analisis: dict, categoria: str, opcion: dict, modo: str, advertencias: list) -> dict:
    despues_total = int(analisis.get('total_clp') or opcion['nuevo_total'])
    diferencia = despues_total - antes_total
    candidato = opcion['candidato']
    return {
        'antes': {
            'total_clp': antes_total,
            'presupuesto_clp': techo,
            'restante_clp': max(techo - antes_total, 0),
        },
        'despues': {
            'total_clp': despues_total,
            'restante_clp': max(techo - despues_total, 0),
        },
        'reemplazos': [
            {
                'categoria': categoria,
                'antes': {
                    'id': opcion['id_actual'],
                    'tipo': opcion['tipo_actual'],
                    'nombre': opcion['nombre_actual'],
                    'precio_clp': opcion['precio_actual'],
                    'cantidad': opcion['cantidad'],
                },
                'despues': {
                    'id': candidato.get('id'),
                    'tipo': candidato.get('model_name'),
                    'nombre': candidato.get('nombre'),
                    'precio_clp': opcion['precio_nuevo'],
                    'cantidad': opcion['cantidad'],
                    'stock': candidato.get('stock'),
                },
                'diferencia_clp': opcion['diferencia'],
                'motivo': _motivo(categoria, opcion, modo),
            }
        ],
        'ahorro_clp': max(-diferencia, 0),
        'costo_adicional_clp': max(diferencia, 0),
        'advertencias': list(advertencias or []),
        'razones': [_motivo(categoria, opcion, modo)],
    }


def _texto(comparacion: dict, *, confirmar: bool) -> str:
    antes = comparacion['antes']
    despues = comparacion['despues']
    lineas = [
        f'Comparación del armado: total ${antes["total_clp"]:,} → ${despues["total_clp"]:,} CLP.'.replace(',', '.'),
        (
            f'Presupuesto original ${antes["presupuesto_clp"]:,} CLP. '
            f'Quedarían ${despues["restante_clp"]:,} CLP.'
        ).replace(',', '.'),
    ]
    if comparacion['ahorro_clp']:
        lineas.append(f'Ahorro: ${comparacion["ahorro_clp"]:,} CLP.'.replace(',', '.'))
    if comparacion['costo_adicional_clp']:
        lineas.append(f'Costo adicional: ${comparacion["costo_adicional_clp"]:,} CLP.'.replace(',', '.'))
    for cambio in comparacion['reemplazos']:
        previo = cambio['antes']
        nuevo = cambio['despues']
        lineas.append(
            f'• {cambio["categoria"]}: {previo["nombre"]} (${previo["precio_clp"]:,}) → '
            f'{nuevo["nombre"]} (${nuevo["precio_clp"]:,}). {cambio["motivo"]}'.replace(',', '.')
        )
    if comparacion['advertencias']:
        lineas.append('Advertencias: ' + '; '.join(comparacion['advertencias'][:3]))
    if confirmar:
        lineas.append('Es una propuesta. Responde "sí, confirmar" para aplicarla en el armador. No toca el carrito.')
    return '\n'.join(lineas)


def _categorias(pedido: dict, proposito: str) -> list[str]:
    if pedido.get('categoria'):
        return [pedido['categoria']]
    if pedido['modo'] == 'cheaper':
        return ['tarjeta_grafica', 'procesador', 'memoria_ram', 'almacenamiento', 'fuente_de_poder', 'gabinete', 'refrigeracion_cooler']
    if pedido['modo'] == 'gaming':
        return ['tarjeta_grafica', 'procesador']
    return list(_ORDEN_MEJORA.get(proposito, _ORDEN_MEJORA['general']))


def optimizar_armado_chat(
    texto: str,
    build_context: dict | None = None,
    builder_componentes: list | None = None,
) -> dict:
    pedido = detectar_optimizacion(texto) or {'modo': 'opportunities', 'categoria': None, 'monto_restante': None}
    ctx = dict(build_context or {})
    items = fusionar_componentes_activos(ctx, builder_componentes)
    if not items:
        return responder_sin_armado(ctx, pedido.get('modo') or '')

    if pedido.get('modo') == 'clarify_reference':
        return {
            'intent': 'clarification',
            'response_type': 'clarification',
            'necesita_clarificacion': True,
            'fallback_reason': 'needs_clarification',
            'reply': (
                'Tengo ese PC en la conversación. ¿Quieres bajarle el precio, usar el resto del presupuesto '
                'o ver qué se puede mejorar?'
            ),
            'armado_context': ctx,
        }

    completo, error = cargar_seleccion_items(items)
    if completo is None:
        return {
            'intent': 'build_upgrade',
            'response_type': 'clarification',
            'reply': error or 'No pude leer las piezas del armado actual.',
        }
    seleccion, almacenamientos, memorias = completo
    total = _total_clp(seleccion, almacenamientos, memorias)
    proposito = str(ctx.get('proposito') or 'general')
    if pedido['modo'] == 'gaming':
        proposito = 'gaming'
    techo = _techo(ctx, total, pedido)
    if pedido['modo'] != 'cheaper' and techo <= total and pedido['modo'] != 'opportunities':
        return {
            'intent': 'build_upgrade',
            'response_type': 'clarification',
            'reply': (
                f'El armado ya usa ${total:,} CLP y el presupuesto original es ${techo:,} CLP. '
                'No queda margen para una mejora.'.replace(',', '.')
            ),
            'armado_context': ctx,
        }

    modo_busqueda = 'cheaper' if pedido['modo'] == 'cheaper' else 'upgrade'
    encontradas = []
    for categoria in _categorias(pedido, proposito):
        for opcion in _opciones(items, categoria, techo=techo, total=total, modo=modo_busqueda, proposito=proposito):
            nuevos, analisis = _armar_cambio(items, categoria, opcion)
            if not analisis.get('ok') or analisis.get('estado') in _ESTADOS_RECHAZADOS:
                continue
            if int(analisis.get('total_clp') or 0) > techo:
                continue
            encontradas.append((categoria, opcion, nuevos, analisis))
            break
    if pedido['modo'] == 'cheaper':
        encontradas.sort(key=lambda fila: fila[1]['precio_actual'] - fila[1]['precio_nuevo'], reverse=True)
    elif pedido['modo'] != 'opportunities':
        encontradas.sort(key=lambda fila: (-fila[1]['ratio'], fila[1]['diferencia']))

    if not encontradas:
        return {
            'intent': 'build_downgrade' if pedido['modo'] == 'cheaper' else 'build_upgrade',
            'response_type': 'clarification',
            'reply': (
                'No hay un cambio compatible, con stock y dentro del presupuesto '
                'que mejore el rendimiento por peso sin gastar de más o sin perder la función esencial.'
            ),
            'armado_context': {
                **ctx,
                'componentes': items,
                'total_clp': total,
                'proposito': proposito,
                'presupuesto_clp': ctx.get('presupuesto_clp') or techo,
                'presupuesto_original_clp': ctx.get('presupuesto_original_clp') or techo,
                'snapshot': _snapshot(items),
            },
        }

    if pedido['modo'] == 'opportunities':
        razones = []
        for categoria, opcion, _, analisis in encontradas[:3]:
            extra = int(analisis.get('total_clp') or 0) - total
            razones.append(
                f'{categoria}: {opcion["candidato"].get("nombre")} '
                f'(+${extra:,} CLP, queda dentro de ${techo:,}).'.replace(',', '.')
            )
        return {
            'intent': 'pc_build_analyze',
            'response_type': 'build_analysis',
            'reply': 'Mejoras posibles con el catálogo actual, sin aplicarlas todavía:\n' + '\n'.join(f'• {r}' for r in razones),
            'build_comparison': {
                'antes': {'total_clp': total, 'presupuesto_clp': techo, 'restante_clp': max(techo - total, 0)},
                'despues': None,
                'reemplazos': [],
                'oportunidades': razones,
                'ahorro_clp': 0,
                'costo_adicional_clp': 0,
                'advertencias': [],
                'razones': razones,
            },
            'armado_context': {
                **ctx,
                'componentes': items,
                'total_clp': total,
                'proposito': proposito,
                'presupuesto_original_clp': ctx.get('presupuesto_original_clp') or techo,
                'snapshot': _snapshot(items),
            },
        }

    categoria, opcion, nuevos, analisis = encontradas[0]
    comparacion = _comparacion(
        total,
        techo,
        analisis,
        categoria,
        opcion,
        modo_busqueda,
        analisis.get('advertencias') or [],
    )
    intent = 'build_downgrade' if modo_busqueda == 'cheaper' else 'build_upgrade'
    pending = {
        'id': secrets.token_urlsafe(12),
        'tipo': 'optimizar_armado',
        'categoria': categoria,
        'componentes': nuevos,
        'resumen': comparacion['razones'][0][:500],
    }
    nuevo_ctx = {
        **ctx,
        'componentes': items,
        'total_clp': total,
        'proposito': proposito,
        'presupuesto_clp': ctx.get('presupuesto_clp') or techo,
        'presupuesto_original_clp': ctx.get('presupuesto_original_clp') or techo,
        'snapshot': _snapshot(items),
        'pending_action': pending,
    }
    return {
        'intent': intent,
        'response_type': 'build_pending_change',
        'reply': _texto(comparacion, confirmar=True),
        'build_comparison': comparacion,
        'armado_context': nuevo_ctx,
        'pending_build_action': pending,
        'armado': {
            'ok': True,
            'total_clp': total,
            'presupuesto_clp': nuevo_ctx['presupuesto_original_clp'],
            'advertencias': comparacion['advertencias'],
            'evaluacion': analisis.get('estado'),
        },
    }
