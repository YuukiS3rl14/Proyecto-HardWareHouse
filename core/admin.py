from django.contrib import admin
from django import forms
from django.utils.html import format_html

from .admin_dashboard import resumen_dashboard
from .imagenes import url_imagen_producto
from .models import *

# ----------------------------------------------------------------------
# 1. CONFIGURACIONES GENERALES Y MODELOS BASE
# ----------------------------------------------------------------------

class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'logo')
    list_display_links = ('nombre',)
    search_fields = ('nombre',)
    list_per_page = 20

# ----------------------------------------------------------------------
# 2. CLASES DE ADMINISTRACIÓN DE PRODUCTOS INDEPENDIENTES
# ----------------------------------------------------------------------

PRODUCTO_LIST_DISPLAY = (
    'id', 'miniatura', 'nombre', 'categoria', 'proveedor',
    'precio', 'en_oferta', 'precio_oferta', 'descuento', 'stock',
)
PRODUCTO_EDITABLE = ('nombre', 'precio', 'en_oferta', 'precio_oferta', 'stock')

class ProductoAdminBase(admin.ModelAdmin):
    search_fields = ('nombre', 'proveedor__nombre')
    list_display_links = ('id',)
    list_per_page = 20
    list_select_related = ('proveedor',)
    save_on_top = True
    readonly_fields = ('creado_en', 'actualizado_en', 'porcentaje_descuento')

    @admin.display(description='Imagen')
    def miniatura(self, obj):
        return format_html(
            '<img src="{}" alt="" class="hw-admin-thumb">',
            url_imagen_producto(obj),
        )

    @admin.display(description='Descuento')
    def descuento(self, obj):
        valor = obj.porcentaje_descuento
        if valor is None:
            return '—'
        return f'{valor}%'

    def get_fieldsets(self, request, obj=None):
        resultado = []
        for nombre, opciones in super().get_fieldsets(request, obj):
            opciones = dict(opciones)
            campos = list(opciones.get('fields') or ())
            if 'stock' in campos and 'stock_minimo' not in campos:
                indice_stock = campos.index('stock') + 1
                campos[indice_stock:indice_stock] = ['stock_minimo', 'stock_advertencia']
                opciones['fields'] = tuple(campos)
            if nombre == 'Información General' and 'precio' in campos and 'en_oferta' not in campos:
                indice = campos.index('precio') + 1
                campos[indice:indice] = ['en_oferta', 'precio_oferta', 'porcentaje_descuento']
                opciones['fields'] = tuple(campos)
            resultado.append((nombre, opciones))
        if not any(nombre == 'Registro' for nombre, _opciones in resultado):
            resultado.append((
                'Registro',
                {'fields': ('creado_en', 'actualizado_en')},
            ))
        return resultado

    def save_model(self, request, obj, form, change):
        from django.core.exceptions import ValidationError
        from django.db import transaction

        from core.inventario import anotar_ajuste_ya_guardado, auditar_umbrales

        if obj.stock < 0:
            raise ValidationError('El stock no puede quedar negativo.')
        with transaction.atomic():
            stock_antes = minimo_antes = advertencia_antes = None
            if change and obj.pk:
                previo = type(obj).objects.select_for_update().filter(pk=obj.pk).first()
                if previo is not None:
                    stock_antes = previo.stock
                    minimo_antes = previo.stock_minimo
                    advertencia_antes = previo.stock_advertencia
            super().save_model(request, obj, form, change)
            if stock_antes is not None and obj.stock != stock_antes:
                anotar_ajuste_ya_guardado(
                    obj, stock_antes,
                    usuario=request.user, origen='admin',
                    motivo='Ajuste desde el administrador',
                )
            if minimo_antes is not None:
                auditar_umbrales(obj, minimo_antes, advertencia_antes, request.user)

class ProcesadorAdmin(ProductoAdminBase):
    list_display = PRODUCTO_LIST_DISPLAY + ('socket', 'nucleos', 'frecuencia_base', 'potencia_referencia_watts', 'incluye_cooler', 'graficos_integrados')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': (
            'socket', 'nucleos', 'frecuencia_base', 'potencia_referencia_watts',
            'incluye_cooler', 'potencia_termica_referencia_watts', 'graficos_integrados',
        )}),
    )

class TarjetaGraficaAdmin(ProductoAdminBase):
    list_display = PRODUCTO_LIST_DISPLAY + ('vram_gb', 'tipo_memoria', 'interfaz', 'consumo_referencia_watts', 'potencia_minima_fuente_watts', 'largo_mm')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('vram_gb', 'tipo_memoria', 'interfaz', 'consumo_referencia_watts', 'potencia_minima_fuente_watts', 'largo_mm')}),
    )

