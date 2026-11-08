from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.admin import ItemPedidoInline
from core.models import ItemPedido, Pedido, Procesador, Proveedor


class AdminPedidoDetalleTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser(
            'staff-pedido', 'staff-pedido@example.com', 'clave-admin-pedido',
        )
        comprador = User.objects.create_user('comprador-pedido', 'comprador-pedido@example.com', 'clave-comprador')
        proveedor = Proveedor.objects.create(nombre='Marca pedido')
        self.cpu = Procesador.objects.create(
            proveedor=proveedor, nombre='CPU pedido', precio=Decimal('10000.00'), stock=4,
            socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
        )
        self.pedido = Pedido.objects.create(
            usuario=comprador,
            total_monto=Decimal('99999.00'),
            direccion_envio='Calle de prueba 123',
            estado='PAGADO',
        )
        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            producto_nombre=self.cpu.nombre,
            producto_tipo=self.cpu.categoria,
            precio_unitario=Decimal('10000.00'),
            cantidad=3,
            producto_modelo='procesador',
            producto_pk=self.cpu.pk,
        )
        self.client.force_login(self.staff)
        self.inline = ItemPedidoInline(ItemPedido, admin.site)

    def test_el_detalle_muestra_el_subtotal_real_sin_cambiar_el_total(self):
        respuesta = self.client.get(reverse('admin:core_pedido_change', args=[self.pedido.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, '30000.00')
        self.assertContains(respuesta, 'empty-form')
        self.assertNotContains(respuesta, 'Precio o cantidad inválidos')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.total_monto, Decimal('99999.00'))
        self.assertEqual(self.item.get_subtotal(), Decimal('30000.00'))
        self.assertEqual(self.inline.get_subtotal(self.item), Decimal('30000.00'))

    def test_la_fila_vacia_no_calcula_un_subtotal(self):
        self.assertEqual(self.inline.get_subtotal(ItemPedido()), '')

    def test_un_registro_con_datos_vacios_no_se_reemplaza_por_cero(self):
        invalido = ItemPedido(precio_unitario=None, cantidad=None)
        invalido.pk = self.item.pk

        solo_precio = ItemPedido(precio_unitario=Decimal('10.00'), cantidad=None)
        solo_precio.pk = self.item.pk

        resultado = self.inline.get_subtotal(invalido)

        self.assertEqual(resultado, 'Precio o cantidad inválidos')
        self.assertEqual(self.inline.get_subtotal(solo_precio), 'Precio o cantidad inválidos')
        self.assertNotEqual(resultado, 0)
        with self.assertRaises(TypeError):
            invalido.get_subtotal()
