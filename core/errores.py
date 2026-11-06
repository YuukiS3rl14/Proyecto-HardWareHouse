"""Páginas 404 y 500 sin context processors ni consultas a la base."""
from django.http import HttpResponse
from django.template import loader


def _html(plantilla, datos):
    return loader.get_template(plantilla).render(datos)


def pagina_no_encontrada(request, exception):
    return HttpResponse(
        _html('404.html', {
            'titulo': 'Página no encontrada',
            'detalle': 'La página que buscas no existe o fue movida.',
            'icono': 'fa-search',
            'explorar': True,
        }),
        status=404,
    )


def producto_no_encontrado():
    return HttpResponse(
        _html('404.html', {
            'titulo': 'Producto no encontrado',
            'detalle': 'El producto que buscas no existe o ya no está disponible.',
            'icono': 'fa-box-open',
            'explorar': True,
        }),
        status=404,
    )


def error_interno(request):
    """Django ya registró la excepción en el log django.request antes de llegar aquí."""
    return HttpResponse(_html('500.html', {}), status=500)
