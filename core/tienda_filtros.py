from decimal import Decimal

from django.db.models import Q

from .models import Proveedor

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
            return Q(precio__gte=banda['minimo'])
        return Q(precio__gte=banda['minimo'], precio__lt=banda['maximo'])
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
        categorias.update(
            modelo.objects.order_by().values_list('categoria', flat=True).distinct()
        )
        proveedor_ids.update(
            modelo.objects.order_by().values_list('proveedor_id', flat=True).distinct()
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
        productos.sort(key=lambda item: (item[0].precio, item[0].nombre.casefold(), item[0].id))
    elif orden == 'precio_desc':
        productos.sort(key=lambda item: (-item[0].precio, item[0].nombre.casefold(), item[0].id))
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
