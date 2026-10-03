import json
from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from core.admin import PlacaMadreAdmin
from core.compatibilidad import validar_armado
from core.models import (
    AlmacenamientoHDD,
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
    Ventilador,
)


def pieza(**atributos):
    return SimpleNamespace(**atributos)


class CompatibilidadTests(SimpleTestCase):
    def armado_base(self, **cambios):
        seleccion = {
            'procesador': pieza(socket='AM5'),
            'placa_madre': pieza(socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='ATX'),
            'memoria_ram': pieza(tipo_ddr='DDR5'),
            'gabinete': pieza(formato_soporte='ATX'),
            'refrigeracion': pieza(socket_compatibles='AM5, LGA1700'),
        }
        seleccion.update(cambios)
        return validar_armado(**seleccion)

    def test_combinacion_compatible_normaliza_espacios_y_mayusculas(self):
        resultado = validar_armado(
            procesador=pieza(socket=' am5 '),
            placa_madre=pieza(socket_cpu='AM5', tipo_ram_soportado=' ddr5 ', formato='micro-atx'),
            memoria_ram=pieza(tipo_ddr='DDR5'),
            gabinete=pieza(formato_soporte=' atx '),
            refrigeracion=pieza(socket_compatibles=' am5 , lga 1700 '),
        )

        self.assertEqual(resultado.estado, 'compatible')
        self.assertTrue(resultado.es_compatible)
        self.assertEqual(resultado.motivos_de_rechazo, [])

    def test_gabinete_mas_grande_admite_placa_mas_chica(self):
        resultado = self.armado_base(
            placa_madre=pieza(socket_cpu='AM5', tipo_ram_soportado='DDR5', formato='Mini-ITX'),
            gabinete=pieza(formato_soporte='ATX'),
        )

        self.assertTrue(resultado.es_compatible)

    def test_socket_ddr_formato_y_cooler_incompatibles(self):
        resultado = validar_armado(
            procesador=pieza(socket='AM5'),
            placa_madre=pieza(socket_cpu='LGA1700', tipo_ram_soportado='DDR4', formato='ATX'),
            memoria_ram=pieza(tipo_ddr='DDR5'),
            gabinete=pieza(formato_soporte='Mini-ITX'),
            refrigeracion=pieza(socket_compatibles='AM4'),
        )

        self.assertEqual(resultado.estado, 'incompatible')
        self.assertFalse(resultado.es_compatible)
        self.assertGreaterEqual(len(resultado.motivos_de_rechazo), 4)
        texto = ' '.join(resultado.motivos_de_rechazo)
        self.assertIn('AM5', texto)
        self.assertIn('LGA1700', texto)
        self.assertIn('DDR5', texto)
        self.assertIn('DDR4', texto)
        self.assertIn('MINI-ITX', texto)

    def test_socket_otro_no_se_declara_compatible(self):
        ambos_otro = validar_armado(
            procesador=pieza(socket='Otro'),
            placa_madre=pieza(socket_cpu=' otro ', tipo_ram_soportado='DDR4', formato='ATX'),
        )
        uno_conocido = validar_armado(
            procesador=pieza(socket='Otro'),
            placa_madre=pieza(socket_cpu='AM4', tipo_ram_soportado='DDR4', formato='ATX'),
        )

        self.assertEqual(ambos_otro.estado, 'datos_insuficientes')
        self.assertFalse(ambos_otro.es_compatible)
        self.assertEqual(uno_conocido.estado, 'datos_insuficientes')
        self.assertTrue(uno_conocido.bloquea_agregar)
        self.assertNotIn('incompatible', [hallazgo.estado for hallazgo in uno_conocido.hallazgos])

    def test_formato_desconocido_no_se_declara_compatible(self):
        resultado = validar_armado(
            placa_madre=pieza(formato='E-ATX', socket_cpu='AM5', tipo_ram_soportado='DDR5'),
            gabinete=pieza(formato_soporte='ATX'),
            procesador=pieza(socket='AM5'),
            memoria_ram=pieza(tipo_ddr='DDR5'),
        )

        self.assertEqual(resultado.estado, 'datos_insuficientes')
        self.assertFalse(resultado.es_compatible)
        self.assertTrue(any(hallazgo.regla == 'formato' for hallazgo in resultado.hallazgos))

    def test_cooler_sin_sockets_conocidos_no_se_declara_compatible(self):
        resultado = self.armado_base(refrigeracion=pieza(socket_compatibles='Otro, foo'))

        self.assertEqual(resultado.estado, 'datos_insuficientes')
        self.assertTrue(resultado.bloquea_agregar)

    def test_seleccion_incompleta_no_es_un_conflicto(self):
        solo_cpu = validar_armado(procesador=pieza(socket='AM5'))
        solo_cooler = validar_armado(refrigeracion=pieza(socket_compatibles='AM5'))
        sin_gabinete = self.armado_base(gabinete=None)

        self.assertEqual(solo_cpu.estado, 'incompleto')
        self.assertFalse(solo_cpu.es_compatible)
        self.assertFalse(solo_cpu.bloquea_agregar)
        self.assertEqual(solo_cooler.estado, 'incompleto')
        self.assertEqual(sin_gabinete.estado, 'incompleto')
        self.assertFalse(sin_gabinete.bloquea_agregar)

    def test_sin_piezas_de_las_reglas_queda_compatible(self):
        resultado = validar_armado()

        self.assertEqual(resultado.estado, 'compatible')
        self.assertTrue(resultado.es_compatible)


