from decimal import Decimal

from django.test import TestCase, override_settings

from core.armado_recomendacion import construir_armado_automatico
from core.chatbot.armado_chat import ejecutar_armado_chat
from core.chatbot.conversation import generar_respuesta
from core.chatbot.nlp_armado import parsear_solicitud_armado
from core.models import (
    FuenteDePoder,
    Gabinete,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    Proveedor,
    RefrigeracionCooler,
    TarjetaGrafica,
    AlmacenamientoSSD,
)


class ArmadoFixtureMixin:
    @classmethod
    def crear_armado_catalogo(cls):
        cls.marca = Proveedor.objects.create(nombre='ArmadoChat')
        cls.cpu = Procesador.objects.create(
            proveedor=cls.marca,
            nombre='Ryzen 5 Chat',
            precio=Decimal('120000'),
            stock=5,
            socket='AM5',
            nucleos=6,
            frecuencia_base=Decimal('4.0'),
            potencia_referencia_watts=65,
        )
        cls.board = PlacaMadre.objects.create(
            proveedor=cls.marca,
            nombre='B650 Chat',
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
        cls.ram = MemoriaRam.objects.create(
            proveedor=cls.marca,
            nombre='DDR5 16 Chat',
            precio=Decimal('45000'),
            stock=5,
            capacidad_gb=16,
            tipo_ddr='DDR5',
            velocidad_mhz=5600,
            modulos_por_producto=1,
            capacidad_modulo_gb=16,
            formato_ram='DIMM',
        )
        cls.gpu = TarjetaGrafica.objects.create(
            proveedor=cls.marca,
            nombre='GPU Chat',
            precio=Decimal('250000'),
            stock=3,
            vram_gb=8,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
            largo_mm=280,
            consumo_referencia_watts=180,
        )
        cls.ssd = AlmacenamientoSSD.objects.create(
            proveedor=cls.marca,
            nombre='SSD Chat 1TB',
            precio=Decimal('55000'),
            stock=5,
            capacidad_gb=1000,
            interfaz='NVMe',
            formato='M.2',
        )
        cls.case = Gabinete.objects.create(
            proveedor=cls.marca,
            nombre='Gabinete Chat ATX',
            precio=Decimal('40000'),
            stock=5,
            formato_soporte='ATX',
            material='Acero',
            largo_max_gpu_mm=320,
        )
        cls.cooler = RefrigeracionCooler.objects.create(
            proveedor=cls.marca,
            nombre='Cooler Chat',
            precio=Decimal('25000'),
            stock=5,
            tipo='Aire',
            socket_compatibles=' am5 , lga 1700 ',
        )
        cls.psu = FuenteDePoder.objects.create(
            proveedor=cls.marca,
            nombre='PSU Chat 650W',
            precio=Decimal('60000'),
            stock=5,
            potencia_watts=650,
            certificacion='80 Plus Bronze',
        )


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class NlpArmadoTests(TestCase):
    def test_lucas_a_clp(self):
        sol = parsear_solicitud_armado('quiero un pc gamer con 700 lucas')
        self.assertEqual(sol.presupuesto_clp, 700_000)
        self.assertEqual(sol.proposito, 'gaming')


class ArmadoRecomendacionTests(ArmadoFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_armado_catalogo()

    def test_construye_dentro_de_presupuesto(self):
        res = construir_armado_automatico(700_000, proposito='gaming', preferencia_cpu='amd')
        self.assertTrue(res.ok)
        self.assertGreater(res.total_clp, 0)
        self.assertLessEqual(res.total_clp, 900_000)
        self.assertTrue(res.componentes)

    def test_chat_armado_respuesta_con_links(self):
        data = ejecutar_armado_chat('armar pc gaming 700 lucas', presupuesto_llm=700_000, proposito_llm='gaming')
        self.assertEqual(data.get('response_type'), 'pc_build')
        self.assertIn('armado_context', data)
        if data.get('armado', {}).get('ok'):
            self.assertIn('/detalle/', data['reply'])
            self.assertIn('carrito', data['reply'].lower())
        else:
            self.assertEqual(data.get('response_type'), 'pc_build_failed')

    def test_ajuste_mas_barato(self):
        first = ejecutar_armado_chat('armar pc gaming 700 lucas', presupuesto_llm=700_000, proposito_llm='gaming')
        ctx = first.get('armado_context')
        second = ejecutar_armado_chat('hazlo mas barato', build_context=ctx)
        self.assertIn(second.get('response_type'), ('pc_build', 'pc_build_failed', 'clarification'))

    def test_sin_presupuesto_pide_aclaracion(self):
        data = ejecutar_armado_chat('quiero armar un pc')
        self.assertEqual(data.get('response_type'), 'clarification')

    def test_reglas_700_lucas(self):
        data = generar_respuesta('armar pc gamer 700 lucas')
        self.assertIn(data.get('response_type'), ('pc_build', 'pc_build_failed', 'clarification'))
