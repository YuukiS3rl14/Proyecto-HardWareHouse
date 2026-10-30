"""Búsquedas por categoría, sin exigir el nombre exacto del producto."""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from core.chatbot.conversation import generar_respuesta
from core.chatbot.llm.intent_schema import IntentoLLM
from core.models import MemoriaRam, Procesador, Proveedor, TarjetaGrafica


class _CatalogoCategoria:
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='CategoriaChat')
        Procesador.objects.create(
            proveedor=marca,
            nombre='Ryzen 3 3100',
            precio=Decimal('89990'),
            stock=5,
            socket='AM4',
            nucleos=4,
            frecuencia_base=Decimal('3.6'),
        )
        Procesador.objects.create(
            proveedor=marca,
            nombre='Pentium Gold',
            descripcion='',
            precio=Decimal('49990'),
            stock=2,
            socket='LGA1200',
            nucleos=2,
            frecuencia_base=Decimal('3.5'),
        )
        TarjetaGrafica.objects.create(
            proveedor=marca,
            nombre='RX 6600',
            precio=Decimal('199990'),
            stock=3,
            vram_gb=8,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
        )
        MemoriaRam.objects.create(
            proveedor=marca,
            nombre='Kit 16GB',
            precio=Decimal('45990'),
            stock=4,
            capacidad_gb=16,
            tipo_ddr='DDR4',
            velocidad_mhz=3200,
        )


@override_settings(
    OLLAMA_BASE_URL='',
    HARDWAREHOUSE_CHAT_INTENT_LLM=False,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
)
class BusquedaCategoriaReglasTests(_CatalogoCategoria, TestCase):

    def test_frases_de_categoria_no_exigen_el_nombre(self):
        frases = (
            ('muéstrame procesadores disponibles', 'CPU', 'Ryzen 3 3100'),
            ('busco tarjetas gráficas', 'Tarjeta Gráfica', 'RX 6600'),
            ('qué memoria RAM tienen', 'Memoria RAM', 'Kit 16GB'),
        )
        for frase, categoria, nombre in frases:
            with self.subTest(frase=frase):
                data = generar_respuesta(frase)
                self.assertEqual(data.get('response_type'), 'product_results')
                resultados = (data.get('catalogo') or {}).get('results') or []
                self.assertTrue(resultados)
                self.assertTrue(all(item['categoria'] == categoria for item in resultados))
                self.assertTrue(any(item['nombre'] == nombre for item in resultados))

    def test_el_nombre_exacto_sigue_encontrando_ese_producto(self):
        data = generar_respuesta('busco Ryzen 3 3100')
        self.assertEqual(data.get('response_type'), 'product_results')
        nombres = [item['nombre'] for item in data['catalogo']['results']]
        self.assertEqual(nombres, ['Ryzen 3 3100'])
        self.assertEqual(data['catalogo']['results'][0]['stock'], 5)
        self.assertEqual(data['catalogo']['results'][0]['precio_clp'], 89990)


@override_settings(
    OLLAMA_BASE_URL='https://ollama.example',
    OLLAMA_MODEL='modelo-demo',
    OLLAMA_API_KEY='no-se-usa',
    HARDWAREHOUSE_CHAT_INTENT_LLM=True,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
)
class BusquedaCategoriaOllamaTests(_CatalogoCategoria, TestCase):
    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_cpu_amplia_con_frase_generica_no_queda_vacia(self, mock_extraer):
        mock_extraer.return_value = IntentoLLM(
            intent='product_search',
            category='CPU',
            query_text='procesador disponible',
            filters={'solo_stock': True},
            confidence=0.95,
        )
        data = generar_respuesta('busco un procesador disponible')
        self.assertEqual(data.get('response_type'), 'product_results')
        self.assertEqual(data.get('motor'), 'ollama')
        resultados = data['catalogo']['results']
        self.assertTrue(all(item['categoria'] == 'CPU' for item in resultados))
        ryzen = next(item for item in resultados if item['nombre'] == 'Ryzen 3 3100')
        self.assertEqual(ryzen['stock'], 5)
        self.assertEqual(ryzen['precio_clp'], 89990)

    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_la_frase_completa_del_usuario_tampoco_anula_la_categoria(self, mock_extraer):
        mock_extraer.return_value = IntentoLLM(
            intent='product_search',
            category='CPU',
            query_text='busco un procesador disponible',
            confidence=0.95,
        )
        data = generar_respuesta('busco un procesador disponible')
        self.assertEqual(data.get('response_type'), 'product_results')
        self.assertTrue(any(item['nombre'] == 'Ryzen 3 3100' for item in data['catalogo']['results']))

    @patch('core.chatbot.engine.extraer_intencion_ollama')
    def test_el_nombre_exacto_que_envia_el_modelo_se_conserva(self, mock_extraer):
        mock_extraer.return_value = IntentoLLM(
            intent='product_search',
            category='CPU',
            query_text='Ryzen 3 3100',
            confidence=0.95,
        )
        data = generar_respuesta('busco Ryzen 3 3100')
        nombres = [item['nombre'] for item in data['catalogo']['results']]
        self.assertEqual(nombres, ['Ryzen 3 3100'])
        self.assertEqual(data['catalogo']['results'][0]['stock'], 5)
