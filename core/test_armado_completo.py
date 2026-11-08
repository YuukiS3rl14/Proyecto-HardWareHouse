import json
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
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


class ArmadoCompletoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proveedor = Proveedor.objects.create(nombre='Marca armado completo')
        cls.user = User.objects.create_user('armado', 'armado@example.com', 'clave-armado')
        cls.cpu = cls._cpu()
        cls.cpu_video = cls._cpu(nombre='CPU con video', graficos_integrados=True)
        cls.cpu_sin_watts = cls._cpu(nombre='CPU sin watts', potencia_referencia_watts=None)
        cls.placa = cls._placa()
        cls.placa_video = cls._placa(nombre='Placa con video', tiene_salidas_video=True)
        cls.placa_ajena = cls._placa(nombre='Placa LGA1700', socket_cpu='LGA1700', chipset='B560')
        cls.ram = cls._ram()
        cls.gpu = cls._gpu()
        cls.gpu_sin_largo = cls._gpu(nombre='GPU sin largo', largo_mm=None, consumo_referencia_watts=100)
        cls.gabinete = cls._gabinete()
        cls.fuente = cls._fuente()
        cls.ssd = cls._ssd()
        cls.ssd_sin_placa = cls._ssd(nombre='SSD de la placa ciega')

    @classmethod
    def _cpu(cls, nombre='CPU completa', potencia_referencia_watts=65, graficos_integrados=None):
        return Procesador.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=Decimal('90000'), stock=4,
            socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
            potencia_referencia_watts=potencia_referencia_watts,
            graficos_integrados=graficos_integrados,
        )

    @classmethod
    def _placa(cls, nombre='Placa completa', socket_cpu='AM5', chipset='B650', tiene_salidas_video=None):
        return PlacaMadre.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=Decimal('80000'), stock=4,
            socket_cpu=socket_cpu, chipset=chipset, formato='ATX', ranuras_ram=4,
            tipo_ram_soportado='DDR5', formato_ram_soportado='DIMM', capacidad_maxima_ram_gb=128,
            tiene_salidas_video=tiene_salidas_video,
        )

    @classmethod
    def _ram(cls):
        return MemoriaRam.objects.create(
            proveedor=cls.proveedor, nombre='RAM completa', precio=Decimal('20000'), stock=4,
            capacidad_gb=16, tipo_ddr='DDR5', velocidad_mhz=5600,
            modulos_por_producto=1, capacidad_modulo_gb=16, formato_ram='DIMM',
        )

    @classmethod
    def _gpu(cls, nombre='GPU completa', largo_mm=200, consumo_referencia_watts=100):
        return TarjetaGrafica.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=Decimal('100000'), stock=4,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
            consumo_referencia_watts=consumo_referencia_watts, largo_mm=largo_mm,
        )

    @classmethod
    def _gabinete(cls):
        return Gabinete.objects.create(
            proveedor=cls.proveedor, nombre='Gabinete completo', precio=Decimal('40000'), stock=4,
            formato_soporte='ATX', material='Acero', largo_max_gpu_mm=320,
        )

    @classmethod
    def _fuente(cls, watts=650):
        return FuenteDePoder.objects.create(
            proveedor=cls.proveedor, nombre=f'Fuente {watts}', precio=Decimal('50000'), stock=4,
            potencia_watts=watts, certificacion='80+ Bronze',
        )

    @classmethod
    def _ssd(cls, nombre='SSD completo'):
        return AlmacenamientoSSD.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=Decimal('20000'), stock=4,
            capacidad_gb=1000, interfaz='NVMe PCIe 4.0', formato='M.2 2280',
        )

    def setUp(self):
        self.client.force_login(self.user)

    def piezas(self, **cambios):
        base = {
            'procesador': self.cpu,
            'placa_madre': self.placa,
            'memoria_ram': self.ram,
            'tarjeta_grafica': self.gpu,
            'gabinete': self.gabinete,
            'fuente_de_poder': self.fuente,
            'almacenamiento_ssd': self.ssd,
        }
        base.update(cambios)
        return [
            {'tipo': tipo, 'id': producto.id}
            for tipo, producto in base.items()
            if producto is not None
        ]

    def post_armado(self, componentes):
        return self.client.post(
            reverse('core:agregar_armado_al_carrito'),
            data=json.dumps({'componentes': componentes}),
            content_type='application/json',
        )

    def test_sin_almacenamiento_no_entra_al_carrito(self):
        respuesta = self.post_armado(self.piezas(almacenamiento_ssd=None))

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()['estado'], 'incompleto')
        self.assertEqual(respuesta.json()['message'], 'Faltan componentes por seleccionar.')
        self.assertIn('Almacenamiento', respuesta.json()['faltantes'])
        self.assertEqual(ItemCarrito.objects.count(), 0)
        self.assertEqual(Carrito.objects.count(), 0)

    def test_sin_placa_madre_no_entra_al_carrito(self):
        respuesta = self.post_armado(self.piezas(placa_madre=None))

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('Placa Madre', respuesta.json()['faltantes'])
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_sin_ram_no_entra_al_carrito(self):
        respuesta = self.post_armado(self.piezas(memoria_ram=None))

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('Memoria RAM', respuesta.json()['faltantes'])
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_el_armado_completo_compatible_entra_sin_cooler(self):
        respuesta = self.post_armado(self.piezas())

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['faltantes'] if 'faltantes' in respuesta.json() else [], [])
        self.assertEqual(ItemCarrito.objects.count(), 7)
        self.assertFalse(ItemCarrito.objects.filter(refrigeracion__isnull=False).exists())
        self.cpu.refresh_from_db()
        self.assertEqual(self.cpu.stock, 4)

    def test_el_armado_incompatible_no_guarda_nada(self):
        respuesta = self.post_armado(self.piezas(placa_madre=self.placa_ajena))

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()['estado'], 'incompatible')
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_los_datos_insuficientes_siguen_bloqueando(self):
        respuesta = self.post_armado(self.piezas(
            procesador=self.cpu_sin_watts,
            tarjeta_grafica=self.gpu_sin_largo,
        ))

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()['estado'], 'datos_insuficientes')
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_el_almacenamiento_no_verificado_sigue_pudiendo_comprarse(self):
        placa = self._placa(nombre='Placa sin conteos M.2')
        respuesta = self.post_armado(self.piezas(placa_madre=placa, almacenamiento_ssd=self.ssd_sin_placa))

        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn(respuesta.json()['estado'], ('incompatible', 'datos_insuficientes'))
        self.assertTrue(ItemCarrito.objects.filter(almacenamiento_ssd=self.ssd_sin_placa).exists())

    def test_una_solicitud_incompleta_directa_no_agrega_parcialmente(self):
        respuesta = self.post_armado([
            {'tipo': 'procesador', 'id': self.cpu.id},
            {'tipo': 'fuente_de_poder', 'id': self.fuente.id},
        ])

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()['message'], 'Faltan componentes por seleccionar.')
        self.assertIn('Falta Placa Madre.', respuesta.json()['motivos'])
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_la_compra_individual_no_exige_el_armado_completo(self):
        respuesta = self.client.post(reverse('core:agregar_al_carrito'), {
            'product_id': self.ssd.id,
            'model_name': 'almacenamiento_ssd',
            'quantity': 1,
        })

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(ItemCarrito.objects.get().almacenamiento_ssd_id, self.ssd.id)

    def test_el_video_integrado_confirmado_no_exige_gpu(self):
        respuesta = self.post_armado(self.piezas(
            procesador=self.cpu_video,
            placa_madre=self.placa_video,
            tarjeta_grafica=None,
        ))

        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        self.assertFalse(ItemCarrito.objects.filter(tarjeta_grafica__isnull=False).exists())
        self.assertGreater(ItemCarrito.objects.count(), 0)

    def test_sin_video_confirmado_la_gpu_sigue_siendo_obligatoria(self):
        respuesta = self.post_armado(self.piezas(tarjeta_grafica=None))

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('Tarjeta Gráfica (GPU)', respuesta.json()['faltantes'])
        self.assertEqual(ItemCarrito.objects.count(), 0)

    def test_la_evaluacion_informa_los_faltantes_sin_borrar_la_seleccion(self):
        respuesta = self.client.post(
            reverse('core:evaluar_armado'),
            data=json.dumps({'componentes': [{'tipo': 'procesador', 'id': self.cpu.id}]}),
            content_type='application/json',
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('Almacenamiento', respuesta.json()['faltantes'])
        self.assertIn('Placa Madre', respuesta.json()['faltantes'])
        pagina = self.client.get(reverse('core:armado'))
        self.assertContains(pagina, 'pc-builder.js?v=selector20')
        js = Path(__file__).resolve().parent.joinpath(
            'static', 'core', 'js', 'pc-builder.js',
        ).read_text(encoding='utf-8')
        self.assertIn('mostrarFaltantes', js)
        self.assertIn('Faltan componentes por seleccionar.', js)
        self.assertIn('Ver componentes faltantes', js)
        self.assertIn('addToCartBtn.disabled = true', js)
