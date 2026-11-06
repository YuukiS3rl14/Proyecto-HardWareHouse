from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN

from core.correo import notificar_pedido_pagado
from core.models import ItemPedido, Pedido, Procesador, Proveedor
from core.payments import clp_a_usd, confirmar_pago_paypal

RECEPTOR = 'sb-merchant@business.example.com'
CLAVE_PRIVADA = 'private-test-secret'
AJUSTES = dict(
    PAYPAL_TEST=True,
    PAYPAL_RECEIVER_EMAIL=RECEPTOR,
    CLP_TO_USD_RATE=950,
    EMAILJS_SERVICE_ID='service-test',
    EMAILJS_TEMPLATE_CONTACTO='template-contacto',
    EMAILJS_TEMPLATE_PEDIDO='template-pedido',
    EMAILJS_PUBLIC_KEY='public-test',
    EMAILJS_PRIVATE_KEY=CLAVE_PRIVADA,
    CONTACTO_CORREO_LIMITE=2,
    CONTACTO_CORREO_VENTANA=600,
    EMAILJS_RECLAMO_SEGUNDOS=120,
    CONTACTO_EMAIL='contacto@hardwarehouse.cl',
)

CORREOS_PERSONALES = (
    'manuelescool11@gmail.com',
    'yxds3rl14@gmail.com',
)


class _Respuesta:
    def __init__(self, status_code):
        self.status_code = status_code


def _contacto(**cambios):
    datos = {
        'nombre': 'Ana Soto',
        'email': 'ana@example.com',
        'telefono': '+56 9 1234 5678',
        'asunto': 'Consulta técnica',
        'mensaje': 'Quiero orientación para un armado.',
    }
    datos.update(cambios)
    return datos


