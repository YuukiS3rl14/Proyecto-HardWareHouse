"""Reseñas, teléfono de contacto y páginas 404/500.

No había pruebas de calificaciones. El correo ya se cubre en
core/test_correo_emailjs.py. El usuario pidió: "Agregar pruebas para
comprobar" medias estrellas, límites, EmailJS con mocks, 404 y 500.
"""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Avg
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.calificaciones import validar_media_estrella
from core.models import Comentario, Procesador, Proveedor
from core.telefonos import normalizar_telefono

_HOSTS = {'ALLOWED_HOSTS': ['testserver', 'localhost']}


def cpu(marca, nombre='CPU reseña', stock=4):
    return Procesador.objects.create(
        proveedor=marca, nombre=nombre, precio=Decimal('10000'), stock=stock,
        socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
    )


class CalificacionTests(TestCase):
    def setUp(self):
        self.marca = Proveedor.objects.create(nombre='Marca Reseña')
        self.producto = cpu(self.marca)
        self.usuario = User.objects.create_user('lector', 'lector@example.com', 'clave-resena-123')
        self.url = reverse('core:agregar_comentario', args=['procesador', self.producto.pk])

    def _datos(self, **cambios):
        datos = {
            'titulo': 'Muy buena pieza',
            'texto': 'Funciona estable en el armado.',
            'calificacion': '4.5',
        }
        datos.update(cambios)
        return datos

    def test_acepta_medios_puntos_y_el_promedio_los_conserva(self):
        for nota in ('0.5', '1.0', '1.5', '2.0', '2.5', '3.0', '3.5', '4.0', '4.5', '5.0'):
            self.assertEqual(validar_media_estrella(nota), Decimal(nota))
        self.client.force_login(self.usuario)
        self.client.post(self.url, self._datos())
        otro = User.objects.create_user('otro', 'otro@example.com', 'clave-resena-123')
        Comentario.objects.create(
            usuario=otro, titulo='Entera previa', texto='Sigue publicada.',
            calificacion=4, procesador=self.producto,
        )
        notas = list(Comentario.objects.values_list('calificacion', flat=True))
        self.assertIn(Decimal('4.5'), notas)
        self.assertIn(Decimal('4.0'), notas)
        promedio = Comentario.objects.aggregate(promedio=Avg('calificacion'))['promedio']
        self.assertEqual(promedio, Decimal('4.25'))
        ficha = self.client.get(reverse('core:detalle', args=['procesador', self.producto.pk]))
        self.assertContains(ficha, '4,25 de 5 estrellas')
        self.assertContains(ficha, 'hw-star-read is-half')

    def test_rechaza_fuera_de_rango_y_pasos_invalidos(self):
        for nota in ('0', '0.0', '5.5', '6', '3.7', '-1'):
            with self.assertRaises(ValidationError):
                validar_media_estrella(nota)
        self.client.force_login(self.usuario)
        respuesta = self.client.post(self.url, self._datos(calificacion='3.7', titulo='No debe guardarse'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'No debe guardarse')
        self.assertContains(respuesta, 'medios puntos')
        self.assertFalse(Comentario.objects.filter(titulo='No debe guardarse').exists())

    def test_respeta_limite_de_caracteres_y_conserva_el_texto(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(self.url, self._datos(
            titulo='T' * 101,
            texto='R' * 1501,
            calificacion='5.0',
        ))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'T' * 101)
        self.assertContains(respuesta, '100 caracteres')
        self.assertContains(respuesta, '1500 caracteres')
        self.assertEqual(Comentario.objects.count(), 0)
        valida = self.client.post(self.url, self._datos(titulo='Cabe', texto='R' * 1500))
        self.assertRedirects(valida, reverse('core:detalle', args=['procesador', self.producto.pk]))
        self.assertEqual(Comentario.objects.get().texto, 'R' * 1500)

    def test_solo_un_usuario_autenticado_puede_publicar(self):
        anonimo = self.client.post(self.url, self._datos())
        self.assertEqual(anonimo.status_code, 302)
        self.assertIn('/login/', anonimo.url)
        self.assertEqual(Comentario.objects.count(), 0)
        self.client.force_login(self.usuario)
        self.client.post(self.url, self._datos(titulo='Publicada'))
        self.assertEqual(Comentario.objects.get().usuario, self.usuario)


class TelefonoTests(TestCase):
    def _formulario(self, **cambios):
        from core.forms import ContactoForm
        datos = {
            'nombre': 'Ana Soto',
            'email': 'ana@example.com',
            'telefono_pais': 'CL',
            'telefono_nacional': '912345678',
            'asunto': 'Consulta',
            'mensaje': 'Hola',
        }
        datos.update(cambios)
        return ContactoForm(datos)

    def test_chile_normaliza_sin_duplicar_el_prefijo(self):
        self.assertEqual(normalizar_telefono('CL', '9 1234 5678'), '+56912345678')
        self.assertEqual(normalizar_telefono('CL', '+56 9 1234 5678'), '+56912345678')
        self.assertEqual(normalizar_telefono('CL', '56912345678'), '+56912345678')

    def test_rechaza_un_movil_chileno_mal_formado_y_acepta_otro_pais(self):
        with self.assertRaises(ValidationError):
            normalizar_telefono('CL', '812345678')
        self.assertEqual(normalizar_telefono('AR', '9112345678'), '+549112345678')
        self.assertEqual(normalizar_telefono('CL', ''), '')
        formulario = self._formulario()
        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertEqual(formulario.cleaned_data['telefono'], '+56912345678')
        self.assertFalse(self._formulario(telefono_nacional='812345678').is_valid())
        self.assertFalse(self._formulario(mensaje='m' * 2001).is_valid())
        self.assertFalse(self._formulario(nombre='n' * 101).is_valid())
        self.assertFalse(self._formulario(asunto='a' * 121).is_valid())
        vacio = self._formulario(telefono_nacional='')
        self.assertTrue(vacio.is_valid(), vacio.errors)
        self.assertEqual(vacio.cleaned_data['telefono'], '')


class ErrorPageTests(TestCase):
    def setUp(self):
        self.marca = Proveedor.objects.create(nombre='Marca Error')
        self.producto = cpu(self.marca, stock=0)

    def test_url_inexistente_es_404_generico(self):
        with override_settings(DEBUG=False, **_HOSTS):
            respuesta = self.client.get('/esta-ruta-no-existe/')
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, 'Página no encontrada', status_code=404)
        self.assertNotContains(respuesta, 'Producto no encontrado', status_code=404)
        self.assertNotContains(respuesta, 'Traceback', status_code=404)
        self.assertContains(respuesta, reverse('core:index'), status_code=404)

    def test_producto_inexistente_es_404_y_el_agotado_sigue_visible(self):
        faltante = self.client.get(reverse('core:detalle', args=['procesador', 999999]))
        self.assertEqual(faltante.status_code, 404)
        self.assertContains(faltante, 'Producto no encontrado', status_code=404)
        self.assertContains(faltante, 'ya no está disponible', status_code=404)
        self.assertContains(faltante, reverse('core:tienda'), status_code=404)
        self.assertNotContains(faltante, 'Traceback', status_code=404)
        agotado = self.client.get(reverse('core:detalle', args=['procesador', self.producto.pk]))
        self.assertEqual(agotado.status_code, 200)
        self.assertContains(agotado, 'Agotado')

    def test_error_interno_muestra_la_pagina_y_se_registra(self):
        cliente = Client(raise_request_exception=False)
        with override_settings(DEBUG=False, **_HOSTS):
            with patch('core.views.render', side_effect=RuntimeError('token-secreto-xyz')):
                with self.assertLogs('django.request', level='ERROR') as logs:
                    respuesta = cliente.get(reverse('core:contacto'))
        self.assertEqual(respuesta.status_code, 500)
        self.assertContains(respuesta, 'Algo salió mal', status_code=500)
        self.assertContains(respuesta, reverse('core:index'), status_code=500)
        self.assertNotContains(respuesta, 'token-secreto-xyz', status_code=500)
        self.assertNotContains(respuesta, 'Traceback', status_code=500)
        self.assertTrue(any('token-secreto-xyz' in linea for linea in logs.output))

    def test_un_pedido_ajeno_no_se_convierte_en_pagina_de_producto(self):
        usuario = User.objects.create_user('cliente-error', 'cliente@example.com', 'clave-error-123')
        self.client.force_login(usuario)
        with override_settings(DEBUG=False, **_HOSTS):
            respuesta = self.client.get(reverse('core:detalle_pedido', args=[999999]))
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, 'Página no encontrada', status_code=404)
        self.assertNotContains(respuesta, 'Producto no encontrado', status_code=404)
        self.client.logout()
        favorito = self.client.post(reverse('core:toggle_favorito'))
        self.assertEqual(favorito.status_code, 302)
        self.assertIn('/login/', favorito.url)
