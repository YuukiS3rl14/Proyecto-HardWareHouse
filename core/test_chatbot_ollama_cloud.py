"""Ollama local y remoto, sin red real."""
import json
from unittest.mock import patch

from django.test import TestCase, override_settings

from core.chatbot.conversation import generar_respuesta
from core.chatbot.llm.intent_extractor import extraer_intencion_ollama
from core.chatbot.llm.ollama import OllamaClient, olvidar_salud_ollama
from core.chatbot.llm.response_composer import response_llm_activo
from core.chatbot.response_finalize import finalizar_respuesta
from core.chatbot.response_types import ORDER_LOGIN, ORDER_STATUS, OLLAMA_POLISH_TIPOS
from core.chatbot.security import historial_para_llm

CLAVE = 'oclave-nube-NO-LOG-77'
NUBE = {
    'OLLAMA_BASE_URL': 'https://ollama.example',
    'OLLAMA_API_KEY': CLAVE,
    'OLLAMA_MODEL': 'modelo-remoto-demo',
    'OLLAMA_TIMEOUT': 10,
    'HARDWAREHOUSE_CHAT_INTENT_LLM': True,
    'HARDWAREHOUSE_CHAT_RESPONSE_LLM': False,
}


class _Respuesta:
    def __init__(self, status, payload=None, roto=False):
        self.status_code = status
        self._payload = payload if payload is not None else {}
        self._roto = roto

    def json(self):
        if self._roto:
            raise ValueError('no es json')
        return self._payload


def _contenido(texto, status=200):
    return _Respuesta(status, {'message': {'content': texto}})


@override_settings(
    OLLAMA_BASE_URL='http://127.0.0.1:11434',
    OLLAMA_API_KEY=CLAVE,
    OLLAMA_MODEL='qwen3:4b-instruct',
    OLLAMA_TIMEOUT=10,
    HARDWAREHOUSE_CHAT_INTENT_LLM=True,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
)
class OllamaLocalAuthTests(TestCase):
    def setUp(self):
        olvidar_salud_ollama()

    @patch('core.chatbot.llm.ollama.requests.post')
    @patch('core.chatbot.llm.ollama.requests.get')
    def test_local_no_envia_la_clave_y_consulta_tags_una_vez(self, mock_get, mock_post):
        mock_get.return_value = _Respuesta(200, {'models': []})
        mock_post.return_value = _contenido('{"intent":"greeting","confidence":0.9}')
        primero = OllamaClient()
        segundo = OllamaClient()
        self.assertTrue(primero.chat_json([{'role': 'user', 'content': 'hola'}]).startswith('{'))
        segundo.disponible()
        self.assertEqual(mock_get.call_count, 1)
        headers = mock_post.call_args.kwargs['headers']
        self.assertEqual(headers, {})
        self.assertNotIn('Authorization', headers)
        self.assertEqual(mock_post.call_args.kwargs['timeout'], 10)
        self.assertEqual(mock_post.call_args.kwargs['json']['model'], 'qwen3:4b-instruct')


@override_settings(**NUBE)
class OllamaRemotoTests(TestCase):
    def setUp(self):
        olvidar_salud_ollama()

    @patch('core.chatbot.llm.ollama.requests.post')
    @patch('core.chatbot.llm.ollama.requests.get')
    def test_https_usa_bearer_sin_tags(self, mock_get, mock_post):
        mock_post.return_value = _contenido('{"intent":"greeting","confidence":0.95}')
        with self.assertLogs('hardwarehouse.chat', level='INFO') as captured:
            texto = OllamaClient().chat_json([{'role': 'user', 'content': 'hola'}])
        self.assertIn('greeting', texto)
        mock_get.assert_not_called()
        self.assertEqual(
            mock_post.call_args.kwargs['headers']['Authorization'],
            f'Bearer {CLAVE}',
        )
        self.assertEqual(mock_post.call_args.kwargs['json']['model'], 'modelo-remoto-demo')
        self.assertEqual(mock_post.call_args.kwargs['timeout'], 10)
        self.assertFalse(mock_post.call_args.kwargs['allow_redirects'])
        unido = '\n'.join(captured.output)
        self.assertNotIn(CLAVE, unido)
        self.assertNotIn('Bearer', unido)

    @patch('core.chatbot.llm.ollama.requests.post')
    @patch('core.chatbot.llm.ollama.requests.get')
    def test_http_remoto_no_manda_la_clave(self, mock_get, mock_post):
        mock_post.return_value = _contenido('ok')
        with override_settings(OLLAMA_BASE_URL='http://inferencia.ejemplo:11434'):
            OllamaClient().chat_texto([{'role': 'user', 'content': 'hola'}])
        mock_get.assert_not_called()
        self.assertEqual(mock_post.call_args.kwargs['headers'], {})

    @patch('core.chatbot.llm.ollama.requests.post')
    @patch('core.chatbot.llm.ollama.requests.get')
    def test_sin_modelo_remoto_no_llama(self, mock_get, mock_post):
        with override_settings(OLLAMA_MODEL=''):
            self.assertIsNone(OllamaClient().chat_json([{'role': 'user', 'content': 'hola'}]))
        mock_get.assert_not_called()
        mock_post.assert_not_called()


