from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import SimpleTestCase
from django.urls import reverse


def _estatico(nombre):
    ruta = finders.find(nombre)
    if not ruta:
        raise AssertionError(f'No está el archivo estático {nombre}.')
    return Path(ruta).read_text(encoding='utf-8')


class ContactoEstaticoTests(SimpleTestCase):
    def test_main_js_ya_no_bloquea_el_envio(self):
        texto = _estatico('core/js/main.js')

        self.assertNotIn('contactForm', texto)
        self.assertNotIn('popup-bg', texto)
        self.assertNotIn('popup-msg', texto)
        self.assertNotIn('preventDefault', texto)
        self.assertNotIn('closePopup', texto)
        self.assertIn('.back-to-top', texto)
        self.assertIn('.vendor-carousel', texto)
        self.assertIn('.related-carousel', texto)
        self.assertIn('addCart', texto)
        self.assertFalse(finders.find('core/js/login-registro.js'))

    def test_contacto_js_solo_frena_datos_invalidos(self):
        texto = _estatico('core/js/contacto.js')

        self.assertIn("getElementById('contactForm')", texto)
        self.assertLess(texto.index('if (!mensaje)'), texto.index('event.preventDefault()'))
        self.assertIn('nombreOk', texto)
        self.assertIn('telefonoInvalido', texto)
        self.assertIn('preventDefault', texto)

    def test_la_pagina_publica_el_post_y_renueva_main_js(self):
        respuesta = self.client.get(reverse('core:contacto'))
        html = respuesta.content.decode()

        self.assertContains(respuesta, 'method="post"')
        self.assertContains(respuesta, 'id="contactForm"')
        self.assertContains(respuesta, 'core/js/main.js?v=contacto1')
        self.assertContains(respuesta, 'core/js/contacto.js')
        self.assertContains(respuesta, 'Chile (+56)')
        self.assertContains(respuesta, 'name="telefono_nacional"')
        self.assertLess(html.index('core/js/main.js'), html.index('core/js/contacto.js'))
        self.assertNotIn('popup-bg', html)
        self.assertNotIn('login-registro.js', html)
        self.assertNotIn('#popup-bg', _estatico('core/css/style2.css'))
