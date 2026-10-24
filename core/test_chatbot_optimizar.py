from decimal import Decimal

from django.test import TestCase, override_settings

from core.chatbot.conversation import generar_respuesta
from core.models import Procesador, TarjetaGrafica
from core.test_chatbot_armado import ArmadoFixtureMixin


def _componentes(fixture) -> list[dict]:
    return [
        {'tipo': 'procesador', 'id': fixture.cpu.pk, 'cantidad': 1},
        {'tipo': 'placa_madre', 'id': fixture.board.pk, 'cantidad': 1},
        {'tipo': 'memoria_ram', 'id': fixture.ram.pk, 'cantidad': 1},
        {'tipo': 'tarjeta_grafica', 'id': fixture.gpu.pk, 'cantidad': 1},
        {'tipo': 'almacenamiento_ssd', 'id': fixture.ssd.pk, 'cantidad': 1},
        {'tipo': 'gabinete', 'id': fixture.case.pk, 'cantidad': 1},
        {'tipo': 'refrigeracion', 'id': fixture.cooler.pk, 'cantidad': 1},
        {'tipo': 'fuente_de_poder', 'id': fixture.psu.pk, 'cantidad': 1},
    ]


@override_settings(OLLAMA_BASE_URL='', HARDWAREHOUSE_CHAT_INTENT_LLM=False)
class OptimizacionArmadoTests(ArmadoFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_armado_catalogo()
        cls.gpu_mejor = TarjetaGrafica.objects.create(
            proveedor=cls.marca,
            nombre='GPU Mejor 12GB',
            precio=Decimal('400000'),
            stock=2,
            vram_gb=12,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
            largo_mm=300,
            consumo_referencia_watts=180,
        )
        cls.gpu_cara = TarjetaGrafica.objects.create(
            proveedor=cls.marca,
            nombre='GPU Fuera de presupuesto',
            precio=Decimal('900000'),
            stock=2,
            vram_gb=16,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
            largo_mm=300,
            consumo_referencia_watts=180,
        )
        cls.gpu_economica = TarjetaGrafica.objects.create(
            proveedor=cls.marca,
            nombre='GPU Igual 8GB barata',
            precio=Decimal('190000'),
            stock=2,
            vram_gb=8,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
            largo_mm=280,
            consumo_referencia_watts=180,
        )
        cls.gpu_debil = TarjetaGrafica.objects.create(
            proveedor=cls.marca,
            nombre='GPU Debil 4GB',
            precio=Decimal('100000'),
            stock=2,
            vram_gb=4,
            tipo_memoria='GDDR6',
            interfaz='PCIe 4.0',
            largo_mm=200,
            consumo_referencia_watts=100,
        )
        cls.cpu_incompatible = Procesador.objects.create(
            proveedor=cls.marca,
            nombre='CPU LGA cara',
            precio=Decimal('220000'),
            stock=2,
            socket='LGA1700',
            nucleos=16,
            frecuencia_base=Decimal('5.0'),
            potencia_referencia_watts=125,
        )

    def _contexto(self):
        return {
            'ultimo_intent': 'pc_build',
            'presupuesto_clp': 1_000_000,
            'presupuesto_original_clp': 1_000_000,
            'proposito': 'gaming',
            'total_clp': 685_000,
            'componentes': _componentes(self),
        }

    def test_restante_mejora_dentro_del_presupuesto_original(self):
        data = generar_respuesta('Use the remaining 400k', build_context=self._contexto())
        self.assertEqual(data.get('response_type'), 'build_pending_change')
        comparacion = data['build_comparison']
        self.assertEqual(comparacion['antes']['presupuesto_clp'], 1_000_000)
        self.assertLessEqual(comparacion['despues']['total_clp'], 1_000_000)
        self.assertGreater(comparacion['costo_adicional_clp'], 0)
        self.assertLess(comparacion['costo_adicional_clp'], 400_000)
        elegido = comparacion['reemplazos'][0]['despues']['id']
        self.assertEqual(elegido, self.gpu_mejor.pk)
        self.assertNotEqual(elegido, self.gpu_cara.pk)
        guardado = data['armado_context']
        self.assertEqual(guardado['presupuesto_original_clp'], 1_000_000)
        self.assertEqual(guardado['presupuesto_clp'], 1_000_000)
        self.assertNotIn('applied_build', data)

    def test_seguimientos_cortos_usan_el_armado_anterior(self):
        for frase in ('the cheaper one', 'el más barato', 'reduce the price', 'baja el precio'):
            data = generar_respuesta(frase, build_context=self._contexto())
            self.assertEqual(data.get('response_type'), 'build_pending_change', frase)
            self.assertGreater(data['build_comparison']['ahorro_clp'], 0, frase)
            self.assertNotIn('No encontré productos', data['reply'])

        resto = generar_respuesta('use the rest', build_context=self._contexto())
        self.assertEqual(resto.get('response_type'), 'build_pending_change')
        self.assertLessEqual(resto['build_comparison']['despues']['total_clp'], 1_000_000)
        self.assertEqual(resto['armado_context']['presupuesto_original_clp'], 1_000_000)

        mejora = generar_respuesta('improve it', build_context=self._contexto())
        self.assertEqual(mejora.get('response_type'), 'build_pending_change')
        self.assertGreater(mejora['build_comparison']['costo_adicional_clp'], 0)

        referencia = generar_respuesta('ese pc', build_context=self._contexto())
        self.assertEqual(referencia.get('response_type'), 'clarification')
        self.assertIn('precio', referencia['reply'].lower())
        self.assertNotEqual(referencia.get('fallback'), 'missing_product')
        self.assertEqual(referencia['armado_context']['presupuesto_clp'], 1_000_000)

    def test_mas_barato_conserva_la_gpu_esencial(self):
        data = generar_respuesta('Make it cheaper', build_context=self._contexto())
        self.assertEqual(data.get('response_type'), 'build_pending_change')
        cambio = data['build_comparison']['reemplazos'][0]
        self.assertEqual(cambio['despues']['id'], self.gpu_economica.pk)
        self.assertNotEqual(cambio['despues']['id'], self.gpu_debil.pk)
        self.assertGreater(data['build_comparison']['ahorro_clp'], 0)
        self.assertLessEqual(data['build_comparison']['despues']['total_clp'], 1_000_000)

    def test_prioriza_gaming_y_mejora_de_gpu(self):
        gaming = generar_respuesta('Prioritize gaming', build_context=self._contexto())
        self.assertEqual(gaming['armado_context']['proposito'], 'gaming')
        self.assertEqual(gaming['build_comparison']['reemplazos'][0]['categoria'], 'tarjeta_grafica')
        gpu = generar_respuesta('Upgrade the graphics card', build_context=self._contexto())
        self.assertEqual(gpu['build_comparison']['reemplazos'][0]['despues']['id'], self.gpu_mejor.pk)
        self.assertIn('propuesta', gpu['reply'].lower())

    def test_que_podemos_mejorar_no_aplica_el_cambio(self):
        data = generar_respuesta('What can we improve?', build_context=self._contexto())
        self.assertEqual(data.get('response_type'), 'build_analysis')
        self.assertTrue(data['build_comparison']['razones'])
        self.assertNotIn('pending_action', data.get('armado_context') or {})

    def test_contexto_en_varios_turnos_y_confirmacion(self):
        primero = generar_respuesta('usa el restante de 400 lucas', build_context=self._contexto())
        ctx = primero['armado_context']
        self.assertEqual(ctx['presupuesto_original_clp'], 1_000_000)
        self.assertEqual(ctx['componentes'][3]['id'], self.gpu.pk)
        aplicado = generar_respuesta('sí, confirmar', build_context=ctx)
        self.assertEqual(aplicado.get('response_type'), 'build_applied')
        pares = {(item['tipo'], item['id']) for item in aplicado['armado_context']['componentes']}
        self.assertIn(('tarjeta_grafica', self.gpu_mejor.pk), pares)
        self.assertNotIn(('tarjeta_grafica', self.gpu.pk), pares)
        self.assertEqual(aplicado['armado_context']['presupuesto_original_clp'], 1_000_000)

    def test_stock_agotado_impide_confirmar(self):
        primero = generar_respuesta('Upgrade the graphics card', build_context=self._contexto())
        self.gpu_mejor.stock = 0
        self.gpu_mejor.save(update_fields=['stock'])
        aplicado = generar_respuesta('sí, confirmar', build_context=primero['armado_context'])
        self.assertEqual(aplicado.get('response_type'), 'build_rejected')
        self.assertIn('stock', aplicado['reply'].lower())
        self.assertEqual(aplicado.get('fallback'), 'unavailable_stock')
        self.assertNotIn('applied_build', aplicado)

    def test_no_propone_cpu_incompatible(self):
        data = generar_respuesta('Upgrade the CPU', build_context=self._contexto())
        self.assertEqual(data.get('response_type'), 'clarification')
        self.assertNotIn(str(self.cpu_incompatible.pk), str(data.get('build_comparison')))
        self.assertNotIn('CPU LGA cara', data['reply'])