@override_settings(**NUBE)
class OllamaFalloTests(TestCase):
    def setUp(self):
        olvidar_salud_ollama()

    def _post(self, mock_post, efecto):
        mock_post.side_effect = None
        mock_post.return_value = None
        if isinstance(efecto, Exception):
            mock_post.side_effect = efecto
        else:
            mock_post.return_value = efecto

    @patch('core.chatbot.llm.ollama.requests.get')
    @patch('core.chatbot.llm.ollama.requests.post')
    def test_401_429_5xx_timeout_y_red_caen_en_reglas(self, mock_post, mock_get):
        import requests

        casos = [
            _Respuesta(401),
            _Respuesta(429),
            _Respuesta(503),
            requests.Timeout('t'),
            requests.ConnectionError('red'),
            _Respuesta(200, roto=True),
        ]
        for efecto in casos:
            with self.subTest(efecto=type(efecto).__name__ if isinstance(efecto, Exception) else efecto.status_code):
                self._post(mock_post, efecto)
                with self.assertLogs('hardwarehouse.chat', level='INFO') as captured:
                    data = generar_respuesta('Hola')
                self.assertEqual(data.get('motor'), 'reglas')
                self.assertNotIn(CLAVE, '\n'.join(captured.output))
        mock_get.assert_not_called()

    @patch('core.chatbot.llm.ollama.requests.get')
    @patch('core.chatbot.llm.ollama.requests.post')
    def test_clasificacion_malformada_o_poco_confiable_usa_reglas(self, mock_post, mock_get):
        mock_post.return_value = _contenido('no-es-json')
        data = generar_respuesta('Hola, buenas')
        self.assertEqual(data.get('motor'), 'reglas')

        mock_post.return_value = _contenido(
            json.dumps({'intent': 'product_search', 'confidence': 0.1, 'filters': {}})
        )
        self.assertIsNone(extraer_intencion_ollama('cpu barata'))
        data = generar_respuesta('Hola, buenas')
        self.assertEqual(data.get('motor'), 'reglas')
        mock_get.assert_not_called()


class ContextoExternoTests(TestCase):
    def test_el_historial_no_lleva_pedidos_ni_datos_personales(self):
        limpio = historial_para_llm(
            [
                {
                    'role': 'assistant',
                    'content': (
                        'Pedido #17 — Pagado — ana@ejemplo.cl — +56 9 1234 5678 — 12.345.678-5'
                    ),
                },
                {'role': 'user', 'content': 'mi correo es ana@ejemplo.cl'},
                {'role': 'user', 'content': 'busco una gpu'},
            ]
        )
        texto = json.dumps(limpio, ensure_ascii=False)
        self.assertNotIn('ana@ejemplo.cl', texto)
        self.assertNotIn('Pedido #17', texto)
        self.assertNotIn('12.345.678-5', texto)
        self.assertNotIn('1234 5678', texto)
        self.assertIn('busco una gpu', texto)

    @override_settings(**NUBE)
    @patch('core.chatbot.llm.ollama.requests.post')
    @patch('core.chatbot.llm.ollama.requests.get')
    def test_la_clasificacion_no_reenvia_el_correo(self, mock_get, mock_post):
        mock_post.return_value = _contenido('{"intent":"greeting","confidence":0.2}')
        extraer_intencion_ollama(
            'mi correo es ana@ejemplo.cl',
            historial=[{'role': 'assistant', 'content': 'Pedido #9 — Pagado — total $10.000'}],
        )
        if mock_post.called:
            enviado = json.dumps(mock_post.call_args.kwargs['json'], ensure_ascii=False)
            self.assertNotIn('ana@ejemplo.cl', enviado)
            self.assertNotIn('Pedido #9', enviado)
            self.assertNotIn(CLAVE, enviado)
        mock_get.assert_not_called()

    @override_settings(**{**NUBE, 'HARDWAREHOUSE_CHAT_RESPONSE_LLM': True})
    def test_pedidos_y_armado_no_se_reescriben(self):
        self.assertNotIn(ORDER_STATUS, OLLAMA_POLISH_TIPOS)
        self.assertNotIn(ORDER_LOGIN, OLLAMA_POLISH_TIPOS)
        with patch('core.chatbot.response_finalize.componer_con_ollama') as mock_compose:
            pedido = finalizar_respuesta(
                {'reply': 'Pedido #4 — Pagado', 'intent': 'orders', 'motor': 'reglas'},
                'mis pedidos',
            )
            armado = finalizar_respuesta(
                {
                    'reply': 'Total 700.000 CLP, stock disponible',
                    'intent': 'pc_build',
                    'response_type': 'pc_build',
                    'armado': {'ok': True},
                    'motor': 'reglas',
                },
                'armame un pc',
            )
        mock_compose.assert_not_called()
        self.assertIn('Pedido #4', pedido['reply'])
        self.assertIn('700.000', armado['reply'])

    @override_settings(**NUBE)
    def test_la_redaccion_queda_apagada_en_la_prueba_inicial(self):
        self.assertFalse(response_llm_activo())
