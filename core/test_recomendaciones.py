import json
from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase
from django.urls import reverse

from core.compatibilidad import evaluar_candidato
from core.models import (
    AlmacenamientoHDD,
    AlmacenamientoSSD,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    Proveedor,
)


def pieza(**atributos):
    return SimpleNamespace(**atributos)


class EvaluarCandidatoTests(TestCase):
    def test_empezar_por_placa_o_por_cpu_usa_la_misma_regla(self):
        cpu_am5 = pieza(socket='AM5')
        cpu_am4 = pieza(socket='AM4')
        placa_am5 = pieza(socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX')

        desde_placa = evaluar_candidato('procesador', cpu_am5, placa_madre=placa_am5)
        desde_cpu = evaluar_candidato('placa_madre', placa_am5, procesador=cpu_am5)
        otro_cpu = evaluar_candidato('procesador', cpu_am4, placa_madre=placa_am5)

        self.assertEqual(desde_placa.estado, 'compatible')
        self.assertEqual(desde_cpu.estado, 'compatible')
        self.assertIn('Socket AM5', desde_placa.coincidencias)
        self.assertIn('Socket AM5', desde_cpu.coincidencias)
        self.assertEqual(otro_cpu.estado, 'incompatible')
        self.assertTrue(otro_cpu.motivos)

    def test_reemplaza_la_pieza_anterior_de_la_misma_categoria(self):
        cpu = pieza(socket='AM5')
        placa_anterior = pieza(socket_cpu='AM4', tipo_ram_soportado='DDR4', formato='ATX')
        placa_nueva = pieza(socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX')

        evaluacion = evaluar_candidato(
            'placa_madre',
            placa_nueva,
            procesador=cpu,
            placa_madre=placa_anterior,
        )

        self.assertEqual(evaluacion.estado, 'compatible')
        self.assertIn('Socket AM5', evaluacion.coincidencias)
        self.assertNotIn('AM4', ' '.join(evaluacion.motivos))

    def test_socket_otro_es_dato_insuficiente_y_no_compatible(self):
        evaluacion = evaluar_candidato(
            'procesador',
            pieza(socket='Otro'),
            placa_madre=pieza(socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX'),
        )

        self.assertEqual(evaluacion.estado, 'datos_insuficientes')
        self.assertFalse(evaluacion.etiqueta.startswith('Coincide'))
        self.assertTrue(evaluacion.motivos)

    def test_candidato_incompatible_trae_el_motivo(self):
        evaluacion = evaluar_candidato(
            'gabinete',
            pieza(formato_soporte='Mini-ITX'),
            placa_madre=pieza(socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX'),
        )

        self.assertEqual(evaluacion.estado, 'incompatible')
        self.assertIn('ATX', ' '.join(evaluacion.motivos))
        self.assertIn('MINI-ITX', ' '.join(evaluacion.motivos))

    def test_sin_par_es_seleccion_incompleta(self):
        evaluacion = evaluar_candidato('memoria_ram', pieza(tipo_ddr='DDR5'))

        self.assertEqual(evaluacion.estado, 'incompleto')
        self.assertEqual(evaluacion.etiqueta, 'Selección incompleta')
        self.assertEqual(evaluacion.coincidencias, ())

    def test_gpu_y_almacenamiento_no_se_declaran_compatibles(self):
        cpu = pieza(socket='AM5')
        placa = pieza(socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX')
        for categoria in ('almacenamiento_ssd', 'almacenamiento_hdd'):
            evaluacion = evaluar_candidato(categoria, pieza(nombre='Pieza'), procesador=cpu, placa_madre=placa)
            self.assertEqual(evaluacion.estado, 'no_evaluada')
            self.assertEqual(evaluacion.etiqueta, 'Compatibilidad no evaluada')

        gpu = evaluar_candidato('tarjeta_grafica', pieza(largo_mm=300), procesador=cpu, placa_madre=placa)
        self.assertEqual(gpu.estado, 'incompleto')
        self.assertEqual(gpu.etiqueta, 'Selección incompleta')

        fuente = evaluar_candidato(
            'fuente_de_poder',
            pieza(potencia_watts=650),
            procesador=cpu,
            placa_madre=placa,
        )
        self.assertEqual(fuente.estado, 'incompleto')
        self.assertNotIn('completamente compatible', fuente.etiqueta.lower())

    def test_coincidencias_nombran_la_regla_comprobada(self):
        evaluacion = evaluar_candidato(
            'memoria_ram',
            pieza(tipo_ddr='DDR5'),
            placa_madre=pieza(socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX'),
            gabinete=pieza(formato_soporte='ATX'),
        )

        self.assertEqual(evaluacion.estado, 'compatible')
        self.assertTrue(any(texto.startswith('DDR ') for texto in evaluacion.coincidencias))


class RecomendarArmadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proveedor = Proveedor.objects.create(nombre='Marca Recomendacion')
        cls.cpu_am5 = cls._cpu('AM5', 'CPU AM5 con stock', Decimal('150000'), 4)
        cls.cpu_am5_agotada = cls._cpu('AM5', 'CPU AM5 agotada', Decimal('1000'), 0)
        cls.cpu_am4 = cls._cpu('AM4', 'CPU AM4', Decimal('90000'), 4)
        cls.cpu_otro = cls._cpu('Otro', 'CPU Otro', Decimal('50000'), 4)
        cls.placa_am5 = cls._placa('AM5', 'DDR5', 'ATX', 'Placa AM5')
        cls.placa_am4 = cls._placa('AM4', 'DDR4', 'ATX', 'Placa AM4')
        cls.ram_ddr5 = cls._ram('DDR5', 'RAM DDR5')
        cls.ram_ddr4 = cls._ram('DDR4', 'RAM DDR4')
        cls.ssd = AlmacenamientoSSD.objects.create(
            proveedor=cls.proveedor, nombre='SSD demo', precio=Decimal('40000'), stock=3,
            capacidad_gb=1000, interfaz='NVMe PCIe 4.0', formato='M.2 2280',
        )
        cls.hdd = AlmacenamientoHDD.objects.create(
            proveedor=cls.proveedor, nombre='HDD demo', precio=Decimal('30000'), stock=3,
            capacidad_gb=2000, velocidad_rpm=7200, cache_mb=64,
        )

    @classmethod
    def _cpu(cls, socket, nombre, precio, stock):
        return Procesador.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=precio, stock=stock,
            socket=socket, nucleos=6, frecuencia_base=Decimal('3.50'),
        )

    @classmethod
    def _placa(cls, socket, ddr, formato, nombre):
        return PlacaMadre.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=Decimal('80000'), stock=4,
            socket_cpu=socket, chipset='B650', formato=formato, ranuras_ram=4,
            tipo_ram_soportado=ddr,
        )

    @classmethod
    def _ram(cls, tipo, nombre):
        return MemoriaRam.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=Decimal('30000'), stock=4,
            capacidad_gb=16, tipo_ddr=tipo, velocidad_mhz=5600,
        )

    def post(self, categoria, componentes):
        return self.client.post(
            reverse('core:recomendar_armado'),
            data=json.dumps({'categoria': categoria, 'componentes': componentes}),
            content_type='application/json',
        )

    def test_prioriza_compatible_con_stock_y_deshabilita_agotados(self):
        response = self.post('procesador', [{'tipo': 'placa_madre', 'id': self.placa_am5.id}])

        self.assertEqual(response.status_code, 200)
        candidatos = response.json()['candidatos']
        por_nombre = {candidato['nombre']: candidato for candidato in candidatos}
        self.assertEqual(por_nombre['CPU AM5 con stock']['estado'], 'compatible')
        self.assertTrue(por_nombre['CPU AM5 con stock']['seleccionable'])
        self.assertIn('Socket AM5', por_nombre['CPU AM5 con stock']['coincidencias'])
        self.assertEqual(por_nombre['CPU AM5 agotada']['estado'], 'compatible')
        self.assertFalse(por_nombre['CPU AM5 agotada']['seleccionable'])
        self.assertEqual(por_nombre['CPU AM4']['estado'], 'incompatible')
        self.assertTrue(por_nombre['CPU AM4']['motivos'])
        self.assertEqual(por_nombre['CPU Otro']['estado'], 'datos_insuficientes')
        self.assertLess(
            candidatos.index(por_nombre['CPU AM5 con stock']),
            candidatos.index(por_nombre['CPU AM4']),
        )
        self.assertLess(
            candidatos.index(por_nombre['CPU AM5 con stock']),
            candidatos.index(por_nombre['CPU AM5 agotada']),
        )

    def test_el_orden_de_las_piezas_enviadas_no_cambia_el_resultado(self):
        piezas = [
            {'tipo': 'procesador', 'id': self.cpu_am5.id},
            {'tipo': 'placa_madre', 'id': self.placa_am5.id},
        ]
        primera = self.post('memoria_ram', piezas)
        segunda = self.post('memoria_ram', list(reversed(piezas)))

        def estados(response):
            return [(item['nombre'], item['estado'], item['coincidencias']) for item in response.json()['candidatos']]

        self.assertEqual(estados(primera), estados(segunda))
        ddr5 = next(item for item in primera.json()['candidatos'] if item['nombre'] == 'RAM DDR5')
        ddr4 = next(item for item in primera.json()['candidatos'] if item['nombre'] == 'RAM DDR4')
        self.assertEqual(ddr5['estado'], 'compatible')
        self.assertTrue(any(texto.startswith('DDR ') for texto in ddr5['coincidencias']))
        self.assertEqual(ddr4['estado'], 'incompatible')

    def test_reemplaza_la_placa_que_ya_estaba_elegida(self):
        response = self.post('placa_madre', [
            {'tipo': 'procesador', 'id': self.cpu_am5.id},
            {'tipo': 'placa_madre', 'id': self.placa_am4.id},
        ])

        por_nombre = {candidato['nombre']: candidato for candidato in response.json()['candidatos']}
        self.assertEqual(por_nombre['Placa AM5']['estado'], 'compatible')
        self.assertIn('Socket AM5', por_nombre['Placa AM5']['coincidencias'])
        self.assertEqual(por_nombre['Placa AM4']['estado'], 'incompatible')

    def test_almacenamiento_conserva_el_tipo_y_no_se_declara_compatible(self):
        response = self.post('almacenamiento', [
            {'tipo': 'procesador', 'id': self.cpu_am5.id},
            {'tipo': 'placa_madre', 'id': self.placa_am5.id},
        ])

        por_nombre = {candidato['nombre']: candidato for candidato in response.json()['candidatos']}
        self.assertEqual(por_nombre['SSD demo']['model_name'], 'almacenamiento_ssd')
        self.assertEqual(por_nombre['HDD demo']['model_name'], 'almacenamiento_hdd')
        self.assertEqual(por_nombre['SSD demo']['estado'], 'no_evaluada')
        self.assertEqual(por_nombre['HDD demo']['etiqueta'], 'Compatibilidad no evaluada')
        self.assertEqual(por_nombre['SSD demo']['etiqueta'], 'Compatibilidad no evaluada')
