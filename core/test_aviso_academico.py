from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.test_validacion_ux import crear_cpu
from core.models import Proveedor


class AvisoAcademicoTests(TestCase):
    def assert_aviso(self, respuesta):
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'id="avisoAcademico"', count=1)
        self.assertContains(respuesta, 'Aviso importante')
        self.assertContains(respuesta, 'HardWareHouse es un proyecto académico')
        self.assertContains(respuesta, 'Entendido, continuar')
        self.assertContains(respuesta, 'data-bs-backdrop="static"')
        self.assertContains(respuesta, 'data-bs-keyboard="false"')
        self.assertContains(respuesta, "localStorage.getItem('hwh_aviso_academico')")
        self.assertContains(respuesta, 'aviso-academico.js?v=aviso1')

    def test_las_paginas_publicas_incluyen_el_aviso_una_vez(self):
        marca = Proveedor.objects.create(nombre='Marca aviso')
        cpu = crear_cpu(marca, 'CPU aviso', Decimal('10000'), 2)
        usuario = User.objects.create_user('cliente-aviso', 'cliente-aviso@example.com', 'clave-aviso')
        self.client.force_login(usuario)
        rutas = (
            reverse('core:index'),
            reverse('core:tienda'),
            reverse('core:armado'),
            reverse('core:carrito'),
            reverse('core:detalle', args=['procesador', cpu.pk]),
        )
        for ruta in rutas:
            self.assert_aviso(self.client.get(ruta))

    def test_el_admin_no_incluye_el_aviso(self):
        staff = User.objects.create_superuser('staff-aviso', 'aviso@example.com', 'clave-aviso-admin')
        self.client.force_login(staff)
        respuesta = self.client.get(reverse('admin:index'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, 'id="avisoAcademico"')
        self.assertNotContains(respuesta, 'hwh_aviso_academico')

    def test_el_script_exige_la_aceptacion_guardada(self):
        texto = Path(__file__).resolve().parent.joinpath(
            'static', 'core', 'js', 'aviso-academico.js'
        ).read_text(encoding='utf-8')

        self.assertIn("localStorage.getItem(CLAVE) === '1'", texto)
        self.assertIn("localStorage.setItem(CLAVE, '1')", texto)
        self.assertIn("backdrop: 'static'", texto)
        self.assertIn('keyboard: false', texto)
        self.assertIn('evento.preventDefault()', texto)