class MemoriaRamAdmin(ProductoAdminBase):
    list_display = PRODUCTO_LIST_DISPLAY + ('capacidad_gb', 'modulos_por_producto', 'capacidad_modulo_gb', 'formato_ram', 'tipo_ddr', 'velocidad_mhz')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('capacidad_gb', 'modulos_por_producto', 'capacidad_modulo_gb', 'formato_ram', 'tipo_ddr', 'velocidad_mhz')}),
    )

class PlacaMadreAdmin(ProductoAdminBase):
    list_display = PRODUCTO_LIST_DISPLAY + ('socket_cpu', 'chipset', 'formato', 'tipo_ram_soportado', 'ranuras_ram', 'formato_ram_soportado', 'capacidad_maxima_ram_gb', 'tiene_salidas_video')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': (
            'socket_cpu', 'chipset', 'formato', 'tipo_ram_soportado', 'ranuras_ram',
            'formato_ram_soportado', 'capacidad_maxima_ram_gb',
            'ranuras_m2_solo_nvme', 'ranuras_m2_solo_sata', 'ranuras_m2_nvme_o_sata',
            'puertos_sata', 'tiene_salidas_video',
        )}),
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

class AlmacenamientoSSDAdmin(ProductoAdminBase):
    form = AlmacenamientoAdminForm
    list_display = PRODUCTO_LIST_DISPLAY + ('capacidad_gb', 'interfaz', 'formato')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': (('capacidad_valor', 'capacidad_unidad'), 'interfaz', 'formato')}),
    )

class AlmacenamientoHDDAdminForm(AlmacenamientoAdminForm):
    class Meta:
        model = AlmacenamientoHDD
        fields = '__all__'


class AlmacenamientoHDDAdmin(ProductoAdminBase):
    form = AlmacenamientoHDDAdminForm
    list_display = PRODUCTO_LIST_DISPLAY + ('capacidad_gb', 'velocidad_rpm', 'cache_mb', 'interfaz', 'formato')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': (('capacidad_valor', 'capacidad_unidad'), 'velocidad_rpm', 'cache_mb', 'interfaz', 'formato')}),
    )
    
class GabineteAdmin(ProductoAdminBase):
    list_display = PRODUCTO_LIST_DISPLAY + ('formato_soporte', 'ventiladores_incluidos', 'material', 'largo_max_gpu_mm', 'altura_max_cooler_mm')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('formato_soporte', 'ventiladores_incluidos', 'material', 'largo_max_gpu_mm', 'altura_max_cooler_mm')}),
    )

class FuenteDePoderAdmin(ProductoAdminBase):
    list_display = PRODUCTO_LIST_DISPLAY + ('potencia_watts', 'certificacion', 'modular')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('potencia_watts', 'certificacion', 'modular')}),
    )
    
class RefrigeracionCoolerAdmin(ProductoAdminBase):
    list_display = PRODUCTO_LIST_DISPLAY + ('tipo', 'socket_compatibles', 'tamanho_radiador_mm', 'disipacion_referencia_watts', 'altura_mm')
    list_filter = ('proveedor',)
    list_editable = PRODUCTO_EDITABLE
    fieldsets = (
        ('Información General', {'fields': ('proveedor', 'nombre', 'descripcion', 'precio', 'stock', 'imagen')}),
        ('Especificaciones Técnicas', {'fields': ('tipo', 'socket_compatibles', 'tamanho_radiador_mm', 'disipacion_referencia_watts', 'altura_mm')}),
    )

class VentiladorAdmin(ProductoAdminBase):
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
    readonly_fields = ('producto_nombre', 'producto_tipo', 'precio_unitario', 'cantidad', 'producto_modelo', 'producto_pk', 'get_subtotal')
    can_delete = False
    extra = 0

    @admin.display(description='Subtotal')
    def get_subtotal(self, obj):
        # La fila plantilla del inline no tiene precio ni cantidad. El cálculo
        # de un ítem guardado sigue en ItemPedido.get_subtotal().
        if obj.precio_unitario is None or obj.cantidad is None:
            if obj.pk is None:
                return ''
            return 'Precio o cantidad inválidos'
        return obj.get_subtotal()

