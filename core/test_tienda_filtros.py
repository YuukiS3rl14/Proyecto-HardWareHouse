from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from core.models import (
    AlmacenamientoHDD,
    FuenteDePoder,
    MemoriaRam,
    Procesador,
    Proveedor,
    TarjetaGrafica,
)
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
        self.assertEqual(html.count(f'option value="{self.amd.pk}"'), 1)
        self.assertEqual(html.count(f'option value="{self.intel.pk}"'), 1)
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
        self.assertContains(respuesta, 'js-filtro-catalogo')
        self.assertNotContains(respuesta, 'custom-checkbox')
        self.assertNotContains(respuesta, 'custom-radio')
        css = Path(settings.BASE_DIR, 'core/static/core/css/tienda-filtros.css').read_text(encoding='utf-8')
        self.assertIn('@media (max-width: 767.98px)', css)
        self.assertIn('.catalog-filters {\n        grid-template-columns: 1fr;\n    }', css)


def _destino(url, pares):
    return f'{url}?{urlencode(pares)}' if pares else url


class ReemplazoDeFiltrosTests(TestCase):
    def setUp(self):
        self.amd = Proveedor.objects.create(nombre='AMD')
        self.intel = Proveedor.objects.create(nombre='Intel')
        self.seagate = Proveedor.objects.create(nombre='Seagate')
        self.seasonic = Proveedor.objects.create(nombre='Seasonic')
        cpu(self.amd, 'Ryzen de vitrina', Decimal('60000'))
        cpu(self.intel, 'Core de vitrina', Decimal('60000'))
        MemoriaRam.objects.create(
            proveedor=self.amd,
            nombre='Vengeance',
            precio=Decimal('50000'),
            stock=2,
            capacidad_gb=16,
            tipo_ddr='DDR5',
            velocidad_mhz=5600,
        )
        AlmacenamientoHDD.objects.create(
            proveedor=self.seagate,
            nombre='Barracuda',
            precio=Decimal('60000'),
            stock=2,
            capacidad_gb=1000,
            velocidad_rpm=7200,
            cache_mb=64,
            interfaz='SATA III',
            formato='3.5"',
        )
        FuenteDePoder.objects.create(
            proveedor=self.seasonic,
            nombre='RM750',
            precio=Decimal('80000'),
            stock=2,
            potencia_watts=750,
            certificacion='80+ Gold',
            modular=True,
        )
        self.url = reverse('core:tienda')

    def _aplicar(self, **params):
        datos = {'aplicar': '1', 'heredado_q': '', 'heredado_categoria': '', 'heredado_proveedor': ''}
        datos.update(params)
        return self.client.get(self.url, datos)

    def test_home_categoria_muestra_solo_esa_familia(self):
        pagina = self.client.get(self.url, {'categoria': 'CPU', 'origen': 'home'})
        self.assertContains(pagina, 'Core de vitrina')
        self.assertContains(pagina, 'Ryzen de vitrina')
        self.assertNotContains(pagina, 'Vengeance')
        self.assertNotContains(pagina, 'Barracuda')
        self.assertContains(pagina, 'name="origen" value="home"')
        self.assertContains(pagina, 'name="heredado_categoria" value="CPU"')
        self.assertContains(pagina, 'id="conteo-categoria" aria-live="polite">1</span>')
        self.assertContains(pagina, 'id="conteo-marca" aria-live="polite">0</span>')
        self.assertContains(pagina, 'class="catalog-chip"')

    def test_home_reemplaza_la_categoria(self):
        respuesta = self._aplicar(origen='home', heredado_categoria='CPU', categoria='Memoria RAM')
        self.assertRedirects(respuesta, _destino(self.url, [('categoria', 'Memoria RAM')]))
        pagina = self.client.get(_destino(self.url, [('categoria', 'Memoria RAM')]))
        self.assertContains(pagina, 'Vengeance')
        self.assertNotContains(pagina, 'Core de vitrina')
        self.assertNotContains(pagina, 'value="CPU" selected')
        self.assertNotContains(pagina, 'name="origen"')

    def test_home_reemplaza_el_proveedor(self):
        respuesta = self._aplicar(
            origen='home',
            heredado_proveedor=str(self.amd.pk),
            proveedor=str(self.intel.pk),
        )
        self.assertRedirects(respuesta, _destino(self.url, [('proveedor', self.intel.pk)]))
        pagina = self.client.get(_destino(self.url, [('proveedor', self.intel.pk)]))
        self.assertContains(pagina, 'Core de vitrina')
        self.assertNotContains(pagina, 'Ryzen de vitrina')
        self.assertNotContains(pagina, f'value="{self.amd.pk}" selected')

    def test_home_al_elegir_proveedor_suelta_la_categoria_y_conserva_precio_y_orden(self):
        respuesta = self._aplicar(
            origen='home',
            heredado_categoria='Disco Duro HDD',
            categoria='Disco Duro HDD',
            proveedor=str(self.intel.pk),
            precio='50-100',
            orden='precio_asc',
        )
        self.assertRedirects(respuesta, _destino(self.url, [
            ('proveedor', self.intel.pk),
            ('precio', '50-100'),
            ('orden', 'precio_asc'),
        ]))
        pagina = self.client.get(respuesta.url)
        self.assertContains(pagina, 'Core de vitrina')
        self.assertNotContains(pagina, 'Barracuda')
        self.assertNotContains(pagina, 'categoria=')
        self.assertNotContains(pagina, 'origen=home')

    def test_home_al_elegir_categoria_suelta_la_busqueda(self):
        respuesta = self._aplicar(
            origen='home',
            q='Memoria RAM',
            heredado_q='Memoria RAM',
            categoria='Fuente de Poder',
        )
        self.assertRedirects(respuesta, _destino(self.url, [('categoria', 'Fuente de Poder')]))
        pagina = self.client.get(respuesta.url)
        self.assertContains(pagina, 'RM750')
        self.assertNotContains(pagina, 'Vengeance')
        self.assertNotIn('q=', pagina.request['QUERY_STRING'])
        formulario = pagina.content.decode().split('id="filtros-catalogo"', 1)[1].split('</form>', 1)[0]
        self.assertNotIn('name="q"', formulario)

    def test_dentro_de_tienda_categoria_y_proveedor_se_combinan(self):
        respuesta = self._aplicar(categoria='CPU', proveedor=str(self.amd.pk))
        self.assertRedirects(respuesta, _destino(self.url, [
            ('categoria', 'CPU'),
            ('proveedor', self.amd.pk),
        ]))
        pagina = self.client.get(respuesta.url)
        self.assertContains(pagina, 'Ryzen de vitrina')
        self.assertNotContains(pagina, 'Core de vitrina')
        self.assertNotContains(pagina, 'Vengeance')
        self.assertContains(pagina, 'id="conteo-categoria" aria-live="polite">1</span>')
        self.assertContains(pagina, 'id="conteo-marca" aria-live="polite">1</span>')
        self.assertEqual(pagina.content.decode().count('class="catalog-chip"'), 2)

    def test_combinacion_sin_resultados_ofrece_quitar_filtros_y_un_chip(self):
        pagina = self.client.get(self.url, {'categoria': 'CPU', 'proveedor': self.seasonic.pk})
        self.assertContains(pagina, 'No se encontraron productos')
        self.assertContains(pagina, 'Quitar filtros')
        self.assertNotContains(pagina, 'Core de vitrina')
        self.assertNotContains(pagina, 'RM750')
        html = pagina.content.decode()
        trozo = html[max(0, html.index('Quitar categoría') - 250):html.index('Quitar categoría')]
        self.assertIn(f'proveedor={self.seasonic.pk}', trozo)
        self.assertNotIn('categoria=', trozo)
        solo_marca = self.client.get(self.url, {'proveedor': self.seasonic.pk})
        self.assertContains(solo_marca, 'RM750')
        self.assertNotContains(solo_marca, 'Core de vitrina')
        self.assertNotContains(self.client.get(self.url), 'Quitar filtros')

    def test_limpiar_y_el_chip_quitan_lo_que_corresponde(self):
        pagina = self.client.get(self.url, {'categoria': 'CPU', 'proveedor': self.intel.pk, 'precio': '50-100'})
        self.assertContains(pagina, 'href="/tienda/"')
        self.assertContains(self.client.get(self.url), 'Barracuda')
        self.assertContains(self.client.get(self.url), 'RM750')
        html = pagina.content.decode()
        marca = html.index('Quitar precio')
        enlace = html.rfind('href="', 0, marca)
        href = html[enlace:html.index('"', enlace + 6)]
        self.assertIn('categoria=CPU', href)
        self.assertIn(f'proveedor={self.intel.pk}', href)
        self.assertNotIn('precio=', href)
        sin_precio = self.client.get(self.url, {'categoria': 'CPU', 'proveedor': self.intel.pk})
        self.assertContains(sin_precio, 'Core de vitrina')
        self.assertNotContains(sin_precio, 'option value="50-100" selected')

    def test_la_url_no_repite_categoria_ni_proveedor(self):
        categorias = self.client.get(f'{self.url}?categoria=CPU&categoria=Memoria+RAM')
        self.assertRedirects(categorias, _destino(self.url, [('categoria', 'Memoria RAM')]))
        final = self.client.get(f'{self.url}?categoria=CPU&categoria=Memoria+RAM', follow=True)
        self.assertEqual(final.request['QUERY_STRING'].count('categoria='), 1)
        self.assertNotIn('CPU', final.request['QUERY_STRING'])

        proveedores = self.client.get(f'{self.url}?proveedor={self.amd.pk}&proveedor={self.intel.pk}')
        self.assertRedirects(proveedores, _destino(self.url, [('proveedor', self.intel.pk)]))
        final = self.client.get(
            f'{self.url}?proveedor={self.amd.pk}&proveedor={self.intel.pk}',
            follow=True,
        )
        self.assertEqual(final.request['QUERY_STRING'].count('proveedor='), 1)
        self.assertNotIn(f'proveedor={self.amd.pk}', final.request['QUERY_STRING'])

    def test_la_paginacion_conserva_el_filtro_heredado_sin_duplicarlo(self):
        with patch('core.views.TIENDA_PAGE_SIZE', 1):
            pagina = self.client.get(self.url, {'categoria': 'CPU', 'origen': 'home'})
        self.assertContains(pagina, 'page=2')
        consulta = pagina.context['pagination_query']
        self.assertEqual(consulta.count('categoria='), 1)
        self.assertIn('origen=home', consulta)
        self.assertNotIn('aplicar', consulta)

    def test_cada_url_vuelve_a_su_propio_estado(self):
        llegada_url = _destino(self.url, [('categoria', 'CPU'), ('origen', 'home')])
        llegada = self.client.get(llegada_url)
        self.assertContains(llegada, 'value="CPU" selected')
        self.assertNotContains(llegada, 'value="Memoria RAM" selected')
        cambio = self._aplicar(origen='home', heredado_categoria='CPU', categoria='Memoria RAM')
        self.assertRedirects(cambio, _destino(self.url, [('categoria', 'Memoria RAM')]))
        self.assertContains(self.client.get(cambio.url), 'value="Memoria RAM" selected')
        self.assertNotContains(self.client.get(cambio.url), 'value="CPU" selected')
        vuelta = self.client.get(llegada_url)
        self.assertContains(vuelta, 'value="CPU" selected')
        self.assertNotContains(vuelta, 'value="Memoria RAM" selected')

    def test_el_movil_usa_el_mismo_formulario_y_las_mismas_reglas(self):
        html = self.client.get(self.url).content.decode()
        self.assertEqual(html.count('id="filtros-catalogo"'), 1)
        panel = html.split('id="panel-filtros"', 1)[1].split('id="filtros-overlay"', 1)[0]
        self.assertIn('name="categoria"', panel)
        self.assertIn('name="proveedor"', panel)
        self.assertNotIn(' multiple', panel)
        js = Path(settings.BASE_DIR, 'core/static/core/js/tienda-filtros.js').read_text(encoding='utf-8')
        envio = js.split("addEventListener('submit'", 1)[1].split('var panel', 1)[0]
        self.assertNotIn('matchMedia', envio)
        self.assertNotIn('.append(', js)
        self.assertIn("params.set('categoria'", js)
        self.assertIn("params.delete('origen')", js)
        self.assertNotIn('orden.form.submit()', js)

    def test_la_busqueda_sigue_siendo_independiente_y_combinable(self):
        busqueda = self.client.get(self.url, {'q': 'Ryzen'})
        self.assertContains(busqueda, 'Ryzen de vitrina')
        self.assertNotContains(busqueda, 'Core de vitrina')
        combinada = self.client.get(self.url, {'q': 'vitrina', 'categoria': 'CPU'})
        self.assertContains(combinada, 'Ryzen de vitrina')
        self.assertContains(combinada, 'Core de vitrina')
        self.assertNotContains(combinada, 'Barracuda')
        self.assertContains(combinada, 'name="q" value="vitrina"')

    def test_las_tarjetas_de_inicio_marcan_el_origen(self):
        inicio = self.client.get(reverse('core:index'))
        self.assertContains(inicio, 'categoria=CPU')
        self.assertContains(inicio, 'origen=home')
        self.assertContains(inicio, 'categoria=Placa%20Madre')
        self.assertContains(inicio, 'q=Almacenamiento')
        self.assertNotContains(inicio, 'q=Procesador')
        self.assertNotContains(inicio, 'q=Memoria')
        plantilla = Path(settings.BASE_DIR, 'core/templates/core/index.html').read_text(encoding='utf-8')
        self.assertIn('proveedor={{ proveedor.id }}&origen=home', plantilla)
