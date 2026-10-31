import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from core.compatibilidad import (
    POLITICA_POTENCIA_DEFECTO,
    PoliticaPotencia,
    evaluar_candidato,
    validar_armado,
)
from core.models import (
    FuenteDePoder,
    Gabinete,
    ItemCarrito,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    Proveedor,
    TarjetaGrafica,
)


def pieza(**atributos):
    return type('Pieza', (), atributos)()


POLITICA_EXACTA = PoliticaPotencia(reserva_otros_watts=50, margen=Decimal('1.10'))


def cpu_gpu_fuente(fuente_w, cpu_w=100, gpu_w=100, minimo_gpu=None):
    return dict(
        procesador=pieza(socket='AM5', potencia_referencia_watts=cpu_w),
        placa_madre=pieza(
            socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX',
            ranuras_ram=4, formato_ram_soportado='DIMM', capacidad_maxima_ram_gb=128,
        ),
        memoria_ram=pieza(
            tipo_ddr='DDR5', capacidad_gb=16, modulos_por_producto=1,
            capacidad_modulo_gb=16, formato_ram='DIMM',
        ),
        gabinete=pieza(formato_soporte='ATX', largo_max_gpu_mm=400),
        tarjeta_grafica=pieza(
            consumo_referencia_watts=gpu_w,
            potencia_minima_fuente_watts=minimo_gpu,
            largo_mm=300,
        ),
        fuente_de_poder=pieza(potencia_watts=fuente_w),
    )


