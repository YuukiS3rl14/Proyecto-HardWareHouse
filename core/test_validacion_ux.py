from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.catalogo.registry import CATALOGO_MODELOS
from core.forms import ContactoForm, RegistroForm
from core.knowledge.service import texto_faq
from core.models import Carrito, ItemCarrito, PagoBoleta, Pedido, Procesador, Proveedor


def crear_cpu(marca, nombre, precio, stock):
    return Procesador.objects.create(
        proveedor=marca,
        nombre=nombre,
        precio=precio,
        stock=stock,
        socket='AM5',
        nucleos=6,
        frecuencia_base=Decimal('3.50'),
    )


class CantidadCarritoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('cliente', 'cliente@example.com', 'clave-cliente')
        self.client.force_login(self.usuario)
        self.marca = Proveedor.objects.create(nombre='Marca UX')
        self.cpu = crear_cpu(self.marca, 'CPU UX', Decimal('19990.00'), 2)
        self.agregar = reverse('core:agregar_al_carrito')

    def post_agregar(self, quantity):
        return self.client.post(self.agregar, {
            'product_id': self.cpu.id,
            'model_name': 'procesador',
            'quantity': quantity,
            'precio': '1',
            'total': '1',
        })

    def test_rechaza_cantidades_invalidas_y_no_infla_el_total(self):
        for cantidad in ('sad', '0', '-1', '1.5', '', '1231'):
            respuesta = self.post_agregar(cantidad)
            self.assertEqual(respuesta.status_code, 302, cantidad)
            self.assertEqual(ItemCarrito.objects.count(), 0, cantidad)
        self.cpu.refresh_from_db()
        self.assertEqual(self.cpu.stock, 2)

        ajax = self.client.post(
            self.agregar,
            {
                'product_id': self.cpu.id,
                'model_name': 'procesador',
                'quantity': 'sad',
                'precio_unitario': '1',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(ajax.status_code, 400)
        self.assertEqual(ajax.json()['status'], 'error')
        self.assertIn('entero', ajax.json()['message'])

        self.post_agregar('1')
        item = ItemCarrito.objects.get()
        self.assertEqual(item.cantidad, 1)
        self.assertEqual(item.precio_unitario, self.cpu.precio)

        actualizar = reverse('core:actualizar_carrito', args=[item.id])
        for cantidad in ('sad', '0', '-3', '2.5', '', '1231'):
            respuesta = self.client.post(actualizar, {
                'quantity': cantidad,
                'precio_unitario': '1',
                'total': '999999',
            })
            self.assertEqual(respuesta.status_code, 302, cantidad)
            item.refresh_from_db()
            self.assertEqual(item.cantidad, 1, cantidad)
            self.assertEqual(item.precio_unitario, Decimal('19990.00'), cantidad)

        self.client.post(actualizar, {'quantity': '2', 'precio_unitario': '1', 'total': '1'})
        item.refresh_from_db()
        carrito = Carrito.objects.get(usuario=self.usuario)
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(item.precio_unitario, Decimal('19990.00'))
        self.assertEqual(carrito.get_total_precio(), Decimal('39980.00'))
        self.assertEqual(item.get_total(), Decimal('39980.00'))

        self.cpu.stock = 1
        self.cpu.save(update_fields=['stock'])
        pedidos = Pedido.objects.count()
        boletas = PagoBoleta.objects.count()
        checkout = self.client.get(reverse('core:checkout'))
        self.assertRedirects(checkout, reverse('core:carrito'), fetch_redirect_response=False)
        self.cpu.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(self.cpu.stock, 1)
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(Pedido.objects.count(), pedidos)
        self.assertEqual(PagoBoleta.objects.count(), boletas)
        self.assertContains(self.client.get(reverse('core:carrito')), 'No hay suficiente stock')


class FormulariosYBusquedaTests(TestCase):
    def test_contacto_rechaza_digitos_y_acepta_un_nombre_valido(self):
        invalido = ContactoForm(data={
            'nombre': 'Juan2',
            'email': 'ana@example.com',
            'telefono': '+56 9 1234 5678',
            'asunto': 'Consulta',
            'mensaje': 'Hola',
        })
        self.assertFalse(invalido.is_valid())
        self.assertIn('letras', invalido.errors['nombre'][0])

        correo = ContactoForm(data={
            'nombre': 'María',
            'email': 'no-es-correo',
            'asunto': 'Consulta',
            'mensaje': 'Hola',
        })
        self.assertFalse(correo.is_valid())
        self.assertIn('correo', correo.errors['email'][0].lower())

        respuesta = self.client.post(reverse('core:contacto'), {
            'nombre': 'Juan2',
            'email': 'ana@example.com',
            'telefono': '+56 9 1234 5678',
            'asunto': 'Consulta',
            'mensaje': 'Hola',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'letras')

        with patch('core.correo.enviar_contacto', return_value=True):
            valido = self.client.post(reverse('core:contacto'), {
                'nombre': "José Pérez-O'Brien",
                'email': 'ana@example.com',
                'telefono': '+56 9 1234 5678',
                'asunto': 'Consulta técnica',
                'mensaje': 'Quiero orientación para un armado.',
            })
        self.assertRedirects(valido, reverse('core:contacto'))

    def test_registro_conserva_usuario_con_digitos_y_el_limite_de_correo(self):
        form = RegistroForm(data={
            'username': 'user123',
            'first_name': 'Ana',
            'last_name': 'Perez',
            'email': 'user123@example.com',
            'password1': 'Clave-Segura-2026',
            'password2': 'Clave-Segura-2026',
        })
        self.assertTrue(form.is_valid(), form.errors)

        largo = RegistroForm(data={
            'username': 'user123',
            'first_name': 'Ana',
            'last_name': 'Perez',
            'email': ('a' * 250) + '@example.com',
            'password1': 'Clave-Segura-2026',
            'password2': 'Clave-Segura-2026',
        })
        self.assertFalse(largo.is_valid())
        self.assertIn('email', largo.errors)

    def test_la_busqueda_larga_no_filtra_y_solo_aparece_en_inicio_y_tienda(self):
        marca = Proveedor.objects.create(nombre='Marca Busqueda')
        crear_cpu(marca, 'CPU Visible', Decimal('10000.00'), 1)
        consulta = 'CPU Visible' + ('x' * 120)
        respuesta = self.client.get(reverse('core:tienda'), {'q': consulta})
        self.assertContains(respuesta, '120 caracteres')
        self.assertContains(respuesta, 'CPU Visible')

        inicio = self.client.get(reverse('core:index'))
        self.assertContains(inicio, 'name="q"')
        self.assertContains(inicio, 'ms-auto')
        self.assertContains(self.client.get(reverse('core:tienda')), 'maxlength="120"')
        for nombre in ('contacto', 'armado', 'sobrenosotros', 'login', 'registro'):
            pagina = self.client.get(reverse(f'core:{nombre}'))
            self.assertNotContains(pagina, 'name="q"', msg_prefix=nombre)
            if nombre in ('contacto', 'armado', 'sobrenosotros'):
                self.assertContains(pagina, 'col-lg-5 d-flex justify-content-end gap-2 ps-0 ps-lg-3 ms-auto', msg_prefix=nombre)


class FiltrosYInicioTests(TestCase):
    def test_filtros_unicos_conservan_seleccion_y_las_tarjetas_apuntan_bien(self):
        marca = Proveedor.objects.create(nombre='Marca Filtro')
        crear_cpu(marca, 'CPU Filtro', Decimal('80000.00'), 3)
        respuesta = self.client.get(reverse('core:tienda'), {
            'categoria': 'CPU',
            'orden': 'precio_asc',
            'proveedor': str(marca.id),
        })
        html = respuesta.content.decode()
        self.assertEqual(html.count('id="filtros-catalogo"'), 1)
        self.assertEqual(html.count('id="filtro-categoria"'), 1)
        self.assertEqual(html.count('id="orden-catalogo"'), 1)
        self.assertContains(respuesta, 'fa-ellipsis-v')
        self.assertContains(respuesta, 'Filtros')
        self.assertContains(respuesta, 'id="abrir-filtros"')
        self.assertContains(respuesta, 'id="cerrar-filtros"')
        self.assertContains(respuesta, 'id="filtros-overlay"')
        self.assertContains(respuesta, 'value="CPU" selected')
        self.assertContains(respuesta, 'value="precio_asc" selected')
        self.assertContains(respuesta, f'value="{marca.id}" selected')
        self.assertIn('orden=precio_asc', respuesta.context['pagination_query'])
        self.assertIn('categoria=CPU', respuesta.context['pagination_query'])
        self.assertContains(respuesta, 'Aplicar')
        self.assertContains(respuesta, 'Limpiar')
        panel = html.split('id="panel-filtros"', 1)[1].split('id="filtros-overlay"', 1)[0]
        self.assertLess(panel.index('id="orden-catalogo"'), panel.index('>Aplicar<'))
        self.assertLess(panel.index('>Aplicar<'), panel.index('>Limpiar<'))

        js = Path('core/static/core/js/tienda-filtros.js').read_text(encoding='utf-8')
        self.assertNotIn('orden.form.submit()', js)
        css = Path('core/static/core/css/tienda-filtros.css').read_text(encoding='utf-8')
        self.assertIn("event.key === 'Escape'", js)
        self.assertIn('cerrarBtn.focus()', js)
        self.assertIn('max-width: 991.98px', css)
        self.assertIn('min-width: 992px', css)

        inicio = self.client.get(reverse('core:index'))
        self.assertContains(inicio, 'Novedades del catálogo')
        self.assertContains(inicio, '?novedades=1')
        self.assertContains(inicio, reverse('core:armado'))
        self.assertContains(inicio, 'Consulta técnica')
        self.assertContains(inicio, reverse('core:contacto'))
        self.assertContains(inicio, 'Conoce HardWareHouse')
        self.assertContains(inicio, reverse('core:sobrenosotros'))
        self.assertNotContains(inicio, 'Soporte técnico 24/7')
        self.assertNotContains(inicio, 'Componentes de calidad')

        for modelo, _etiqueta in CATALOGO_MODELOS:
            nombres = {campo.name for campo in modelo._meta.concrete_fields}
            self.assertTrue(
                {'creado_en', 'actualizado_en', 'en_oferta', 'precio_oferta'} <= nombres,
                modelo.__name__,
            )
        novedades = self.client.get(reverse('core:tienda'), {'novedades': '1'})
        self.assertNotContains(novedades, 'no guarda la fecha de alta')
        self.assertContains(novedades, 'más recientemente')
        self.assertContains(novedades, 'CPU Filtro')

        sobre = self.client.get(reverse('core:sobrenosotros'))
        self.assertContains(sobre, '<a href="/contacto/">Contacto</a>', html=True)
        self.assertNotContains(sobre, 'en /contacto/')
        self.assertIn('/contacto/', texto_faq('contacto'))
