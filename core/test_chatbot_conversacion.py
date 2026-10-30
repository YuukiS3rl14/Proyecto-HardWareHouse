from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from core.chatbot.conversation import generar_respuesta
from core.chatbot.response_types import CLARIFICATION, OFF_TOPIC, PRODUCT_NOT_FOUND, PRODUCT_RESULTS
from core.models import PlacaMadre, Procesador, Proveedor
from core.test_chatbot_armado import ArmadoFixtureMixin


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class FallbackConversacionTests(TestCase):
    def test_intent_desconocido_pide_aclaracion(self):
        data = generar_respuesta('asdfqwer mensaje suelto')
        self.assertEqual(data.get('response_type'), CLARIFICATION)
        self.assertEqual(data.get('fallback'), 'unknown_intent')
        self.assertIn('No entendí bien', data['reply'])
        self.assertNotIn('No encontré productos', data['reply'])

    def test_producto_inexistente_solo_en_busqueda(self):
        data = generar_respuesta('busco zzzproducto404')
        self.assertEqual(data.get('response_type'), PRODUCT_NOT_FOUND)
        self.assertEqual(data.get('fallback'), 'missing_product')
        self.assertIn('No encontré productos', data['reply'])

    def test_mensaje_ambiguo_no_dice_que_no_hay_productos(self):
        data = generar_respuesta('busco algo')
        self.assertEqual(data.get('response_type'), CLARIFICATION)
        self.assertNotEqual(data.get('fallback'), 'missing_product')
        self.assertNotIn('No encontré productos', data['reply'])

    def test_off_topic_tiene_fallback_propio(self):
        data = generar_respuesta('¿Quién ganó el mundial de fútbol?')
        self.assertEqual(data.get('response_type'), OFF_TOPIC)
        self.assertEqual(data.get('fallback'), 'off_topic')
        self.assertNotIn('No encontré productos', data['reply'])

    def test_presupuesto_invalido(self):
        data = generar_respuesta('armame un pc gamer por 50 lucas')
        self.assertEqual(data.get('response_type'), 'pc_build_failed')
        self.assertEqual(data.get('fallback'), 'invalid_budget')
        self.assertNotIn('No encontré productos', data['reply'])
        self.assertFalse((data.get('armado') or {}).get('ok'))

    def test_seguimiento_sin_armado(self):
        for frase in ('ese pc', 'that pc', 'use the rest', 'reduce the price', 'improve it'):
            data = generar_respuesta(frase)
            self.assertEqual(data.get('fallback'), 'missing_pc_build', frase)
            self.assertNotIn('No encontré productos', data['reply'])

    def test_el_mas_barato_tras_una_busqueda_pide_categoria(self):
        marca = Proveedor.objects.create(nombre='ConvBrand')
        Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Conversacion 1',
            precio=80000,
            stock=2,
            socket='AM5',
            nucleos=4,
            frecuencia_base=3,
        )
        primero = generar_respuesta('busco CPU Conversacion 1')
        self.assertEqual(primero.get('response_type'), PRODUCT_RESULTS)
        segundo = generar_respuesta('the cheaper one', build_context=primero.get('armado_context'))
        self.assertEqual(segundo.get('response_type'), CLARIFICATION)
        self.assertIn('categoría', segundo['reply'].lower())
        self.assertNotEqual(segundo.get('fallback'), 'missing_product')


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class ConversacionArmadoTests(ArmadoFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_armado_catalogo()
        cls.placa_lga = PlacaMadre.objects.create(
            proveedor=cls.marca,
            nombre='Placa LGA chat',
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
        cls.cpu_agotada = Procesador.objects.create(
            proveedor=cls.marca,
            nombre='AgotadaZZ99',
            precio=Decimal('100000'),
            stock=0,
            socket='AM5',
            nucleos=4,
            frecuencia_base=Decimal('3.5'),
        )

    def test_stock_agotado_no_es_producto_inexistente(self):
        data = generar_respuesta('busco AgotadaZZ99')
        self.assertEqual(data.get('response_type'), PRODUCT_RESULTS)
        self.assertEqual(data.get('fallback'), 'unavailable_stock')
        self.assertIn('AgotadaZZ99', data['reply'])
        self.assertIn('stock', data['reply'].lower())
        self.assertNotIn('No encontré productos', data['reply'])

    def test_componentes_incompatibles(self):
        data = generar_respuesta(
            'sí, confirmar',
            build_context={
                'pending_action': {
                    'id': 'propuesta-incompatible',
                    'tipo': 'optimizar_armado',
                    'resumen': 'Cambio de placa',
                    'componentes': [
                        {'tipo': 'procesador', 'id': self.cpu.pk, 'cantidad': 1},
                        {'tipo': 'placa_madre', 'id': self.placa_lga.pk, 'cantidad': 1},
                    ],
                }
            },
        )
        self.assertEqual(data.get('response_type'), 'build_rejected')
        self.assertEqual(data.get('fallback'), 'incompatible_components')
        self.assertNotIn('applied_build', data)
        self.assertNotIn('No encontré productos', data['reply'])

    def test_turno_siguiente_recuerda_el_pc(self):
        primero = generar_respuesta('armame un PC gamer por 700 lucas')
        self.assertEqual(primero.get('response_type'), 'pc_build')
        self.assertLessEqual(primero['armado']['total_clp'], 700_000)
        self.assertEqual(primero['armado_context']['presupuesto_clp'], 700_000)

        segundo = generar_respuesta('ese pc', build_context=primero['armado_context'])
        self.assertEqual(segundo.get('response_type'), CLARIFICATION)
        self.assertIn('precio', segundo['reply'].lower())
        self.assertEqual(segundo['armado_context']['presupuesto_clp'], 700_000)
        self.assertNotIn('No encontré productos', segundo['reply'])

        tercero = generar_respuesta(
            'armame ese pc por 1 palo',
            build_context=segundo['armado_context'],
        )
        self.assertIn(tercero.get('response_type'), ('pc_build', 'pc_build_failed', 'clarification'))
        self.assertEqual((tercero.get('armado_context') or {}).get('presupuesto_clp'), 1_000_000)


@override_settings(
    OLLAMA_BASE_URL='http://127.0.0.1:11434',
    HARDWAREHOUSE_CHAT_INTENT_LLM=True,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=True,
)
class RedaccionOllamaTests(ArmadoFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_armado_catalogo()

    @patch('core.chatbot.engine.extraer_intencion_ollama', return_value=None)
    @patch('core.chatbot.response_finalize.componer_con_ollama')
    def test_ollama_explica_con_hechos_de_django(self, mock_compose, _mock_intent):
        mock_compose.return_value = 'Te dejo el armado con las piezas que ya revisé en el catálogo.'
        data = generar_respuesta('armame un PC gamer por 700 lucas')
        self.assertEqual(data.get('response_type'), 'pc_build')
        self.assertIn('catálogo', data['reply'])
        hechos = mock_compose.call_args.kwargs['hechos_verificados']
        self.assertIn('CLP', hechos)
        self.assertLessEqual(data['armado']['total_clp'], 700_000)

    @patch('core.chatbot.engine.extraer_intencion_ollama', return_value=None)
    @patch('core.chatbot.response_finalize.componer_con_ollama', return_value=None)
    def test_si_ollama_no_redacta_quedan_los_precios(self, _mock_compose, _mock_intent):
        data = generar_respuesta('armame un PC gamer por 700 lucas')
        self.assertEqual(data.get('response_type'), 'pc_build')
        self.assertIn('CLP', data['reply'])
        self.assertIn('stock', data['reply'].lower())
