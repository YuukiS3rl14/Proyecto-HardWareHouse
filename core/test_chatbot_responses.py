from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from core.chatbot.conversation import generar_respuesta
from core.chatbot.response_finalize import finalizar_respuesta, inferir_tipo_respuesta
from core.chatbot.response_templates import plantilla_producto_no_encontrado
from core.chatbot.response_types import (
    CLARIFICATION,
    FAQ,
    GREETING,
    OFF_TOPIC,
    ORDER_LOGIN,
    PRODUCT_NOT_FOUND,
    PRODUCT_RESULTS,
)
from core.models import Procesador, Proveedor


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class ResponseTypeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='RespBrand')
        cls.cpu = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Response Test',
            precio=99000,
            stock=2,
            socket='AM5',
            nucleos=6,
            frecuencia_base=3.8,
        )

    def test_producto_no_encontrado_solo_plantilla(self):
        data = generar_respuesta('busco xyz-inexistente-404')
        self.assertEqual(data.get('response_type'), PRODUCT_NOT_FOUND)
        self.assertEqual(data['reply'], plantilla_producto_no_encontrado())
        self.assertNotIn('PayPal', data['reply'])

    def test_producto_con_orm(self):
        data = generar_respuesta('CPU Response Test')
        self.assertEqual(data.get('response_type'), PRODUCT_RESULTS)
        self.assertIn('99.000', data['reply'])
        self.assertIn('CPU Response Test', data['reply'])

    def test_faq_despacho_verificado(self):
        data = generar_respuesta('hacen deliveries?')
        self.assertEqual(data.get('response_type'), FAQ)
        self.assertIn('retiro', data['reply'].lower())
        self.assertIn('no', data['reply'].lower())

    def test_fuera_de_tema(self):
        data = generar_respuesta('¿Quién ganó el mundial de fútbol?')
        self.assertEqual(data.get('response_type'), OFF_TOPIC)
        self.assertIn('HardWareHouse', data['reply'])
        self.assertIn('/contacto/', data['reply'])

    def test_pedido_sin_login(self):
        data = generar_respuesta('estado de mi pedido')
        self.assertEqual(data.get('response_type'), ORDER_LOGIN)
        self.assertIn('iniciar sesión', data['reply'].lower())

    def test_inferir_clarification(self):
        tipo = inferir_tipo_respuesta({'intent': 'clarification'})
        self.assertEqual(tipo, CLARIFICATION)


@override_settings(
    OLLAMA_BASE_URL='http://127.0.0.1:11434',
    HARDWAREHOUSE_CHAT_INTENT_LLM=True,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=True,
)
class ResponseOllamaClarificationTests(TestCase):
    @patch('core.chatbot.engine.extraer_intencion_ollama')
    @patch('core.chatbot.response_finalize.componer_con_ollama')
    def test_clarificacion_con_interpretacion(self, mock_compose, mock_intent):
        from core.chatbot.llm.intent_schema import IntentoLLM

        mock_intent.return_value = IntentoLLM(
            intent='clarification',
            category='CPU',
            confidence=0.8,
        )
        mock_compose.return_value = (
            '¿Buscas una CPU en particular? Puedo mostrarte opciones del catálogo con stock real.'
        )
        data = generar_respuesta('algo de cpu')
        self.assertEqual(data.get('response_type'), CLARIFICATION)
        self.assertIn('CPU', data['reply'])

    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_faq_sin_inventar_productos(self, mock_intent):
        from core.chatbot.llm.intent_schema import IntentoLLM

        mock_intent.return_value = IntentoLLM(
            intent='store_faq',
            faq_topic='despacho',
            confidence=0.9,
        )
        with patch('core.chatbot.response_finalize.componer_con_ollama', return_value=None):
            data = generar_respuesta('envían a mi casa?')
        self.assertEqual(data.get('response_type'), FAQ)
        self.assertNotIn('RTX', data['reply'])


class FinalizeUnitTests(TestCase):
    def test_finalize_product_not_found(self):
        out = finalizar_respuesta(
            {
                'catalogo': {'count': 0, 'results': []},
                'intent': 'product_search',
                'busqueda_catalogo': True,
            },
            'busco foo',
        )
        self.assertEqual(out['response_type'], PRODUCT_NOT_FOUND)

    def test_finalize_busqueda_sin_catalogo_no_es_not_found(self):
        tipo = inferir_tipo_respuesta({'intent': 'product_search'})
        self.assertEqual(tipo, CLARIFICATION)

    def test_finalize_pc_build_sin_presupuesto_es_clarificacion(self):
        tipo = inferir_tipo_respuesta(
            {
                'intent': 'pc_build',
                'response_type': 'clarification',
                'reply': 'indica presupuesto',
            }
        )
        self.assertEqual(tipo, CLARIFICATION)


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class IntentRoutingRegressionTests(TestCase):
    def test_saludo_no_product_not_found(self):
        data = generar_respuesta('Hola')
        self.assertEqual(data.get('response_type'), GREETING)
        self.assertNotEqual(data.get('response_type'), PRODUCT_NOT_FOUND)

    def test_mensaje_vago_no_product_not_found(self):
        data = generar_respuesta('busco algo')
        self.assertEqual(data.get('response_type'), CLARIFICATION)
        self.assertNotIn('No encontré productos', data.get('reply', ''))


@override_settings(
    OLLAMA_BASE_URL='http://127.0.0.1:11434',
    HARDWAREHOUSE_CHAT_INTENT_LLM=True,
)
class IntentRoutingOllamaMockTests(TestCase):
    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_ollama_delivery_no_product_not_found(self, mock_extraer):
        from core.chatbot.llm.intent_schema import IntentoLLM

        mock_extraer.return_value = IntentoLLM(
            intent='store_faq',
            faq_topic='despacho',
            confidence=0.9,
        )
        data = generar_respuesta('envío a domicilio?')
        self.assertEqual(data.get('response_type'), FAQ)
        self.assertNotEqual(data.get('response_type'), PRODUCT_NOT_FOUND)

    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_ollama_off_topic_response_type(self, mock_extraer):
        from core.chatbot.llm.intent_schema import IntentoLLM

        mock_extraer.return_value = IntentoLLM(
            intent='off_topic',
            confidence=0.95,
        )
        data = generar_respuesta('receta de empanadas')
        self.assertEqual(data.get('response_type'), OFF_TOPIC)

    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_ollama_vague_product_clarification(self, mock_extraer):
        from core.chatbot.llm.intent_schema import IntentoLLM

        mock_extraer.return_value = IntentoLLM(
            intent='product_search',
            confidence=0.7,
        )
        data = generar_respuesta('algo')
        self.assertEqual(data.get('response_type'), CLARIFICATION)
