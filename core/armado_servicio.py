"""
Servicios de armado PC reutilizados por el armador web y el chatbot.

No modifica carrito ni stock; solo lectura ORM y reglas de compatibilidad.
"""
from __future__ import annotations

import json
import secrets
from datetime import timedelta
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from django.urls import reverse

from core.armado_recomendacion import candidatos_para_categoria
from core.compatibilidad import (
    MENSAJE_ALMACENAMIENTO,
    ESTADO_NO_EVALUADA,
    EvaluacionCandidato,
    evaluaciones_de_seleccion,
    texto_del_armado,
)
from core.views import (
    PRODUCT_MODEL_MAP,
    _UI_POR_TIPO,
    _cargar_seleccion,
    _serializar_evaluacion,
)

_TIPOS_VALIDOS = frozenset(PRODUCT_MODEL_MAP.keys())
_MAX_ITEMS = 24

_CATEGORIA_UI_POR_TEXTO: dict[str, str] = {
    'gpu': 'tarjeta_grafica',
    'grafica': 'tarjeta_grafica',
    'tarjeta': 'tarjeta_grafica',
    'cpu': 'procesador',
    'procesador': 'procesador',
    'placa': 'placa_madre',
    'motherboard': 'placa_madre',
    'ram': 'memoria_ram',
    'memoria': 'memoria_ram',
    'fuente': 'fuente_de_poder',
    'psu': 'fuente_de_poder',
    'gabinete': 'gabinete',
    'case': 'gabinete',
    'cooler': 'refrigeracion_cooler',
    'refrigeracion': 'refrigeracion_cooler',
    'graphics': 'tarjeta_grafica',
    'ssd': 'almacenamiento',
    'hdd': 'almacenamiento',
    'disco': 'almacenamiento',
    'almacenamiento': 'almacenamiento',
}


def sanitizar_lista_componentes(raw: list | None) -> list[dict]:
    if not isinstance(raw, list):
        return []
    limpio: list[dict] = []
    for item in raw[:_MAX_ITEMS]:
        if not isinstance(item, dict):
            continue
        tipo = item.get('tipo') or item.get('model_name')
        if not isinstance(tipo, str) or tipo not in _TIPOS_VALIDOS:
            continue
        try:
            product_id = int(item.get('id'))
        except (TypeError, ValueError):
            continue
        if product_id < 1:
            continue
        entrada: dict[str, Any] = {'tipo': tipo, 'id': product_id}
        if 'cantidad' in item and item.get('cantidad') not in (None, ''):
            try:
                cantidad = int(item['cantidad'])
            except (TypeError, ValueError):
                continue
            if cantidad < 1 or cantidad > 99:
                continue
            entrada['cantidad'] = cantidad
        limpio.append(entrada)
    return limpio


def _mensaje_error_carga(error_response) -> str:
    if error_response is None:
        return 'Selección no válida.'
    try:
        data = json.loads(error_response.content.decode('utf-8'))
        return data.get('message') or 'Selección no válida.'
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
        return 'Selección no válida.'


def cargar_seleccion_items(
    componentes: list[dict],
    *,
    excluir_clave: str | None = None,
) -> tuple[tuple | None, str | None]:
    cargado, error = _cargar_seleccion(componentes, excluir_clave=excluir_clave)
    if error:
        return None, _mensaje_error_carga(error)
    return cargado, None


def _total_clp(seleccion: dict, almacenamientos: list, memorias: list) -> int:
    total = 0
    for producto in seleccion.values():
        total += int(producto.precio)
    for item in almacenamientos:
        total += int(item['producto'].precio) * int(item['cantidad'])
    for linea in memorias:
        total += int(linea.producto.precio) * int(linea.cantidad)
    return total


def _linea_componente(tipo: str, producto, cantidad: int = 1) -> str:
    nombre = getattr(producto, 'nombre_completo', None) or str(producto)
    precio = int(producto.precio) * cantidad
    stock = int(getattr(producto, 'stock', 0))
    url = reverse('core:detalle', kwargs={'model_name': tipo, 'pk': producto.pk})
    return (
        f'• {nombre} — ${_formato_clp(precio)} CLP'
        f'{f" (×{cantidad})" if cantidad > 1 else ""}, stock {stock}. Ver: {url}'
    )


