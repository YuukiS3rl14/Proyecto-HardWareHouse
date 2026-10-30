from django.test import TestCase, override_settings

from core.chatbot.conversation import generar_respuesta
from core.chatbot.response_ui import construir_ui_payload
from core.chatbot.response_types import PRODUCT_RESULTS
from core.models import Procesador, Proveedor


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class ChatUiPayloadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='UiBrand')
        cls.cpu = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Ui Test',
            precio=99000,
            stock=2,
            socket='AM5',
            nucleos=6,
            frecuencia_base=3.8,
        )

    def test_generar_respuesta_incluye_ui_productos(self):
        data = generar_respuesta('CPU Ui Test')
        self.assertEqual(data.get('response_type'), PRODUCT_RESULTS)
        ui = data.get('ui') or {}
        self.assertEqual(ui.get('kind'), 'products')
        self.assertTrue(any(p.get('nombre') == 'CPU Ui Test' for p in ui.get('products', [])))

    def test_construir_ui_catalogo(self):
        ui = construir_ui_payload(
            {
                'catalogo': {
                    'count': 1,
                    'results': [
                        {
                            'nombre_completo': 'X',
                            'precio_clp': 1000,
                            'stock': 1,
                            'url_detalle': '/detalle/procesador/1/',
                        }
                    ],
                }
            },
            PRODUCT_RESULTS,
        )
        self.assertEqual(len(ui.get('products', [])), 1)
