from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.chatbot.conversation import generar_respuesta
from core.knowledge.service import (
    ConocimientoInvalido,
    buscar_conocimiento,
    cargar_conocimiento,
    perfil_publico,
    texto_faq,
    validar_conocimiento,
)

_SETTINGS = dict(
    OLLAMA_BASE_URL='',
    HARDWAREHOUSE_CHAT_INTENT_LLM=False,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
)


@override_settings(**_SETTINGS)
class KnowledgeSourceTests(TestCase):
    def test_json_valido_y_anos(self):
        datos = cargar_conocimiento()
        self.assertEqual(datos['identity']['years_in_business'], 5)
        self.assertTrue(datos['contact']['address']['placeholder'])

    def test_sobre_nosotros_usa_la_misma_mision(self):
        perfil = perfil_publico()
        response = Client().get(reverse('core:sobrenosotros'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, perfil['mission'][:40])
        self.assertContains(response, 'cinco años')

    def test_faq_despacho_sin_inventar_envio(self):
        texto = texto_faq('despacho') or ''
        self.assertIn('no ofrece despacho', texto.lower())
        self.assertIn('/sobre-nosotros/', texto)

    def test_chat_mision_vision_valores_servicios(self):
        mision = generar_respuesta('¿Cuál es la misión de la empresa?')
        self.assertEqual(mision.get('intent'), 'empresa')
        self.assertIn('componentes de calidad', mision['reply'].lower())
        self.assertNotEqual(mision.get('response_type'), 'product_not_found')

        vision = generar_respuesta('y la visión', historial=[{'role': 'user', 'content': 'misión'}])
        self.assertIn('top 3', vision['reply'].lower())

        valores = generar_respuesta('cuales son sus valores')
        self.assertIn('respetuoso', valores['reply'].lower())

        servicios = generar_respuesta('qué servicios ofrecen')
        self.assertIn('armado', servicios['reply'].lower())

    def test_chat_delivery_y_contacto_ejemplo(self):
        envio = generar_respuesta('hacen deliveries po?')
        self.assertEqual(envio.get('intent'), 'despacho')
        self.assertIn('retiro', envio['reply'].lower())
        self.assertNotEqual(envio.get('response_type'), 'product_not_found')

        contacto = generar_respuesta('cuál es el teléfono de la tienda')
        self.assertIn('ejemplo', contacto['reply'].lower())
        self.assertIn('/contacto/', contacto['reply'])

    def test_historia(self):
        data = generar_respuesta('cuántos años llevan en el mercado')
        self.assertIn('cinco años', data['reply'].lower())
        self.assertEqual(buscar_conocimiento('historia de la empresa')['id'], 'identidad')

    def test_validacion_rechaza_json_incompleto(self):
        with self.assertRaises(ConocimientoInvalido):
            validar_conocimiento({'identity': {'name': 'X', 'years_in_business': 1}})
