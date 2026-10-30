from django.contrib.auth.views import LoginView
from django.urls import path

from core.chatbot.api import (
    armado_estado_api,
    armado_revalidar_api,
    chat_sesion_restaurar_api,
    catalogo_buscar_api,
    catalogo_metadata_api,
    catalogo_presupuesto_api,
    catalogo_total_armado_api,
    chat_asistente_api,
    chat_asistente_config_api,
)

from .views import *

urlpatterns = [
    path('', mostrarIndex, name='index'),
    path('index/', mostrarIndex, name='index'),
    path('armado/', mostrarArmado, name='armado'),
    path('armado/recomendar/', recomendar_armado, name='recomendar_armado'),
    path('armado/evaluar/', evaluar_armado, name='evaluar_armado'),
    path('armado/exportar/', exportar_armado, name='exportar_armado'),
    path('carrito/', mostrarCarrito, name='carrito'),
    path('checkout/', mostrarCheckout, name='checkout'),
    path('contacto/', mostrarContacto, name='contacto'),
    path('sobre-nosotros/', mostrarSobreNosotros, name='sobrenosotros'),
    path('detalle/<str:model_name>/<int:pk>/', mostrarDetalle, name='detalle'),
    path('tienda/', mostrarTienda, name='tienda'),
    path('catalogo/productos.csv', descargar_productos_csv, name='descargar_productos_csv'),
    path('api/chat/', chat_asistente_api, name='chat_api'),
    path('api/chat/config/', chat_asistente_config_api, name='chat_asistente_config_api'),
    path('api/chat/armado/estado/', armado_estado_api, name='armado_estado_api'),
    path('api/chat/armado/revalidar/', armado_revalidar_api, name='armado_revalidar_api'),
    path('api/chat/sesion/restaurar/', chat_sesion_restaurar_api, name='chat_sesion_restaurar_api'),
    path('api/catalogo/buscar/', catalogo_buscar_api, name='catalogo_buscar_api'),
    path('api/catalogo/presupuesto/', catalogo_presupuesto_api, name='catalogo_presupuesto_api'),
    path('api/catalogo/total-armado/', catalogo_total_armado_api, name='catalogo_total_armado_api'),
    path('api/catalogo/metadata/', catalogo_metadata_api, name='catalogo_metadata_api'),
    path('registro/', mostrarRegistro, name='registro'),
    path('perfil/', verPerfil, name='perfil'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),

    # URLs del Carrito
    path('carrito/agregar/', agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/agregar-armado/', agregar_armado_al_carrito, name='agregar_armado_al_carrito'),
    path('carrito/eliminar/<int:item_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/actualizar/<int:item_id>/', actualizar_carrito, name='actualizar_carrito'),

    # URLs de Favoritos
    path('favoritos/', mostrar_favoritos, name='favoritos'),
    path('favoritos/toggle/', toggle_favorito, name='toggle_favorito'),
    path('favoritos/eliminar/<int:fav_id>/', eliminar_favorito, name='eliminar_favorito'),

    # URL de Comentarios
    path('comentario/agregar/<str:model_name>/<int:pk>/', agregar_comentario, name='agregar_comentario'),

    # URLs de Pedidos
    path('pedidos/', mis_pedidos, name='mis_pedidos'),
    path('pedidos/<int:pedido_id>/', detalle_pedido, name='detalle_pedido'),
    path('pedidos/cancelar/<int:pedido_id>/', cancelar_pedido, name='cancelar_pedido'),
    path('pedidos/boleta/<int:pedido_id>/', ver_boleta, name='ver_boleta'),

    path('payment/success/', paymentSuccess, name='payment_success'),
    path('payment/failed/', paymentFailed, name='payment_failed'),
]