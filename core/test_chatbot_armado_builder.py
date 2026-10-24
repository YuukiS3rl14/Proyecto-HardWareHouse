from decimal import Decimal

from django.test import TestCase, override_settings

from core.armado_servicio import analizar_armado, proponer_reemplazo, sanitizar_lista_componentes
from core.chatbot.armado_builder_chat import (
    ejecutar_analisis_armado_chat,
    intentar_confirmar_accion,
)
from core.models import (
    Gabinete,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    Proveedor,
    TarjetaGrafica,
)


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class ArmadoServicioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='BuilderBrand')
        cls.cpu = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Builder',
            precio=200000,
            stock=3,
            socket='AM5',
            nucleos=6,
            frecuencia_base=3.5,
            potencia_referencia_watts=65,
        )
        cls.mb = PlacaMadre.objects.create(
            proveedor=marca,
            nombre='MB Builder',
            precio=150000,
            stock=2,
            socket_cpu='AM5',
            formato='ATX',
            tipo_ram_soportado='DDR5',
            formato_ram_soportado='DIMM',
            ranuras_ram=2,
            capacidad_maxima_ram_gb=64,
        )
        cls.gpu_cara = TarjetaGrafica.objects.create(
            proveedor=marca,
            nombre='GPU Cara',
            precio=Decimal('500000'),
            stock=1,
            vram_gb=8,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
            largo_mm=280,
            consumo_referencia_watts=200,
            potencia_minima_fuente_watts=550,
        )
        cls.gpu_barata = TarjetaGrafica.objects.create(
            proveedor=marca,
            nombre='GPU Barata',
            precio=Decimal('250000'),
            stock=2,
            vram_gb=6,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
            largo_mm=240,
            consumo_referencia_watts=120,
            potencia_minima_fuente_watts=450,
        )
        Gabinete.objects.create(
            proveedor=marca,
            nombre='Case Builder',
            precio=80000,
            stock=2,
            formato_soporte='ATX',
            largo_max_gpu_mm=320,
        )

    def test_sanitizar_componentes(self):
        items = sanitizar_lista_componentes(
            [{'tipo': 'procesador', 'id': self.cpu.pk}, {'tipo': 'invalid', 'id': 1}]
        )
        self.assertEqual(len(items), 1)

    def test_analizar_armado_minimo(self):
        componentes = [
            {'tipo': 'procesador', 'id': self.cpu.pk},
            {'tipo': 'placa_madre', 'id': self.mb.pk},
        ]
        out = analizar_armado(componentes)
        self.assertTrue(out.get('ok'))
        self.assertGreater(out.get('total_clp', 0), 0)
        self.assertIn('estado', out)

    def test_chat_analizar_sin_piezas(self):
        data = ejecutar_analisis_armado_chat('analiza mi armado', None, None)
        self.assertEqual(data.get('response_type'), 'clarification')

    def test_proponer_gpu_mas_barata(self):
        base = [
            {'tipo': 'procesador', 'id': self.cpu.pk},
            {'tipo': 'placa_madre', 'id': self.mb.pk},
            {'tipo': 'tarjeta_grafica', 'id': self.gpu_cara.pk},
        ]
        prop = proponer_reemplazo(base, 'tarjeta_grafica', preferencia='cheaper')
        self.assertTrue(prop.get('ok'))
        self.assertIn('pending_action', prop)
        ids = [p['id'] for p in prop['componentes_propuestos'] if p['tipo'] == 'tarjeta_grafica']
        self.assertEqual(ids[0], self.gpu_barata.pk)

    def test_confirmar_requiere_pending(self):
        ctx = {'pending_action': {'id': 'abc', 'componentes': [], 'resumen': 'x'}}
        self.assertIsNone(intentar_confirmar_accion('hola', ctx))
        ctx['pending_action']['componentes'] = [
            {'tipo': 'procesador', 'id': self.cpu.pk},
            {'tipo': 'placa_madre', 'id': self.mb.pk},
        ]
        out = intentar_confirmar_accion('sí, confirmar', ctx)
        self.assertIsNotNone(out)
        self.assertEqual(out.get('response_type'), 'build_applied')
