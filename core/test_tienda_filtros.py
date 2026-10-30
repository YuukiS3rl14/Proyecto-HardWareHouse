from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from core.models import Procesador, Proveedor, TarjetaGrafica
from core.tienda_filtros import BANDAS_PRECIO, filtro_precio


def cpu(marca, nombre, precio):
    return Procesador.objects.create(
        proveedor=marca,
        nombre=nombre,
        precio=precio,
        stock=2,
        socket='AM5',
        nucleos=6,
        frecuencia_base=Decimal('3.50'),
    )


class LimitesDePrecioTests(TestCase):
    def test_cada_limite_cae_en_una_sola_banda(self):
        marca = Proveedor.objects.create(nombre='Limites')
        valores = (
            Decimal('0'),
            Decimal('49999.99'),
            Decimal('50000'),
            Decimal('99999.99'),
            Decimal('100000'),
            Decimal('249999.99'),
            Decimal('250000'),
            Decimal('499999.99'),
            Decimal('500000'),
            Decimal('999999.99'),
            Decimal('1000000'),
            Decimal('1000000.01'),
        )
        for precio in valores:
            cpu(marca, f'Lim-{precio}-fin', precio)

        esperadas = {
            '0-50': {'0', '49999.99'},
            '50-100': {'50000', '99999.99'},
            '100-250': {'100000', '249999.99'},
            '250-500': {'250000', '499999.99'},
            '500-1000': {'500000', '999999.99'},
            '1000+': {'1000000', '1000000.01'},
        }
        for codigo, nombres in esperadas.items():
            respuesta = self.client.get(reverse('core:tienda'), {'precio': codigo})
            self.assertEqual(respuesta.status_code, 200)
            html = respuesta.content.decode()
            for precio in valores:
                visible = f'Lim-{precio}-fin'
                if str(precio) in nombres:
                    self.assertIn(visible, html)
                else:
                    self.assertNotIn(visible, html)
            self.assertIsNotNone(filtro_precio(codigo))
        self.assertEqual(len(BANDAS_PRECIO), 6)


class FiltrosCombinadosTests(TestCase):
    def setUp(self):
        self.amd = Proveedor.objects.create(nombre='AMD')
        self.intel = Proveedor.objects.create(nombre='Intel')
        self.cpu_media = cpu(self.amd, 'Ryzen de vitrina', Decimal('60000'))
        cpu(self.amd, 'Ryzen economico', Decimal('10000'))
        cpu(self.intel, 'Core de vitrina', Decimal('60000'))
        TarjetaGrafica.objects.create(
            proveedor=self.amd,
            nombre='Radeon de vitrina',
            precio=Decimal('60000'),
            stock=2,
            vram_gb=8,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
            consumo_referencia_watts=120,
            largo_mm=280,
        )
        self.url = reverse('core:tienda')

    def test_categoria_marca_y_precio_se_aplican_juntos(self):
        respuesta = self.client.get(self.url, {
            'categoria': 'CPU',
            'proveedor': self.amd.pk,
            'precio': '50-100',
        })
        self.assertContains(respuesta, 'Ryzen de vitrina')
        self.assertNotContains(respuesta, 'Ryzen economico')
        self.assertNotContains(respuesta, 'Core de vitrina')
        self.assertNotContains(respuesta, 'Radeon de vitrina')
        self.assertContains(respuesta, 'option value="CPU" selected')
        self.assertContains(respuesta, f'option value="{self.amd.pk}" selected')
        self.assertContains(respuesta, 'option value="50-100" selected')

    def test_la_seleccion_sigue_en_la_paginacion(self):
        cpu(self.amd, 'Ryzen extra', Decimal('70000'))
        with patch('core.views.TIENDA_PAGE_SIZE', 1):
            respuesta = self.client.get(self.url, {
                'categoria': 'CPU',
                'proveedor': self.amd.pk,
                'precio': '50-100',
                'orden': 'nombre',
            })
        self.assertContains(respuesta, 'page=2')
        self.assertContains(respuesta, 'categoria=CPU')
        self.assertContains(respuesta, f'proveedor={self.amd.pk}')
        self.assertContains(respuesta, 'precio=50-100')
        self.assertContains(respuesta, 'orden=nombre')
        self.assertContains(respuesta, 'href="/tienda/"')

    def test_las_marcas_no_se_repiten_y_salen_de_los_productos(self):
        cpu(self.amd, 'Otro Ryzen', Decimal('61000'))
        respuesta = self.client.get(self.url)
        html = respuesta.content.decode()
        self.assertEqual(html.count(f'value="{self.amd.pk}"'), 1)
        self.assertEqual(html.count(f'value="{self.intel.pk}"'), 1)
        self.assertNotContains(respuesta, 'custom-checkbox')

    def test_un_filtro_sin_coincidencias_muestra_el_vacio(self):
        respuesta = self.client.get(self.url, {'categoria': 'CPU', 'precio': '1000+'})
        self.assertContains(respuesta, 'No se encontraron productos')
        self.assertContains(respuesta, 'option value="1000+" selected')
        self.assertNotContains(respuesta, 'Ryzen de vitrina')


