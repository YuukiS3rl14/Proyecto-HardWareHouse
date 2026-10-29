from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.chatbot.private_data import respuesta_mis_pedidos
from core.models import ItemPedido, PagoBoleta, Pedido, Procesador, Proveedor
from core.payments import clp_a_usd

ZONA = ZoneInfo('America/Santiago')
UTC = ZoneInfo('UTC')


def _momento(anio, mes, dia, hora, minuto, fold=0):
    return datetime(anio, mes, dia, hora, minuto, fold=fold, tzinfo=ZONA)


@override_settings(CLP_TO_USD_RATE=950, TIME_ZONE='America/Santiago', USE_TZ=True)
class MonedaYHoraChileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('cliente-cl', 'cliente-cl@example.com', 'clave-chile-123')
        marca = Proveedor.objects.create(nombre='Marca Chile')
        cls.cpu = Procesador.objects.create(
            proveedor=marca, nombre='CPU Chile', precio=Decimal('95000'), stock=5,
            socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
        )

    def pedido(self, momento, estado='PAGADO'):
        pedido = Pedido.objects.create(
            usuario=self.user,
            estado=estado,
            total_monto=Decimal('190000.00'),
            direccion_envio='Por definir',
            paypal_transaccion_id='TXN-CL' if estado == 'PAGADO' else '',
            fecha_pedido=momento,
        )
        ItemPedido.objects.create(
            pedido=pedido,
            producto_nombre=self.cpu.nombre,
            producto_tipo='CPU',
            precio_unitario=Decimal('95000'),
            cantidad=2,
            producto_modelo='procesador',
            producto_pk=self.cpu.pk,
        )
        if estado == 'PAGADO':
            boleta = PagoBoleta.objects.create(
                pedido=pedido,
                monto_pagado=pedido.total_monto,
                metodo_pago='PayPal',
                transaccion_id=f'TXN-CL-{pedido.id}',
                nombre_comprador='Cliente',
                email_comprador='cliente-cl@example.com',
            )
            PagoBoleta.objects.filter(pk=boleta.pk).update(fecha_pago=momento)
            pedido.paypal_transaccion_id = boleta.transaccion_id
            pedido.save(update_fields=['paypal_transaccion_id'])
        pedido.refresh_from_db()
        return pedido

    def test_el_total_en_clp_y_el_cobro_en_usd_usan_el_mismo_centavo(self):
        pedido = self.pedido(_momento(2026, 7, 15, 23, 30), estado='PENDIENTE')
        self.client.force_login(self.user)
        detalle = self.client.get(reverse('core:detalle_pedido', args=[pedido.id]))
        usd = f'{clp_a_usd(pedido.total_monto):.2f}'

        self.assertContains(detalle, 'CLP')
        self.assertContains(detalle, f'PayPal cobrará:</strong> {usd} USD')
        self.assertContains(detalle, '1 USD = 950 CLP')
        self.assertContains(detalle, 'PayPal no acepta CLP')
        self.assertContains(detalle, f'name="amount" value="{usd}"')
        self.assertContains(detalle, '15/07/2026 23:30')
        self.assertNotContains(detalle, '16/07/2026 03:30')

    def test_la_boleta_muestra_clp_y_el_usd_sin_ocultarlo(self):
        pedido = self.pedido(_momento(2026, 1, 15, 23, 30))
        self.client.force_login(self.user)
        boleta = self.client.get(reverse('core:ver_boleta', args=[pedido.id]))
        usd = f'{clp_a_usd(pedido.total_monto):.2f}'

        self.assertContains(boleta, 'Total pagado:')
        self.assertContains(boleta, 'CLP')
        self.assertContains(boleta, f'PayPal cobró:</strong> {usd} USD')
        self.assertContains(boleta, '15/01/2026 23:30')
        self.assertNotContains(boleta, '16/01/2026 02:30')

    def test_medianoche_y_el_cambio_de_hora_se_ven_en_santiago(self):
        casos = (
            _momento(2026, 7, 15, 23, 30),
            _momento(2026, 1, 15, 23, 30),
            _momento(2026, 4, 4, 23, 30, fold=0),
            _momento(2026, 4, 4, 23, 30, fold=1),
            _momento(2026, 9, 5, 23, 30),
            _momento(2026, 9, 6, 1, 30),
        )
        self.assertEqual(casos[0].utcoffset().total_seconds(), -4 * 3600)
        self.assertEqual(casos[1].utcoffset().total_seconds(), -3 * 3600)
        self.assertNotEqual(casos[2].utcoffset(), casos[3].utcoffset())
        self.assertEqual(casos[4].utcoffset().total_seconds(), -4 * 3600)
        self.assertEqual(casos[5].utcoffset().total_seconds(), -3 * 3600)

        self.client.force_login(self.user)
        for momento in casos:
            pedido = self.pedido(momento)
            self.assertEqual(pedido.fecha_pedido.timestamp(), momento.timestamp())
            texto = timezone.localtime(pedido.fecha_pedido).strftime('%d/%m/%Y %H:%M')
            self.assertEqual(texto, momento.strftime('%d/%m/%Y %H:%M'))
            self.assertNotEqual(momento.astimezone(UTC).strftime('%d/%m/%Y %H:%M'), texto)

            lista = self.client.get(reverse('core:mis_pedidos'))
            self.assertContains(lista, texto)
            self.assertContains(lista, 'pesos chilenos')

            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT fecha FROM analytics.fact_venta_item WHERE pedido_id = %s',
                    [pedido.id],
                )
                self.assertEqual(cursor.fetchone()[0], momento.date())

            chat = respuesta_mis_pedidos(self.user, limite=10)
            propio = next(item for item in chat['pedidos'] if item['id'] == pedido.id)
            self.assertEqual(propio['fecha'], timezone.localtime(pedido.fecha_pedido).isoformat())
            self.assertNotEqual(propio['fecha'], pedido.fecha_pedido.astimezone(UTC).isoformat())
            self.assertIn(momento.strftime('%d-%m-%Y %H:%M'), chat['reply'])
            self.assertIn('CLP', chat['reply'])
            self.assertNotIn(momento.astimezone(UTC).strftime('%d-%m-%Y %H:%M'), chat['reply'])
