import io
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from core.demo_catalog import build_catalog, validar_catalogo
from core.demo_catalog_io import comparar_fuentes, parse_csv, parse_product_inserts
from core.demo_catalog_sync import es_fila_demo, sincronizar_filas
from core.models import ItemPedido, Pedido, Procesador, Proveedor, TarjetaGrafica
from pathlib import Path

from django.conf import settings


def _fuentes():
    base = Path(settings.BASE_DIR)
    sql = (base / "data" / "seed_test_data.sql").read_text(encoding="utf-8")
    csv = (base / "data" / "productos_componentes.csv").read_text(encoding="utf-8-sig")
    return parse_product_inserts(sql), parse_csv(csv), sql


class CatalogoDemoArchivoTests(SimpleTestCase):
    def test_fuentes_coinciden_y_no_traen_serie_test(self):
        filas, csv_filas, sql = _fuentes()
        validar_catalogo(filas)
        comparar_fuentes(filas, csv_filas)
        self.assertEqual(len(filas), 1000)
        self.assertNotIn("Serie Test", sql)
        for fila in filas:
            self.assertNotIn("test", f" {fila['nombre'].lower()} ")
            self.assertNotIn("de prueba", fila["descripcion"].lower())
            self.assertIn("no son un precio de mercado verificado", fila["descripcion"])
        nombres = [fila["nombre"] for fila in filas]
        self.assertEqual(len(nombres), len(set((fila["modelo"], fila["nombre"]) for fila in filas)))
        cpu = next(fila for fila in filas if fila["modelo"] == "procesador" and fila["pk"] == 1)
        self.assertEqual(cpu["marca"], "AMD")
        self.assertEqual(cpu["campos"]["socket"], "AM4")
        self.assertIn("WHERE nombre = 'AMD'", sql)
        placa_b550 = next(
            fila for fila in filas
            if fila["modelo"] == "placa_madre" and fila["campos"]["chipset"] == "B550"
        )
        self.assertEqual(placa_b550["campos"]["socket_cpu"], "AM4")
        self.assertEqual(placa_b550["campos"]["tipo_ram_soportado"], "DDR4")
        placa_b650 = next(
            fila for fila in filas
            if fila["modelo"] == "placa_madre" and fila["campos"]["chipset"] == "B650"
        )
        self.assertEqual(placa_b650["campos"]["socket_cpu"], "AM5")
        self.assertEqual(placa_b650["campos"]["tipo_ram_soportado"], "DDR5")

    def test_roundtrip_del_generador(self):
        catalogo = build_catalog()
        filas, _, _ = _fuentes()
        self.assertEqual(
            [(fila["modelo"], fila["pk"], fila["nombre"]) for fila in catalogo],
            [(fila["modelo"], fila["pk"], fila["nombre"]) for fila in filas],
        )

    def test_marca_demo_reconoce_nombres_de_prueba(self):
        self.assertTrue(es_fila_demo("Intel CPU Serie Test 001", "Procesador de prueba", "AMD Ryzen 5 5600"))
        self.assertFalse(es_fila_demo("Procesador de vitrina", "Unidad de exhibición", "AMD Ryzen 5 5600"))
        self.assertTrue(es_fila_demo("AMD Ryzen 5 5600", "Otra descripción", "AMD Ryzen 5 5600"))


