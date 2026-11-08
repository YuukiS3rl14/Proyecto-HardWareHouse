from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from core.admin_dashboard import MODELOS_PRODUCTO, inicio_del_mes, inicio_ventana_ventas
from core.models import Carrito, ItemCarrito, ItemPedido, Pedido, Procesador, Proveedor, TarjetaGrafica, Ventilador


class DashboardAdminTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser('root-panel', 'root@example.com', 'clave-panel-root')
        self.cliente = User.objects.create_user('cliente-panel', 'cliente@example.com', 'clave-panel-cliente')
        self.proveedor = Proveedor.objects.create(nombre='Marca panel')
        self.inicio = inicio_del_mes()

    def staff(self, nombre, *codenames):
        usuario = User.objects.create_user(nombre, f'{nombre}@example.com', 'clave-panel-staff')
        usuario.is_staff = True
        usuario.save(update_fields=['is_staff'])
        permisos = Permission.objects.filter(content_type__app_label='core', codename__in=codenames)
        usuario.user_permissions.set(permisos)
        return usuario

    def cpu(self, nombre, stock):
        return Procesador.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal('10000.00'), stock=stock,
            socket='AM5', nucleos=6, frecuencia_base=Decimal('3.50'),
        )

    def gpu(self, nombre, stock):
        return TarjetaGrafica.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal('20000.00'), stock=stock,
            vram_gb=8, tipo_memoria='GDDR6', interfaz='PCIe 4.0',
        )

    def ventilador(self, nombre, stock):
        return Ventilador.objects.create(
            proveedor=self.proveedor, nombre=nombre, precio=Decimal('5000.00'), stock=stock,
            tamanho_mm=120, velocidad_rpm=1500,
        )

    def pedido(self, estado, total, fecha):
        return Pedido.objects.create(
            usuario=self.cliente,
            estado=estado,
            total_monto=Decimal(total),
            direccion_envio='DIRECCION-SECRETA-99',
            fecha_pedido=fecha,
        )

    def panel(self, usuario):
        self.client.force_login(usuario)
        return self.client.get(reverse('admin:index'))

    def test_los_diez_componentes_entran_en_el_conteo(self):
        nombres = {modelo._meta.model_name for modelo in MODELOS_PRODUCTO}
        self.assertEqual(len(MODELOS_PRODUCTO), 10)
        self.assertEqual(nombres, {
            'procesador', 'tarjetagrafica', 'memoriaram', 'placamadre',
            'almacenamientossd', 'almacenamientohdd', 'gabinete',
            'fuentedepoder', 'refrigeracioncooler', 'ventilador',
        })

    def test_sin_pedidos_ni_productos_muestra_cero(self):
        respuesta = self.panel(self.superuser)
        datos = respuesta.context['hw']

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(datos['ventas']['mes'], Decimal('0'))
        self.assertEqual(datos['ventas']['historico'], Decimal('0'))
        self.assertEqual(datos['pedidos']['registrados'], 0)
        self.assertEqual(datos['pedidos']['pendientes'], 0)
        self.assertEqual(datos['pedidos']['recientes'], [])
        self.assertEqual(datos['productos']['disponibles'], 0)
        self.assertEqual(datos['productos']['stock_bajo'], 0)
        self.assertEqual(datos['productos']['agotados'], 0)
        self.assertEqual(datos['productos']['alertas'], [])
        self.assertEqual(len(datos['graficos']['ventas']['puntos']), 12)
        self.assertTrue(all(punto['valor'] == 0 for punto in datos['graficos']['ventas']['puntos']))
        self.assertTrue(datos['graficos']['estados']['vacio'])
        self.assertTrue(datos['graficos']['vendidos']['vacio'])
        self.assertContains(respuesta, 'No hay pedidos registrados.')
        self.assertContains(respuesta, 'No hay productos con stock bajo ni agotados.')
        self.assertContains(respuesta, 'No hay ventas registradas.')
        self.assertContains(respuesta, 'Aún no hay ventas registradas.')
        self.assertNotContains(respuesta, 'id="hw-chart-ventas"')
        self.assertNotContains(respuesta, '/static/core/vendor/chart.umd.min.js')
        self.assertNotContains(respuesta, '/static/core/js/admin-charts.js')
        self.assertNotContains(respuesta, 'cdn.jsdelivr.net')
        self.assertNotContains(respuesta, 'cdnjs.cloudflare.com')
        self.assertContains(respuesta, '$0')
        self.assertContains(respuesta, 'Catálogo y componentes')
        self.assertContains(respuesta, 'Inventario')
        self.assertContains(respuesta, 'Pedidos y ventas')
        self.assertContains(respuesta, 'Clientes y actividad')
        self.assertContains(respuesta, 'Configuración')
        self.assertContains(respuesta, 'Buscar pedidos')
        self.assertContains(respuesta, 'Buscar usuarios')
        self.assertEqual(respuesta.content.decode().count('class="hw-access"'), 4)
        self.assertContains(respuesta, 'class="hw-access" href="%s"' % reverse('admin:core_pedido_changelist'))
        self.assertContains(respuesta, 'class="hw-access" href="%s"' % (reverse('admin:index') + '#hw-alertas'))
        self.assertContains(respuesta, 'class="hw-access" href="%s"' % reverse('admin:core_procesador_changelist'))
        self.assertContains(respuesta, 'class="hw-access" href="%s"' % reverse('admin:auth_user_changelist'))
        listado = self.client.get(reverse('admin:core_procesador_changelist'))
        self.assertNotContains(listado, 'chart.umd.min.js')

    def test_ventas_pedidos_y_stock_usan_datos_reales(self):
        self.pedido('PAGADO', '10000.00', self.inicio - timedelta(seconds=1))
        self.pedido('PAGADO', '20000.00', self.inicio)
        self.pedido('ENVIADO', '3000.00', self.inicio + timedelta(hours=1))
        self.pedido('ENTREGADO', '4000.00', self.inicio + timedelta(hours=2))
        self.pedido('CANCELADO', '70000.00', self.inicio + timedelta(hours=3))
        pendiente = self.pedido('PENDIENTE', '50000.00', self.inicio + timedelta(hours=4))
        cpu_baja = self.cpu('CPU-BAJA', 3)
        self.cpu('CPU-AGOTADA', 0)
        self.cpu('CPU-HOLGADA', 10)
        self.gpu('GPU-LIMITE', 5)
        self.gpu('GPU-HOLGADA', 6)
        self.ventilador('FAN-BAJA', 1)
        carrito = Carrito.objects.create(usuario=self.cliente)
        ItemCarrito.objects.create(
            carrito=carrito, procesador=cpu_baja, cantidad=1, precio_unitario=Decimal('999999.00'),
        )

        respuesta = self.panel(self.superuser)
        datos = respuesta.context['hw']

        self.assertEqual(datos['ventas']['mes'], Decimal('27000.00'))
        self.assertEqual(datos['ventas']['historico'], Decimal('37000.00'))
        self.assertFalse(datos['graficos']['ventas']['vacio'])
        self.assertContains(respuesta, 'id="hw-chart-ventas"')
        self.assertContains(respuesta, '/static/core/vendor/chart.umd.min.js')
        self.assertNotContains(respuesta, 'Aún no hay ventas registradas.')
        self.assertEqual(datos['graficos']['ventas']['puntos'][-1]['valor'], 27000)
        self.assertEqual(datos['graficos']['ventas']['puntos'][-2]['valor'], 10000)
        self.assertEqual(datos['pedidos']['registrados'], 6)
        self.assertEqual(datos['pedidos']['pendientes'], 1)
        self.assertEqual(datos['pedidos']['recientes'][0].pk, pendiente.pk)
        self.assertEqual(datos['productos']['disponibles'], 5)
        self.assertEqual(datos['productos']['stock_bajo'], 3)
        self.assertEqual(datos['productos']['agotados'], 1)
        self.assertEqual(
            [alerta['nombre'] for alerta in datos['productos']['alertas']],
            ['CPU-AGOTADA', 'FAN-BAJA', 'CPU-BAJA', 'GPU-LIMITE'],
        )
        self.assertEqual(datos['productos']['alertas'][0]['estado'], 'Agotado')
        self.assertEqual(datos['productos']['alertas'][2]['estado'], 'Stock bajo')
        self.assertEqual(datos['productos']['alertas'][2]['tipo'], 'CPU')
        self.assertEqual(datos['productos']['alertas'][2]['stock'], 3)
        self.assertEqual(
            datos['productos']['alertas'][2]['url'],
            reverse('admin:core_procesador_change', args=[cpu_baja.pk]),
        )
        self.assertContains(respuesta, reverse('admin:core_pedido_change', args=[pendiente.pk]))
        self.assertContains(respuesta, 'Pendiente de Pago')
        self.assertNotContains(respuesta, 'DIRECCION-SECRETA-99')
        self.assertNotContains(respuesta, '999999')
        self.assertNotContains(respuesta, '999.999')
        self.assertEqual(self.client.get(datos['productos']['alertas'][2]['url']).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:core_pedido_change', args=[pendiente.pk])).status_code, 200)

    def test_un_staff_de_pedidos_no_ve_productos(self):
        self.pedido('PAGADO', '180000.00', self.inicio)
        self.gpu('GPU-OCULTA-77', 2)
        usuario = self.staff('solo-pedidos', 'view_pedido')
        self.client.force_login(usuario)

        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.client.get(reverse('admin:index'))
        sql = ' '.join(consulta['sql'] for consulta in consultas.captured_queries)
        datos = respuesta.context['hw']

        self.assertTrue(datos['ventas']['permitido'])
        self.assertEqual(datos['ventas']['mes'], Decimal('180000.00'))
        self.assertFalse(datos['productos']['permitido'])
        self.assertNotIn('disponibles', datos['productos'])
        self.assertNotIn('core_tarjetagrafica', sql)
        self.assertNotContains(respuesta, 'GPU-OCULTA-77')
        self.assertNotContains(respuesta, reverse('admin:core_tarjetagrafica_changelist'))
        self.assertIsNone(datos['graficos']['vendidos'])
        self.assertNotContains(respuesta, 'hw-grafico-vendidos')
        self.assertContains(respuesta, 'No tienes permiso para ver los productos.')
        self.assertContains(respuesta, reverse('admin:core_pedido_changelist'))
        self.assertContains(respuesta, 'Pedidos y ventas')
        self.assertNotContains(respuesta, 'Catálogo y componentes')
        self.assertNotContains(respuesta, reverse('admin:auth_user_changelist'))
        self.assertEqual(respuesta.content.decode().count('class="hw-access"'), 1)
        self.assertContains(respuesta, 'class="hw-access" href="%s"' % reverse('admin:core_pedido_changelist'))
        self.assertNotContains(respuesta, '#hw-alertas')

    def test_un_staff_de_un_componente_no_ve_pedidos_ni_otros_productos(self):
        self.pedido('PAGADO', '180000.00', self.inicio)
        self.cpu('CPU-VISIBLE', 4)
        self.gpu('GPU-OCULTA-77', 2)
        usuario = self.staff('solo-cpu', 'view_procesador')
        self.client.force_login(usuario)

        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.client.get(reverse('admin:index'))
        sql = ' '.join(consulta['sql'] for consulta in consultas.captured_queries)
        datos = respuesta.context['hw']

        self.assertFalse(datos['ventas']['permitido'])
        self.assertFalse(datos['pedidos']['permitido'])
        self.assertNotIn('mes', datos['ventas'])
        self.assertEqual(datos['productos']['disponibles'], 1)
        self.assertEqual(datos['productos']['stock_bajo'], 1)
        self.assertEqual(datos['productos']['agotados'], 0)
        self.assertEqual([alerta['nombre'] for alerta in datos['productos']['alertas']], ['CPU-VISIBLE'])
        self.assertNotIn('core_pedido', sql)
        self.assertNotIn('core_tarjetagrafica', sql)
        self.assertIn('core_procesador', sql)
        self.assertNotContains(respuesta, 'GPU-OCULTA-77')
        self.assertNotContains(respuesta, '180000')
        self.assertNotContains(respuesta, '180.000')
        self.assertNotContains(respuesta, reverse('admin:core_tarjetagrafica_changelist'))
        self.assertIsNone(datos['graficos']['ventas'])
        self.assertIsNone(datos['graficos']['estados'])
        self.assertIsNone(datos['graficos']['vendidos'])
        self.assertNotContains(respuesta, 'hw-grafico-ventas')
        self.assertNotContains(respuesta, 'chart.umd.min.js')
        self.assertContains(respuesta, 'CPU-VISIBLE')
        self.assertContains(respuesta, 'No tienes permiso para ver los pedidos.')
        self.assertContains(respuesta, 'Catálogo y componentes')
        self.assertContains(respuesta, 'Inventario')
        self.assertContains(respuesta, 'Procesadores (CPU)')
        self.assertNotContains(respuesta, 'Pedidos y ventas')
        self.assertNotContains(respuesta, 'Aún no hay ventas registradas.')
        self.assertNotContains(respuesta, reverse('admin:core_pedido_changelist'))
        self.assertNotContains(respuesta, reverse('admin:auth_user_changelist'))
        self.assertEqual(respuesta.content.decode().count('class="hw-access"'), 2)
        self.assertContains(respuesta, 'class="hw-access" href="%s"' % reverse('admin:core_procesador_changelist'))
        self.assertContains(respuesta, 'class="hw-access" href="%s"' % (reverse('admin:index') + '#hw-alertas'))
        self.assertEqual(self.client.get(reverse('admin:core_tarjetagrafica_changelist')).status_code, 403)

    def test_accesos_principales_usa_el_primer_catalogo_autorizado(self):
        from core.templatetags.admin_menu import accesos_principales

        menu = [{'models': [{
            'model_str': 'core.tarjetagrafica',
            'url': '/admin/core/tarjetagrafica/',
            'name': 'GPU',
        }]}]
        accesos = accesos_principales(menu)
        self.assertEqual(
            [(acceso['nombre'], acceso['url']) for acceso in accesos],
            [
                ('Inventario', reverse('admin:index') + '#hw-alertas'),
                ('Productos', '/admin/core/tarjetagrafica/'),
            ],
        )
        self.assertEqual(accesos_principales([]), [])

    def test_sin_permiso_de_staff_no_entra_al_panel(self):
        self.pedido('PAGADO', '180000.00', self.inicio)
        self.client.force_login(self.cliente)
        respuesta = self.client.get(reverse('admin:index'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/admin/login/', respuesta.url)
        self.assertNotContains(respuesta, '180000', status_code=302)

    def linea(self, pedido, producto, cantidad, modelo):
        return ItemPedido.objects.create(
            pedido=pedido,
            producto_nombre=producto.nombre,
            producto_tipo=producto.categoria,
            precio_unitario=producto.precio,
            cantidad=cantidad,
            producto_modelo=modelo,
            producto_pk=producto.pk,
        )

    def test_ventas_mensuales_dejan_en_cero_los_meses_vacios(self):
        inicio = inicio_ventana_ventas()
        self.pedido('PAGADO', '111.00', inicio - timedelta(seconds=1))
        self.pedido('PAGADO', '222.00', inicio)
        self.pedido('ENVIADO', '300.00', self.inicio)
        self.pedido('ENTREGADO', '33.40', self.inicio + timedelta(minutes=5))
        self.pedido('PENDIENTE', '444.00', self.inicio + timedelta(hours=1))
        self.pedido('CANCELADO', '555.00', self.inicio + timedelta(hours=2))

        respuesta = self.panel(self.superuser)
        puntos = respuesta.context['hw']['graficos']['ventas']['puntos']
        estados = {
            punto['clave']: punto['valor']
            for punto in respuesta.context['hw']['graficos']['estados']['puntos']
        }

        self.assertEqual(len(puntos), 12)
        self.assertEqual(puntos[0]['valor'], 222)
        self.assertEqual(puntos[-1]['valor'], 333)
        self.assertTrue(all(punto['valor'] == 0 for punto in puntos[1:-1]))
        self.assertIn(str(inicio.year), puntos[0]['etiqueta'])
        self.assertIn(str(self.inicio.year), puntos[-1]['etiqueta'])
        self.assertEqual(estados, {
            'PENDIENTE': 1,
            'PAGADO': 2,
            'ENVIADO': 1,
            'ENTREGADO': 1,
            'CANCELADO': 1,
        })
        self.assertContains(respuesta, 'id="hw-chart-ventas"')
        self.assertContains(respuesta, '"valor": 0')
        self.assertNotContains(respuesta, 'Aún no hay ventas registradas.')

    def test_mas_vendidos_separa_el_mismo_nombre_en_modelos_distintos(self):
        cpu_a = self.cpu('Repetido', 8)
        cpu_b = self.cpu('Repetido', 8)
        gpu = self.gpu('Repetido', 8)
        pagado = self.pedido('PAGADO', '1000.00', self.inicio)
        cancelado = self.pedido('CANCELADO', '1000.00', self.inicio)
        self.linea(pagado, cpu_a, 2, 'procesador')
        self.linea(pagado, cpu_b, 7, 'procesador')
        self.linea(pagado, gpu, 4, 'tarjeta_grafica')
        self.linea(cancelado, cpu_a, 9, 'procesador')
        carrito = Carrito.objects.create(usuario=self.cliente)
        ItemCarrito.objects.create(
            carrito=carrito, procesador=cpu_a, cantidad=8, precio_unitario=Decimal('1000.00'),
        )

        respuesta = self.panel(self.superuser)
        puntos = respuesta.context['hw']['graficos']['vendidos']['puntos']

        self.assertEqual(
            [(punto['etiqueta'], punto['valor']) for punto in puntos],
            [
                (f'Repetido · CPU · #{cpu_b.pk}', 7),
                ('Repetido · Tarjeta Gráfica', 4),
                (f'Repetido · CPU · #{cpu_a.pk}', 2),
            ],
        )

        limitado = self.staff('cpu-y-pedidos', 'view_pedido', 'view_procesador')
        visible = self.panel(limitado)
        self.assertEqual(
            [(punto['etiqueta'], punto['valor']) for punto in visible.context['hw']['graficos']['vendidos']['puntos']],
            [
                (f'Repetido · CPU · #{cpu_b.pk}', 7),
                (f'Repetido · CPU · #{cpu_a.pk}', 2),
            ],
        )
        self.assertNotContains(visible, 'Tarjeta Gráfica')
        self.assertNotContains(visible, reverse('admin:core_tarjetagrafica_change', args=[gpu.pk]))
        html = visible.content.decode()
        self.assertNotIn('"valor": 4', html)
        self.assertNotIn('"valor":4', html)
