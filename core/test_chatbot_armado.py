from decimal import Decimal

from django.test import TestCase, override_settings

from datetime import timedelta

from django.utils import timezone

from core.armado_recomendacion import construir_armado_automatico
from core.armado_servicio import crear_propuesta_pendiente_armado, revalidar_propuesta_armado
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


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class TransferenciaArmadoChatTests(ArmadoFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_armado_catalogo()

    def test_un_millon_se_interpreta_como_un_millon_clp(self):
        sol = parsear_solicitud_armado('armame un PC gamer por 1m')
        self.assertEqual(sol.presupuesto_clp, 1_000_000)
        self.assertEqual(sol.proposito, 'gaming')

    def test_presupuesto_bajo_no_inventa_piezas(self):
        res = construir_armado_automatico(100_000, proposito='gaming')
        self.assertFalse(res.ok)
        self.assertFalse(res.componentes)

    def test_sin_fuente_en_stock_el_armado_falla(self):
        self.psu.stock = 0
        self.psu.save(update_fields=['stock'])
        res = construir_armado_automatico(1_000_000, proposito='gaming', preferencia_cpu='amd')
        self.assertFalse(res.ok)
        self.assertIn('fuente', (res.motivo_fallo or '').lower())

    def test_propuesta_de_un_millon_se_revalida_y_transfiere(self):
        data = generar_respuesta('armame un PC gamer por 1m')
        self.assertEqual(data.get('response_type'), 'pc_build')
        propuesta = data.get('build_proposal') or {}
        self.assertLessEqual(propuesta.get('total_clp'), 1_000_000)
        tipos = {item['tipo'] for item in propuesta['componentes']}
        self.assertTrue({'procesador', 'placa_madre', 'memoria_ram', 'fuente_de_poder'} <= tipos)
        for item in propuesta['componentes']:
            self.assertTrue(item['id'])
            self.assertTrue(item['url_detalle'])
            self.assertGreaterEqual(item['stock'], item['cantidad'])
        ui = data.get('ui') or {}
        self.assertTrue(ui.get('apply_build'))
        self.assertIn('aplicar=1', ui.get('apply_path') or '')
        revalidada = revalidar_propuesta_armado(propuesta=data['proposal_pending'])
        self.assertTrue(revalidada.get('ok'))
        self.assertEqual(
            [(c['tipo'], c['id']) for c in revalidada['componentes']],
            [(c['tipo'], c['id']) for c in data['proposal_pending']['componentes']],
        )

    def test_propuesta_expirada_no_se_aplica(self):
        data = generar_respuesta('armame un PC gamer por 1m')
        propuesta = data['proposal_pending']
        propuesta['expires_at'] = (timezone.now() - timedelta(minutes=1)).isoformat()
        out = revalidar_propuesta_armado(propuesta=propuesta)
        self.assertFalse(out.get('ok'))
        self.assertTrue(out.get('expired'))

    def test_stock_cero_bloquea_la_propuesta(self):
        data = generar_respuesta('armame un PC gamer por 1m')
        self.cpu.stock = 0
        self.cpu.save(update_fields=['stock'])
        out = revalidar_propuesta_armado(propuesta=data['proposal_pending'])
        self.assertFalse(out.get('ok'))
        self.assertIn('stock', out.get('mensaje', '').lower())

    def test_socket_incompatible_no_se_transfiere(self):
        otra = PlacaMadre.objects.create(
            proveedor=self.marca,
            nombre='Placa LGA incompatible',
            precio=Decimal('80000'),
            stock=2,
            socket_cpu='LGA1700',
            chipset='B760',
            formato='ATX',
            ranuras_ram=4,
            tipo_ram_soportado='DDR5',
            formato_ram_soportado='DIMM',
            capacidad_maxima_ram_gb=128,
        )
        propuesta = crear_propuesta_pendiente_armado([
            {'tipo': 'procesador', 'id': self.cpu.pk, 'cantidad': 1},
            {'tipo': 'placa_madre', 'id': otra.pk, 'cantidad': 1},
        ])
        out = revalidar_propuesta_armado(propuesta=propuesta)
        self.assertFalse(out.get('ok'))
        self.assertIn('compatibilidad', out.get('mensaje', '').lower())

    def test_seguimiento_amd_y_mas_barato(self):
        first = generar_respuesta('armame un PC gamer por 1m')
        ctx = first.get('armado_context')
        cheaper = generar_respuesta('make it cheaper', build_context=ctx)
        self.assertIn(
            cheaper.get('response_type'),
            ('pc_build', 'pc_build_failed', 'build_pending_change', 'clarification'),
        )
        amd = generar_respuesta('use AMD', build_context=ctx)
        self.assertIn(amd.get('response_type'), ('pc_build', 'pc_build_failed'))
        gpu = generar_respuesta(
            'change the GPU',
            build_context=ctx,
            builder_componentes=ctx.get('componentes'),
        )
        self.assertIn(
            gpu.get('response_type'),
            ('build_pending_change', 'pc_build', 'pc_build_failed', 'clarification', 'build_analysis'),
        )
