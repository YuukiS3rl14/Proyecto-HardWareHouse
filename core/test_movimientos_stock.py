import threading
from decimal import Decimal
from pathlib import Path

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN

from core.admin import ProcesadorAdmin
from core.inventario import StockInsuficiente, ajustar_stock, aplicar_delta, registrar_venta, reponer_stock
from core.models import (
    AuditoriaUmbral,
    ItemPedido,
    MovimientoStock,
    Pedido,
    Procesador,
    Proveedor,
    Ventilador,
)
from core.payments import clp_a_usd, confirmar_pago_paypal

RECEPTOR = 'sb-merchant@business.example.com'
BASE = Path(__file__).resolve().parent


def cpu(marca, nombre, stock, **extra):
    datos = dict(
        proveedor=marca, nombre=nombre, precio=Decimal('10000'), stock=stock,
        socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
    )
    datos.update(extra)
    return Procesador.objects.create(**datos)


@override_settings(
    PAYPAL_TEST=True,
    PAYPAL_RECEIVER_EMAIL=RECEPTOR,
    CLP_TO_USD_RATE=950,
    EMAILJS_SERVICE_ID='',
    EMAILJS_TEMPLATE_CONTACTO='',
    EMAILJS_TEMPLATE_PEDIDO='',
    EMAILJS_PUBLIC_KEY='',
    EMAILJS_PRIVATE_KEY='',
)
class MovimientosStockTests(TestCase):
    def setUp(self):
        self.marca = Proveedor.objects.create(nombre='Marca Mov')
        self.staff = User.objects.create_user(
            'TrabajadorGenerico', 'trabajador-mov@example.com', 'clave-mov-123', is_staff=True,
        )
        self.cliente = User.objects.create_user('cliente-mov', 'cliente-mov@example.com', 'clave-mov-123')

    def test_venta_reposicion_y_ajuste_dejan_saldos_coherentes(self):
        pieza = cpu(self.marca, 'CPU historial', 8)
        pedido = Pedido.objects.create(
            usuario=self.cliente, estado='PENDIENTE', total_monto=Decimal('20000.00'), direccion_envio='Local',
        )
        item = ItemPedido.objects.create(
            pedido=pedido, producto_nombre='CPU historial', producto_tipo='CPU',
            precio_unitario=Decimal('10000.00'), cantidad=2,
            producto_modelo='procesador', producto_pk=pieza.pk,
        )
        venta = aplicar_delta(
            pieza, -2, tipo=MovimientoStock.VENTA, origen='paypal', pedido=pedido, item=item,
            motivo=f'Pedido #{pedido.pk}',
        )
        reposicion = reponer_stock(pieza, 10, usuario=self.staff, motivo='Ingreso')
        ajuste = ajustar_stock(pieza, reposicion.stock_posterior - 1, usuario=self.staff, motivo='Corrección')
        pieza.refresh_from_db()
        self.assertEqual(venta.cantidad, -2)
        self.assertEqual(venta.stock_anterior, 8)
        self.assertEqual(venta.stock_posterior, 6)
        self.assertIsNone(venta.usuario)
        self.assertEqual(venta.origen, 'paypal')
        self.assertEqual(reposicion.tipo, MovimientoStock.REPOSICION)
        self.assertEqual(reposicion.cantidad, 10)
        self.assertEqual(reposicion.stock_anterior, 6)
        self.assertEqual(reposicion.stock_posterior, 16)
        self.assertEqual(reposicion.usuario, self.staff)
        self.assertEqual(ajuste.tipo, MovimientoStock.AJUSTE)
        self.assertEqual(ajuste.cantidad, -1)
        self.assertEqual(ajuste.stock_anterior, 16)
        self.assertEqual(ajuste.stock_posterior, 15)
        self.assertEqual(pieza.stock, 15)
        self.assertEqual(ajuste.cantidad_visible(), '−1')
        self.assertEqual(reposicion.cantidad_visible(), '+10')

    def test_una_operacion_fallida_no_deja_movimiento(self):
        pieza = cpu(self.marca, 'CPU falla', 4)
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                aplicar_delta(
                    pieza, -1, tipo=MovimientoStock.AJUSTE, usuario=self.staff, origen='servicio',
                )
                raise RuntimeError('falla')
        with self.assertRaises(StockInsuficiente):
            aplicar_delta(pieza, -10, tipo=MovimientoStock.AJUSTE, usuario=self.staff, origen='servicio')
        pieza.refresh_from_db()
        self.assertEqual(pieza.stock, 4)
        self.assertFalse(MovimientoStock.objects.exists())

    def test_la_venta_repetida_del_mismo_item_no_descuenta_dos_veces(self):
        pieza = cpu(self.marca, 'CPU doble', 8)
        pedido = Pedido.objects.create(
            usuario=self.cliente, estado='PENDIENTE', total_monto=Decimal('10000.00'), direccion_envio='Local',
        )
        item = ItemPedido.objects.create(
            pedido=pedido, producto_nombre='CPU doble', producto_tipo='CPU',
            precio_unitario=Decimal('10000.00'), cantidad=2,
            producto_modelo='procesador', producto_pk=pieza.pk,
        )
        self.assertIsNotNone(registrar_venta(pieza, item, pedido))
        self.assertIsNone(registrar_venta(pieza, item, pedido))
        pieza.refresh_from_db()
        self.assertEqual(pieza.stock, 6)
        self.assertEqual(MovimientoStock.objects.filter(tipo=MovimientoStock.VENTA).count(), 1)

    def test_paypal_registra_una_venta_y_la_repeticion_no_la_duplica(self):
        pieza = cpu(self.marca, 'CPU paypal', 6)
        pedido = Pedido.objects.create(
            usuario=self.cliente, estado='PENDIENTE', total_monto=Decimal('10000.00'), direccion_envio='Local',
        )
        ItemPedido.objects.create(
            pedido=pedido, producto_nombre='CPU paypal', producto_tipo='CPU',
            precio_unitario=Decimal('10000.00'), cantidad=1,
            producto_modelo='procesador', producto_pk=pieza.pk,
        )
        ipn = PayPalIPN.objects.create(
            payment_status='Completed', txn_id='TXN-MOV', invoice=str(pedido.paypal_invoice),
            mc_gross=clp_a_usd(pedido.total_monto), mc_currency='USD', receiver_email=RECEPTOR,
            test_ipn=True, payer_email='cliente-mov@example.com',
        )
        self.assertEqual(confirmar_pago_paypal(ipn), 'pagado')
        self.assertEqual(confirmar_pago_paypal(ipn), 'ya_procesado')
        pieza.refresh_from_db()
        pedido.refresh_from_db()
        movimiento = MovimientoStock.objects.get()
        self.assertEqual(pieza.stock, 5)
        self.assertEqual(pedido.estado, 'PAGADO')
        self.assertEqual(movimiento.tipo, MovimientoStock.VENTA)
        self.assertEqual(movimiento.cantidad, -1)
        self.assertEqual(movimiento.stock_anterior, 6)
        self.assertEqual(movimiento.stock_posterior, 5)
        self.assertIsNone(movimiento.usuario)
        self.assertEqual(movimiento.origen, 'paypal')
        self.assertEqual(movimiento.pedido_id, pedido.pk)
        self.assertEqual(movimiento.producto_modelo, 'procesador')

    def test_un_pago_sin_stock_no_deja_movimiento_ni_cambia_el_pedido(self):
        pieza = cpu(self.marca, 'CPU corto', 1)
        pedido = Pedido.objects.create(
            usuario=self.cliente, estado='PENDIENTE', total_monto=Decimal('20000.00'), direccion_envio='Local',
        )
        ItemPedido.objects.create(
            pedido=pedido, producto_nombre='CPU corto', producto_tipo='CPU',
            precio_unitario=Decimal('10000.00'), cantidad=2,
            producto_modelo='procesador', producto_pk=pieza.pk,
        )
        ipn = PayPalIPN.objects.create(
            payment_status='Completed', txn_id='TXN-CORTO', invoice=str(pedido.paypal_invoice),
            mc_gross=clp_a_usd(pedido.total_monto), mc_currency='USD', receiver_email=RECEPTOR,
            test_ipn=True,
        )
        self.assertEqual(confirmar_pago_paypal(ipn), 'rechazado')
        pieza.refresh_from_db()
        pedido.refresh_from_db()
        self.assertEqual(pieza.stock, 1)
        self.assertEqual(pedido.estado, 'PENDIENTE')
        self.assertFalse(MovimientoStock.objects.exists())

    def test_dos_familias_con_el_mismo_numero_no_se_mezclan(self):
        pieza = cpu(self.marca, 'CPU familia', 3)
        fan = Ventilador.objects.create(
            pk=pieza.pk,
            proveedor=self.marca, nombre='Fan familia', precio=Decimal('5000'), stock=4,
            tamanho_mm=120, velocidad_rpm=800,
        )
        self.assertEqual(pieza.pk, fan.pk)
        reponer_stock(pieza, 1, usuario=self.staff, motivo='cpu')
        reponer_stock(fan, 2, usuario=self.staff, motivo='fan')
        pieza.nombre = 'CPU renombrada'
        pieza.save(update_fields=['nombre'])
        self.client.force_login(self.staff)
        cpu_pagina = self.client.get(reverse('core:movimientos_producto', args=['procesador', pieza.pk]))
        fan_pagina = self.client.get(reverse('core:movimientos_producto', args=['ventilador', fan.pk]))
        self.assertContains(cpu_pagina, 'CPU familia')
        self.assertNotContains(cpu_pagina, 'Fan familia')
        self.assertContains(fan_pagina, 'Fan familia')
        self.assertNotContains(fan_pagina, 'CPU familia')
        self.assertContains(cpu_pagina, '+1')
        self.assertContains(fan_pagina, '+2')
        vacio = cpu(self.marca, 'CPU sin movimientos', 9)
        respuesta = self.client.get(reverse('core:movimientos_producto', args=['procesador', vacio.pk]))
        self.assertContains(respuesta, 'Este producto todavía no tiene movimientos registrados')

    def test_el_historial_ordena_filtra_y_pagina(self):
        pieza = cpu(self.marca, 'CPU lista', 30)
        for indice in range(21):
            reponer_stock(pieza, 1, usuario=self.staff, motivo=f'lote-{indice:02d}')
        ajustar_stock(pieza, pieza.stock, usuario=self.staff, motivo='sin cambio')
        self.client.force_login(self.staff)
        pagina = self.client.get(reverse('core:movimientos_stock'))
        html = pagina.content.decode()
        self.assertContains(pagina, 'lote-20')
        self.assertNotContains(pagina, 'lote-00')
        self.assertLess(html.index('lote-20'), html.index('lote-19'))
        segunda = self.client.get(reverse('core:movimientos_stock'), {'page': 2})
        self.assertContains(segunda, 'lote-00')
        self.assertNotContains(segunda, 'lote-20')
        hoy = timezone.localdate().isoformat()
        filtrada = self.client.get(reverse('core:movimientos_stock'), {
            'q': f'procesador:{pieza.pk}',
            'tipo': MovimientoStock.REPOSICION,
            'categoria': 'CPU',
            'usuario': self.staff.pk,
            'desde': hoy,
            'hasta': hoy,
        })
        self.assertContains(filtrada, 'lote-20')
        self.assertContains(filtrada, 'Reposición')
        sistema = self.client.get(reverse('core:movimientos_stock'), {'usuario': 'sistema'})
        self.assertContains(sistema, 'No hay movimientos que coincidan con estos filtros.')
        fuera = self.client.get(reverse('core:movimientos_stock'), {'desde': '2999-01-01'})
        self.assertContains(fuera, 'No hay movimientos que coincidan con estos filtros.')
        self.assertEqual(MovimientoStock.objects.filter(motivo='sin cambio').count(), 0)

    def test_el_admin_registra_el_ajuste_y_rechaza_el_negativo(self):
        pieza = cpu(self.marca, 'CPU admin', 6)
        admin = ProcesadorAdmin(Procesador, AdminSite())
        request = RequestFactory().post('/admin/core/procesador/')
        request.user = self.staff
        pieza.stock = 5
        admin.save_model(request, pieza, None, True)
        movimiento = MovimientoStock.objects.get()
        self.assertEqual(movimiento.tipo, MovimientoStock.AJUSTE)
        self.assertEqual(movimiento.cantidad, -1)
        self.assertEqual(movimiento.stock_anterior, 6)
        self.assertEqual(movimiento.stock_posterior, 5)
        self.assertEqual(movimiento.usuario, self.staff)
        self.assertEqual(movimiento.origen, 'admin')
        pieza.stock_minimo = 2
        pieza.stock_advertencia = 4
        admin.save_model(request, pieza, None, True)
        pieza.refresh_from_db()
        self.assertEqual(pieza.stock, 5)
        self.assertEqual(MovimientoStock.objects.count(), 1)
        self.assertEqual(AuditoriaUmbral.objects.count(), 1)
        pieza.stock = -1
        with self.assertRaises(ValidationError):
            admin.save_model(request, pieza, None, True)
        pieza.refresh_from_db()
        self.assertEqual(pieza.stock, 5)
        self.assertEqual(MovimientoStock.objects.count(), 1)

    def test_editar_umbrales_valida_permisos_y_no_toca_el_stock(self):
        pieza = cpu(self.marca, 'CPU umbral', 4)
        url = reverse('core:alertas_stock_umbrales')
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.staff)
        datos = {'modelo': 'procesador', 'pk': pieza.pk, 'stock_minimo': 1, 'stock_advertencia': 1}
        self.assertEqual(self.client.post(url, datos).status_code, 403)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.staff.user_permissions.add(Permission.objects.get(codename='change_procesador'))
        self.staff = User.objects.get(pk=self.staff.pk)
        self.client.force_login(self.staff)
        invalido = self.client.post(url, {
            'modelo': 'procesador', 'pk': pieza.pk, 'stock_minimo': -1, 'stock_advertencia': 2,
        })
        self.assertEqual(invalido.status_code, 400)
        decimal = self.client.post(url, {
            'modelo': 'procesador', 'pk': pieza.pk, 'stock_minimo': '1.5', 'stock_advertencia': 2,
        })
        self.assertEqual(decimal.status_code, 400)
        cruzado = self.client.post(url, {
            'modelo': 'procesador', 'pk': pieza.pk, 'stock_minimo': 4, 'stock_advertencia': 2,
        })
        self.assertEqual(cruzado.status_code, 400)
        pieza.refresh_from_db()
        self.assertEqual((pieza.stock, pieza.stock_minimo, pieza.stock_advertencia), (4, 3, 5))
        self.assertFalse(MovimientoStock.objects.exists())
        self.assertFalse(AuditoriaUmbral.objects.exists())
        guardado = self.client.post(url, datos)
        self.assertEqual(guardado.status_code, 200)
        cuerpo = guardado.json()
        self.assertTrue(cuerpo['ok'])
        self.assertEqual(cuerpo['estado'], 'NORMAL')
        self.assertFalse(cuerpo['visible'])
        self.assertEqual(cuerpo['stock'], 4)
        pieza.refresh_from_db()
        self.assertEqual(pieza.stock, 4)
        self.assertEqual(pieza.stock_minimo, 1)
        self.assertEqual(pieza.stock_advertencia, 1)
        self.assertFalse(MovimientoStock.objects.exists())
        self.assertEqual(AuditoriaUmbral.objects.count(), 1)
        panel = self.client.get(reverse('core:alertas_stock'))
        self.assertNotContains(panel, 'CPU umbral')
        self.assertContains(panel, 'hw-stock-card')
        self.assertContains(panel, 'Historial de movimientos')

    def test_cancelar_no_escribe_y_el_nombre_largo_no_rompe_el_cierre(self):
        pieza = cpu(self.marca, 'CPU cancelar', 1)
        self.staff.user_permissions.add(Permission.objects.get(codename='change_procesador'))
        self.staff = User.objects.get(pk=self.staff.pk)
        self.client.force_login(self.staff)
        panel = self.client.get(reverse('core:alertas_stock'))
        self.assertContains(panel, 'Cancelar')
        self.assertEqual(pieza.stock_minimo, 3)
        self.assertFalse(AuditoriaUmbral.objects.exists())
        script = (BASE / 'static/core/js/alertas_stock.js').read_text(encoding='utf-8')
        tramo = script.split("closest('.js-cancelar')", 1)[1].split('const guardar', 1)[0]
        self.assertNotIn('fetch(', tramo)
        self.assertIn('cerrar(fila)', tramo)
        inicio = self.client.get(reverse('core:index'))
        self.assertContains(inicio, 'title="TrabajadorGenerico"')
        self.assertContains(inicio, 'hw-user-name')
        self.assertContains(inicio, 'Cerrar Sesión')
        self.assertContains(inicio, 'hw-logout-btn')
        estilos = (BASE / 'static/core/css/custom.css').read_text(encoding='utf-8')
        self.assertIn('text-overflow: ellipsis', estilos)
        self.assertIn('min-width: 0', estilos)
        self.assertIn('white-space: nowrap', estilos)
        tarjetas = (BASE / 'static/core/css/inventario.css').read_text(encoding='utf-8')
        self.assertIn('background-color: #FFFFFF', tarjetas)
        self.assertIn('0 4px 16px rgba(15, 23, 42, 0.08)', tarjetas)
        self.assertNotIn('backdrop-filter', tarjetas)

    def test_el_historial_exige_personal_activo(self):
        self.assertEqual(self.client.get(reverse('core:movimientos_stock')).status_code, 302)
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse('core:movimientos_stock')).status_code, 403)
        self.staff.is_active = False
        self.staff.save()
        self.client.force_login(self.staff)
        inactivo = self.client.get(reverse('core:movimientos_stock'))
        self.assertEqual(inactivo.status_code, 302)
        self.assertIn('/login/', inactivo.url)


