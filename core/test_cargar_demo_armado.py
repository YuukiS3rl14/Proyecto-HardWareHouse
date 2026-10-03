import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from core.management.commands.cargar_demo_armado import CATALOGO_DEMO, PROVEEDOR_DEMO
from core.management.commands.cargar_demo_armado import (
    FUENTES_DEMO,
    GPU_DEMO,
    GPUS_LARGO_DEMO,
    LARGO_GABINETE_DEMO,
    PLACAS_RAM_DEMO,
    POTENCIA_CPU_DEMO,
    RAM_DEMO,
)
from core.models import (
    AlmacenamientoHDD,
    AlmacenamientoSSD,
    FuenteDePoder,
    Gabinete,
    ItemCarrito,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    Proveedor,
    RefrigeracionCooler,
    TarjetaGrafica,
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
        self.assertIsNone(previo.potencia_referencia_watts)
        self.assertIsNone(ajeno.potencia_referencia_watts)
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
        self.assertIsNone(Procesador.objects.get(nombre='DEMO CPU AM5').potencia_referencia_watts)
        self.assertIsNone(Gabinete.objects.get(nombre='DEMO Gabinete ATX').largo_max_gpu_mm)
        ram_demo = MemoriaRam.objects.get(nombre='DEMO RAM DDR5')
        self.assertIsNone(ram_demo.modulos_por_producto)
        self.assertIsNone(ram_demo.capacidad_modulo_gb)
        self.assertIsNone(ram_demo.formato_ram)
        self.assertIsNone(
            PlacaMadre.objects.get(nombre='DEMO Placa AM5 DDR5 ATX').capacidad_maxima_ram_gb
        )
        self.assertEqual(TarjetaGrafica.objects.count(), 0)
        self.assertEqual(FuenteDePoder.objects.count(), 0)


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
            ('gabinete', self.gabinete_atx),
            ('refrigeracion', self.cooler_am5),
            ('almacenamiento_ssd', self.ssd),
            ('almacenamiento_hdd', self.hdd),
        ])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['estado'], 'incompleto')
        self.assertEqual(ItemCarrito.objects.count(), 6)
        item_ssd = ItemCarrito.objects.get(almacenamiento_ssd__isnull=False)
        item_hdd = ItemCarrito.objects.get(almacenamiento_hdd__isnull=False)
        self.assertEqual(item_ssd.almacenamiento_ssd_id, self.ssd.id)
        self.assertIsNone(item_ssd.almacenamiento_hdd_id)
        self.assertEqual(item_hdd.almacenamiento_hdd_id, self.hdd.id)
        self.assertIsNone(item_hdd.almacenamiento_ssd_id)


