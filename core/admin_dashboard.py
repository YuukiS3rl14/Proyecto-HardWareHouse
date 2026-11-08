from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Count, F, Max, Q, Sum
from django.urls import reverse
from django.utils import timezone

from core.models import (
    AlmacenamientoHDD,
    AlmacenamientoSSD,
    FuenteDePoder,
    Gabinete,
    ItemPedido,
    MemoriaRam,
    Pedido,
    PlacaMadre,
    Procesador,
    RefrigeracionCooler,
    TarjetaGrafica,
    Ventilador,
    _MODELOS_DE_PRODUCTO,
)

ESTADOS_VENTA = ('PAGADO', 'ENVIADO', 'ENTREGADO')
STOCK_BAJO_MINIMO = 1
STOCK_BAJO_MAXIMO = 5
TAMANO_PAGINA = 8
LIMITE_MAS_VENDIDOS = 5
ZONA_VENTAS = ZoneInfo('America/Santiago')
_MESES = (
    'ene', 'feb', 'mar', 'abr', 'may', 'jun',
    'jul', 'ago', 'sep', 'oct', 'nov', 'dic',
)
MODELOS_PRODUCTO = (
    Procesador,
    TarjetaGrafica,
    MemoriaRam,
    PlacaMadre,
    AlmacenamientoSSD,
    AlmacenamientoHDD,
    Gabinete,
    FuenteDePoder,
    RefrigeracionCooler,
    Ventilador,
)


def inicio_del_mes(momento=None):
    actual = timezone.localtime(momento, ZONA_VENTAS) if momento is not None else timezone.localtime()
    return actual.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def inicio_ventana_ventas(momento=None):
    actual = inicio_del_mes(momento)
    mes = actual.month - 11
    anio = actual.year
    while mes <= 0:
        mes += 12
        anio -= 1
    return actual.replace(year=anio, month=mes)


def mes_santiago(fecha):
    local = timezone.localtime(fecha, ZONA_VENTAS)
    return local.year, local.month


def resumen_dashboard(request):
    ventas, pedidos = _ventas_y_pedidos(request)
    productos = _productos(request)
    return {
        'ventas': ventas,
        'pedidos': pedidos,
        'productos': productos,
        'graficos': _graficos(request, pedidos['permitido'], productos['permitido']),
    }


def datos_tarjeta(request, nombre):
    """Datos de una sola tarjeta. No calcula gráficos ni la otra lista."""
    if nombre == 'pedidos':
        _ventas, pedidos = _ventas_y_pedidos(request)
        return {'pedidos': pedidos}
    if nombre == 'alertas':
        return {'productos': _productos(request)}
    return None


def _puede_ver(request, modelo):
    from django.contrib import admin

    model_admin = admin.site._registry.get(modelo)
    if model_admin is None:
        return False
    return model_admin.has_view_permission(request)


def _url_cambio(modelo, pk):
    opciones = modelo._meta
    return reverse(f'admin:{opciones.app_label}_{opciones.model_name}_change', args=[pk])


def _decimal(valor):
    if valor is None:
        return Decimal('0')
    return valor


