import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.compatibilidad import LineaRam
from core.models import (
    AlmacenamientoHDD,
    AlmacenamientoSSD,
    FuenteDePoder,
    Gabinete,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    Proveedor,
    RefrigeracionCooler,
    TarjetaGrafica,
)
from core.recomendador_pc import EntradaInvalida, generar_recomendaciones, interpretar_pedido


class RecomendadorPcTests(TestCase):
    def setUp(self):
        self.proveedor = Proveedor.objects.create(nombre='Marca Recomendador')

    def cpu(self, nombre, socket, nucleos=6, frecuencia='3.50', watts=65, precio='100000', stock=4, incluye=None, termica=None):
        return Procesador.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal(precio), stock=stock,
            socket=socket, nucleos=nucleos, frecuencia_base=Decimal(frecuencia),
            potencia_referencia_watts=watts, incluye_cooler=incluye,
            potencia_termica_referencia_watts=termica,
        )

    def placa(self, nombre, socket, ddr, precio='80000', stock=4, formato_ram='DIMM', ranuras=4, capacidad=128):
        return PlacaMadre.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal(precio), stock=stock,
            socket_cpu=socket, chipset='B650' if socket == 'AM5' else 'B550', formato='ATX',
            ranuras_ram=ranuras, tipo_ram_soportado=ddr, formato_ram_soportado=formato_ram,
            capacidad_maxima_ram_gb=capacidad,
        )

    def ram(self, nombre, ddr, precio='20000', stock=4, formato='DIMM', modulos=1, capacidad=16):
        return MemoriaRam.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal(precio), stock=stock,
            capacidad_gb=capacidad, tipo_ddr=ddr, velocidad_mhz=5600,
            modulos_por_producto=modulos, capacidad_modulo_gb=capacidad if modulos == 1 else None,
            formato_ram=formato,
        )

    def cooler(self, sockets, precio='15000', stock=4, altura=None, disipacion=None, tipo='Aire', nombre=None):
        return RefrigeracionCooler.objects.create(
            proveedor=self.proveedor, nombre=nombre or f'Cooler {sockets}', precio=Decimal(precio), stock=stock,
            tipo=tipo, socket_compatibles=sockets, altura_mm=altura,
            disipacion_referencia_watts=disipacion,
        )

    def gpu(self, nombre, largo, consumo=100, vram=8, precio='150000', stock=2):
        return TarjetaGrafica.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal(precio), stock=stock,
            vram_gb=vram, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
            consumo_referencia_watts=consumo, largo_mm=largo,
        )

    def gabinete(self, nombre, largo, precio='40000', stock=2, altura_max=None):
        return Gabinete.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal(precio), stock=stock,
            formato_soporte='ATX', material='Acero', largo_max_gpu_mm=largo,
            altura_max_cooler_mm=altura_max,
        )

    def fuente(self, nombre, watts, precio='50000', stock=2):
        return FuenteDePoder.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal(precio), stock=stock,
            potencia_watts=watts, certificacion='80+ Bronze', modular=False,
        )

    def ssd(self, nombre='SSD 1TB', precio='25000', stock=4, capacidad=1000):
        return AlmacenamientoSSD.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal(precio), stock=stock,
            capacidad_gb=capacidad, interfaz='NVMe PCIe 4.0', formato='M.2 2280',
        )

    def catalogo_valido(self):
        return {
            'cpu': self.cpu('CPU AM5', 'AM5', nucleos=8, frecuencia='4.20'),
            'placa': self.placa('Placa AM5', 'AM5', 'DDR5'),
            'ram': self.ram('RAM DDR5', 'DDR5'),
            'cooler': self.cooler('AM5'),
            'gpu': self.gpu('GPU 280', 280),
            'gabinete': self.gabinete('Gabinete 350', 350),
            'fuente': self.fuente('Fuente 650', 650),
            'ssd': self.ssd(),
        }

    def test_un_armado_valido_explica_y_no_se_declara_del_todo_compatible_con_disco(self):
        piezas = self.catalogo_valido()
        resultado = generar_recomendaciones(2_000_000, 'gaming')

        self.assertEqual(resultado['status'], 'success')
        opcion = resultado['recomendaciones'][0]
        self.assertEqual(opcion['estado_reglas'], 'compatible')
        self.assertFalse(opcion['completamente_compatible'])
        self.assertLessEqual(opcion['total'], 2_000_000)
        self.assertIn('No se estiman FPS', opcion['explicacion'])
        self.assertTrue(any('SATA' in texto for texto in opcion['limitaciones']))
        tipos = {item['tipo'] for item in opcion['componentes']}
        self.assertIn('procesador', tipos)
        self.assertIn('almacenamiento_ssd', tipos)
        self.assertEqual(piezas['cpu'].id, self._id(opcion, 'procesador'))

    def test_gaming_elige_ssd_aunque_exista_un_hdd_mas_grande(self):
        self.catalogo_valido()
        AlmacenamientoHDD.objects.create(
            proveedor=self.proveedor, nombre='HDD 4TB', precio=Decimal('30000'), stock=2,
            capacidad_gb=4000, velocidad_rpm=7200, cache_mb=256,
        )
        opcion = generar_recomendaciones(2_000_000, 'gaming')['recomendaciones'][0]
        tipos = {item['tipo'] for item in opcion['componentes']}

        self.assertIn('almacenamiento_ssd', tipos)
        self.assertNotIn('almacenamiento_hdd', tipos)

    def test_prioriza_dos_modulos_cuando_hay_stock_y_presupuesto(self):
        self.catalogo_valido()
        opcion = generar_recomendaciones(2_000_000, 'gaming')['recomendaciones'][0]
        ram = self._item(opcion, 'memoria_ram')

        self.assertEqual(ram['cantidad'], 2)
        self.assertEqual(ram['subtotal'], 40000)

    def test_presupuesto_insuficiente(self):
        self.catalogo_valido()
        resultado = generar_recomendaciones(1_000, 'general')

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertEqual(resultado['recomendaciones'], [])
        self.assertIn('presupuesto', resultado['mensaje'].lower())

    def test_stock_insuficiente(self):
        self.catalogo_valido()
        Procesador.objects.update(stock=0)
        resultado = generar_recomendaciones(2_000_000, 'general')

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertIn('stock', resultado['mensaje'].lower())

    def test_no_completa_cpu_y_placa_incompatibles(self):
        cpu = self.cpu('CPU AM5', 'AM5')
        placa = self.placa('Placa AM4', 'AM4', 'DDR4')
        resultado = generar_recomendaciones(
            2_000_000,
            'general',
            seleccion={'procesador': cpu, 'placa_madre': placa},
        )

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertIn('AM5', resultado['mensaje'])
        self.assertIn('AM4', resultado['mensaje'])

    def test_no_completa_ram_ddr_incompatible(self):
        placa = self.placa('Placa AM5', 'AM5', 'DDR5')
        ram = self.ram('RAM DDR4', 'DDR4')
        resultado = generar_recomendaciones(
            2_000_000,
            'general',
            seleccion={'placa_madre': placa},
            memorias=[LineaRam(ram, 1)],
        )

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertIn('DDR4', resultado['mensaje'])
        self.assertIn('DDR5', resultado['mensaje'])

    def test_fuente_insuficiente_no_se_recomienda(self):
        self.cpu('CPU AM5', 'AM5', watts=120)
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280, consumo=220)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 300', 300)
        resultado = generar_recomendaciones(2_000_000, 'gaming')

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertIn('Potencia insuficiente', resultado['mensaje'])

    def test_gpu_demasiado_larga_no_se_recomienda(self):
        self.cpu('CPU AM5', 'AM5')
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU larga', 400)
        self.gabinete('Gabinete corto', 200)
        self.fuente('Fuente 650', 650)
        resultado = generar_recomendaciones(2_000_000, 'gaming')

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertIn('400 mm', resultado['mensaje'])
        self.assertIn('200 mm', resultado['mensaje'])

    def test_datos_incompletos_no_se_presentan_como_compatibles(self):
        self.cpu('CPU AM5', 'AM5')
        self.placa('Placa AM5', 'AM5', 'DDR5')
        MemoriaRam.objects.create(
            proveedor=self.proveedor, nombre='RAM sin formato', precio=Decimal('20000'), stock=4,
            capacidad_gb=16, tipo_ddr='DDR5', velocidad_mhz=5600,
        )
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        resultado = generar_recomendaciones(2_000_000, 'general')

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertFalse(resultado['recomendaciones'])
        self.assertIn('formato DIMM', resultado['mensaje'])

    def test_conserva_el_procesador_seleccionado(self):
        amd4 = self.cpu('CPU AM4', 'AM4', nucleos=4, frecuencia='3.20', precio='70000')
        self.cpu('CPU AM5', 'AM5', nucleos=8, frecuencia='4.20', precio='200000')
        self.placa('Placa AM4', 'AM4', 'DDR4')
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR4', 'DDR4')
        self.ram('RAM DDR5', 'DDR5', precio='30000')
        self.cooler('AM4, AM5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        resultado = generar_recomendaciones(2_000_000, 'gaming', seleccion={'procesador': amd4})

        self.assertEqual(resultado['status'], 'success')
        self.assertEqual(self._id(resultado['recomendaciones'][0], 'procesador'), amd4.id)
        self.assertIn('AM4', self._item(resultado['recomendaciones'][0], 'placa_madre')['motivo'])

    def test_conserva_cantidades_de_ram_y_almacenamiento(self):
        piezas = self.catalogo_valido()
        resultado = generar_recomendaciones(
            2_000_000,
            'trabajo',
            memorias=[LineaRam(piezas['ram'], 1)],
            almacenamientos=[{'tipo': 'almacenamiento_ssd', 'producto': piezas['ssd'], 'cantidad': 2}],
        )
        opcion = resultado['recomendaciones'][0]

        self.assertEqual(self._item(opcion, 'memoria_ram')['cantidad'], 1)
        self.assertEqual(self._item(opcion, 'almacenamiento_ssd')['cantidad'], 2)
        self.assertEqual(self._item(opcion, 'almacenamiento_ssd')['subtotal'], 50000)

    def test_la_recomendacion_se_puede_cargar_en_el_evaluador_y_no_toca_el_carrito(self):
        self.catalogo_valido()
        respuesta = self.client.post(
            reverse('core:recomendar_pc'),
            data=json.dumps({
                'presupuesto': 2_000_000,
                'uso': 'general',
                'resolucion': '1440p',
                'modo': 'desde_cero',
            }),
            content_type='application/json',
        )
        self.assertEqual(respuesta.status_code, 200)
        opcion = respuesta.json()['recomendaciones'][0]
        evaluacion = self.client.post(
            reverse('core:evaluar_armado'),
            data=json.dumps({'componentes': [
                {'tipo': item['tipo'], 'id': item['id'], 'cantidad': item['cantidad']}
                for item in opcion['componentes']
            ]}),
            content_type='application/json',
        )
        self.assertEqual(evaluacion.status_code, 200)
        self.assertEqual(evaluacion.json()['estado'], 'compatible')
        self.assertEqual(evaluacion.json()['piezas']['almacenamiento']['estado'], 'no_evaluada')
        from core.models import ItemCarrito
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_desde_cero_ignora_una_seleccion_incompatible(self):
        self.catalogo_valido()
        cpu_am4 = self.cpu('CPU AM4 suelta', 'AM4')
        respuesta = self.client.post(
            reverse('core:recomendar_pc'),
            data=json.dumps({
                'presupuesto': '2000000',
                'uso': 'general',
                'modo': 'desde_cero',
                'componentes': [{'tipo': 'procesador', 'id': cpu_am4.id}],
            }),
            content_type='application/json',
        )

        self.assertEqual(respuesta.status_code, 200)
        ids = [item['id'] for item in respuesta.json()['recomendaciones'][0]['componentes']]
        self.assertNotIn(cpu_am4.id, ids)

    def test_gaming_reserva_presupuesto_para_una_gpu_con_mas_vram(self):
        modesta = self.cpu('CPU modesta', 'AM5', nucleos=6, frecuencia='3.50', precio='120000')
        self.cpu('CPU cara', 'AM5', nucleos=16, frecuencia='4.80', watts=125, precio='900000')
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU justa', 280, vram=4, precio='100000')
        capaz = self.gpu('GPU capaz', 280, vram=16, consumo=180, precio='600000')
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 750', 750)
        self.ssd()

        opcion = generar_recomendaciones(1_500_000, 'gaming')['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'procesador'), modesta.id)
        self.assertEqual(self._id(opcion, 'tarjeta_grafica'), capaz.id)
        self.assertLessEqual(opcion['total'], 1_500_000)
        self.assertIn('No se estiman FPS', opcion['explicacion'])

    def test_no_paga_mas_por_la_misma_vram(self):
        self.catalogo_valido()
        cara = self.gpu('GPU cara igual', 280, vram=8, precio='400000')
        opcion = generar_recomendaciones(2_000_000, 'gaming')['recomendaciones'][0]

        self.assertNotEqual(self._id(opcion, 'tarjeta_grafica'), cara.id)

    def test_trabajo_prioriza_procesador_aunque_exista_una_gpu_con_mas_vram(self):
        cara = self.cpu('CPU cara', 'AM5', nucleos=16, frecuencia='4.80', watts=125, precio='900000')
        self.cpu('CPU modesta', 'AM5', nucleos=6, frecuencia='3.50', precio='120000')
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU justa', 280, vram=4, precio='100000')
        self.gpu('GPU capaz', 280, vram=16, consumo=180, precio='600000')
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 750', 750)
        self.ssd()

        opcion = generar_recomendaciones(1_500_000, 'trabajo')['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'procesador'), cara.id)
        self.assertLessEqual(opcion['total'], 1_500_000)

    def test_trabajo_prioriza_ssd_aunque_el_hdd_tenga_mas_capacidad(self):
        self.catalogo_valido()
        AlmacenamientoHDD.objects.create(
            proveedor=self.proveedor, nombre='HDD 4TB', precio=Decimal('30000'), stock=2,
            capacidad_gb=4000, velocidad_rpm=7200, cache_mb=256,
        )
        opcion = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones'][0]
        tipos = {item['tipo'] for item in opcion['componentes']}

        self.assertIn('almacenamiento_ssd', tipos)
        self.assertNotIn('almacenamiento_hdd', tipos)
        self.assertTrue(any('SATA' in texto for texto in opcion['limitaciones']))

    def test_sin_ssd_el_hdd_queda_como_alternativa(self):
        piezas = self.catalogo_valido()
        piezas['ssd'].stock = 0
        piezas['ssd'].save(update_fields=['stock'])
        AlmacenamientoHDD.objects.create(
            proveedor=self.proveedor, nombre='HDD 1TB', precio=Decimal('20000'), stock=2,
            capacidad_gb=1000, velocidad_rpm=7200, cache_mb=64,
        )
        opcion = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones'][0]
        tipos = {item['tipo'] for item in opcion['componentes']}

        self.assertIn('almacenamiento_hdd', tipos)
        self.assertNotIn('almacenamiento_ssd', tipos)
        self.assertTrue(any('SATA' in texto for texto in opcion['limitaciones']))

    def test_trabajo_prefiere_mas_capacidad_de_almacenamiento(self):
        self.catalogo_valido()
        grande = self.ssd('SSD 2TB', precio='80000', capacidad=2000)
        opcion = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'almacenamiento_ssd'), grande.id)

    def test_entradas_invalidas(self):
        with self.assertRaises(EntradaInvalida):
            interpretar_pedido({'presupuesto': -1, 'uso': 'gaming', 'modo': 'desde_cero'})
        with self.assertRaises(EntradaInvalida):
            interpretar_pedido({'presupuesto': 10.5, 'uso': 'gaming', 'modo': 'desde_cero'})
        with self.assertRaises(EntradaInvalida):
            interpretar_pedido({'presupuesto': 1000, 'uso': 'xbox', 'modo': 'desde_cero'})
        with self.assertRaises(EntradaInvalida):
            interpretar_pedido({'presupuesto': 1000, 'uso': 'gaming', 'resolucion': '8k', 'modo': 'desde_cero'})
        with self.assertRaises(EntradaInvalida):
            interpretar_pedido({'presupuesto': 1000, 'uso': 'gaming', 'modo': 'magia'})

        respuesta = self.client.post(
            reverse('core:recomendar_pc'),
            data=json.dumps({'presupuesto': 'abc', 'uso': 'gaming', 'modo': 'completar', 'componentes': 'no-lista'}),
            content_type='application/json',
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()['status'], 'error')

    def _catalogo_con_gamas(self):
        self.cpu('CPU básica', 'AM4', nucleos=4, frecuencia='3.40', watts=65, precio='60000')
        alta = self.cpu('CPU alta', 'AM5', nucleos=12, frecuencia='4.60', watts=170, precio='430000')
        self.placa('Placa AM4', 'AM4', 'DDR4', precio='50000')
        self.placa('Placa AM5', 'AM5', 'DDR5', precio='140000')
        self.ram('RAM DDR4 16', 'DDR4', precio='25000', capacidad=16)
        self.ram('RAM DDR5 32', 'DDR5', precio='80000', capacidad=32)
        self.gpu('GPU 4GB', 190, consumo=110, vram=4, precio='110000')
        self.gpu('GPU 8GB sin consumo', 280, consumo=None, vram=8, precio='180000')
        con_datos = self.gpu('GPU 8GB', 270, consumo=170, vram=8, precio='300000')
        self.gabinete('Gabinete corto', 230, precio='33000')
        self.gabinete('Gabinete medio', 320, precio='70000')
        self.fuente('Fuente 450', 450, precio='35000')
        self.fuente('Fuente 650', 650, precio='65000')
        self.ssd('SSD 1TB', precio='55000')
        self.cooler('AM4')
        self.cooler('AM5')
        return alta, con_datos

    def test_gaming_1440p_no_se_queda_con_la_gpu_de_4gb(self):
        _alta, gpu = self._catalogo_con_gamas()
        resultado = generar_recomendaciones(1_200_000, 'gaming', resolucion='1440p')
        self.assertEqual(resultado['status'], 'success')
        opcion = resultado['recomendaciones'][0]
        self.assertEqual(self._id(opcion, 'tarjeta_grafica'), gpu.id)
        self.assertLessEqual(opcion['total'], 1_200_000)
        self.assertGreater(opcion['puntaje'], resultado['recomendaciones'][-1]['puntaje'])
        self.assertIn('No se estiman FPS', opcion['explicacion'])

    def test_edicion_no_recomienda_solo_la_cpu_basica(self):
        alta, gpu = self._catalogo_con_gamas()
        resultado = generar_recomendaciones(1_500_000, 'edicion', resolucion='1080p')
        self.assertEqual(resultado['status'], 'success')
        opcion = resultado['recomendaciones'][0]
        self.assertEqual(self._id(opcion, 'procesador'), alta.id)
        self.assertEqual(self._id(opcion, 'tarjeta_grafica'), gpu.id)
        nombres = {item['nombre'] for item in opcion['componentes']}
        self.assertNotIn('GPU 8GB sin consumo', nombres)

    def test_las_opciones_cambian_cpu_o_vram_y_se_ordenan_por_puntaje(self):
        self._catalogo_con_gamas()
        opciones = generar_recomendaciones(1_500_000, 'gaming', resolucion='1440p')['recomendaciones']
        self.assertGreaterEqual(len(opciones), 2)
        puntajes = [opcion['puntaje'] for opcion in opciones]
        self.assertEqual(puntajes, sorted(puntajes, reverse=True))
        perfiles = []
        for opcion in opciones:
            perfiles.append((
                self._id(opcion, 'procesador'),
                self._item(opcion, 'tarjeta_grafica')['nombre'],
            ))
        self.assertEqual(len(perfiles), len(set(perfiles)))
        self.assertEqual(opciones[0]['rol'], 'mejor')
        self.assertEqual(opciones[0]['titulo'], 'Mejor clasificada')

    def test_la_ram_no_pasa_del_objetivo_solo_para_sumar_puntaje(self):
        piezas = self.catalogo_valido()
        piezas['ram'].stock = 0
        piezas['ram'].save(update_fields=['stock'])
        kit = self.ram('Kit 64', 'DDR5', precio='160000', stock=4, modulos=2, capacidad=64)
        kit.capacidad_modulo_gb = 32
        kit.save(update_fields=['capacidad_modulo_gb'])

        gaming = generar_recomendaciones(2_000_000, 'gaming')['recomendaciones'][0]
        ram = self._item(gaming, 'memoria_ram')
        self.assertEqual(ram['id'], kit.id)
        self.assertEqual(ram['cantidad'], 1)

        edicion = generar_recomendaciones(2_000_000, 'edicion')['recomendaciones'][0]
        self.assertEqual(self._item(edicion, 'memoria_ram')['cantidad'], 1)

    def test_una_ram_fijada_por_el_usuario_no_se_reduce(self):
        piezas = self.catalogo_valido()
        piezas['ram'].stock = 0
        piezas['ram'].save(update_fields=['stock'])
        kit = self.ram('Kit 64', 'DDR5', precio='160000', stock=4, modulos=2, capacidad=64)
        kit.capacidad_modulo_gb = 32
        kit.save(update_fields=['capacidad_modulo_gb'])
        opcion = generar_recomendaciones(
            2_000_000,
            'gaming',
            memorias=[LineaRam(kit, 2)],
        )['recomendaciones'][0]
        self.assertEqual(self._item(opcion, 'memoria_ram')['cantidad'], 2)

    def test_sin_cooler_la_configuracion_no_queda_como_lista(self):
        self.catalogo_valido()
        RefrigeracionCooler.objects.all().delete()
        opcion = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones'][0]
        self.assertFalse(opcion['completamente_compatible'])
        self.assertTrue(any('Refrigeración no verificada' in texto for texto in opcion['limitaciones']))
        self.assertNotIn('refrigeracion', {item['tipo'] for item in opcion['componentes']})

    def test_gaming_con_presupuesto_incluye_un_cooler_dedicado(self):
        self.catalogo_valido()
        opcion = generar_recomendaciones(2_000_000, 'gaming')['recomendaciones'][0]
        self.assertIn('refrigeracion', {item['tipo'] for item in opcion['componentes']})
        self.assertLessEqual(opcion['total'], 2_000_000)
        self.assertFalse(opcion['completamente_compatible'])
        self.assertTrue(any('Refrigeración no verificada' in texto for texto in opcion['limitaciones']))

    def test_gaming_ajustado_reserva_el_cooler_antes_que_el_disco_grande(self):
        self.cpu('CPU media', 'AM4', nucleos=6, frecuencia='3.80', watts=95, precio='120000')
        self.placa('Placa AM4', 'AM4', 'DDR4', precio='50000')
        self.ram('RAM 32', 'DDR4', precio='45000', capacidad=32)
        self.gpu('GPU 8GB', 280, consumo=100, vram=8, precio='200000')
        self.gabinete('Gabinete 320', 320, precio='60000')
        self.fuente('Fuente 650', 650, precio='65000')
        grande = self.ssd('SSD 1TB', precio='55000')
        chico = self.ssd('SSD 500', precio='30000', capacidad=500)
        cooler = self.cooler('AM4', precio='20000')

        opcion = generar_recomendaciones(600_000, 'gaming', resolucion='1080p')['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'refrigeracion'), cooler.id)
        self.assertEqual(self._id(opcion, 'almacenamiento_ssd'), chico.id)
        self.assertNotEqual(self._id(opcion, 'almacenamiento_ssd'), grande.id)
        self.assertLessEqual(opcion['total'], 600_000)
        self.assertIn('refrigeracion', {item['tipo'] for item in opcion['componentes']})

    def test_edicion_descarta_el_cooler_que_no_cubre_la_referencia_termica(self):
        self.cpu('CPU exigente', 'AM5', nucleos=12, frecuencia='4.60', watts=170, precio='200000', incluye=False, termica=120)
        self.placa('Placa AM5', 'AM5', 'DDR5', precio='80000')
        self.ram('RAM 64', 'DDR5', precio='80000', capacidad=64)
        self.gpu('GPU 8GB', 280, vram=8, precio='150000')
        self.gabinete('Gabinete 160', 350, altura_max=160)
        self.fuente('Fuente 750', 750, precio='50000')
        self.ssd()
        self.cooler('AM5', precio='10000', altura=140, disipacion=80, nombre='Cooler corto')
        capaz = self.cooler('AM5', precio='25000', altura=150, disipacion=150, nombre='Cooler capaz')

        opcion = generar_recomendaciones(2_000_000, 'edicion')['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'refrigeracion'), capaz.id)
        self.assertEqual(self._id(opcion, 'procesador'), Procesador.objects.get(nombre='CPU exigente').id)

    def test_uso_general_conserva_el_cooler_de_fabrica_confirmado(self):
        self.cpu('CPU con caja', 'AM5', incluye=True)
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        self.ssd()
        self.cooler('AM5')
        opcion = generar_recomendaciones(2_000_000, 'general')['recomendaciones'][0]

        self.assertNotIn('refrigeracion', {item['tipo'] for item in opcion['componentes']})
        self.assertTrue(any('cooler de fábrica' in texto for texto in opcion['limitaciones']))
        self.assertFalse(opcion['completamente_compatible'])

    def test_sin_cooler_de_fabrica_agrega_uno_dedicado(self):
        self.cpu('CPU pelada', 'AM5', incluye=False)
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        self.ssd()
        cooler = self.cooler('AM5')
        opcion = generar_recomendaciones(2_000_000, 'general')['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'refrigeracion'), cooler.id)

    def test_cooler_de_fabrica_desconocido_no_se_da_por_verificado(self):
        self.catalogo_valido()
        Procesador.objects.update(incluye_cooler=None)
        opcion = generar_recomendaciones(2_000_000, 'general')['recomendaciones'][0]

        self.assertNotIn('refrigeracion', {item['tipo'] for item in opcion['componentes']})
        self.assertTrue(any('no registra si incluye cooler' in texto for texto in opcion['limitaciones']))

    def test_un_cooler_fijado_con_socket_incompatible_no_se_completa(self):
        piezas = self.catalogo_valido()
        ajeno = self.cooler('LGA1700', nombre='Cooler LGA1700')
        resultado = generar_recomendaciones(
            2_000_000,
            'gaming',
            seleccion={'procesador': piezas['cpu'], 'refrigeracion': ajeno},
        )

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertIn('AM5', resultado['mensaje'])
        self.assertIn('cooler', resultado['mensaje'])

    def test_cooler_demasiado_alto_no_se_elige(self):
        self.cpu('CPU AM5', 'AM5', termica=100)
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete bajo', 350, altura_max=160)
        self.fuente('Fuente 650', 650)
        self.ssd()
        self.cooler('AM5', precio='10000', altura=180, disipacion=200, nombre='Cooler alto')
        bajo = self.cooler('AM5', precio='20000', altura=140, disipacion=200, nombre='Cooler bajo')

        opcion = generar_recomendaciones(2_000_000, 'gaming')['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'refrigeracion'), bajo.id)
        self.assertFalse(any('Refrigeración no verificada' in texto for texto in opcion['limitaciones']))

    def test_cooler_sin_stock_deja_la_refrigeracion_sin_verificar(self):
        self.catalogo_valido()
        RefrigeracionCooler.objects.update(stock=0)
        opcion = generar_recomendaciones(2_000_000, 'gaming')['recomendaciones'][0]

        self.assertNotIn('refrigeracion', {item['tipo'] for item in opcion['componentes']})
        self.assertTrue(any('Refrigeración no verificada' in texto for texto in opcion['limitaciones']))
        self.assertFalse(opcion['completamente_compatible'])

    def test_conserva_el_cooler_que_el_usuario_ya_eligio(self):
        piezas = self.catalogo_valido()
        fijado = self.cooler('AM5', precio='40000', nombre='Cooler elegido')
        opcion = generar_recomendaciones(
            2_000_000,
            'gaming',
            seleccion={'refrigeracion': fijado},
        )['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'refrigeracion'), fijado.id)
        self.assertNotEqual(self._id(opcion, 'refrigeracion'), piezas['cooler'].id)

    def test_sin_dinero_para_cooler_no_se_declara_listo(self):
        self.cpu('CPU AM5', 'AM5', precio='200000', incluye=False)
        self.placa('Placa AM5', 'AM5', 'DDR5', precio='80000')
        self.ram('RAM DDR5', 'DDR5', precio='40000')
        self.gpu('GPU 280', 280, precio='150000')
        self.gabinete('Gabinete 350', 350, precio='40000')
        self.fuente('Fuente 650', 650, precio='50000')
        self.ssd(precio='30000')
        self.cooler('AM5', precio='300000')

        opcion = generar_recomendaciones(600_000, 'gaming')['recomendaciones'][0]

        self.assertNotIn('refrigeracion', {item['tipo'] for item in opcion['componentes']})
        self.assertLessEqual(opcion['total'], 600_000)
        self.assertTrue(any('no incluye cooler de fábrica' in texto for texto in opcion['limitaciones']))
        self.assertFalse(opcion['completamente_compatible'])

    def test_la_recomendacion_con_cooler_se_puede_cargar_en_el_armador(self):
        self.catalogo_valido()
        respuesta = self.client.post(
            reverse('core:recomendar_pc'),
            data=json.dumps({
                'presupuesto': 2_000_000,
                'uso': 'gaming',
                'resolucion': '1080p',
                'modo': 'desde_cero',
            }),
            content_type='application/json',
        )
        opcion = respuesta.json()['recomendaciones'][0]
        cooler = self._item(opcion, 'refrigeracion')
        evaluacion = self.client.post(
            reverse('core:evaluar_armado'),
            data=json.dumps({'componentes': [
                {'tipo': item['tipo'], 'id': item['id'], 'cantidad': item['cantidad']}
                for item in opcion['componentes']
            ]}),
            content_type='application/json',
        )

        self.assertEqual(evaluacion.status_code, 200)
        self.assertEqual(evaluacion.json()['piezas']['refrigeracion_cooler']['estado'], 'compatible')
        self.assertEqual(cooler['id'], self._id(opcion, 'refrigeracion'))
        from core.models import ItemCarrito
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def _item(self, opcion, tipo):
        return next(item for item in opcion['componentes'] if item['tipo'] == tipo)

    def _id(self, opcion, tipo):
        return self._item(opcion, tipo)['id']
