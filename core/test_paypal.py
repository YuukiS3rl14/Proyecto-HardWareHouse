from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode
from paypal.standard.ipn.models import PayPalIPN

from core.models import Carrito, ItemCarrito, ItemPedido, PagoBoleta, Pedido, Procesador, Proveedor
from core.payments import clp_a_usd, confirmar_pago_paypal

RECEPTOR = 'sb-merchant@business.example.com'
SITIO = 'https://proyecto-hardwarehouse-production.up.railway.app'


@override_settings(PAYPAL_TEST=True, PAYPAL_RECEIVER_EMAIL=RECEPTOR, CLP_TO_USD_RATE=950)
class PayPalSandboxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('comprador', 'comprador@example.com', 'clave-paypal-123')
        cls.proveedor = Proveedor.objects.create(nombre='Marca PayPal')
        cls.cpu = Procesador.objects.create(
            proveedor=cls.proveedor, nombre='CPU Sandbox', precio=Decimal('95000'), stock=5,
            socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
        )
        cls.ram = Procesador.objects.create(
            proveedor=cls.proveedor, nombre='CPU secundaria', precio=Decimal('9500'), stock=4,
            socket='AM4', nucleos=4, frecuencia_base=Decimal('3.20'),
        )

    def setUp(self):
        self.cpu.refresh_from_db()
        self.ram.refresh_from_db()

    def pedido(self, cantidad=2, stock=5, estado='PENDIENTE', producto=None, enlazado=True):
        producto = producto or self.cpu
        producto.stock = stock
        producto.save(update_fields=['stock'])
        total = producto.precio * cantidad
        pedido = Pedido.objects.create(
            usuario=self.user,
            estado=estado,
            total_monto=total,
            direccion_envio='Por definir',
        )
        ItemPedido.objects.create(
            pedido=pedido,
            producto_nombre=producto.nombre,
            producto_tipo=producto.categoria,
            precio_unitario=producto.precio,
            cantidad=cantidad,
            producto_modelo='procesador' if enlazado else '',
            producto_pk=producto.pk if enlazado else None,
        )
        return pedido

    def notificar(self, pedido, txn_id='TXN-OK', verificado=b'VERIFIED', **cambios):
        datos = {
            'payment_status': 'Completed',
            'txn_id': txn_id,
            'invoice': str(pedido.id) if pedido is not None else '999999',
            'mc_gross': f'{clp_a_usd(pedido.total_monto):.2f}' if pedido is not None else '10.00',
            'mc_currency': 'USD',
            'receiver_email': RECEPTOR,
            'business': RECEPTOR,
            'payer_email': 'sb-buyer@personal.example.com',
            'first_name': 'Sandbox',
            'last_name': 'Buyer',
            'test_ipn': '1',
            'charset': 'utf-8',
        }
        if cambios.pop('omitir_test_ipn', False):
            datos.pop('test_ipn', None)
        datos.update(cambios)
        cuerpo = urlencode(datos)
        with patch('paypal.standard.ipn.models.PayPalIPN._postback', return_value=verificado):
            return self.client.post(
                reverse('paypal-ipn'),
                cuerpo,
                content_type='application/x-www-form-urlencoded',
            )

    def test_el_checkout_abre_el_sandbox_y_deja_el_pedido_pendiente(self):
        self.cpu.stock = 5
        self.cpu.save(update_fields=['stock'])
        carrito = Carrito.objects.create(usuario=self.user)
        ItemCarrito.objects.create(
            carrito=carrito, procesador=self.cpu, cantidad=2, precio_unitario=self.cpu.precio,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:checkout'))

        pedido = Pedido.objects.get(usuario=self.user)
        item = pedido.items_pedido.get()
        self.cpu.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)
        self.assertEqual(item.producto_modelo, 'procesador')
        self.assertEqual(item.producto_pk, self.cpu.pk)
        self.assertContains(response, 'https://www.sandbox.paypal.com/cgi-bin/webscr')
        self.assertContains(response, RECEPTOR)
        self.assertContains(response, '/paypal/')
        self.assertFalse(PagoBoleta.objects.exists())

    def test_el_regreso_de_paypal_no_marca_el_pedido_como_pagado(self):
        pedido = self.pedido()
        self.client.force_login(self.user)

        exito = self.client.get(reverse('core:payment_success'))
        fallo = self.client.get(reverse('core:payment_failed'))
        self.assertContains(exito, 'sigue pendiente')
        self.assertContains(fallo, 'no se descontó stock')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())

    def test_un_pago_confirmado_guarda_la_transaccion_y_descuenta_el_stock(self):
        pedido = self.pedido(cantidad=2, stock=5)

        response = self.notificar(pedido, txn_id='TXN-PAGADO')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        ipn = PayPalIPN.objects.get(txn_id='TXN-PAGADO')
        boleta = pedido.pago_boleta
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'OKAY')
        self.assertFalse(ipn.flag)
        self.assertEqual(ipn.payment_status, 'Completed')
        self.assertEqual(ipn.invoice, str(pedido.id))
        self.assertEqual(ipn.mc_gross, Decimal('200.00'))
        self.assertEqual(ipn.receiver_email, RECEPTOR)
        self.assertTrue(ipn.test_ipn)
        self.assertEqual(pedido.estado, 'PAGADO')
        self.assertEqual(pedido.paypal_transaccion_id, 'TXN-PAGADO')
        self.assertEqual(boleta.transaccion_id, 'TXN-PAGADO')
        self.assertEqual(boleta.monto_pagado, Decimal('190000.00'))
        self.assertEqual(boleta.metodo_pago, 'PayPal')
        self.assertEqual(boleta.email_comprador, 'sb-buyer@personal.example.com')
        self.assertEqual(boleta.nombre_comprador, 'Sandbox Buyer')
        self.assertEqual(self.cpu.stock, 3)

    def test_un_callback_duplicado_no_vuelve_a_descontar_stock(self):
        pedido = self.pedido(cantidad=2, stock=5)
        ipn = PayPalIPN.objects.create(
            payment_status='Completed',
            txn_id='TXN-DOS',
            invoice=str(pedido.id),
            mc_gross=clp_a_usd(pedido.total_monto),
            mc_currency='USD',
            receiver_email=RECEPTOR,
            test_ipn=True,
            payer_email='sb-buyer@personal.example.com',
            first_name='Sandbox',
            last_name='Buyer',
        )

        self.assertEqual(confirmar_pago_paypal(ipn), 'pagado')
        self.assertEqual(confirmar_pago_paypal(ipn), 'ya_procesado')
        self.notificar(pedido, txn_id='TXN-DOS')

        self.cpu.refresh_from_db()
        pedido.refresh_from_db()
        self.assertEqual(self.cpu.stock, 3)
        self.assertEqual(pedido.estado, 'PAGADO')
        self.assertEqual(PagoBoleta.objects.filter(transaccion_id='TXN-DOS').count(), 1)

    def test_un_pago_pendiente_no_cobra_y_el_completed_posterior_si(self):
        pedido = self.pedido(cantidad=2, stock=5)

        self.notificar(pedido, txn_id='TXN-PEND', payment_status='Pending')
        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())

        self.notificar(pedido, txn_id='TXN-PEND', payment_status='Completed')
        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PAGADO')
        self.assertEqual(pedido.paypal_transaccion_id, 'TXN-PEND')
        self.assertEqual(self.cpu.stock, 3)

    def test_los_pagos_fallidos_o_rechazados_no_descuentan_stock(self):
        pedido = self.pedido(cantidad=2, stock=5)

        for indice, estado in enumerate(('Failed', 'Denied', 'Voided', 'Refunded', 'Reversed')):
            response = self.notificar(pedido, txn_id=f'TXN-FALLO-{indice}', payment_status=estado)
            self.assertEqual(response.content, b'OKAY')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())
        self.assertEqual(PayPalIPN.objects.count(), 5)

    def test_un_postback_invalido_no_confirma_el_pago(self):
        pedido = self.pedido()

        response = self.notificar(pedido, txn_id='TXN-MALO', verificado=b'INVALID')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        ipn = PayPalIPN.objects.get(txn_id='TXN-MALO')
        self.assertEqual(response.content, b'OKAY')
        self.assertTrue(ipn.flag)
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())

    def test_monto_moneda_receptor_o_invoice_invalidos_no_descuentan_stock(self):
        pedido = self.pedido()
        casos = (
            {'txn_id': 'TXN-MONTO', 'mc_gross': '1.00'},
            {'txn_id': 'TXN-MONEDA', 'mc_currency': 'EUR'},
            {'txn_id': 'TXN-OTRO', 'receiver_email': 'otro@business.example.com'},
            {'txn_id': 'TXN-INV', 'invoice': 'no-es-un-pedido'},
            {'txn_id': 'TXN-AUSENTE', 'invoice': '99999999'},
        )

        for cambios in casos:
            self.notificar(pedido, **cambios)

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())

    def test_sin_stock_o_sin_producto_no_hay_descuento_parcial(self):
        self.cpu.stock = 5
        self.cpu.save(update_fields=['stock'])
        self.ram.stock = 0
        self.ram.save(update_fields=['stock'])
        pedido = Pedido.objects.create(
            usuario=self.user, estado='PENDIENTE', total_monto=Decimal('104500'), direccion_envio='Por definir',
        )
        ItemPedido.objects.create(
            pedido=pedido, producto_nombre=self.cpu.nombre, producto_tipo='CPU',
            precio_unitario=self.cpu.precio, cantidad=1,
            producto_modelo='procesador', producto_pk=self.cpu.pk,
        )
        ItemPedido.objects.create(
            pedido=pedido, producto_nombre=self.ram.nombre, producto_tipo='CPU',
            precio_unitario=self.ram.precio, cantidad=1,
            producto_modelo='procesador', producto_pk=self.ram.pk,
        )

        self.notificar(pedido, txn_id='TXN-STOCK')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.ram.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertEqual(self.cpu.stock, 5)
        self.assertEqual(self.ram.stock, 0)
        self.assertFalse(PagoBoleta.objects.exists())

        huerfano = self.pedido(cantidad=1, stock=5, enlazado=False)
        self.notificar(huerfano, txn_id='TXN-HUERFANO')
        huerfano.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(huerfano.estado, 'PENDIENTE')
        self.assertEqual(self.cpu.stock, 5)

    def test_un_pedido_cancelado_no_descuenta_stock_aunque_paypal_confirme(self):
        pedido = self.pedido(estado='CANCELADO')

        self.notificar(pedido, txn_id='TXN-CANCEL')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'CANCELADO')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())

    def test_la_misma_transaccion_no_paga_dos_pedidos(self):
        primero = self.pedido(cantidad=1, stock=5)
        segundo = self.pedido(cantidad=1, stock=4, producto=self.ram)

        self.notificar(primero, txn_id='TXN-UNICA')
        self.notificar(segundo, txn_id='TXN-UNICA')

        primero.refresh_from_db()
        segundo.refresh_from_db()
        self.cpu.refresh_from_db()
        self.ram.refresh_from_db()
        self.assertEqual(primero.estado, 'PAGADO')
        self.assertEqual(self.cpu.stock, 4)
        self.assertEqual(segundo.estado, 'PENDIENTE')
        self.assertIsNone(segundo.paypal_transaccion_id)
        self.assertEqual(self.ram.stock, 4)
        self.assertEqual(PagoBoleta.objects.filter(transaccion_id='TXN-UNICA').count(), 1)

    @override_settings(PAYPAL_TEST=False)
    def test_un_ipn_de_sandbox_no_se_acepta_con_la_cuenta_real(self):
        pedido = self.pedido()

        self.notificar(pedido, txn_id='TXN-SANDBOX')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertEqual(self.cpu.stock, 5)

    @override_settings(SITE_URL=SITIO)
    def test_el_checkout_firma_las_urls_del_dominio_publico(self):
        self.cpu.stock = 5
        self.cpu.save(update_fields=['stock'])
        carrito = Carrito.objects.create(usuario=self.user)
        ItemCarrito.objects.create(
            carrito=carrito, procesador=self.cpu, cantidad=1, precio_unitario=self.cpu.precio,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:checkout'))

        self.assertContains(response, 'https://www.sandbox.paypal.com/cgi-bin/webscr')
        self.assertContains(response, SITIO + reverse('paypal-ipn'))
        self.assertContains(response, SITIO + reverse('core:payment_success'))
        self.assertContains(response, SITIO + reverse('core:payment_failed'))
        self.assertNotContains(response, '127.0.0.1')
        self.assertNotContains(response, 'localhost')

    @override_settings(SITE_URL=SITIO)
    def test_reintentar_el_pago_usa_las_mismas_urls(self):
        pedido = self.pedido(cantidad=1, stock=5)
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:detalle_pedido', args=[pedido.id]))

        self.assertContains(response, SITIO + reverse('paypal-ipn'))
        self.assertContains(response, SITIO + reverse('core:payment_success'))
        self.assertContains(response, SITIO + reverse('core:payment_failed'))

    def test_el_regreso_exitoso_vacia_el_carrito_y_el_cancelado_no_toca_el_pedido(self):
        pedido = self.pedido(cantidad=1, stock=5)
        carrito = Carrito.objects.create(usuario=self.user)
        ItemCarrito.objects.create(
            carrito=carrito, procesador=self.cpu, cantidad=1, precio_unitario=self.cpu.precio,
        )
        self.client.force_login(self.user)

        exito = self.client.get(reverse('core:payment_success'))
        self.assertContains(exito, 'sigue pendiente')
        self.assertFalse(carrito.items.exists())

        ItemCarrito.objects.create(
            carrito=carrito, procesador=self.cpu, cantidad=1, precio_unitario=self.cpu.precio,
        )
        fallo = self.client.get(reverse('core:payment_failed'))
        self.assertContains(fallo, 'no se descontó stock')
        self.assertEqual(carrito.items.count(), 1)

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())

    def test_el_regreso_sin_sesion_no_confirma_el_pago(self):
        pedido = self.pedido(cantidad=1, stock=5)

        response = self.client.get(reverse('core:payment_success'))

        pedido.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertEqual(self.cpu.stock, 5)

    def test_un_ipn_real_no_se_acepta_en_sandbox(self):
        pedido = self.pedido(cantidad=1, stock=5)

        self.notificar(pedido, txn_id='TXN-REAL', omitir_test_ipn=True)

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())

    def test_un_completed_sin_transaccion_no_descuenta_stock(self):
        pedido = self.pedido(cantidad=1, stock=5)

        response = self.notificar(pedido, txn_id='', payment_status='Completed')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(response.content, b'OKAY')
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertEqual(self.cpu.stock, 5)

    def test_si_la_boleta_no_se_guarda_el_stock_vuelve_atras(self):
        pedido = self.pedido(cantidad=2, stock=5)

        with patch('core.payments.PagoBoleta.objects.create', side_effect=IntegrityError('duplicada')):
            response = self.notificar(pedido, txn_id='TXN-ATOMIC')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(response.content, b'OKAY')
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())

    def test_el_inicio_no_es_el_endpoint_de_paypal(self):
        response = self.client.get(reverse('core:index'))

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, b'OKAY')
        self.assertEqual(reverse('paypal-ipn'), '/paypal/')