def _pesos(valor):
    return int(_decimal(valor).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


class _Paginador(Paginator):
    """Usa un total ya calculado y solo lee la página pedida."""

    def __init__(self, object_list, total):
        self._total = total
        super().__init__(object_list, TAMANO_PAGINA)

    @property
    def count(self):
        return self._total


class _Corte:
    def __init__(self, leer):
        self.leer = leer

    def __getitem__(self, corte):
        inicio = corte.start or 0
        cantidad = (corte.stop or inicio) - inicio
        if cantidad <= 0:
            return []
        return self.leer(inicio, cantidad)


def _pagina(request, clave, total, leer):
    pagina = _Paginador(_Corte(leer), total).get_page(request.GET.get(clave))
    return list(pagina.object_list), _controles(request, clave, pagina)


def _controles(request, clave, pagina):
    ancla = 'hw-ultimos-pedidos' if clave == 'pedidos_pagina' else 'hw-alertas'

    def enlace(numero):
        params = request.GET.copy()
        params.pop('hw_tarjeta', None)
        if numero <= 1:
            params.pop(clave, None)
        else:
            params[clave] = numero
        consulta = params.urlencode()
        base = reverse('admin:index')
        url = f'{base}?{consulta}' if consulta else base
        return f'{url}#{ancla}'

    return {
        'numero': pagina.number,
        'paginas': pagina.paginator.num_pages,
        'total': pagina.paginator.count,
        'anterior': enlace(pagina.previous_page_number()) if pagina.has_previous() else '',
        'siguiente': enlace(pagina.next_page_number()) if pagina.has_next() else '',
    }


def _cita(nombre):
    return connection.ops.quote_name(nombre)


def _ventas_y_pedidos(request):
    if not _puede_ver(request, Pedido):
        return {'permitido': False}, {'permitido': False, 'recientes': []}

    inicio = inicio_del_mes()
    venta = Q(estado__in=ESTADOS_VENTA)
    totales = Pedido.objects.aggregate(
        mes=Sum('total_monto', filter=venta & Q(fecha_pedido__gte=inicio)),
        historico=Sum('total_monto', filter=venta),
        registrados=Count('pk'),
        pendientes=Count('pk', filter=Q(estado='PENDIENTE')),
    )
    registrados = totales['registrados'] or 0

    def leer(inicio, cantidad):
        return list(
            Pedido.objects.select_related('usuario').order_by('-fecha_pedido', '-pk')[inicio:inicio + cantidad]
        )

    recientes, paginacion = _pagina(request, 'pedidos_pagina', registrados, leer)
    return (
        {
            'permitido': True,
            'mes': _decimal(totales['mes']),
            'historico': _decimal(totales['historico']),
        },
        {
            'permitido': True,
            'registrados': registrados,
            'pendientes': totales['pendientes'] or 0,
            'recientes': recientes,
            'paginacion': paginacion,
        },
    )


def _productos(request):
    modelos = [modelo for modelo in MODELOS_PRODUCTO if _puede_ver(request, modelo)]
    if not modelos:
        return {'permitido': False, 'alertas': []}

    disponibles = 0
    stock_bajo = 0
    agotados = 0
    con_alerta = []
    for modelo in modelos:
        conteo = modelo.objects.aggregate(
            disponibles=Count('pk', filter=Q(stock__gt=0)),
            stock_bajo=Count('pk', filter=Q(stock__gte=STOCK_BAJO_MINIMO, stock__lte=STOCK_BAJO_MAXIMO)),
            agotados=Count('pk', filter=Q(stock=0)),
        )
        disponibles += conteo['disponibles'] or 0
        stock_bajo += conteo['stock_bajo'] or 0
        agotados += conteo['agotados'] or 0
        if conteo['stock_bajo'] or conteo['agotados']:
            con_alerta.append(modelo)

    def leer(inicio, cantidad):
        return _leer_alertas(con_alerta, inicio, cantidad)

    alertas, paginacion = _pagina(request, 'alertas_pagina', stock_bajo + agotados, leer)
    return {
        'permitido': True,
        'disponibles': disponibles,
        'stock_bajo': stock_bajo,
        'agotados': agotados,
        'alertas': alertas,
        'alertas_totales': stock_bajo + agotados,
        'paginacion': paginacion,
    }


def _leer_alertas(modelos, inicio, cantidad):
    if not modelos or cantidad <= 0:
        return []
    partes = []
    parametros = []
    for modelo in modelos:
        tabla = _cita(modelo._meta.db_table)
        campos = [
            _cita(modelo._meta.pk.column),
            _cita(modelo._meta.get_field('nombre').column),
            _cita(modelo._meta.get_field('categoria').column),
            _cita(modelo._meta.get_field('stock').column),
        ]
        partes.append(
            f'SELECT {campos[0]} AS pk, {campos[1]} AS nombre, {campos[2]} AS categoria, '
            f'{campos[3]} AS stock, %s AS origen FROM {tabla} '
            f'WHERE {campos[3]} >= %s AND {campos[3]} <= %s'
        )
        parametros.extend([modelo._meta.model_name, 0, STOCK_BAJO_MAXIMO])
    consulta = (
        'SELECT pk, nombre, categoria, stock, origen FROM ('
        + ' UNION ALL '.join(partes)
        + ') alertas ORDER BY stock ASC, nombre ASC, origen ASC, pk ASC LIMIT %s OFFSET %s'
    )
    parametros.extend([cantidad, inicio])
    indices = {modelo._meta.model_name: modelo for modelo in modelos}
    with connection.cursor() as cursor:
        cursor.execute(consulta, parametros)
        filas = cursor.fetchall()
    return [
        {
            'nombre': nombre,
            'tipo': categoria,
            'stock': stock,
            'estado': 'Agotado' if stock == 0 else 'Stock bajo',
            'url': _url_cambio(indices[origen], pk),
        }
        for pk, nombre, categoria, stock, origen in filas
    ]


def _claves_producto_visibles(request):
    return [
        clave for clave, modelo in _MODELOS_DE_PRODUCTO.items()
        if _puede_ver(request, modelo)
    ]


def _rango_meses(inicio, actual):
    meses = []
    anio, mes = inicio.year, inicio.month
    while (anio, mes) <= (actual.year, actual.month):
        meses.append((anio, mes))
        mes += 1
        if mes == 13:
            mes = 1
            anio += 1
    return meses


def _grafico_visible(grafico):
    return bool(grafico) and not grafico.get('vacio')


def _graficos(request, puede_pedidos, puede_productos):
    ventas = _grafico_ventas() if puede_pedidos else None
    estados = _grafico_estados() if puede_pedidos else None
    vendidos = _grafico_vendidos(request) if puede_pedidos and puede_productos else None
    return {
        'ventas': ventas,
        'estados': estados,
        'vendidos': vendidos,
        'cargar': _grafico_visible(ventas) or _grafico_visible(estados),
    }


def _grafico_ventas():
    inicio = inicio_ventana_ventas()
    meses = _rango_meses(inicio, inicio_del_mes())
    totales = {mes: Decimal('0') for mes in meses}
    filas = Pedido.objects.filter(
        estado__in=ESTADOS_VENTA,
        fecha_pedido__gte=inicio,
    ).values_list('fecha_pedido', 'total_monto')
    for fecha, monto in filas:
        clave = mes_santiago(fecha)
        if clave in totales:
            totales[clave] += monto or Decimal('0')
    puntos = [
        {'etiqueta': f'{_MESES[mes - 1]} {anio}', 'valor': _pesos(totales[(anio, mes)])}
        for anio, mes in meses
    ]
    return {
        'vacio': not any(punto['valor'] for punto in puntos),
        'puntos': puntos,
    }


def _grafico_estados():
    totales = Pedido.objects.aggregate(**{
        estado: Count('pk', filter=Q(estado=estado))
        for estado, _etiqueta in Pedido.ESTADOS
    })
    puntos = [
        {'etiqueta': etiqueta, 'clave': estado, 'valor': totales[estado] or 0}
        for estado, etiqueta in Pedido.ESTADOS
    ]
    if not any(punto['valor'] for punto in puntos):
        return {'vacio': True}
    return {'vacio': False, 'puntos': puntos}


def _grafico_vendidos(request):
    claves = _claves_producto_visibles(request)
    if not claves:
        return None
    filas = list(
        ItemPedido.objects.filter(
            pedido__estado__in=ESTADOS_VENTA,
            producto_modelo__in=claves,
            producto_pk__isnull=False,
        ).values('producto_modelo', 'producto_pk').annotate(
            unidades=Sum('cantidad'),
            ingresos=Sum(F('precio_unitario') * F('cantidad')),
            nombre_linea=Max('producto_nombre'),
            tipo_linea=Max('producto_tipo'),
        ).order_by('-unidades', 'producto_modelo', 'producto_pk')[:LIMITE_MAS_VENDIDOS]
    )
    if not filas:
        return {'vacio': True}

    ids = {}
    for fila in filas:
        ids.setdefault(fila['producto_modelo'], set()).add(fila['producto_pk'])
    nombres = {}
    for clave, pks in ids.items():
        modelo = _MODELOS_DE_PRODUCTO.get(clave)
        if modelo is None:
            continue
        for pk, nombre, categoria in modelo.objects.filter(pk__in=pks).values_list('pk', 'nombre', 'categoria'):
            nombres[(clave, pk)] = (nombre, categoria)

    base = []
    for fila in filas:
        clave = (fila['producto_modelo'], fila['producto_pk'])
        nombre, tipo = nombres.get(clave, (fila['nombre_linea'], fila['tipo_linea']))
        base.append((
            clave[1], nombre, tipo, int(fila['unidades'] or 0), _pesos(fila['ingresos']),
        ))
    repetidas = {}
    for _pk, nombre, tipo, _unidades, _ingresos in base:
        etiqueta = f'{nombre} · {tipo}'
        repetidas[etiqueta] = repetidas.get(etiqueta, 0) + 1
    puntos = []
    for pk, nombre, tipo, unidades, ingresos in base:
        etiqueta = f'{nombre} · {tipo}'
        if repetidas[etiqueta] > 1:
            etiqueta = f'{etiqueta} · #{pk}'
        puntos.append({'etiqueta': etiqueta, 'valor': unidades, 'ingresos': ingresos})
    maximo = max(punto['valor'] for punto in puntos) or 1
    for punto in puntos:
        punto['ancho'] = round(punto['valor'] * 100 / maximo)
    return {'vacio': False, 'puntos': puntos}
