"""Consultas reales que el chat respondía como catálogo vacío."""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from core.chatbot.conversation import generar_respuesta
from core.chatbot.llm.intent_schema import IntentoLLM
from core.models import PlacaMadre, Procesador, Proveedor, TarjetaGrafica

FRASE_CPU = 'Busco un prosesador para jugar que este disponible'
FRASE_GPU = 'Muéstrame tarjetas gráficas disponibles por menos de $200.000'
FRASE_SOCKET = '¿Es compatible el AMD Ryzen 3 3100 con la ASRock B550I Lightning WiFi?'
FRASE_INCOMPATIBLE = '¿Puedo instalar el procesador Proce 2000 en la ASRock B550I Lightning WiFi?'
FRASE_RAM = '¿Qué tipo de memoria RAM puedo instalar en la ASRock B550I Lightning WiFi?'
_SIN_RESULTADOS = 'No encontré productos en el catálogo con esos criterios.'


@override_settings(
    OLLAMA_BASE_URL='',
    HARDWAREHOUSE_CHAT_INTENT_LLM=False,
    HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
)
class ConsultasCatalogoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='Consultas NL')
        Procesador.objects.create(
            proveedor=marca,
            nombre='AMD Ryzen 3 3100',
            precio=Decimal('89990'),
            stock=5,
            socket='AM4',
            nucleos=4,
            frecuencia_base=Decimal('3.6'),
        )
        Procesador.objects.create(
            proveedor=marca,
            nombre='Pentium Agotado',
            precio=Decimal('49990'),
            stock=0,
            socket='LGA1200',
            nucleos=2,
            frecuencia_base=Decimal('3.5'),
        )
        Procesador.objects.create(
            proveedor=marca,
            nombre='Proce 2000',
            precio=Decimal('2000'),
            stock=4,
            socket='LGA1200',
            nucleos=2,
            frecuencia_base=Decimal('3.0'),
        )
        TarjetaGrafica.objects.create(
            proveedor=marca,
            nombre='GALAX GeForce GTX 1650',
            precio=Decimal('149990'),
            stock=4,
            vram_gb=4,
            tipo_memoria='GDDR6',
            interfaz='PCIe 3.0',
        )
        TarjetaGrafica.objects.create(
            proveedor=marca,
            nombre='GPU por encima del presupuesto',
            precio=Decimal('249990'),
            stock=2,
            vram_gb=8,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
        )
        PlacaMadre.objects.create(
            proveedor=marca,
            nombre='ASRock B550I Lightning WiFi',
            precio=Decimal('129990'),
            stock=3,
            socket_cpu='AM4',
            chipset='B550',
            formato='Mini-ITX',
            ranuras_ram=2,
            tipo_ram_soportado='DDR4',
            formato_ram_soportado='DIMM',
        )

    def _por_reglas_y_llm(self, frase):
        respuestas = [generar_respuesta(frase)]
        with override_settings(
            OLLAMA_BASE_URL='https://ollama.example',
            OLLAMA_MODEL='demo',
            HARDWAREHOUSE_CHAT_INTENT_LLM=True,
            HARDWAREHOUSE_CHAT_RESPONSE_LLM=False,
        ):
            with patch('core.chatbot.engine.extraer_intencion_ollama') as mock:
                mock.return_value = IntentoLLM(
                    intent='product_search',
                    query_text=frase,
                    confidence=0.92,
                )
                respuestas.append(generar_respuesta(frase))
        return respuestas

    def test_el_typo_de_procesador_lista_cpus_con_stock(self):
        for data in self._por_reglas_y_llm(FRASE_CPU):
            self.assertEqual(data.get('response_type'), 'product_results')
            self.assertNotIn(_SIN_RESULTADOS, data['reply'])
            resultados = data['catalogo']['results']
            self.assertTrue(resultados)
            nombres = {item['nombre'] for item in resultados}
            self.assertIn('AMD Ryzen 3 3100', nombres)
            self.assertNotIn('Pentium Agotado', nombres)
            self.assertNotIn('GALAX GeForce GTX 1650', nombres)
            self.assertTrue(all(item['categoria'] == 'CPU' for item in resultados))
            self.assertTrue(all(item['stock'] > 0 for item in resultados))

    def test_las_graficas_respetan_precio_y_stock(self):
        for data in self._por_reglas_y_llm(FRASE_GPU):
            self.assertEqual(data.get('response_type'), 'product_results')
            self.assertNotIn(_SIN_RESULTADOS, data['reply'])
            resultados = data['catalogo']['results']
            self.assertEqual([item['nombre'] for item in resultados], ['GALAX GeForce GTX 1650'])
            self.assertEqual(resultados[0]['precio_clp'], 149990)
            self.assertEqual(resultados[0]['stock'], 4)
            self.assertEqual(resultados[0]['categoria'], 'Tarjeta Gráfica')
            self.assertLessEqual(resultados[0]['precio_clp'], 200000)

    def test_ryzen_y_b550_son_compatibles(self):
        for data in self._por_reglas_y_llm(FRASE_SOCKET):
            self.assertEqual(data.get('response_type'), 'compatibility')
            self.assertEqual(data['compatibilidad']['estado'], 'compatible')
            self.assertNotIn(_SIN_RESULTADOS, data['reply'])
            self.assertIn('AMD Ryzen 3 3100', data['reply'])
            self.assertIn('ASRock B550I Lightning WiFi', data['reply'])
            self.assertIn('AM4', data['reply'])

    def test_proce_2000_no_entra_en_la_b550(self):
        for data in self._por_reglas_y_llm(FRASE_INCOMPATIBLE):
            self.assertEqual(data.get('response_type'), 'compatibility')
            self.assertEqual(data['compatibilidad']['estado'], 'incompatible')
            self.assertNotIn(_SIN_RESULTADOS, data['reply'])
            self.assertIn('Proce 2000', data['reply'])
            self.assertIn('LGA1200', data['reply'])
            self.assertIn('AM4', data['reply'])

    def test_la_b550_admite_ddr4_dimm(self):
        for data in self._por_reglas_y_llm(FRASE_RAM):
            self.assertEqual(data.get('response_type'), 'compatibility')
            self.assertEqual(data['compatibilidad']['estado'], 'dato_catalogo')
            self.assertNotIn(_SIN_RESULTADOS, data['reply'])
            self.assertIn('ASRock B550I Lightning WiFi', data['reply'])
            self.assertIn('DDR4', data['reply'])
            self.assertIn('DIMM', data['reply'])
