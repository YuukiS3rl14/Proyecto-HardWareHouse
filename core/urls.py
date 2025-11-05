from django.urls import path
from .views import *

urlpatterns = [
    path('', mostrarIndex, name='index'),
    path('armado/', mostrarArmado, name='armado'),
    path('carrito/', mostrarCarrito, name='carrito'),
    path('checkout/', mostrarCheckout, name='checkout'),
    path('contacto/', mostrarContacto, name='contacto'),
    path('detalle/<str:model_name>/<int:pk>/', mostrarDetalle, name='detalle'),
    path('tienda/', mostrarTienda, name='tienda'),
    path('registro/', mostrarRegistro, name='registro'),
    path('perfil/', verPerfil, name='perfil'),

    # URLs del Carrito
    path('carrito/agregar/', agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/eliminar/<int:item_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/actualizar/<int:item_id>/', actualizar_carrito, name='actualizar_carrito'),

    # URLs de Favoritos
    path('favoritos/', mostrar_favoritos, name='favoritos'),
    path('favoritos/toggle/', toggle_favorito, name='toggle_favorito'),
    path('favoritos/eliminar/<int:fav_id>/', eliminar_favorito, name='eliminar_favorito'),

    # URL de Comentarios
    path('comentario/agregar/<str:model_name>/<int:pk>/', agregar_comentario, name='agregar_comentario'),
]