from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse

from core.formato_clp import formatear_pesos, miles_clp
from core.models import Carrito, ItemCarrito, ItemPedido, Pedido, Procesador, Proveedor
from core.test_validacion_ux import crear_cpu


class FormatoPesosTests(TestCase):
    def test_montos_enteros_usan_punto_de_miles(self):
        self.assertEqual(formatear_pesos(0), '$0')
        self.assertEqual(formatear_pesos(1000), '$1.000')
        self.assertEqual(formatear_pesos(12500), '$12.500')
        self.assertEqual(formatear_pesos(500000), '$500.000')
        self.assertEqual(formatear_pesos(1250654), '$1.250.654')
        self.assertEqual(formatear_pesos(Decimal('1250654.40')), '$1.250.654')
        self.assertEqual(formatear_pesos(None), '$0')
        self.assertEqual(miles_clp(95000), '95.000')

    def test_el_filtro_de_plantilla_no_deja_espacios(self):
        html = Template('{% load formato_clp %}{{ valor|pesos }}').render(
            Context({'valor': Decimal('553990')}),
        )
        self.assertEqual(html, '$553.990')
        self.assertNotIn('\xa0', html)
        self.assertNotIn(' ', html)


class PaginasConPreciosTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('cliente-clp', 'clp@example.com', 'clave-clp')
        self.client.force_login(self.usuario)
        marca = Proveedor.objects.create(nombre='Marca CLP')
        self.cpu = crear_cpu(marca, 'CPU CLP', Decimal('1250654.00'), 3)
        carrito = Carrito.objects.create(usuario=self.usuario)
        ItemCarrito.objects.create(
            carrito=carrito,
            procesador=self.cpu,
            cantidad=1,
            precio_unitario=Decimal('1250654.00'),
        )
        self.pedido = Pedido.objects.create(
            usuario=self.usuario,
            total_monto=Decimal('500000.00'),
            direccion_envio='Calle de prueba 1',
            estado='PAGADO',
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            producto_nombre=self.cpu.nombre,
            producto_tipo=self.cpu.categoria,
            precio_unitario=Decimal('12500.00'),
            cantidad=1,
            producto_modelo='procesador',
            producto_pk=self.cpu.pk,
        )

    def test_carrito_y_pedidos_muestran_puntos_sin_cambiar_el_monto(self):
        carrito = self.client.get(reverse('core:carrito'))
        pedidos = self.client.get(reverse('core:mis_pedidos'))
        detalle = self.client.get(reverse('core:detalle_pedido', args=[self.pedido.pk]))

        self.assertContains(carrito, '$1.250.654')
        self.assertContains(carrito, 'data-precio="1250654.00"')
        self.assertNotContains(carrito, '$1 250 654')
        self.assertContains(pedidos, '$500.000 CLP')
        self.assertContains(detalle, '$12.500 CLP')
        self.assertContains(detalle, '$500.000 CLP')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.total_monto, Decimal('500000.00'))
        self.assertEqual(self.cpu.precio, Decimal('1250654.00'))

    def test_los_scripts_comparten_el_formateador(self):
        base = Path(__file__).resolve().parent / 'static' / 'core' / 'js'
        formato = (base / 'formato-clp.js').read_text(encoding='utf-8')
        armador = (base / 'pc-builder.js').read_text(encoding='utf-8')
        graficos = (base / 'admin-charts.js').read_text(encoding='utf-8')
        chat = (base / 'chat-widget.js').read_text(encoding='utf-8')

        self.assertIn('window.hwPesos', formato)
        self.assertIn("replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.')", formato)
        self.assertIn('window.hwPesos', armador)
        self.assertIn('window.hwPesos', graficos)
        self.assertIn('window.hwPesos', chat)
        self.assertNotIn("toLocaleString('es-CL')", armador)
        self.assertNotIn('style: "currency"', graficos)

        pagina = self.client.get(reverse('core:armado'))
        self.assertContains(pagina, 'formato-clp.js?v=20261108o')
        self.assertContains(pagina, 'pc-builder.js?v=selector20')
