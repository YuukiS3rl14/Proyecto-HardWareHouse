import json
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.admin import GabineteAdmin, TarjetaGraficaAdmin
from core.compatibilidad import evaluar_candidato, validar_armado
from core.models import (
    AlmacenamientoSSD,
    Carrito,
    FuenteDePoder,
    Gabinete,
    ItemCarrito,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    Proveedor,
    RefrigeracionCooler,
    TarjetaGrafica,
)
from core.tests import pieza


def armado_largo(largo_gpu, largo_maximo):
    return validar_armado(
        procesador=pieza(socket='AM5'),
        placa_madre=pieza(
            socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX',
            ranuras_ram=4, formato_ram_soportado='DIMM', capacidad_maxima_ram_gb=128,
        ),
        memoria_ram=pieza(
            tipo_ddr='DDR5', capacidad_gb=16, modulos_por_producto=1,
            capacidad_modulo_gb=16, formato_ram='DIMM',
        ),
        gabinete=pieza(formato_soporte='ATX', largo_max_gpu_mm=largo_maximo),
        tarjeta_grafica=pieza(largo_mm=largo_gpu),
    )


class LargoGpuTests(TestCase):
    def test_el_limite_exacto_cabe_y_un_milimetro_no(self):
        exacto = armado_largo(320, 320)
        exceso = armado_largo(321, 320)

        self.assertEqual(exacto.estado, 'compatible')
        self.assertFalse(exacto.bloquea_agregar)
        self.assertFalse(any(hallazgo.regla == 'largo' for hallazgo in exacto.hallazgos))
        self.assertEqual(exceso.estado, 'incompatible')
        self.assertTrue(exceso.bloquea_agregar)
        texto = ' '.join(exceso.motivos_de_rechazo)
        self.assertIn('321 mm', texto)
        self.assertIn('320 mm', texto)
        self.assertIn('no el grosor', texto)

    def test_la_medida_desconocida_no_se_toma_como_cero(self):
        for largo_gpu, largo_maximo in ((None, 320), (320, None), (0, 320), (320, 0)):
            resultado = armado_largo(largo_gpu, largo_maximo)
            self.assertEqual(resultado.estado, 'datos_insuficientes', (largo_gpu, largo_maximo))
            self.assertTrue(resultado.bloquea_agregar)
            self.assertIn('no se toma como medida conocida', ' '.join(resultado.motivos_de_rechazo))

    def test_sin_gpu_o_sin_gabinete_la_seleccion_queda_incompleta(self):
        sin_gpu = validar_armado(
            procesador=pieza(socket='AM5'),
            gabinete=pieza(formato_soporte='ATX', largo_max_gpu_mm=320),
            placa_madre=pieza(
                socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX',
                ranuras_ram=4, formato_ram_soportado='DIMM', capacidad_maxima_ram_gb=128,
            ),
            memoria_ram=pieza(
                tipo_ddr='DDR5', capacidad_gb=16, modulos_por_producto=1,
                capacidad_modulo_gb=16, formato_ram='DIMM',
            ),
        )
        sin_gabinete = validar_armado(tarjeta_grafica=pieza(largo_mm=320))

        self.assertEqual(sin_gpu.estado, 'incompleto')
        self.assertEqual(sin_gabinete.estado, 'incompleto')
        self.assertFalse(sin_gpu.bloquea_agregar)
        self.assertFalse(sin_gabinete.bloquea_agregar)

    def test_el_texto_de_cumplimiento_no_valida_otras_dimensiones(self):
        desde_gpu = evaluar_candidato(
            'tarjeta_grafica',
            pieza(largo_mm=320),
            gabinete=pieza(formato_soporte='ATX', largo_max_gpu_mm=320),
        )
        desde_gabinete = evaluar_candidato(
            'gabinete',
            pieza(formato_soporte='ATX', largo_max_gpu_mm=320),
            tarjeta_grafica=pieza(largo_mm=320),
            placa_madre=pieza(socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX'),
        )

        self.assertEqual(desde_gpu.estado, 'compatible')
        self.assertTrue(desde_gpu.etiqueta.startswith('Cumple el límite de largo (320 mm de 320 mm)'))
        self.assertIn('radiadores', desde_gpu.etiqueta)
        self.assertIn('Formato ATX', desde_gabinete.coincidencias)
        self.assertTrue(any(texto.startswith('Cumple el límite de largo') for texto in desde_gabinete.coincidencias))

    def test_el_admin_muestra_los_campos(self):
        self.assertIn('largo_mm', TarjetaGraficaAdmin.list_display)
        self.assertIn('largo_mm', TarjetaGraficaAdmin.fieldsets[1][1]['fields'])
        self.assertIn('largo_max_gpu_mm', GabineteAdmin.list_display)
        self.assertIn('largo_max_gpu_mm', GabineteAdmin.fieldsets[1][1]['fields'])


class RecomendacionLargoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proveedor = Proveedor.objects.create(nombre='Marca Largo')
        cls.placa = PlacaMadre.objects.create(
            proveedor=cls.proveedor, nombre='Placa ATX', precio=Decimal('80000'), stock=4,
            socket_cpu='AM5', chipset='B650', formato='ATX', ranuras_ram=4, tipo_ram_soportado='DDR5',
        )
        cls.gpu_exacta = cls._gpu('GPU exacta', 320, Decimal('100000'))
        cls.gpu_larga = cls._gpu('GPU larga', 321, Decimal('150000'))
        cls.gpu_sin_dato = cls._gpu('GPU sin largo', None, Decimal('90000'))
        cls.case_exacto = cls._case('Gabinete exacto', 'ATX', 320, Decimal('50000'))
        cls.case_corto = cls._case('Gabinete corto', 'ATX', 319, Decimal('40000'))
        cls.case_mini = cls._case('Gabinete mini', 'Mini-ITX', 400, Decimal('30000'))
        cls.case_sin_dato = cls._case('Gabinete sin máximo', 'ATX', None, Decimal('20000'))
        cls.user = User.objects.create_user('largo', 'largo@example.com', 'clave-largo')

    @classmethod
    def _gpu(cls, nombre, largo, precio):
        return TarjetaGrafica.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=precio, stock=4,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0', largo_mm=largo,
        )

    @classmethod
    def _case(cls, nombre, formato, largo_maximo, precio):
        return Gabinete.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=precio, stock=4,
            formato_soporte=formato, material='Acero', largo_max_gpu_mm=largo_maximo,
        )

    def post(self, categoria, componentes):
        return self.client.post(
            reverse('core:recomendar_armado'),
            data=json.dumps({'categoria': categoria, 'componentes': componentes}),
            content_type='application/json',
        )

    def test_elegir_gpu_o_gabinete_usa_la_misma_regla(self):
        gpus = self.post('tarjeta_grafica', [{'tipo': 'gabinete', 'id': self.case_exacto.id}])
        cases = self.post('gabinete', [
            {'tipo': 'tarjeta_grafica', 'id': self.gpu_exacta.id},
            {'tipo': 'placa_madre', 'id': self.placa.id},
        ])
        self.assertEqual(gpus.status_code, 200)
        self.assertEqual(cases.status_code, 200)

        por_gpu = {item['nombre']: item for item in gpus.json()['candidatos']}
        por_case = {item['nombre']: item for item in cases.json()['candidatos']}
        self.assertEqual(por_gpu['GPU exacta']['estado'], 'compatible')
        self.assertIn('320 mm de 320 mm', por_gpu['GPU exacta']['etiqueta'])
        self.assertEqual(por_gpu['GPU larga']['estado'], 'incompatible')
        self.assertIn('321 mm', ' '.join(por_gpu['GPU larga']['motivos']))
        self.assertIn('320 mm', ' '.join(por_gpu['GPU larga']['motivos']))
        self.assertEqual(por_gpu['GPU sin largo']['estado'], 'datos_insuficientes')
        self.assertEqual(por_case['Gabinete exacto']['estado'], 'compatible')
        self.assertIn('Formato ATX', por_case['Gabinete exacto']['coincidencias'])
        self.assertTrue(any('límite de largo' in texto for texto in por_case['Gabinete exacto']['coincidencias']))
        self.assertEqual(por_case['Gabinete corto']['estado'], 'incompatible')
        self.assertEqual(por_case['Gabinete mini']['estado'], 'incompatible')
        self.assertIn('MINI-ITX', ' '.join(por_case['Gabinete mini']['motivos']))
        self.assertEqual(por_case['Gabinete sin máximo']['estado'], 'datos_insuficientes')
        nombres_gpu = [item['nombre'] for item in gpus.json()['candidatos']]
        self.assertLess(nombres_gpu.index('GPU exacta'), nombres_gpu.index('GPU larga'))

    def test_sin_la_otra_pieza_queda_incompleta_en_ambos_sentidos(self):
        gpus = self.post('tarjeta_grafica', [])
        cases = self.post('gabinete', [{'tipo': 'placa_madre', 'id': self.placa.id}])
        por_gpu = {item['nombre']: item for item in gpus.json()['candidatos']}
        por_case = {item['nombre']: item for item in cases.json()['candidatos']}

        self.assertEqual(por_gpu['GPU exacta']['estado'], 'incompleto')
        self.assertEqual(por_gpu['GPU exacta']['etiqueta'], 'Selección incompleta')
        self.assertEqual(por_case['Gabinete exacto']['estado'], 'compatible')
        self.assertTrue(por_case['Gabinete exacto']['pendientes'])

    def test_gpu_mas_larga_no_entra_al_carrito(self):
        self.client.force_login(self.user)
        carrito_previo = ItemCarrito.objects.create(
            carrito=Carrito.objects.create(usuario=self.user),
            fuente_de_poder=FuenteDePoder.objects.create(
                proveedor=self.proveedor, nombre='Fuente ajena', precio=Decimal('10000'), stock=2,
                potencia_watts=500, certificacion='80+ Bronze',
            ),
            cantidad=1,
            precio_unitario=Decimal('10000'),
        )

        response = self.client.post(
            reverse('core:agregar_armado_al_carrito'),
            data=json.dumps({'componentes': [
                {'tipo': 'tarjeta_grafica', 'id': self.gpu_larga.id},
                {'tipo': 'gabinete', 'id': self.case_exacto.id},
            ]}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['estado'], 'incompatible')
        self.assertEqual(ItemCarrito.objects.count(), 1)
        self.assertTrue(ItemCarrito.objects.filter(pk=carrito_previo.pk).exists())
        self.assertFalse(ItemCarrito.objects.filter(tarjeta_grafica__isnull=False).exists())
        self.assertFalse(ItemCarrito.objects.filter(gabinete__isnull=False).exists())


class EvaluacionVisualTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        proveedor = Proveedor.objects.create(nombre='Marca Visual')
        cls.cpu = Procesador.objects.create(
            proveedor=proveedor, nombre='CPU visual', precio=Decimal('100000'), stock=3,
            socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'), potencia_referencia_watts=65,
        )
        cls.placa = PlacaMadre.objects.create(
            proveedor=proveedor, nombre='Placa visual', precio=Decimal('80000'), stock=3,
            socket_cpu='AM5', chipset='B650', formato='ATX', ranuras_ram=4, tipo_ram_soportado='DDR5',
            formato_ram_soportado='DIMM', capacidad_maxima_ram_gb=128,
        )
        cls.ram = MemoriaRam.objects.create(
            proveedor=proveedor, nombre='RAM visual', precio=Decimal('40000'), stock=3,
            capacidad_gb=16, tipo_ddr='DDR5', velocidad_mhz=5600,
            modulos_por_producto=1, capacidad_modulo_gb=16, formato_ram='DIMM',
        )
        cls.cooler = RefrigeracionCooler.objects.create(
            proveedor=proveedor, nombre='Cooler visual', precio=Decimal('30000'), stock=3,
            tipo='Aire', socket_compatibles='AM5',
        )
        cls.gpu = TarjetaGrafica.objects.create(
            proveedor=proveedor, nombre='GPU 320', precio=Decimal('200000'), stock=3,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
            consumo_referencia_watts=100, largo_mm=320,
        )
        cls.gpu_larga = TarjetaGrafica.objects.create(
            proveedor=proveedor, nombre='GPU 321', precio=Decimal('210000'), stock=3,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0', largo_mm=321,
        )
        cls.gpu_sin_dato = TarjetaGrafica.objects.create(
            proveedor=proveedor, nombre='GPU sin largo visual', precio=Decimal('90000'), stock=3,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
        )
        cls.case = Gabinete.objects.create(
            proveedor=proveedor, nombre='Gabinete 320', precio=Decimal('50000'), stock=3,
            formato_soporte='ATX', material='Acero', largo_max_gpu_mm=320,
        )
        cls.fuente = FuenteDePoder.objects.create(
            proveedor=proveedor, nombre='Fuente visual', precio=Decimal('60000'), stock=3,
            potencia_watts=500, certificacion='80+ Bronze', modular=False,
        )
        cls.ssd = AlmacenamientoSSD.objects.create(
            proveedor=proveedor, nombre='SSD visual', precio=Decimal('20000'), stock=3,
            capacidad_gb=500, interfaz='NVMe PCIe 4.0', formato='M.2 2280',
        )

    def post(self, componentes):
        return self.client.post(
            reverse('core:evaluar_armado'),
            data=json.dumps({'componentes': componentes}),
            content_type='application/json',
        )

    def piezas(self, *objetos):
        return [{'tipo': self._tipo(objeto), 'id': objeto.id} for objeto in objetos]

    def _tipo(self, objeto):
        nombres = {
            Procesador: 'procesador',
            PlacaMadre: 'placa_madre',
            MemoriaRam: 'memoria_ram',
            RefrigeracionCooler: 'refrigeracion',
            TarjetaGrafica: 'tarjeta_grafica',
            Gabinete: 'gabinete',
            FuenteDePoder: 'fuente_de_poder',
            AlmacenamientoSSD: 'almacenamiento_ssd',
        }
        return nombres[type(objeto)]

    def test_las_tarjetas_reciben_largo_y_el_resto_de_reglas(self):
        componentes = self.piezas(
            self.cpu, self.placa, self.ram, self.cooler, self.gpu, self.case, self.fuente, self.ssd,
        )
        response = self.post(componentes)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        piezas = data['piezas']

        self.assertEqual(data['estado'], 'compatible')
        self.assertIn('piezas sin regla', data['texto'])
        self.assertTrue(piezas['tarjeta_grafica']['etiqueta'].startswith('Cumple el límite de largo (320 mm de 320 mm)'))
        self.assertIn('radiadores', piezas['tarjeta_grafica']['etiqueta'])
        self.assertIn('Formato ATX', piezas['gabinete']['etiqueta'])
        self.assertIn('Cumple el límite de largo (320 mm de 320 mm)', piezas['gabinete']['etiqueta'])
        self.assertIn('Socket AM5', piezas['procesador']['etiqueta'])
        self.assertIn('DDR DDR5', piezas['memoria_ram']['etiqueta'])
        self.assertIn('Cooler para AM5', piezas['refrigeracion_cooler']['etiqueta'])
        self.assertIn('Cumple la estimación de potencia', piezas['fuente_de_poder']['etiqueta'])
        self.assertIn('conectores', piezas['fuente_de_poder']['etiqueta'])
        self.assertEqual(piezas['almacenamiento']['estado'], 'no_evaluada')
        self.assertIn('SATA', piezas['almacenamiento']['etiqueta'])
        self.assertIn('bahías', piezas['almacenamiento']['etiqueta'])
        self.assertNotEqual(piezas['almacenamiento']['estado'], 'compatible')
        self.assertEqual(Carrito.objects.count(), 0)
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_el_exceso_los_datos_desconocidos_y_la_seleccion_incompleta(self):
        exceso = self.post(self.piezas(self.gpu_larga, self.case)).json()['piezas']
        self.assertEqual(exceso['tarjeta_grafica']['estado'], 'incompatible')
        self.assertEqual(exceso['gabinete']['estado'], 'incompatible')
        texto_gpu = ' '.join(exceso['tarjeta_grafica']['motivos'])
        texto_case = ' '.join(exceso['gabinete']['motivos'])
        self.assertIn('321 mm', texto_gpu)
        self.assertIn('320 mm', texto_gpu)
        self.assertIn('321 mm', texto_case)
        self.assertIn('320 mm', texto_case)

        sin_dato = self.post(self.piezas(self.gpu_sin_dato, self.case)).json()['piezas']
        self.assertEqual(sin_dato['tarjeta_grafica']['estado'], 'datos_insuficientes')
        self.assertEqual(sin_dato['gabinete']['estado'], 'datos_insuficientes')
        self.assertEqual(sin_dato['tarjeta_grafica']['etiqueta'], 'Datos insuficientes')

        solo_gpu = self.post(self.piezas(self.gpu)).json()
        self.assertEqual(solo_gpu['estado'], 'incompleto')
        self.assertEqual(solo_gpu['texto'], 'Selección incompleta')
        self.assertEqual(solo_gpu['piezas']['tarjeta_grafica']['etiqueta'], 'Selección incompleta')

        sin_gpu = self.post(self.piezas(self.placa, self.case)).json()['piezas']['gabinete']
        self.assertIn('Formato ATX', sin_gpu['coincidencias'])
        self.assertTrue(sin_gpu['pendientes'])
        self.assertNotIn('321 mm', ' '.join(sin_gpu['motivos']))

    def test_una_pieza_inexistente_no_devuelve_la_evaluacion(self):
        response = self.post([{'tipo': 'gabinete', 'id': 999999}])
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('piezas', response.json())

    def test_el_armador_no_recalcula_las_reglas_en_el_navegador(self):
        js = Path(__file__).resolve().parent.joinpath('static', 'core', 'js', 'pc-builder.js').read_text(encoding='utf-8')
        pagina = self.client.get(reverse('core:armado'))
        inicio = js.index('async function downloadAsExcel')
        hasta_archivo = js.index('URL.createObjectURL')
        self.assertNotIn('function checkCompatibility', js)
        self.assertNotIn('function evaluarSocket', js)
        self.assertNotIn('XLSX', js)
        self.assertIn('evaluarUrl', js)
        self.assertIn('exportarUrl', js[inicio:hasta_archivo])
        self.assertNotIn('evaluacionActual', js[inicio:hasta_archivo])
        self.assertLess(js.index('El Excel no se generó'), hasta_archivo)
        self.assertContains(pagina, 'data-evaluar-url')
        self.assertContains(pagina, 'data-exportar-url')
        self.assertContains(pagina, 'pc-builder.js?v=ram1')
        self.assertNotContains(pagina, 'xlsx.full.min.js')
