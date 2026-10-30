import json
from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.compatibilidad import LineaDisco, evaluar_candidato, validar_armado
from core.tests import pieza
from core.models import (
    AlmacenamientoHDD,
    AlmacenamientoSSD,
    ItemCarrito,
    PlacaMadre,
    Proveedor,
)


def placa(**extra):
    datos = {
        'ranuras_m2_solo_nvme': 0,
        'ranuras_m2_solo_sata': 0,
        'ranuras_m2_nvme_o_sata': 0,
        'puertos_sata': 0,
    }
    datos.update(extra)
    return SimpleNamespace(**datos)


def ssd(interfaz, formato):
    return SimpleNamespace(interfaz=interfaz, formato=formato)


def hdd(interfaz='SATA III', formato='3.5"'):
    return SimpleNamespace(interfaz=interfaz, formato=formato)


def linea(producto, cantidad, tipo):
    return LineaDisco(producto, cantidad, tipo)


class ReglasAlmacenamientoTests(TestCase):
    def evaluar(self, discos, madre=None):
        return validar_armado(placa_madre=madre, almacenamientos=discos)

    def test_ssd_nvme_cabe_y_no_rechaza_pcie_4_ni_3(self):
        madre = placa(ranuras_m2_solo_nvme=2)
        discos = [
            linea(ssd('NVMe PCIe 4.0', 'M.2 2280'), 1, 'almacenamiento_ssd'),
            linea(ssd('NVMe PCIe 3.0', 'M.2 2280'), 1, 'almacenamiento_ssd'),
        ]
        resultado = self.evaluar(discos, madre)
        self.assertEqual(resultado.almacenamiento.estado, 'compatible')
        self.assertFalse(resultado.bloquea_agregar)
        self.assertNotIn(resultado.estado, ('incompatible', 'datos_insuficientes'))
        self.assertIn('No se compara PCIe 3.0 con PCIe 4.0', resultado.almacenamiento.coincidencias[0])

    def test_ssd_nvme_sin_ranura_es_incompatible(self):
        resultado = self.evaluar(
            [linea(ssd('NVMe PCIe 4.0', 'M.2 2280'), 1, 'almacenamiento_ssd')],
            placa(),
        )
        self.assertEqual(resultado.estado, 'incompatible')
        self.assertTrue(resultado.bloquea_agregar)
        self.assertIn('SSD NVMe', resultado.motivos_de_rechazo[0])

    def test_ssd_m2_sata_compatible_e_incompatible(self):
        disco = [linea(ssd('SATA III', 'M.2 2280'), 1, 'almacenamiento_ssd')]
        cabe = self.evaluar(disco, placa(ranuras_m2_solo_sata=1))
        self.assertEqual(cabe.almacenamiento.estado, 'compatible')
        self.assertNotIn('PCIe', cabe.almacenamiento.coincidencias[0])
        no_cabe = self.evaluar(disco, placa(ranuras_m2_solo_nvme=2, puertos_sata=4))
        self.assertEqual(no_cabe.estado, 'incompatible')
        self.assertIn('M.2 SATA', no_cabe.motivos_de_rechazo[0])

    def test_ssd_sata_de_2_5_usa_puerto_sata(self):
        disco = [linea(ssd('SATA III', '2.5"'), 1, 'almacenamiento_ssd')]
        self.assertEqual(self.evaluar(disco, placa(puertos_sata=1)).almacenamiento.estado, 'compatible')
        self.assertEqual(self.evaluar(disco, placa(ranuras_m2_solo_nvme=4)).estado, 'incompatible')

    def test_hdd_sata_usa_puerto_sata(self):
        disco = [linea(hdd(), 1, 'almacenamiento_hdd')]
        self.assertEqual(self.evaluar(disco, placa(puertos_sata=1)).almacenamiento.estado, 'compatible')
        self.assertIn('puertos SATA', self.evaluar(disco, placa()).motivos_de_rechazo[0])

    def test_varias_unidades_no_superan_los_puertos(self):
        discos = [
            linea(ssd('SATA III', '2.5"'), 2, 'almacenamiento_ssd'),
            linea(hdd(), 1, 'almacenamiento_hdd'),
        ]
        self.assertEqual(self.evaluar(discos, placa(puertos_sata=2)).estado, 'incompatible')
        self.assertEqual(self.evaluar(discos, placa(puertos_sata=3)).almacenamiento.estado, 'compatible')

    def test_la_ranura_m2_compartida_no_se_cuenta_dos_veces(self):
        madre = placa(ranuras_m2_nvme_o_sata=1)
        uno = [
            linea(ssd('NVMe PCIe 4.0', 'M.2 2280'), 1, 'almacenamiento_ssd'),
        ]
        self.assertEqual(self.evaluar(uno, madre).almacenamiento.estado, 'compatible')
        ambos = uno + [linea(ssd('SATA III', 'M.2 2280'), 1, 'almacenamiento_ssd')]
        conflicto = self.evaluar(ambos, madre)
        self.assertEqual(conflicto.estado, 'incompatible')
        self.assertIn('compartidas', conflicto.motivos_de_rechazo[0])
        alcanza = self.evaluar(ambos, placa(ranuras_m2_solo_nvme=1, ranuras_m2_nvme_o_sata=1))
        self.assertEqual(alcanza.almacenamiento.estado, 'compatible')

    def test_sin_datos_tecnicos_sigue_sin_evaluarse_y_no_bloquea(self):
        antiguo = [linea(hdd(interfaz=None, formato=None), 1, 'almacenamiento_hdd')]
        resultado = self.evaluar(antiguo, placa(puertos_sata=4, ranuras_m2_solo_nvme=2))
        self.assertEqual(resultado.almacenamiento.estado, 'no_evaluada')
        self.assertIn('interfaz', resultado.almacenamiento.motivos[0])
        self.assertNotIn('SATA', resultado.almacenamiento.motivos[0])
        self.assertNotIn(resultado.estado, ('incompatible', 'datos_insuficientes'))
        self.assertFalse(resultado.bloquea_agregar)

        sin_placa = self.evaluar(
            [linea(ssd('NVMe PCIe 4.0', 'M.2 2280'), 2, 'almacenamiento_ssd')],
        )
        self.assertEqual(sin_placa.almacenamiento.estado, 'no_evaluada')
        self.assertIn('placa madre', sin_placa.almacenamiento.motivos[0])
        self.assertFalse(sin_placa.bloquea_agregar)

        placa_vieja = SimpleNamespace()
        desconocida = self.evaluar(
            [linea(ssd('NVMe PCIe 4.0', 'M.2 2280'), 1, 'almacenamiento_ssd')],
            placa_vieja,
        )
        self.assertEqual(desconocida.almacenamiento.estado, 'no_evaluada')
        self.assertIn('ranuras M.2', desconocida.almacenamiento.motivos[0])
        self.assertFalse(desconocida.bloquea_agregar)

    def test_hdd_con_otra_interfaz_no_se_trata_como_sata(self):
        disco = [linea(hdd(interfaz='SAS', formato='3.5"'), 1, 'almacenamiento_hdd')]
        resultado = self.evaluar(disco, placa(
            puertos_sata=4,
            ranuras_m2_solo_nvme=0,
            ranuras_m2_solo_sata=0,
            ranuras_m2_nvme_o_sata=0,
        ))
        self.assertEqual(resultado.almacenamiento.estado, 'no_evaluada')
        self.assertIn('SAS', resultado.almacenamiento.motivos[0])
        self.assertFalse(resultado.bloquea_agregar)
        self.assertNotEqual(resultado.estado, 'incompatible')

    def test_ssd_sata_sin_puertos_registrados_nombra_el_dato(self):
        disco = [linea(ssd('SATA III', '2.5"'), 1, 'almacenamiento_ssd')]
        resultado = self.evaluar(disco, placa(
            ranuras_m2_solo_nvme=1,
            ranuras_m2_solo_sata=0,
            ranuras_m2_nvme_o_sata=0,
            puertos_sata=None,
        ))
        self.assertEqual(resultado.almacenamiento.estado, 'no_evaluada')
        self.assertIn('puertos SATA', resultado.almacenamiento.motivos[0])
        self.assertFalse(resultado.bloquea_agregar)

    def test_una_placa_sin_otras_piezas_no_es_incompatible(self):
        evaluacion = evaluar_candidato(
            'placa_madre',
            pieza(socket_cpu='AM5', tipo_ram_soportado='DDR4', formato='ATX'),
        )
        self.assertEqual(evaluacion.estado, 'incompleto')
        self.assertFalse(evaluacion.motivos)


class CarritoAlmacenamientoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        marca = Proveedor.objects.create(nombre='Marca almacenamiento')
        cls.user = User.objects.create_user('discos-placa', 'discos-placa@example.com', 'clave-discos')
        cls.nvme = AlmacenamientoSSD.objects.create(
            proveedor=marca, nombre='SSD NVMe prueba', precio=Decimal('10000'), stock=5,
            capacidad_gb=1000, interfaz='NVMe PCIe 4.0', formato='M.2 2280',
        )
        cls.hdd_viejo = AlmacenamientoHDD.objects.create(
            proveedor=marca, nombre='HDD sin interfaz', precio=Decimal('5000'), stock=5,
            capacidad_gb=2000, velocidad_rpm=7200, cache_mb=64,
        )
        cls.placa_sin_datos = PlacaMadre.objects.create(
            proveedor=marca, nombre='Placa sin puertos', precio=Decimal('20000'), stock=5,
            socket_cpu='AM5', chipset='B650', formato='ATX', ranuras_ram=4,
            tipo_ram_soportado='DDR5',
        )
        cls.placa_sin_nvme = PlacaMadre.objects.create(
            proveedor=marca, nombre='Placa sin NVMe', precio=Decimal('20000'), stock=5,
            socket_cpu='AM5', chipset='B650', formato='ATX', ranuras_ram=4,
            tipo_ram_soportado='DDR5',
            ranuras_m2_solo_nvme=0, ranuras_m2_solo_sata=0,
            ranuras_m2_nvme_o_sata=0, puertos_sata=4,
        )
        cls.placa_con_nvme = PlacaMadre.objects.create(
            proveedor=marca, nombre='Placa con NVMe', precio=Decimal('20000'), stock=5,
            socket_cpu='AM5', chipset='B650', formato='ATX', ranuras_ram=4,
            tipo_ram_soportado='DDR5',
            ranuras_m2_solo_nvme=1, ranuras_m2_solo_sata=0,
            ranuras_m2_nvme_o_sata=0, puertos_sata=4,
        )

    def setUp(self):
        self.client.login(username='discos-placa', password='clave-discos')

    def post(self, url, componentes):
        return self.client.post(
            url,
            data=json.dumps({'componentes': componentes}),
            content_type='application/json',
        )

    def test_un_armado_viejo_con_disco_sigue_pudiendo_entrar_al_carrito(self):
        response = self.post(reverse('core:agregar_armado_al_carrito'), [
            {'tipo': 'placa_madre', 'id': self.placa_sin_datos.id},
            {'tipo': 'almacenamiento_hdd', 'id': self.hdd_viejo.id, 'cantidad': 1},
            {'tipo': 'almacenamiento_ssd', 'id': self.nvme.id, 'cantidad': 1},
        ])
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['estado'] in ('incompatible', 'datos_insuficientes'))
        self.assertEqual(ItemCarrito.objects.count(), 3)

    def test_nvme_en_placa_sin_ranura_no_entra_al_carrito(self):
        response = self.post(reverse('core:agregar_armado_al_carrito'), [
            {'tipo': 'placa_madre', 'id': self.placa_sin_nvme.id},
            {'tipo': 'almacenamiento_ssd', 'id': self.nvme.id, 'cantidad': 1},
        ])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['estado'], 'incompatible')
        self.assertEqual(ItemCarrito.objects.count(), 0)

        evaluacion = self.post(reverse('core:evaluar_armado'), [
            {'tipo': 'placa_madre', 'id': self.placa_con_nvme.id},
            {'tipo': 'almacenamiento_ssd', 'id': self.nvme.id, 'cantidad': 1},
        ]).json()
        self.assertEqual(evaluacion['piezas']['almacenamiento']['estado'], 'compatible')
        self.assertIn('PCIe', evaluacion['piezas']['almacenamiento']['etiqueta'])
