from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Count, Q, Sum
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


_MESES_LARGOS = (
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
)
_MODOS_PERIODO = ('mes', 'anio', 'elegir', 'rango')
_ANIO_MINIMO = 2000
_ANIO_MAXIMO = 2100
_RANGO_MAXIMO_DIAS = 366 * 3
_TITULO_VENTAS = {'dia': 'Ventas por día', 'semana': 'Ventas por semana', 'mes': 'Ventas por mes'}
_TITULO_UNIDADES = {
    'dia': 'Unidades vendidas por día',
    'semana': 'Unidades vendidas por semana',
    'mes': 'Unidades vendidas por mes',
}


def resumen_dashboard(request):
    periodo = leer_periodo(request)
    pedidos = _lista_pedidos(request)
    productos = _productos(request)
    ventas = _indicadores(request, periodo, productos['permitido'])
    return {
        'periodo': periodo,
        'ventas': ventas,
        'pedidos': pedidos,
        'productos': productos,
        'graficos': _graficos(request, ventas['permitido'], productos['permitido'], periodo),
    }


def datos_tarjeta(request, nombre):
    """Datos de una sola tarjeta. No calcula la otra lista."""
    if nombre == 'pedidos':
        return {'pedidos': _lista_pedidos(request)}
    if nombre == 'alertas':
        return {'productos': _productos(request)}
    if nombre == 'comercial':
        periodo = leer_periodo(request)
        conteo, _modelos = _conteo_inventario(request)
        ventas = _indicadores(request, periodo, conteo['permitido'])
        if ventas['permitido']:
            pedidos = {
                'permitido': True,
                'pendientes': Pedido.objects.filter(estado='PENDIENTE').count(),
            }
        else:
            pedidos = {'permitido': False}
        return {
            'periodo': periodo,
            'ventas': ventas,
            'pedidos': pedidos,
            'productos': conteo,
            'graficos': _graficos(request, ventas['permitido'], conteo['permitido'], periodo),
        }
    return None


def _ahora_santiago():
    return timezone.localtime(timezone.now(), ZONA_VENTAS)


def _inicio_dia(fecha):
    return datetime(fecha.year, fecha.month, fecha.day, tzinfo=ZONA_VENTAS)


def _mes_completo(anio, mes):
    inicio = datetime(anio, mes, 1, tzinfo=ZONA_VENTAS)
    if mes == 12:
        fin = datetime(anio + 1, 1, 1, tzinfo=ZONA_VENTAS)
    else:
        fin = datetime(anio, mes + 1, 1, tzinfo=ZONA_VENTAS)
    return inicio, fin


def _entero(valor, minimo, maximo):
    try:
        numero = int(str(valor).strip())
    except (TypeError, ValueError, AttributeError):
        return None
    if numero < minimo or numero > maximo:
        return None
    return numero


