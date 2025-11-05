from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html 

from .models import *

# ----------------------------------------------------------------------
# 1. CONFIGURACIONES GENERALES Y MODELOS BASE
# ----------------------------------------------------------------------

class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'logo')
    search_fields = ('nombre',)
    list_per_page = 20

# ----------------------------------------------------------------------
# 2. CLASES DE ADMINISTRACIÓN DE PRODUCTOS INDEPENDIENTES
# ----------------------------------------------------------------------

# Atributos generales de listado para todos los productos (sin herencia de código)
PRODUCTO_LIST_DISPLAY = ('id', 'nombre', 'categoria', 'proveedor', 'precio', 'stock', 'imagen')
PRODUCTO_EDITABLE = ('nombre', 'precio', 'stock')

class ProcesadorAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('socket', 'nucleos', 'frecuencia_base')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('socket', 'nucleos', 'frecuencia_base')}),
    )

class TarjetaGraficaAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('vram_gb', 'tipo_memoria', 'interfaz')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('vram_gb', 'tipo_memoria', 'interfaz')}),
    )

class MemoriaRamAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('capacidad_gb', 'tipo_ddr', 'velocidad_mhz')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('capacidad_gb', 'tipo_ddr', 'velocidad_mhz')}),
    )

class PlacaMadreAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('socket_cpu', 'chipset', 'formato', 'ranuras_ram')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('socket_cpu', 'chipset', 'formato', 'ranuras_ram')}),
    )

class AlmacenamientoSSDAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('capacidad_gb', 'interfaz', 'formato')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('capacidad_gb', 'interfaz', 'formato')}),
    )

class AlmacenamientoHDDAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('capacidad_gb', 'velocidad_rpm', 'cache_mb')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('capacidad_gb', 'velocidad_rpm', 'cache_mb')}),
    )
    
class GabineteAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('formato_soporte', 'ventiladores_incluidos', 'material')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('formato_soporte', 'ventiladores_incluidos', 'material')}),
    )

class FuenteDePoderAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('potencia_watts', 'certificacion', 'modular')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('potencia_watts', 'certificacion', 'modular')}),
    )
    
class RefrigeracionCoolerAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('tipo', 'socket_compatibles', 'tamanho_radiador_mm')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('tipo', 'socket_compatibles', 'tamanho_radiador_mm')}),
    )

class VentiladorAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('tamanho_mm', 'velocidad_rpm', 'rgb')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('tamanho_mm', 'velocidad_rpm', 'rgb')}),
    )


# ----------------------------------------------------------------------
# 3. ADMINISTRACIÓN DE CARRO Y PEDIDOS 
# ----------------------------------------------------------------------

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    readonly_fields = ('producto_nombre', 'producto_tipo', 'precio_unitario', 'cantidad', 'get_subtotal')
    can_delete = False
    extra = 0

class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_pedido', 'total_monto', 'estado')
    list_filter = ('estado', 'fecha_pedido')
    list_per_page = 20
    search_fields = ('usuario__username', 'id')
    inlines = [ItemPedidoInline]
    readonly_fields = ('usuario', 'total_monto', 'fecha_pedido')

# ----------------------------------------------------------------------
# 4. REGISTRO DE MODELOS (Usando clases específicas)
# ----------------------------------------------------------------------

admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(Proveedor, ProveedorAdmin)

# Registro de Modelos de Producto Específicos
admin.site.register(Procesador, ProcesadorAdmin)
admin.site.register(TarjetaGrafica, TarjetaGraficaAdmin)
admin.site.register(MemoriaRam, MemoriaRamAdmin)
admin.site.register(PlacaMadre, PlacaMadreAdmin)
admin.site.register(AlmacenamientoSSD, AlmacenamientoSSDAdmin)
admin.site.register(AlmacenamientoHDD, AlmacenamientoHDDAdmin)
admin.site.register(Gabinete, GabineteAdmin)
admin.site.register(FuenteDePoder, FuenteDePoderAdmin)
admin.site.register(RefrigeracionCooler, RefrigeracionCoolerAdmin)
admin.site.register(Ventilador, VentiladorAdmin)

# Otros modelos
admin.site.register(Comentario)

class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_creacion', 'get_total_precio')
    list_per_page = 20
    readonly_fields = ('get_total_precio',)

admin.site.register(Carrito, CarritoAdmin)
admin.site.register(ItemCarrito) 
admin.site.register(Pedido, PedidoAdmin)
admin.site.register(PagoBoleta)

# 5. Sobrescribir títulos del Admin Site
admin.site.site_header = 'HardWareHouse | Panel de Control'
admin.site.site_title = 'Admin HardWareHouse'
admin.site.index_title = 'Gestión de la Plataforma'
