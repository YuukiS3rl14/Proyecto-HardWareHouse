import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from core.chatbot.conversation import generar_respuesta
from core.chatbot.llm.intent_schema import validar_intento_llm
from core.chatbot.llm.router import ejecutar_ruta_llm
from core.models import Procesador, Proveedor


@override_settings(
    OLLAMA_BASE_URL='http://127.0.0.1:11434',
    HARDWAREHOUSE_CHAT_INTENT_LLM=True,
)
class OllamaIntentRoutingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='TestBrand')
        Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Ollama Cheap',
            precio=70000,
            stock=4,
            socket='AM4',
            nucleos=4,
            frecuencia_base=3.5,
        )

    def test_validar_json_intent(self):
        data = validar_intento_llm(
            {
                'intent': 'product_search',
                'category': 'CPU',
                'brand': None,
                'budget_clp': None,
                'price_sort': 'precio_asc',
                'filters': {'solo_stock': True},
                'confidence': 0.9,
            }
        )
        self.assertIsNotNone(data)
        self.assertEqual(data.intent, 'product_search')
        self.assertEqual(data.price_sort, 'precio_asc')

    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_store_faq_delivery_via_ollama(self, mock_extraer):
        from core.chatbot.llm.intent_schema import IntentoLLM

        mock_extraer.return_value = IntentoLLM(
            intent='store_faq',
            faq_topic='despacho',
            confidence=0.88,
        )
        data = generar_respuesta('hacen deliveries po?')
        self.assertIn(data.get('motor'), ('reglas', 'ollama', 'conocimiento'))
        self.assertIn(data.get('intent'), ('despacho', 'store_faq'))
        self.assertIn('retir', data['reply'].lower())
        mock_extraer.assert_not_called()

    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_product_search_cheapest_cpu(self, mock_extraer):
        from core.chatbot.llm.intent_schema import IntentoLLM

        mock_extraer.return_value = IntentoLLM(
            intent='product_search',
            category='CPU',
            price_sort='precio_asc',
            filters={'solo_stock': True},
            confidence=0.92,
        )
        data = generar_respuesta('cpu mas barata')
        self.assertEqual(data.get('motor'), 'ollama')
        self.assertIn('70.000', data['reply'])

    @patch('core.chatbot.engine.extraer_intencion_ollama', return_value=None)
    def test_fallback_reglas_si_ollama_falla(self, _mock):
        data = generar_respuesta('Hola, buenas')
        self.assertEqual(data.get('motor'), 'reglas')
        self.assertTrue(data.get('fallback') == 'reglas' or data.get('intent'))

    def test_off_topic_llm(self):
        extraido = validar_intento_llm(
            {'intent': 'off_topic', 'confidence': 0.95, 'filters': {}}
        )
        out = ejecutar_ruta_llm(extraido, 'receta de empanadas')
        self.assertTrue(out.get('rechazado'))

    def test_pc_build_modify_intent_valido(self):
        data = validar_intento_llm(
            {'intent': 'pc_build_modify', 'confidence': 0.85, 'filters': {}}
        )
        self.assertIsNotNone(data)
        self.assertEqual(data.intent, 'pc_build_modify')


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class OllamaDisabledTests(TestCase):
    def test_sin_ollama_sigue_reglas(self):
        data = generar_respuesta('Hola')
        self.assertEqual(data.get('motor'), 'reglas')

    def test_debug_log_no_incluye_el_mensaje(self):
        secreto = 'CLAVE-SECRETA-NO-LOG-8841'
        with self.assertLogs('hardwarehouse.chat', level='INFO') as captured:
            generar_respuesta(f'hola {secreto}')
        joined = '\n'.join(captured.output)
        self.assertNotIn(secreto, joined)
        self.assertIn('route=reglas', joined)
        self.assertIn('ollama=skipped', joined)
        self.assertIn('reason=rules_only', joined)