class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_pedido', 'total_monto', 'estado', 'paypal_transaccion_id', 'paypal_invoice')
    list_display_links = ('id',)
    list_filter = ('estado', 'fecha_pedido')
    date_hierarchy = 'fecha_pedido'
    list_per_page = 20
    search_fields = ('usuario__username', 'id', 'paypal_transaccion_id', 'paypal_invoice', 'paypal_invoice_legado')
    list_select_related = ('usuario',)
    ordering = ('-fecha_pedido',)
    inlines = [ItemPedidoInline]
    readonly_fields = (
        'usuario', 'total_monto', 'fecha_pedido', 'paypal_transaccion_id',
        'paypal_invoice', 'paypal_invoice_legado',
    )
    save_on_top = True

# ----------------------------------------------------------------------
# 4. REGISTRO DE MODELOS (Usando clases específicas)
# ----------------------------------------------------------------------

class RegionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre')
    list_display_links = ('nombre',)
    search_fields = ('nombre',)
    ordering = ('numero',)

class ComunaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'region')
    list_display_links = ('nombre',)
    search_fields = ('nombre', 'region__nombre')
    list_filter = ('region',)
    list_select_related = ('region',)
    autocomplete_fields = ('region',)

class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'calificacion', 'fecha_creacion')
    list_display_links = ('titulo',)
    search_fields = ('titulo', 'texto', 'usuario__username')
    list_filter = ('calificacion', 'fecha_creacion')
    list_select_related = ('usuario',)
    date_hierarchy = 'fecha_creacion'
    ordering = ('-fecha_creacion',)

admin.site.register(Region, RegionAdmin)
admin.site.register(Comuna, ComunaAdmin)
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

admin.site.register(Comentario, ComentarioAdmin)

class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_creacion', 'get_total_precio')
    list_display_links = ('usuario',)
    search_fields = ('usuario__username',)
    list_select_related = ('usuario',)
    list_per_page = 20
    readonly_fields = ('get_total_precio',)

class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ('id', 'carrito', 'cantidad', 'precio_unitario', 'producto')
    list_display_links = ('id',)
    search_fields = ('carrito__usuario__username',)
    list_select_related = ('carrito__usuario',)
    list_per_page = 20

    @admin.display(description='Producto')
    def producto(self, obj):
        return obj.get_related_product() or '—'

admin.site.register(Carrito, CarritoAdmin)
admin.site.register(ItemCarrito, ItemCarritoAdmin)
admin.site.register(Pedido, PedidoAdmin)

class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'get_related_product', 'fecha_agregado')
    list_display_links = ('usuario',)
    list_filter = ('usuario',)
    search_fields = ('usuario__username',)
    list_select_related = ('usuario',)
    ordering = ('-fecha_agregado',)

class PagoBoletaAdmin(admin.ModelAdmin):
    list_display = ('transaccion_id', 'pedido', 'monto_pagado', 'metodo_pago', 'email_comprador', 'fecha_pago')
    list_display_links = ('transaccion_id',)
    search_fields = ('transaccion_id', 'email_comprador', 'nombre_comprador')
    list_filter = ('metodo_pago', 'fecha_pago')
    list_select_related = ('pedido',)
    date_hierarchy = 'fecha_pago'
    ordering = ('-fecha_pago',)

admin.site.register(Favorito, FavoritoAdmin)
admin.site.register(PagoBoleta, PagoBoletaAdmin)


class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = (
        'creado_en', 'nombre_producto', 'producto_modelo', 'producto_pk',
        'tipo', 'cantidad', 'stock_anterior', 'stock_posterior', 'origen', 'usuario',
    )
    list_filter = ('tipo', 'origen', 'categoria')
    search_fields = ('nombre_producto', 'producto_modelo', 'motivo')
    ordering = ('-creado_en', '-id')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class AuditoriaUmbralAdmin(admin.ModelAdmin):
    list_display = (
        'creado_en', 'nombre_producto', 'producto_modelo', 'producto_pk',
        'minimo_anterior', 'minimo_nuevo', 'advertencia_anterior', 'advertencia_nueva', 'usuario',
    )
    ordering = ('-creado_en', '-id')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(MovimientoStock, MovimientoStockAdmin)
admin.site.register(AuditoriaUmbral, AuditoriaUmbralAdmin)

# ----------------------------------------------------------------------
# 5. Sobrescribir títulos del Admin Site
# ----------------------------------------------------------------------

admin.site.site_header = 'HardWareHouse | Panel de Control'
admin.site.site_title = 'Admin HardWareHouse'
admin.site.index_title = 'Gestión de la Plataforma'

_index_original = admin.site.index


def index(request, extra_context=None):
    extra_context = dict(extra_context or {})
    extra_context['hw'] = resumen_dashboard(request)
    return _index_original(request, extra_context)


admin.site.index = index
