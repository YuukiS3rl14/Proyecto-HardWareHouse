import logging
from unittest.mock import patch

from django.test import TestCase, override_settings

from core.chatbot.conversation import generar_respuesta
from core.chatbot.llm.intent_schema import validar_intento_llm
from core.chatbot.nlp import normalizar_presupuesto_clp
from core.chatbot.nlp_armado import parsear_solicitud_armado
from core.chatbot.response_types import CLARIFICATION, OFF_TOPIC, PRODUCT_NOT_FOUND, PRODUCT_RESULTS
from core.models import Procesador, Proveedor


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class PresupuestoChilenoTests(TestCase):
    def test_un_millon_y_sinonimos(self):
        for frase in ('un millón', '1m', '1 palo', '1000 lucas', '1 millon'):
            self.assertEqual(normalizar_presupuesto_clp(frase), 1_000_000, frase)

    def test_setecientos_mil_y_sinonimos(self):
        for frase in ('700 mil', '700k', '700 lucas', '700 luca'):
            self.assertEqual(normalizar_presupuesto_clp(frase), 700_000, frase)

    def test_armado_hereda_palo(self):
        sol = parsear_solicitud_armado('armame un PC gamer por 1 palo')
        self.assertEqual(sol.presupuesto_clp, 1_000_000)
        self.assertEqual(sol.proposito, 'gaming')


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class IntentFallbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='IntentBrand')
        Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Intent 9000',
            precio=120000,
            stock=2,
            socket='AM5',
            nucleos=6,
            frecuencia_base=4,
        )

    def test_mensaje_desconocido_no_busca_productos(self):
        data = generar_respuesta('asdfqwer mensaje suelto')
        self.assertEqual(data.get('response_type'), CLARIFICATION)
        self.assertNotEqual(data.get('response_type'), PRODUCT_NOT_FOUND)
        self.assertIn('No entendí bien', data['reply'])
        self.assertEqual(data.get('fallback'), 'unknown_intent')
        self.assertEqual(data.get('fallback_reason'), 'unknown_intent')
        self.assertNotIn('catalogo', data)

    def test_busqueda_real_sigue_en_orm(self):
        data = generar_respuesta('busco CPU Intent 9000')
        self.assertEqual(data.get('response_type'), PRODUCT_RESULTS)
        self.assertIn('120.000', data['reply'])
        self.assertEqual(data.get('intent_clasificado'), 'product_search')

    def test_busqueda_vacia_solo_si_era_busqueda(self):
        data = generar_respuesta('busco zzzproducto404')
        self.assertEqual(data.get('response_type'), PRODUCT_NOT_FOUND)

    def test_off_topic_se_mantiene(self):
        data = generar_respuesta('¿Quién ganó el mundial de fútbol?')
        self.assertEqual(data.get('response_type'), OFF_TOPIC)

    def test_contexto_de_intent_y_presupuesto(self):
        ctx = {
            'ultimo_intent': 'pc_build',
            'presupuesto_clp': 1_000_000,
            'proposito': 'gaming',
        }
        data = generar_respuesta('no se que decirte ahora', build_context=ctx)
        self.assertEqual(data.get('response_type'), CLARIFICATION)
        self.assertIn('armado', data['reply'].lower())
        guardado = data.get('armado_context') or {}
        self.assertEqual(guardado.get('ultimo_intent'), 'pc_build')
        self.assertEqual(guardado.get('presupuesto_clp'), 1_000_000)

    def test_log_no_incluye_el_mensaje(self):
        secreto = 'clave-secreta-intent-9988'
        with self.assertLogs('hardwarehouse.chat', level=logging.INFO) as logs:
            generar_respuesta(f'asdfqwer {secreto}')
        self.assertNotIn(secreto, '\n'.join(logs.output))
        self.assertTrue(any('classified=' in linea for linea in logs.output))


@override_settings(
    OLLAMA_BASE_URL='http://127.0.0.1:11434',
    HARDWAREHOUSE_CHAT_INTENT_LLM=True,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
)
class OllamaIntentSchemaTests(TestCase):
    def test_intents_nuevos_en_json(self):
        for intent in (
            'pc_build',
            'build_upgrade',
            'build_downgrade',
            'budget_adjustment',
            'product_search',
            'faq',
            'orders',
            'clarification',
            'off_topic',
        ):
            data = validar_intento_llm({'intent': intent, 'confidence': 0.8, 'budget_clp': 700000})
            self.assertIsNotNone(data, intent)
            self.assertEqual(data.intent, intent)

    def test_intent_desconocido_se_rechaza(self):
        self.assertIsNone(validar_intento_llm({'intent': 'inventar_productos', 'confidence': 0.9}))

    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_ollama_vago_no_cae_en_busqueda(self, mock_extraer):
        from core.chatbot.llm.intent_schema import IntentoLLM

        mock_extraer.return_value = IntentoLLM(intent='product_search', confidence=0.4)
        data = generar_respuesta('quiero eso nomas')
        self.assertNotEqual(data.get('response_type'), PRODUCT_NOT_FOUND)

    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_budget_adjustment_no_inventa_catalogo(self, mock_extraer):
        from core.chatbot.llm.intent_schema import IntentoLLM

        mock_extraer.return_value = IntentoLLM(
            intent='budget_adjustment',
            budget_clp=1,
            confidence=0.9,
            filters={'purpose': 'gaming'},
        )
        data = generar_respuesta(
            'bajalo a 700 lucas',
            build_context={'ultimo_intent': 'pc_build', 'presupuesto_clp': 1_000_000, 'proposito': 'gaming'},
        )
        self.assertNotEqual(data.get('response_type'), PRODUCT_NOT_FOUND)
        self.assertIn(data.get('intent_clasificado'), ('budget_adjustment', 'pc_build', 'clarification'))
        self.assertEqual((data.get('armado_context') or {}).get('presupuesto_clp'), 700_000)