class ConcurrenciaStockTests(TransactionTestCase):
    def test_dos_descuentos_simultaneos_no_pisan_el_stock(self):
        if connection.vendor != 'postgresql':
            self.skipTest('El bloqueo de fila se comprueba en PostgreSQL.')
        marca = Proveedor.objects.create(nombre='Marca Concurrente')
        pieza = cpu(marca, 'CPU concurrente', 5)
        staff = User.objects.create_user('trabajador-con', 'con@example.com', 'clave-con-123', is_staff=True)
        errores = []
        barrera = threading.Barrier(2)

        def bajar():
            try:
                barrera.wait(timeout=5)
                aplicar_delta(
                    pieza, -1, tipo=MovimientoStock.AJUSTE, usuario=staff, origen='servicio', motivo='concurrente',
                )
            except Exception as exc:
                errores.append(exc)
            finally:
                connection.close()

        hilos = [threading.Thread(target=bajar), threading.Thread(target=bajar)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(timeout=15)
        self.assertEqual(errores, [])
        pieza.refresh_from_db()
        movimientos = list(
            MovimientoStock.objects.filter(producto_modelo='procesador', producto_pk=pieza.pk).order_by('id')
        )
        self.assertEqual(pieza.stock, 3)
        self.assertEqual(len(movimientos), 2)
        self.assertEqual(movimientos[0].stock_anterior, 5)
        self.assertEqual(movimientos[0].stock_posterior, 4)
        self.assertEqual(movimientos[1].stock_anterior, 4)
        self.assertEqual(movimientos[1].stock_posterior, 3)
        self.assertEqual(sum(movimiento.cantidad for movimiento in movimientos), -2)
