import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from core.management.commands.cargar_demo_armado import CATALOGO_DEMO, PROVEEDOR_DEMO
from core.models import (
    AlmacenamientoHDD,
    AlmacenamientoSSD,
    Gabinete,
    ItemCarrito,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    Proveedor,
    RefrigeracionCooler,
)


@override_settings(DEBUG=True)
class CargarDemoArmadoTests(TestCase):
    def test_rechaza_si_debug_esta_apagado(self):
        with override_settings(DEBUG=False):
            with self.assertRaises(CommandError):
                call_command('cargar_demo_armado')

        self.assertEqual(Procesador.objects.count(), 0)
        self.assertEqual(Proveedor.objects.count(), 0)

    def test_segunda_ejecucion_no_duplica_ni_modifica(self):
        marca = Proveedor.objects.create(nombre='Marca existente')
        ajeno = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU que no es demo',
            precio=Decimal('111.00'),
            stock=3,
            socket='LGA1700',
            nucleos=4,
            frecuencia_base=Decimal('2.50'),
        )
        previo = Procesador.objects.create(
            proveedor=marca,
            nombre='DEMO CPU AM5',
            descripcion='No tocar',
            precio=Decimal('1.00'),
            stock=1,
            socket='AM4',
            nucleos=2,
            frecuencia_base=Decimal('1.10'),
        )

        call_command('cargar_demo_armado')
        call_command('cargar_demo_armado')

        previo.refresh_from_db()
        ajeno.refresh_from_db()
        self.assertEqual(previo.precio, Decimal('1.00'))
        self.assertEqual(previo.stock, 1)
        self.assertEqual(previo.socket, 'AM4')
        self.assertEqual(previo.descripcion, 'No tocar')
        self.assertEqual(previo.proveedor_id, marca.id)
        self.assertEqual(ajeno.precio, Decimal('111.00'))
        self.assertEqual(Procesador.objects.filter(nombre='DEMO CPU AM5').count(), 1)
        self.assertEqual(Procesador.objects.filter(nombre='DEMO CPU AM4').count(), 1)
        self.assertEqual(Proveedor.objects.filter(nombre=PROVEEDOR_DEMO).count(), 1)
        self.assertEqual(PlacaMadre.objects.count(), 2)
        self.assertEqual(MemoriaRam.objects.count(), 2)
        self.assertEqual(Gabinete.objects.count(), 2)
        self.assertEqual(RefrigeracionCooler.objects.count(), 2)
        self.assertEqual(AlmacenamientoSSD.objects.count(), 1)
        self.assertEqual(AlmacenamientoHDD.objects.count(), 1)

    def test_crea_el_catalogo_con_stock_y_especificaciones(self):
        call_command('cargar_demo_armado')

        for item in CATALOGO_DEMO:
            producto = item['modelo'].objects.get(nombre=item['nombre'])
            self.assertGreater(producto.stock, 0)
            self.assertTrue(producto.nombre.startswith('DEMO'))
            for campo, valor in item['campos'].items():
                self.assertEqual(getattr(producto, campo), valor)

        self.assertEqual(Procesador.objects.get(nombre='DEMO CPU AM4').socket, 'AM4')
        self.assertEqual(Procesador.objects.get(nombre='DEMO CPU AM5').socket, 'AM5')
        self.assertEqual(PlacaMadre.objects.get(nombre='DEMO Placa AM4 DDR4 ATX').tipo_ram_soportado, 'DDR4')
        self.assertEqual(PlacaMadre.objects.get(nombre='DEMO Placa AM5 DDR5 ATX').tipo_ram_soportado, 'DDR5')
        self.assertEqual(Gabinete.objects.get(nombre='DEMO Gabinete Mini-ITX').formato_soporte, 'Mini-ITX')
        self.assertEqual(RefrigeracionCooler.objects.get(nombre='DEMO Cooler AM4').socket_compatibles, 'AM4')
        self.assertEqual(RefrigeracionCooler.objects.get(nombre='DEMO Cooler AM5').socket_compatibles, 'AM5')


@override_settings(DEBUG=True)
class DemoArmadoCarritoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('cargar_demo_armado')
        cls.user = User.objects.create_user('demoarmado', 'demoarmado@example.com', 'clave-demo-armado')
        cls.cpu_am5 = Procesador.objects.get(nombre='DEMO CPU AM5')
        cls.placa_am4 = PlacaMadre.objects.get(nombre='DEMO Placa AM4 DDR4 ATX')
        cls.placa_am5 = PlacaMadre.objects.get(nombre='DEMO Placa AM5 DDR5 ATX')
        cls.ram_ddr4 = MemoriaRam.objects.get(nombre='DEMO RAM DDR4')
        cls.ram_ddr5 = MemoriaRam.objects.get(nombre='DEMO RAM DDR5')
        cls.gabinete_mini = Gabinete.objects.get(nombre='DEMO Gabinete Mini-ITX')
        cls.gabinete_atx = Gabinete.objects.get(nombre='DEMO Gabinete ATX')
        cls.cooler_am5 = RefrigeracionCooler.objects.get(nombre='DEMO Cooler AM5')
        cls.ssd = AlmacenamientoSSD.objects.get(nombre='DEMO SSD NVMe 1TB')
        cls.hdd = AlmacenamientoHDD.objects.get(nombre='DEMO HDD 2TB')

    def setUp(self):
        self.client.force_login(self.user)

    def post_armado(self, pares):
        componentes = [{'tipo': tipo, 'id': producto.id} for tipo, producto in pares]
        return self.client.post(
            reverse('core:agregar_armado_al_carrito'),
            data=json.dumps({'componentes': componentes}),
            content_type='application/json',
        )

    def test_cpu_am5_con_placa_am4_no_cambia_el_carrito(self):
        response = self.post_armado([
            ('procesador', self.cpu_am5),
            ('placa_madre', self.placa_am4),
        ])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['estado'], 'incompatible')
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_ram_ddr5_con_placa_ddr4_se_rechaza(self):
        response = self.post_armado([
            ('placa_madre', self.placa_am4),
            ('memoria_ram', self.ram_ddr5),
        ])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['estado'], 'incompatible')
        self.assertIn('DDR5', ' '.join(response.json()['motivos']))
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_placa_atx_con_gabinete_mini_itx_se_rechaza(self):
        response = self.post_armado([
            ('placa_madre', self.placa_am5),
            ('gabinete', self.gabinete_mini),
        ])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['estado'], 'incompatible')
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_seleccion_compatible_agrega_ssd_y_hdd_con_su_tipo(self):
        response = self.post_armado([
            ('procesador', self.cpu_am5),
            ('placa_madre', self.placa_am5),
            ('memoria_ram', self.ram_ddr5),
            ('gabinete', self.gabinete_atx),
            ('refrigeracion', self.cooler_am5),
            ('almacenamiento_ssd', self.ssd),
            ('almacenamiento_hdd', self.hdd),
        ])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['estado'], 'compatible')
        self.assertEqual(ItemCarrito.objects.count(), 7)
        item_ssd = ItemCarrito.objects.get(almacenamiento_ssd__isnull=False)
        item_hdd = ItemCarrito.objects.get(almacenamiento_hdd__isnull=False)
        self.assertEqual(item_ssd.almacenamiento_ssd_id, self.ssd.id)
        self.assertIsNone(item_ssd.almacenamiento_hdd_id)
        self.assertEqual(item_hdd.almacenamiento_hdd_id, self.hdd.id)
        self.assertIsNone(item_hdd.almacenamiento_ssd_id)
