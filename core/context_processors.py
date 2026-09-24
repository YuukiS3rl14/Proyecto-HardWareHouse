from .models import *

def extras_context(request):
    context = {
        'cart_item_count': 0,
        'favorite_item_count': 0,
    }
    if request.user.is_authenticated:
        carrito, created = Carrito.objects.get_or_create(usuario=request.user)
        context['cart_item_count'] = carrito.items.count()
            
        context['favorite_item_count'] = Favorito.objects.filter(usuario=request.user).count()
        
    return context