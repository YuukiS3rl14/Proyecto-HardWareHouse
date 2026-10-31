"""Lista filtrada, seguimiento de esa lista y aislamiento entre conversaciones."""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from core.chatbot.conversation import generar_respuesta
from core.chatbot.llm.intent_schema import IntentoLLM
from core.chatbot.policy import solicita_datos_sensibles
from core.chatbot.security import validar_build_context
from core.models import Procesador, Proveedor, TarjetaGrafica

FRASE_LISTA = 'Muéstrame tarjetas gráficas por menos de $200.000'
FRASE_BARATA = '¿Cuál de esas es la más barata?'


@override_settings(
    OLLAMA_BASE_URL='',
    HARDWAREHOUSE_CHAT_INTENT_LLM=False,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
)
class ContextoCatalogoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='Contexto Chat')
        cls.barata = TarjetaGrafica.objects.create(
            proveedor=marca,
            nombre='GPU Barata',
            precio=Decimal('100000'),
            stock=4,
            vram_gb=4,
            tipo_memoria='GDDR6',
            interfaz='PCIe 3.0',
        )
        TarjetaGrafica.objects.create(
            proveedor=marca,
            nombre='GPU Media',
            precio=Decimal('150000'),
            stock=3,
            vram_gb=6,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
        )
        TarjetaGrafica.objects.create(
            proveedor=marca,
            nombre='GPU Alta',
            precio=Decimal('180000'),
            stock=2,
            vram_gb=8,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
        )
        TarjetaGrafica.objects.create(
            proveedor=marca,
            nombre='GPU Fuera',
            precio=Decimal('250000'),
            stock=2,
            vram_gb=8,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
        )
        cls.cpu = Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Barata',
            precio=Decimal('40000'),
            stock=5,
            socket='AM4',
            nucleos=4,
            frecuencia_base=Decimal('3.5'),
        )
        Procesador.objects.create(
            proveedor=marca,
            nombre='CPU Cara',
            precio=Decimal('90000'),
            stock=2,
            socket='AM4',
            nucleos=6,
            frecuencia_base=Decimal('4.0'),
        )

    def test_la_lista_filtrada_recuerda_la_mas_barata(self):
        lista = generar_respuesta(FRASE_LISTA)
        self.assertEqual(lista.get('response_type'), 'product_results')
        nombres = [item['nombre'] for item in lista['catalogo']['results']]
        self.assertCountEqual(nombres, ['GPU Barata', 'GPU Media', 'GPU Alta'])
        self.assertNotIn('GPU Fuera', nombres)
        self.assertTrue(all(item['precio_clp'] <= 200000 for item in lista['catalogo']['results']))
        self.assertGreater(len(nombres), 1)

        contexto = validar_build_context({'build_context': lista['armado_context']})
        barata = generar_respuesta(FRASE_BARATA, build_context=contexto)
        self.assertEqual(barata.get('response_type'), 'product_results')
        self.assertEqual(
            [item['nombre'] for item in barata['catalogo']['results']],
            ['GPU Barata'],
        )
        self.assertEqual(barata['catalogo']['results'][0]['precio_clp'], 100000)
        self.assertEqual(barata['catalogo']['results'][0]['producto_pk'], self.barata.pk)

        with override_settings(
            OLLAMA_BASE_URL='https://ollama.example',
            OLLAMA_MODEL='demo',
            HARDWAREHOUSE_CHAT_INTENT_LLM=True,
            HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
        ):
            with patch('core.chatbot.engine.extraer_intencion_ollama') as mock:
                mock.return_value = IntentoLLM(
                    intent='product_search',
                    category='Tarjeta Gráfica',
                    price_sort='precio_asc',
                    query_text=FRASE_LISTA,
                    confidence=0.93,
                )
                por_modelo = generar_respuesta(FRASE_LISTA)
        self.assertEqual(por_modelo.get('response_type'), 'product_results')
        self.assertCountEqual(
            [item['nombre'] for item in por_modelo['catalogo']['results']],
            ['GPU Barata', 'GPU Media', 'GPU Alta'],
        )

    def test_tarjeta_grafica_y_gpu_no_son_datos_bancarios(self):
        self.assertFalse(solicita_datos_sensibles('tarjeta grafica'))
        self.assertFalse(solicita_datos_sensibles('tarjeta gráfica'))
        self.assertFalse(solicita_datos_sensibles('gpu'))
        self.assertTrue(solicita_datos_sensibles('pásame el número de tarjeta'))
        self.assertTrue(solicita_datos_sensibles('dame la contraseña del admin'))
        self.assertTrue(solicita_datos_sensibles('el cvv de la cuenta bancaria'))

        for frase in ('tarjeta grafica', 'gpu'):
            data = generar_respuesta(frase)
            self.assertNotEqual(data.get('motivo'), 'privacidad', frase)
            self.assertEqual(data.get('response_type'), 'product_results', frase)
            self.assertTrue(data['catalogo']['results'])
            self.assertTrue(
                all(item['categoria'] == 'Tarjeta Gráfica' for item in data['catalogo']['results']),
                frase,
            )

    def test_el_contexto_no_cruza_conversaciones(self):
        lista_gpu = generar_respuesta(FRASE_LISTA)
        contexto_gpu = validar_build_context({'build_context': lista_gpu['armado_context']})

        ajena = generar_respuesta(FRASE_BARATA, build_context=None)
        self.assertEqual(ajena.get('response_type'), 'clarification')
        self.assertNotIn('GPU Barata', ajena['reply'])

        lista_cpu = generar_respuesta('muéstrame procesadores')
        contexto_cpu = validar_build_context({'build_context': lista_cpu['armado_context']})
        barata_cpu = generar_respuesta(FRASE_BARATA, build_context=contexto_cpu)
        self.assertEqual(
            [item['nombre'] for item in barata_cpu['catalogo']['results']],
            ['CPU Barata'],
        )
        self.assertEqual(barata_cpu['catalogo']['results'][0]['producto_pk'], self.cpu.pk)
        self.assertNotIn('GPU Barata', barata_cpu['reply'])

        otra_vez = generar_respuesta(FRASE_BARATA, build_context=contexto_gpu)
        self.assertEqual(otra_vez['catalogo']['results'][0]['nombre'], 'GPU Barata')
        self.assertEqual(otra_vez['catalogo']['results'][0]['producto_pk'], self.barata.pk)
