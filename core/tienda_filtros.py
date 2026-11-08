from decimal import Decimal
from urllib.parse import urlencode

from django.db.models import Q

from .models import Proveedor, expresion_precio_vigente
from .piezas_demo import sin_demo

# El límite superior queda fuera de la banda, salvo «1.000.000 o más».
# Así 50.000 pertenece a 50–100 mil y 1.000.000 pertenece a 1 millón o más.
BANDAS_PRECIO = (
    {'codigo': '0-50', 'etiqueta': '$0 – $50.000', 'minimo': Decimal('0'), 'maximo': Decimal('50000')},
    {'codigo': '50-100', 'etiqueta': '$50.000 – $100.000', 'minimo': Decimal('50000'), 'maximo': Decimal('100000')},
    {'codigo': '100-250', 'etiqueta': '$100.000 – $250.000', 'minimo': Decimal('100000'), 'maximo': Decimal('250000')},
    {'codigo': '250-500', 'etiqueta': '$250.000 – $500.000', 'minimo': Decimal('250000'), 'maximo': Decimal('500000')},
    {'codigo': '500-1000', 'etiqueta': '$500.000 – $1.000.000', 'minimo': Decimal('500000'), 'maximo': Decimal('1000000')},
    {'codigo': '1000+', 'etiqueta': '$1.000.000 o más', 'minimo': Decimal('1000000'), 'maximo': None},
)

ORDENES = (
    ('relevancia', 'Relevancia'),
    ('precio_asc', 'Precio: menor a mayor'),
    ('precio_desc', 'Precio: mayor a menor'),
    ('nombre', 'Nombre'),
)
ORDENES_VALIDAS = {codigo for codigo, _etiqueta in ORDENES}


def filtro_precio(codigo):
    for banda in BANDAS_PRECIO:
        if banda['codigo'] != codigo:
            continue
        if banda['maximo'] is None:
            return Q(_precio_vigente__gte=banda['minimo'])
        return Q(_precio_vigente__gte=banda['minimo'], _precio_vigente__lt=banda['maximo'])
    return None


def ids_validos(valores):
    ids = []
    for valor in valores:
        try:
            ids.append(int(valor))
        except (TypeError, ValueError):
            continue
    return ids


def opciones_catalogo(modelos):
    """Categorías y marcas que ya tienen productos, sin repetir."""
    categorias = set()
    proveedor_ids = set()
    for modelo in modelos:
        visibles = sin_demo(modelo.objects.all())
        categorias.update(
            visibles.order_by().values_list('categoria', flat=True).distinct()
        )
        proveedor_ids.update(
            visibles.order_by().values_list('proveedor_id', flat=True).distinct()
        )
    categorias.discard(None)
    categorias.discard('')
    proveedor_ids.discard(None)
    proveedores = Proveedor.objects.filter(pk__in=proveedor_ids).order_by('nombre')
    return sorted(categorias, key=str.casefold), proveedores


def ordenar_catalogo(productos, orden, consulta):
    consulta = (consulta or '').strip().casefold()
    if orden not in ORDENES_VALIDAS:
        orden = 'relevancia'

    if orden == 'precio_asc':
        productos.sort(key=lambda item: (item[0].precio_vigente, item[0].nombre.casefold(), item[0].id))
    elif orden == 'precio_desc':
        productos.sort(key=lambda item: (-item[0].precio_vigente, item[0].nombre.casefold(), item[0].id))
    elif orden == 'nombre':
        productos.sort(key=lambda item: (item[0].nombre.casefold(), item[0].id))
    else:
        productos.sort(key=lambda item: _clave_relevancia(item[0], consulta))
    return productos


def _clave_relevancia(producto, consulta):
    if not consulta:
        return (-producto.id,)
    nombre = producto.nombre.casefold()
    marca = producto.proveedor.nombre.casefold()
    categoria = (producto.categoria or '').casefold()
    if nombre.startswith(consulta):
        rango = 0
    elif consulta in nombre:
        rango = 1
    elif consulta in marca:
        rango = 2
    elif consulta in categoria:
        rango = 3
    else:
        rango = 4
    return (rango, nombre, producto.id)


def campo_novedad(modelo):
    """Fecha real de alta o actualización. No usa el id como sustituto."""
    nombres = {campo.name for campo in modelo._meta.concrete_fields}
    for nombre in ('actualizado_en', 'creado_en'):
        if nombre in nombres:
            return nombre
    return None


def catalogo_tiene_fechas(modelos) -> bool:
    return all(campo_novedad(modelo) for modelo in modelos)


# origen=home marca la llegada desde Home. Se consume al cambiar categoría o
# proveedor. heredado_* es la foto de esa llegada y solo viaja en el envío de Aplicar.
_CLAVES_DE_ENVIO = ('aplicar', 'heredado_q', 'heredado_categoria', 'heredado_proveedor')


def _limpio(valor):
    return (valor or '').strip()