def _formato_clp(valor: int) -> str:
    return f'${valor:,}'.replace(',', '.')


def analizar_armado(componentes: list[dict]) -> dict:
    items = sanitizar_lista_componentes(componentes)
    if not items:
        return {
            'ok': False,
            'error': 'vacío',
            'mensaje': 'No hay piezas en el armado para analizar. Elige componentes en /armado/ o pídeme un armado nuevo.',
        }

    cargado, err = cargar_seleccion_items(items)
    if cargado is None:
        return {'ok': False, 'error': 'invalido', 'mensaje': err or 'Selección no válida.'}

    seleccion, almacenamientos, memorias = cargado
    resultado, por_categoria = evaluaciones_de_seleccion(
        seleccion,
        memorias_ram=memorias or None,
    )
    if almacenamientos:
        por_categoria['almacenamiento'] = EvaluacionCandidato(
            ESTADO_NO_EVALUADA,
            motivos=(MENSAJE_ALMACENAMIENTO,),
        )

    total = _total_clp(seleccion, almacenamientos, memorias)
    lineas = [
        f'Estado del armado: {resultado.estado}.',
        texto_del_armado(resultado, bool(almacenamientos), bool(seleccion) or bool(memorias)),
        f'Total estimado (catálogo): {_formato_clp(total)} CLP.',
    ]
    for clave, producto in seleccion.items():
        tipo_api = next(
            (t for t, p in PRODUCT_MODEL_MAP.items() if p == type(producto)),
            clave,
        )
        lineas.append(_linea_componente(tipo_api, producto))
    for item in almacenamientos:
        lineas.append(
            _linea_componente(item['tipo'], item['producto'], cantidad=item['cantidad'])
        )
    for linea_ram in memorias:
        lineas.append(
            _linea_componente('memoria_ram', linea_ram.producto, cantidad=linea_ram.cantidad)
        )
    if resultado.advertencias:
        lineas.append('Advertencias: ' + '; '.join(resultado.advertencias[:5]))
    if resultado.motivos_de_rechazo:
        lineas.append('Incompatibilidades: ' + '; '.join(resultado.motivos_de_rechazo[:5]))

    return {
        'ok': True,
        'estado': resultado.estado,
        'total_clp': total,
        'bloquea_agregar': resultado.bloquea_agregar,
        'advertencias': list(resultado.advertencias),
        'motivos': list(resultado.motivos_de_rechazo),
        'piezas': {
            clave: _serializar_evaluacion(ev) for clave, ev in por_categoria.items()
        },
        'componentes': items,
        'texto': '\n'.join(lineas),
    }


def detectar_categoria_armado(texto: str) -> str | None:
    bajo = (texto or '').lower()
    for clave, categoria in _CATEGORIA_UI_POR_TEXTO.items():
        if clave in bajo:
            return categoria
    return None


def _clave_exclusion_categoria(categoria_ui: str) -> str | None:
    from core.views import _CLAVE_QUE_REEMPLAZA

    return _CLAVE_QUE_REEMPLAZA.get(categoria_ui)