class PlacaMadreAdminTests(SimpleTestCase):
    def test_muestra_tipo_ram_soportado(self):
        self.assertIn('tipo_ram_soportado', PlacaMadreAdmin.list_display)
        especificaciones = PlacaMadreAdmin.fieldsets[1][1]['fields']
        self.assertIn('tipo_ram_soportado', especificaciones)


class ArmadoCarritoTests(TestCase):
    password = 'test-armado-123'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('armado', 'armado@example.com', cls.password)
        cls.proveedor = Proveedor.objects.create(nombre='Marca Armado')
        cls.cpu_am5 = cls._cpu('AM5', 'Ryzen')
        cls.cpu_otro = cls._cpu('Otro', 'CPU generico')
        cls.board_am5 = cls._board('AM5', 'DDR5', 'ATX', 'B650 ATX')
        cls.board_am4 = cls._board('AM4', 'DDR4', 'ATX', 'B550 ATX')
        cls.board_eatx = cls._board('AM5', 'DDR5', 'E-ATX', 'Placa rara')
        cls.ram_ddr5 = cls._ram('DDR5')
        cls.ram_ddr4 = cls._ram('DDR4')
        cls.case_atx = cls._case('ATX', 'Gabinete ATX')
        cls.case_mini = cls._case('Mini-ITX', 'Gabinete Mini')
        cls.cooler = cls._cooler(' am5 , lga 1700 ')
        cls.gpu = cls._gpu()
        cls.ssd = cls._ssd()
        cls.hdd = cls._hdd()
        cls.fuente = cls._fuente()
        cls.ventilador = cls._ventilador()

    def setUp(self):
        self.client.login(username='armado', password=self.password)

    @classmethod
    def _cpu(cls, socket, nombre):
        return Procesador.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=Decimal('100000'), stock=4,
            socket=socket, nucleos=6, frecuencia_base=Decimal('3.50'),
            potencia_referencia_watts=65,
        )

    @classmethod
    def _board(cls, socket, ddr, formato, nombre):
        return PlacaMadre.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=Decimal('80000'), stock=4,
            socket_cpu=socket, chipset='B650', formato=formato, ranuras_ram=4,
            tipo_ram_soportado=ddr,
        )

    @classmethod
    def _ram(cls, tipo):
        return MemoriaRam.objects.create(
            proveedor=cls.proveedor, nombre=f'RAM {tipo}', precio=Decimal('40000'), stock=4,
            capacidad_gb=16, tipo_ddr=tipo, velocidad_mhz=5600,
        )

    @classmethod
    def _case(cls, formato, nombre):
        return Gabinete.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=Decimal('50000'), stock=4,
            formato_soporte=formato, material='Acero',
        )

    @classmethod
    def _cooler(cls, sockets):
        return RefrigeracionCooler.objects.create(
            proveedor=cls.proveedor, nombre='Cooler', precio=Decimal('30000'), stock=4,
            tipo='Aire', socket_compatibles=sockets,
        )

    @classmethod
    def _gpu(cls):
        return TarjetaGrafica.objects.create(
            proveedor=cls.proveedor, nombre='GPU', precio=Decimal('300000'), stock=4,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
            consumo_referencia_watts=120,
        )

    @classmethod
    def _ssd(cls):
        return AlmacenamientoSSD.objects.create(
            proveedor=cls.proveedor, nombre='SSD', precio=Decimal('60000'), stock=4,
            capacidad_gb=1000, interfaz='NVMe PCIe 4.0', formato='M.2 2280',
        )

    @classmethod
    def _hdd(cls):
        return AlmacenamientoHDD.objects.create(
            proveedor=cls.proveedor, nombre='HDD', precio=Decimal('45000'), stock=4,
            capacidad_gb=2000, velocidad_rpm=7200, cache_mb=256,
        )

    @classmethod
    def _fuente(cls):
        return FuenteDePoder.objects.create(
            proveedor=cls.proveedor, nombre='Fuente', precio=Decimal('70000'), stock=4,
            potencia_watts=650, certificacion='80+ Bronze',
        )

    @classmethod
    def _ventilador(cls):
        return Ventilador.objects.create(
            proveedor=cls.proveedor, nombre='Ventilador', precio=Decimal('10000'), stock=4,
            tamanho_mm=120, velocidad_rpm=1500,
        )

    def post_armado(self, pares):
        componentes = [{'tipo': tipo, 'id': producto.id} for tipo, producto in pares]
        return self.client.post(
            reverse('core:agregar_armado_al_carrito'),
            data=json.dumps({'componentes': componentes}),
            content_type='application/json',
        )

    def armado_valido(self):
        return [
            ('procesador', self.cpu_am5),
            ('placa_madre', self.board_am5),
            ('memoria_ram', self.ram_ddr5),
            ('gabinete', self.case_atx),
            ('refrigeracion', self.cooler),
            ('tarjeta_grafica', self.gpu),
            ('almacenamiento_ssd', self.ssd),
            ('almacenamiento_hdd', self.hdd),
            ('fuente_de_poder', self.fuente),
        ]

    def test_armado_compatible_distingue_ssd_y_hdd(self):
        response = self.post_armado(self.armado_valido())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['estado'], 'compatible')
        self.assertEqual(ItemCarrito.objects.count(), 9)
        item_ssd = ItemCarrito.objects.get(almacenamiento_ssd__isnull=False)
        item_hdd = ItemCarrito.objects.get(almacenamiento_hdd__isnull=False)
        self.assertEqual(item_ssd.almacenamiento_ssd_id, self.ssd.id)
        self.assertIsNone(item_ssd.almacenamiento_hdd_id)
        self.assertEqual(item_hdd.almacenamiento_hdd_id, self.hdd.id)
        self.assertIsNone(item_hdd.almacenamiento_ssd_id)

    def test_armado_incompatible_no_agrega_ninguna_pieza(self):
        carrito = Carrito.objects.create(usuario=self.user)
        ItemCarrito.objects.create(
            carrito=carrito, ventilador=self.ventilador, cantidad=1,
            precio_unitario=self.ventilador.precio,
        )

        response = self.post_armado([
            ('procesador', self.cpu_am5),
            ('placa_madre', self.board_am4),
            ('memoria_ram', self.ram_ddr5),
            ('gabinete', self.case_mini),
            ('tarjeta_grafica', self.gpu),
        ])

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['estado'], 'incompatible')
        self.assertGreaterEqual(len(data['motivos']), 2)
        self.assertEqual(ItemCarrito.objects.count(), 1)
        self.assertTrue(ItemCarrito.objects.filter(ventilador_id=self.ventilador.id).exists())
        self.assertFalse(ItemCarrito.objects.filter(procesador__isnull=False).exists())
        self.assertFalse(ItemCarrito.objects.filter(placa_madre__isnull=False).exists())
        self.assertFalse(ItemCarrito.objects.filter(tarjeta_grafica__isnull=False).exists())

    def test_datos_desconocidos_rechazan_el_armado_completo(self):
        response = self.post_armado([
            ('procesador', self.cpu_otro),
            ('placa_madre', self.board_am5),
            ('memoria_ram', self.ram_ddr5),
            ('tarjeta_grafica', self.gpu),
        ])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['estado'], 'datos_insuficientes')
        self.assertEqual(ItemCarrito.objects.count(), 0)

        response_formato = self.post_armado([
            ('procesador', self.cpu_am5),
            ('placa_madre', self.board_eatx),
            ('memoria_ram', self.ram_ddr5),
            ('gabinete', self.case_atx),
        ])

        self.assertEqual(response_formato.status_code, 400)
        self.assertEqual(response_formato.json()['estado'], 'datos_insuficientes')
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_seleccion_incompleta_si_se_agrega(self):
        response = self.post_armado([
            ('procesador', self.cpu_am5),
            ('placa_madre', self.board_am5),
            ('memoria_ram', self.ram_ddr5),
        ])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['estado'], 'incompleto')
        self.assertEqual(ItemCarrito.objects.count(), 3)

    def test_compra_individual_no_valida_el_armado(self):
        respuesta_cpu = self.client.post(reverse('core:agregar_al_carrito'), {
            'product_id': self.cpu_otro.id,
            'model_name': 'procesador',
            'quantity': 1,
        })
        respuesta_placa = self.client.post(reverse('core:agregar_al_carrito'), {
            'product_id': self.board_am5.id,
            'model_name': 'placa_madre',
            'quantity': 1,
        })

        self.assertEqual(respuesta_cpu.status_code, 302)
        self.assertEqual(respuesta_placa.status_code, 302)
        self.assertEqual(ItemCarrito.objects.count(), 2)
        self.assertTrue(ItemCarrito.objects.filter(procesador_id=self.cpu_otro.id).exists())
        self.assertTrue(ItemCarrito.objects.filter(placa_madre_id=self.board_am5.id).exists())

    def test_la_pagina_de_armado_identifica_ssd_y_hdd(self):
        response = self.client.get(reverse('core:armado'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'almacenamiento_ssd')
        self.assertContains(response, 'almacenamiento_hdd')
        self.assertContains(response, 'agregar-armado')


class CarritoSinImagenTests(TestCase):
    def test_carrito_con_producto_sin_imagen_responde_200(self):
        usuario = User.objects.create_user(
            'carrito_sin_imagen',
            'sin-imagen@example.com',
            'clave-test-carrito',
        )
        proveedor = Proveedor.objects.create(nombre='Marca sin imagen')
        cpu = Procesador.objects.create(
            proveedor=proveedor,
            nombre='CPU sin foto de prueba',
            precio=Decimal('1000.00'),
            stock=2,
            socket='AM5',
            nucleos=6,
            frecuencia_base=Decimal('3.50'),
        )
        carrito = Carrito.objects.create(usuario=usuario)
        ItemCarrito.objects.create(
            carrito=carrito,
            procesador=cpu,
            cantidad=1,
            precio_unitario=cpu.precio,
        )

        self.client.force_login(usuario)
        response = self.client.get(reverse('core:carrito'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CPU sin foto de prueba')
        self.assertContains(response, 'Sin imagen')
        self.assertContains(response, 'core/img/placeholder.webp')
