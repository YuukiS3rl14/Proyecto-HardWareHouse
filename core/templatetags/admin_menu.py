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
    ('Catálogo y componentes', COMPONENTES + ('core.proveedor',)),
    ('Pedidos y ventas', (
        'core.pedido',
        'core.pagoboleta',
        'ipn.paypalipn',
    )),
    ('Clientes y actividad', (
        'core.carrito',
        'core.itemcarrito',
        'core.favorito',
        'core.comentario',
        'auth.user',
    )),
    ('Configuración', (
        'core.region',
        'core.comuna',
        'auth.group',
    )),
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


@register.simple_tag
def agrupar_menu(side_menu):
    """Agrupa el menú que Jazzmin ya filtró por permisos. No oculta modelos desconocidos."""
    encontrados = _modelos(side_menu)
    usados = set()
    grupos = []
    for nombre, claves in GRUPOS:
        modelos = _tomar(encontrados, claves, usados)
        if modelos:
            grupos.append({'nombre': nombre, 'modelos': modelos})
        if nombre == 'Catálogo y componentes' and any(clave in encontrados for clave in COMPONENTES):
            grupos.append({
                'nombre': 'Inventario',
                'modelos': [{
                    'name': 'Alertas de inventario',
                    'url': reverse('admin:index') + '#hw-alertas',
                    'icon': 'fas fa-exclamation-triangle',
                }],
            })
    restantes = [modelo for clave, modelo in encontrados.items() if clave not in usados]
    if restantes:
        grupos.append({'nombre': 'Otros', 'modelos': restantes})
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
