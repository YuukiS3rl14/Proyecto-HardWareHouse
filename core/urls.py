from django.urls import path
from .views import *

urlpatterns = [
    path('', mostrarIndex, name='index'),
    path('armado/', mostrarArmado, name='armado'),
    path('carrito/', mostrarCarrito, name='carrito'),
    path('checkout/', mostrarCheckout, name='checkout'),
    path('contacto/', mostrarContacto, name='contacto'),
    path('detalle/', mostrarDetalle, name='detalle'),
    path('tienda/', mostrarTienda, name='tienda'),
    path('login/', mostrarLogin, name='login'),
    path('registro/', mostrarRegistro, name='registro'),
]