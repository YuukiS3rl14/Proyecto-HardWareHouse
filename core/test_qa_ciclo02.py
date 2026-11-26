"""Escenarios de UT-04, UT-05 y UT-06 que no estaban aislados en los tests previos."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.alertas_stock import ADVERTENCIA, AGOTADO, CRITICO, NORMAL, _filas, estado_stock, resumen
from core.cantidad_carrito import (
    MENSAJE_ENTERO,
    MENSAJE_MINIMO,
    MENSAJE_SIN_STOCK,
    CantidadInvalida,
    mensaje_stock,
    parsear_cantidad,
)
from core.inventario import guardar_umbrales
from core.models import Carrito, ItemCarrito, Procesador, Proveedor


def cpu(marca, nombre, precio, stock, **extra):
    datos = dict(
        proveedor=marca,
        nombre=nombre,
        precio=precio,
        stock=stock,
        socket='AM5',
        nucleos=6,
        frecuencia_base=Decimal('3.50'),
    )
    datos.update(extra)
    return Procesador.objects.create(**datos)


class Ut04TotalesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('totales', 'totales@example.com', 'clave-totales')
        self.client.force_login(self.usuario)
        self.marca = Proveedor.objects.create(nombre='Marca Totales')
        self.agregar = reverse('core:agregar_al_carrito')

    def post_agregar(self, producto, quantity='1'):
        return self.client.post(self.agregar, {
            'product_id': producto.id,
            'model_name': 'procesador',
            'quantity': quantity,
            'precio': '1',
            'total': '1',
        })

    def test_ut04_totales_oferta_decimales_y_un_solo_descuento(self):
        simple = cpu(self.marca, 'CPU lista', Decimal('19990.00'), 5)
        self.post_agregar(simple, '1')
        item = ItemCarrito.objects.get(procesador=simple)
        self.assertEqual(item.cantidad, 1)
        self.assertEqual(item.precio_unitario, Decimal('19990.00'))
        self.assertEqual(item.get_total(), Decimal('19990.00'))

        otra = cpu(self.marca, 'CPU pack', Decimal('10000.00'), 8)
        self.post_agregar(simple, '1')
        self.post_agregar(otra, '3')
        item.refresh_from_db()
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(item.get_total(), Decimal('39980.00'))
        pack = ItemCarrito.objects.get(procesador=otra)
        self.assertEqual(pack.get_total(), Decimal('30000.00'))
        carrito = Carrito.objects.get(usuario=self.usuario)
        self.assertEqual(carrito.get_total_precio(), Decimal('69980.00'))

        oferta = cpu(
            self.marca, 'CPU oferta', Decimal('200.00'), 6,
            en_oferta=True, precio_oferta=Decimal('133.00'),
        )
        self.assertEqual(oferta.precio_vigente, Decimal('133.00'))
        self.assertEqual(oferta.porcentaje_descuento, 34)
        self.post_agregar(oferta, '2')
        linea_oferta = ItemCarrito.objects.get(procesador=oferta)
        self.assertEqual(linea_oferta.precio_unitario, Decimal('133.00'))
        self.assertEqual(linea_oferta.get_total(), Decimal('266.00'))
        self.assertNotEqual(linea_oferta.get_total(), Decimal('132.00'))

        decimal = cpu(self.marca, 'CPU decimal', Decimal('10.10'), 4)
        self.post_agregar(decimal, '3')
        linea_decimal = ItemCarrito.objects.get(procesador=decimal)
        self.assertEqual(linea_decimal.get_total(), Decimal('30.30'))

        centavos = cpu(self.marca, 'CPU centavos', Decimal('0.10'), 2)
        otro_centavo = cpu(self.marca, 'CPU dos centavos', Decimal('0.20'), 2)
        self.post_agregar(centavos, '1')
        self.post_agregar(otro_centavo, '1')
        carrito.refresh_from_db()
        self.assertEqual(
            carrito.get_total_precio(),
            Decimal('19990.00') * 2 + Decimal('30000.00') + Decimal('266.00') + Decimal('30.30') + Decimal('0.30'),
        )

        self.client.post(
            reverse('core:actualizar_carrito', args=[item.id]),
            {'quantity': '4', 'precio_unitario': '1', 'total': '1'},
        )
        item.refresh_from_db()
        self.assertEqual(item.cantidad, 4)
        self.assertEqual(item.precio_unitario, Decimal('19990.00'))
        self.assertEqual(item.get_total(), Decimal('79960.00'))

        self.post_agregar(oferta, '1')
        linea_oferta.refresh_from_db()
        self.assertEqual(linea_oferta.cantidad, 3)
        self.assertEqual(linea_oferta.precio_unitario, Decimal('133.00'))
        self.assertEqual(linea_oferta.get_total(), Decimal('399.00'))


class Ut05LimitesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('limites', 'limites@example.com', 'clave-limites')
        self.client.force_login(self.usuario)
        self.marca = Proveedor.objects.create(nombre='Marca Limites')
        self.cpu = cpu(self.marca, 'CPU limite', Decimal('5000.00'), 3)
        self.agregar = reverse('core:agregar_al_carrito')

    def post(self, quantity, producto=None):
        producto = producto or self.cpu
        return self.client.post(self.agregar, {
            'product_id': producto.id,
            'model_name': 'procesador',
            'quantity': quantity,
            'precio': '1',
            'total': '999',
        })

    def test_ut05_rechaza_invalidas_y_acepta_el_stock_exacto(self):
        casos = (
            ('0', MENSAJE_MINIMO),
            ('-1', MENSAJE_ENTERO),
            ('abc', MENSAJE_ENTERO),
            ('1.5', MENSAJE_ENTERO),
            ('4', mensaje_stock(3)),
        )
        for valor, mensaje in casos:
            with self.assertRaises(CantidadInvalida) as error:
                parsear_cantidad(valor, 3)
            self.assertEqual(error.exception.mensaje, mensaje)
            self.post(valor)
            self.assertEqual(ItemCarrito.objects.count(), 0)
        self.cpu.refresh_from_db()
        self.assertEqual(self.cpu.stock, 3)

        self.assertEqual(parsear_cantidad('3', 3), 3)
        self.assertEqual(parsear_cantidad('2', 3), 2)
        self.post('3')
        item = ItemCarrito.objects.get()
        self.assertEqual(item.cantidad, 3)
        self.assertEqual(item.get_total(), Decimal('15000.00'))
        self.cpu.refresh_from_db()
        self.assertEqual(self.cpu.stock, 3)

        agotado = cpu(self.marca, 'CPU agotada', Decimal('1000.00'), 0)
        with self.assertRaises(CantidadInvalida) as error:
            parsear_cantidad('1', 0)
        self.assertEqual(error.exception.mensaje, MENSAJE_SIN_STOCK)
        self.post('1', agotado)
        self.assertEqual(ItemCarrito.objects.filter(procesador=agotado).count(), 0)
        agotado.refresh_from_db()
        self.assertEqual(agotado.stock, 0)
        item.refresh_from_db()
        self.assertEqual(item.cantidad, 3)


class Ut06EstadosTests(TestCase):
    def setUp(self):
        self.marca = Proveedor.objects.create(nombre='Marca Estados')
        self.staff = User.objects.create_user(
            'estados', 'estados@example.com', 'clave-estados', is_staff=True,
        )

    def test_ut06_clasifica_umbrales_y_contadores_sin_duplicar(self):
        esperados = (
            (0, AGOTADO),
            (1, CRITICO),
            (3, CRITICO),
            (4, ADVERTENCIA),
            (5, ADVERTENCIA),
            (6, NORMAL),
        )
        piezas = []
        for stock, estado in esperados:
            pieza = cpu(self.marca, f'Pieza {stock}', Decimal('1000'), stock)
            self.assertEqual(estado_stock(pieza.stock, 3, 5), estado)
            self.assertEqual(
                [estado_stock(pieza.stock, 3, 5) == candidato for candidato in (AGOTADO, CRITICO, ADVERTENCIA, NORMAL)].count(True),
                1,
            )
            piezas.append(pieza)

        filas = _filas()
        nombres = [fila.nombre for fila in filas]
        self.assertNotIn('Pieza 6', nombres)
        self.assertEqual(len(filas), 5)
        self.assertEqual(len({(fila.modelo, fila.pk) for fila in filas}), 5)
        self.assertEqual(resumen(filas), {
            'agotados': 1,
            'criticos': 2,
            'advertencia': 2,
            'afectados': 5,
        })

        propia = piezas[3]
        self.assertEqual(estado_stock(4, 2, 4), ADVERTENCIA)
        self.assertEqual(estado_stock(2, 2, 4), CRITICO)
        self.assertEqual(estado_stock(5, 2, 4), NORMAL)
        guardar_umbrales(propia, 4, 6, self.staff)
        propia.refresh_from_db()
        self.assertEqual(estado_stock(propia.stock, propia.stock_minimo, propia.stock_advertencia), CRITICO)
        filas = _filas()
        fila = next(item for item in filas if item.pk == propia.pk)
        self.assertEqual(fila.estado, CRITICO)
        self.assertEqual(len([item for item in filas if item.pk == propia.pk]), 1)
