import json
import os
import threading
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import connection
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

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
    TarjetaGrafica,
)


def _motivo_concurrencia_pendiente():
    """Cadena vacía si esta ejecución puede probar la carrera en PostgreSQL local."""
    if os.environ.get('ARMADO_CONCURRENCIA_PG') != '1':
        return (
            'Pendiente. Define ARMADO_CONCURRENCIA_PG=1 y apunta Django a un '
            'PostgreSQL local de pruebas, nunca a Railway.'
        )
    if connection.vendor != 'postgresql':
        return 'Pendiente. Esta ejecución no está usando PostgreSQL.'
    host = (connection.settings_dict.get('HOST') or '').lower()
    if host not in ('127.0.0.1', 'localhost', '::1'):
        return 'Pendiente. El host no es un PostgreSQL local aislado.'
    texto = f"{host} {(connection.settings_dict.get('NAME') or '')}".lower()
    if 'railway' in texto or 'rlwy' in texto:
        return 'Pendiente. Se rechazó un host o nombre que parece de producción.'
    return ''


class StockArmadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proveedor = Proveedor.objects.create(nombre='Marca stock armado')
        cls.user = User.objects.create_user('stock_armado', 'stock@example.com', 'clave-stock')
        cls.otro = User.objects.create_user('stock_otro', 'otro@example.com', 'clave-stock')

    def setUp(self):
        self.client.force_login(self.user)

    def cpu(self, nombre, stock, socket='AM5', precio='100000'):
        return Procesador.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal(precio), stock=stock,
            socket=socket, nucleos=6, frecuencia_base=Decimal('3.50'),
        )

    def ram(self, stock):
        return MemoriaRam.objects.create(
            proveedor=self.proveedor, nombre=f'RAM {stock}', precio=Decimal('20000'), stock=stock,
            capacidad_gb=16, tipo_ddr='DDR5', velocidad_mhz=5600,
            modulos_por_producto=1, capacidad_modulo_gb=16, formato_ram='DIMM',
        )

    def placa(self, socket):
        return PlacaMadre.objects.create(
            proveedor=self.proveedor, nombre=f'Placa {socket}', precio=Decimal('80000'), stock=4,
            socket_cpu=socket, chipset='B650', formato='ATX', ranuras_ram=4,
            tipo_ram_soportado='DDR5',
        )

    def companeros(self, cpu, incluir_ram=True):
        placa = PlacaMadre.objects.create(
            proveedor=self.proveedor, nombre=f'Placa de {cpu.nombre}', precio=Decimal('80000'), stock=4,
            socket_cpu=cpu.socket, chipset='B650', formato='ATX', ranuras_ram=4,
            tipo_ram_soportado='DDR5', formato_ram_soportado='DIMM', capacidad_maxima_ram_gb=128,
        )
        gpu = TarjetaGrafica.objects.create(
            proveedor=self.proveedor, nombre=f'GPU de {cpu.nombre}', precio=Decimal('100000'), stock=4,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
            consumo_referencia_watts=100, largo_mm=200,
        )
        gabinete = Gabinete.objects.create(
            proveedor=self.proveedor, nombre=f'Gabinete de {cpu.nombre}', precio=Decimal('40000'), stock=4,
            formato_soporte='ATX', material='Acero', largo_max_gpu_mm=320,
        )
        fuente = FuenteDePoder.objects.create(
            proveedor=self.proveedor, nombre=f'Fuente de {cpu.nombre}', precio=Decimal('50000'), stock=4,
            potencia_watts=650, certificacion='80+ Bronze',
        )
        disco = AlmacenamientoSSD.objects.create(
            proveedor=self.proveedor, nombre=f'SSD de {cpu.nombre}', precio=Decimal('20000'), stock=4,
            capacidad_gb=1000, interfaz='NVMe PCIe 4.0', formato='M.2 2280',
        )
        pares = [
            ('placa_madre', placa, None),
            ('tarjeta_grafica', gpu, None),
            ('gabinete', gabinete, None),
            ('fuente_de_poder', fuente, None),
            ('almacenamiento_ssd', disco, None),
        ]
        if incluir_ram:
            ram = MemoriaRam.objects.create(
                proveedor=self.proveedor, nombre=f'RAM de {cpu.nombre}', precio=Decimal('20000'), stock=4,
                capacidad_gb=16, tipo_ddr='DDR5', velocidad_mhz=5600,
                modulos_por_producto=1, capacidad_modulo_gb=16, formato_ram='DIMM',
            )
            pares.insert(1, ('memoria_ram', ram, 1))
        return tuple(pares)

    def post(self, client, *pares):
        componentes = [
            {'tipo': tipo, 'id': producto.id, **({'cantidad': cantidad} if cantidad else {})}
            for tipo, producto, cantidad in pares
        ]
        return client.post(
            reverse('core:agregar_armado_al_carrito'),
            data=json.dumps({'componentes': componentes}),
            content_type='application/json',
        )

    def test_la_cantidad_igual_al_stock_se_agrega_y_el_stock_no_cambia(self):
        ram = MemoriaRam.objects.create(
            proveedor=self.proveedor, nombre='RAM completa', precio=Decimal('20000'), stock=2,
            capacidad_gb=16, tipo_ddr='DDR5', velocidad_mhz=5600,
            modulos_por_producto=1, capacidad_modulo_gb=16, formato_ram='DIMM',
        )
        cpu = self.cpu('CPU con la RAM', 4)
        cpu.potencia_referencia_watts = 65
        cpu.save(update_fields=['potencia_referencia_watts'])
        respuesta = self.post(
            self.client,
            ('procesador', cpu, None),
            ('memoria_ram', ram, 2),
            *self.companeros(cpu, incluir_ram=False),
        )

        self.assertEqual(respuesta.status_code, 200)
        item = ItemCarrito.objects.get(memoria_ram__isnull=False)
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(item.precio_unitario, ram.precio)
        ram.refresh_from_db()
        self.assertEqual(ram.stock, 2)

    def test_superar_el_stock_no_guarda_nada(self):
        ram = self.ram(2)
        respuesta = self.post(self.client, ('memoria_ram', ram, 3))

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()['estado'], 'error')
        self.assertIn('stock', respuesta.json()['motivos'][0])
        self.assertEqual(ItemCarrito.objects.count(), 0)
        self.assertEqual(Carrito.objects.count(), 0)
        ram.refresh_from_db()
        self.assertEqual(ram.stock, 2)

    def test_la_cantidad_previa_del_mismo_usuario_cuenta(self):
        cpu = self.cpu('CPU previa', 1, precio='50000')
        carrito = Carrito.objects.create(usuario=self.user)
        ItemCarrito.objects.create(
            carrito=carrito, procesador=cpu, cantidad=1, precio_unitario=Decimal('1.00'),
        )

        rechazo = self.post(self.client, ('procesador', cpu, None))
        self.assertEqual(rechazo.status_code, 400)
        self.assertIn('1 ya en el carrito', rechazo.json()['motivos'][0])
        self.assertEqual(ItemCarrito.objects.get().cantidad, 1)
        self.assertEqual(ItemCarrito.objects.get().precio_unitario, Decimal('1.00'))

        cpu.stock = 2
        cpu.potencia_referencia_watts = 65
        cpu.save(update_fields=['stock', 'potencia_referencia_watts'])
        aceptada = self.post(self.client, ('procesador', cpu, None), *self.companeros(cpu))
        self.assertEqual(aceptada.status_code, 200)
        item = ItemCarrito.objects.get(procesador__isnull=False)
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(item.precio_unitario, Decimal('1.00'))
        cpu.refresh_from_db()
        self.assertEqual(cpu.stock, 2)

    def test_el_stock_insuficiente_no_guarda_el_resto_del_armado(self):
        cpu = self.cpu('CPU acompañante', 4)
        placa = self.placa('AM5')
        placa.stock = 1
        placa.save(update_fields=['stock'])
        carrito = Carrito.objects.create(usuario=self.user)
        ItemCarrito.objects.create(
            carrito=carrito, placa_madre=placa, cantidad=1, precio_unitario=placa.precio,
        )

        respuesta = self.post(
            self.client,
            ('procesador', cpu, None),
            ('placa_madre', placa, None),
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(ItemCarrito.objects.count(), 1)
        self.assertFalse(ItemCarrito.objects.filter(procesador__isnull=False).exists())
        cpu.refresh_from_db()
        placa.refresh_from_db()
        self.assertEqual(cpu.stock, 4)
        self.assertEqual(placa.stock, 1)

    def test_la_incompatibilidad_no_guarda_ninguna_pieza(self):
        cpu = self.cpu('CPU AM5 stock', 4)
        placa = self.placa('LGA1700')
        respuesta = self.post(
            self.client,
            ('procesador', cpu, None),
            ('placa_madre', placa, None),
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()['estado'], 'incompatible')
        self.assertEqual(ItemCarrito.objects.count(), 0)
        cpu.refresh_from_db()
        placa.refresh_from_db()
        self.assertEqual(cpu.stock, 4)
        self.assertEqual(placa.stock, 4)

    def test_dos_usuarios_pueden_guardar_la_ultima_unidad(self):
        cpu = self.cpu('Ultima CPU', 1)
        cpu.potencia_referencia_watts = 65
        cpu.save(update_fields=['potencia_referencia_watts'])
        pares = (('procesador', cpu, None), *self.companeros(cpu))
        primero = self.post(self.client, *pares)
        otro = Client()
        otro.force_login(self.otro)
        segundo = self.post(otro, *pares)

        self.assertEqual(primero.status_code, 200)
        self.assertEqual(segundo.status_code, 200)
        self.assertEqual(ItemCarrito.objects.filter(procesador__isnull=False).count(), 2)
        self.assertEqual(Carrito.objects.count(), 2)
        cpu.refresh_from_db()
        self.assertEqual(cpu.stock, 1)

    def test_una_segunda_alta_actualiza_la_linea_existente(self):
        cpu = self.cpu('CPU repetida', 4)
        cpu.potencia_referencia_watts = 65
        cpu.save(update_fields=['potencia_referencia_watts'])
        pares = (('procesador', cpu, None), *self.companeros(cpu))
        self.assertEqual(self.post(self.client, *pares).status_code, 200)
        self.assertEqual(self.post(self.client, *pares).status_code, 200)

        item = ItemCarrito.objects.get(procesador__isnull=False)
        self.assertEqual(item.cantidad, 2)
        cpu.refresh_from_db()
        self.assertEqual(cpu.stock, 4)


class ConcurrenciaMismoUsuarioTests(TransactionTestCase):
    """Dos POST reales del mismo usuario.

    No se ejecuta con SQLite. Para comprobarla, levanta un PostgreSQL vacío
    en la máquina local y corre solo esta clase, sin DATABASE_URL de Railway:

        $env:USE_SQLITE='False'
        $env:USE_HTTPS='False'
        $env:DATABASE_URL=''
        $env:DB_HOST='127.0.0.1'
        $env:DB_PORT='5432'
        $env:DB_NAME='hwh_armado_test'
        $env:DB_USER='postgres'
        $env:DB_PASSWORD='clave-local'
        $env:ARMADO_CONCURRENCIA_PG='1'
        .\\.venv\\Scripts\\python.exe manage.py test core.test_stock_armado.ConcurrenciaMismoUsuarioTests
    """

    def setUp(self):
        motivo = _motivo_concurrencia_pendiente()
        if motivo:
            self.skipTest(motivo)
        self.proveedor = Proveedor.objects.create(nombre='Marca concurrencia')
        self.user = User.objects.create_user('concurre', 'concurre@example.com', 'clave-concurre')
        self.cpu = Procesador.objects.create(
            proveedor=self.proveedor, nombre='CPU unica', precio=Decimal('10000'), stock=1,
            socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
        )

    def _post_simultaneos(self):
        barrera = threading.Barrier(2)
        resultados = []

        def intentar():
            connection.close()
            cliente = Client()
            cliente.force_login(self.user)
            barrera.wait()
            respuesta = cliente.post(
                reverse('core:agregar_armado_al_carrito'),
                data=json.dumps({'componentes': [{'tipo': 'procesador', 'id': self.cpu.id}]}),
                content_type='application/json',
            )
            resultados.append(respuesta.status_code)
            connection.close()

        hilos = [threading.Thread(target=intentar), threading.Thread(target=intentar)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()
        return resultados

    def test_dos_solicitudes_simultaneas_no_superan_el_stock_ni_duplican_la_linea(self):
        codigos = self._post_simultaneos()

        self.assertCountEqual(codigos, [200, 400])
        self.assertEqual(ItemCarrito.objects.count(), 1)
        self.assertEqual(ItemCarrito.objects.get().cantidad, 1)
        self.assertEqual(Carrito.objects.filter(usuario=self.user).count(), 1)
        self.cpu.refresh_from_db()
        self.assertEqual(self.cpu.stock, 1)
