from django import template
from django.urls import reverse

register = template.Library()

COMPONENTES = (
    'core.procesador',
    'core.tarjetagrafica',
    'core.memoriaram',
    'core.placamadre',
    'core.almacenamientossd',
    'core.almacenamientohdd',
    'core.gabinete',
    'core.fuentedepoder',
    'core.refrigeracioncooler',
    'core.ventilador',
)

GRUPOS = (
    ('Catálogo y componentes', COMPONENTES + ('core.proveedor',), 'fas fa-microchip'),
    ('Pedidos y ventas', (
        'core.pedido',
        'core.pagoboleta',
        'ipn.paypalipn',
    ), 'fas fa-receipt'),
    ('Usuarios y permisos', (
        'auth.user',
        'auth.group',
    ), 'fas fa-user-shield'),
)


def _modelos(side_menu):
    encontrados = {}
    for app in side_menu or []:
        for modelo in app.get('models', []):
            clave = (modelo.get('model_str') or '').lower()
            if clave:
                encontrados[clave] = modelo
    return encontrados


def _tomar(encontrados, claves, usados):
    modelos = []
    for clave in claves:
        modelo = encontrados.get(clave)
        if modelo:
            modelos.append(modelo)
            usados.add(clave)
    return modelos


@register.simple_tag
def accesos_principales(side_menu):
    """Cuatro accesos del panel, tomados del menú que Jazzmin ya filtró."""
    encontrados = _modelos(side_menu)
    accesos = []

    pedido = encontrados.get('core.pedido')
    if pedido and pedido.get('url'):
        accesos.append({
            'clave': 'pedidos',
            'nombre': 'Pedidos',
            'url': pedido['url'],
            'icono': 'fas fa-receipt',
        })

    if any(clave in encontrados for clave in COMPONENTES):
        accesos.append({
            'clave': 'inventario',
            'nombre': 'Inventario',
            'url': reverse('admin:index') + '#hw-alertas',
            'icono': 'fas fa-exclamation-triangle',
        })
        for clave in COMPONENTES:
            producto = encontrados.get(clave)
            if producto and producto.get('url'):
                accesos.append({
                    'clave': 'productos',
                    'nombre': 'Productos',
                    'url': producto['url'],
                    'icono': 'fas fa-box',
                })
                break

    usuario = encontrados.get('auth.user')
    if usuario and usuario.get('url'):
        accesos.append({
            'clave': 'usuarios',
            'nombre': 'Usuarios',
            'url': usuario['url'],
            'icono': 'fas fa-user',
        })
    return accesos


def _ruta(url):
    return (url or '').split('#', 1)[0].rstrip('/') or '/'


def _coincide(url, ruta):
    if not url or not ruta or '#' in url:
        return False
    base = _ruta(url)
    if base == '/admin':
        return ruta == '/admin'
    return ruta == base or ruta.startswith(base + '/')


def _grupo(nombre, icono, modelos, ruta):
    return {
        'nombre': nombre,
        'icono': icono,
        'modelos': modelos,
        'abierto': any(_coincide(modelo.get('url'), ruta) for modelo in modelos),
    }


@register.simple_tag(takes_context=True)
def agrupar_menu(context, side_menu):
    """Agrupa el menú que Jazzmin ya filtró por permisos. No oculta modelos desconocidos."""
    request = context.get('request') if context else None
    ruta = _ruta(getattr(request, 'path', ''))
    encontrados = _modelos(side_menu)
    usados = set()
    grupos = []
    for nombre, claves, icono in GRUPOS:
        if nombre == 'Pedidos y ventas':
            inventario = []
            if any(clave in encontrados for clave in COMPONENTES):
                inventario.append({
                    'name': 'Alertas de inventario',
                    'url': reverse('admin:index') + '#hw-alertas',
                    'icon': 'fas fa-exclamation-triangle',
                })
            inventario.extend(_tomar(encontrados, ('core.movimientostock',), usados))
            if inventario:
                grupos.append(_grupo('Inventario', 'fas fa-boxes', inventario, ruta))
        modelos = _tomar(encontrados, claves, usados)
        if modelos:
            grupos.append(_grupo(nombre, icono, modelos, ruta))
    restantes = [modelo for clave, modelo in encontrados.items() if clave not in usados]
    if restantes:
        grupos.append(_grupo('Otros', 'fas fa-ellipsis-h', restantes, ruta))
    return grupos


@register.filter
def busqueda_visible(search_model, user):
    """Muestra el buscador solo si el usuario puede ver o cambiar ese modelo."""
    if not getattr(user, 'is_authenticated', False):
        return False
    partes = [parte for parte in (search_model or {}).get('search_url', '').split('/') if parte]
    try:
        indice = partes.index('admin')
    except ValueError:
        return False
    if len(partes) < indice + 3:
        return False
    app = partes[indice + 1]
    modelo = partes[indice + 2].replace('-', '')
    return user.has_perm(f'{app}.view_{modelo}') or user.has_perm(f'{app}.change_{modelo}')
