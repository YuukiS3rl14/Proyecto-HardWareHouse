from decimal import Decimal

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.armado_servicio import revalidar_propuesta_armado
from core.chatbot.session_client import build_context_persistible
from core.models import PlacaMadre, Procesador, Proveedor


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class ChatSessionClientTests(TestCase):
    def test_build_context_sin_pedidos(self):
        ctx = build_context_persistible(
            {'presupuesto_clp': 500000, 'pedidos': [{'id': 1}], 'componentes': []}
        )
        self.assertIsNotNone(ctx)
        self.assertNotIn('pedidos', ctx)

    def test_revalidar_propuesta_vacia(self):
        out = revalidar_propuesta_armado()
        self.assertFalse(out.get('ok'))


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class ChatSessionApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='SessionBrand')
        cls.cpu = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Session',
            precio=Decimal('120000'),
            stock=2,
            socket='AM5',
            nucleos=6,
            frecuencia_base=3.5,
            potencia_referencia_watts=65,
        )
        cls.mb = PlacaMadre.objects.create(
            proveedor=marca,
            nombre='MB Session',
            precio=Decimal('100000'),
            stock=2,
            socket_cpu='AM5',
            formato='ATX',
            tipo_ram_soportado='DDR5',
            formato_ram_soportado='DIMM',
            ranuras_ram=2,
            capacidad_maxima_ram_gb=64,
        )

    def test_api_revalidar_propuesta(self):
        client = Client()
        propuesta = {
            'componentes': [
                {'tipo': 'procesador', 'id': self.cpu.pk},
                {'tipo': 'placa_madre', 'id': self.mb.pk},
            ]
        }
        response = client.post(
            reverse('core:armado_revalidar_api'),
            data={'proposal': propuesta},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        self.assertTrue(data.get('productos'))
        self.assertEqual(data['analisis']['estado'], 'incompleto')
