"""Integración chatbot: APIs, revalidación, pedidos, Ollama caído, propuestas."""
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.armado_servicio import revalidar_propuesta_armado
from core.chatbot.armado_builder_chat import intentar_confirmar_accion
from core.chatbot.conversation import generar_respuesta
from core.models import Pedido, PlacaMadre, Procesador, Proveedor

_SETTINGS = dict(
    OLLAMA_BASE_URL='',
    HARDWAREHOUSE_CHAT_INTENT_LLM=False,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
)


@override_settings(**_SETTINGS)
class CatalogIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='IntBrand')
        cls.barata = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Int Barata',
            precio=80000,
            stock=5,
            socket='AM4',
            nucleos=4,
            frecuencia_base=3.5,
        )
        cls.cara = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Int Cara',
            precio=350000,
            stock=2,
            socket='AM4',
            nucleos=8,
            frecuencia_base=4.2,
        )

    def test_cpu_mas_cara_orm(self):
        data = generar_respuesta('cpu mas cara')
        self.assertEqual(data.get('response_type'), 'product_results')
        self.assertIn('350.000', data['reply'])
        ui = data.get('ui') or {}
        self.assertEqual(ui.get('kind'), 'products')

    def test_chat_api_build_context_sanitizado(self):
        client = Client()
        response = client.post(
            reverse('core:chat_api'),
            data=json.dumps(
                {
                    'message': 'hola',
                    'build_context': {
                        'presupuesto_clp': 500000,
                        'pedidos': [{'id': 99, 'total': 1}],
                        'componentes': [{'tipo': 'invalid', 'id': 1}],
                    },
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)


@override_settings(**_SETTINGS)
class ProposalHomeToArmadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='PropBrand')
        cls.cpu = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Prop',
            precio=Decimal('200000'),
            stock=3,
            socket='AM5',
            nucleos=6,
            frecuencia_base=3.5,
            potencia_referencia_watts=65,
        )
        cls.mb = PlacaMadre.objects.create(
            proveedor=marca,
            nombre='MB Prop',
            precio=Decimal('150000'),
            stock=2,
            socket_cpu='AM5',
            formato='ATX',
            tipo_ram_soportado='DDR5',
            formato_ram_soportado='DIMM',
            ranuras_ram=2,
            capacidad_maxima_ram_gb=64,
        )

    def test_propuesta_home_revalida_como_en_armado(self):
        propuesta = {
            'version': 1,
            'componentes': [
                {'tipo': 'procesador', 'id': self.cpu.pk},
                {'tipo': 'placa_madre', 'id': self.mb.pk},
            ],
            'guardado_en': 'chat',
        }
        out = revalidar_propuesta_armado(propuesta=propuesta)
        self.assertTrue(out.get('ok'))
        self.assertTrue(out.get('proposal_pending'))
        client = Client()
        res = client.post(
            reverse('core:armado_revalidar_api'),
            data=json.dumps({'proposal': propuesta}),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get('componentes')[0]['id'], self.cpu.pk)

    def test_stock_cero_reflejado_en_productos_revalidados(self):
        self.cpu.stock = 0
        self.cpu.save(update_fields=['stock'])
        propuesta = {
            'componentes': [
                {'tipo': 'procesador', 'id': self.cpu.pk},
                {'tipo': 'placa_madre', 'id': self.mb.pk},
            ]
        }
        out = revalidar_propuesta_armado(propuesta=propuesta)
        self.assertFalse(out.get('ok'))
        self.assertIn('stock', (out.get('mensaje') or '').lower())


@override_settings(**_SETTINGS)
class OrdersAndConfirmIntegrationTests(TestCase):
    def test_pedidos_autenticados_incluyen_ui_sin_persistir_pedidos_en_context(self):
        user = User.objects.create_user('pedint', password='x')
        Pedido.objects.create(usuario=user, total_monto=120000, estado='pagado')
        client = Client()
        client.login(username='pedint', password='x')
        res = client.post(
            reverse('core:chat_api'),
            data=json.dumps({'message': 'estado de mi pedido'}),
            content_type='application/json',
        )
        data = res.json()
        self.assertEqual(data.get('response_type'), 'order_status')
        self.assertTrue(data.get('ui', {}).get('orders'))

    def test_confirmar_sin_pending_no_aplica(self):
        self.assertIsNone(intentar_confirmar_accion('sí, confirmar', None))

    def test_confirmar_duplicado_misma_sesion_ok(self):
        ctx = {
            'pending_action': {
                'id': 'abc',
                'componentes': [],
                'resumen': 'x',
            }
        }
        self.assertIsNone(intentar_confirmar_accion('sí, confirmar', ctx))


@override_settings(
    OLLAMA_BASE_URL='http://127.0.0.1:11434',
    HARDWAREHOUSE_CHAT_INTENT_LLM=True,
)
class OllamaUnavailableIntegrationTests(TestCase):
    @patch('core.chatbot.engine.extraer_intencion_ollama', return_value=None)
    def test_ollama_caido_usa_reglas_faq(self, _mock):
        data = generar_respuesta('hacen deliveries?')
        self.assertEqual(data.get('motor'), 'reglas')
        self.assertIn(data.get('intent'), ('despacho', 'store_faq'))


@override_settings(**_SETTINGS)
class InvalidApiIntegrationTests(TestCase):
    def test_revalidar_sin_cuerpo_valido(self):
        client = Client()
        res = client.post(
            reverse('core:armado_revalidar_api'),
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 400)

    def test_armado_estado_componentes_invalidos(self):
        client = Client()
        res = client.post(
            reverse('core:armado_estado_api'),
            data=json.dumps({'componentes': [{'tipo': 'nope', 'id': 1}]}),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 400)
