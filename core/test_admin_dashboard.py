from datetime import timedelta
from calendar import monthrange
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
        self.assertEqual(datos['periodo']['aplicado'], 'anio')
        self.assertEqual(datos['periodo']['etiqueta'], str(self.inicio.year))
        self.assertEqual(datos['graficos']['ventas']['titulo'], 'Ventas por mes')
        self.assertEqual(len(datos['graficos']['ventas']['puntos']), 12)
        self.assertTrue(all(punto['valor'] == 0 for punto in datos['graficos']['ventas']['puntos']))
        self.assertTrue(datos['graficos']['estados']['vacio'])
        self.assertTrue(datos['graficos']['vendidos']['vacio'])
        self.assertContains(respuesta, 'No hay pedidos registrados.')
        self.assertContains(respuesta, 'No hay productos con stock bajo ni agotados.')
        self.assertContains(respuesta, 'No hay ventas registradas.')
        self.assertContains(respuesta, 'Aún no hay ventas registradas.')
        self.assertContains(respuesta, 'Sin comparación disponible')
        self.assertNotContains(respuesta, 'id="hw-chart-ventas"')
        self.assertContains(respuesta, '/static/core/vendor/chart.umd.min.js')
        self.assertContains(respuesta, '/static/core/js/admin-charts.js')
        self.assertNotContains(respuesta, 'cdn.jsdelivr.net')
        self.assertNotContains(respuesta, 'cdnjs.cloudflare.com')
        self.assertContains(respuesta, '$0')
        self.assertContains(respuesta, 'Dashboard')
        self.assertNotContains(respuesta, '>Panel<')
        self.assertContains(respuesta, 'Catálogo y componentes')
        self.assertContains(respuesta, 'Inventario')
        self.assertContains(respuesta, 'Pedidos y ventas')
        self.assertContains(respuesta, 'Usuarios y permisos')
        self.assertContains(respuesta, 'Otros')
        self.assertContains(respuesta, 'Movimientos de stock')
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

        self.client.force_login(self.superuser)
        respuesta = self.client.get(reverse('admin:index'), {'hw_periodo': 'mes'})
        datos = respuesta.context['hw']

        self.assertEqual(datos['ventas']['mes'], Decimal('27000.00'))
        self.assertEqual(datos['ventas']['historico'], Decimal('37000.00'))
        self.assertEqual(datos['ventas']['confirmados'], 3)
        self.assertEqual(datos['ventas']['ticket'], Decimal('9000'))
        self.assertEqual(datos['ventas']['unidades'], 0)
        self.assertEqual(datos['ventas']['variacion_monto']['texto'], '+170%')
        self.assertFalse(datos['graficos']['ventas']['vacio'])
        self.assertContains(respuesta, 'id="hw-chart-ventas"')
        self.assertContains(respuesta, '/static/core/vendor/chart.umd.min.js')
        self.assertNotContains(respuesta, 'Aún no hay ventas registradas.')
        self.assertEqual(datos['graficos']['ventas']['puntos'][0]['valor'], 27000)
        self.assertTrue(all(punto['valor'] == 0 for punto in datos['graficos']['ventas']['puntos'][1:]))
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

    def test_los_pedidos_se_paginan_de_a_ocho_y_conservan_el_mas_antiguo(self):
        creados = [
            self.pedido('PAGADO', '1000.00', self.inicio + timedelta(minutes=indice))
            for indice in range(9)
        ]
        with CaptureQueriesContext(connection) as consultas:
            primera = self.panel(self.superuser)
        sql = ' '.join(consulta['sql'] for consulta in consultas.captured_queries)
        recientes = primera.context['hw']['pedidos']['recientes']
        self.assertEqual(len(recientes), 8)
        self.assertEqual(recientes[0].pk, creados[-1].pk)
        self.assertNotIn(creados[0].pk, [pedido.pk for pedido in recientes])
        self.assertTrue(any(
            'LIMIT 8' in consulta['sql'] and 'core_pedido' in consulta['sql']
            for consulta in consultas.captured_queries
        ))
        self.assertNotIn('OFFSET 8', sql)
        self.assertContains(primera, 'Página 1 de 2')
        self.assertContains(primera, 'hw-pager-link is-disabled')
        self.assertContains(primera, 'aria-disabled="true"')
        self.assertContains(primera, 'pedidos_pagina=2#hw-ultimos-pedidos')
        self.assertContains(primera, reverse('admin:core_pedido_change', args=[creados[-1].pk]))

        segunda = self.client.get(reverse('admin:index'), {'pedidos_pagina': 2, 'alertas_pagina': 3})
        self.assertEqual(
            [pedido.pk for pedido in segunda.context['hw']['pedidos']['recientes']],
            [creados[0].pk],
        )
        self.assertContains(segunda, reverse('admin:core_pedido_change', args=[creados[0].pk]))
        self.assertContains(segunda, 'alertas_pagina=3#hw-ultimos-pedidos')
        invalida = self.client.get(reverse('admin:index'), {'pedidos_pagina': 'no'})
        self.assertEqual(invalida.context['hw']['pedidos']['paginacion']['numero'], 1)

    def test_las_alertas_se_paginan_priorizando_agotados(self):
        productos = [self.cpu(f'CPU-{indice:02d}', 0 if indice < 10 else 1) for indice in range(21)]
        primera = self.panel(self.superuser)
        alertas = primera.context['hw']['productos']['alertas']
        self.assertEqual(len(alertas), 8)
        self.assertEqual([alerta['estado'] for alerta in alertas], ['Agotado'] * 8)
        self.assertEqual(alertas[0]['nombre'], 'CPU-00')
        self.assertContains(primera, 'Página 1 de 3')
        self.assertContains(primera, reverse('admin:core_procesador_change', args=[productos[0].pk]))

        tercera = self.client.get(reverse('admin:index'), {'alertas_pagina': 3, 'pedidos_pagina': 4})
        self.assertEqual(
            [alerta['nombre'] for alerta in tercera.context['hw']['productos']['alertas']],
            ['CPU-16', 'CPU-17', 'CPU-18', 'CPU-19', 'CPU-20'],
        )
        self.assertEqual(tercera.context['hw']['pedidos']['paginacion']['numero'], 1)
        self.assertContains(tercera, 'pedidos_pagina=4#hw-alertas')
        self.assertContains(tercera, reverse('admin:core_procesador_change', args=[productos[20].pk]))

    def test_cada_paginacion_respeta_el_permiso_y_no_consulta_lo_ajeno(self):
        for indice in range(9):
            self.pedido('PAGADO', '1000.00', self.inicio + timedelta(minutes=indice))
            self.cpu(f'CPU-PAG-{indice}', 0)
            self.gpu(f'GPU-OCULTA-{indice}', 0)
        pedidos = self.staff('pagina-pedidos', 'view_pedido')
        self.client.force_login(pedidos)
        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.client.get(reverse('admin:index'), {'pedidos_pagina': 2, 'alertas_pagina': 2})
        sql = ' '.join(consulta['sql'] for consulta in consultas.captured_queries)
        self.assertEqual(len(respuesta.context['hw']['pedidos']['recientes']), 1)
        self.assertNotIn('core_procesador', sql)
        self.assertNotIn('core_tarjetagrafica', sql)
        self.assertNotContains(respuesta, 'CPU-PAG-0')
        self.assertNotContains(respuesta, 'GPU-OCULTA-0')

        cpu = self.staff('pagina-cpu', 'view_procesador')
        self.client.force_login(cpu)
        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.client.get(reverse('admin:index'), {'pedidos_pagina': 2, 'alertas_pagina': 2})
        sql = ' '.join(consulta['sql'] for consulta in consultas.captured_queries)
        self.assertEqual(len(respuesta.context['hw']['productos']['alertas']), 1)
        self.assertEqual(respuesta.context['hw']['productos']['alertas'][0]['nombre'], 'CPU-PAG-8')
        self.assertNotIn('core_pedido', sql)
        self.assertNotIn('core_tarjetagrafica', sql)
        self.assertNotContains(respuesta, 'GPU-OCULTA-0')
        self.assertContains(respuesta, 'No tienes permiso para ver los pedidos.')

    def test_la_tarjeta_parcial_no_trae_el_resto_del_dashboard(self):
        creados = [
            self.pedido('PAGADO', '1000.00', self.inicio + timedelta(minutes=indice))
            for indice in range(9)
        ]
        for indice in range(9):
            self.cpu(f'CPU-A-{indice:02d}', 0)
        self.client.force_login(self.superuser)
        with CaptureQueriesContext(connection) as consultas:
            pedidos = self.client.get(reverse('admin:index'), {
                'hw_tarjeta': 'pedidos',
                'pedidos_pagina': 2,
                'alertas_pagina': 3,
            })
        sql = ' '.join(consulta['sql'] for consulta in consultas.captured_queries)
        self.assertEqual(pedidos.status_code, 200)
        self.assertContains(pedidos, '<!-- hw-tarjeta:pedidos -->')
        self.assertContains(pedidos, 'Página 2 de 2')
        self.assertContains(pedidos, reverse('admin:core_pedido_change', args=[creados[0].pk]))
        self.assertContains(pedidos, 'alertas_pagina=3#hw-ultimos-pedidos')
        self.assertNotContains(pedidos, 'hw_tarjeta')
        self.assertNotContains(pedidos, 'Ventas confirmadas')
        self.assertNotContains(pedidos, 'hw-chart-ventas')
        self.assertNotContains(pedidos, '<!-- hw-tarjeta:alertas -->')
        self.assertNotContains(pedidos, 'CPU-A-00')
        self.assertNotIn('core_procesador', sql)

        self.client.force_login(self.superuser)
        alertas = self.client.get(reverse('admin:index'), {
            'hw_tarjeta': 'alertas',
            'pedidos_pagina': 4,
        })
        self.assertContains(alertas, '<!-- hw-tarjeta:alertas -->')
        self.assertContains(alertas, 'CPU-A-00')
        self.assertContains(alertas, 'pedidos_pagina=4')
        self.assertContains(alertas, 'alertas_pagina=2#hw-alertas')
        self.assertNotContains(alertas, 'Ventas confirmadas')
        self.assertNotContains(alertas, 'hw_tarjeta')

        completo = self.client.get(reverse('admin:index'), {'hw_tarjeta': 'otra'})
        self.assertContains(completo, 'Ventas confirmadas')
        self.assertContains(completo, 'id="hw-chart-ventas"')

    def test_la_tarjeta_parcial_respeta_permisos_y_el_enlace_html(self):
        for indice in range(9):
            self.pedido('PAGADO', '1000.00', self.inicio + timedelta(minutes=indice))
            self.cpu(f'CPU-PAR-{indice}', 0)
        pedidos = self.staff('parcial-pedidos', 'view_pedido')
        self.client.force_login(pedidos)
        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.client.get(reverse('admin:index'), {'hw_tarjeta': 'alertas', 'alertas_pagina': 2})
        sql = ' '.join(consulta['sql'] for consulta in consultas.captured_queries)
        self.assertContains(respuesta, 'No tienes permiso para ver el inventario.')
        self.assertNotContains(respuesta, 'CPU-PAR-0')
        self.assertNotIn('core_procesador', sql)
        self.assertContains(
            self.client.get(reverse('admin:index'), {'hw_tarjeta': 'pedidos'}),
            'href="/admin/?pedidos_pagina=2#hw-ultimos-pedidos"',
        )

        cpu = self.staff('parcial-cpu', 'view_procesador')
        self.client.force_login(cpu)
        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.client.get(reverse('admin:index'), {'hw_tarjeta': 'pedidos', 'pedidos_pagina': 2})
        sql = ' '.join(consulta['sql'] for consulta in consultas.captured_queries)
        self.assertContains(respuesta, 'No tienes permiso para ver los pedidos.')
        self.assertNotIn('core_pedido', sql)
        self.assertNotContains(respuesta, '1000')

        self.client.force_login(self.cliente)
        anonima = self.client.get(reverse('admin:index'), {'hw_tarjeta': 'pedidos'})
        self.assertEqual(anonima.status_code, 302)
        self.assertIn('/admin/login/', anonima.url)

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

        self.client.force_login(self.superuser)
        respuesta = self.client.get(reverse('admin:index'), {'hw_periodo': 'mes'})
        puntos = respuesta.context['hw']['graficos']['ventas']['puntos']
        estados = {
            punto['clave']: punto['valor']
            for punto in respuesta.context['hw']['graficos']['estados']['puntos']
        }

        self.assertEqual(len(puntos), monthrange(self.inicio.year, self.inicio.month)[1])
        self.assertEqual(puntos[0]['valor'], 333)
        self.assertTrue(all(punto['valor'] == 0 for punto in puntos[1:]))
        self.assertEqual(estados, {
            'PENDIENTE': 1,
            'PAGADO': 0,
            'ENVIADO': 1,
            'ENTREGADO': 1,
            'CANCELADO': 1,
        })
        self.assertContains(respuesta, 'id="hw-chart-ventas"')
        self.assertContains(respuesta, '"valor": 0')
        self.assertNotContains(respuesta, 'Aún no hay ventas registradas.')

        anual = self.client.get(reverse('admin:index'), {'hw_periodo': 'anio'})
        anuales = anual.context['hw']['graficos']['ventas']['puntos']
        self.assertEqual(len(anuales), 12)
        self.assertEqual(anuales[self.inicio.month - 1]['valor'], 333)
        self.assertTrue(all(
            punto['valor'] == 0
            for indice, punto in enumerate(anuales)
            if indice != self.inicio.month - 1
        ))
        self.assertIn(str(self.inicio.year), anuales[self.inicio.month - 1]['etiqueta'])

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
        self.assertContains(visible, '7 unidades')
        self.assertContains(visible, '$70.000')
        self.assertNotContains(visible, 'hw-chart-vendidos')

    def test_mas_vendidos_ordena_por_unidades_y_omite_pendientes(self):
        productos = [self.cpu(f'RANK-{indice}', 8) for indice in range(6)]
        pagado = self.pedido('PAGADO', '1000.00', self.inicio)
        pendiente = self.pedido('PENDIENTE', '1000.00', self.inicio)
        cancelado = self.pedido('CANCELADO', '1000.00', self.inicio)
        for indice, producto in enumerate(productos):
            self.linea(pagado, producto, indice + 1, 'procesador')
        self.linea(pendiente, productos[0], 50, 'procesador')
        self.linea(cancelado, productos[1], 40, 'procesador')

        puntos = self.panel(self.superuser).context['hw']['graficos']['vendidos']['puntos']
        self.assertEqual(
            [(punto['etiqueta'], punto['valor'], punto['ingresos']) for punto in puntos],
            [
                ('RANK-5 · CPU', 6, 60000),
                ('RANK-4 · CPU', 5, 50000),
                ('RANK-3 · CPU', 4, 40000),
                ('RANK-2 · CPU', 3, 30000),
                ('RANK-1 · CPU', 2, 20000),
            ],
        )
        self.assertEqual(puntos[0]['ancho'], 100)
        self.assertNotIn('RANK-0', [punto['etiqueta'] for punto in puntos])

    def test_el_script_intercepta_el_clic_aunque_falle_el_menu(self):
        from pathlib import Path

        from django.conf import settings

        texto = (Path(settings.BASE_DIR) / 'core' / 'static' / 'core' / 'js' / 'admin.js').read_text(encoding='utf-8')
        inicio_menu = texto.index('var menu = document.querySelector')
        inicio_paginacion = texto.index('document.addEventListener("click"')
        self.assertLess(inicio_menu, texto.index('} catch (error) {'))
        self.assertLess(texto.index('} catch (error) {'), inicio_paginacion)
        self.assertIn('parentNode', texto)
        self.assertIn('evento.button > 0', texto)
        self.assertLess(inicio_paginacion, texto.index('evento.preventDefault()'))
        self.assertIn('}, true);', texto[inicio_paginacion:])
        respuesta = self.panel(self.superuser)
        self.assertContains(respuesta, 'core/js/admin.js?v=20261108n')
        self.assertContains(respuesta, 'core/css/admin.css?v=20261108n')
        self.assertIn('data-modo', texto)
        self.assertIn('hw_periodo', texto)
        self.assertIn('firmaFiltro', texto)
        self.assertIn('popstate', texto)
        self.assertIn('hw-filtros', texto)

    def test_filtros_de_periodo_validan_fechas_y_no_mezclan_paginacion(self):
        for indice in range(9):
            self.pedido('PAGADO', '1000.00', self.inicio + timedelta(minutes=indice))
        self.client.force_login(self.superuser)
        dia = self.inicio.date().isoformat()
        rango = self.client.get(reverse('admin:index'), {
            'hw_periodo': 'rango',
            'hw_desde': dia,
            'hw_hasta': dia,
            'pedidos_pagina': 2,
        })
        datos = rango.context['hw']
        self.assertEqual(datos['periodo']['aplicado'], 'rango')
        self.assertEqual(datos['periodo']['agrupacion'], 'dia')
        self.assertEqual(datos['ventas']['mes'], Decimal('9000.00'))
        self.assertEqual(datos['ventas']['confirmados'], 9)
        self.assertEqual(datos['ventas']['ticket'], Decimal('1000'))
        self.assertEqual(len(datos['graficos']['ventas']['puntos']), 1)
        self.assertEqual(datos['graficos']['ventas']['puntos'][0]['valor'], 9000)
        self.assertContains(rango, 'Página 2 de 2')
        self.assertContains(rango, 'hw_periodo=rango')
        self.assertContains(rango, 'Período activo:')

        invertido = self.client.get(reverse('admin:index'), {
            'hw_periodo': 'rango',
            'hw_desde': '2026-11-08',
            'hw_hasta': '2026-11-01',
        })
        self.assertContains(invertido, 'El rango está invertido.')
        self.assertContains(invertido, 'Se muestra este año.')
        self.assertEqual(invertido.context['hw']['periodo']['aplicado'], 'anio')
        self.assertEqual(invertido.context['hw']['periodo']['etiqueta'], str(self.inicio.year))

        invalido = self.client.get(reverse('admin:index'), {
            'hw_periodo': 'elegir',
            'hw_mes': '13',
            'hw_anio': '1999',
        })
        self.assertContains(invalido, 'La fecha no es válida.')
        self.assertEqual(invalido.context['hw']['periodo']['aplicado'], 'anio')
        self.assertEqual(invalido.context['hw']['periodo']['modo'], 'elegir')

        manipulado = self.client.get(reverse('admin:index'), {'hw_periodo': 'todo'})
        self.assertContains(manipulado, 'El período no es válido.')
        self.assertEqual(manipulado.context['hw']['periodo']['aplicado'], 'anio')
        self.assertEqual(manipulado.context['hw']['ventas']['mes'], Decimal('9000.00'))

        explicito = self.client.get(reverse('admin:index'), {'hw_periodo': 'mes', 'pedidos_pagina': 2})
        self.assertEqual(explicito.context['hw']['periodo']['aplicado'], 'mes')
        self.assertNotIn('hw_periodo', explicito.context['hw']['periodo']['restablecer'])
        self.assertIn('pedidos_pagina=2', explicito.context['hw']['periodo']['restablecer'])
        restablecido = self.client.get(explicito.context['hw']['periodo']['restablecer'])
        self.assertEqual(restablecido.context['hw']['periodo']['aplicado'], 'anio')
        self.assertEqual(restablecido.context['hw']['periodo']['etiqueta'], str(self.inicio.year))
        self.assertContains(restablecido, 'data-modo="anio"')
        self.assertContains(restablecido, 'Página 2 de 2')

    def test_periodo_sin_ventas_comparacion_categoria_y_ranking(self):
        anterior = self.pedido('PAGADO', '4000.00', self.inicio - timedelta(days=1))
        actual = self.pedido('PAGADO', '9000.00', self.inicio)
        self.pedido('PENDIENTE', '8000.00', self.inicio)
        self.pedido('CANCELADO', '7000.00', self.inicio)
        cpu = self.cpu('CPU-FILTRO', 6)
        gpu = self.gpu('GPU-FILTRO', 6)
        self.linea(anterior, cpu, 5, 'procesador')
        self.linea(actual, cpu, 2, 'procesador')
        linea_gpu = self.linea(actual, gpu, 1, 'tarjeta_grafica')
        linea_gpu.precio_unitario = Decimal('1500.00')
        linea_gpu.save(update_fields=['precio_unitario'])
        gpu.precio = Decimal('99999.00')
        gpu.save(update_fields=['precio'])
        gpu.delete()

        self.client.force_login(self.superuser)
        vacio = self.client.get(reverse('admin:index'), {
            'hw_periodo': 'elegir',
            'hw_mes': 3,
            'hw_anio': 2001,
        })
        datos_vacios = vacio.context['hw']
        self.assertEqual(datos_vacios['ventas']['mes'], Decimal('0'))
        self.assertEqual(datos_vacios['ventas']['confirmados'], 0)
        self.assertEqual(datos_vacios['ventas']['ticket'], Decimal('0'))
        self.assertEqual(datos_vacios['ventas']['unidades'], 0)
        self.assertFalse(datos_vacios['ventas']['variacion_monto']['disponible'])
        self.assertContains(vacio, 'Sin comparación disponible')
        self.assertTrue(datos_vacios['graficos']['ventas']['vacio'])
        self.assertEqual(len(datos_vacios['graficos']['ventas']['puntos']), 31)
        self.assertTrue(all(punto['valor'] == 0 for punto in datos_vacios['graficos']['ventas']['puntos']))
        self.assertTrue(datos_vacios['graficos']['vendidos']['vacio'])
        self.assertNotContains(vacio, 'CPU-FILTRO')

        mes = self.client.get(reverse('admin:index'), {'hw_periodo': 'mes'})
        datos = mes.context['hw']
        self.assertEqual(datos['ventas']['unidades'], 3)
        self.assertEqual(datos['ventas']['variacion_unidades']['texto'], '-40%')
        self.assertEqual(
            [(punto['etiqueta'], punto['valor'], punto['ingresos']) for punto in datos['graficos']['vendidos']['puntos']],
            [('CPU-FILTRO · CPU', 2, 20000), ('GPU-FILTRO · Tarjeta Gráfica', 1, 1500)],
        )
        self.assertEqual(
            [(punto['etiqueta'], punto['valor']) for punto in datos['graficos']['categorias']['puntos']],
            [('CPU', 20000), ('Tarjeta Gráfica', 1500)],
        )
        self.assertEqual(datos['graficos']['unidades']['puntos'][0]['valor'], 3)
        self.assertContains(mes, 'Unidades vendidas por día')
        self.assertNotContains(mes, 'RANK-AUSENTE')

        amplio = self.client.get(reverse('admin:index'), {
            'hw_periodo': 'rango',
            'hw_desde': '2026-01-01',
            'hw_hasta': '2026-06-01',
        })
        self.assertEqual(amplio.context['hw']['periodo']['agrupacion'], 'mes')
        semana = self.client.get(reverse('admin:index'), {
            'hw_periodo': 'rango',
            'hw_desde': '2026-08-01',
            'hw_hasta': '2026-10-01',
        })
        self.assertEqual(semana.context['hw']['periodo']['agrupacion'], 'semana')

    def test_la_tarjeta_comercial_es_parcial_y_respeta_permisos(self):
        self.pedido('PAGADO', '180000.00', self.inicio)
        self.cpu('CPU-VISIBLE', 4)
        self.client.force_login(self.superuser)
        parcial = self.client.get(reverse('admin:index'), {
            'hw_tarjeta': 'comercial',
            'hw_periodo': 'mes',
            'pedidos_pagina': 2,
            'alertas_pagina': 3,
        })
        self.assertContains(parcial, '<!-- hw-tarjeta:comercial -->')
        self.assertContains(parcial, 'Ventas confirmadas')
        self.assertContains(parcial, 'Aplicar filtros')
        self.assertContains(parcial, 'Restablecer')
        self.assertNotContains(parcial, 'Últimos pedidos')
        self.assertNotContains(parcial, 'hw_tarjeta')
        self.assertContains(parcial, 'pedidos_pagina=2')
        self.assertContains(parcial, 'alertas_pagina=3')
        self.assertEqual(parcial.context['hw']['productos']['disponibles'], 1)
        self.assertNotIn('alertas', parcial.context['hw']['productos'])

        cpu = self.staff('comercial-cpu', 'view_procesador')
        self.client.force_login(cpu)
        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.client.get(reverse('admin:index'), {'hw_tarjeta': 'comercial'})
        sql = ' '.join(consulta['sql'] for consulta in consultas.captured_queries)
        self.assertContains(respuesta, 'No tienes permiso para ver los pedidos.')
        self.assertNotContains(respuesta, '180000')
        self.assertNotContains(respuesta, '180.000')
        self.assertNotIn('core_pedido', sql)

        self.client.force_login(self.cliente)
        anonima = self.client.get(reverse('admin:index'), {'hw_tarjeta': 'comercial'})
        self.assertEqual(anonima.status_code, 302)
        self.assertIn('/admin/login/', anonima.url)