class SincronizarCatalogoDemoTests(TestCase):
    def test_dry_run_no_escribe(self):
        marca = Proveedor.objects.create(nombre="Marca Ajena")
        Procesador.objects.create(
            pk=1,
            proveedor=marca,
            nombre="Intel CPU Serie Test 001 5c",
            descripcion="Procesador de prueba #1.",
            precio=Decimal("1000.00"),
            stock=6,
            socket="AM4",
            nucleos=4,
            frecuencia_base=Decimal("3.50"),
            potencia_referencia_watts=65,
        )
        salida = io.StringIO()
        call_command("sincronizar_catalogo_demo", "--dry-run", stdout=salida)
        cpu = Procesador.objects.get(pk=1)
        self.assertEqual(cpu.nombre, "Intel CPU Serie Test 001 5c")
        self.assertEqual(cpu.proveedor_id, marca.pk)
        self.assertIn("Dry-run", salida.getvalue())
        self.assertIn("Actualizados: 1", salida.getvalue())

    def test_apply_respeta_reales_pedidos_y_proveedor_por_nombre(self):
        primera = Proveedor.objects.create(nombre="ZZZ Primera")
        ajena = Proveedor.objects.create(nombre="Marca Ajena")
        vitrina = Proveedor.objects.create(nombre="Vitrina Local")
        Procesador.objects.create(
            pk=1,
            proveedor=ajena,
            nombre="Intel CPU Serie Test 001 5c",
            descripcion="Procesador de prueba #1.",
            precio=Decimal("1000.00"),
            stock=6,
            socket="LGA1700",
            nucleos=8,
            frecuencia_base=Decimal("2.50"),
            potencia_referencia_watts=65,
        )
        Procesador.objects.create(
            pk=50,
            proveedor=vitrina,
            nombre="Procesador de vitrina",
            descripcion="Unidad de exhibición.",
            precio=Decimal("10.00"),
            stock=3,
            socket="AM4",
            nucleos=4,
            frecuencia_base=Decimal("3.50"),
            potencia_referencia_watts=65,
        )
        usuario = User.objects.create_user("cliente-demo", password="clave-demo")
        pedido = Pedido.objects.create(
            usuario=usuario,
            total_monto=Decimal("1000.00"),
            direccion_envio="Calle 1",
            estado="PENDIENTE",
        )
        item = ItemPedido.objects.create(
            pedido=pedido,
            producto_nombre="Intel CPU Serie Test 001 5c",
            producto_tipo="CPU",
            precio_unitario=Decimal("1000.00"),
            cantidad=1,
            producto_modelo="procesador",
            producto_pk=1,
        )
        destino = next(fila for fila in build_catalog() if fila["modelo"] == "procesador" and fila["pk"] == 1)

        salida = io.StringIO()
        call_command("sincronizar_catalogo_demo", "--apply", stdout=salida)
        cpu = Procesador.objects.select_related("proveedor").get(pk=1)
        self.assertEqual(cpu.nombre, destino["nombre"])
        self.assertEqual(cpu.proveedor.nombre, destino["marca"])
        self.assertNotEqual(cpu.proveedor_id, primera.pk)
        self.assertEqual(cpu.socket, destino["campos"]["socket"])
        real = Procesador.objects.get(pk=50)
        self.assertEqual(real.nombre, "Procesador de vitrina")
        self.assertEqual(real.stock, 3)
        self.assertEqual(real.proveedor_id, vitrina.pk)
        item.refresh_from_db()
        pedido.refresh_from_db()
        self.assertEqual(item.producto_nombre, "Intel CPU Serie Test 001 5c")
        self.assertEqual(pedido.estado, "PENDIENTE")
        self.assertEqual(pedido.total_monto, Decimal("1000.00"))
        self.assertEqual(Procesador.objects.count(), 100)
        self.assertEqual(TarjetaGrafica.objects.count(), 100)
        self.assertFalse(Procesador.objects.filter(nombre__icontains="Serie Test").exists())
        self.assertIn("Omitidos por ser registros reales: 1", salida.getvalue())

        segunda = io.StringIO()
        call_command("sincronizar_catalogo_demo", "--apply", stdout=segunda)
        texto = segunda.getvalue()
        self.assertIn("Insertados: 0", texto)
        self.assertIn("Actualizados: 0", texto)
        self.assertIn("Sin cambios: 999", texto)
        self.assertEqual(Procesador.objects.get(pk=50).nombre, "Procesador de vitrina")

    def test_sincronizar_filas_no_usa_id_fijo_de_proveedor(self):
        Proveedor.objects.create(nombre="Otra Marca")
        amd = Proveedor.objects.create(nombre="AMD")
        fila = next(item for item in build_catalog() if item["modelo"] == "procesador" and item["pk"] == 1)
        resumen = sincronizar_filas([fila], apply=True)
        cpu = Procesador.objects.get(pk=1)
        self.assertEqual(resumen["insertados"], 1)
        self.assertEqual(cpu.proveedor_id, amd.pk)
        self.assertNotEqual(cpu.proveedor_id, 1)
