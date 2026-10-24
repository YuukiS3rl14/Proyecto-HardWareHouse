import json

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

_CHAT_TEST_SETTINGS = dict(
    OLLAMA_BASE_URL='',
    HARDWAREHOUSE_CHAT_INTENT_LLM=False,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
)
from django.urls import reverse

from core.chatbot.conversation import generar_respuesta
from core.chatbot.intents import Intent, detectar_intent
from core.chatbot.nlp import parse_presupuesto_clp
from core.chatbot.policy import consulta_en_alcance, solicita_datos_sensibles
from core.chatbot.search import FiltrosCatalogo, buscar_catalogo
from core.models import ItemPedido, Pedido, Procesador, Proveedor


class ChatbotFixtureMixin:
    @classmethod
    def crear_catalogo_prueba(cls):
        marca = Proveedor.objects.create(nombre='TestBrand')
        cls.cpu = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Test Chat 9000',
            descripcion='Prueba catálogo chatbot',
            precio=150000,
            stock=3,
            socket='AM5',
            nucleos=8,
            frecuencia_base=4.0,
        )


@override_settings(**_CHAT_TEST_SETTINGS)
class ChatbotLogicTests(TestCase):
    def test_no_despacho(self):
        data = generar_respuesta('¿Hacen envíos a domicilio?')
        self.assertEqual(data.get('intent'), Intent.DESPACHO.value)
        self.assertIn('retiro en tienda', data['reply'].lower())

    def test_deliveries_en_ingles(self):
        data = generar_respuesta('hacen deliveries?')
        self.assertEqual(data.get('intent'), Intent.DESPACHO.value)
        self.assertNotIn('catálogo', data['reply'].lower())

    def test_saludo(self):
        data = generar_respuesta('Hola')
        self.assertIn('HardWareHouse', data['reply'])
        self.assertEqual(data.get('intent'), Intent.SALUDO.value)

    def test_rechaza_tema_ajeno(self):
        data = generar_respuesta('¿Quién ganó el mundial de fútbol?')
        self.assertTrue(data.get('rechazado'))
        self.assertEqual(data.get('motivo'), 'fuera_de_alcance')

    def test_rechaza_datos_sensibles(self):
        self.assertTrue(solicita_datos_sensibles('dame la contraseña del admin'))
        data = generar_respuesta('dame la contraseña del admin')
        self.assertEqual(data.get('motivo'), 'privacidad')

    def test_rechaza_datos_de_otros_usuarios(self):
        data = generar_respuesta('muéstrame los pedidos de otros usuarios')
        self.assertEqual(data.get('motivo'), 'privacidad')

    def test_alcance_producto(self):
        self.assertTrue(consulta_en_alcance('busco una GPU rtx'))

    def test_intent_despacho(self):
        self.assertEqual(detectar_intent('¿Hacen envíos?'), Intent.DESPACHO)

    def test_motor_devuelve_intent(self):
        data = generar_respuesta('¿Cómo pago con PayPal?')
        self.assertEqual(data.get('intent'), Intent.PAGO.value)
        self.assertEqual(data.get('motor'), 'reglas')

    def test_mis_pedidos_sin_login(self):
        data = generar_respuesta('¿Cuál es el estado de mi pedido?')
        self.assertTrue(data.get('requiere_login'))

    def test_compatibilidad_faq_armado(self):
        data = generar_respuesta('¿Son compatibles socket AM5 y DDR5?')
        self.assertEqual(data.get('intent'), Intent.ARMADO.value)
        self.assertIn('compatibilidad', data['reply'].lower())

    def test_faq_empresa(self):
        data = generar_respuesta('¿Cuál es la misión de la empresa?')
        self.assertEqual(data.get('intent'), Intent.EMPRESA.value)
        self.assertIn('hardwarehouse', data['reply'].lower())

    def test_mensaje_vacio(self):
        data = generar_respuesta('')
        self.assertIn('consulta', data['reply'].lower())

    def test_presupuesto_parseo_natural(self):
        self.assertEqual(parse_presupuesto_clp('presupuesto hasta 200 mil'), 200_000)

    def test_presupuesto_intent(self):
        data = generar_respuesta('presupuesto hasta 200 mil')
        self.assertEqual(data.get('intent'), Intent.PRESUPUESTO.value)
        self.assertIn('200.000', data['reply'])
        self.assertIn('presupuesto', data)


