import re
from decimal import Decimal
from posixpath import normpath

from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from core.models import Procesador, Proveedor


PAGINAS = ('core:index', 'core:tienda', 'core:armado')
EXTENSIONES = ('webp', 'png', 'ico', 'jpg', 'jpeg', 'gif', 'svg')


def _rutas_de_html(html):
    return set(re.findall(
        r'/static/([^"\']+\.(?:webp|png|ico|jpe?g|gif|svg))(?:\?[^"\']*)?',
        html,
    ))


def _rutas_de_css(css_estatico, texto):
    carpeta = css_estatico.rsplit('/', 1)[0]
    rutas = set()
    for referencia in re.findall(r'url\((?:\'|")?([^)\'"]+)(?:\'|")?\)', texto):
        referencia = referencia.split('?', 1)[0].split('#', 1)[0].strip()
        if not referencia or referencia.startswith(('data:', 'http:', 'https:')):
            continue
        if referencia.startswith('/static/'):
            rutas.add(referencia[len('/static/'):])
            continue
        if referencia.startswith('/'):
            continue
        rutas.add(normpath(f'{carpeta}/{referencia}'))
    return rutas


class PaginasPublicasSinImagenRotaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='Marca estaticos')
        cls.cpu = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU de auditoria',
            precio=Decimal('1000.00'),
            stock=2,
            socket='AM5',
            nucleos=6,
            frecuencia_base=Decimal('3.50'),
        )

    def test_inicio_catalogo_detalle_y_armado_usan_archivos_presentes(self):
        respuestas = [self.client.get(reverse(nombre)) for nombre in PAGINAS]
        respuestas.append(self.client.get(reverse('core:detalle', args=['procesador', self.cpu.pk])))
        rutas = set()
        for respuesta in respuestas:
            self.assertEqual(respuesta.status_code, 200)
            html = respuesta.content.decode()
            self.assertNotIn('placeholder.png', html)
            self.assertNotIn('placeholder.webp', html)
            self.assertIn('brand-logo', html)
            self.assertIn('>H</span>ardware House', html)
            self.assertIn('>HardWareHouse</h5>', html)
            self.assertNotIn('HWH_banner.png', html)
            self.assertNotIn('HWH_logo_ampliado.png', html)
            self.assertNotIn('core/img/logo.ico', html)
            self.assertNotIn('core/img/admin-logo.png', html)
            rutas.update(_rutas_de_html(html))
            for css in re.findall(r'/static/([^"\']+\.css)', html):
                archivo = finders.find(css)
                self.assertTrue(archivo, css)
                texto = open(archivo, encoding='utf-8', errors='ignore').read()
                rutas.update(_rutas_de_css(css, texto))

        self.assertIn('core/img/carrusel_armado.webp', rutas)
        self.assertIn('core/img/ofertas_pc_gamer.webp', rutas)
        self.assertIn('core/img/HWH_logo.png', rutas)
        self.assertNotIn('core/img/HWH_banner.png', rutas)
        self.assertNotIn('core/img/HWH_logo_ampliado.png', rutas)
        self.assertIn('core/img/cpu.webp', rutas)
        self.assertNotIn('core/img/logo.ico', rutas)
        for ruta in sorted(rutas):
            self.assertTrue(ruta.lower().endswith(EXTENSIONES), ruta)
            self.assertTrue(finders.find(ruta), ruta)
