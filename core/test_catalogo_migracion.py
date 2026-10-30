"""Importación de catálogo: altas nuevas, sin tocar compras ni IDs existentes."""
import json
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from core.catalogo_migracion import (
    FORMATO,
    VERSION,
    CatalogoMigracionError,
    exportar_documento,
    importar_documento,
    normalizar_clave,
)
from core.models import (
    AlmacenamientoHDD,
    AlmacenamientoSSD,
    FuenteDePoder,
    Gabinete,
    ItemPedido,
    MemoriaRam,
    PagoBoleta,
    Pedido,
    PlacaMadre,
    Procesador,
    Proveedor,
    RefrigeracionCooler,
    TarjetaGrafica,
    Ventilador,
)


def _documento(proveedores, productos):
    return {
        'formato': FORMATO,
        'version': VERSION,
        'proveedores': proveedores,
        'productos': productos,
    }


def _cpu(proveedor, nombre, precio='89990.00', stock=5, **campos):
    especificaciones = {
        'socket': 'AM4',
        'nucleos': 4,
        'frecuencia_base': '3.60',
        'potencia_referencia_watts': 65,
        'incluye_cooler': None,
        'potencia_termica_referencia_watts': None,
    }
    especificaciones.update(campos)
    return {
        'familia': 'procesador',
        'proveedor': proveedor,
        'nombre': nombre,
        'descripcion': '',
        'precio': precio,
        'stock': stock,
        'campos': especificaciones,
    }