class PoliticaPotenciaTests(SimpleTestCase):
    def test_la_formula_redondea_hacia_arriba(self):
        politica = PoliticaPotencia(reserva_otros_watts=10, margen=Decimal('1.25'))

        estimacion, minimo = politica.estimar(100, 200, None)

        # (100 + 200 + 10) * 1.25 = 387.5 -> 388
        self.assertEqual(estimacion, 388)
        self.assertEqual(minimo, 388)

    def test_la_gama_basica_de_450w_alcanza_el_minimo_estimado(self):
        # 65 + 110 + 150 = 325; techo(325 × 1.20) = 390; la GPU pide 450 W.
        estimacion, minimo = POLITICA_POTENCIA_DEFECTO.estimar(65, 110, 450)

        self.assertEqual(estimacion, 390)
        self.assertEqual(minimo, 450)
        for watts in (450, 650, 850):
            resultado = validar_armado(**cpu_gpu_fuente(watts, cpu_w=65, gpu_w=110, minimo_gpu=450))
            self.assertEqual(resultado.estado, 'compatible', watts)

    def test_una_configuracion_sobre_450w_rechaza_esa_fuente(self):
        # 95 + 170 + 150 = 415; techo(415 × 1.20) = 498; la GPU pide 550 W.
        estimacion, minimo = POLITICA_POTENCIA_DEFECTO.estimar(95, 170, 550)
        cpu = pieza(socket='AM5', potencia_referencia_watts=95)
        gpu = pieza(consumo_referencia_watts=170, potencia_minima_fuente_watts=550, largo_mm=270)
        corta = pieza(potencia_watts=450)
        suficiente = pieza(potencia_watts=650)

        self.assertEqual(estimacion, 498)
        self.assertEqual(minimo, 550)
        for fuente, esperado in ((corta, 'incompatible'), (suficiente, 'compatible')):
            armado = validar_armado(**cpu_gpu_fuente(
                fuente.potencia_watts, cpu_w=95, gpu_w=170, minimo_gpu=550,
            ))
            candidato = evaluar_candidato(
                'fuente_de_poder', fuente, procesador=cpu, tarjeta_grafica=gpu,
            )
            self.assertEqual(armado.estado, esperado, fuente.potencia_watts)
            self.assertEqual(candidato.estado, armado.estado, fuente.potencia_watts)

        motivos = ' '.join(evaluar_candidato(
            'fuente_de_poder', corta, procesador=cpu, tarjeta_grafica=gpu,
        ).motivos)
        self.assertIn('450 W', motivos)
        self.assertIn('550 W', motivos)
        self.assertIn('498 W', motivos)

    def test_la_recomendacion_de_la_gpu_eleva_el_minimo(self):
        estimacion, minimo = POLITICA_EXACTA.estimar(100, 100, 400)

        self.assertEqual(estimacion, 275)
        self.assertEqual(minimo, 400)

    def test_el_watt_justo_alcanza_y_uno_menos_no(self):
        justo = validar_armado(**cpu_gpu_fuente(275), politica=POLITICA_EXACTA)
        corto = validar_armado(**cpu_gpu_fuente(274), politica=POLITICA_EXACTA)

        self.assertEqual(justo.estado, 'compatible')
        self.assertFalse(justo.bloquea_agregar)
        self.assertEqual(corto.estado, 'incompatible')
        self.assertTrue(corto.bloquea_agregar)
        texto = ' '.join(corto.motivos_de_rechazo)
        self.assertIn('Potencia insuficiente según la política', texto)
        self.assertIn('274 W', texto)
        self.assertIn('275 W', texto)

    def test_valores_desconocidos_o_cero_no_cuentan_como_consumo(self):
        for cpu_w, gpu_w, fuente_w in ((None, 100, 500), (100, None, 500), (100, 100, None), (0, 100, 500), (100, 0, 500)):
            resultado = validar_armado(
                **cpu_gpu_fuente(fuente_w, cpu_w=cpu_w, gpu_w=gpu_w),
                politica=POLITICA_EXACTA,
            )
            self.assertEqual(resultado.estado, 'datos_insuficientes', (cpu_w, gpu_w, fuente_w))
            self.assertTrue(resultado.bloquea_agregar)
            self.assertIn('no se toma como consumo conocido', ' '.join(resultado.motivos_de_rechazo))

    def test_sin_cpu_o_gpu_la_seleccion_queda_incompleta(self):
        sin_gpu = validar_armado(
            procesador=pieza(socket='AM5', potencia_referencia_watts=100),
            fuente_de_poder=pieza(potencia_watts=750),
            politica=POLITICA_EXACTA,
        )
        sin_cpu = validar_armado(
            tarjeta_grafica=pieza(consumo_referencia_watts=100),
            fuente_de_poder=pieza(potencia_watts=750),
            politica=POLITICA_EXACTA,
        )

        self.assertEqual(sin_gpu.estado, 'incompleto')
        self.assertEqual(sin_cpu.estado, 'incompleto')
        self.assertFalse(sin_gpu.bloquea_agregar)
        self.assertFalse(sin_cpu.bloquea_agregar)

    def test_sin_fuente_no_aplica_la_regla_al_resto_del_armado(self):
        resultado = validar_armado(
            procesador=pieza(socket='AM5', potencia_referencia_watts=100),
            placa_madre=pieza(
                socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX',
                ranuras_ram=4, formato_ram_soportado='DIMM', capacidad_maxima_ram_gb=128,
            ),
            memoria_ram=pieza(
                tipo_ddr='DDR5', capacidad_gb=16, modulos_por_producto=1,
                capacidad_modulo_gb=16, formato_ram='DIMM',
            ),
            gabinete=pieza(formato_soporte='ATX', largo_max_gpu_mm=400),
            tarjeta_grafica=pieza(consumo_referencia_watts=200, largo_mm=300),
            politica=POLITICA_EXACTA,
        )

        self.assertEqual(resultado.estado, 'compatible')
        self.assertFalse(any(hallazgo.regla == 'potencia' for hallazgo in resultado.hallazgos))

    @override_settings(POLITICA_POTENCIA_ARMADO={'reserva_otros_watts': 0, 'margen': '1'})
    def test_el_ajuste_cambia_el_minimo_sin_pasar_la_politica(self):
        resultado = validar_armado(**cpu_gpu_fuente(200))

        self.assertEqual(resultado.estado, 'compatible')
        self.assertNotEqual(
            validar_armado(**cpu_gpu_fuente(200), politica=POLITICA_POTENCIA_DEFECTO).estado,
            'compatible',
        )


class RecomendacionPotenciaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proveedor = Proveedor.objects.create(nombre='Marca Potencia')
        cls.cpu = Procesador.objects.create(
            proveedor=cls.proveedor, nombre='CPU con referencia', precio=Decimal('100000'), stock=4,
            socket='AM5', nucleos=8, frecuencia_base=Decimal('4.00'), potencia_referencia_watts=100,
        )
        cls.cpu_sin_dato = Procesador.objects.create(
            proveedor=cls.proveedor, nombre='CPU sin referencia', precio=Decimal('90000'), stock=4,
            socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
        )
        cls.gpu = TarjetaGrafica.objects.create(
            proveedor=cls.proveedor, nombre='GPU con consumo', precio=Decimal('200000'), stock=4,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
            consumo_referencia_watts=100, potencia_minima_fuente_watts=400,
        )
        cls.gpu_sin_dato = TarjetaGrafica.objects.create(
            proveedor=cls.proveedor, nombre='GPU sin consumo', precio=Decimal('150000'), stock=4,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
        )
        cls.fuente_corta = FuenteDePoder.objects.create(
            proveedor=cls.proveedor, nombre='Fuente corta', precio=Decimal('30000'), stock=4,
            potencia_watts=399, certificacion='80+ Bronze', modular=False,
        )
        cls.fuente_justa = FuenteDePoder.objects.create(
            proveedor=cls.proveedor, nombre='Fuente justa', precio=Decimal('40000'), stock=4,
            potencia_watts=400, certificacion='80+ Bronze', modular=False,
        )
        cls.fuente_holgada = FuenteDePoder.objects.create(
            proveedor=cls.proveedor, nombre='Fuente holgada', precio=Decimal('80000'), stock=2,
            potencia_watts=750, certificacion='80+ Gold', modular=True,
        )
        cls.user = User.objects.create_user('potencia', 'potencia@example.com', 'clave-potencia')

    def post(self, categoria, componentes):
        return self.client.post(
            reverse('core:recomendar_armado'),
            data=json.dumps({'categoria': categoria, 'componentes': componentes}),
            content_type='application/json',
        )

    def fuentes(self, componentes):
        response = self.post('fuente_de_poder', componentes)
        self.assertEqual(response.status_code, 200)
        return {item['nombre']: item for item in response.json()['candidatos']}

    @override_settings(POLITICA_POTENCIA_ARMADO={'reserva_otros_watts': 50, 'margen': '1.10'})
    def test_recomienda_la_fuente_que_alcanza_sin_declararla_completa(self):
        por_nombre = self.fuentes([
            {'tipo': 'procesador', 'id': self.cpu.id},
            {'tipo': 'tarjeta_grafica', 'id': self.gpu.id},
        ])

        justa = por_nombre['Fuente justa']
        corta = por_nombre['Fuente corta']
        holgada = por_nombre['Fuente holgada']
        self.assertEqual(justa['estado'], 'compatible')
        self.assertIn('Cumple la estimación de potencia (400 W)', justa['etiqueta'])
        self.assertIn('conectores', justa['etiqueta'])
        self.assertNotIn('completamente compatible', justa['etiqueta'].lower())
        self.assertEqual(holgada['estado'], 'compatible')
        self.assertEqual(corta['estado'], 'incompatible')
        self.assertIn('Potencia insuficiente según la política', ' '.join(corta['motivos']))
        self.assertLess(
            [item['nombre'] for item in self.post('fuente_de_poder', [
                {'tipo': 'procesador', 'id': self.cpu.id},
                {'tipo': 'tarjeta_grafica', 'id': self.gpu.id},
            ]).json()['candidatos']].index('Fuente justa'),
            [item['nombre'] for item in self.post('fuente_de_poder', [
                {'tipo': 'procesador', 'id': self.cpu.id},
                {'tipo': 'tarjeta_grafica', 'id': self.gpu.id},
            ]).json()['candidatos']].index('Fuente corta'),
        )

    def test_el_modal_y_el_armado_coinciden_cuando_hacen_falta_mas_de_450w(self):
        cpu = Procesador.objects.create(
            proveedor=self.proveedor, nombre='CPU media 95', precio=Decimal('120000'), stock=4,
            socket='AM4', nucleos=6, frecuencia_base=Decimal('3.80'), potencia_referencia_watts=95,
        )
        gpu = TarjetaGrafica.objects.create(
            proveedor=self.proveedor, nombre='GPU media 170', precio=Decimal('300000'), stock=4,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
            consumo_referencia_watts=170, potencia_minima_fuente_watts=550, largo_mm=270,
        )
        fuente_450 = FuenteDePoder.objects.create(
            proveedor=self.proveedor, nombre='Fuente 450 de prueba', precio=Decimal('35000'), stock=4,
            potencia_watts=450, certificacion='80+ Bronze', modular=False,
        )
        fuente_650 = FuenteDePoder.objects.create(
            proveedor=self.proveedor, nombre='Fuente 650 de prueba', precio=Decimal('65000'), stock=4,
            potencia_watts=650, certificacion='80+ Gold', modular=False,
        )
        placa = PlacaMadre.objects.create(
            proveedor=self.proveedor, nombre='Placa AM4 de prueba', precio=Decimal('80000'), stock=4,
            socket_cpu='AM4', chipset='B550', formato='ATX', ranuras_ram=4,
            tipo_ram_soportado='DDR4', formato_ram_soportado='DIMM', capacidad_maxima_ram_gb=128,
        )
        ram = MemoriaRam.objects.create(
            proveedor=self.proveedor, nombre='RAM DDR4 de prueba', precio=Decimal('30000'), stock=4,
            capacidad_gb=16, tipo_ddr='DDR4', velocidad_mhz=3200, modulos_por_producto=1,
            capacidad_modulo_gb=16, formato_ram='DIMM',
        )
        gabinete = Gabinete.objects.create(
            proveedor=self.proveedor, nombre='Gabinete ATX de prueba', precio=Decimal('40000'), stock=4,
            formato_soporte='ATX', material='Acero', largo_max_gpu_mm=320,
        )
        base = [
            {'tipo': 'procesador', 'id': cpu.id},
            {'tipo': 'tarjeta_grafica', 'id': gpu.id},
        ]
        por_nombre = self.fuentes(base)
        componentes = base + [
            {'tipo': 'placa_madre', 'id': placa.id},
            {'tipo': 'memoria_ram', 'id': ram.id},
            {'tipo': 'gabinete', 'id': gabinete.id},
        ]

        self.assertEqual(por_nombre['Fuente 450 de prueba']['estado'], 'incompatible')
        self.assertIn('550 W', ' '.join(por_nombre['Fuente 450 de prueba']['motivos']))
        self.assertEqual(por_nombre['Fuente 650 de prueba']['estado'], 'compatible')

        for fuente, esperado in ((fuente_450, 'incompatible'), (fuente_650, 'compatible')):
            respuesta = self.client.post(
                reverse('core:evaluar_armado'),
                data=json.dumps({'componentes': componentes + [
                    {'tipo': 'fuente_de_poder', 'id': fuente.id},
                ]}),
                content_type='application/json',
            )
            self.assertEqual(respuesta.status_code, 200)
            cuerpo = respuesta.json()
            self.assertEqual(cuerpo['estado'], esperado)
            self.assertEqual(cuerpo['piezas']['fuente_de_poder']['estado'], esperado)
            self.assertEqual(
                cuerpo['piezas']['fuente_de_poder']['estado'],
                por_nombre[fuente.nombre]['estado'],
            )

    def test_sin_gpu_la_fuente_queda_incompleta(self):
        por_nombre = self.fuentes([{'tipo': 'procesador', 'id': self.cpu.id}])

        self.assertEqual(por_nombre['Fuente holgada']['estado'], 'incompleto')
        self.assertEqual(por_nombre['Fuente holgada']['etiqueta'], 'Selección incompleta')

    def test_consumo_desconocido_es_dato_insuficiente(self):
        por_nombre = self.fuentes([
            {'tipo': 'procesador', 'id': self.cpu_sin_dato.id},
            {'tipo': 'tarjeta_grafica', 'id': self.gpu_sin_dato.id},
        ])

        self.assertEqual(por_nombre['Fuente holgada']['estado'], 'datos_insuficientes')
        self.assertIn('potencia de referencia del procesador', ' '.join(por_nombre['Fuente holgada']['motivos']))
        self.assertIn('consumo de referencia de la GPU', ' '.join(por_nombre['Fuente holgada']['motivos']))

    @override_settings(POLITICA_POTENCIA_ARMADO={'reserva_otros_watts': 50, 'margen': '1.10'})
    def test_una_fuente_insuficiente_no_entra_al_carrito(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('core:agregar_armado_al_carrito'),
            data=json.dumps({'componentes': [
                {'tipo': 'procesador', 'id': self.cpu.id},
                {'tipo': 'tarjeta_grafica', 'id': self.gpu.id},
                {'tipo': 'fuente_de_poder', 'id': self.fuente_corta.id},
            ]}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['estado'], 'incompatible')
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_la_gpu_sigue_sin_declararse_compatible(self):
        evaluacion = evaluar_candidato(
            'tarjeta_grafica',
            self.gpu,
            procesador=self.cpu,
            fuente_de_poder=self.fuente_holgada,
        )

        self.assertEqual(evaluacion.estado, 'incompleto')
        self.assertEqual(evaluacion.etiqueta, 'Selección incompleta')
        self.assertNotIn('Cumple el límite de largo', evaluacion.etiqueta)
