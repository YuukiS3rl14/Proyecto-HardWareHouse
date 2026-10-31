import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.compatibilidad import evaluar_candidato, validar_armado
from core.models import (
    Carrito,
    Gabinete,
    ItemCarrito,
    Procesador,
    Proveedor,
    RefrigeracionCooler,
)


def pieza(**atributos):
    return SimpleNamespace(**atributos)


class AlturaCoolerTests(TestCase):
    def test_cooler_mas_alto_que_el_gabinete_es_incompatible(self):
        resultado = self._evaluar(165, 155)

        self.assertEqual(resultado.estado, 'incompatible')
        self.assertTrue(resultado.bloquea_agregar)
        self.assertIn(
            'El cooler mide 165 mm y el gabinete admite un máximo de 155 mm.',
            resultado.motivos_de_rechazo,
        )

    def test_cooler_mas_bajo_supera_la_comprobacion(self):
        self._assert_altura_cumplida(150, 155)

    def test_la_altura_igual_al_maximo_supera_la_comprobacion(self):
        self._assert_altura_cumplida(155, 155)

    def test_altura_desconocida_no_se_declara_compatible(self):
        sin_altura = self._evaluar(None, 155)
        sin_maximo = self._evaluar(150, None)
        ambos = self._evaluar(None, None)
        cero = self._evaluar(0, 155)

        for resultado in (sin_altura, sin_maximo, ambos, cero):
            self.assertEqual(resultado.estado, 'datos_insuficientes')
            self.assertTrue(resultado.bloquea_agregar)
            self.assertFalse(resultado.es_compatible)
            texto = ' '.join(resultado.motivos_de_rechazo)
            self.assertIn('No se asume que quepa.', texto)
            self.assertNotIn('El cooler mide', texto)

    def test_el_socket_incompatible_se_sigue_rechazando(self):
        resultado = validar_armado(
            procesador=pieza(socket='AM5'),
            refrigeracion=pieza(tipo='Aire', socket_compatibles='AM4', altura_mm=150),
            gabinete=pieza(altura_max_cooler_mm=155),
        )

        self.assertEqual(resultado.estado, 'incompatible')
        self.assertTrue(resultado.bloquea_agregar)
        texto = ' '.join(resultado.motivos_de_rechazo)
        self.assertIn('El cooler no admite el socket AM5', texto)
        self.assertNotIn('165 mm', texto)

    def test_sin_las_dos_piezas_la_altura_no_se_inventa(self):
        solo_cooler = validar_armado(
            procesador=pieza(socket='AM5'),
            refrigeracion=pieza(tipo='Aire', socket_compatibles='AM5', altura_mm=165),
        )
        solo_gabinete = validar_armado(gabinete=pieza(altura_max_cooler_mm=155, formato_soporte='ATX'))
        liquido = validar_armado(
            procesador=pieza(socket='AM5'),
            refrigeracion=pieza(tipo='Líquida', socket_compatibles='AM5'),
            gabinete=pieza(altura_max_cooler_mm=155),
        )

        self.assertFalse(any(hallazgo.regla == 'altura' for hallazgo in solo_cooler.hallazgos))
        self.assertFalse(any(hallazgo.regla == 'altura' for hallazgo in solo_gabinete.hallazgos))
        self.assertFalse(any(hallazgo.regla == 'altura' for hallazgo in liquido.hallazgos))
        self.assertNotEqual(liquido.estado, 'datos_insuficientes')
        self.assertNotEqual(liquido.estado, 'incompatible')

    def _assert_altura_cumplida(self, altura, maximo):
        resultado = self._evaluar(altura, maximo)
        candidato = self._candidato(altura, maximo)

        self.assertFalse(any(hallazgo.regla == 'altura' for hallazgo in resultado.hallazgos))
        self.assertNotIn('incompatible', [hallazgo.estado for hallazgo in resultado.hallazgos])
        self.assertEqual(candidato.estado, 'compatible')
        self.assertIn(
            f'Cumple la altura del cooler ({altura} mm de {maximo} mm).',
            candidato.coincidencias,
        )

    def _evaluar(self, altura, maximo):
        return validar_armado(
            procesador=pieza(socket='AM5'),
            refrigeracion=pieza(tipo='Aire', socket_compatibles='AM5', altura_mm=altura),
            gabinete=pieza(altura_max_cooler_mm=maximo),
        )

    def _candidato(self, altura, maximo):
        cooler = pieza(tipo='Aire', socket_compatibles='AM5', altura_mm=altura)
        gabinete = pieza(altura_max_cooler_mm=maximo)
        cpu = pieza(socket='AM5')
        return evaluar_candidato(
            'refrigeracion',
            cooler,
            procesador=cpu,
            gabinete=gabinete,
        )


class AlturaCoolerArmadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proveedor = Proveedor.objects.create(nombre='Marca Altura')
        cls.user = User.objects.create_user('altura', 'altura@example.com', 'clave-altura')
        cls.cpu = Procesador.objects.create(
            proveedor=cls.proveedor, nombre='CPU AM5', precio=Decimal('100000'), stock=4,
            socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
        )
        cls.cpu_ajeno = Procesador.objects.create(
            proveedor=cls.proveedor, nombre='CPU LGA1700', precio=Decimal('100000'), stock=4,
            socket='LGA1700', nucleos=6, frecuencia_base=Decimal('3.50'),
        )
        cls.case = Gabinete.objects.create(
            proveedor=cls.proveedor, nombre='Gabinete 155', precio=Decimal('50000'), stock=4,
            formato_soporte='ATX', material='Acero', altura_max_cooler_mm=155,
        )
        cls.cooler_alto = cls._cooler('Cooler 165', 165, 'AM5')
        cls.cooler_bajo = cls._cooler('Cooler 150', 150, 'AM5')
        cls.cooler_exacto = cls._cooler('Cooler 155', 155, 'AM5')
        cls.cooler_sin_dato = cls._cooler('Cooler sin altura', None, 'AM5')
        cls.cooler_socket = cls._cooler('Cooler AM4', 150, 'AM4')

    @classmethod
    def _cooler(cls, nombre, altura, sockets):
        return RefrigeracionCooler.objects.create(
            proveedor=cls.proveedor, nombre=nombre, precio=Decimal('30000'), stock=4,
            tipo='Aire', socket_compatibles=sockets, altura_mm=altura,
        )

    def post(self, url, payload):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def componentes(self, *pares):
        return [{'tipo': tipo, 'id': producto.id} for tipo, producto in pares]

    def test_el_servidor_no_agrega_un_armado_incompatible_por_altura(self):
        self.client.force_login(self.user)
        response = self.post(reverse('core:agregar_armado_al_carrito'), {
            'componentes': self.componentes(
                ('procesador', self.cpu),
                ('refrigeracion', self.cooler_alto),
                ('gabinete', self.case),
            ),
        })

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['estado'], 'incompatible')
        self.assertIn(
            'El cooler mide 165 mm y el gabinete admite un máximo de 155 mm.',
            data['motivos'],
        )
        self.assertEqual(ItemCarrito.objects.count(), 0)
        self.assertEqual(Carrito.objects.count(), 0)

    def test_el_modal_y_el_armado_coinciden(self):
        seleccion = self.componentes(('procesador', self.cpu), ('gabinete', self.case))
        modal = self.post(reverse('core:recomendar_armado'), {
            'categoria': 'refrigeracion_cooler',
            'componentes': seleccion,
        })
        self.assertEqual(modal.status_code, 200)
        por_nombre = {item['nombre']: item for item in modal.json()['candidatos']}

        self.assertEqual(por_nombre['Cooler 165']['estado'], 'incompatible')
        self.assertIn(
            'El cooler mide 165 mm y el gabinete admite un máximo de 155 mm.',
            por_nombre['Cooler 165']['motivos'],
        )
        self.assertEqual(por_nombre['Cooler 150']['estado'], 'compatible')
        self.assertIn('150 mm de 155 mm', ' '.join(por_nombre['Cooler 150']['coincidencias']))
        self.assertEqual(por_nombre['Cooler 155']['estado'], 'compatible')
        self.assertIn('155 mm de 155 mm', ' '.join(por_nombre['Cooler 155']['coincidencias']))
        self.assertEqual(por_nombre['Cooler sin altura']['estado'], 'datos_insuficientes')
        self.assertIn('No se asume que quepa.', ' '.join(por_nombre['Cooler sin altura']['motivos']))
        self.assertEqual(por_nombre['Cooler AM4']['estado'], 'incompatible')
        self.assertIn('AM5', ' '.join(por_nombre['Cooler AM4']['motivos']))

        casos = self.post(reverse('core:recomendar_armado'), {
            'categoria': 'gabinete',
            'componentes': self.componentes(
                ('procesador', self.cpu),
                ('refrigeracion', self.cooler_alto),
            ),
        })
        gabinete = {item['nombre']: item for item in casos.json()['candidatos']}['Gabinete 155']
        self.assertEqual(gabinete['estado'], 'incompatible')
        self.assertIn(
            'El cooler mide 165 mm y el gabinete admite un máximo de 155 mm.',
            gabinete['motivos'],
        )

        for cooler in (
            self.cooler_alto,
            self.cooler_bajo,
            self.cooler_exacto,
            self.cooler_sin_dato,
            self.cooler_socket,
        ):
            evaluacion = self.post(reverse('core:evaluar_armado'), {
                'componentes': self.componentes(
                    ('procesador', self.cpu),
                    ('refrigeracion', cooler),
                    ('gabinete', self.case),
                ),
            })
            self.assertEqual(evaluacion.status_code, 200)
            data = evaluacion.json()
            pieza = data['piezas']['refrigeracion_cooler']
            self.assertEqual(pieza['estado'], por_nombre[cooler.nombre]['estado'])
            self.assertEqual(pieza['motivos'], por_nombre[cooler.nombre]['motivos'])
            self.assertEqual(pieza['coincidencias'], por_nombre[cooler.nombre]['coincidencias'])
            if cooler is self.cooler_socket:
                self.assertEqual(data['estado'], 'incompatible')
                self.assertEqual(data['piezas']['gabinete']['estado'], 'compatible')
            else:
                self.assertEqual(data['piezas']['gabinete']['estado'], pieza['estado'])
                self.assertEqual(data['estado'], pieza['estado'] if pieza['estado'] != 'compatible' else 'incompleto')

    def test_el_navegador_no_recalcula_la_altura(self):
        js = Path(__file__).resolve().parent.joinpath(
            'static', 'core', 'js', 'pc-builder.js',
        ).read_text(encoding='utf-8')
        self.assertNotIn('altura_mm >', js)
        self.assertNotIn('altura_max_cooler_mm <', js)
        self.assertNotIn('function evaluarAltura', js)
        self.assertIn("estado === 'datos_insuficientes'", js)
        self.assertIn('No verificada', js)
