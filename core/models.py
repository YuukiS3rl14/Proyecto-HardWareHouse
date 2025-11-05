from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# --- 1. MODELOS BASE DE REFERENCIA (Geografía y Proveedor) ---

class Region(models.Model):
    numero = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.numero} - {self.nombre}"

class Comuna(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='comunas')
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.nombre} ({self.region.nombre})"

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='proveedores/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Proveedores / Marcas"

    def __str__(self):
        return self.nombre


# --- 2. MODELOS DE PRODUCTOS INDEPENDIENTES ---

# Nota: El campo proveedor ahora es obligatorio y no tiene default.
# La categoría es un CharField estático.

class Procesador(models.Model):
    categoria = models.CharField(max_length=50, default='CPU', editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Marca/Proveedor") # Ya no usa default=
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    socket = models.CharField(max_length=20)
    nucleos = models.IntegerField()
    frecuencia_base = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        verbose_name_plural = "Procesadores (CPU)"
    def __str__(self):
        return f"[CPU | {self.proveedor.nombre}] {self.nombre}"

class TarjetaGrafica(models.Model):
    categoria = models.CharField(max_length=50, default='Tarjeta Gráfica', editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Marca/Proveedor") # Ya no usa default=
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    vram_gb = models.IntegerField(verbose_name="VRAM (GB)")
    tipo_memoria = models.CharField(max_length=10, verbose_name="Tipo Memoria") 
    interfaz = models.CharField(max_length=20, verbose_name="Interfaz Bus") 

    class Meta:
        verbose_name_plural = "Tarjetas Gráficas (GPU)"
    def __str__(self):
        return f"[GPU | {self.proveedor.nombre}] {self.nombre}"

class MemoriaRam(models.Model):
    categoria = models.CharField(max_length=50, default='Memoria RAM', editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Marca/Proveedor") # Ya no usa default=
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    capacidad_gb = models.IntegerField(verbose_name="Capacidad (GB)")
    tipo_ddr = models.CharField(max_length=5, verbose_name="Tipo DDR") 
    velocidad_mhz = models.IntegerField(verbose_name="Velocidad (MHz)")
    
    class Meta:
        verbose_name_plural = "Memorias RAM"
    def __str__(self):
        return f"[RAM | {self.proveedor.nombre}] {self.nombre}"

class PlacaMadre(models.Model):
    categoria = models.CharField(max_length=50, default='Placa Madre', editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Marca/Proveedor") # Ya no usa default=
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    socket_cpu = models.CharField(max_length=20, verbose_name="Socket CPU")
    chipset = models.CharField(max_length=30)
    formato = models.CharField(max_length=30) 
    ranuras_ram = models.IntegerField(verbose_name="Slots RAM")

    class Meta:
        verbose_name_plural = "Placas Madre"
    def __str__(self):
        return f"[MB | {self.proveedor.nombre}] {self.nombre}"

class AlmacenamientoSSD(models.Model):
    categoria = models.CharField(max_length=50, default='SSD', editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Marca/Proveedor") # Ya no usa default=
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    capacidad_gb = models.IntegerField(verbose_name="Capacidad (GB)")
    interfaz = models.CharField(max_length=20) 
    formato = models.CharField(max_length=10) 

    class Meta:
        verbose_name_plural = "Almacenamiento SSD"
    def __str__(self):
        return f"[SSD | {self.proveedor.nombre}] {self.nombre}"

class AlmacenamientoHDD(models.Model):
    categoria = models.CharField(max_length=50, default='Disco Duro HDD', editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Marca/Proveedor") # Ya no usa default=
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    capacidad_gb = models.IntegerField(verbose_name="Capacidad (GB)")
    velocidad_rpm = models.IntegerField(verbose_name="Velocidad (RPM)")
    cache_mb = models.IntegerField(verbose_name="Cache (MB)")
    
    class Meta:
        verbose_name_plural = "Almacenamiento HDD"
    def __str__(self):
        return f"[HDD | {self.proveedor.nombre}] {self.nombre}"

class Gabinete(models.Model):
    categoria = models.CharField(max_length=50, default='Gabinete', editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Marca/Proveedor") # Ya no usa default=
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    formato_soporte = models.CharField(max_length=50, verbose_name="Soporte Placa") 
    ventiladores_incluidos = models.BooleanField(default=False)
    material = models.CharField(max_length=50) 

    class Meta:
        verbose_name_plural = "Gabinetes"
    def __str__(self):
        return f"[Case | {self.proveedor.nombre}] {self.nombre}"

class FuenteDePoder(models.Model):
    categoria = models.CharField(max_length=50, default='Fuente de Poder', editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Marca/Proveedor") # Ya no usa default=
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    potencia_watts = models.IntegerField(verbose_name="Potencia (W)")
    certificacion = models.CharField(max_length=20) 
    modular = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Fuentes de Poder (PSU)"
    def __str__(self):
        return f"[PSU | {self.proveedor.nombre}] {self.nombre}"
    
class RefrigeracionCooler(models.Model):
    categoria = models.CharField(max_length=50, default='Refrigeración', editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Marca/Proveedor") # Ya no usa default=
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    tipo = models.CharField(max_length=20, verbose_name="Tipo (Aire/Líquida)") 
    socket_compatibles = models.CharField(max_length=150, verbose_name="Sockets Comp.")
    tamanho_radiador_mm = models.IntegerField(null=True, blank=True, verbose_name="Radiador (mm)") 

    class Meta:
        verbose_name_plural = "Refrigeración (Cooler)"
    def __str__(self):
        return f"[Cooler | {self.proveedor.nombre}] {self.nombre}"

class Ventilador(models.Model):
    categoria = models.CharField(max_length=50, default='Ventilador', editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Marca/Proveedor") # Ya no usa default=
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    tamanho_mm = models.IntegerField(verbose_name="Tamaño (mm)")
    velocidad_rpm = models.IntegerField(verbose_name="Velocidad (RPM)")
    rgb = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Ventiladores"
    def __str__(self):
        return f"[Fan | {self.proveedor.nombre}] {self.nombre}"

    
# --- 3. COMENTARIOS Y RESEÑAS (CLAVES FORÁNEAS MÚLTIPLES) ---

class Comentario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    texto = models.TextField()
    calificacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Calificación de 1 a 5 estrellas."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Claves Foráneas Múltiples para enlazar a CUALQUIER producto
    procesador = models.ForeignKey(Procesador, on_delete=models.CASCADE, null=True, blank=True)
    tarjeta_grafica = models.ForeignKey(TarjetaGrafica, on_delete=models.CASCADE, null=True, blank=True)
    memoria_ram = models.ForeignKey(MemoriaRam, on_delete=models.CASCADE, null=True, blank=True)
    placa_madre = models.ForeignKey(PlacaMadre, on_delete=models.CASCADE, null=True, blank=True)
    almacenamiento_ssd = models.ForeignKey(AlmacenamientoSSD, on_delete=models.CASCADE, null=True, blank=True)
    almacenamiento_hdd = models.ForeignKey(AlmacenamientoHDD, on_delete=models.CASCADE, null=True, blank=True)
    gabinete = models.ForeignKey(Gabinete, on_delete=models.CASCADE, null=True, blank=True)
    fuente_de_poder = models.ForeignKey(FuenteDePoder, on_delete=models.CASCADE, null=True, blank=True)
    refrigeracion = models.ForeignKey(RefrigeracionCooler, on_delete=models.CASCADE, null=True, blank=True)
    ventilador = models.ForeignKey(Ventilador, on_delete=models.CASCADE, null=True, blank=True)
    
    def get_related_product(self):
        """Método helper para obtener el producto real al que apunta el comentario."""
        if self.procesador_id: return self.procesador
        if self.tarjeta_grafica_id: return self.tarjeta_grafica
        if self.memoria_ram_id: return self.memoria_ram
        if self.placa_madre_id: return self.placa_madre
        if self.almacenamiento_ssd_id: return self.almacenamiento_ssd
        if self.almacenamiento_hdd_id: return self.almacenamiento_hdd
        if self.gabinete_id: return self.gabinete
        if self.fuente_de_poder_id: return self.fuente_de_poder
        if self.refrigeracion_id: return self.refrigeracion
        if self.ventilador_id: return self.ventilador
        return None

    def __str__(self):
        producto = self.get_related_product()
        nombre_producto = producto.nombre if producto else "Producto Eliminado/Desconocido"
        return f"{self.titulo} sobre {nombre_producto} por {self.usuario.username}"


# --- 4. CARRITO DE COMPRAS (Pre-orden, CLAVES FORÁNEAS MÚLTIPLES) ---

class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carrito')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def get_total_precio(self):
        return sum(item.get_total() for item in self.items.all())

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Claves Foráneas Múltiples para enlazar a CUALQUIER producto
    procesador = models.ForeignKey(Procesador, on_delete=models.CASCADE, null=True, blank=True)
    tarjeta_grafica = models.ForeignKey(TarjetaGrafica, on_delete=models.CASCADE, null=True, blank=True)
    memoria_ram = models.ForeignKey(MemoriaRam, on_delete=models.CASCADE, null=True, blank=True)
    placa_madre = models.ForeignKey(PlacaMadre, on_delete=models.CASCADE, null=True, blank=True)
    almacenamiento_ssd = models.ForeignKey(AlmacenamientoSSD, on_delete=models.CASCADE, null=True, blank=True)
    almacenamiento_hdd = models.ForeignKey(AlmacenamientoHDD, on_delete=models.CASCADE, null=True, blank=True)
    gabinete = models.ForeignKey(Gabinete, on_delete=models.CASCADE, null=True, blank=True)
    fuente_de_poder = models.ForeignKey(FuenteDePoder, on_delete=models.CASCADE, null=True, blank=True)
    refrigeracion = models.ForeignKey(RefrigeracionCooler, on_delete=models.CASCADE, null=True, blank=True)
    ventilador = models.ForeignKey(Ventilador, on_delete=models.CASCADE, null=True, blank=True)
    
    # Campo para almacenar el precio del producto en el momento en que fue añadido al carrito
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    def get_related_product(self):
        """Método helper para obtener el producto real al que apunta el ítem."""
        if self.procesador_id: return self.procesador
        if self.tarjeta_grafica_id: return self.tarjeta_grafica
        if self.memoria_ram_id: return self.memoria_ram
        if self.placa_madre_id: return self.placa_madre
        if self.almacenamiento_ssd_id: return self.almacenamiento_ssd
        if self.almacenamiento_hdd_id: return self.almacenamiento_hdd
        if self.gabinete_id: return self.gabinete
        if self.fuente_de_poder_id: return self.fuente_de_poder
        if self.refrigeracion_id: return self.refrigeracion
        if self.ventilador_id: return self.ventilador
        return None

    def get_total(self):
        # Usamos el precio almacenado
        return self.precio_unitario * self.cantidad
        
    def __str__(self):
        producto = self.get_related_product()
        nombre_producto = producto.nombre if producto else "Producto Desconocido"
        return f"{self.cantidad} x {nombre_producto} en carrito de {self.carrito.usuario.username}"


# --- 5. PEDIDOS Y BOLETAS (Post-Pago) ---

class Pedido(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente de Pago'),
        ('PAGADO', 'Pago Confirmado'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    )
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='pedidos')
    fecha_pedido = models.DateTimeField(default=timezone.now)
    total_monto = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Datos de Envío/Facturación (simulación de Boleta)
    direccion_envio = models.CharField(max_length=255)
    comuna_envio = models.ForeignKey(Comuna, on_delete=models.PROTECT, null=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    
    def __str__(self):
        return f"Pedido #{self.id} de {self.usuario.username} - {self.estado}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items_pedido')
    
    # Datos Estáticos del Producto al momento de la compra
    producto_nombre = models.CharField(max_length=200, verbose_name="Producto")
    producto_tipo = models.CharField(max_length=50, verbose_name="Tipo") # Ej: Procesador, SSD
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) 
    cantidad = models.PositiveIntegerField()
    
    def get_subtotal(self):
        return self.precio_unitario * self.cantidad
        
    def __str__(self):
        return f"{self.cantidad} x {self.producto_nombre} en Pedido #{self.pedido.id}"

class PagoBoleta(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='pago_boleta')
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=50) 
    transaccion_id = models.CharField(max_length=100, unique=True)
    
    # Datos del Usuario (tomados del Pedido)
    nombre_comprador = models.CharField(max_length=200)
    email_comprador = models.EmailField()
    
    def __str__(self):
        return f"Boleta/Pago Transacción {self.transaccion_id}"


# --- 6. FAVORITOS DE USUARIO ---

class Favorito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoritos')
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    # Claves Foráneas Múltiples para enlazar a CUALQUIER producto
    procesador = models.ForeignKey(Procesador, on_delete=models.CASCADE, null=True, blank=True)
    tarjeta_grafica = models.ForeignKey(TarjetaGrafica, on_delete=models.CASCADE, null=True, blank=True)
    memoria_ram = models.ForeignKey(MemoriaRam, on_delete=models.CASCADE, null=True, blank=True)
    placa_madre = models.ForeignKey(PlacaMadre, on_delete=models.CASCADE, null=True, blank=True)
    almacenamiento_ssd = models.ForeignKey(AlmacenamientoSSD, on_delete=models.CASCADE, null=True, blank=True)
    almacenamiento_hdd = models.ForeignKey(AlmacenamientoHDD, on_delete=models.CASCADE, null=True, blank=True)
    gabinete = models.ForeignKey(Gabinete, on_delete=models.CASCADE, null=True, blank=True)
    fuente_de_poder = models.ForeignKey(FuenteDePoder, on_delete=models.CASCADE, null=True, blank=True)
    refrigeracion = models.ForeignKey(RefrigeracionCooler, on_delete=models.CASCADE, null=True, blank=True)
    ventilador = models.ForeignKey(Ventilador, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = "Favorito"
        verbose_name_plural = "Favoritos"
        # Restricción para que un usuario no pueda añadir el mismo producto a favoritos más de una vez.
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'procesador'], name='unique_fav_procesador'),
            models.UniqueConstraint(fields=['usuario', 'tarjeta_grafica'], name='unique_fav_tarjeta_grafica'),
            models.UniqueConstraint(fields=['usuario', 'memoria_ram'], name='unique_fav_memoria_ram'),
            models.UniqueConstraint(fields=['usuario', 'placa_madre'], name='unique_fav_placa_madre'),
            models.UniqueConstraint(fields=['usuario', 'almacenamiento_ssd'], name='unique_fav_almacenamiento_ssd'),
            models.UniqueConstraint(fields=['usuario', 'almacenamiento_hdd'], name='unique_fav_almacenamiento_hdd'),
            models.UniqueConstraint(fields=['usuario', 'gabinete'], name='unique_fav_gabinete'),
            models.UniqueConstraint(fields=['usuario', 'fuente_de_poder'], name='unique_fav_fuente_de_poder'),
            models.UniqueConstraint(fields=['usuario', 'refrigeracion'], name='unique_fav_refrigeracion'),
            models.UniqueConstraint(fields=['usuario', 'ventilador'], name='unique_fav_ventilador'),
        ]

    def get_related_product(self):
        """Método helper para obtener el producto real al que apunta el favorito."""
        product_fields = ['procesador', 'tarjeta_grafica', 'memoria_ram', 'placa_madre', 'almacenamiento_ssd', 'almacenamiento_hdd', 'gabinete', 'fuente_de_poder', 'refrigeracion', 'ventilador']
        for field in product_fields:
            if getattr(self, field):
                return getattr(self, field)
        return None
