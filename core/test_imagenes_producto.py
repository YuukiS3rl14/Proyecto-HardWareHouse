from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse

from core.admin import ProcesadorAdmin
from core.imagenes import ARCHIVOS_CATEGORIA, ARCHIVO_GENERICO, url_imagen_producto
from core.models import Carrito, Favorito, ItemCarrito, Procesador, Proveedor


CATEGORIAS = (
    ('CPU', '01_CPU.webp'),
    ('Tarjeta Gráfica', '02_GPU.webp'),
    ('Memoria RAM', '03_RAM.webp'),
    ('Placa Madre', '04_Placa_madre.webp'),
    ('SSD', '05_SSD.webp'),
    ('Disco Duro HDD', '06_HDD.webp'),
    ('Fuente de Poder', '07_Fuente_de_poder.webp'),
    ('Gabinete', '08_Gabinete.webp'),
    ('Refrigeración', '09_Refrigeracion.webp'),
    ('Ventilador', '10_Ventilador.webp'),
)


def _sin_foto(categoria):
    return SimpleNamespace(imagen=None, categoria=categoria)


class UrlImagenProductoTests(TestCase):
    def test_cada_categoria_usa_su_estatico(self):
        self.assertEqual(len(ARCHIVOS_CATEGORIA), 10)
        for categoria, archivo in CATEGORIAS:
            url = url_imagen_producto(_sin_foto(categoria))
            self.assertTrue(url.endswith(f'core/img/categorias/{archivo}'), url)
            self.assertTrue((Path(settings.BASE_DIR) / 'core' / 'static' / 'core' / 'img' / 'categorias' / archivo).is_file())

    def test_una_categoria_desconocida_usa_la_imagen_generica(self):
        url = url_imagen_producto(_sin_foto('Otra cosa'))
        self.assertTrue(url.endswith(ARCHIVO_GENERICO))

    def test_la_foto_subida_se_conserva(self):
        class Foto:
            url = '/media/productos/foto-real.webp'

        producto = SimpleNamespace(imagen=Foto(), categoria='CPU')
        self.assertEqual(url_imagen_producto(producto), '/media/productos/foto-real.webp')

    def test_un_archivo_vacio_cae_en_la_categoria(self):
        class FotoRota:
            @property
            def url(self):
                raise ValueError('sin archivo')

        producto = SimpleNamespace(imagen=FotoRota(), categoria='SSD')
        self.assertTrue(url_imagen_producto(producto).endswith('core/img/categorias/05_SSD.webp'))

    def test_el_filtro_renderiza_cada_categoria(self):
        plantilla = Template('{% load producto_extras %}{{ producto|imagen_producto }}')
        for categoria, archivo in CATEGORIAS:
            html = plantilla.render(Context({'producto': _sin_foto(categoria)}))
            self.assertIn(f'core/img/categorias/{archivo}', html)
            self.assertNotIn('placeholder.webp', html)


class PaginasSinFotoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('fotos', 'fotos@example.com', 'clave-fotos-123')
        marca = Proveedor.objects.create(nombre='Marca fotos')
        self.cpu = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU de vitrina',
            precio=Decimal('1000.00'),
            stock=3,
            socket='AM5',
            nucleos=6,
            frecuencia_base=Decimal('3.50'),
        )
        self.client.force_login(self.user)

    def test_tienda_detalle_carrito_favoritos_y_armado_usan_la_categoria(self):
        Favorito.objects.create(usuario=self.user, procesador=self.cpu)
        carrito = Carrito.objects.create(usuario=self.user)
        ItemCarrito.objects.create(
            carrito=carrito, procesador=self.cpu, cantidad=1, precio_unitario=self.cpu.precio,
        )

        tienda = self.client.get(reverse('core:tienda'))
        detalle = self.client.get(reverse('core:detalle', args=['procesador', self.cpu.pk]))
        carrito_respuesta = self.client.get(reverse('core:carrito'))
        favoritos = self.client.get(reverse('core:favoritos'))
        armado = self.client.get(reverse('core:armado'))

        for respuesta in (tienda, detalle, carrito_respuesta, favoritos, armado):
            self.assertEqual(respuesta.status_code, 200)
            self.assertContains(respuesta, 'core/img/categorias/01_CPU.webp')
            self.assertNotContains(respuesta, 'placeholder.webp')
        self.assertContains(detalle, 'data-zoom=')
        self.assertContains(armado, 'imagenes-categoria')
        self.assertIn('CPU de vitrina', armado.content.decode())

    def test_el_detalle_y_el_armado_conservan_la_foto_subida(self):
        self.cpu.imagen.name = 'productos/foto-real.webp'
        self.cpu.save(update_fields=['imagen'])

        detalle = self.client.get(reverse('core:detalle', args=['procesador', self.cpu.pk]))
        armado = self.client.get(reverse('core:armado'))
        html_detalle = detalle.content.decode()
        self.assertIn('/media/productos/foto-real.webp', html_detalle)
        self.assertIn('data-zoom="/media/productos/foto-real.webp"', html_detalle)
        self.assertNotIn('core/img/categorias/01_CPU.webp', html_detalle)
        self.assertIn('/media/productos/foto-real.webp', armado.content.decode())

    def test_la_miniatura_del_admin_usa_el_mismo_recurso(self):
        html = str(ProcesadorAdmin(Procesador, admin.site).miniatura(self.cpu))
        self.assertIn('core/img/categorias/01_CPU.webp', html)

        self.cpu.imagen.name = 'productos/foto-real.webp'
        html_real = str(ProcesadorAdmin(Procesador, admin.site).miniatura(self.cpu))
        self.assertIn('/media/productos/foto-real.webp', html_real)