class CatalogoMigracionTests(TestCase):
    def setUp(self):
        self.marca = Proveedor.objects.create(nombre='Tienda')
        self.cpus = [
            self._procesador(nombre, Decimal(precio), stock)
            for nombre, precio, stock in (
                ('CPU uno', '1000.00', 1),
                ('CPU dos', '2000.00', 2),
                ('CPU vendido', '3000.00', 3),
                ('CPU otro vendido', '4000.00', 4),
            )
        ]
        self.ram = MemoriaRam.objects.create(
            proveedor=self.marca,
            nombre='RAM vendida',
            precio=Decimal('45990.00'),
            stock=4,
            capacidad_gb=16,
            tipo_ddr='DDR4',
            velocidad_mhz=3200,
        )
        self.usuario = User.objects.create_user('comprador', 'comprador@example.com', 'clave-de-prueba')
        self.pedido = Pedido.objects.create(
            usuario=self.usuario,
            total_monto=Decimal('10000.00'),
            direccion_envio='Calle 1',
            estado='PAGADO',
        )
        self.boleta = PagoBoleta.objects.create(
            pedido=self.pedido,
            monto_pagado=Decimal('10000.00'),
            metodo_pago='PayPal',
            transaccion_id='SANDBOX-TEST-1',
            nombre_comprador='Comprador',
            email_comprador='comprador@example.com',
        )
        self.linea_cpu = ItemPedido.objects.create(
            pedido=self.pedido,
            producto_nombre='CPU vendido',
            producto_tipo='CPU',
            precio_unitario=Decimal('3000.00'),
            cantidad=1,
            producto_modelo='procesador',
            producto_pk=self.cpus[2].pk,
        )
        self.linea_cpu_2 = ItemPedido.objects.create(
            pedido=self.pedido,
            producto_nombre='CPU otro vendido',
            producto_tipo='CPU',
            precio_unitario=Decimal('4000.00'),
            cantidad=1,
            producto_modelo='procesador',
            producto_pk=self.cpus[3].pk,
        )
        self.linea_ram = ItemPedido.objects.create(
            pedido=self.pedido,
            producto_nombre='RAM vendida',
            producto_tipo='Memoria RAM',
            precio_unitario=Decimal('45990.00'),
            cantidad=1,
            producto_modelo='memoria_ram',
            producto_pk=self.ram.pk,
        )

    def _procesador(self, nombre, precio, stock, proveedor=None):
        return Procesador.objects.create(
            proveedor=proveedor or self.marca,
            nombre=nombre,
            precio=precio,
            stock=stock,
            socket='AM4',
            nucleos=4,
            frecuencia_base=Decimal('3.60'),
            potencia_referencia_watts=65,
        )

    def _ids_previos(self):
        return set(Procesador.objects.values_list('pk', flat=True)) | set(
            MemoriaRam.objects.values_list('pk', flat=True)
        )

    def _assert_compras_intactas(self):
        self.linea_cpu.refresh_from_db()
        self.linea_cpu_2.refresh_from_db()
        self.linea_ram.refresh_from_db()
        self.cpus[2].refresh_from_db()
        self.cpus[3].refresh_from_db()
        self.ram.refresh_from_db()
        self.boleta.refresh_from_db()
        self.assertEqual(self.linea_cpu.producto_pk, self.cpus[2].pk)
        self.assertEqual(self.linea_cpu.producto_nombre, 'CPU vendido')
        self.assertEqual(self.linea_cpu.get_related_product().nombre, 'CPU vendido')
        self.assertEqual(self.linea_cpu_2.producto_pk, self.cpus[3].pk)
        self.assertEqual(self.linea_cpu_2.get_related_product().nombre, 'CPU otro vendido')
        self.assertEqual(self.linea_ram.producto_pk, self.ram.pk)
        self.assertEqual(self.linea_ram.get_related_product().nombre, 'RAM vendida')
        self.assertEqual(self.cpus[2].precio, Decimal('3000.00'))
        self.assertEqual(self.cpus[2].stock, 3)
        self.assertEqual(self.ram.stock, 4)
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(PagoBoleta.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.boleta.transaccion_id, 'SANDBOX-TEST-1')

    def test_alta_nueva_conserva_ids_precios_y_compras(self):
        previos = self._ids_previos()
        documento = _documento(
            ['Tienda', 'AMD'],
            [
                _cpu('Tienda', 'CPU vendido', precio='1.00', stock=99),
                _cpu('AMD', 'Ryzen 3 3100'),
            ],
        )
        resumen = importar_documento(documento, apply=True)
        self.assertEqual(resumen['insertar'], 1)
        self.assertEqual(resumen['distintos'], 1)
        ryzen = Procesador.objects.get(nombre='Ryzen 3 3100')
        self.assertNotIn(ryzen.pk, previos)
        self.assertEqual(ryzen.proveedor.nombre, 'AMD')
        self.assertEqual(ryzen.socket, 'AM4')
        self.assertEqual(ryzen.nucleos, 4)
        self.assertEqual(ryzen.frecuencia_base, Decimal('3.60'))
        self.assertEqual(ryzen.potencia_referencia_watts, 65)
        self.assertEqual(ryzen.precio, Decimal('89990.00'))
        self.assertEqual(ryzen.stock, 5)
        self._assert_compras_intactas()

        otra_vez = importar_documento(documento, apply=True)
        self.assertEqual(otra_vez['insertar'], 0)
        self.assertEqual(otra_vez['proveedores_crear'], 0)
        self.assertEqual(Procesador.objects.filter(nombre='Ryzen 3 3100').count(), 1)
        self._assert_compras_intactas()

    def test_nombres_duplicados_no_se_insertan_ni_se_actualizan(self):
        primero = self._procesador('ss', Decimal('111.00'), 3)
        segundo = self._procesador('ss', Decimal('222.00'), 4)
        documento = _documento(
            ['Tienda', 'AMD'],
            [
                _cpu('Tienda', 'ss', precio='999.00', stock=9),
                _cpu('AMD', 'Ryzen 3 3100'),
            ],
        )
        resumen = importar_documento(documento, apply=True)
        self.assertEqual(resumen['ambiguos'], 1)
        self.assertEqual(resumen['insertar'], 1)
        primero.refresh_from_db()
        segundo.refresh_from_db()
        self.assertEqual(primero.precio, Decimal('111.00'))
        self.assertEqual(segundo.precio, Decimal('222.00'))
        self.assertEqual(primero.stock, 3)
        self.assertEqual(segundo.stock, 4)
        self.assertEqual(Procesador.objects.filter(nombre='ss').count(), 2)
        self.assertTrue(Procesador.objects.filter(nombre='Ryzen 3 3100').exists())
        self._assert_compras_intactas()

    def test_proveedor_ambiguo_no_recibe_productos_ni_otro_registro(self):
        Proveedor.objects.create(nombre='AA')
        Proveedor.objects.create(nombre='aa')
        antes = Proveedor.objects.count()
        documento = _documento(['AA'], [_cpu('AA', 'Ryzen 3 3100')])
        resumen = importar_documento(documento, apply=True)
        self.assertEqual(resumen['proveedores_ambiguos'], 1)
        self.assertEqual(resumen['insertar'], 0)
        self.assertEqual(Proveedor.objects.count(), antes)
        self.assertFalse(Procesador.objects.filter(nombre='Ryzen 3 3100').exists())
        self.marca.refresh_from_db()
        self.assertEqual(self.marca.nombre, 'Tienda')

    def test_reutiliza_el_proveedor_aunque_cambie_mayusculas(self):
        documento = _documento(['tienda'], [_cpu('tienda', 'Ryzen 3 3100')])
        resumen = importar_documento(documento, apply=True)
        self.assertEqual(resumen['proveedores_crear'], 0)
        self.assertEqual(resumen['proveedores_reutilizar'], 1)
        ryzen = Procesador.objects.get(nombre='Ryzen 3 3100')
        self.assertEqual(ryzen.proveedor_id, self.marca.pk)
        self.assertEqual(self.marca.nombre, 'Tienda')
        self.assertEqual(Proveedor.objects.count(), 1)

    def test_el_archivo_invalido_no_escribe_y_un_fallo_final_revierte(self):
        antes_proveedores = Proveedor.objects.count()
        antes_cpus = Procesador.objects.count()
        incompleto = _documento(['AMD'], [_cpu('AMD', 'Ryzen 3 3100')])
        incompleto['productos'][0]['proveedor'] = 'Nadie'
        with self.assertRaises(CatalogoMigracionError):
            importar_documento(incompleto, apply=True)
        repetido = _documento(
            ['AMD'],
            [_cpu('AMD', 'Ryzen 3 3100'), _cpu('AMD', 'ryzen 3 3100', precio='1.00')],
        )
        with self.assertRaises(CatalogoMigracionError):
            importar_documento(repetido, apply=True)
        invalido = _cpu('AMD', 'Socket malo')
        invalido['campos']['socket'] = 'SLOT-X'
        with self.assertRaises(CatalogoMigracionError):
            importar_documento(_documento(['AMD'], [invalido]), apply=True)
        self.assertEqual(Proveedor.objects.count(), antes_proveedores)
        self.assertEqual(Procesador.objects.count(), antes_cpus)

        with patch(
            'core.catalogo_migracion._exigir_intactos',
            side_effect=CatalogoMigracionError('forzado'),
        ):
            with self.assertRaises(CatalogoMigracionError):
                importar_documento(_documento(['AMD'], [_cpu('AMD', 'Ryzen 3 3100')]), apply=True)
        self.assertEqual(Proveedor.objects.count(), antes_proveedores)
        self.assertFalse(Procesador.objects.filter(nombre='Ryzen 3 3100').exists())
        self._assert_compras_intactas()

    def test_dry_run_no_escribe(self):
        documento = _documento(['AMD'], [_cpu('AMD', 'Ryzen 3 3100')])
        with CaptureQueriesContext(connection) as consultas:
            resumen = importar_documento(documento, apply=False)
        self.assertFalse(resumen['apply'])
        self.assertEqual(resumen['insertar'], 1)
        self.assertFalse(Procesador.objects.filter(nombre='Ryzen 3 3100').exists())
        escrituras = [
            consulta['sql']
            for consulta in consultas.captured_queries
            if consulta['sql'].lstrip().lower().startswith(
                ('insert', 'update', 'delete', 'truncate', 'alter', 'drop', 'create')
            )
        ]
        self.assertEqual(escrituras, [])
        self.assertFalse(any('for update' in consulta['sql'].lower() for consulta in consultas.captured_queries))

    def test_las_diez_familias_conservan_compatibilidad_e_ids_nuevos(self):
        marca = Proveedor.objects.create(nombre='Catalogo Nuevo')
        creados = [
            Procesador.objects.create(
                proveedor=marca, nombre='CPU nueva', precio=Decimal('10.00'), stock=1,
                socket='AM5', nucleos=6, frecuencia_base=Decimal('4.20'), potencia_referencia_watts=88,
            ),
            TarjetaGrafica.objects.create(
                proveedor=marca, nombre='GPU nueva', precio=Decimal('20.00'), stock=2,
                vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0', largo_mm=270,
                consumo_referencia_watts=160, potencia_minima_fuente_watts=550,
            ),
            MemoriaRam.objects.create(
                proveedor=marca, nombre='RAM nueva', precio=Decimal('30.00'), stock=3,
                capacidad_gb=32, tipo_ddr='DDR5', velocidad_mhz=6000, modulos_por_producto=2,
                capacidad_modulo_gb=16, formato_ram='DIMM',
            ),
            PlacaMadre.objects.create(
                proveedor=marca, nombre='Placa nueva', precio=Decimal('40.00'), stock=4,
                socket_cpu='AM5', chipset='B650', formato='ATX', ranuras_ram=4,
                tipo_ram_soportado='DDR5', formato_ram_soportado='DIMM', capacidad_maxima_ram_gb=128,
            ),
            AlmacenamientoSSD.objects.create(
                proveedor=marca, nombre='SSD nuevo', precio=Decimal('50.00'), stock=5,
                capacidad_gb=1000, interfaz='NVMe PCIe 4.0', formato='M.2 2280',
            ),
            AlmacenamientoHDD.objects.create(
                proveedor=marca, nombre='HDD nuevo', precio=Decimal('60.00'), stock=6,
                capacidad_gb=2000, velocidad_rpm=7200, cache_mb=256,
            ),
            Gabinete.objects.create(
                proveedor=marca, nombre='Gabinete nuevo', precio=Decimal('70.00'), stock=7,
                formato_soporte='ATX', ventiladores_incluidos=True, material='Acero', largo_max_gpu_mm=360,
            ),
            FuenteDePoder.objects.create(
                proveedor=marca, nombre='Fuente nueva', precio=Decimal('80.00'), stock=8,
                potencia_watts=650, certificacion='80+ Bronze', modular=True,
            ),
            RefrigeracionCooler.objects.create(
                proveedor=marca, nombre='Cooler nuevo', precio=Decimal('90.00'), stock=9,
                tipo='Aire', socket_compatibles='AM4, AM5, LGA1700', tamanho_radiador_mm=None,
            ),
            Ventilador.objects.create(
                proveedor=marca, nombre='Fan nuevo', precio=Decimal('15.00'), stock=10,
                tamanho_mm=120, velocidad_rpm=1500, rgb=True,
            ),
        ]
        previos = {obj.pk for obj in creados}
        documento = json.loads(json.dumps(exportar_documento()))
        for obj in creados:
            obj.delete()
        marca.delete()
        resumen = importar_documento(documento, apply=True)
        self.assertEqual(resumen['insertar'], 10)
        self.assertEqual(resumen['proveedores_crear'], 1)
        gpu = TarjetaGrafica.objects.get(nombre='GPU nueva')
        ram = MemoriaRam.objects.get(nombre='RAM nueva')
        placa = PlacaMadre.objects.get(nombre='Placa nueva')
        self.assertNotIn(gpu.pk, previos)
        self.assertEqual(gpu.vram_gb, 8)
        self.assertEqual(gpu.largo_mm, 270)
        self.assertEqual(gpu.consumo_referencia_watts, 160)
        self.assertEqual(ram.tipo_ddr, 'DDR5')
        self.assertEqual(ram.modulos_por_producto, 2)
        self.assertEqual(ram.formato_ram, 'DIMM')
        self.assertEqual(placa.socket_cpu, 'AM5')
        self.assertEqual(placa.tipo_ram_soportado, 'DDR5')
        self.assertEqual(placa.capacidad_maxima_ram_gb, 128)
        self.assertEqual(AlmacenamientoSSD.objects.get(nombre='SSD nuevo').interfaz, 'NVMe PCIe 4.0')
        self.assertEqual(AlmacenamientoHDD.objects.get(nombre='HDD nuevo').velocidad_rpm, 7200)
        self.assertEqual(Gabinete.objects.get(nombre='Gabinete nuevo').largo_max_gpu_mm, 360)
        self.assertEqual(FuenteDePoder.objects.get(nombre='Fuente nueva').potencia_watts, 650)
        self.assertEqual(
            RefrigeracionCooler.objects.get(nombre='Cooler nuevo').socket_compatibles,
            'AM4, AM5, LGA1700',
        )
        self.assertTrue(Ventilador.objects.get(nombre='Fan nuevo').rgb)
        self._assert_compras_intactas()

    def test_los_campos_de_0013_y_0014_viajan_sin_pisar_lo_existente(self):
        marca = Proveedor.objects.create(nombre='Compat Nueva')
        Procesador.objects.create(
            proveedor=marca, nombre='CPU con cooler', precio=Decimal('11.00'), stock=1,
            socket='AM4', nucleos=4, frecuencia_base=Decimal('3.60'),
            incluye_cooler=True, potencia_termica_referencia_watts=95,
        )
        Procesador.objects.create(
            proveedor=marca, nombre='CPU sin dato termico', precio=Decimal('12.00'), stock=1,
            socket='AM5', nucleos=8, frecuencia_base=Decimal('4.00'),
            incluye_cooler=False, potencia_termica_referencia_watts=None,
        )
        Gabinete.objects.create(
            proveedor=marca, nombre='Gabinete alto', precio=Decimal('13.00'), stock=1,
            formato_soporte='ATX', ventiladores_incluidos=False, material='Acero',
            altura_max_cooler_mm=165,
        )
        Gabinete.objects.create(
            proveedor=marca, nombre='Gabinete sin altura', precio=Decimal('14.00'), stock=1,
            formato_soporte='Mini-ITX', ventiladores_incluidos=False, material='Acero',
            altura_max_cooler_mm=None,
        )
        RefrigeracionCooler.objects.create(
            proveedor=marca, nombre='Cooler medido', precio=Decimal('15.00'), stock=1,
            tipo='Aire', socket_compatibles='AM4, AM5',
            disipacion_referencia_watts=180, altura_mm=158,
        )
        RefrigeracionCooler.objects.create(
            proveedor=marca, nombre='Cooler sin medida', precio=Decimal('16.00'), stock=1,
            tipo='Líquida', socket_compatibles='LGA1700',
            disipacion_referencia_watts=None, altura_mm=None,
        )
        PlacaMadre.objects.create(
            proveedor=marca, nombre='Placa con ranuras', precio=Decimal('17.00'), stock=1,
            socket_cpu='AM5', chipset='B650', formato='ATX', ranuras_ram=4,
            tipo_ram_soportado='DDR5',
            ranuras_m2_solo_nvme=2, ranuras_m2_solo_sata=0,
            ranuras_m2_nvme_o_sata=1, puertos_sata=0,
        )
        PlacaMadre.objects.create(
            proveedor=marca, nombre='Placa sin ranuras', precio=Decimal('18.00'), stock=1,
            socket_cpu='AM4', chipset='B550', formato='Micro-ATX', ranuras_ram=2,
            tipo_ram_soportado='DDR4',
            ranuras_m2_solo_nvme=None, ranuras_m2_solo_sata=None,
            ranuras_m2_nvme_o_sata=None, puertos_sata=None,
        )
        AlmacenamientoHDD.objects.create(
            proveedor=marca, nombre='HDD sata', precio=Decimal('19.00'), stock=1,
            capacidad_gb=2000, velocidad_rpm=7200, cache_mb=64,
            interfaz='SATA III', formato='3.5"',
        )
        AlmacenamientoHDD.objects.create(
            proveedor=marca, nombre='HDD sin interfaz', precio=Decimal('21.00'), stock=1,
            capacidad_gb=1000, velocidad_rpm=5400, cache_mb=32,
            interfaz=None, formato=None,
        )
        documento = json.loads(json.dumps(exportar_documento()))
        for producto in documento['productos']:
            if producto['nombre'] == 'CPU vendido':
                producto['campos']['incluye_cooler'] = True
                producto['campos']['potencia_termica_referencia_watts'] = 120
                producto['stock'] = 99
        for modelo in (
            Procesador, Gabinete, RefrigeracionCooler, PlacaMadre, AlmacenamientoHDD,
        ):
            modelo.objects.filter(proveedor=marca).delete()
        marca.delete()

        invalido = json.loads(json.dumps(documento))
        disco = next(item for item in invalido['productos'] if item['nombre'] == 'HDD sata')
        disco['nombre'] = 'HDD interfaz mala'
        disco['campos']['interfaz'] = 'IDE'
        with self.assertRaises(CatalogoMigracionError):
            importar_documento(invalido, apply=True)
        self.assertFalse(AlmacenamientoHDD.objects.filter(nombre='HDD interfaz mala').exists())

        resumen = importar_documento(documento, apply=True)
        self.assertGreaterEqual(resumen['distintos'], 1)
        cpu_si = Procesador.objects.get(nombre='CPU con cooler')
        cpu_no = Procesador.objects.get(nombre='CPU sin dato termico')
        self.assertIs(cpu_si.incluye_cooler, True)
        self.assertEqual(cpu_si.potencia_termica_referencia_watts, 95)
        self.assertIs(cpu_no.incluye_cooler, False)
        self.assertIsNone(cpu_no.potencia_termica_referencia_watts)
        self.assertEqual(Gabinete.objects.get(nombre='Gabinete alto').altura_max_cooler_mm, 165)
        self.assertIsNone(Gabinete.objects.get(nombre='Gabinete sin altura').altura_max_cooler_mm)
        cooler = RefrigeracionCooler.objects.get(nombre='Cooler medido')
        self.assertEqual(cooler.disipacion_referencia_watts, 180)
        self.assertEqual(cooler.altura_mm, 158)
        self.assertIsNone(RefrigeracionCooler.objects.get(nombre='Cooler sin medida').disipacion_referencia_watts)
        self.assertIsNone(RefrigeracionCooler.objects.get(nombre='Cooler sin medida').altura_mm)
        placa = PlacaMadre.objects.get(nombre='Placa con ranuras')
        self.assertEqual(placa.ranuras_m2_solo_nvme, 2)
        self.assertEqual(placa.ranuras_m2_solo_sata, 0)
        self.assertEqual(placa.ranuras_m2_nvme_o_sata, 1)
        self.assertEqual(placa.puertos_sata, 0)
        vacia = PlacaMadre.objects.get(nombre='Placa sin ranuras')
        self.assertIsNone(vacia.ranuras_m2_solo_nvme)
        self.assertIsNone(vacia.puertos_sata)
        disco = AlmacenamientoHDD.objects.get(nombre='HDD sata')
        self.assertEqual(disco.interfaz, 'SATA III')
        self.assertEqual(disco.formato, '3.5"')
        self.assertIsNone(AlmacenamientoHDD.objects.get(nombre='HDD sin interfaz').interfaz)
        self.assertIsNone(AlmacenamientoHDD.objects.get(nombre='HDD sin interfaz').formato)
        self.cpus[2].refresh_from_db()
        self.assertIsNone(self.cpus[2].incluye_cooler)
        self.assertIsNone(self.cpus[2].potencia_termica_referencia_watts)
        self.assertEqual(self.cpus[2].stock, 3)
        self._assert_compras_intactas()
        otra_vez = importar_documento(documento, apply=True)
        self.assertEqual(otra_vez['insertar'], 0)

    def test_la_exportacion_sale_del_repositorio_y_omite_compras(self):
        texto_prohibido = ('SANDBOX-TEST-1', 'comprador@example.com', 'clave-de-prueba', 'Calle 1')
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / 'catalogo.json'
            salida = StringIO()
            call_command('exportar_catalogo', '--salida', str(destino), stdout=salida)
            crudo = destino.read_text(encoding='utf-8')
            call_command('importar_catalogo', '--archivo', str(destino), stdout=StringIO())
        data = json.loads(crudo)
        self.assertEqual(data['formato'], FORMATO)
        claves = set()

        def recorrer(valor):
            if isinstance(valor, dict):
                claves.update(valor)
                for item in valor.values():
                    recorrer(item)
            elif isinstance(valor, list):
                for item in valor:
                    recorrer(item)

        recorrer(data)
        self.assertFalse(claves.intersection({'id', 'pk', 'proveedor_id', 'pedidos', 'usuarios', 'ipn'}))
        for texto in texto_prohibido:
            self.assertNotIn(texto, crudo)
        with self.assertRaises(CommandError):
            call_command(
                'exportar_catalogo',
                '--salida',
                str(Path(settings.BASE_DIR) / 'catalogo_hardwarehouse.json'),
            )

    def test_comandos_dry_run_y_respaldo(self):
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / 'catalogo.json'
            archivo.write_text(
                json.dumps(_documento(['AMD'], [_cpu('AMD', 'Ryzen 3 3100')])),
                encoding='utf-8',
            )
            salida = StringIO()
            call_command('importar_catalogo', '--archivo', str(archivo), stdout=salida)
            self.assertIn('Dry-run', salida.getvalue())
            self.assertFalse(Procesador.objects.filter(nombre='Ryzen 3 3100').exists())
            with self.assertRaises(CommandError):
                call_command('importar_catalogo', '--archivo', str(archivo), '--apply')
            self.assertFalse(Procesador.objects.filter(nombre='Ryzen 3 3100').exists())
            call_command(
                'importar_catalogo',
                '--archivo',
                str(archivo),
                '--apply',
                '--confirmo-respaldo',
                stdout=StringIO(),
            )
        self.assertTrue(Procesador.objects.filter(nombre='Ryzen 3 3100').exists())
        self._assert_compras_intactas()

    def test_normalizacion_de_clave(self):
        self.assertEqual(normalizar_clave(' ÁMD '), normalizar_clave('amd'))
        self.assertEqual(normalizar_clave('ss'), normalizar_clave(' SS '))
