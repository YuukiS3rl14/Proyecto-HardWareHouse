from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import *

# Register your models here.

# 1. Registro de Modelos de Geografía y Categoría
admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(Categoria)


# 2. Configuración de Modelos de Productos
class ProductoAdmin(admin.ModelAdmin):
    
    exclude = ('categoria',) 

    list_display = ('nombre', 'categoria', 'precio', 'stock', 'imagen')
    list_filter = ('categoria',)
    list_editable = ('precio', 'stock')
    list_per_page = 20
    search_fields = ('nombre', 'descripcion', 'categoria')

    
admin.site.register(ProductoBase, ProductoAdmin)
admin.site.register(Procesador, ProductoAdmin)
admin.site.register(TarjetaGrafica, ProductoAdmin)
admin.site.register(MemoriaRam, ProductoAdmin)
admin.site.register(AlmacenamientoSSD, ProductoAdmin)
admin.site.register(AlmacenamientoHDD, ProductoAdmin)
admin.site.register(Gabinete, ProductoAdmin)
admin.site.register(FuenteDePoder, ProductoAdmin)
admin.site.register(RefrigeracionCooler, ProductoAdmin)
admin.site.register(Ventilador, ProductoAdmin)


# 3. Configuración de Carrito y Pedidos
class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0 

class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_creacion', 'get_total_precio')
    list_per_page = 20
    inlines = [ItemCarritoInline]
    readonly_fields = ('get_total_precio',)

admin.site.register(Carrito, CarritoAdmin)
admin.site.register(ItemCarrito) 


# 4. Configuración de Pedidos y Pagos
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    readonly_fields = ('producto', 'precio_unitario', 'cantidad', 'get_subtotal')
    can_delete = False
    extra = 0

class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_pedido', 'total_monto', 'estado')
    list_filter = ('estado', 'fecha_pedido')
    list_per_page = 20
    search_fields = ('usuario__username', 'id')
    inlines = [ItemPedidoInline]
    readonly_fields = ('usuario', 'total_monto', 'fecha_pedido')

admin.site.register(Pedido, PedidoAdmin)
admin.site.register(PagoBoleta)
admin.site.register(Comentario)


# 5. Sobrescribir títulos del Admin Site
admin.site.site_header = 'HardWareHouse | Panel de Control'
admin.site.site_title = 'Admin HardWareHouse'
admin.site.index_title = 'Gestión de la Plataforma'
