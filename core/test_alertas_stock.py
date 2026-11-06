from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from paypal.standard.ipn.models import PayPalIPN

from core.alertas_stock import ADVERTENCIA, AGOTADO, CRITICO, NORMAL, estado_stock, unidades_para_normal
from core.models import ItemPedido, MemoriaRam, Pedido, Procesador, Proveedor
from core.payments import clp_a_usd, confirmar_pago_paypal

RECEPTOR = 'sb-merchant@business.example.com'


def cpu(marca, nombre, stock, **extra):
    datos = dict(
        proveedor=marca,
        nombre=nombre,
        precio=Decimal('10000'),
        stock=stock,
        socket='AM5',
        nucleos=6,
        frecuencia_base=Decimal('3.50'),
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
class AlertasStockTests(TestCase):
    def setUp(self):
        self.marca = Proveedor.objects.create(nombre='Marca Stock')
        self.staff = User.objects.create_user(
            'trabajador-stock', 'trabajador@example.com', 'clave-stock-123', is_staff=True,
        )
        self.cliente = User.objects.create_user('cliente-stock', 'cliente-stock@example.com', 'clave-stock-123')

    def panel(self, usuario=None, **params):
        if usuario is not None:
            self.client.force_login(usuario)
        return self.client.get(reverse('core:alertas_stock'), params)

    def test_los_limites_por_defecto(self):
        self.assertEqual(estado_stock(0, 3, 5), AGOTADO)
        self.assertEqual(estado_stock(1, 3, 5), CRITICO)
        self.assertEqual(estado_stock(3, 3, 5), CRITICO)
        self.assertEqual(estado_stock(4, 3, 5), ADVERTENCIA)
        self.assertEqual(estado_stock(5, 3, 5), ADVERTENCIA)
        self.assertEqual(estado_stock(6, 3, 5), NORMAL)
        self.assertEqual(unidades_para_normal(0, 5), 6)
        self.assertEqual(unidades_para_normal(6, 5), 0)

    def test_el_panel_separa_los_estados_y_no_lista_el_normal(self):
        cpu(self.marca, 'Pieza cero', 0)
        cpu(self.marca, 'Pieza uno', 1)
        cpu(self.marca, 'Pieza tres', 3)
        cpu(self.marca, 'Pieza cuatro', 4)
        cpu(self.marca, 'Pieza cinco', 5)
        cpu(self.marca, 'Pieza seis', 6)
        respuesta = self.panel(self.staff)
        self.assertContains(respuesta, 'Pieza cero')
        self.assertContains(respuesta, 'Agotado')
        self.assertContains(respuesta, 'Pieza uno')
        self.assertContains(respuesta, 'Pieza tres')
        self.assertContains(respuesta, 'Crítico')
        self.assertContains(respuesta, 'Pieza cuatro')
        self.assertContains(respuesta, 'Pieza cinco')
        self.assertContains(respuesta, 'Advertencia')
        self.assertNotContains(respuesta, 'Pieza seis')

    def test_los_umbrales_propios_cambian_el_estado(self):
        pieza = cpu(self.marca, 'Umbral propio', 2, stock_minimo=1, stock_advertencia=2)
        self.assertEqual(estado_stock(pieza.stock, pieza.stock_minimo, pieza.stock_advertencia), ADVERTENCIA)
        pieza.stock = 1
        pieza.save(update_fields=['stock'])
        respuesta = self.panel(self.staff)
        self.assertContains(respuesta, 'Umbral propio')
        self.assertContains(respuesta, 'Crítico')
        pieza.stock = 3
        pieza.save(update_fields=['stock'])
        self.assertNotContains(self.panel(self.staff), 'Umbral propio')

    def test_un_umbral_invalido_no_se_guarda(self):
        pieza = cpu(self.marca, 'Umbral malo', 4)
        pieza.stock_minimo = 6
        pieza.stock_advertencia = 4
        with self.assertRaises(ValidationError):
            pieza.full_clean()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                pieza.save()
        pieza.refresh_from_db()
        self.assertEqual(pieza.stock, 4)
        self.assertEqual(pieza.stock_minimo, 3)
        self.assertEqual(pieza.stock_advertencia, 5)

    def test_anonimo_va_al_login_y_el_cliente_recibe_403(self):
        publico = self.client.get(reverse('core:tienda'))
        self.assertNotContains(publico, 'Control de stock')
        self.assertNotContains(publico, 'Inventario por revisar')
        anonimo = self.panel()
        self.assertEqual(anonimo.status_code, 302)
        self.assertIn('/login/', anonimo.url)
        self.assertEqual(self.panel(self.cliente).status_code, 403)

    def test_el_personal_consulta_pero_no_edita_sin_permiso(self):
        pieza = cpu(self.marca, 'Editable', 1)
        sin_permiso = self.panel(self.staff)
        self.assertEqual(sin_permiso.status_code, 200)
        self.assertContains(sin_permiso, 'Sin permiso de edición')
        self.assertNotContains(sin_permiso, f'/admin/core/procesador/{pieza.pk}/change/')
        self.staff.user_permissions.add(Permission.objects.get(codename='change_procesador'))
        self.staff = User.objects.get(pk=self.staff.pk)
        con_permiso = self.panel(self.staff)
        self.assertContains(con_permiso, f'/admin/core/procesador/{pieza.pk}/change/')

    def test_los_contadores_no_duplican_y_el_orden_sigue_la_urgencia(self):
        cpu(self.marca, 'Aviso medio', 5)
        cpu(self.marca, 'Aviso grave', 0)
        cpu(self.marca, 'Aviso bajo', 2)
        MemoriaRam.objects.create(
            proveedor=self.marca, nombre='RAM baja', precio=Decimal('8000'), stock=1,
            capacidad_gb=16, tipo_ddr='DDR5', velocidad_mhz=5600,
        )
        respuesta = self.panel(self.staff)
        html = respuesta.content.decode()
        self.assertEqual(html.count('Aviso grave'), 1)
        self.assertLess(html.index('Aviso grave'), html.index('RAM baja'))
        self.assertLess(html.index('RAM baja'), html.index('Aviso bajo'))
        self.assertLess(html.index('Aviso bajo'), html.index('Aviso medio'))
        self.assertContains(respuesta, '>1<')
        self.assertContains(respuesta, '>2<')
        self.assertContains(respuesta, '>4<')

    def test_reponer_quita_la_alerta_y_bajar_el_stock_la_crea(self):
        pieza = cpu(self.marca, 'Reposicion', 8)
        self.assertNotContains(self.panel(self.staff), 'Reposicion')
        pieza.stock = 5
        pieza.save(update_fields=['stock'])
        self.assertContains(self.panel(self.staff), 'Reposicion')
        self.assertContains(self.panel(self.staff), 'Advertencia')
        pieza.stock = 10
        pieza.save(update_fields=['stock'])
        respuesta = self.panel(self.staff)
        self.assertNotContains(respuesta, 'Reposicion')
        self.assertContains(respuesta, 'niveles de inventario son adecuados')

    def test_una_pieza_demo_agotada_no_avisa(self):
        demo = Proveedor.objects.create(nombre='DEMO')
        cpu(demo, 'Kit ficticio', 0)
        cpu(self.marca, 'DEMO suelto', 0)
        respuesta = self.panel(self.staff)
        self.assertNotContains(respuesta, 'Kit ficticio')
        self.assertNotContains(respuesta, 'DEMO suelto')
        self.assertContains(respuesta, 'niveles de inventario son adecuados')

    def test_el_aviso_de_sesion_no_se_repite_hasta_que_empeora(self):
        pieza = cpu(self.marca, 'Sesion', 4)
        self.client.force_login(self.staff)
        primero = self.client.get(reverse('core:index'))
        self.assertContains(primero, 'Inventario por revisar')
        self.assertContains(primero, 'En advertencia: 1')
        segundo = self.client.get(reverse('core:tienda'))
        self.assertNotContains(segundo, 'Inventario por revisar')
        self.assertContains(segundo, 'Control de stock')
        pieza.stock = 0
        pieza.save(update_fields=['stock'])
        tercero = self.client.get(reverse('core:index'))
        self.assertContains(tercero, 'Inventario por revisar')
        self.assertContains(tercero, 'Agotados: 1')

    def test_el_pago_descuenta_una_vez_y_la_alerta_lee_ese_stock(self):
        pieza = cpu(self.marca, 'Compra stock', 6)
        pedido = Pedido.objects.create(
            usuario=self.cliente, estado='PENDIENTE', total_monto=Decimal('10000.00'), direccion_envio='Local',
        )
        ItemPedido.objects.create(
            pedido=pedido, producto_nombre='Compra stock', producto_tipo='CPU',
            precio_unitario=Decimal('10000.00'), cantidad=1,
            producto_modelo='procesador', producto_pk=pieza.pk,
        )
        ipn = PayPalIPN.objects.create(
            payment_status='Completed', txn_id='TXN-STOCK', invoice=str(pedido.paypal_invoice),
            mc_gross=clp_a_usd(pedido.total_monto), mc_currency='USD', receiver_email=RECEPTOR,
            test_ipn=True, payer_email='cliente-stock@example.com',
        )
        self.assertEqual(confirmar_pago_paypal(ipn), 'pagado')
        self.assertEqual(confirmar_pago_paypal(PayPalIPN.objects.get(txn_id='TXN-STOCK')), 'ya_procesado')
        pieza.refresh_from_db()
        self.assertEqual(pieza.stock, 5)
        self.assertContains(self.panel(self.staff), 'Compra stock')
        self.assertContains(self.panel(self.staff), 'Advertencia')
