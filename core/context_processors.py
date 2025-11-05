from .models import *

def extras_context(request):
    """
    Context processor para añadir contadores de carrito y favoritos a todas las plantillas.
    """
    context = {
        'cart_item_count': 0,
        'favorite_item_count': 0,
    }
    if request.user.is_authenticated:
        # Contar items del carrito
        carrito, created = Carrito.objects.get_or_create(usuario=request.user)
        context['cart_item_count'] = carrito.items.count()
            
        # Contar items de favoritos
        context['favorite_item_count'] = Favorito.objects.filter(usuario=request.user).count()
        
    return context