class OrdenDelCatalogoTests(TestCase):
    def setUp(self):
        self.marca = Proveedor.objects.create(nombre='Orden')
        cpu(self.marca, 'Medio', Decimal('20000'))
        cpu(self.marca, 'Caro', Decimal('90000'))
        cpu(self.marca, 'Barato', Decimal('5000'))
        self.url = reverse('core:tienda')

    def _posiciones(self, **params):
        html = self.client.get(self.url, params).content.decode()
        return html.index('Barato'), html.index('Medio'), html.index('Caro')

    def test_precio_ascendente_y_descendente(self):
        barato, medio, caro = self._posiciones(orden='precio_asc')
        self.assertLess(barato, medio)
        self.assertLess(medio, caro)
        barato, medio, caro = self._posiciones(orden='precio_desc')
        self.assertLess(caro, medio)
        self.assertLess(medio, barato)

    def test_nombre_y_relevancia(self):
        html = self.client.get(self.url, {'orden': 'nombre'}).content.decode()
        self.assertLess(html.index('Barato'), html.index('Caro'))
        self.assertLess(html.index('Caro'), html.index('Medio'))

        amd = Proveedor.objects.create(nombre='AMD')
        cpu(amd, 'Ryzen Especial', Decimal('80000'))
        cpu(amd, 'Accesorio ryzen', Decimal('80000'))
        html = self.client.get(self.url, {'q': 'ryzen', 'orden': 'relevancia'}).content.decode()
        self.assertLess(html.index('Ryzen Especial'), html.index('Accesorio ryzen'))
        self.assertContains(self.client.get(self.url, {'orden': 'relevancia'}), 'option value="relevancia" selected')


class DisposicionMovilTests(TestCase):
    def test_la_barra_se_apila_en_pantallas_pequenas(self):
        marca = Proveedor.objects.create(nombre='Pantalla')
        cpu(marca, 'CPU movil', Decimal('15000'))
        respuesta = self.client.get(reverse('core:tienda'))
        self.assertContains(respuesta, 'class="catalog-filters"')
        self.assertContains(respuesta, 'name="categoria"')
        self.assertContains(respuesta, 'name="proveedor"')
        self.assertContains(respuesta, 'name="precio"')
        self.assertContains(respuesta, 'name="orden"')
        self.assertContains(respuesta, 'js-filtro-multiple')
        self.assertNotContains(respuesta, 'custom-checkbox')
        self.assertNotContains(respuesta, 'custom-radio')
        css = Path(settings.BASE_DIR, 'core/static/core/css/tienda-filtros.css').read_text(encoding='utf-8')
        self.assertIn('@media (max-width: 767.98px)', css)
        self.assertIn('.catalog-filters {\n        grid-template-columns: 1fr;\n    }', css)
