import importlib
from decimal import Decimal
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth.models import User
from django.db import IntegrityError, connection
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
            'invoice': str(pedido.paypal_invoice) if pedido is not None else '999999',
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
        self.assertContains(response, 'CLP')
        self.assertContains(response, 'PayPal cobrará:')
        self.assertContains(response, '200.00 USD')
        self.assertContains(response, '1 USD = 950 CLP')
        self.assertContains(response, 'name="amount" value="200.00"')
        self.assertContains(response, 'PayPal no acepta CLP')
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
        self.assertEqual(ipn.invoice, str(pedido.paypal_invoice))
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
            invoice=str(pedido.paypal_invoice),
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

    def test_el_regreso_exitoso_conserva_el_carrito_y_el_cancelado_no_toca_el_pedido(self):
        pedido = self.pedido(cantidad=1, stock=5)
        carrito = Carrito.objects.create(usuario=self.user)
        ItemCarrito.objects.create(
            carrito=carrito, procesador=self.cpu, cantidad=1, precio_unitario=self.cpu.precio,
        )
        self.client.force_login(self.user)

        exito = self.client.get(reverse('core:payment_success'), {'pedido': pedido.id})
        self.assertContains(exito, 'sigue pendiente')
        self.assertContains(exito, 'Verificando pago')
        self.assertEqual(carrito.items.count(), 1)

        fallo = self.client.get(reverse('core:payment_failed'), {'pedido': pedido.id})
        self.assertContains(fallo, 'no se descontó stock')
        self.assertContains(fallo, 'Reintentar pago')
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

    def _carrito(self, cantidad=1, precio=None):
        carrito, _creado = Carrito.objects.get_or_create(usuario=self.user)
        ItemCarrito.objects.filter(carrito=carrito).delete()
        ItemCarrito.objects.create(
            carrito=carrito,
            procesador=self.cpu,
            cantidad=cantidad,
            precio_unitario=precio if precio is not None else self.cpu.precio,
        )
        return carrito

    def test_repetir_el_checkout_reutiliza_el_pendiente_igual(self):
        self.cpu.stock = 5
        self.cpu.save(update_fields=['stock'])
        self._carrito(cantidad=2)
        self.client.force_login(self.user)

        with self.assertLogs('paypal.ipn', level='INFO') as primera:
            self.client.get(reverse('core:checkout'))
        primero = Pedido.objects.get(usuario=self.user)
        with self.assertLogs('paypal.ipn', level='INFO') as segunda:
            respuesta = self.client.get(reverse('core:checkout'))

        self.assertEqual(Pedido.objects.filter(usuario=self.user).count(), 1)
        self.assertEqual(primero.estado, 'PENDIENTE')
        self.assertEqual(Pedido.objects.get(pk=primero.id).paypal_invoice, primero.paypal_invoice)
        self.assertIsNone(primero.paypal_invoice_legado)
        self.assertContains(respuesta, f'Pedido #{primero.id}')
        self.assertContains(respuesta, f'name="invoice" value="{primero.paypal_invoice}"')
        self.assertNotContains(respuesta, f'name="invoice" value="{primero.id}"')
        self.assertContains(respuesta, 'Esperando pago')
        self.assertTrue(any(f'pedido pendiente #{primero.id}' in linea for linea in primera.output))
        self.assertTrue(any('reutiliza el pedido pendiente' in linea for linea in segunda.output))
        self.assertNotIn('comprador@example.com', '\n'.join(primera.output + segunda.output))

    def test_un_carrito_distinto_abre_otro_pedido(self):
        self.cpu.stock = 5
        self.cpu.save(update_fields=['stock'])
        carrito = self._carrito(cantidad=1)
        self.client.force_login(self.user)
        self.client.get(reverse('core:checkout'))
        primero = Pedido.objects.get(usuario=self.user)

        carrito.items.update(cantidad=2)
        self.client.get(reverse('core:checkout'))

        pedidos = list(Pedido.objects.filter(usuario=self.user).order_by('id'))
        self.assertEqual(len(pedidos), 2)
        self.assertEqual(pedidos[0].items_pedido.get().cantidad, 1)
        self.assertEqual(pedidos[1].items_pedido.get().cantidad, 2)
        self.assertNotEqual(pedidos[0].paypal_invoice, pedidos[1].paypal_invoice)
        self.assertNotEqual(str(pedidos[0].paypal_invoice), str(pedidos[0].id))
        self.assertIsNone(pedidos[1].paypal_invoice_legado)
        self.assertNotEqual(pedidos[0].total_monto, pedidos[1].total_monto)

        carrito.items.update(cantidad=2, precio_unitario=Decimal('1000'))
        self.client.get(reverse('core:checkout'))
        self.assertEqual(Pedido.objects.filter(usuario=self.user).count(), 3)
        reciente = Pedido.objects.filter(usuario=self.user).order_by('-id').first()
        self.assertEqual(reciente.items_pedido.get().precio_unitario, Decimal('1000'))

    def test_no_reutiliza_el_pendiente_de_otro_usuario_ni_un_pedido_pagado(self):
        self.cpu.stock = 5
        self.cpu.save(update_fields=['stock'])
        otro = User.objects.create_user('otro', 'otro@example.com', 'clave-paypal-123')
        ajeno = self.pedido(cantidad=1, stock=5)
        ajeno.usuario = otro
        ajeno.save(update_fields=['usuario'])
        pagado = self.pedido(cantidad=1, stock=5, estado='PAGADO')
        pagado.paypal_transaccion_id = 'TXN-YA-PAGADO'
        pagado.save(update_fields=['paypal_transaccion_id'])

        self._carrito(cantidad=1)
        self.client.force_login(self.user)
        self.client.get(reverse('core:checkout'))

        nuevo = Pedido.objects.get(usuario=self.user, estado='PENDIENTE')
        ajeno.refresh_from_db()
        pagado.refresh_from_db()
        self.assertNotEqual(nuevo.id, ajeno.id)
        self.assertEqual(ajeno.usuario, otro)
        self.assertEqual(pagado.estado, 'PAGADO')
        self.assertEqual(pagado.paypal_transaccion_id, 'TXN-YA-PAGADO')
        self.assertIsNone(nuevo.paypal_transaccion_id)

    def test_el_reintento_usa_el_invoice_pendiente_y_el_pagado_no_se_vuelve_a_cobrar(self):
        pendiente = self.pedido(cantidad=1, stock=5)
        pagado = self.pedido(cantidad=1, stock=5, estado='PAGADO')
        pagado.paypal_transaccion_id = 'TXN-CERRADO'
        pagado.save(update_fields=['paypal_transaccion_id'])
        self.client.force_login(self.user)

        reintento = self.client.get(reverse('core:detalle_pedido', args=[pendiente.id]))
        cerrado = self.client.get(reverse('core:detalle_pedido', args=[pagado.id]))

        self.assertContains(reintento, 'Esperando pago')
        self.assertContains(reintento, 'Reintentar pago')
        self.assertContains(reintento, f'Pedido #{pendiente.id}')
        self.assertContains(reintento, 'PayPal cobrará:')
        self.assertContains(reintento, '100.00 USD')
        self.assertContains(reintento, '1 USD = 950 CLP')
        self.assertContains(reintento, f'name="invoice" value="{pendiente.paypal_invoice}"')
        self.assertNotContains(reintento, f'name="invoice" value="{pendiente.id}"')
        self.assertNotContains(reintento, f'name="invoice" value="{pagado.paypal_invoice}"')
        self.assertContains(cerrado, 'Pagado')
        self.assertNotContains(cerrado, 'https://www.sandbox.paypal.com/cgi-bin/webscr')
        self.assertNotContains(cerrado, 'name="invoice"')

    def test_el_regreso_espera_al_ipn_y_un_ipn_tardio_confirma_una_sola_vez(self):
        self.cpu.stock = 5
        self.cpu.save(update_fields=['stock'])
        carrito = self._carrito(cantidad=1)
        self.client.force_login(self.user)
        self.client.get(reverse('core:checkout'))
        pedido = Pedido.objects.get(usuario=self.user)

        regreso = self.client.get(reverse('core:payment_success'), {'pedido': pedido.id})
        pedido.refresh_from_db()
        self.assertContains(regreso, 'Verificando pago')
        self.assertContains(regreso, 'sigue pendiente')
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertEqual(carrito.items.count(), 1)
        self.assertEqual(self.cpu.stock, 5)

        lista = self.client.get(reverse('core:mis_pedidos'))
        self.assertContains(lista, 'Verificando pago')

        self.notificar(pedido, txn_id='TXN-TARDE')
        self.notificar(pedido, txn_id='TXN-TARDE')
        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PAGADO')
        self.assertEqual(pedido.paypal_transaccion_id, 'TXN-TARDE')
        self.assertEqual(PagoBoleta.objects.filter(transaccion_id='TXN-TARDE').count(), 1)
        self.assertEqual(self.cpu.stock, 4)
        self.assertFalse(carrito.items.exists())

        detalle = self.client.get(reverse('core:detalle_pedido', args=[pedido.id]))
        self.assertContains(detalle, 'Pagado')
        self.assertNotContains(detalle, 'https://www.sandbox.paypal.com/cgi-bin/webscr')

    def test_un_ipn_tardio_no_vacia_un_carrito_que_ya_cambio(self):
        self.cpu.stock = 5
        self.cpu.save(update_fields=['stock'])
        carrito = self._carrito(cantidad=1)
        self.client.force_login(self.user)
        self.client.get(reverse('core:checkout'))
        pedido = Pedido.objects.get(usuario=self.user)
        carrito.items.update(cantidad=3)

        self.notificar(pedido, txn_id='TXN-CARRITO')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PAGADO')
        self.assertEqual(carrito.items.get().cantidad, 3)
        self.assertEqual(self.cpu.stock, 4)

    def test_cancelar_en_paypal_deja_el_reintento_sin_cobrar(self):
        self.cpu.stock = 5
        self.cpu.save(update_fields=['stock'])
        carrito = self._carrito(cantidad=1)
        self.client.force_login(self.user)
        self.client.get(reverse('core:checkout'))
        pedido = Pedido.objects.get(usuario=self.user)
        self.client.get(reverse('core:payment_success'), {'pedido': pedido.id})

        fallo = self.client.get(reverse('core:payment_failed'), {'pedido': pedido.id})
        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertContains(fallo, 'Pago cancelado')
        self.assertContains(fallo, 'Reintentar pago')
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(carrito.items.count(), 1)
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())

        reintento = self.client.get(reverse('core:detalle_pedido', args=[pedido.id]))
        self.assertContains(reintento, 'Esperando pago')
        self.assertContains(reintento, f'name="invoice" value="{pedido.paypal_invoice}"')
        self.assertNotContains(reintento, f'name="invoice" value="{pedido.id}"')

    def test_el_regreso_sin_sesion_no_confirma_ni_el_exito_ni_la_cancelacion(self):
        pedido = self.pedido(cantidad=1, stock=5)

        exito = self.client.get(reverse('core:payment_success'), {'pedido': pedido.id})
        fallo = self.client.get(reverse('core:payment_failed'), {'pedido': pedido.id})

        pedido.refresh_from_db()
        self.assertEqual(exito.status_code, 302)
        self.assertEqual(fallo.status_code, 302)
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)

    def test_transaction_refused_no_lo_resuelve_django(self):
        pedido = self.pedido(cantidad=1, stock=5)

        with self.assertLogs('paypal.ipn', level='INFO') as logs:
            response = self.notificar(pedido, txn_id='TXN-REFUSED', payment_status='Refused')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        texto = '\n'.join(logs.output)
        self.assertEqual(response.content, b'OKAY')
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())
        self.assertIn('Refused', texto)
        self.assertNotIn('sb-buyer@personal.example.com', texto)

    def test_el_numero_de_pedido_no_sirve_como_invoice(self):
        pedido = self.pedido(cantidad=1, stock=5)
        self.assertNotEqual(str(pedido.paypal_invoice), str(pedido.id))
        self.assertIsNone(pedido.paypal_invoice_legado)

        with self.assertLogs('paypal.ipn', level='ERROR') as logs:
            self.notificar(pedido, txn_id='TXN-ID', invoice=str(pedido.id))

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertIsNone(pedido.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())
        self.assertIn('conciliación manual', '\n'.join(logs.output))

    def test_el_invoice_desconocido_no_confirma_ningun_pedido(self):
        pedido = self.pedido(cantidad=1, stock=5)

        with self.assertLogs('paypal.ipn', level='ERROR') as logs:
            self.notificar(pedido, txn_id='TXN-RARO', invoice='no-es-uuid')

        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertEqual(self.cpu.stock, 5)
        self.assertIn('Invoice desconocido', '\n'.join(logs.output))
        self.assertNotIn('sb-buyer@personal.example.com', '\n'.join(logs.output))

    def test_el_ipn_legado_solo_cobra_el_pedido_que_guardo_ese_invoice(self):
        historico = self.pedido(cantidad=1, stock=5)
        historico.paypal_invoice_legado = '9001'
        historico.save(update_fields=['paypal_invoice_legado'])
        otro = self.pedido(cantidad=1, stock=5)

        self.notificar(historico, txn_id='TXN-LEGADO', invoice='9001')
        self.notificar(historico, txn_id='TXN-LEGADO', invoice='9001')

        historico.refresh_from_db()
        otro.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(historico.estado, 'PAGADO')
        self.assertEqual(historico.paypal_transaccion_id, 'TXN-LEGADO')
        self.assertEqual(otro.estado, 'PENDIENTE')
        self.assertIsNone(otro.paypal_transaccion_id)
        self.assertEqual(PagoBoleta.objects.filter(transaccion_id='TXN-LEGADO').count(), 1)
        self.assertEqual(self.cpu.stock, 4)

    def test_un_ipn_legado_tardio_no_vuelve_a_cobrar_un_pedido_pagado(self):
        historico = self.pedido(cantidad=1, stock=5)
        historico.paypal_invoice_legado = '9002'
        historico.save(update_fields=['paypal_invoice_legado'])
        self.notificar(historico, txn_id='TXN-YA', invoice=str(historico.paypal_invoice))

        resultado = confirmar_pago_paypal(PayPalIPN.objects.create(
            payment_status='Completed',
            txn_id='TXN-TARDE-LEGADO',
            invoice='9002',
            mc_gross=clp_a_usd(historico.total_monto),
            mc_currency='USD',
            receiver_email=RECEPTOR,
            test_ipn=True,
        ))

        historico.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(resultado, 'ya_procesado')
        self.assertEqual(historico.paypal_transaccion_id, 'TXN-YA')
        self.assertEqual(self.cpu.stock, 4)
        self.assertEqual(PagoBoleta.objects.count(), 1)

    def test_reiniciar_los_ids_no_reutiliza_un_invoice_pagado(self):
        original = self.pedido(cantidad=1, stock=5)
        invoice_pagado = str(original.paypal_invoice)
        id_pagado = original.id
        self.notificar(original, txn_id='TXN-ORIGINAL')
        self.assertEqual(original.pago_boleta.transaccion_id, 'TXN-ORIGINAL')

        PagoBoleta.objects.all().delete()
        ItemPedido.objects.all().delete()
        Pedido.objects.all().delete()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence('core_pedido', 'id'), %s, false)",
                [id_pagado],
            )
        nuevo = self.pedido(cantidad=1, stock=5)

        self.assertEqual(nuevo.id, id_pagado)
        self.assertNotEqual(str(nuevo.paypal_invoice), invoice_pagado)
        self.assertIsNone(nuevo.paypal_invoice_legado)

        with self.assertLogs('paypal.ipn', level='ERROR') as logs:
            self.notificar(nuevo, txn_id='TXN-VIEJO-UUID', invoice=invoice_pagado)
            self.notificar(nuevo, txn_id='TXN-VIEJO-NUMERO', invoice=str(id_pagado))

        nuevo.refresh_from_db()
        self.cpu.refresh_from_db()
        texto = '\n'.join(logs.output)
        self.assertEqual(nuevo.estado, 'PENDIENTE')
        self.assertIsNone(nuevo.paypal_transaccion_id)
        self.assertEqual(self.cpu.stock, 5)
        self.assertFalse(PagoBoleta.objects.exists())
        self.assertIn('Invoice desconocido', texto)
        self.assertIn('conciliación manual', texto)

    def test_el_relleno_asigna_un_uuid_distinto_y_conserva_el_legado(self):
        primero = self.pedido(cantidad=1, stock=5)
        segundo = self.pedido(cantidad=1, stock=5)
        invoice_inicial = primero.paypal_invoice

        rellenar = importlib.import_module(
            'core.migrations.0012_pedido_paypal_invoice'
        ).rellenar_invoices_existentes
        rellenar(apps, None)

        primero.refresh_from_db()
        segundo.refresh_from_db()
        self.assertNotEqual(primero.paypal_invoice, invoice_inicial)
        self.assertNotEqual(primero.paypal_invoice, segundo.paypal_invoice)
        self.assertEqual(primero.paypal_invoice_legado, str(primero.id))
        self.assertEqual(segundo.paypal_invoice_legado, str(segundo.id))
        self.assertNotEqual(str(primero.paypal_invoice), primero.paypal_invoice_legado)
        self.assertEqual(Pedido.objects.count(), 2)
