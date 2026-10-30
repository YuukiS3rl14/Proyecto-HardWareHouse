"""Vistas JSON del backend del chatbot."""
from __future__ import annotations

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from core.chatbot.assistant_config import get_asistente_config
from core.chatbot.llm.intent_extractor import intent_llm_activo
from core.chatbot.budget import ConsultaPresupuesto, buscar_por_presupuesto, presupuesto_armado_simple
from core.chatbot.conversation import generar_respuesta
from core.chatbot.policy import metadata_sistema
from core.chatbot.search import FiltrosCatalogo, buscar_catalogo
from core.armado_servicio import analizar_armado, revalidar_propuesta_armado, sanitizar_lista_componentes
from core.chatbot.session_client import build_context_persistible
from core.chatbot.security import (
    cargar_json,
    chat_api_protegida,
    validar_build_context,
    validar_builder_componentes,
    validar_payload_chat,
)
from core.catalogo.registry import categorias_disponibles


@require_POST
@csrf_protect
@chat_api_protegida('chat')
def chat_asistente_api(request):
    payload, error = cargar_json(request)
    if error:
        return error

    mensaje, historial, error = validar_payload_chat(payload)
    if error:
        return error

    build_context = validar_build_context(payload)
    builder_componentes = validar_builder_componentes(payload)
    resultado = generar_respuesta(
        mensaje,
        historial=historial,
        usuario=request.user,
        build_context=build_context,
        builder_componentes=builder_componentes,
    )
    return JsonResponse(resultado)


@require_POST
@csrf_protect
@chat_api_protegida('catalogo')
def armado_estado_api(request):
    """Estado verificado del armado (compatibilidad, total, advertencias). Solo lectura."""
    payload, error = cargar_json(request)
    if error:
        return error
    componentes = sanitizar_lista_componentes(payload.get('componentes'))
    if not componentes:
        return JsonResponse(
            {'error': 'componentes debe ser una lista no vacía con tipo e id válidos.'},
            status=400,
        )
    data = analizar_armado(componentes)
    if not data.get('ok'):
        return JsonResponse({'status': 'error', 'message': data.get('mensaje')}, status=400)
    return JsonResponse({'status': 'success', **data})


@require_POST
@csrf_protect
@chat_api_protegida('catalogo')
def armado_revalidar_api(request):
    """Revalida propuesta o selección guardada (precios, stock, compatibilidad)."""
    payload, error = cargar_json(request)
    if error:
        return error
    propuesta = payload.get('proposal') or payload.get('proposal_pending')
    componentes = sanitizar_lista_componentes(payload.get('componentes'))
    data = revalidar_propuesta_armado(componentes=componentes or None, propuesta=propuesta)
    if not data.get('ok'):
        return JsonResponse({'status': 'error', **data}, status=400)
    return JsonResponse({'status': 'success', **data})


@require_POST
@csrf_protect
@chat_api_protegida('chat')
def chat_sesion_restaurar_api(request):
    """Restaura contexto de armado persistido sin datos de pedidos."""
    payload, error = cargar_json(request)
    if error:
        return error
    ctx = build_context_persistible(payload.get('build_context'))
    propuesta = payload.get('proposal_pending')
    componentes = ctx.get('componentes') if ctx else []
    data = revalidar_propuesta_armado(
        componentes=componentes,
        propuesta=propuesta if isinstance(propuesta, dict) else None,
    )
    if not data.get('ok') and componentes:
        return JsonResponse(
            {
                'status': 'partial',
                'build_context': ctx,
                'mensaje': data.get('mensaje'),
            }
        )
    return JsonResponse(
        {
            'status': 'success',
            'build_context': data.get('build_context') or ctx,
            'proposal_pending': data.get('proposal_pending'),
            'productos': data.get('productos') or [],
            'analisis': data.get('analisis'),
        }
    )


@require_GET
@chat_api_protegida('metadata')
def chat_asistente_config_api(request):
    """Identidad y reglas públicas del asistente (sin datos privados)."""
    config = get_asistente_config()
    return JsonResponse(
        {
            **metadata_sistema(config),
            'nombre_corto': config.nombre_corto,
            'mensaje_bienvenida': config.mensaje_bienvenida,
            'subtitulo_widget': config.subtitulo_widget,
            'placeholder_input': config.placeholder_input,
            'motor': 'ollama' if intent_llm_activo() else 'reglas',
            'intent_llm': intent_llm_activo(),
        }
    )


@require_POST
@csrf_protect
@chat_api_protegida('catalogo')
def catalogo_buscar_api(request):
    payload, error = cargar_json(request)
    if error:
        return error

    filtros = FiltrosCatalogo.desde_dict(payload)
    if not any(
        [
            filtros.q,
            filtros.categoria,
            filtros.marca,
            filtros.proveedor_id,
            filtros.precio_min,
            filtros.precio_max,
            filtros.solo_con_stock,
            filtros.modelos,
        ]
    ):
        return JsonResponse(
            {'error': 'Indica al menos un criterio de búsqueda o filtro.'},
            status=400,
        )
    return JsonResponse(buscar_catalogo(filtros))


@require_POST
@csrf_protect
@chat_api_protegida('catalogo')
def catalogo_presupuesto_api(request):
    payload, error = cargar_json(request)
    if error:
        return error

    consulta = ConsultaPresupuesto.desde_dict(payload)
    if consulta is None:
        return JsonResponse({'error': 'presupuesto_max inválido o ausente.'}, status=400)
    return JsonResponse(buscar_por_presupuesto(consulta))


@require_POST
@csrf_protect
@chat_api_protegida('catalogo')
def catalogo_total_armado_api(request):
    payload, error = cargar_json(request)
    if error:
        return error

    items = payload.get('items')
    if not isinstance(items, list) or not items:
        return JsonResponse({'error': 'items debe ser una lista no vacía.'}, status=400)
    if len(items) > 50:
        return JsonResponse({'error': 'Demasiados ítems en el armado.'}, status=400)
    return JsonResponse(presupuesto_armado_simple(items))


@require_GET
@chat_api_protegida('metadata')
def catalogo_metadata_api(request):
    from core.models import Proveedor

    marcas = list(Proveedor.objects.order_by('nombre').values('id', 'nombre'))
    return JsonResponse(
        {
            'categorias': categorias_disponibles(),
            'marcas': marcas,
            'ordenes': ['relevancia', 'precio_asc', 'precio_desc', 'stock_desc'],
        }
    )