def proponer_reemplazo(
    componentes: list[dict],
    categoria_ui: str,
    *,
    preferencia: str = 'cheaper',
) -> dict:
    items = sanitizar_lista_componentes(componentes)
    if not items:
        return {
            'ok': False,
            'mensaje': 'Primero necesito piezas en tu armado (en /armado/ o desde una propuesta del chat).',
        }

    excluir = _clave_exclusion_categoria(categoria_ui)
    cargado, err = cargar_seleccion_items(items, excluir_clave=excluir)
    if cargado is None:
        return {'ok': False, 'mensaje': err or 'No pude cargar el armado actual.'}

    seleccion, almacenamientos, memorias = cargado
    candidatos = candidatos_para_categoria(categoria_ui, seleccion, memorias=memorias or None)
    if not candidatos:
        return {
            'ok': False,
            'mensaje': f'No hay candidatos en catálogo para {categoria_ui}.',
        }

    actual_id = None
    for item in items:
        tipo = item.get('tipo')
        if _UI_POR_TIPO.get(tipo) == categoria_ui:
            actual_id = item.get('id')
            break

    con_stock = [c for c in candidatos if c.get('stock', 0) > 0]
    pool = con_stock or candidatos
    compatibles = [c for c in pool if c.get('estado') == 'compatible']
    if not compatibles:
        compatibles = [c for c in pool if c.get('estado') != 'incompatible']
    if not compatibles:
        return {
            'ok': False,
            'mensaje': 'No encontré reemplazos compatibles con el resto del armado.',
        }

    if preferencia == 'better' and actual_id is not None:
        precio_actual = next(
            (c.get('precio') or 0 for c in pool if c.get('id') == actual_id),
            None,
        )
        compatibles.sort(key=lambda c: (c.get('precio') or 0, c.get('nombre') or ''))
        elegido = None
        for cand in compatibles:
            if cand.get('id') == actual_id:
                continue
            if precio_actual is None or (cand.get('precio') or 0) > precio_actual:
                elegido = cand
                break
        if elegido is None:
            return {
                'ok': False,
                'mensaje': 'No hay una pieza compatible más capaz que la actual en esa categoría.',
            }
    elif preferencia == 'cheaper' and actual_id is not None:
        compatibles.sort(key=lambda c: (c.get('precio') or 0, c.get('nombre') or ''))
        elegido = None
        for cand in compatibles:
            if cand.get('id') != actual_id:
                elegido = cand
                break
        if elegido is None:
            return {
                'ok': False,
                'mensaje': 'Ya tienes la opción más económica compatible en esa categoría.',
            }
    else:
        compatibles.sort(key=lambda c: (0 if c.get('stock', 0) > 0 else 1, c.get('precio') or 0))
        elegido = compatibles[0]
        if actual_id is not None and elegido.get('id') == actual_id:
            return {
                'ok': False,
                'mensaje': 'La pieza actual ya coincide con la mejor opción compatible encontrada.',
            }

    model_name = elegido.get('model_name') or elegido.get('tipo')
    nuevos = [i for i in items if _UI_POR_TIPO.get(i['tipo']) != categoria_ui]
    nuevos.append({'tipo': model_name, 'id': elegido['id'], 'cantidad': 1})

    analisis = analizar_armado(nuevos)
    action_id = secrets.token_urlsafe(12)
    resumen = (
        f"Reemplazar {categoria_ui}: {elegido.get('nombre')} — "
        f"{_formato_clp(int(elegido.get('precio') or 0))} CLP, stock {elegido.get('stock', 0)}."
    )
    return {
        'ok': True,
        'candidato': elegido,
        'componentes_propuestos': nuevos,
        'resumen': resumen,
        'analisis': analisis,
        'pending_action': {
            'id': action_id,
            'tipo': 'reemplazar_pieza',
            'categoria': categoria_ui,
            'componentes': nuevos,
            'resumen': resumen,
        },
    }


def fusionar_componentes_activos(
    build_context: dict | None,
    builder_componentes: list[dict] | None,
) -> list[dict]:
    builder = sanitizar_lista_componentes(builder_componentes)
    if builder:
        return builder
    if build_context and isinstance(build_context.get('componentes'), list):
        return sanitizar_lista_componentes(build_context['componentes'])
    return []


_PROPUESTA_TTL = timedelta(minutes=10)


def crear_propuesta_pendiente_armado(componentes: list[dict], meta: dict | None = None) -> dict:
    """Propuesta para aplicar al abrir /armado/ (sesión del cliente)."""
    items = sanitizar_lista_componentes(componentes)
    ahora = timezone.now()
    return {
        'version': 1,
        'componentes': items,
        'meta': meta or {},
        'guardado_en': 'chat',
        'created_at': ahora.isoformat(),
        'expires_at': (ahora + _PROPUESTA_TTL).isoformat(),
    }


