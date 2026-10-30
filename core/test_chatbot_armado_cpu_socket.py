"""El armado automático no se queda con un CPU sin placa compatible."""
from decimal import Decimal

from django.test import TestCase, override_settings

from core.chatbot.armado_chat import ejecutar_armado_chat
from core.models import (
    AlmacenamientoSSD,
    FuenteDePoder,
    Gabinete,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    Proveedor,
    RefrigeracionCooler,
    TarjetaGrafica,
)


def _catalogo_completable(marca):
    Procesador.objects.create(
        proveedor=marca,
        nombre='CPU AM5 viable',
        precio=Decimal('120000'),
        stock=5,
        socket='AM5',
        nucleos=6,
        frecuencia_base=Decimal('4.0'),
        potencia_referencia_watts=65,
    )
    PlacaMadre.objects.create(
        proveedor=marca,
        nombre='Placa AM5',
        precio=Decimal('90000'),
        stock=5,
        socket_cpu='AM5',
        chipset='B650',
        formato='ATX',
        ranuras_ram=4,
        tipo_ram_soportado='DDR5',
        formato_ram_soportado='DIMM',
        capacidad_maxima_ram_gb=128,
    )
    MemoriaRam.objects.create(
        proveedor=marca,
        nombre='DDR5 16',
        precio=Decimal('45000'),
        stock=5,
        capacidad_gb=16,
        tipo_ddr='DDR5',
        velocidad_mhz=5600,
        modulos_por_producto=1,
        capacidad_modulo_gb=16,
        formato_ram='DIMM',
    )
    TarjetaGrafica.objects.create(
        proveedor=marca,
        nombre='GPU compatible',
        precio=Decimal('250000'),
        stock=3,
        vram_gb=8,
        tipo_memoria='GDDR6',
        interfaz='PCIe 4.0',
        largo_mm=280,
        consumo_referencia_watts=180,
    )
    AlmacenamientoSSD.objects.create(
        proveedor=marca,
        nombre='SSD 1TB',
        precio=Decimal('55000'),
        stock=5,
        capacidad_gb=1000,
        interfaz='NVMe PCIe 4.0',
        formato='M.2 2280',
    )
    Gabinete.objects.create(
        proveedor=marca,
        nombre='Gabinete ATX',
        precio=Decimal('40000'),
        stock=5,
        formato_soporte='ATX',
        material='Acero',
        largo_max_gpu_mm=320,
    )
    RefrigeracionCooler.objects.create(
        proveedor=marca,
        nombre='Cooler AM5',
        precio=Decimal('25000'),
        stock=5,
        tipo='Aire',
        socket_compatibles='AM5, LGA1700',
    )
    FuenteDePoder.objects.create(
        proveedor=marca,
        nombre='Fuente 650W',
        precio=Decimal('60000'),
        stock=5,
        potencia_watts=650,
        certificacion='80+ Bronze',
        modular=False,
    )


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class CpuSinPlacaTests(TestCase):
    def test_el_cpu_mas_barato_sin_placa_no_impide_el_armado(self):
        marca = Proveedor.objects.create(nombre='SocketChat')
        Procesador.objects.create(
            proveedor=marca,
            nombre='Proce 2000',
            precio=Decimal('2000'),
            stock=5,
            socket='LGA1200',
            nucleos=2,
            frecuencia_base=Decimal('3.0'),
        )
        _catalogo_completable(marca)
        data = ejecutar_armado_chat('armame un PC gamer con presupuesto 700000')
        self.assertEqual(data.get('response_type'), 'pc_build')
        self.assertNotIn('Proce 2000', data['reply'])
        self.assertIn('CPU AM5 viable', data['reply'])
        propuesta = data['build_proposal']
        self.assertLessEqual(propuesta['total_clp'], 700_000)
        self.assertEqual(
            propuesta['total_clp'],
            sum(item['precio_clp'] * item['cantidad'] for item in propuesta['componentes']),
        )
        ids = {item['tipo']: item['id'] for item in propuesta['componentes']}
        cpu = Procesador.objects.get(pk=ids['procesador'])
        placa = PlacaMadre.objects.get(pk=ids['placa_madre'])
        self.assertEqual(cpu.socket, 'AM5')
        self.assertEqual(placa.socket_cpu, 'AM5')
        self.assertEqual(cpu.precio, Decimal('120000'))
        self.assertEqual(placa.precio, Decimal('90000'))

    def test_sin_armado_compatible_el_mensaje_explica_el_fallo(self):
        marca = Proveedor.objects.create(nombre='SocketVacio')
        Procesador.objects.create(
            proveedor=marca,
            nombre='Proce 2000',
            precio=Decimal('2000'),
            stock=5,
            socket='LGA1200',
            nucleos=2,
            frecuencia_base=Decimal('3.0'),
        )
        Procesador.objects.create(
            proveedor=marca,
            nombre='CPU AM5 sin placa',
            precio=Decimal('50000'),
            stock=4,
            socket='AM5',
            nucleos=6,
            frecuencia_base=Decimal('4.0'),
        )
        PlacaMadre.objects.create(
            proveedor=marca,
            nombre='Placa LGA1700',
            precio=Decimal('80000'),
            stock=5,
            socket_cpu='LGA1700',
            chipset='Z790',
            formato='ATX',
            ranuras_ram=4,
            tipo_ram_soportado='DDR5',
        )
        data = ejecutar_armado_chat('armame un PC gamer con presupuesto 700000')
        self.assertEqual(data.get('response_type'), 'pc_build_failed')
        self.assertIn('compatible', data['reply'].lower())
        self.assertNotIn('698', data['reply'])
        self.assertNotIn('Proce 2000', data['reply'])
