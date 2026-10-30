import io
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from core.models import ItemPedido, PagoBoleta, Pedido, Procesador, Proveedor, TarjetaGrafica
from core.payments import confirmar_pago_paypal
from core.pedidos_demo_pbi import (
    PREFIJO,
    auditar_pedidos_demo,
    exigir_base_local,
    firma_stock,
    planificar_pedidos,
)


def _productos(cantidad=8):
    filas = []
    for pk in range(1, cantidad + 1):
        filas.append({
            "modelo": "procesador" if pk % 2 else "tarjeta_grafica",
            "pk": pk,
            "nombre": f"Pieza sintética {pk}",
            "categoria": "CPU" if pk % 2 else "Tarjeta Gráfica",
            "precio": Decimal("10000.00") + Decimal(pk * 1000),
        })
    return filas


class PlanPedidosDemoTests(SimpleTestCase):
    def test_la_semilla_repite_el_mismo_plan(self):
        fin = timezone.localdate() - timedelta(days=1)
        primero = planificar_pedidos(_productos(), [], count=40, seed=42, fecha_fin=fin)
        segundo = planificar_pedidos(_productos(), [], count=40, seed=42, fecha_fin=fin)
        self.assertEqual(
            [(plan["transaccion_id"], plan["fecha"], plan["total"]) for plan in primero],
            [(plan["transaccion_id"], plan["fecha"], plan["total"]) for plan in segundo],
        )
        self.assertTrue(all(plan["transaccion_id"].startswith(PREFIJO) for plan in primero))
        fechas = [plan["fecha"] for plan in primero]
        self.assertGreaterEqual((max(fechas) - min(fechas)).days, 200)
        self.assertGreaterEqual(len({fecha.date().replace(day=1) for fecha in fechas}), 6)
        for plan in primero:
            self.assertGreaterEqual(len(plan["items"]), 1)
            self.assertLessEqual(len(plan["items"]), 5)
            suma = sum(item["precio"] * item["cantidad"] for item in plan["items"])
            self.assertEqual(suma.quantize(Decimal("0.01")), plan["total"])

    def test_rechaza_una_base_remota(self):
        with patch("core.pedidos_demo_pbi.connection") as conexion:
            conexion.vendor = "postgresql"
            conexion.settings_dict = {"HOST": "monorail.proxy.rlwy.net", "NAME": "railway"}
            with self.assertRaises(Exception):
                exigir_base_local()


class GenerarPedidosDemoTests(TestCase):
    def setUp(self):
        marca = Proveedor.objects.create(nombre="AMD")
        self.cpu = Procesador.objects.create(
            pk=1,
            proveedor=marca,
            nombre="AMD Ryzen 5 5600",
            descripcion="Precio sintético.",
            precio=Decimal("129990.00"),
            stock=9,
            socket="AM4",
            nucleos=6,
            frecuencia_base=Decimal("3.50"),
            potencia_referencia_watts=65,
        )
        self.gpu = TarjetaGrafica.objects.create(
            pk=2,
            proveedor=marca,
            nombre="ASUS GeForce RTX 4060",
            descripcion="Precio sintético.",
            precio=Decimal("329990.00"),
            stock=7,
            vram_gb=8,
            tipo_memoria="GDDR6",
            interfaz="PCIe 4.0",
            consumo_referencia_watts=115,
            potencia_minima_fuente_watts=550,
            largo_mm=240,
        )
        self.real = User.objects.create_user("cliente-real", password="clave-real", email="real@example.com")
        self.pedido_real = Pedido.objects.create(
            usuario=self.real,
            estado="PENDIENTE",
            total_monto=Decimal("214990.00"),
            direccion_envio="Calle real 10",
        )
        ItemPedido.objects.create(
            pedido=self.pedido_real,
            producto_nombre="G.Skill CPU Serie Test 100 19c",
            producto_tipo="CPU",
            precio_unitario=Decimal("214990.00"),
            cantidad=1,
            producto_modelo="procesador",
            producto_pk=1,
        )

    def test_dry_run_y_apply_sin_confirmacion_no_escriben(self):
        salida = io.StringIO()
        call_command("generar_pedidos_demo_pbi", "--dry-run", "--count", "6", "--seed", "42", stdout=salida)
        self.assertEqual(PagoBoleta.objects.count(), 0)
        self.assertIn("Dry-run", salida.getvalue())
        with self.assertRaises(CommandError):
            call_command("generar_pedidos_demo_pbi", "--apply", "--count", "6", "--seed", "42")
        self.assertEqual(PagoBoleta.objects.count(), 0)
        self.assertEqual(self.cpu.stock, 9)

    def test_apply_crea_pedidos_pagados_sin_tocar_stock_ni_paypal(self):
        with patch("core.payments.confirmar_pago_paypal", wraps=confirmar_pago_paypal) as pago:
            call_command(
                "generar_pedidos_demo_pbi",
                "--apply",
                "--confirm",
                "--count",
                "12",
                "--seed",
                "42",
            )
        pago.assert_not_called()
        self.assertEqual(PagoBoleta.objects.filter(transaccion_id__startswith=PREFIJO).count(), 12)
        self.assertEqual(auditar_pedidos_demo(12), [])
        self.cpu.refresh_from_db()
        self.gpu.refresh_from_db()
        self.assertEqual(self.cpu.stock, 9)
        self.assertEqual(self.gpu.stock, 7)
        self.pedido_real.refresh_from_db()
        self.assertEqual(self.pedido_real.estado, "PENDIENTE")
        self.assertEqual(self.pedido_real.total_monto, Decimal("214990.00"))
        self.assertIsNone(self.pedido_real.paypal_transaccion_id)
        boleta = PagoBoleta.objects.get(transaccion_id=f"{PREFIJO}000001")
        self.assertEqual(boleta.pedido.estado, "PAGADO")
        self.assertEqual(boleta.monto_pagado, boleta.pedido.total_monto)
        self.assertLess(boleta.fecha_pago.date(), timezone.localdate())
        self.assertTrue(boleta.email_comprador.endswith("@example.com"))
        self.assertTrue(boleta.pedido.usuario.username.startswith("demo-pbi-"))
        self.assertFalse(boleta.pedido.usuario.has_usable_password())
        firma = firma_stock()
        salida = io.StringIO()
        call_command(
            "generar_pedidos_demo_pbi",
            "--apply",
            "--confirm",
            "--count",
            "12",
            "--seed",
            "42",
            stdout=salida,
        )
        self.assertIn("Creados: 0", salida.getvalue())
        self.assertEqual(PagoBoleta.objects.count(), 12)
        self.assertEqual(firma_stock(), firma)
        self.assertEqual(Pedido.objects.filter(usuario=self.real).count(), 1)