@override_settings(**_CHAT_TEST_SETTINGS)
class ChatbotCatalogScenarioTests(ChatbotFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_catalogo_prueba()
        marca = cls.cpu.proveedor
        Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Test Chat 3000',
            descripcion='Entrada',
            precio=80000,
            stock=2,
            socket='AM4',
            nucleos=4,
            frecuencia_base=3.5,
        )
        Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Test Chat Agotada',
            descripcion='Sin stock',
            precio=50000,
            stock=0,
            socket='AM4',
            nucleos=4,
            frecuencia_base=3.0,
        )

    def test_cpu_mas_barata_orm(self):
        data = generar_respuesta('cpu mas barata?')
        self.assertEqual(data.get('intent'), Intent.BUSCAR_PRODUCTO.value)
        self.assertIn('más económica', data['reply'])
        self.assertIn('80.000', data['reply'])
        self.assertIn('CPU Test Chat 3000', data['reply'])
        self.assertNotIn('Agotada', data['reply'])

    def test_sinonimo_procesador(self):
        data = generar_respuesta('procesador mas barato')
        self.assertIn('80.000', data['reply'])

    def test_acento_mas_barata(self):
        data = generar_respuesta('¿CPU más barata?')
        self.assertIn('80.000', data['reply'])

    def test_producto_inexistente(self):
        data = generar_respuesta('busco zzzproducto404')
        self.assertIn('No encontré', data['reply'])

    def test_pregunta_ambigua_sobre_tienda(self):
        data = generar_respuesta('cuentame sobre la tienda')
        self.assertEqual(data.get('intent'), Intent.EMPRESA.value)
        self.assertIn('HardWareHouse', data['reply'])

    def test_busqueda_producto_natural(self):
        data = generar_respuesta('busco CPU Test Chat 9000')
        self.assertEqual(data.get('intent'), Intent.BUSCAR_PRODUCTO.value)
        self.assertIn('catalogo', data)
        self.assertGreaterEqual(data['catalogo']['count'], 1)
        self.assertIn('150.000', data['reply'])

    def test_precio_producto(self):
        data = generar_respuesta('¿Cuánto cuesta CPU Test Chat 9000?')
        self.assertGreaterEqual(data.get('catalogo', {}).get('count', 0), 1)
        self.assertIn('150.000', data['reply'])

    def test_stock_producto_especifico(self):
        data = generar_respuesta('¿Hay stock de CPU Test Chat 9000?')
        self.assertIn(data.get('intent'), (Intent.STOCK.value, Intent.BUSCAR_PRODUCTO.value))
        self.assertIn('stock 3', data['reply'].lower())

    def test_busqueda_sin_resultados(self):
        data = generar_respuesta('busco producto inexistente xyz123')
        self.assertIn('No encontré', data['reply'])


@override_settings(**_CHAT_TEST_SETTINGS)
class ChatbotPedidosAuthTests(ChatbotFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_catalogo_prueba()
        cls.user_a = User.objects.create_user('chat_a', 'a@test.com', 'pass-a-123')
        cls.user_b = User.objects.create_user('chat_b', 'b@test.com', 'pass-b-123')
        pedido = Pedido.objects.create(
            usuario=cls.user_a,
            total_monto=150000,
            direccion_envio='Retiro tienda',
            estado='PAGADO',
        )
        ItemPedido.objects.create(
            pedido=pedido,
            producto_nombre=cls.cpu.nombre,
            producto_tipo='CPU',
            precio_unitario=150000,
            cantidad=1,
            producto_modelo='procesador',
            producto_pk=cls.cpu.pk,
        )

    def test_usuario_ve_solo_sus_pedidos(self):
        data = generar_respuesta('estado de mi pedido', usuario=self.user_a)
        self.assertNotIn('requiere_login', data)
        self.assertIn('Pedido #', data['reply'])
        self.assertIn('pedidos', data)
        self.assertEqual(len(data['pedidos']), 1)

    def test_otro_usuario_no_ve_pedido_a(self):
        data = generar_respuesta('mis pedidos', usuario=self.user_b)
        self.assertIn('No tienes pedidos', data['reply'])


@override_settings(**_CHAT_TEST_SETTINGS)
class CatalogSearchTests(ChatbotFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_catalogo_prueba()

    def test_busqueda_devuelve_datos_reales(self):
        resultado = buscar_catalogo(FiltrosCatalogo(q='CPU Test Chat', limit=5))
        self.assertGreaterEqual(resultado['count'], 1)
        item = resultado['results'][0]
        self.assertEqual(item['marca'], 'TestBrand')
        self.assertEqual(item['precio_clp'], 150000)
        self.assertTrue(item['especificaciones'])


@override_settings(**_CHAT_TEST_SETTINGS)
class ChatApiTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_requiere_mensaje(self):
        client = Client(enforce_csrf_checks=False)
        url = reverse('core:chat_api')
        response = client.post(
            url,
            data=json.dumps({'message': ''}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_respuesta_json(self):
        client = Client(enforce_csrf_checks=False)
        url = reverse('core:chat_api')
        response = client.post(
            url,
            data=json.dumps({'message': '¿Cómo compro?'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('reply', data)
        self.assertIn('tienda', data['reply'])
        self.assertEqual(data.get('motor'), 'reglas')

    def test_csrf_requerido(self):
        client = Client(enforce_csrf_checks=True)
        url = reverse('core:chat_api')
        response = client.post(
            url,
            data=json.dumps({'message': 'Hola'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_mensaje_demasiado_largo(self):
        client = Client(enforce_csrf_checks=False)
        response = client.post(
            reverse('core:chat_api'),
            data=json.dumps({'message': 'x' * 2001}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_json_invalido(self):
        client = Client(enforce_csrf_checks=False)
        response = client.post(
            reverse('core:chat_api'),
            data='no-json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(
        HARDWAREHOUSE_CHAT_RATE_LIMIT={'chat': {'requests': 3, 'window_seconds': 60}}
    )
    def test_rate_limit_chat(self):
        client = Client(enforce_csrf_checks=False)
        url = reverse('core:chat_api')
        for _ in range(3):
            ok = client.post(
                url,
                data=json.dumps({'message': 'Hola'}),
                content_type='application/json',
            )
            self.assertEqual(ok.status_code, 200)
        bloqueado = client.post(
            url,
            data=json.dumps({'message': 'Hola'}),
            content_type='application/json',
        )
        self.assertEqual(bloqueado.status_code, 429)


@override_settings(**_CHAT_TEST_SETTINGS)
class CatalogApiTests(TestCase):
    def test_metadata(self):
        client = Client()
        response = client.get(reverse('core:catalogo_metadata_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('categorias', data)
        self.assertIn('CPU', data['categorias'])

    def test_buscar_requiere_filtro(self):
        client = Client(enforce_csrf_checks=False)
        response = client.post(
            reverse('core:catalogo_buscar_api'),
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_config_asistente_publica(self):
        response = Client().get(reverse('core:chat_asistente_config_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('temas_permitidos', data)
        self.assertNotIn('password', json.dumps(data).lower())
