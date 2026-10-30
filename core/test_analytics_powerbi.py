from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from core.management.commands.crear_rol_powerbi import Command
from core.models import ItemPedido, PagoBoleta, Pedido, Procesador, Proveedor


class VistasAnalyticsTests(TestCase):
    def setUp(self):
        marca = Proveedor.objects.create(nombre="AMD")
        self.cpu = Procesador.objects.create(
            proveedor=marca,
            nombre="AMD Ryzen 5 5600",
            precio=Decimal("100.00"),
            stock=8,
            socket="AM4",
            nucleos=6,
            frecuencia_base=Decimal("3.50"),
            potencia_referencia_watts=65,
        )
        usuario = User.objects.create_user("cliente-vista", password="x", email="cliente@example.com")
        self.pagado = self._pedido(usuario, "PAGADO", "DEMO-PBI-000777", "DEMO-PBI", Decimal("250.00"))
        ItemPedido.objects.create(
            pedido=self.pagado,
            producto_nombre="AMD Ryzen 5 5600",
            producto_tipo="CPU",
            precio_unitario=Decimal("100.00"),
            cantidad=1,
            producto_modelo="procesador",
            producto_pk=self.cpu.pk,
        )
        ItemPedido.objects.create(
            pedido=self.pagado,
            producto_nombre="Nombre histórico distinto",
            producto_tipo="CPU",
            precio_unitario=Decimal("75.00"),
            cantidad=2,
            producto_modelo="procesador",
            producto_pk=self.cpu.pk,
        )
        self.pendiente = self._pedido(usuario, "PENDIENTE", None, None, Decimal("100.00"))
        ItemPedido.objects.create(
            pedido=self.pendiente,
            producto_nombre="No debe entrar",
            producto_tipo="CPU",
            precio_unitario=Decimal("100.00"),
            cantidad=1,
            producto_modelo="procesador",
            producto_pk=self.cpu.pk,
        )
        cancelado = self._pedido(usuario, "CANCELADO", "TXN-CANCELADA", "PayPal", Decimal("100.00"))
        ItemPedido.objects.create(
            pedido=cancelado,
            producto_nombre="Cancelado",
            producto_tipo="CPU",
            precio_unitario=Decimal("100.00"),
            cantidad=1,
            producto_modelo="procesador",
            producto_pk=self.cpu.pk,
        )
        PagoBoleta.objects.create(
            pedido=cancelado,
            monto_pagado=Decimal("100.00"),
            metodo_pago="PayPal",
            transaccion_id="TXN-CANCELADA",
            nombre_comprador="Persona Real",
            email_comprador="persona@example.com",
        )

    def _pedido(self, usuario, estado, transaccion, metodo, total):
        pedido = Pedido.objects.create(
            usuario=usuario,
            estado=estado,
            total_monto=total,
            direccion_envio="Calle privada 123",
            paypal_transaccion_id=transaccion,
            fecha_pedido=timezone.now() - timedelta(days=40),
        )
        if estado == "PAGADO":
            PagoBoleta.objects.create(
                pedido=pedido,
                monto_pagado=total,
                metodo_pago=metodo,
                transaccion_id=transaccion,
                nombre_comprador="Persona Real",
                email_comprador="persona@example.com",
            )
        return pedido

    def test_el_ingreso_usa_el_item_y_omite_lo_no_pagado(self):
        fact = self._filas("SELECT pedido_id, producto_nombre, cantidad, precio_unitario, total_linea, es_demo, marca_catalogo FROM analytics.fact_venta_item")
        self.assertEqual(len(fact), 2)
        self.assertEqual({fila[0] for fila in fact}, {self.pagado.id})
        self.assertEqual(sum(fila[4] for fila in fact), Decimal("250.00"))
        self.assertTrue(all(fila[5] for fila in fact))
        self.assertEqual(fact[0][6], "AMD")
        historico = next(fila for fila in fact if fila[1] == "Nombre histórico distinto")
        self.assertEqual(historico[3], Decimal("75.00"))
        self.assertEqual(historico[4], Decimal("150.00"))

        pedidos = self._filas("SELECT COUNT(*), SUM(total_pedido) FROM analytics.pedido_pagado")
        self.assertEqual(pedidos[0][0], 1)
        self.assertEqual(pedidos[0][1], Decimal("250.00"))

        inflado = self._filas(
            """
            SELECT SUM(o.total_pedido)
            FROM analytics.fact_venta_item f
            JOIN analytics.pedido_pagado o ON o.pedido_id = f.pedido_id
            """
        )
        self.assertGreater(inflado[0][0], Decimal("250.00"))

        columnas = self._filas(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'analytics'
            """
        )
        nombres = {fila[0] for fila in columnas}
        for privada in ("email", "email_comprador", "nombre_comprador", "direccion_envio", "usuario_id", "username"):
            self.assertNotIn(privada, nombres)

        ranking = self._filas(
            """
            SELECT producto_nombre, ingresos, ranking_ingresos
            FROM analytics.producto_top
            ORDER BY ranking_ingresos, producto_nombre
            """
        )
        self.assertEqual(ranking[0][0], "Nombre histórico distinto")
        self.assertEqual(ranking[0][1], Decimal("150.00"))

    def _filas(self, consulta):
        with connection.cursor() as cursor:
            cursor.execute(consulta)
            return cursor.fetchall()


class RolPowerBiTests(TestCase):
    def test_rechaza_una_base_remota(self):
        comando = Command()
        with patch("core.management.commands.crear_rol_powerbi.connection") as conexion:
            conexion.vendor = "postgresql"
            conexion.settings_dict = {"HOST": "monorail.proxy.rlwy.net", "NAME": "railway"}
            with self.assertRaises(CommandError):
                comando._exigir_local()