@override_settings(DEBUG=True)
class CargarDemoPotenciaTests(TestCase):
    def test_sin_la_opcion_no_escribe_potencia(self):
        call_command('cargar_demo_armado')

        self.assertIsNone(Procesador.objects.get(nombre='DEMO CPU AM5').potencia_referencia_watts)
        self.assertFalse(TarjetaGrafica.objects.filter(nombre=GPU_DEMO['nombre']).exists())
        self.assertFalse(FuenteDePoder.objects.filter(nombre='DEMO Fuente 550W').exists())

    def test_la_opcion_solo_completa_las_piezas_demo(self):
        marca = Proveedor.objects.create(nombre='Marca real')
        real = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU real',
            precio=Decimal('222.00'),
            stock=2,
            socket='LGA1700',
            nucleos=4,
            frecuencia_base=Decimal('3.00'),
        )
        demo_previo = Procesador.objects.create(
            proveedor=marca,
            nombre='DEMO CPU AM5',
            descripcion='No tocar el resto',
            precio=Decimal('1.00'),
            stock=1,
            socket='AM4',
            nucleos=2,
            frecuencia_base=Decimal('1.10'),
        )
        gpu_previa = TarjetaGrafica.objects.create(
            proveedor=marca,
            nombre=GPU_DEMO['nombre'],
            descripcion='GPU ya cargada',
            precio=Decimal('5.00'),
            stock=1,
            vram_gb=4,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
        )

        call_command('cargar_demo_armado', potencia=True)
        call_command('cargar_demo_armado', potencia=True)

        real.refresh_from_db()
        demo_previo.refresh_from_db()
        gpu_previa.refresh_from_db()
        self.assertIsNone(real.potencia_referencia_watts)
        self.assertEqual(real.precio, Decimal('222.00'))
        self.assertEqual(demo_previo.precio, Decimal('1.00'))
        self.assertEqual(demo_previo.socket, 'AM4')
        self.assertEqual(demo_previo.descripcion, 'No tocar el resto')
        self.assertEqual(demo_previo.potencia_referencia_watts, POTENCIA_CPU_DEMO['DEMO CPU AM5'])
        self.assertEqual(gpu_previa.precio, Decimal('5.00'))
        self.assertEqual(gpu_previa.vram_gb, 4)
        self.assertEqual(gpu_previa.consumo_referencia_watts, GPU_DEMO['consumo_referencia_watts'])
        self.assertEqual(gpu_previa.potencia_minima_fuente_watts, GPU_DEMO['potencia_minima_fuente_watts'])
        self.assertEqual(TarjetaGrafica.objects.filter(nombre=GPU_DEMO['nombre']).count(), 1)
        self.assertEqual(FuenteDePoder.objects.count(), len(FUENTES_DEMO))
        for item in FUENTES_DEMO:
            fuente = FuenteDePoder.objects.get(nombre=item['nombre'])
            self.assertEqual(fuente.potencia_watts, item['potencia_watts'])
            self.assertTrue(fuente.nombre.startswith('DEMO'))

    def test_rechaza_la_opcion_si_debug_esta_apagado(self):
        with override_settings(DEBUG=False):
            with self.assertRaises(CommandError):
                call_command('cargar_demo_armado', potencia=True)

        self.assertEqual(FuenteDePoder.objects.count(), 0)
        self.assertEqual(Procesador.objects.count(), 0)


@override_settings(DEBUG=True)
class CargarDemoDimensionesTests(TestCase):
    def test_sin_la_opcion_no_escribe_largos(self):
        call_command('cargar_demo_armado')

        self.assertIsNone(Gabinete.objects.get(nombre='DEMO Gabinete ATX').largo_max_gpu_mm)
        self.assertFalse(TarjetaGrafica.objects.filter(nombre='DEMO GPU 280mm').exists())
        self.assertFalse(TarjetaGrafica.objects.filter(nombre='DEMO GPU 321mm').exists())

    def test_la_opcion_solo_completa_las_piezas_demo(self):
        marca = Proveedor.objects.create(nombre='Marca real de medidas')
        real = Gabinete.objects.create(
            proveedor=marca, nombre='Gabinete real', precio=Decimal('10.00'), stock=1,
            formato_soporte='ATX', material='Acero',
        )
        demo = Gabinete.objects.create(
            proveedor=marca, nombre='DEMO Gabinete ATX', descripcion='No tocar formato',
            precio=Decimal('2.00'), stock=1, formato_soporte='Mini-ITX', material='Acero',
        )
        gpu_potencia = TarjetaGrafica.objects.create(
            proveedor=marca, nombre='DEMO GPU', descripcion='Ya existía',
            precio=Decimal('3.00'), stock=1, vram_gb=4, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
        )

        call_command('cargar_demo_armado', dimensiones=True)
        call_command('cargar_demo_armado', dimensiones=True)

        real.refresh_from_db()
        demo.refresh_from_db()
        gpu_potencia.refresh_from_db()
        self.assertIsNone(real.largo_max_gpu_mm)
        self.assertEqual(demo.precio, Decimal('2.00'))
        self.assertEqual(demo.formato_soporte, 'Mini-ITX')
        self.assertEqual(demo.descripcion, 'No tocar formato')
        self.assertEqual(demo.largo_max_gpu_mm, LARGO_GABINETE_DEMO['DEMO Gabinete ATX'])
        self.assertEqual(gpu_potencia.precio, Decimal('3.00'))
        self.assertEqual(gpu_potencia.vram_gb, 4)
        self.assertEqual(gpu_potencia.largo_mm, 280)
        self.assertEqual(TarjetaGrafica.objects.filter(nombre='DEMO GPU').count(), 1)
        for item in GPUS_LARGO_DEMO:
            gpu = TarjetaGrafica.objects.get(nombre=item['nombre'])
            self.assertEqual(gpu.largo_mm, item['largo_mm'])
            self.assertEqual(TarjetaGrafica.objects.filter(nombre=item['nombre']).count(), 1)

    def test_rechaza_la_opcion_si_debug_esta_apagado(self):
        with override_settings(DEBUG=False):
            with self.assertRaises(CommandError):
                call_command('cargar_demo_armado', dimensiones=True)

        self.assertEqual(TarjetaGrafica.objects.count(), 0)
        self.assertEqual(Gabinete.objects.count(), 0)


