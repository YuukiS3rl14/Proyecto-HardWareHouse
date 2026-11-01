import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.compatibilidad import MENSAJE_POTENCIA_INTEGRADA, LineaRam, validar_armado
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
from core.recomendador_pc import EntradaInvalida, Preferencias, generar_recomendaciones, interpretar_pedido


class RecomendadorPcTests(TestCase):
    def setUp(self):
        self.proveedor = Proveedor.objects.create(nombre='Marca Recomendador')

    def cpu(self, nombre, socket, nucleos=6, frecuencia='3.50', watts=65, precio='100000', stock=4, incluye=None, termica=None, graficos=None):
        return Procesador.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal(precio), stock=stock,
            socket=socket, nucleos=nucleos, frecuencia_base=Decimal(frecuencia),
            potencia_referencia_watts=watts, incluye_cooler=incluye,
            potencia_termica_referencia_watts=termica, graficos_integrados=graficos,
        )

    def placa(self, nombre, socket, ddr, precio='80000', stock=4, formato_ram='DIMM', ranuras=4, capacidad=128, salidas=None):
        return PlacaMadre.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal(precio), stock=stock,
            socket_cpu=socket, chipset='B650' if socket == 'AM5' else 'B550', formato='ATX',
            ranuras_ram=ranuras, tipo_ram_soportado=ddr, formato_ram_soportado=formato_ram,
            capacidad_maxima_ram_gb=capacidad, tiene_salidas_video=salidas,
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
            'cooler': self.cooler('AM5', altura=150),
            'gpu': self.gpu('GPU 280', 280),
            'gabinete': self.gabinete('Gabinete 350', 350, altura_max=160),
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
        self.assertTrue(any('ranuras M.2' in texto for texto in opcion['limitaciones']))
        self.assertFalse(any('puertos SATA' in texto for texto in opcion['limitaciones']))
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
        self.assertTrue(any('ranuras M.2' in texto for texto in opcion['limitaciones']))
        self.assertFalse(any('puertos SATA' in texto for texto in opcion['limitaciones']))

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
        self.assertTrue(any('Falta la interfaz' in texto for texto in opcion['limitaciones']))
        self.assertFalse(any('ranuras M.2' in texto or 'puertos SATA' in texto for texto in opcion['limitaciones']))

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
        self.gabinete('Gabinete 320', 320, precio='60000', altura_max=160)
        self.fuente('Fuente 650', 650, precio='65000')
        grande = self.ssd('SSD 1TB', precio='55000')
        chico = self.ssd('SSD 500', precio='30000', capacidad=500)
        cooler = self.cooler('AM4', precio='20000', altura=150)

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
        self.gabinete('Gabinete 350', 350, altura_max=160)
        self.fuente('Fuente 650', 650)
        self.ssd()
        cooler = self.cooler('AM5', altura=150)
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
        fijado = self.cooler('AM5', precio='40000', altura=150, nombre='Cooler elegido')
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

    def test_prefiere_la_placa_que_permite_comprobar_el_disco(self):
        self.cpu('CPU AM5', 'AM5', watts=65, termica=80, incluye=False)
        self.placa('Placa sin conteos', 'AM5', 'DDR5', precio='70000')
        con_datos = self.placa('Placa con conteos', 'AM5', 'DDR5', precio='90000')
        con_datos.ranuras_m2_solo_nvme = 1
        con_datos.ranuras_m2_solo_sata = 0
        con_datos.ranuras_m2_nvme_o_sata = 0
        con_datos.puertos_sata = 4
        con_datos.save()
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350, altura_max=160)
        self.fuente('Fuente 650', 650)
        self.ssd()
        cooler = self.cooler('AM5', altura=150, disipacion=120)

        opcion = generar_recomendaciones(2_000_000, 'gaming')['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'placa_madre'), con_datos.id)
        self.assertEqual(self._id(opcion, 'refrigeracion'), cooler.id)
        self.assertIn('almacenamiento_ssd', {item['tipo'] for item in opcion['componentes']})
        self.assertTrue(opcion['completamente_compatible'])
        self.assertFalse(any('SATA' in texto or 'No se incluyó almacenamiento' in texto for texto in opcion['limitaciones']))
        self.assertIn('6 núcleos', self._item(opcion, 'procesador')['motivo'])
        self.assertIn('No suma puntaje', self._item(opcion, 'placa_madre')['motivo'])
        self.assertIn('GB de VRAM de catálogo', self._item(opcion, 'tarjeta_grafica')['motivo'])
        self.assertIn('SSD', self._item(opcion, 'almacenamiento_ssd')['motivo'])
        self.assertLessEqual(opcion['total'], 2_000_000)

    def test_si_el_nvme_no_entra_en_la_placa_usa_el_hdd(self):
        self.cpu('CPU AM5', 'AM5')
        placa = self.placa('Placa solo SATA', 'AM5', 'DDR5')
        placa.ranuras_m2_solo_nvme = 0
        placa.ranuras_m2_solo_sata = 0
        placa.ranuras_m2_nvme_o_sata = 0
        placa.puertos_sata = 2
        placa.save()
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        self.ssd('SSD NVMe')
        hdd = AlmacenamientoHDD.objects.create(
            proveedor=self.proveedor, nombre='HDD SATA', precio=Decimal('22000'), stock=2,
            capacidad_gb=1000, velocidad_rpm=7200, cache_mb=64, interfaz='SATA III', formato='3.5"',
        )

        opcion = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones'][0]
        tipos = {item['tipo'] for item in opcion['componentes']}

        self.assertIn('almacenamiento_hdd', tipos)
        self.assertNotIn('almacenamiento_ssd', tipos)
        self.assertEqual(self._id(opcion, 'almacenamiento_hdd'), hdd.id)
        self.assertFalse(any('No se incluyó almacenamiento' in texto for texto in opcion['limitaciones']))
        self.assertFalse(any('ranuras M.2' in texto for texto in opcion['limitaciones']))

    def test_ssd_nvme_sin_ranuras_registradas_explica_solo_esa_causa(self):
        self.cpu('CPU AM5', 'AM5', watts=65)
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5', stock=4, capacidad=16)
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        ssd = self.ssd('SSD NVMe')
        opcion = generar_recomendaciones(
            2_000_000, 'general',
            preferencias=Preferencias(
                ram_gb=32, ram_modo='obligatorio',
                disco_tipo='ssd', disco_tipo_modo='obligatorio',
                socket='AM5', socket_modo='obligatorio',
            ),
        )['recomendaciones'][0]
        aviso = (
            'No fue posible verificar la compatibilidad del SSD con la placa madre '
            'porque el catálogo no contiene información suficiente sobre sus ranuras M.2.'
        )

        self.assertEqual(self._id(opcion, 'almacenamiento_ssd'), ssd.id)
        self.assertGreaterEqual(
            sum(item['cantidad'] * 16 for item in opcion['componentes'] if item['tipo'] == 'memoria_ram'),
            32,
        )
        self.assertIn('SSD: cumple el tipo de almacenamiento solicitado.', opcion['requisitos_cumplidos'])
        self.assertIn('Socket AM5: cumple la plataforma seleccionada.', opcion['requisitos_cumplidos'])
        self.assertLessEqual(opcion['total'], 2_000_000)
        self.assertEqual(opcion['estado_reglas'], 'compatible')
        self.assertFalse(opcion['completamente_compatible'])
        self.assertIn(aviso, opcion['limitaciones'])
        self.assertEqual(sum('ranuras M.2' in texto for texto in opcion['limitaciones']), 1)
        self.assertFalse(any('puertos SATA' in texto for texto in opcion['limitaciones']))
        self.assertNotIn(aviso, self._item(opcion, 'almacenamiento_ssd')['motivo'])
        evaluacion = validar_armado(
            procesador=Procesador.objects.get(pk=self._id(opcion, 'procesador')),
            placa_madre=PlacaMadre.objects.get(pk=self._id(opcion, 'placa_madre')),
            almacenamientos=[{'tipo': 'almacenamiento_ssd', 'producto': ssd, 'cantidad': 1}],
        )
        self.assertEqual(evaluacion.almacenamiento.estado, 'no_evaluada')
        self.assertNotIn(evaluacion.estado, ('incompatible', 'datos_insuficientes'))

    def test_ssd_sata_sin_puertos_registrados_no_menciona_ranuras_m2(self):
        self.cpu('CPU AM5', 'AM5', watts=65)
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        ssd = AlmacenamientoSSD.objects.create(
            proveedor=self.proveedor, nombre='SSD SATA', precio=Decimal('25000'), stock=4,
            capacidad_gb=500, interfaz='SATA III', formato='2.5"',
        )
        opcion = generar_recomendaciones(2_000_000, 'general')['recomendaciones'][0]
        aviso = (
            'No fue posible verificar la compatibilidad del SSD con la placa madre '
            'porque el catálogo no contiene información suficiente sobre sus puertos SATA.'
        )

        self.assertEqual(self._id(opcion, 'almacenamiento_ssd'), ssd.id)
        self.assertIn(aviso, opcion['limitaciones'])
        self.assertFalse(any('ranuras M.2' in texto for texto in opcion['limitaciones']))
        self.assertNotIn(aviso, self._item(opcion, 'almacenamiento_ssd')['motivo'])
        self.assertLessEqual(opcion['total'], 2_000_000)

    def test_ssd_nvme_con_ranuras_suficientes_sigue_compatible(self):
        self.cpu('CPU AM5', 'AM5', watts=65, termica=80, incluye=False)
        placa = self.placa('Placa AM5', 'AM5', 'DDR5')
        placa.ranuras_m2_solo_nvme = 1
        placa.ranuras_m2_solo_sata = 0
        placa.ranuras_m2_nvme_o_sata = 0
        placa.puertos_sata = 4
        placa.save()
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350, altura_max=160)
        self.fuente('Fuente 650', 650)
        self.ssd()
        self.cooler('AM5', altura=150, disipacion=120)
        opcion = generar_recomendaciones(2_000_000, 'general')['recomendaciones'][0]

        self.assertIn('almacenamiento_ssd', {item['tipo'] for item in opcion['componentes']})
        self.assertTrue(opcion['completamente_compatible'])
        self.assertFalse(any('No fue posible verificar la compatibilidad del SSD' in texto for texto in opcion['limitaciones']))
        self.assertIn('Cabe', self._item(opcion, 'almacenamiento_ssd')['motivo'])

    def test_ssd_nvme_que_no_cabe_sigue_rechazado(self):
        self.cpu('CPU AM5', 'AM5')
        placa = self.placa('Placa sin NVMe', 'AM5', 'DDR5')
        placa.ranuras_m2_solo_nvme = 0
        placa.ranuras_m2_solo_sata = 0
        placa.ranuras_m2_nvme_o_sata = 0
        placa.puertos_sata = 4
        placa.save()
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        self.ssd('SSD NVMe')
        opcion = generar_recomendaciones(2_000_000, 'general')['recomendaciones'][0]

        self.assertNotIn('almacenamiento_ssd', {item['tipo'] for item in opcion['componentes']})
        self.assertTrue(opcion['configuracion_incompleta'])
        self.assertFalse(any('ranuras M.2' in texto for texto in opcion['limitaciones']))
        self.assertLessEqual(opcion['total'], 2_000_000)

    def test_sin_disco_en_catalogo_no_se_declara_completo(self):
        self.cpu('CPU AM5', 'AM5')
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)

        opcion = generar_recomendaciones(2_000_000, 'general')['recomendaciones'][0]

        self.assertNotIn('almacenamiento_ssd', {item['tipo'] for item in opcion['componentes']})
        self.assertNotIn('almacenamiento_hdd', {item['tipo'] for item in opcion['componentes']})
        self.assertTrue(opcion['configuracion_incompleta'])
        self.assertEqual(opcion['titulo'], 'Configuración incompleta')
        self.assertEqual(opcion['compatibilidad'], 'Configuración incompleta')
        self.assertEqual(opcion['pieza_faltante'], 'Almacenamiento')
        self.assertIn('presupuesto', opcion['motivo_incompleto'])
        self.assertFalse(opcion['completamente_compatible'])
        self.assertNotIn('PC completo', opcion['titulo'])
        self.assertTrue(any('No se encontró un componente compatible' in texto for texto in opcion['limitaciones']))
        self.assertTrue(any('Refrigeración no verificada' in texto for texto in opcion['limitaciones']))

    def test_un_cooler_comprobable_reemplaza_al_de_fabrica_sin_medidas(self):
        self.cpu('CPU con caja', 'AM5', incluye=True, termica=65)
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350, altura_max=160)
        self.fuente('Fuente 650', 650)
        self.ssd()
        cooler = self.cooler('AM5', altura=150, disipacion=90)

        opcion = generar_recomendaciones(2_000_000, 'general')['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'refrigeracion'), cooler.id)
        self.assertFalse(any('cooler de fábrica' in texto for texto in opcion['limitaciones']))
        self.assertFalse(any('Refrigeración no verificada' in texto for texto in opcion['limitaciones']))
        self.assertLessEqual(opcion['total'], 2_000_000)

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

    def _oficina(self, graficos=True, salidas=True, watts=65, fuente_w=450, con_gpu=True):
        cpu = self.cpu('CPU oficina', 'AM5', watts=watts, graficos=graficos)
        placa = self.placa('Placa oficina', 'AM5', 'DDR5', salidas=salidas)
        self.ram('RAM DDR5', 'DDR5')
        self.gabinete('Gabinete 350', 350)
        self.fuente(f'Fuente {fuente_w}', fuente_w)
        self.ssd()
        gpu = self.gpu('GPU oficina', 280, precio='120000') if con_gpu else None
        return cpu, placa, gpu

    def _tiene_gpu(self, opcion):
        return any(item['tipo'] == 'tarjeta_grafica' for item in opcion['componentes'])

    def _tiene_disco(self, opcion):
        return any(item['tipo'] in ('almacenamiento_ssd', 'almacenamiento_hdd') for item in opcion['componentes'])

    def test_trabajo_sin_gpu_en_catalogo_usa_el_video_confirmado(self):
        self._oficina(con_gpu=False, fuente_w=450)
        resultado = generar_recomendaciones(2_000_000, 'trabajo')

        self.assertEqual(resultado['status'], 'success')
        opcion = resultado['recomendaciones'][0]
        self.assertTrue(opcion['usa_graficos_integrados'])
        self.assertFalse(self._tiene_gpu(opcion))
        self.assertFalse(opcion['completamente_compatible'])
        self.assertIn('gráficos integrados', opcion['explicacion'])
        self.assertIn(MENSAJE_POTENCIA_INTEGRADA, opcion['limitaciones'])
        self.assertLessEqual(opcion['total'], 2_000_000)
        self.assertEqual(
            opcion['total'],
            sum(item['subtotal'] for item in opcion['componentes']),
        )

    def test_trabajo_conserva_la_gpu_cuando_suma_mas_puntaje(self):
        self._oficina(con_gpu=True)
        opciones = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones']

        self.assertTrue(self._tiene_gpu(opciones[0]))
        self.assertFalse(opciones[0]['usa_graficos_integrados'])
        sin_gpu = [opcion for opcion in opciones if opcion['usa_graficos_integrados']]
        self.assertTrue(sin_gpu)
        self.assertGreaterEqual(opciones[0]['puntaje'], sin_gpu[0]['puntaje'])

    def test_general_tambien_admite_el_armado_sin_gpu(self):
        self._oficina(con_gpu=False)
        opcion = generar_recomendaciones(2_000_000, 'general')['recomendaciones'][0]
        self.assertTrue(opcion['usa_graficos_integrados'])
        self.assertFalse(self._tiene_gpu(opcion))

    def test_cpu_sin_graficos_sigue_exigiendo_gpu(self):
        self._oficina(graficos=False, salidas=True)
        opciones = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones']
        self.assertTrue(all(self._tiene_gpu(opcion) for opcion in opciones))
        self.assertTrue(all(not opcion['usa_graficos_integrados'] for opcion in opciones))

    def test_placa_sin_salida_de_video_sigue_exigiendo_gpu(self):
        self._oficina(graficos=True, salidas=False)
        opciones = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones']
        self.assertTrue(all(self._tiene_gpu(opcion) for opcion in opciones))

    def test_un_campo_desconocido_sigue_exigiendo_gpu(self):
        self._oficina(graficos=True, salidas=None)
        con_cpu = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones']
        self.assertTrue(all(self._tiene_gpu(opcion) for opcion in con_cpu))

        Procesador.objects.update(graficos_integrados=None)
        PlacaMadre.objects.update(tiene_salidas_video=True)
        con_placa = generar_recomendaciones(2_000_000, 'general')['recomendaciones']
        self.assertTrue(all(self._tiene_gpu(opcion) for opcion in con_placa))

    def test_el_nombre_no_demuestra_graficos_integrados(self):
        self.cpu('Ryzen 5 5600G', 'AM5', graficos=None)
        self.placa('Placa B550 oficina', 'AM5', 'DDR5', salidas=None)
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        self.ssd()

        opcion = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones'][0]

        self.assertTrue(self._tiene_gpu(opcion))
        self.assertFalse(opcion['usa_graficos_integrados'])
        self.assertIsNone(Procesador.objects.get(nombre='Ryzen 5 5600G').graficos_integrados)
        self.assertIsNone(PlacaMadre.objects.get(nombre='Placa B550 oficina').tiene_salidas_video)

    def test_gaming_y_edicion_siguen_exigiendo_gpu(self):
        self._oficina(graficos=True, salidas=True, con_gpu=False)
        for uso in ('gaming', 'edicion'):
            resultado = generar_recomendaciones(2_000_000, uso)
            self.assertEqual(resultado['status'], 'sin_recomendacion', uso)

        self.gpu('GPU obligatoria', 280)
        for uso in ('gaming', 'edicion'):
            opcion = generar_recomendaciones(2_000_000, uso)['recomendaciones'][0]
            self.assertTrue(self._tiene_gpu(opcion), uso)
            self.assertFalse(opcion['usa_graficos_integrados'], uso)

    def test_la_potencia_sin_gpu_no_cuenta_una_tarjeta_dedicada(self):
        cpu = self.cpu('CPU 65', 'AM5', watts=65, graficos=True)
        placa = self.placa('Placa video', 'AM5', 'DDR5', salidas=True)
        ram = self.ram('RAM potencia', 'DDR5')
        gabinete = self.gabinete('Gabinete potencia', 350)
        suficiente = self.fuente('Fuente 300', 300)
        corta = self.fuente('Fuente 250', 250)

        cumple = validar_armado(
            procesador=cpu, placa_madre=placa, memoria_ram=ram,
            gabinete=gabinete, fuente_de_poder=suficiente,
        )
        self.assertEqual(cumple.estado, 'compatible')
        self.assertIn(MENSAJE_POTENCIA_INTEGRADA, cumple.advertencias)
        self.assertNotIn('consumo de referencia de la GPU', ' '.join(cumple.advertencias))

        no_alcanza = validar_armado(
            procesador=cpu, placa_madre=placa, memoria_ram=ram,
            gabinete=gabinete, fuente_de_poder=corta,
        )
        self.assertEqual(no_alcanza.estado, 'incompatible')
        self.assertIn('258 W', ' '.join(no_alcanza.motivos_de_rechazo))

        antigua = validar_armado(
            procesador=self.cpu('CPU antigua', 'AM4', watts=65),
            placa_madre=self.placa('Placa antigua', 'AM4', 'DDR4'),
            memoria_ram=self.ram('RAM antigua', 'DDR4'),
            gabinete=self.gabinete('Gabinete antiguo', 350),
            fuente_de_poder=suficiente,
        )
        self.assertEqual(antigua.estado, 'incompleto')
        self.assertIn('tarjeta gráfica', ' '.join(hallazgo.mensaje for hallazgo in antigua.hallazgos))

    def test_el_armado_sin_gpu_se_puede_evaluar_en_el_armador(self):
        self._oficina(con_gpu=True)
        respuesta = self.client.post(
            reverse('core:recomendar_pc'),
            data=json.dumps({
                'presupuesto': 2_000_000,
                'uso': 'trabajo',
                'modo': 'desde_cero',
            }),
            content_type='application/json',
        )
        opciones = respuesta.json()['recomendaciones']
        opcion = next(item for item in opciones if item['usa_graficos_integrados'])
        evaluacion = self.client.post(
            reverse('core:evaluar_armado'),
            data=json.dumps({'componentes': [
                {'tipo': item['tipo'], 'id': item['id'], 'cantidad': item['cantidad']}
                for item in opcion['componentes']
            ]}),
            content_type='application/json',
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(evaluacion.status_code, 200)
        self.assertEqual(evaluacion.json()['estado'], 'compatible')
        self.assertIn(MENSAJE_POTENCIA_INTEGRADA, evaluacion.json()['advertencias'])
        self.assertNotIn('tarjeta_grafica', {item['tipo'] for item in opcion['componentes']})
        self.assertEqual(opcion['total'], sum(item['subtotal'] for item in opcion['componentes']))
        from core.models import ItemCarrito
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_un_producto_antiguo_sin_el_dato_conserva_la_gpu(self):
        self.cpu('CPU sin campo', 'AM5')
        self.placa('Placa sin campo', 'AM5', 'DDR5')
        self.ram('RAM DDR5', 'DDR5')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        self.ssd()

        self.assertIsNone(Procesador.objects.get().graficos_integrados)
        self.assertIsNone(PlacaMadre.objects.get().tiene_salidas_video)
        opciones = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones']
        self.assertTrue(all(self._tiene_gpu(opcion) for opcion in opciones))
        self.assertTrue(all(self._tiene_disco(opcion) for opcion in opciones))
        self.assertTrue(all(not opcion['configuracion_incompleta'] for opcion in opciones))

    def test_un_armado_completo_con_gpu_conserva_precios_y_no_es_parcial(self):
        self.catalogo_valido()
        opcion = generar_recomendaciones(2_000_000, 'gaming')['recomendaciones'][0]

        self.assertTrue(self._tiene_gpu(opcion))
        self.assertTrue(self._tiene_disco(opcion))
        self.assertFalse(opcion['configuracion_incompleta'])
        self.assertEqual(opcion['pieza_faltante'], '')
        self.assertEqual(opcion['titulo'], 'Mejor clasificada')
        self.assertEqual(opcion['total'], sum(item['subtotal'] for item in opcion['componentes']))
        self.assertGreaterEqual(self._item(opcion, 'memoria_ram')['cantidad'], 1)
        self.assertEqual(
            self._item(opcion, 'almacenamiento_ssd')['subtotal'],
            int(Decimal(self._item(opcion, 'almacenamiento_ssd')['precio']) * self._item(opcion, 'almacenamiento_ssd')['cantidad']),
        )

    def test_un_armado_completo_con_graficos_integrados_incluye_disco(self):
        self._oficina(con_gpu=False)
        opcion = generar_recomendaciones(2_000_000, 'trabajo')['recomendaciones'][0]

        self.assertTrue(opcion['usa_graficos_integrados'])
        self.assertFalse(self._tiene_gpu(opcion))
        self.assertTrue(self._tiene_disco(opcion))
        self.assertFalse(opcion['configuracion_incompleta'])
        self.assertIn(MENSAJE_POTENCIA_INTEGRADA, opcion['limitaciones'])
        self.assertFalse(opcion['completamente_compatible'])
        self.assertEqual(opcion['total'], sum(item['subtotal'] for item in opcion['componentes']))

    def test_prioriza_la_configuracion_completa_aunque_la_parcial_puntue_mas(self):
        cara = self.cpu('CPU cara', 'AM5', nucleos=16, frecuencia='4.50', precio='420000')
        barata = self.cpu('CPU con disco', 'AM5', nucleos=4, frecuencia='3.20', precio='90000')
        self.placa('Placa AM5', 'AM5', 'DDR5', precio='80000')
        self.ram('RAM DDR5', 'DDR5', precio='20000')
        self.gpu('GPU 280', 280, precio='120000')
        self.gabinete('Gabinete 350', 350, precio='40000')
        self.fuente('Fuente 650', 650, precio='50000')
        disco = self.ssd(precio='80000')

        opciones = generar_recomendaciones(760_000, 'gaming')['recomendaciones']

        self.assertTrue(opciones)
        self.assertTrue(all(self._tiene_disco(opcion) for opcion in opciones))
        self.assertTrue(all(not opcion['configuracion_incompleta'] for opcion in opciones))
        self.assertNotIn(cara.id, [self._id(opcion, 'procesador') for opcion in opciones])
        self.assertEqual(self._id(opciones[0], 'procesador'), barata.id)
        self.assertEqual(self._id(opciones[0], 'almacenamiento_ssd'), disco.id)
        self.assertEqual(opciones[0]['total'], sum(item['subtotal'] for item in opciones[0]['componentes']))
        self.assertLessEqual(opciones[0]['total'], 760_000)

    def test_sin_disco_viable_se_informa_como_incompleta_y_se_puede_evaluar(self):
        self.cpu('CPU cara', 'AM5', nucleos=16, frecuencia='4.50', precio='420000')
        self.placa('Placa AM5', 'AM5', 'DDR5', precio='80000')
        self.ram('RAM DDR5', 'DDR5', precio='20000')
        self.gpu('GPU 280', 280, precio='120000')
        self.gabinete('Gabinete 350', 350, precio='40000')
        self.fuente('Fuente 650', 650, precio='50000')
        self.ssd(precio='80000')

        respuesta = self.client.post(
            reverse('core:recomendar_pc'),
            data=json.dumps({'presupuesto': 760_000, 'uso': 'gaming', 'modo': 'desde_cero'}),
            content_type='application/json',
        )
        opciones = respuesta.json()['recomendaciones']
        opcion = opciones[0]
        evaluacion = self.client.post(
            reverse('core:evaluar_armado'),
            data=json.dumps({'componentes': [
                {'tipo': item['tipo'], 'id': item['id'], 'cantidad': item['cantidad']}
                for item in opcion['componentes']
            ]}),
            content_type='application/json',
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(opcion['configuracion_incompleta'])
        self.assertEqual(opcion['compatibilidad'], 'Configuración incompleta')
        self.assertEqual(opcion['pieza_faltante'], 'Almacenamiento')
        self.assertNotEqual(opcion['titulo'], 'Mejor clasificada')
        self.assertFalse(opcion['completamente_compatible'])
        self.assertFalse(self._tiene_disco(opcion))
        self.assertTrue(any('Refrigeración no verificada' in texto for texto in opcion['limitaciones']))
        self.assertEqual(evaluacion.status_code, 200)
        self.assertEqual(opcion['total'], sum(item['subtotal'] for item in opcion['componentes']))
        self.assertLessEqual(opcion['total'], 760_000)
        from core.models import ItemCarrito
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_la_advertencia_de_graficos_llega_una_vez_y_la_critica_se_conserva(self):
        cpu = self.cpu('CPU 65', 'AM5', watts=65, graficos=True)
        placa = self.placa('Placa video', 'AM5', 'DDR5', salidas=True)
        ram = self.ram('RAM DDR5', 'DDR5')
        gabinete = self.gabinete('Gabinete 350', 350)
        fuente = self.fuente('Fuente 300', 300)
        respuesta = self.client.post(
            reverse('core:evaluar_armado'),
            data=json.dumps({'componentes': [
                {'tipo': 'procesador', 'id': cpu.id, 'cantidad': 1},
                {'tipo': 'placa_madre', 'id': placa.id, 'cantidad': 1},
                {'tipo': 'memoria_ram', 'id': ram.id, 'cantidad': 1},
                {'tipo': 'gabinete', 'id': gabinete.id, 'cantidad': 1},
                {'tipo': 'fuente_de_poder', 'id': fuente.id, 'cantidad': 1},
            ]}),
            content_type='application/json',
        )
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo['advertencias'].count(MENSAJE_POTENCIA_INTEGRADA), 1)
        self.assertNotIn(MENSAJE_POTENCIA_INTEGRADA, cuerpo['piezas']['procesador']['advertencias'])
        self.assertNotIn(MENSAJE_POTENCIA_INTEGRADA, cuerpo['piezas']['fuente_de_poder']['advertencias'])

        corta = self.fuente('Fuente 250', 250)
        critica = validar_armado(
            procesador=cpu, placa_madre=placa, memoria_ram=ram,
            gabinete=gabinete, fuente_de_poder=corta,
        )
        self.assertEqual(critica.estado, 'incompatible')
        self.assertTrue(any('Potencia insuficiente' in texto for texto in critica.motivos_de_rechazo))

    def test_ram_minima_obligatoria_puede_sumar_dos_modulos(self):
        self.catalogo_valido()
        resultado = generar_recomendaciones(
            2_000_000, 'gaming',
            preferencias=Preferencias(ram_gb=32, ram_modo='obligatorio'),
        )

        self.assertEqual(resultado['status'], 'success')
        for opcion in resultado['recomendaciones']:
            ram = self._item(opcion, 'memoria_ram')
            self.assertEqual(ram['cantidad'], 2)
            self.assertIn('32 GB de RAM: cumple el mínimo solicitado.', opcion['requisitos_cumplidos'])

    def test_capacidad_minima_elige_el_ssd_que_la_alcanza(self):
        piezas = self.catalogo_valido()
        piezas['ssd'].capacidad_gb = 500
        piezas['ssd'].save(update_fields=['capacidad_gb'])
        grande = self.ssd('SSD 1TB pedido', precio='30000', capacidad=1000)
        opcion = generar_recomendaciones(
            2_000_000, 'gaming',
            preferencias=Preferencias(disco_gb=1000, disco_gb_modo='obligatorio'),
        )['recomendaciones'][0]

        self.assertEqual(self._id(opcion, 'almacenamiento_ssd'), grande.id)
        self.assertIn('SSD de 1000 GB: cumple la capacidad solicitada.', opcion['requisitos_cumplidos'])

    def test_ssd_obligatorio_no_cae_en_hdd(self):
        piezas = self.catalogo_valido()
        piezas['ssd'].stock = 0
        piezas['ssd'].save(update_fields=['stock'])
        AlmacenamientoHDD.objects.create(
            proveedor=self.proveedor, nombre='HDD 2TB', precio=Decimal('20000'), stock=4,
            capacidad_gb=2000, velocidad_rpm=7200, cache_mb=256,
        )
        resultado = generar_recomendaciones(
            2_000_000, 'gaming',
            preferencias=Preferencias(disco_tipo='ssd', disco_tipo_modo='obligatorio'),
        )

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertEqual(resultado['recomendaciones'], [])
        self.assertIn('SSD', resultado['mensaje'])

    def test_socket_obligatorio_no_acepta_un_cpu_de_otra_plataforma(self):
        self.cpu('Ryzen 5 5600', 'AM4')
        self.placa('Placa AM4', 'AM4', 'DDR4')
        self.ram('RAM DDR4', 'DDR4')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        self.ssd()
        pedido = Preferencias(socket='AM5', socket_modo='obligatorio')
        rechazo = generar_recomendaciones(2_000_000, 'gaming', preferencias=pedido)

        self.assertEqual(rechazo['status'], 'sin_recomendacion')
        self.assertIn('AM5', rechazo['mensaje'])
        self.assertIn('stock', rechazo['mensaje'].lower())

        self.catalogo_valido()
        opciones = generar_recomendaciones(2_000_000, 'gaming', preferencias=pedido)['recomendaciones']
        self.assertTrue(opciones)
        self.assertTrue(all(
            Procesador.objects.get(pk=self._id(opcion, 'procesador')).socket == 'AM5'
            for opcion in opciones
        ))
        self.assertIn('Socket AM5: cumple la plataforma seleccionada.', opciones[0]['requisitos_cumplidos'])

    def test_preferencia_opcional_imposible_se_explica_sin_fallar(self):
        self.catalogo_valido()
        resultado = generar_recomendaciones(
            2_000_000, 'gaming',
            preferencias=Preferencias(socket='AM4', socket_modo='preferencia'),
        )

        self.assertEqual(resultado['status'], 'success')
        opcion = resultado['recomendaciones'][0]
        self.assertEqual(Procesador.objects.get(pk=self._id(opcion, 'procesador')).socket, 'AM5')
        self.assertTrue(any('AM4' in texto for texto in opcion['preferencias_no_cumplidas']))

    def test_sin_gpu_obligatoria_con_video_confirmado(self):
        self._oficina(graficos=True, salidas=True, con_gpu=True)
        resultado = generar_recomendaciones(
            2_000_000, 'trabajo',
            preferencias=Preferencias(gpu='sin_dedicada', gpu_modo='obligatorio'),
        )

        self.assertEqual(resultado['status'], 'success')
        opcion = resultado['recomendaciones'][0]
        self.assertTrue(opcion['usa_graficos_integrados'])
        self.assertFalse(self._tiene_gpu(opcion))
        self.assertTrue(any('Sin GPU dedicada' in texto for texto in opcion['requisitos_cumplidos']))

    def test_sin_gpu_obligatoria_no_se_relaja_si_el_video_es_desconocido(self):
        self._oficina(graficos=None, salidas=None, con_gpu=True)
        mensaje = (
            'No se encontró una combinación de procesador y placa madre con gráficos integrados '
            'y salida de video confirmados. No es posible generar una configuración sin tarjeta '
            'gráfica dedicada con los componentes disponibles.'
        )
        for uso in ('general', 'trabajo'):
            resultado = generar_recomendaciones(
                2_000_000, uso,
                preferencias=Preferencias(gpu='sin_dedicada', gpu_modo='obligatorio'),
            )
            self.assertEqual(resultado['status'], 'sin_recomendacion')
            self.assertEqual(resultado['recomendaciones'], [])
            self.assertEqual(resultado['mensaje'], mensaje)

    def test_sin_gpu_se_rechaza_en_gaming_y_edicion_aunque_sea_preferencia(self):
        self.catalogo_valido()
        mensajes = {
            'gaming': (
                'Para un PC Gaming se requiere una tarjeta gráfica dedicada. '
                'No es posible generar una configuración sin ella.'
            ),
            'edicion': (
                'Para un PC de Edición se requiere una tarjeta gráfica dedicada '
                'según las reglas actuales del recomendador. '
                'No es posible generar una configuración sin ella.'
            ),
        }
        for uso, mensaje in mensajes.items():
            for modo in ('preferencia', 'obligatorio'):
                resultado = generar_recomendaciones(
                    2_000_000, uso,
                    preferencias=Preferencias(gpu='sin_dedicada', gpu_modo=modo),
                )
                self.assertEqual(resultado['status'], 'sin_recomendacion')
                self.assertEqual(resultado['recomendaciones'], [])
                self.assertEqual(resultado['mensaje'], mensaje)

    def test_presupuesto_insuficiente_para_la_ram_obligatoria(self):
        self.cpu('CPU', 'AM5', watts=65, precio='90000')
        self.placa('Placa', 'AM5', 'DDR5', precio='20000')
        self.ram('RAM 16', 'DDR5', precio='10000', stock=1, capacidad=16)
        self.ram('RAM 32', 'DDR5', precio='100000', stock=4, capacidad=32)
        self.gpu('GPU', 200, consumo=80, precio='40000')
        self.gabinete('Gabinete', 350, precio='15000')
        self.fuente('Fuente 450', 450, precio='20000')
        self.ssd(precio='10000')
        resultado = generar_recomendaciones(
            180_000, 'gaming',
            preferencias=Preferencias(ram_gb=32, ram_modo='obligatorio'),
        )

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertIn('32', resultado['mensaje'])
        self.assertIn('presupuesto', resultado['mensaje'].lower())

    def test_socket_obligatorio_sin_stock_no_usa_otra_plataforma(self):
        self.cpu('CPU AM5 agotada', 'AM5', stock=0)
        self.cpu('CPU AM4', 'AM4')
        self.placa('Placa AM4', 'AM4', 'DDR4')
        self.placa('Placa AM5', 'AM5', 'DDR5')
        self.ram('RAM DDR4', 'DDR4')
        self.gpu('GPU 280', 280)
        self.gabinete('Gabinete 350', 350)
        self.fuente('Fuente 650', 650)
        self.ssd()
        resultado = generar_recomendaciones(
            2_000_000, 'gaming',
            preferencias=Preferencias(socket='AM5', socket_modo='obligatorio'),
        )

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertIn('AM5', resultado['mensaje'])
        self.assertIn('stock', resultado['mensaje'].lower())

    def test_completar_no_reemplaza_un_cpu_que_contradice_el_socket(self):
        self.catalogo_valido()
        elegida = self.cpu('Ryzen 5 5600', 'AM4', precio='90000')
        resultado = generar_recomendaciones(
            2_000_000, 'gaming',
            seleccion={'procesador': elegida},
            preferencias=Preferencias(socket='AM5', socket_modo='obligatorio'),
        )

        self.assertEqual(resultado['status'], 'sin_recomendacion')
        self.assertIn('No se reemplazó', resultado['mensaje'])
        self.assertIn('AM4', resultado['mensaje'])
        self.assertIn('AM5', resultado['mensaje'])

    def test_una_preferencia_holgada_conserva_las_alternativas(self):
        self._catalogo_con_gamas()
        base = generar_recomendaciones(1_500_000, 'gaming', resolucion='1440p')
        con_preferencia = generar_recomendaciones(
            1_500_000, 'gaming', resolucion='1440p',
            preferencias=Preferencias(ram_gb=8, ram_modo='preferencia'),
        )

        self.assertEqual(base['status'], 'success')
        self.assertEqual(len(base['recomendaciones']), len(con_preferencia['recomendaciones']))
        opciones = con_preferencia['recomendaciones']
        self.assertGreaterEqual(len(opciones), 2)
        self.assertLessEqual(len(opciones), 3)
        perfiles = {
            (self._id(opcion, 'procesador'), self._item(opcion, 'tarjeta_grafica')['nombre'])
            for opcion in opciones
        }
        self.assertEqual(len(perfiles), len(opciones))

    def test_sin_preferencias_conserva_el_resultado_anterior(self):
        self.catalogo_valido()
        anterior = generar_recomendaciones(2_000_000, 'gaming')
        actual = generar_recomendaciones(2_000_000, 'gaming', preferencias=Preferencias())

        def firma(resultado):
            return [
                [(item['tipo'], item['id'], item['cantidad']) for item in opcion['componentes']]
                for opcion in resultado['recomendaciones']
            ]

        self.assertEqual(anterior['status'], actual['status'])
        self.assertEqual(firma(anterior), firma(actual))
        self.assertEqual(actual['recomendaciones'][0]['requisitos_cumplidos'], [])
        self.assertEqual(actual['recomendaciones'][0]['preferencias_no_cumplidas'], [])

    def _post_recomendacion(self, **extra):
        cuerpo = {
            'presupuesto': 2_000_000,
            'uso': 'general',
            'resolucion': '',
            'modo': 'desde_cero',
            'gpu': 'automatica',
        }
        cuerpo.update(extra)
        return self.client.post(
            reverse('core:recomendar_pc'),
            data=json.dumps(cuerpo),
            content_type='application/json',
        )

    def _assert_plataformas(self, data, socket):
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['recomendaciones'])
        for opcion in data['recomendaciones']:
            cpu = Procesador.objects.get(pk=self._id(opcion, 'procesador'))
            placa = PlacaMadre.objects.get(pk=self._id(opcion, 'placa_madre'))
            self.assertEqual(cpu.socket, socket)
            self.assertEqual(placa.socket_cpu, socket)
            if socket:
                self.assertNotEqual(cpu.socket, 'AM4')
                self.assertNotEqual(placa.socket_cpu, 'AM4')

    def test_la_vista_obliga_am5_cuando_hay_piezas_compatibles(self):
        self.catalogo_valido()
        self.cpu('CPU AM4', 'AM4', precio='60000')
        self.placa('Placa AM4', 'AM4', 'DDR4', precio='50000')
        self.ram('RAM DDR4', 'DDR4', precio='20000')
        respuesta = self._post_recomendacion(socket='AM5', socket_modo='obligatorio')

        self.assertEqual(respuesta.status_code, 200)
        data = respuesta.json()
        self._assert_plataformas(data, 'AM5')
        self.assertIn(
            'Socket AM5: cumple la plataforma seleccionada.',
            data['recomendaciones'][0]['requisitos_cumplidos'],
        )

    def test_am5_obligatorio_sin_piezas_explica_el_vacio(self):
        respuesta = self._post_recomendacion(
            presupuesto=600_000, socket='AM5', socket_modo='obligatorio',
        )
        data = respuesta.json()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(data['status'], 'sin_recomendacion')
        self.assertEqual(data['recomendaciones'], [])
        self.assertIn('AM5', data['mensaje'])
        self.assertIn('stock', data['mensaje'].lower())

    def test_am5_obligatorio_no_cae_en_un_catalogo_solo_am4(self):
        self.cpu('CPU AM4 básica', 'AM4', watts=65, precio='59990')
        self.placa('Placa AM4', 'AM4', 'DDR4', precio='49990')
        self.ram('RAM DDR4', 'DDR4', precio='24990')
        self.gpu('GPU 4GB', 190, consumo=110, precio='109990')
        self.gabinete('Gabinete', 300, precio='69990')
        self.fuente('Fuente 450', 450, precio='34990')
        self.ssd(precio='29990')
        respuesta = self._post_recomendacion(
            presupuesto=600_000, socket='AM5', socket_modo='obligatorio',
        )
        data = respuesta.json()

        self.assertEqual(data['status'], 'sin_recomendacion')
        self.assertEqual(data['recomendaciones'], [])
        self.assertIn('AM5', data['mensaje'])
        self.assertNotIn('AM4', data['mensaje'])

    def test_am5_opcional_puede_usar_am4_y_lo_explica(self):
        self.cpu('CPU AM4 básica', 'AM4', watts=65, precio='59990')
        self.placa('Placa AM4', 'AM4', 'DDR4', precio='49990')
        self.ram('RAM DDR4', 'DDR4', precio='24990')
        self.gpu('GPU 4GB', 190, consumo=110, precio='109990')
        self.gabinete('Gabinete', 300, precio='69990')
        self.fuente('Fuente 450', 450, precio='34990')
        self.ssd(precio='29990')
        data = self._post_recomendacion(
            presupuesto=600_000, socket='AM5', socket_modo='preferencia',
        ).json()

        self.assertEqual(data['status'], 'success')
        cpu = Procesador.objects.get(pk=self._id(data['recomendaciones'][0], 'procesador'))
        self.assertEqual(cpu.socket, 'AM4')
        self.assertTrue(any(
            'AM5' in texto or 'AM4' in texto
            for texto in data['recomendaciones'][0]['preferencias_no_cumplidas']
        ))

    def test_completar_con_cpu_am4_no_lo_cambia_por_am5_obligatorio(self):
        self.catalogo_valido()
        elegida = self.cpu('CPU AM4 básica', 'AM4', watts=65, precio='59990')
        respuesta = self._post_recomendacion(
            modo='completar',
            socket='AM5',
            socket_modo='obligatorio',
            componentes=[{'tipo': 'procesador', 'id': elegida.id, 'cantidad': 1}],
        )
        data = respuesta.json()

        self.assertEqual(data['status'], 'sin_recomendacion')
        self.assertIn('No se reemplazó', data['mensaje'])
        self.assertIn('AM4', data['mensaje'])
        self.assertIn('AM5', data['mensaje'])
        self.assertEqual(data['recomendaciones'], [])

    def test_presupuesto_justo_obliga_am5_aunque_la_ram_mayor_no_quepa(self):
        self.cpu('CPU AM5 sin watts', 'AM5', nucleos=12, frecuencia='4.60', watts=None, precio='149990')
        media = self.cpu('CPU AM5 media', 'AM5', nucleos=6, frecuencia='3.50', watts=105, precio='189990')
        self.cpu('CPU AM4 básica', 'AM4', watts=65, precio='59990')
        self.placa('Placa AM5', 'AM5', 'DDR5', precio='129990')
        self.placa('Placa AM5 media', 'AM5', 'DDR5', precio='139990')
        self.placa('Placa AM4', 'AM4', 'DDR4', precio='49990')
        self.ram('RAM DDR5 16', 'DDR5', precio='39990', capacidad=16)
        self.ram('RAM DDR5 32', 'DDR5', precio='79990', capacidad=32)
        self.ram('RAM DDR4', 'DDR4', precio='24990', capacidad=16)
        self.gpu('GPU 4GB', 190, consumo=110, vram=4, precio='109990')
        self.gabinete('Gabinete ATX', 300, precio='69990')
        self.fuente('Fuente 450', 450, precio='34990')
        self.ssd(precio='29990', capacidad=500)
        data = self._post_recomendacion(
            presupuesto=600_000, socket='AM5', socket_modo='obligatorio',
        ).json()

        self._assert_plataformas(data, 'AM5')
        for opcion in data['recomendaciones']:
            self.assertEqual(self._id(opcion, 'procesador'), media.id)
            self.assertLessEqual(opcion['total'], 600_000)
            self.assertNotIn('AM4', opcion['titulo'])

    def _placa_con_puertos(self, nombre, socket, ddr, **kwargs):
        placa = self.placa(nombre, socket, ddr, **kwargs)
        placa.puertos_sata = 2
        placa.ranuras_m2_solo_nvme = 1
        placa.ranuras_m2_solo_sata = 0
        placa.ranuras_m2_nvme_o_sata = 0
        placa.save()
        return placa

    def test_recupera_un_armado_completo_que_el_haz_corto_descarta(self):
        self.cpu('CPU AM5', 'AM5', nucleos=8, frecuencia='4.00', watts=65, precio='100000')
        self._placa_con_puertos('Placa AM5', 'AM5', 'DDR5', precio='80000')
        self.ram('RAM 16', 'DDR5', precio='20000', stock=1, capacidad=16)
        self.ram('RAM 32', 'DDR5', precio='80000', stock=2, capacidad=32)
        self.gpu('GPU', 200, consumo=100, precio='100000')
        self.gabinete('Gabinete', 300, precio='40000')
        self.fuente('Fuente 450', 450, precio='50000')
        disco = self.ssd(precio='40000', capacidad=500)
        data = self._post_recomendacion(presupuesto=470_000, uso='general').json()

        self.assertFalse(data['sin_configuracion_completa'])
        self.assertEqual(len(data['recomendaciones']), 1)
        opcion = data['recomendaciones'][0]
        self.assertFalse(opcion['configuracion_incompleta'])
        self.assertEqual(self._id(opcion, 'almacenamiento_ssd'), disco.id)
        self.assertEqual(self._item(opcion, 'memoria_ram')['cantidad'], 1)
        self.assertEqual(self._item(opcion, 'memoria_ram')['nombre'], 'RAM 16')
        self.assertLessEqual(opcion['total'], 470_000)
        self.assertEqual(opcion['titulo'], 'Mejor clasificada')

    def test_sin_disco_verificado_informa_el_adicional_de_esa_configuracion(self):
        self.cpu('CPU AM5', 'AM5', watts=65, precio='100000')
        self._placa_con_puertos('Placa AM5', 'AM5', 'DDR5', precio='80000')
        self.ram('RAM 16', 'DDR5', precio='20000', stock=1, capacidad=16)
        self.gpu('GPU', 200, consumo=100, precio='100000')
        self.gabinete('Gabinete', 300, precio='40000')
        self.fuente('Fuente 450', 450, precio='50000')
        disco = self.ssd('SSD verificable', precio='80000', capacidad=500)
        data = self._post_recomendacion(presupuesto=420_000, uso='general').json()
        opcion = data['recomendaciones'][0]
        base = 100000 + 80000 + 20000 + 100000 + 40000 + 50000

        self.assertTrue(data['sin_configuracion_completa'])
        self.assertIn('computador completo', data['mensaje'])
        self.assertTrue(opcion['configuracion_incompleta'])
        self.assertEqual(opcion['pieza_faltante'], 'Almacenamiento')
        self.assertEqual(opcion['presupuesto_adicional'], 80000 - (420000 - base))
        self.assertEqual(opcion['disco_para_completar'], disco.nombre)
        self.assertIn('no es el mínimo de todo el catálogo', opcion['motivo_incompleto'])
        self.assertLessEqual(opcion['total'], 420_000)
        self.assertFalse(self._tiene_disco(opcion))

    def test_am5_obligatorio_sin_completo_no_relaja_ni_supera_el_presupuesto(self):
        self.cpu('CPU AM5', 'AM5', watts=105, precio='189990')
        self.cpu('CPU AM4', 'AM4', watts=65, precio='59990')
        self._placa_con_puertos('Placa AM5', 'AM5', 'DDR5', precio='139990')
        self.placa('Placa AM4', 'AM4', 'DDR4', precio='49990')
        self.ram('RAM DDR5 16', 'DDR5', precio='39990', stock=1, capacidad=16)
        self.ram('RAM DDR4', 'DDR4', precio='24990', capacidad=16)
        self.gpu('GPU 4GB', 190, consumo=110, precio='109990')
        self.gabinete('Gabinete ATX', 300, precio='69990')
        self.fuente('Fuente 450', 450, precio='34990')
        self.ssd(precio='29990', capacidad=500)
        data = self._post_recomendacion(
            presupuesto=600_000, uso='general', socket='AM5', socket_modo='obligatorio',
        ).json()

        self.assertTrue(data['sin_configuracion_completa'])
        self.assertIn('computador completo', data['mensaje'])
        self._assert_plataformas(data, 'AM5')
        for opcion in data['recomendaciones']:
            self.assertTrue(opcion['configuracion_incompleta'])
            self.assertFalse(self._tiene_disco(opcion))
            self.assertLessEqual(opcion['total'], 600_000)
            self.assertIn('lista para comprar', data['mensaje'])

    def test_la_vista_aplica_el_socket_y_rechaza_uno_invalido(self):
        self.catalogo_valido()
        respuesta = self.client.post(
            reverse('core:recomendar_pc'),
            data=json.dumps({
                'presupuesto': 2_000_000,
                'uso': 'gaming',
                'modo': 'desde_cero',
                'socket': 'AM5',
                'socket_modo': 'obligatorio',
            }),
            content_type='application/json',
        )
        invalida = self.client.post(
            reverse('core:recomendar_pc'),
            data=json.dumps({
                'presupuesto': 2_000_000,
                'uso': 'gaming',
                'modo': 'desde_cero',
                'socket': 'TR4',
            }),
            content_type='application/json',
        )

        self.assertEqual(respuesta.status_code, 200)
        opcion = respuesta.json()['recomendaciones'][0]
        self.assertIn('Socket AM5: cumple la plataforma seleccionada.', opcion['requisitos_cumplidos'])
        self.assertEqual(invalida.status_code, 400)

    def _item(self, opcion, tipo):
        return next(item for item in opcion['componentes'] if item['tipo'] == tipo)

    def _id(self, opcion, tipo):
        return self._item(opcion, tipo)['id']
