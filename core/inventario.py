"""Cambios de existencias y su historial.

No pasan por aquí, y por eso no dejan movimiento:
QuerySet.update(), la sincronización del catálogo demo y cualquier save()
que asigne stock fuera de aplicar_delta, reponer_stock o el administrador.

Cancelar un pedido o recibir un reembolso de PayPal no devuelve unidades.
No se registra una devolución si la mercancía no volvió al inventario.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from core.alertas_stock import ETIQUETAS, _filas, estado_stock, resumen, unidades_para_normal
from core.catalogo.registry import MODEL_BY_API_NAME, model_name_for
from core.models import AuditoriaUmbral, MovimientoStock


class StockInsuficiente(Exception):
    pass


def _datos_producto(producto):
    return {
        'content_type': ContentType.objects.get_for_model(producto, for_concrete_model=False),
        'object_id': producto.pk,
        'producto_modelo': model_name_for(type(producto)),
        'producto_pk': producto.pk,
        'nombre_producto': producto.nombre,
    }


def _anotar(producto, anterior, posterior, *, tipo, usuario, origen, pedido=None, item=None, motivo=''):
    return MovimientoStock.objects.create(
        **_datos_producto(producto),
        categoria=producto.categoria,
        tipo=tipo,
        cantidad=posterior - anterior,
        stock_anterior=anterior,
        stock_posterior=posterior,
        usuario=usuario,
        origen=origen,
        pedido=pedido,
        item_pedido=item,
        motivo=(motivo or '')[:255],
    )


def aplicar_delta(producto, delta, *, tipo, usuario=None, origen, pedido=None, item=None, motivo=''):
    """Suma delta dentro del bloqueo de la fila. Un delta negativo descuenta."""
    delta = int(delta)
    with transaction.atomic():
        bloqueado = type(producto).objects.select_for_update().get(pk=producto.pk)
        if item is not None and tipo == MovimientoStock.VENTA:
            if MovimientoStock.objects.filter(item_pedido=item, tipo=MovimientoStock.VENTA).exists():
                producto.stock = bloqueado.stock
                return None
        anterior = bloqueado.stock
        posterior = anterior + delta
        if delta == 0:
            return None
        if posterior < 0:
            raise StockInsuficiente(bloqueado.nombre)
        bloqueado.stock = posterior
        bloqueado.save(update_fields=['stock'])
        producto.stock = posterior
        return _anotar(
            bloqueado, anterior, posterior,
            tipo=tipo, usuario=usuario, origen=origen,
            pedido=pedido, item=item, motivo=motivo,
        )


def registrar_venta(producto, item, pedido):
    return aplicar_delta(
        producto, -item.cantidad,
        tipo=MovimientoStock.VENTA, origen='paypal', pedido=pedido, item=item,
        motivo=f'Pedido #{pedido.pk}',
    )


def reponer_stock(producto, cantidad, *, usuario, origen='servicio', motivo=''):
    cantidad = int(cantidad)
    if cantidad <= 0:
        raise StockInsuficiente('La reposición debe ser de al menos una unidad.')
    return aplicar_delta(
        producto, cantidad,
        tipo=MovimientoStock.REPOSICION, usuario=usuario, origen=origen, motivo=motivo,
    )


def ajustar_stock(producto, nuevo_stock, *, usuario, origen='servicio', motivo=''):
    nuevo_stock = int(nuevo_stock)
    if nuevo_stock < 0:
        raise StockInsuficiente('El stock no puede quedar negativo.')
    with transaction.atomic():
        bloqueado = type(producto).objects.select_for_update().get(pk=producto.pk)
        anterior = bloqueado.stock
        if nuevo_stock == anterior:
            return None
        bloqueado.stock = nuevo_stock
        bloqueado.save(update_fields=['stock'])
        producto.stock = nuevo_stock
        return _anotar(
            bloqueado, anterior, nuevo_stock,
            tipo=MovimientoStock.AJUSTE, usuario=usuario, origen=origen, motivo=motivo,
        )


def anotar_ajuste_ya_guardado(producto, anterior, *, usuario, origen, motivo):
    """El stock ya se guardó en esta transacción. Solo deja constancia."""
    posterior = producto.stock
    if posterior == anterior or posterior < 0:
        return None
    return _anotar(
        producto, anterior, posterior,
        tipo=MovimientoStock.AJUSTE, usuario=usuario, origen=origen, motivo=motivo,
    )


def _entero(valor, etiqueta):
    if isinstance(valor, bool) or isinstance(valor, float):
        raise ValueError(f'{etiqueta} debe ser un número entero.')
    texto = str(valor if valor is not None else '').strip()
    if not texto.isdigit():
        raise ValueError(f'{etiqueta} debe ser un número entero igual o mayor que cero.')
    return int(texto)


def guardar_umbrales(producto, minimo, advertencia, usuario):
    minimo = _entero(minimo, 'El stock mínimo')
    advertencia = _entero(advertencia, 'El umbral de advertencia')
    if advertencia < minimo:
        raise ValueError('El umbral de advertencia debe ser mayor o igual que el stock mínimo.')
    with transaction.atomic():
        bloqueado = type(producto).objects.select_for_update().get(pk=producto.pk)
        anterior_min = bloqueado.stock_minimo
        anterior_adv = bloqueado.stock_advertencia
        if (anterior_min, anterior_adv) == (minimo, advertencia):
            return bloqueado
        bloqueado.stock_minimo = minimo
        bloqueado.stock_advertencia = advertencia
        bloqueado.save(update_fields=['stock_minimo', 'stock_advertencia', 'actualizado_en'])
        auditar_umbrales(bloqueado, anterior_min, anterior_adv, usuario)
        producto.stock_minimo = minimo
        producto.stock_advertencia = advertencia
        return bloqueado


def auditar_umbrales(producto, minimo_anterior, advertencia_anterior, usuario):
    if (producto.stock_minimo, producto.stock_advertencia) == (minimo_anterior, advertencia_anterior):
        return None
    return AuditoriaUmbral.objects.create(
        **_datos_producto(producto),
        minimo_anterior=minimo_anterior,
        minimo_nuevo=producto.stock_minimo,
        advertencia_anterior=advertencia_anterior,
        advertencia_nueva=producto.stock_advertencia,
        usuario=usuario,
    )


def _exigir_staff(request):
    if not request.user.is_active or not request.user.is_staff:
        raise PermissionDenied('Solo el personal puede ver el inventario.')


def _consulta_movimientos(request):
    consulta = MovimientoStock.objects.select_related('usuario', 'pedido')
    texto = (request.GET.get('q') or '').strip()
    tipo = (request.GET.get('tipo') or '').strip()
    categoria = (request.GET.get('categoria') or '').strip()
    usuario_id = (request.GET.get('usuario') or '').strip()
    desde = parse_date(request.GET.get('desde') or '')
    hasta = parse_date(request.GET.get('hasta') or '')
    if texto and ':' in texto:
        modelo, pk = texto.split(':', 1)
        if pk.isdigit():
            consulta = consulta.filter(producto_modelo=modelo, producto_pk=int(pk))
        else:
            consulta = consulta.none()
    elif texto.isdigit():
        consulta = consulta.filter(producto_pk=int(texto))
    elif texto:
        consulta = consulta.filter(nombre_producto__icontains=texto)
    if tipo in dict(MovimientoStock.TIPOS):
        consulta = consulta.filter(tipo=tipo)
    if categoria:
        consulta = consulta.filter(categoria=categoria)
    if usuario_id == 'sistema':
        consulta = consulta.filter(usuario__isnull=True)
    elif usuario_id.isdigit():
        consulta = consulta.filter(usuario_id=int(usuario_id))
    if desde:
        consulta = consulta.filter(creado_en__date__gte=desde)
    if hasta:
        consulta = consulta.filter(creado_en__date__lte=hasta)
    return consulta.order_by('-creado_en', '-id')


def _pagina_movimientos(request, consulta, extra):
    paginador = Paginator(consulta, 20)
    pagina = paginador.get_page(request.GET.get('page'))
    parametros = request.GET.copy()
    parametros.pop('page', None)
    vistos = list(
        User.objects.filter(movimientos_stock__isnull=False).order_by('username').distinct()
    )
    contexto = {
        'pagina': pagina,
        'consulta': parametros.urlencode(),
        'q': request.GET.get('q') or '',
        'tipo': request.GET.get('tipo') or '',
        'categoria': request.GET.get('categoria') or '',
        'usuario': request.GET.get('usuario') or '',
        'desde': request.GET.get('desde') or '',
        'hasta': request.GET.get('hasta') or '',
        'tipos': MovimientoStock.TIPOS,
        'categorias': sorted(set(MovimientoStock.objects.values_list('categoria', flat=True))),
        'usuarios': vistos,
    }
    contexto.update(extra)
    return render(request, 'core/movimientos_stock.html', contexto)


@login_required
def vista_movimientos(request):
    _exigir_staff(request)
    return _pagina_movimientos(request, _consulta_movimientos(request), {
        'titulo': 'Historial de movimientos',
        'producto': None,
    })


@login_required
def vista_movimientos_producto(request, model_name, pk):
    _exigir_staff(request)
    modelo = MODEL_BY_API_NAME.get(model_name)
    if modelo is None:
        raise Http404
    producto = get_object_or_404(modelo, pk=pk)
    consulta = _consulta_movimientos(request).filter(producto_modelo=model_name, producto_pk=pk)
    return _pagina_movimientos(request, consulta, {
        'titulo': f'Historial de {producto.nombre}',
        'producto': producto,
        'model_name': model_name,
    })


@login_required
@require_POST
def vista_guardar_umbrales(request):
    _exigir_staff(request)
    model_name = (request.POST.get('modelo') or '').strip()
    modelo = MODEL_BY_API_NAME.get(model_name)
    pk = request.POST.get('pk')
    if modelo is None or not str(pk).isdigit():
        return JsonResponse({'ok': False, 'error': 'Producto desconocido.'}, status=404)
    if not request.user.has_perm(f'{modelo._meta.app_label}.change_{modelo._meta.model_name}'):
        return JsonResponse({'ok': False, 'error': 'No tienes permiso para editar este producto.'}, status=403)
    producto = get_object_or_404(modelo, pk=int(pk))
    try:
        guardado = guardar_umbrales(
            producto, request.POST.get('stock_minimo'), request.POST.get('stock_advertencia'), request.user,
        )
    except ValueError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    estado = estado_stock(guardado.stock, guardado.stock_minimo, guardado.stock_advertencia)
    filtro = (request.POST.get('estado') or 'todos').strip()
    categoria = (request.POST.get('categoria') or '').strip()
    texto = (request.POST.get('q') or '').strip().lower()
    visible = estado != 'NORMAL'
    mapa = {'agotado': 'AGOTADO', 'critico': 'CRITICO', 'advertencia': 'ADVERTENCIA'}
    if filtro in mapa and estado != mapa[filtro]:
        visible = False
    if categoria and guardado.categoria != categoria:
        visible = False
    if texto and texto not in guardado.nombre.lower() and texto not in f'{model_name}:{guardado.pk}' and texto != str(guardado.pk):
        visible = False
    return JsonResponse({
        'ok': True,
        'stock': guardado.stock,
        'stock_minimo': guardado.stock_minimo,
        'stock_advertencia': guardado.stock_advertencia,
        'estado': estado,
        'etiqueta': ETIQUETAS[estado],
        'unidades': unidades_para_normal(guardado.stock, guardado.stock_advertencia),
        'visible': visible,
        'resumen': resumen(_filas()),
    })