@override_settings(DEBUG=True)
class CargarDemoRamTests(TestCase):
    def test_sin_la_opcion_no_inventa_modulos_ni_formato(self):
        call_command('cargar_demo_armado')

        ram = MemoriaRam.objects.get(nombre='DEMO RAM DDR4')
        self.assertIsNone(ram.modulos_por_producto)
        self.assertIsNone(ram.capacidad_modulo_gb)
        self.assertIsNone(ram.formato_ram)
        self.assertFalse(MemoriaRam.objects.filter(nombre='DEMO RAM módulo DDR5 16GB').exists())
        self.assertIsNone(
            PlacaMadre.objects.get(nombre='DEMO Placa AM5 DDR5 ATX').formato_ram_soportado
        )

    def test_la_opcion_solo_completa_las_piezas_previstas(self):
        marca = Proveedor.objects.create(nombre='Marca real de RAM')
        real = MemoriaRam.objects.create(
            proveedor=marca, nombre='RAM real', precio=Decimal('10.00'), stock=1,
            capacidad_gb=8, tipo_ddr='DDR4', velocidad_mhz=3200,
        )
        previa = MemoriaRam.objects.create(
            proveedor=marca, nombre='DEMO RAM DDR5', descripcion='No convertir en kit',
            precio=Decimal('1.00'), stock=1, capacidad_gb=16, tipo_ddr='DDR5', velocidad_mhz=5600,
        )
        placa_real = PlacaMadre.objects.create(
            proveedor=marca, nombre='Placa real', precio=Decimal('20.00'), stock=1,
            socket_cpu='AM4', chipset='B550', formato='ATX', ranuras_ram=2, tipo_ram_soportado='DDR4',
        )

        call_command('cargar_demo_armado', ram=True)
        call_command('cargar_demo_armado', ram=True)

        real.refresh_from_db()
        previa.refresh_from_db()
        placa_real.refresh_from_db()
        self.assertIsNone(real.modulos_por_producto)
        self.assertIsNone(real.formato_ram)
        self.assertEqual(real.precio, Decimal('10.00'))
        self.assertEqual(previa.precio, Decimal('1.00'))
        self.assertEqual(previa.descripcion, 'No convertir en kit')
        self.assertIsNone(previa.modulos_por_producto)
        self.assertIsNone(placa_real.formato_ram_soportado)
        self.assertIsNone(placa_real.capacidad_maxima_ram_gb)
        for item in RAM_DEMO:
            producto = MemoriaRam.objects.get(nombre=item['nombre'])
            self.assertEqual(MemoriaRam.objects.filter(nombre=item['nombre']).count(), 1)
            self.assertEqual(producto.modulos_por_producto, item['campos']['modulos_por_producto'])
            self.assertEqual(producto.capacidad_gb, item['campos']['capacidad_gb'])
            self.assertEqual(producto.capacidad_modulo_gb, item['campos']['capacidad_modulo_gb'])
            self.assertEqual(producto.formato_ram, item['campos']['formato_ram'])
        for nombre, campos in PLACAS_RAM_DEMO.items():
            placa = PlacaMadre.objects.get(nombre=nombre)
            self.assertEqual(placa.formato_ram_soportado, campos['formato_ram_soportado'])
            self.assertEqual(placa.capacidad_maxima_ram_gb, campos['capacidad_maxima_ram_gb'])

    def test_rechaza_la_opcion_si_debug_esta_apagado(self):
        with override_settings(DEBUG=False):
            with self.assertRaises(CommandError):
                call_command('cargar_demo_armado', ram=True)

        self.assertEqual(MemoriaRam.objects.count(), 0)