@override_settings(**AJUSTES)
class CorreoEmailJsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.usuario = User.objects.create_user(
            'comprador-mail', 'cuenta@example.com', 'clave-correo-123',
        )
        self.marca = Proveedor.objects.create(nombre='Marca Correo')
        self.cpu = Procesador.objects.create(
            proveedor=self.marca, nombre='CPU Aviso', precio=Decimal('95000'), stock=5,
            socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
        )

    def pedido(self):
        pedido = Pedido.objects.create(
            usuario=self.usuario,
            estado='PENDIENTE',
            total_monto=Decimal('95000.00'),
            direccion_envio='Por definir',
        )
        ItemPedido.objects.create(
            pedido=pedido,
            producto_nombre='CPU Aviso',
            producto_tipo='CPU',
            precio_unitario=Decimal('95000.00'),
            cantidad=1,
            producto_modelo='procesador',
            producto_pk=self.cpu.pk,
        )
        return pedido

    def ipn(self, pedido, txn_id='TXN-MAIL', **cambios):
        datos = dict(
            payment_status='Completed',
            txn_id=txn_id,
            invoice=str(pedido.paypal_invoice),
            mc_gross=clp_a_usd(pedido.total_monto),
            mc_currency='USD',
            receiver_email=RECEPTOR,
            test_ipn=True,
            payer_email='cliente@example.com',
            first_name='Ana',
            last_name='Soto',
        )
        datos.update(cambios)
        return PayPalIPN.objects.create(**datos)

    def test_el_contacto_valido_usa_la_plantilla_y_no_expone_la_clave(self):
        with patch('core.correo.requests.post', return_value=_Respuesta(200)) as envio:
            respuesta = self.client.post(reverse('core:contacto'), _contacto(), follow=True)

        self.assertContains(respuesta, 'Recibimos tu mensaje')
        self.assertNotContains(respuesta, CLAVE_PRIVADA)
        cuerpo = envio.call_args.kwargs['json']
        self.assertEqual(envio.call_args.args[0], 'https://api.emailjs.com/api/v1.0/email/send')
        self.assertEqual(cuerpo['service_id'], 'service-test')
        self.assertEqual(cuerpo['template_id'], 'template-contacto')
        self.assertEqual(cuerpo['user_id'], 'public-test')
        self.assertEqual(cuerpo['accessToken'], CLAVE_PRIVADA)
        self.assertNotIn('accessToken', cuerpo['template_params'])
        parametros = cuerpo['template_params']
        self.assertEqual(parametros['from_email'], 'ana@example.com')
        self.assertEqual(parametros['email'], 'ana@example.com')
        self.assertEqual(parametros['mensaje'], 'Quiero orientación para un armado.')
        self.assertEqual(parametros['reply_to'], 'ana@example.com')
        self.assertEqual(parametros['contacto_destino'], 'contacto@hardwarehouse.cl')
        self.assertEqual(parametros['destino'], 'contacto@hardwarehouse.cl')
        self.assertNotIn('cliente_email', parametros)
        for correo in CORREOS_PERSONALES:
            self.assertNotIn(correo, str(parametros))
        self.assertContains(respuesta, 'contacto@hardwarehouse.cl')
        self.assertNotContains(respuesta, 'contacto@techparts.cl')

    def test_el_contacto_invalido_o_sin_servicio_no_llama_a_emailjs(self):
        with patch('core.correo.requests.post') as envio:
            invalido = self.client.post(reverse('core:contacto'), _contacto(nombre='Juan2'))
        self.assertEqual(invalido.status_code, 200)
        self.assertContains(invalido, 'letras')
        envio.assert_not_called()

        with override_settings(EMAILJS_PRIVATE_KEY=''):
            with patch('core.correo.requests.post') as envio:
                fallo = self.client.post(reverse('core:contacto'), _contacto())
        self.assertEqual(fallo.status_code, 200)
        self.assertContains(fallo, 'No pudimos enviar el mensaje')
        self.assertNotContains(fallo, CLAVE_PRIVADA)
        envio.assert_not_called()

    def test_un_error_de_emailjs_no_confirma_el_envio_y_el_limite_corta_las_llamadas(self):
        with patch('core.correo.requests.post', return_value=_Respuesta(500)) as envio:
            error = self.client.post(reverse('core:contacto'), _contacto())
        self.assertEqual(error.status_code, 200)
        self.assertContains(error, 'No pudimos enviar el mensaje')
        self.assertEqual(envio.call_count, 1)

        with patch('core.correo.requests.post', return_value=_Respuesta(200)) as envio:
            self.client.post(reverse('core:contacto'), _contacto(mensaje='Segundo aviso.'))
            bloqueado = self.client.post(reverse('core:contacto'), _contacto(mensaje='Tercer aviso.'))
        self.assertEqual(envio.call_count, 1)
        self.assertContains(bloqueado, 'Demasiados mensajes')

    def test_el_pedido_pagado_avisa_una_vez_con_los_datos_guardados(self):
        pedido = self.pedido()
        self.cpu.nombre = 'CPU renombrada después'
        self.cpu.save(update_fields=['nombre'])

        with patch('core.correo.requests.post', return_value=_Respuesta(200)) as envio:
            self.assertEqual(confirmar_pago_paypal(self.ipn(pedido)), 'pagado')
            self.assertEqual(confirmar_pago_paypal(PayPalIPN.objects.get(txn_id='TXN-MAIL')), 'ya_procesado')

        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        aviso = pedido.aviso_correo
        parametros = envio.call_args.kwargs['json']['template_params']
        self.assertEqual(envio.call_count, 1)
        self.assertEqual(envio.call_args.kwargs['json']['template_id'], 'template-pedido')
        self.assertEqual(pedido.estado, 'PAGADO')
        self.assertEqual(self.cpu.stock, 4)
        detalle = '1 x CPU Aviso (CPU) — 95.000 CLP c/u — 95.000 CLP'
        self.assertEqual(parametros['cliente_email'], 'cuenta@example.com')
        self.assertEqual(parametros['to_email'], 'cuenta@example.com')
        self.assertEqual(parametros['email'], 'cuenta@example.com')
        self.assertNotEqual(parametros['cliente_email'], 'cliente@example.com')
        self.assertNotIn('contacto_destino', parametros)
        self.assertNotEqual(parametros['cliente_email'], 'contacto@hardwarehouse.cl')
        for correo in CORREOS_PERSONALES:
            self.assertNotIn(correo, str(parametros))
        self.assertEqual(parametros['cliente_nombre'], 'Ana Soto')
        self.assertEqual(parametros['pedido_id'], str(pedido.id))
        self.assertEqual(parametros['total_clp'], '95.000 CLP')
        self.assertEqual(parametros['detalle_productos'], detalle)
        self.assertEqual(parametros['productos'], detalle)
        self.assertNotIn('CPU renombrada', parametros['detalle_productos'])
        self.assertEqual(pedido.pago_boleta.email_comprador, 'cliente@example.com')
        self.assertEqual(parametros['transaccion_id'], 'TXN-MAIL')
        self.assertIsNotNone(aviso.enviado_en)
        self.assertIsNone(aviso.reclamo)

    def test_sin_correo_de_cuenta_el_aviso_usa_el_pagador_verificado(self):
        self.usuario.email = 'sandbox-sin-arroba'
        self.usuario.save(update_fields=['email'])
        pedido = self.pedido()

        with patch('core.correo.requests.post', return_value=_Respuesta(200)) as envio:
            self.assertEqual(confirmar_pago_paypal(self.ipn(pedido, txn_id='TXN-FALLBACK')), 'pagado')

        parametros = envio.call_args.kwargs['json']['template_params']
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'PAGADO')
        self.assertEqual(pedido.pago_boleta.email_comprador, 'cliente@example.com')
        self.assertEqual(parametros['cliente_email'], 'cliente@example.com')
        self.assertEqual(parametros['to_email'], 'cliente@example.com')
        self.assertEqual(parametros['cliente_nombre'], 'Ana Soto')
        self.assertEqual(parametros['pedido_id'], str(pedido.id))
        self.assertEqual(parametros['total_clp'], '95.000 CLP')
        self.assertEqual(
            parametros['detalle_productos'],
            '1 x CPU Aviso (CPU) — 95.000 CLP c/u — 95.000 CLP',
        )

    def test_si_el_correo_falla_el_pago_queda_y_un_reintento_no_lo_duplica(self):
        pedido = self.pedido()
        respuestas = [_Respuesta(503), _Respuesta(200)]

        with patch('core.correo.requests.post', side_effect=respuestas) as envio:
            self.assertEqual(confirmar_pago_paypal(self.ipn(pedido, txn_id='TXN-REINTENTO')), 'pagado')
            pedido.refresh_from_db()
            self.cpu.refresh_from_db()
            self.assertEqual(pedido.estado, 'PAGADO')
            self.assertEqual(self.cpu.stock, 4)
            self.assertIsNone(pedido.aviso_correo.enviado_en)

            pedido.aviso_correo.reclamo = '11111111-1111-1111-1111-111111111111'
            pedido.aviso_correo.reclamo_en = timezone.now()
            pedido.aviso_correo.save(update_fields=['reclamo', 'reclamo_en'])
            self.assertEqual(notificar_pedido_pagado(pedido.id), 'omitido')
            self.assertEqual(envio.call_count, 1)

            pedido.aviso_correo.reclamo_en = timezone.now() - timedelta(minutes=5)
            pedido.aviso_correo.save(update_fields=['reclamo_en'])
            self.assertEqual(
                confirmar_pago_paypal(PayPalIPN.objects.get(txn_id='TXN-REINTENTO')),
                'ya_procesado',
            )

        pedido.refresh_from_db()
        aviso = pedido.aviso_correo
        aviso.refresh_from_db()
        self.assertEqual(pedido.estado, 'PAGADO')
        self.assertEqual(self.cpu.stock, 4)
        self.assertEqual(envio.call_count, 2)
        self.assertIsNotNone(aviso.enviado_en)
        with patch('core.correo.requests.post') as extra:
            self.assertEqual(notificar_pedido_pagado(pedido.id), 'omitido')
        extra.assert_not_called()

    def test_un_pago_no_confirmado_no_envia_correo_aunque_emailjs_explote(self):
        pedido = self.pedido()
        with patch('core.correo.requests.post') as envio:
            self.assertEqual(
                confirmar_pago_paypal(self.ipn(pedido, txn_id='TXN-PENDIENTE', payment_status='Pending')),
                'ignorado',
            )
        envio.assert_not_called()
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'PENDIENTE')

        with patch('core.correo.notificar_pedido_pagado', side_effect=RuntimeError('correo caído')):
            self.assertEqual(confirmar_pago_paypal(self.ipn(pedido, txn_id='TXN-CAE')), 'pagado')
        pedido.refresh_from_db()
        self.cpu.refresh_from_db()
        self.assertEqual(pedido.estado, 'PAGADO')
        self.assertEqual(pedido.paypal_transaccion_id, 'TXN-CAE')
        self.assertEqual(self.cpu.stock, 4)

    def test_contacto_y_compra_no_llaman_a_smtp(self):
        with patch('core.correo.requests.post', return_value=_Respuesta(200)) as envio, \
             patch('django.core.mail.send_mail') as smtp, \
             patch('django.core.mail.EmailMessage.send') as mensaje:
            self.client.post(reverse('core:contacto'), _contacto())
            self.assertEqual(
                confirmar_pago_paypal(self.ipn(self.pedido(), txn_id='TXN-SIN-SMTP')),
                'pagado',
            )
        self.assertEqual(envio.call_count, 2)
        smtp.assert_not_called()
        mensaje.assert_not_called()
        self.assertNotEqual(settings.EMAIL_HOST, 'smtp.mx.cloudflare.net')


class DestinosCorreoTests(SimpleTestCase):
    def test_el_worker_reenvia_el_buzon_publico_a_las_dos_cuentas(self):
        raiz = Path(__file__).resolve().parents[1]
        worker = (raiz / 'cloudflare' / 'email-worker' / 'contacto-router.js').read_text(encoding='utf-8')
        self.assertIn('contacto@hardwarehouse.cl', worker)
        self.assertIn('trabajadorhardwarehouse@gmail.com', worker)
        self.assertIn('administradorhardwarehouse@gmail.com', worker)
        for correo in CORREOS_PERSONALES:
            self.assertNotIn(correo, worker)
        django_correo = (raiz / 'core' / 'correo.py').read_text(encoding='utf-8')
        self.assertNotIn('trabajadorhardwarehouse@gmail.com', django_correo)
        self.assertNotIn('administradorhardwarehouse@gmail.com', django_correo)
        for correo in CORREOS_PERSONALES:
            self.assertNotIn(correo, django_correo)
