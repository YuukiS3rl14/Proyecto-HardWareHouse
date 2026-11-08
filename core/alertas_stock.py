"""Estados de stock calculados al consultar. No descuenta inventario ni guarda alertas."""
from dataclasses import dataclass

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import render
from django.urls import reverse

from core.catalogo.registry import CATALOGO_MODELOS, MODEL_BY_API_NAME
from core.imagenes import url_imagen_producto
from core.piezas_demo import sin_demo

AGOTADO = 'AGOTADO'
CRITICO = 'CRITICO'
ADVERTENCIA = 'ADVERTENCIA'
NORMAL = 'NORMAL'

ETIQUETAS = {
    AGOTADO: 'Agotado',
    CRITICO: 'Crítico',
    ADVERTENCIA: 'Advertencia',
    NORMAL: 'Normal',
}
PRIORIDAD = {AGOTADO: 0, CRITICO: 1, ADVERTENCIA: 2, NORMAL: 3}
CLAVE_SESION = 'hw_stock_aviso'
POR_PAGINA = 20


def estado_stock(stock, minimo, advertencia):
    """Cero es agotado. El resto usa los umbrales del propio producto."""
    if stock <= 0:
        return AGOTADO
    if stock <= minimo:
        return CRITICO
    if stock <= advertencia:
        return ADVERTENCIA
    return NORMAL


def unidades_para_normal(stock, advertencia):
    if stock > advertencia:
        return 0
    return advertencia + 1 - stock


@dataclass
class FilaAlerta:
    modelo: str
    model_name: str
    pk: int
    nombre: str
    categoria: str
    stock: int
    stock_minimo: int
    stock_advertencia: int
    estado: str
    etiqueta: str
    unidades: int
    imagen_url: str
    identificador: str
    puede_editar: bool = False
    url_edicion: str = ''

    @property
    def clave(self):
        return (self.modelo, self.pk)


def _filas():
    filas = []
    for modelo, model_name in CATALOGO_MODELOS:
        consulta = sin_demo(
            modelo.objects.filter(stock__lte=F('stock_advertencia')).select_related('proveedor')
        )
        for producto in consulta:
            estado = estado_stock(producto.stock, producto.stock_minimo, producto.stock_advertencia)
            if estado == NORMAL:
                continue
            filas.append(FilaAlerta(
                modelo=modelo._meta.model_name,
                model_name=model_name,
                pk=producto.pk,
                nombre=producto.nombre,
                categoria=producto.categoria,
                stock=producto.stock,
                stock_minimo=producto.stock_minimo,
                stock_advertencia=producto.stock_advertencia,
                estado=estado,
                etiqueta=ETIQUETAS[estado],
                unidades=unidades_para_normal(producto.stock, producto.stock_advertencia),
                imagen_url=url_imagen_producto(producto),
                identificador=f'{model_name}:{producto.pk}',
            ))
    filas.sort(key=lambda fila: (PRIORIDAD[fila.estado], fila.stock, fila.nombre.lower(), fila.pk))
    return filas


def problemas(request):
    if not hasattr(request, '_problemas_stock'):
        request._problemas_stock = _filas()
    return request._problemas_stock


def resumen(filas):
    agotados = sum(1 for fila in filas if fila.estado == AGOTADO)
    criticos = sum(1 for fila in filas if fila.estado == CRITICO)
    advertencia = sum(1 for fila in filas if fila.estado == ADVERTENCIA)
    return {
        'agotados': agotados,
        'criticos': criticos,
        'advertencia': advertencia,
        'afectados': agotados + criticos + advertencia,
    }


def firma(filas):
    return [
        [fila.modelo, fila.pk, fila.estado]
        for fila in sorted(filas, key=lambda fila: (fila.modelo, fila.pk))
    ]


def debe_mostrar(actual, guardada):
    if not actual:
        return False
    if not guardada:
        return True
    previo = {(item[0], item[1]): item[2] for item in guardada}
    for modelo, pk, estado in actual:
        anterior = previo.get((modelo, pk))
        if anterior is None or PRIORIDAD[estado] < PRIORIDAD[anterior]:
            return True
    return False


def aviso_visible(request, filas):
    if hasattr(request, '_aviso_stock'):
        return request._aviso_stock
    visible = False
    usuario = request.user
    if usuario.is_authenticated and usuario.is_active and usuario.is_staff and filas:
        actual = firma(filas)
        visible = debe_mostrar(actual, request.session.get(CLAVE_SESION))
        if visible:
            request.session[CLAVE_SESION] = actual
            request.session.modified = True
    request._aviso_stock = visible
    return visible


def _puede_editar(usuario, model_name):
    modelo = MODEL_BY_API_NAME[model_name]
    return usuario.has_perm(f'{modelo._meta.app_label}.change_{modelo._meta.model_name}')


def _url_edicion(fila):
    return reverse(f'admin:core_{fila.modelo}_change', args=[fila.pk])


@login_required
def vista_alertas_stock(request):
    if not request.user.is_active or not request.user.is_staff:
        raise PermissionDenied('Solo el personal puede ver las alertas de stock.')
    todas = problemas(request)
    estado = request.GET.get('estado') or 'todos'
    if estado not in ('todos', 'agotado', 'critico', 'advertencia'):
        estado = 'todos'
    categoria = (request.GET.get('categoria') or '').strip()
    texto = (request.GET.get('q') or '').strip()
    mapa = {'agotado': AGOTADO, 'critico': CRITICO, 'advertencia': ADVERTENCIA}
    filas = todas
    if estado in mapa:
        filas = [fila for fila in filas if fila.estado == mapa[estado]]
    if categoria:
        filas = [fila for fila in filas if fila.categoria == categoria]
    if texto:
        needle = texto.lower()
        filas = [
            fila for fila in filas
            if needle in fila.nombre.lower() or needle in fila.identificador.lower() or needle == str(fila.pk)
        ]
    categorias = sorted({fila.categoria for fila in todas})
    paginador = Paginator(filas, POR_PAGINA)
    pagina = paginador.get_page(request.GET.get('page'))
    for fila in pagina.object_list:
        fila.puede_editar = _puede_editar(request.user, fila.model_name)
        fila.url_edicion = _url_edicion(fila) if fila.puede_editar else ''
    consulta = request.GET.copy()
    consulta.pop('page', None)
    return render(request, 'core/alertas_stock.html', {
        'resumen': resumen(todas),
        'pagina': pagina,
        'estado': estado,
        'categoria': categoria,
        'q': texto,
        'categorias': categorias,
        'consulta': consulta.urlencode(),
    })
