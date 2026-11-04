import importlib
from datetime import timedelta
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from core.catalogo.registry import CATALOGO_MODELOS
from core.chatbot.search import FiltrosCatalogo, buscar_catalogo
from core.models import ItemCarrito, Pedido, Procesador, Proveedor
from core.test_validacion_ux import crear_cpu


class OfertaYFechasTests(TestCase):
    def setUp(self):
        self.marca = Proveedor.objects.create(nombre='Marca Oferta')
        self.usuario = User.objects.create_user('oferta', 'oferta@example.com', 'clave-oferta')
        self.client.force_login(self.usuario)

    def test_la_oferta_se_valida_y_el_descuento_se_calcula(self):
        for oferta in (Decimal('0'), Decimal('-1'), Decimal('1000'), Decimal('1001')):
            cpu = Procesador(
                precio=Decimal('1000'),
                precio_oferta=oferta,
                en_oferta=True,
            )
            with self.assertRaises(ValidationError):
                cpu.clean()

        sin_precio = Procesador(precio=Decimal('1000'), en_oferta=True)
        with self.assertRaises(ValidationError):
            sin_precio.clean()

        valida = Procesador(
            precio=Decimal('1000'),
            precio_oferta=Decimal('750'),
            en_oferta=True,
        )
        valida.clean()
        self.assertEqual(valida.precio_vigente, Decimal('750'))
        self.assertEqual(valida.porcentaje_descuento, 25)
        valida.en_oferta = False
        self.assertEqual(valida.precio_vigente, Decimal('1000'))
        self.assertIsNone(valida.porcentaje_descuento)

        redondeo = Procesador(
            precio=Decimal('200'),
            precio_oferta=Decimal('133'),
            en_oferta=True,
        )
        self.assertEqual(redondeo.porcentaje_descuento, 34)

    def test_la_base_rechaza_ofertas_invalidas_sin_cambiar_el_id(self):
        cpu = crear_cpu(self.marca, 'CPU Oferta', Decimal('100000'), 3)
        pk = cpu.pk
        cpu.en_oferta = True
        cpu.precio_oferta = Decimal('80000')
        cpu.save()
        cpu.refresh_from_db()
        self.assertEqual(cpu.pk, pk)
        self.assertIsNotNone(cpu.creado_en)
        self.assertIsNotNone(cpu.actualizado_en)
        creado = cpu.creado_en
        cpu.nombre = 'CPU Oferta actualizada'
        cpu.save()
        cpu.refresh_from_db()
        self.assertEqual(cpu.creado_en, creado)
        self.assertGreater(cpu.actualizado_en, creado)
        self.assertEqual(cpu.pk, pk)

        for oferta, en_oferta in (
            (Decimal('0'), False),
            (Decimal('100000'), False),
            (Decimal('150000'), False),
            (None, True),
        ):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():
                    invalida = crear_cpu(
                        self.marca,
                        f'CPU invalida {oferta} {en_oferta}',
                        Decimal('100000'),
                        1,
                    )
                    Procesador.objects.filter(pk=invalida.pk).update(
                        precio_oferta=oferta,
                        en_oferta=en_oferta,
                    )

    def test_tienda_carrito_checkout_y_chat_usan_el_precio_vigente(self):
        oferta = crear_cpu(self.marca, 'CPU Oferta Visible', Decimal('200000'), 4)
        oferta.en_oferta = True
        oferta.precio_oferta = Decimal('40000')
        oferta.save()
        crear_cpu(self.marca, 'CPU Normal', Decimal('45000'), 4)
        pk_oferta = oferta.pk

        tienda = self.client.get(reverse('core:tienda'), {'precio': '0-50', 'orden': 'precio_asc'})
        self.assertContains(tienda, 'CPU Oferta Visible')
        self.assertContains(tienda, 'CPU Normal')
        self.assertContains(tienda, '-80%')
        self.assertContains(tienda, '<s>$200\xa0000</s>')
        self.assertContains(tienda, '$40\xa0000')
        nombres = [item[0].nombre for item in tienda.context['productos']]
        self.assertLess(nombres.index('CPU Oferta Visible'), nombres.index('CPU Normal'))

        cara = self.client.get(reverse('core:tienda'), {'precio': '100-250'})
        self.assertNotContains(cara, 'CPU Oferta Visible')
        self.assertNotContains(cara, 'CPU Normal')

        detalle = self.client.get(reverse('core:detalle', args=['procesador', oferta.pk]))
        self.assertContains(detalle, '-80%')
        self.assertContains(detalle, '<s>$200\xa0000 CLP</s>')
        self.assertContains(detalle, '$40\xa0000 CLP')

        self.client.post(reverse('core:agregar_al_carrito'), {
            'product_id': oferta.id,
            'model_name': 'procesador',
            'quantity': '1',
            'precio': '1',
            'total': '1',
        })
        item = ItemCarrito.objects.get()
        self.assertEqual(item.precio_unitario, Decimal('40000.00'))

        oferta.en_oferta = False
        oferta.precio_oferta = None
        oferta.save()
        item.precio_unitario = Decimal('200000.00')
        item.save(update_fields=['precio_unitario'])
        oferta.en_oferta = True
        oferta.precio_oferta = Decimal('80000')
        oferta.save()

        checkout = self.client.get(reverse('core:checkout'))
        self.assertEqual(checkout.status_code, 200)
        pedido = Pedido.objects.get()
        linea = pedido.items_pedido.get()
        self.assertEqual(linea.precio_unitario, Decimal('80000.00'))
        self.assertEqual(pedido.total_monto, Decimal('80000.00'))
        self.assertEqual(oferta.pk, pk_oferta)

        oferta.precio = Decimal('150000')
        oferta.precio_oferta = Decimal('70000')
        oferta.save()
        pedido.refresh_from_db()
        linea.refresh_from_db()
        self.assertEqual(linea.precio_unitario, Decimal('80000.00'))
        self.assertEqual(pedido.total_monto, Decimal('80000.00'))

        otro = self.client.get(reverse('core:checkout'))
        self.assertEqual(otro.status_code, 200)
        self.assertEqual(Pedido.objects.count(), 2)
        pedido.refresh_from_db()
        linea.refresh_from_db()
        self.assertEqual(linea.precio_unitario, Decimal('80000.00'))
        nuevo = Pedido.objects.exclude(pk=pedido.pk).get()
        self.assertEqual(nuevo.items_pedido.get().precio_unitario, Decimal('70000.00'))
        self.assertEqual(nuevo.total_monto, Decimal('70000.00'))

        chat = buscar_catalogo(FiltrosCatalogo(
            categoria='CPU',
            precio_max=75000,
            orden='precio_asc',
            limit=10,
        ))
        precios = [fila['precio_clp'] for fila in chat['results']]
        self.assertIn(70000, precios)
        self.assertNotIn(150000, precios)
        self.assertNotIn(200000, precios)

    def test_novedades_toma_los_30_mas_recientes_y_el_admin_edita_la_oferta(self):
        ahora = timezone.now()
        productos = [
            crear_cpu(self.marca, f'CPU {indice:02d}', Decimal('10000'), 1)
            for indice in range(31)
        ]
        for indice, cpu in enumerate(productos):
            Procesador.objects.filter(pk=cpu.pk).update(
                actualizado_en=ahora - timedelta(minutes=31 - indice),
            )
        Procesador.objects.filter(pk=productos[0].pk).update(actualizado_en=ahora)

        novedades = self.client.get(reverse('core:tienda'), {'novedades': '1'})
        self.assertEqual(novedades.context['total_productos'], 30)
        self.assertFalse(novedades.context['novedades_pendiente'])
        self.assertContains(novedades, 'más recientemente')
        self.assertContains(novedades, 'no una fecha histórica')
        visibles = [item[0].pk for item in novedades.context['productos']]
        self.assertEqual(visibles[0], productos[0].pk)
        self.assertNotIn(productos[1].pk, visibles)

        request = RequestFactory().get('/admin/')
        for modelo, _nombre in CATALOGO_MODELOS:
            nombres = {campo.name for campo in modelo._meta.concrete_fields}
            self.assertTrue(
                {'creado_en', 'actualizado_en', 'en_oferta', 'precio_oferta'} <= nombres,
            )
            registro = admin.site._registry[modelo]
            texto = str(registro.get_fieldsets(request))
            self.assertIn('en_oferta', texto)
            self.assertIn('precio_oferta', texto)
            self.assertIn('porcentaje_descuento', texto)
            self.assertIn('creado_en', texto)
            self.assertIn('en_oferta', registro.list_editable)
            self.assertIn('precio_oferta', registro.list_editable)
            self.assertIn('creado_en', registro.readonly_fields)
            self.assertIn('actualizado_en', registro.readonly_fields)

        migracion = importlib.import_module('core.migrations.0016_producto_fechas_oferta')
        separada = migracion.Migration.operations[0]
        self.assertEqual(len(migracion._MODELOS), 10)
        self.assertEqual(
            sum(1 for op in separada.state_operations if op.__class__.__name__ == 'AddField'),
            40,
        )
        sql = '\n'.join(op.sql for op in separada.database_operations)
        self.assertNotIn('DROP COLUMN', sql)
        self.assertEqual(sql.count('DEFAULT NOW()'), 20)
        self.assertEqual(sql.count('DEFAULT false'), 10)
        nombres_estado = {op.__class__.__name__ for op in separada.state_operations}
        self.assertNotIn('RemoveField', nombres_estado)
        self.assertNotIn('DeleteModel', nombres_estado)
        self.assertNotIn('AlterField', nombres_estado)
