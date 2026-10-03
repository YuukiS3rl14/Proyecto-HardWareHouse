from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
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

PRODUCTO_LIST_DISPLAY = ('id', 'nombre', 'categoria', 'proveedor', 'precio', 'stock', 'imagen')
PRODUCTO_EDITABLE = ('nombre', 'precio', 'stock')

class ProcesadorAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('socket', 'nucleos', 'frecuencia_base', 'potencia_referencia_watts')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('socket', 'nucleos', 'frecuencia_base', 'potencia_referencia_watts')}),
    )

class TarjetaGraficaAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('vram_gb', 'tipo_memoria', 'interfaz', 'consumo_referencia_watts', 'potencia_minima_fuente_watts', 'largo_mm')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('vram_gb', 'tipo_memoria', 'interfaz', 'consumo_referencia_watts', 'potencia_minima_fuente_watts', 'largo_mm')}),
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
    list_display = PRODUCTO_LIST_DISPLAY + ('socket_cpu', 'chipset', 'formato', 'tipo_ram_soportado', 'ranuras_ram')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('socket_cpu', 'chipset', 'formato', 'tipo_ram_soportado', 'ranuras_ram')}),
    )

class AlmacenamientoAdminForm(forms.ModelForm):
    capacidad_valor = forms.IntegerField(label="Capacidad (Valor)", help_text="Ej: 512, 1, 2")
    capacidad_unidad = forms.ChoiceField(label="Unidad", choices=[('GB', 'GB'), ('TB', 'TB')])

    class Meta:
        model = AlmacenamientoSSD 
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            capacidad_gb = self.instance.capacidad_gb
            if capacidad_gb >= 1000:
                self.fields['capacidad_valor'].initial = capacidad_gb / 1024
                self.fields['capacidad_unidad'].initial = 'TB'
            else:
                self.fields['capacidad_valor'].initial = capacidad_gb
                self.fields['capacidad_unidad'].initial = 'GB'

    def save(self, commit=True):
        valor = self.cleaned_data.get('capacidad_valor')
        unidad = self.cleaned_data.get('capacidad_unidad')

        if valor is not None and unidad:
            if unidad == 'TB':
                self.instance.capacidad_gb = valor * 1024
            else: 
                self.instance.capacidad_gb = valor
        
        return super().save(commit=commit)

class AlmacenamientoSSDAdmin(admin.ModelAdmin):
    form = AlmacenamientoAdminForm
    list_display = PRODUCTO_LIST_DISPLAY + ('capacidad_gb', 'interfaz', 'formato')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': (('capacidad_valor', 'capacidad_unidad'), 'interfaz', 'formato')}),
    )

class AlmacenamientoHDDAdmin(admin.ModelAdmin):
    form = AlmacenamientoAdminForm
    list_display = PRODUCTO_LIST_DISPLAY + ('capacidad_gb', 'velocidad_rpm', 'cache_mb')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': (('capacidad_valor', 'capacidad_unidad'), 'velocidad_rpm', 'cache_mb')}),
    )
    
class GabineteAdmin(admin.ModelAdmin):
    list_display = PRODUCTO_LIST_DISPLAY + ('formato_soporte', 'ventiladores_incluidos', 'material', 'largo_max_gpu_mm')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('formato_soporte', 'ventiladores_incluidos', 'material', 'largo_max_gpu_mm')}),
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
    list_display = ('id', 'usuario', 'fecha_pedido', 'total_monto', 'estado', 'paypal_transaccion_id')
    list_filter = ('estado', 'fecha_pedido')
    list_per_page = 20
    search_fields = ('usuario__username', 'id')
    inlines = [ItemPedidoInline]
    readonly_fields = ('usuario', 'total_monto', 'fecha_pedido', 'paypal_transaccion_id')

# ----------------------------------------------------------------------
# 4. REGISTRO DE MODELOS (Usando clases específicas)
# ----------------------------------------------------------------------

admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(Proveedor, ProveedorAdmin)

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

admin.site.register(Comentario)

class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_creacion', 'get_total_precio')
    list_per_page = 20
    readonly_fields = ('get_total_precio',)

admin.site.register(Carrito, CarritoAdmin)
admin.site.register(ItemCarrito) 
admin.site.register(Pedido, PedidoAdmin)

class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'get_related_product', 'fecha_agregado')
    list_filter = ('usuario',)
admin.site.register(Favorito, FavoritoAdmin)
admin.site.register(PagoBoleta)

# ----------------------------------------------------------------------
# 5. Sobrescribir títulos del Admin Site
# ----------------------------------------------------------------------

admin.site.site_header = 'HardWareHouse | Panel de Control'
admin.site.site_title = 'Admin HardWareHouse'
admin.site.index_title = 'Gestión de la Plataforma'