def _fecha_iso(valor):
    if not valor or not isinstance(valor, str):
        return None
    try:
        return datetime.strptime(valor.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _etiqueta_dia(fecha):
    return f'{fecha.day} {_MESES[fecha.month - 1]} {fecha.year}'


def _url_sin_periodo(request):
    params = request.GET.copy()
    for clave in ('hw_periodo', 'hw_mes', 'hw_anio', 'hw_desde', 'hw_hasta', 'hw_tarjeta'):
        params.pop(clave, None)
    consulta = params.urlencode()
    base = reverse('admin:index')
    return f'{base}?{consulta}' if consulta else base


def _anio_en_curso(ahora):
    return (
        datetime(ahora.year, 1, 1, tzinfo=ZONA_VENTAS),
        datetime(ahora.year + 1, 1, 1, tzinfo=ZONA_VENTAS),
    )


def leer_periodo(request):
    """Lee el filtro comercial. Si llega manipulado, deja el año en curso y explica el error."""
    ahora = _ahora_santiago()
    pedido = (request.GET.get('hw_periodo') or 'anio').strip().lower()
    mes_form = request.GET.get('hw_mes') or str(ahora.month)
    anio_form = request.GET.get('hw_anio') or str(ahora.year)
    desde_form = (request.GET.get('hw_desde') or '').strip()
    hasta_form = (request.GET.get('hw_hasta') or '').strip()
    error = ''
    modo = pedido if pedido in _MODOS_PERIODO else 'anio'
    if pedido not in _MODOS_PERIODO:
        error = 'El período no es válido.'

    if modo == 'mes':
        inicio, fin = _mes_completo(ahora.year, ahora.month)
    elif modo == 'elegir' and not error:
        mes = _entero(mes_form, 1, 12)
        anio = _entero(anio_form, _ANIO_MINIMO, _ANIO_MAXIMO)
        if mes is None or anio is None:
            error = 'La fecha no es válida.'
            inicio, fin = _anio_en_curso(ahora)
        else:
            inicio, fin = _mes_completo(anio, mes)
    elif modo == 'rango' and not error:
        desde = _fecha_iso(desde_form)
        hasta = _fecha_iso(hasta_form)
        if desde is None or hasta is None:
            error = 'La fecha no es válida.'
        elif desde > hasta:
            error = 'El rango está invertido.'
        elif (hasta - desde).days + 1 > _RANGO_MAXIMO_DIAS:
            error = 'El rango es demasiado amplio.'
        if error:
            inicio, fin = _anio_en_curso(ahora)
        else:
            inicio = _inicio_dia(desde)
            fin = _inicio_dia(hasta + timedelta(days=1))
    else:
        inicio, fin = _anio_en_curso(ahora)

    aplicado = 'anio' if error else modo
    comparado = _periodo_anterior(inicio, fin, aplicado)
    return {
        'modo': modo,
        'aplicado': aplicado,
        'error': error,
        'etiqueta': _etiqueta_periodo(inicio, fin, aplicado),
        'comparado_con': _etiqueta_periodo(comparado[0], comparado[1], aplicado),
        'inicio': inicio,
        'fin': fin,
        'anterior_inicio': comparado[0],
        'anterior_fin': comparado[1],
        'agrupacion': _agrupacion(aplicado, inicio, fin),
        'mes': mes_form,
        'anio': anio_form,
        'desde': desde_form,
        'hasta': hasta_form,
        'restablecer': _url_sin_periodo(request),
    }


def _agrupacion(modo, inicio, fin):
    if modo in ('mes', 'elegir'):
        return 'dia'
    if modo == 'anio':
        return 'mes'
    dias = (fin - inicio).days
    if dias <= 31:
        return 'dia'
    if dias <= 120:
        return 'semana'
    return 'mes'


def _periodo_anterior(inicio, fin, modo):
    if modo in ('mes', 'elegir'):
        mes = inicio.month - 1 or 12
        anio = inicio.year - 1 if inicio.month == 1 else inicio.year
        return _mes_completo(anio, mes)
    if modo == 'anio':
        return (
            datetime(inicio.year - 1, 1, 1, tzinfo=ZONA_VENTAS),
            datetime(inicio.year, 1, 1, tzinfo=ZONA_VENTAS),
        )
    delta = fin - inicio
    return inicio - delta, inicio


def _etiqueta_periodo(inicio, fin, modo):
    ultimo = timezone.localtime(fin - timedelta(seconds=1), ZONA_VENTAS)
    if modo in ('mes', 'elegir'):
        return f'{_MESES_LARGOS[inicio.month - 1]} {inicio.year}'
    if modo == 'anio':
        return str(inicio.year)
    return f'{_etiqueta_dia(inicio.date())} – {_etiqueta_dia(ultimo.date())}'


def _variacion(actual, anterior):
    anterior = Decimal('0') if anterior is None else Decimal(anterior)
    if anterior == 0:
        return {
            'disponible': False,
            'texto': 'Sin comparación disponible',
            'sube': False,
            'baja': False,
        }
    porcentaje = (
        ((Decimal('0') if actual is None else Decimal(actual)) - anterior) / anterior * Decimal('100')
    ).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return {
        'disponible': True,
        'porcentaje': int(porcentaje),
        'anterior': anterior,
        'texto': f'{int(porcentaje):+}%',
        'sube': porcentaje > 0,
        'baja': porcentaje < 0,
    }


def _indicadores(request, periodo, puede_productos):
    if not _puede_ver(request, Pedido):
        return {'permitido': False}

    filas = Pedido.objects.filter(
        fecha_pedido__gte=periodo['anterior_inicio'],
        fecha_pedido__lt=periodo['fin'],
    ).values_list('fecha_pedido', 'total_monto', 'estado')
    actual = _corte(filas, periodo['inicio'], periodo['fin'])
    previo = _corte(filas, periodo['anterior_inicio'], periodo['anterior_fin'])
    monto = _suma_confirmada(actual)
    monto_previo = _suma_confirmada(previo)
    confirmados = _cuenta_confirmada(actual)
    confirmados_previo = _cuenta_confirmada(previo)
    ticket = (monto / confirmados).quantize(Decimal('1'), rounding=ROUND_HALF_UP) if confirmados else Decimal('0')
    ticket_previo = (
        (monto_previo / confirmados_previo).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        if confirmados_previo else Decimal('0')
    )
    historico = Pedido.objects.filter(estado__in=ESTADOS_VENTA).aggregate(total=Sum('total_monto'))['total']
    unidades = None
    unidades_previas = None
    if puede_productos:
        claves = _claves_producto_visibles(request)
        unidades = _unidades(claves, periodo['inicio'], periodo['fin'])
        unidades_previas = _unidades(claves, periodo['anterior_inicio'], periodo['anterior_fin'])
    return {
        'permitido': True,
        'mes': monto,
        'monto': monto,
        'historico': _decimal(historico),
        'confirmados': confirmados,
        'ticket': ticket,
        'unidades': unidades,
        'variacion_monto': _variacion(monto, monto_previo),
        'variacion_pedidos': _variacion(confirmados, confirmados_previo),
        'variacion_ticket': _variacion(ticket, ticket_previo),
        'variacion_unidades': _variacion(unidades or 0, unidades_previas or 0) if puede_productos else None,
    }


def _corte(filas, inicio, fin):
    return [
        (fecha, monto, estado)
        for fecha, monto, estado in filas
        if inicio <= timezone.localtime(fecha, ZONA_VENTAS) < fin
    ]


def _suma_confirmada(filas):
    total = Decimal('0')
    for _fecha, monto, estado in filas:
        if estado in ESTADOS_VENTA:
            total += monto or Decimal('0')
    return total


def _cuenta_confirmada(filas):
    return sum(1 for _fecha, _monto, estado in filas if estado in ESTADOS_VENTA)


def _unidades(claves, inicio, fin):
    if not claves:
        return 0
    total = ItemPedido.objects.filter(
        pedido__estado__in=ESTADOS_VENTA,
        pedido__fecha_pedido__gte=inicio,
        pedido__fecha_pedido__lt=fin,
        producto_modelo__in=claves,
    ).aggregate(total=Sum('cantidad'))['total']
    return int(total or 0)


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


def _lista_pedidos(request):
    if not _puede_ver(request, Pedido):
        return {'permitido': False, 'recientes': []}

    totales = Pedido.objects.aggregate(
        registrados=Count('pk'),
        pendientes=Count('pk', filter=Q(estado='PENDIENTE')),
    )
    registrados = totales['registrados'] or 0

    def leer(inicio, cantidad):
        return list(
            Pedido.objects.select_related('usuario').order_by('-fecha_pedido', '-pk')[inicio:inicio + cantidad]
        )

    recientes, paginacion = _pagina(request, 'pedidos_pagina', registrados, leer)
    return {
        'permitido': True,
        'registrados': registrados,
        'pendientes': totales['pendientes'] or 0,
        'recientes': recientes,
        'paginacion': paginacion,
    }


def _productos(request):
    conteo, con_alerta = _conteo_inventario(request)
    if not conteo['permitido']:
        return {'permitido': False, 'alertas': []}

    def leer(inicio, cantidad):
        return _leer_alertas(con_alerta, inicio, cantidad)

    alertas, paginacion = _pagina(
        request, 'alertas_pagina', conteo['stock_bajo'] + conteo['agotados'], leer,
    )
    conteo.update({
        'alertas': alertas,
        'alertas_totales': conteo['stock_bajo'] + conteo['agotados'],
        'paginacion': paginacion,
    })
    return conteo


def _conteo_inventario(request):
    modelos = [modelo for modelo in MODELOS_PRODUCTO if _puede_ver(request, modelo)]
    if not modelos:
        return {'permitido': False}, []

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
    return {
        'permitido': True,
        'disponibles': disponibles,
        'stock_bajo': stock_bajo,
        'agotados': agotados,
    }, con_alerta


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


def _graficos(request, puede_pedidos, puede_productos, periodo):
    ventas = _grafico_ventas(periodo) if puede_pedidos else None
    estados = _grafico_estados(periodo) if puede_pedidos else None
    lineas = _lineas_periodo(_claves_producto_visibles(request), periodo) if puede_pedidos and puede_productos else None
    vendidos = _grafico_vendidos(lineas) if lineas is not None else None
    categorias = _grafico_categorias(lineas) if lineas is not None else None
    unidades = _grafico_unidades(lineas, periodo) if lineas is not None else None
    return {
        'ventas': ventas,
        'estados': estados,
        'vendidos': vendidos,
        'categorias': categorias,
        'unidades': unidades,
        'resumen': _resumen_visual(ventas, estados, categorias) if puede_pedidos else None,
        'cargar': bool(puede_pedidos),
    }


def _resumen_visual(ventas, estados, categorias):
    """Arma el resumen con puntos que los gráficos ya calcularon."""
    mejor = None
    if ventas and ventas.get('puntos'):
        candidato = max(ventas['puntos'], key=lambda punto: punto['valor'])
        if candidato['valor']:
            mejor = candidato
    categoria = categorias['puntos'][0] if categorias and categorias.get('puntos') else None
    pedidos = sum(punto['valor'] for punto in estados['puntos']) if estados and estados.get('puntos') else 0
    return {'mejor': mejor, 'categoria': categoria, 'pedidos': pedidos}


def _cubetas(periodo):
    inicio = periodo['inicio']
    fin = periodo['fin']
    agrupacion = periodo['agrupacion']
    cubetas = []
    if agrupacion == 'dia':
        dia = inicio.date()
        ultimo = (fin - timedelta(seconds=1)).date()
        while dia <= ultimo:
            cubetas.append((
                _inicio_dia(dia),
                _inicio_dia(dia + timedelta(days=1)),
                f'{dia.day} {_MESES[dia.month - 1]}',
            ))
            dia += timedelta(days=1)
        return cubetas
    if agrupacion == 'semana':
        cursor = inicio
        while cursor < fin:
            siguiente = min(cursor + timedelta(days=7), fin)
            hasta = timezone.localtime(siguiente - timedelta(seconds=1), ZONA_VENTAS)
            cubetas.append((cursor, siguiente, _etiqueta_semana(cursor, hasta)))
            cursor = siguiente
        return cubetas
    cursor = inicio
    limite = timezone.localtime(fin - timedelta(seconds=1), ZONA_VENTAS)
    while (cursor.year, cursor.month) <= (limite.year, limite.month):
        siguiente_mes = 1 if cursor.month == 12 else cursor.month + 1
        siguiente_anio = cursor.year + 1 if cursor.month == 12 else cursor.year
        siguiente = datetime(siguiente_anio, siguiente_mes, 1, tzinfo=ZONA_VENTAS)
        cubetas.append((
            cursor,
            siguiente,
            f'{_MESES[cursor.month - 1]} {cursor.year}',
        ))
        cursor = siguiente
    return cubetas


def _etiqueta_semana(inicio, hasta):
    if inicio.month == hasta.month:
        return f'{inicio.day}–{hasta.day} {_MESES[inicio.month - 1]}'
    return f'{inicio.day} {_MESES[inicio.month - 1]}–{hasta.day} {_MESES[hasta.month - 1]}'


def _cubeta_de(fecha, cubetas):
    local = timezone.localtime(fecha, ZONA_VENTAS)
    for inicio, fin, _etiqueta in cubetas:
        if inicio <= local < fin:
            return inicio
    return None


def _grafico_ventas(periodo):
    cubetas = _cubetas(periodo)
    totales = {inicio: Decimal('0') for inicio, _fin, _etiqueta in cubetas}
    filas = Pedido.objects.filter(
        estado__in=ESTADOS_VENTA,
        fecha_pedido__gte=periodo['inicio'],
        fecha_pedido__lt=periodo['fin'],
    ).values_list('fecha_pedido', 'total_monto')
    for fecha, monto in filas:
        clave = _cubeta_de(fecha, cubetas)
        if clave in totales:
            totales[clave] += monto or Decimal('0')
    puntos = [
        {'etiqueta': etiqueta, 'valor': _pesos(totales[inicio])}
        for inicio, _fin, etiqueta in cubetas
    ]
    return {
        'vacio': not any(punto['valor'] for punto in puntos),
        'titulo': _TITULO_VENTAS[periodo['agrupacion']],
        'puntos': puntos,
    }


def _grafico_estados(periodo):
    totales = Pedido.objects.filter(
        fecha_pedido__gte=periodo['inicio'],
        fecha_pedido__lt=periodo['fin'],
    ).aggregate(**{
        estado: Count('pk', filter=Q(estado=estado))
        for estado, _etiqueta in Pedido.ESTADOS
    })
    puntos = [
        {'etiqueta': etiqueta, 'clave': estado, 'valor': totales[estado] or 0}
        for estado, etiqueta in Pedido.ESTADOS
    ]
    if not any(punto['valor'] for punto in puntos):
        return {'vacio': True, 'puntos': puntos}
    return {'vacio': False, 'puntos': puntos}


def _lineas_periodo(claves, periodo):
    if not claves:
        return []
    return list(
        ItemPedido.objects.filter(
            pedido__estado__in=ESTADOS_VENTA,
            pedido__fecha_pedido__gte=periodo['inicio'],
            pedido__fecha_pedido__lt=periodo['fin'],
            producto_modelo__in=claves,
            producto_pk__isnull=False,
        ).values_list(
            'pedido__fecha_pedido', 'cantidad', 'precio_unitario',
            'producto_modelo', 'producto_pk', 'producto_nombre', 'producto_tipo',
        )
    )


def _grafico_vendidos(lineas):
    grupos = {}
    for _fecha, cantidad, precio, modelo, pk, nombre, tipo in lineas:
        clave = (modelo, pk)
        grupo = grupos.setdefault(clave, {
            'unidades': 0,
            'ingresos': Decimal('0'),
            'nombre': nombre,
            'tipo': tipo,
        })
        grupo['unidades'] += int(cantidad or 0)
        grupo['ingresos'] += (precio or Decimal('0')) * (cantidad or 0)
    if not grupos:
        return {'vacio': True, 'puntos': []}
    ordenados = sorted(grupos.items(), key=lambda item: (-item[1]['unidades'], item[0][0], item[0][1]))
    ordenados = ordenados[:LIMITE_MAS_VENDIDOS]
    ids = {}
    for (modelo, pk), _grupo in ordenados:
        ids.setdefault(modelo, set()).add(pk)
    nombres = {}
    for clave, pks in ids.items():
        modelo = _MODELOS_DE_PRODUCTO.get(clave)
        if modelo is None:
            continue
        for pk, nombre, categoria in modelo.objects.filter(pk__in=pks).values_list('pk', 'nombre', 'categoria'):
            nombres[(clave, pk)] = (nombre, categoria)
    base = []
    for (modelo, pk), grupo in ordenados:
        nombre, tipo = nombres.get((modelo, pk), (grupo['nombre'], grupo['tipo']))
        base.append((pk, nombre, tipo, grupo['unidades'], _pesos(grupo['ingresos'])))
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


def _grafico_categorias(lineas):
    totales = {}
    for _fecha, cantidad, precio, _modelo, _pk, _nombre, tipo in lineas:
        categoria = (tipo or '').strip()
        if not categoria:
            continue
        totales[categoria] = totales.get(categoria, Decimal('0')) + (precio or Decimal('0')) * (cantidad or 0)
    if not totales:
        return {'vacio': True, 'puntos': []}
    puntos = [
        {'etiqueta': nombre, 'valor': _pesos(monto)}
        for nombre, monto in sorted(totales.items(), key=lambda item: (-item[1], item[0]))
    ]
    return {'vacio': False, 'puntos': puntos}


def _grafico_unidades(lineas, periodo):
    cubetas = _cubetas(periodo)
    totales = {inicio: 0 for inicio, _fin, _etiqueta in cubetas}
    for fecha, cantidad, _precio, _modelo, _pk, _nombre, _tipo in lineas:
        clave = _cubeta_de(fecha, cubetas)
        if clave in totales:
            totales[clave] += int(cantidad or 0)
    puntos = [
        {'etiqueta': etiqueta, 'valor': totales[inicio]}
        for inicio, _fin, etiqueta in cubetas
    ]
    return {
        'vacio': not any(punto['valor'] for punto in puntos),
        'titulo': _TITULO_UNIDADES[periodo['agrupacion']],
        'puntos': puntos,
    }
