from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# --- 1. UBICACIÓN (Región y Comuna) ---

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

# --- 2. PRODUCTOS Y CATEGORÍAS (Herencia) ---

class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.nombre

class ProductoBase(models.Model):
    categoria = models.ForeignKey('Categoria', on_delete=models.PROTECT) 
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)

    class Meta:
        verbose_name = "Producto Base"

    def __str__(self):
        return f"[{self.categoria.nombre}] {self.nombre}"

# --- Modelos Específicos (Heredan de ProductoBase) ---

class Procesador(ProductoBase):
    socket = models.CharField(max_length=20)
    nucleos = models.IntegerField()
    frecuencia_base = models.DecimalField(max_digits=4, decimal_places=2)

class TarjetaGrafica(ProductoBase):
    vram_gb = models.IntegerField()
    tipo_memoria = models.CharField(max_length=10) 
    interfaz = models.CharField(max_length=20) 

class MemoriaRam(ProductoBase):
    capacidad_gb = models.IntegerField()
    tipo_ddr = models.CharField(max_length=5) 
    velocidad_mhz = models.IntegerField()

class PlacaMadre(ProductoBase):
    socket_cpu = models.CharField(max_length=20)
    chipset = models.CharField(max_length=30)
    formato = models.CharField(max_length=30) 
    ranuras_ram = models.IntegerField(verbose_name="Slots RAM")

class AlmacenamientoSSD(ProductoBase):
    capacidad_gb = models.IntegerField()
    interfaz = models.CharField(max_length=20) 
    formato = models.CharField(max_length=10) 

class AlmacenamientoHDD(ProductoBase):
    capacidad_gb = models.IntegerField()
    velocidad_rpm = models.IntegerField(verbose_name="Velocidad (RPM)")
    cache_mb = models.IntegerField(verbose_name="Cache (MB)")
    
class Gabinete(ProductoBase):
    formato_soporte = models.CharField(max_length=50, verbose_name="Soporte Placa") 
    ventiladores_incluidos = models.IntegerField()
    material = models.CharField(max_length=50) 

class FuenteDePoder(ProductoBase):
    potencia_watts = models.IntegerField(verbose_name="Potencia (W)")
    certificacion = models.CharField(max_length=20) 
    modular = models.BooleanField(default=False)
    
class RefrigeracionCooler(ProductoBase):
    tipo = models.CharField(max_length=20) 
    socket_compatibles = models.CharField(max_length=150)
    tamanho_radiador_mm = models.IntegerField(null=True, blank=True) 

class Ventilador(ProductoBase):
    tamanho_mm = models.IntegerField(verbose_name="Tamaño (mm)")
    velocidad_rpm = models.IntegerField(verbose_name="Velocidad (RPM)")
    rgb = models.BooleanField(default=False)

# --- 3. COMENTARIOS Y RESEÑAS ---

class Comentario(models.Model):
    producto = models.ForeignKey(ProductoBase, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    texto = models.TextField()
    calificacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Calificación de 1 a 5 estrellas."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.titulo} por {self.usuario.username}"

# --- 4. CARRITO DE COMPRAS (Pre-orden) ---

class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carrito')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def get_total_precio(self):
        return sum(item.get_total() for item in self.items.all())

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(ProductoBase, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    def get_total(self):
        return self.producto.precio * self.cantidad
        
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en carrito de {self.carrito.usuario.username}"

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
    producto = models.CharField(max_length=200)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) 
    cantidad = models.PositiveIntegerField()
    
    def get_subtotal(self):
        return self.precio_unitario * self.cantidad
        
    def __str__(self):
        return f"{self.cantidad} x {self.producto} en Pedido #{self.pedido.id}"

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
    