def _ultimo_texto(valores):
    limpios = [_limpio(valor) for valor in valores if _limpio(valor)]
    return limpios[-1] if limpios else ''


def _ultimo_proveedor(valores):
    ids = ids_validos(_limpio(valor) for valor in valores)
    return str(ids[-1]) if ids else ''


def resolver_filtros_tienda(get):
    """Deja como máximo una categoría y un proveedor, y reemplaza lo heredado de Home."""
    categoria = _ultimo_texto(get.getlist('categoria'))
    proveedor = _ultimo_proveedor(get.getlist('proveedor'))
    consulta = _limpio(get.get('q'))
    precio = _limpio(get.get('precio'))
    if filtro_precio(precio) is None:
        precio = ''
    orden = _limpio(get.get('orden')) or 'relevancia'
    if orden not in ORDENES_VALIDAS:
        orden = 'relevancia'
    novedades = get.get('novedades') == '1'
    origen = 'home' if get.get('origen') == 'home' else ''
    pagina = '' if 'aplicar' in get else _limpio(get.get('page'))

    if origen == 'home' and 'aplicar' in get:
        heredado_q = _limpio(get.get('heredado_q'))
        heredado_categoria = _limpio(get.get('heredado_categoria'))
        heredado_proveedor = _ultimo_proveedor([get.get('heredado_proveedor')])
        cambio_categoria = categoria != heredado_categoria
        cambio_proveedor = proveedor != heredado_proveedor
        if cambio_categoria or cambio_proveedor:
            if consulta == heredado_q:
                consulta = ''
            if not cambio_categoria:
                categoria = ''
            if not cambio_proveedor:
                proveedor = ''
            origen = ''

    pares = []
    if consulta:
        pares.append(('q', consulta))
    if categoria:
        pares.append(('categoria', categoria))
    if proveedor:
        pares.append(('proveedor', proveedor))
    if precio:
        pares.append(('precio', precio))
    if orden != 'relevancia':
        pares.append(('orden', orden))
    if novedades:
        pares.append(('novedades', '1'))
    if origen:
        pares.append(('origen', origen))
    if pagina:
        pares.append(('page', pagina))

    return {
        'q': consulta,
        'categoria': categoria,
        'proveedor': proveedor,
        'precio': precio,
        'orden': orden,
        'novedades': novedades,
        'origen': origen,
        'page': pagina,
        'pares': pares,
        'categorias': [categoria] if categoria else [],
        'proveedores': [int(proveedor)] if proveedor else [],
    }


def debe_redirigir_filtros(get):
    """Redirige cuando la URL trae duplicados, valores inválidos o el envío de Aplicar."""
    if any(clave in get for clave in _CLAVES_DE_ENVIO):
        return True
    if 'origen' in get and get.get('origen') != 'home':
        return True
    categorias = [_limpio(valor) for valor in get.getlist('categoria') if _limpio(valor)]
    if len(categorias) > 1:
        return True
    proveedores = [_limpio(valor) for valor in get.getlist('proveedor') if _limpio(valor)]
    if len(proveedores) > 1 or (len(proveedores) == 1 and not ids_validos(proveedores)):
        return True
    precio = _limpio(get.get('precio'))
    if precio and filtro_precio(precio) is None:
        return True
    orden = _limpio(get.get('orden'))
    if orden and orden not in ORDENES_VALIDAS:
        return True
    return False


def consulta_sin(pares, clave):
    return urlencode([(k, v) for k, v in pares if k not in {clave, 'page'}])


def chips_de_filtros(estado, nombres_proveedor):
    pares = estado['pares']
    chips = []
    if estado['q']:
        chips.append({
            'nombre': 'búsqueda',
            'etiqueta': f'Búsqueda: {estado["q"]}',
            'consulta': consulta_sin(pares, 'q'),
        })
    if estado['categoria']:
        chips.append({
            'nombre': 'categoría',
            'etiqueta': estado['categoria'],
            'consulta': consulta_sin(pares, 'categoria'),
        })
    if estado['proveedor']:
        marca = nombres_proveedor.get(int(estado['proveedor']), estado['proveedor'])
        chips.append({
            'nombre': 'proveedor',
            'etiqueta': marca,
            'consulta': consulta_sin(pares, 'proveedor'),
        })
    if estado['precio']:
        etiqueta = next(
            (banda['etiqueta'] for banda in BANDAS_PRECIO if banda['codigo'] == estado['precio']),
            estado['precio'],
        )
        chips.append({
            'nombre': 'precio',
            'etiqueta': etiqueta,
            'consulta': consulta_sin(pares, 'precio'),
        })
    if estado['orden'] != 'relevancia':
        chips.append({
            'nombre': 'orden',
            'etiqueta': dict(ORDENES).get(estado['orden'], estado['orden']),
            'consulta': consulta_sin(pares, 'orden'),
        })
    if estado['novedades']:
        chips.append({
            'nombre': 'novedades',
            'etiqueta': 'Novedades',
            'consulta': consulta_sin(pares, 'novedades'),
        })
    return chips