def propuesta_expirada(propuesta: dict | None) -> bool:
    if not isinstance(propuesta, dict):
        return False
    raw = propuesta.get('expires_at')
    if not raw or not isinstance(raw, str):
        return False
    momento = parse_datetime(raw)
    if momento is None:
        return False
    if timezone.is_naive(momento):
        momento = timezone.make_aware(momento, timezone.get_current_timezone())
    return timezone.now() > momento


def productos_catalogo_desde_componentes(componentes: list[dict]) -> list[dict]:
    from core.chatbot.serializers import producto_a_dict

    productos: list[dict] = []
    for item in sanitizar_lista_componentes(componentes):
        modelo = PRODUCT_MODEL_MAP.get(item['tipo'])
        if modelo is None:
            continue
        producto = modelo.objects.filter(pk=item['id']).select_related('proveedor').first()
        if producto is None:
            continue
        productos.append(producto_a_dict(producto, item['tipo']))
    return productos


def revalidar_propuesta_armado(
    componentes: list[dict] | None = None,
    propuesta: dict | None = None,
) -> dict:
    """Relee ORM, compatibilidad y stock antes de aplicar una propuesta guardada."""
    if propuesta_expirada(propuesta if isinstance(propuesta, dict) else None):
        return {
            'ok': False,
            'expired': True,
            'mensaje': 'La propuesta expiró. Pide un armado nuevo en el chat.',
        }

    items: list[dict] = []
    if isinstance(propuesta, dict) and isinstance(propuesta.get('componentes'), list):
        items = sanitizar_lista_componentes(propuesta['componentes'])
    if not items and componentes:
        items = sanitizar_lista_componentes(componentes)
    if not items:
        return {'ok': False, 'mensaje': 'No hay piezas válidas para revalidar.'}

    analisis = analizar_armado(items)
    if not analisis.get('ok'):
        return {
            'ok': False,
            'mensaje': analisis.get('mensaje') or 'El armado ya no es válido con el catálogo actual.',
            'analisis': analisis,
        }
    if analisis.get('estado') in ('incompatible', 'datos_insuficientes'):
        return {
            'ok': False,
            'mensaje': 'La propuesta no pasa las reglas de compatibilidad del armador.',
            'analisis': analisis,
        }

    productos = productos_catalogo_desde_componentes(items)
    if not productos:
        return {
            'ok': False,
            'mensaje': 'Las piezas de la propuesta ya no están disponibles en el catálogo.',
        }
    pedidos = {(item['tipo'], item['id']): int(item.get('cantidad') or 1) for item in items}
    sin_stock = []
    for producto in productos:
        necesario = pedidos.get((producto.get('modelo'), producto.get('producto_pk')), 1)
        producto['cantidad'] = necesario
        if int(producto.get('stock') or 0) < necesario:
            sin_stock.append(producto.get('nombre_completo') or producto.get('nombre'))
    if sin_stock:
        return {
            'ok': False,
            'mensaje': 'Sin stock suficiente: ' + ', '.join(sin_stock),
            'productos': productos,
        }

    meta = propuesta.get('meta') if isinstance(propuesta, dict) else None
    propuesta_limpia = crear_propuesta_pendiente_armado(items, meta=meta if isinstance(meta, dict) else None)
    if isinstance(propuesta, dict) and propuesta.get('expires_at'):
        propuesta_limpia['created_at'] = propuesta.get('created_at')
        propuesta_limpia['expires_at'] = propuesta.get('expires_at')
    from core.chatbot.session_client import build_context_persistible

    ctx = build_context_persistible(
        {
            'componentes': items,
            'total_clp': analisis.get('total_clp'),
            'proposito': (meta or {}).get('proposito') if isinstance(meta, dict) else 'general',
            'presupuesto_clp': (meta or {}).get('presupuesto_clp') if isinstance(meta, dict) else None,
        }
    )
    return {
        'ok': True,
        'componentes': items,
        'productos': productos,
        'proposal_pending': propuesta_limpia,
        'build_context': ctx,
        'analisis': {
            'estado': analisis.get('estado'),
            'total_clp': analisis.get('total_clp'),
            'advertencias': analisis.get('advertencias'),
            'motivos': analisis.get('motivos'),
            'bloquea_agregar': analisis.get('bloquea_agregar'),
        },
    }
