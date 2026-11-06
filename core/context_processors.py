from django.conf import settings

from core.chatbot.assistant_config import get_asistente_config

from .models import *


def extras_context(request):
    asistente = get_asistente_config()
    context = {
        'cart_item_count': 0,
        'favorite_item_count': 0,
        'asistente_config': asistente,
        'contacto_email': settings.CONTACTO_EMAIL,
        'direccion_publica': settings.DIRECCION_PUBLICA,
        'mapa_embed': settings.MAPA_EMBED,
        'mapa_enlace': settings.MAPA_ENLACE,
    }
    if request.user.is_authenticated:
        carrito, created = Carrito.objects.get_or_create(usuario=request.user)
        context['cart_item_count'] = carrito.items.count()
            
        context['favorite_item_count'] = Favorito.objects.filter(usuario=request.user).count()

    usuario = request.user
    if usuario.is_authenticated and usuario.is_active and usuario.is_staff:
        from core.alertas_stock import aviso_visible, problemas, resumen

        filas = problemas(request)
        context['alertas_stock'] = resumen(filas)
        context['mostrar_aviso_stock'] = aviso_visible(request, filas)

    return context