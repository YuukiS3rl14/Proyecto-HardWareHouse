from io import StringIO

from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from core.cuentas import GRUPOS_PERSONAL, asignar_grupo_cliente

CLAVE = 'Clave-Segura-2026'


def datos_registro(username='cliente-nuevo', email='cliente-nuevo@example.com'):
    return {
        'username': username,
        'first_name': 'Ana',
        'last_name': 'Perez',
        'email': email,
        'password1': CLAVE,
        'password2': CLAVE,
    }


class GrupoClienteTests(TestCase):
    def test_el_registro_publico_asigna_cliente_sin_permisos_ni_personal(self):
        self.assertFalse(Group.objects.filter(name='Cliente').exists())
        respuesta = self.client.post(reverse('core:registro'), datos_registro())
        self.assertRedirects(respuesta, reverse('login'))
        usuario = User.objects.get(username='cliente-nuevo')
        grupo = Group.objects.get(name='Cliente')
        self.assertEqual(list(usuario.groups.all()), [grupo])
        self.assertEqual(grupo.permissions.count(), 0)
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertTrue(self.client.login(username='cliente-nuevo', password=CLAVE))

    def test_reutiliza_el_grupo_y_no_duplica_la_membresia(self):
        grupo = Group.objects.create(name='Cliente')
        self.client.post(reverse('core:registro'), datos_registro())
        usuario = User.objects.get(username='cliente-nuevo')
        asignar_grupo_cliente(usuario)
        self.assertEqual(Group.objects.filter(name='Cliente').count(), 1)
        self.assertEqual(usuario.groups.filter(pk=grupo.pk).count(), 1)

    def test_un_grupo_con_permisos_se_conserva_y_se_advierte(self):
        permiso = Permission.objects.get(codename='view_user')
        grupo = Group.objects.create(name='Cliente')
        grupo.permissions.add(permiso)
        with self.assertLogs('core.cuentas', level='WARNING') as aviso:
            self.client.post(reverse('core:registro'), datos_registro())
        grupo.refresh_from_db()
        self.assertEqual(list(grupo.permissions.all()), [permiso])
        self.assertIn('auth.view_user', aviso.output[0])
        self.assertTrue(User.objects.get(username='cliente-nuevo').groups.filter(pk=grupo.pk).exists())

    def test_un_registro_invalido_no_crea_cuenta_ni_toca_otros_grupos(self):
        otro = User.objects.create_user('cuenta-vieja', 'vieja@example.com', CLAVE)
        otro.groups.add(Group.objects.create(name='Vecinos'))
        datos = datos_registro()
        datos['password2'] = 'Clave-Distinta-2026'
        respuesta = self.client.post(reverse('core:registro'), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username='cliente-nuevo').exists())
        self.assertFalse(Group.objects.filter(name='Cliente').exists())
        self.assertEqual(list(otro.groups.values_list('name', flat=True)), ['Vecinos'])

    def test_el_admin_no_asigna_cliente_al_crear_un_trabajador(self):
        admin = User.objects.create_superuser('dueno', 'dueno@example.com', CLAVE)
        self.client.force_login(admin)
        respuesta = self.client.post(reverse('admin:auth_user_add'), {
            'username': 'trabajador-panel',
            'password1': CLAVE,
            'password2': CLAVE,
        })
        self.assertEqual(respuesta.status_code, 302)
        trabajador = User.objects.get(username='trabajador-panel')
        trabajador.is_staff = True
        trabajador.save(update_fields=['is_staff'])
        self.assertFalse(trabajador.groups.filter(name='Cliente').exists())
        self.assertFalse(admin.groups.filter(name='Cliente').exists())

    def test_el_comando_es_idempotente_y_omite_al_personal(self):
        normal = User.objects.create_user('cliente-viejo', 'viejo@example.com', CLAVE)
        normal.groups.add(Group.objects.create(name='Vecinos'))
        staff = User.objects.create_user('trabajador', 'trabajador@example.com', CLAVE, is_staff=True)
        superuser = User.objects.create_superuser('root', 'root@example.com', CLAVE)
        interno = User.objects.create_user('interno', 'interno@example.com', CLAVE)
        interno.groups.add(Group.objects.create(name=GRUPOS_PERSONAL[0]))
        con_permiso = User.objects.create_user('con-permiso', 'permiso@example.com', CLAVE)
        con_permiso.user_permissions.add(Permission.objects.get(codename='view_user'))

        preview = StringIO()
        call_command('asignar_grupo_cliente', '--dry-run', stdout=preview)
        texto = preview.getvalue()
        self.assertIn('Se asignaría el grupo Cliente a 1 usuario.', texto)
        self.assertIn('cliente-viejo', texto)
        self.assertNotIn('trabajador', texto)
        self.assertNotIn('root', texto)
        self.assertNotIn('interno', texto)
        self.assertFalse(normal.groups.filter(name='Cliente').exists())

        aplicado = StringIO()
        call_command('asignar_grupo_cliente', stdout=aplicado)
        self.assertIn('Usuarios actualizados: 1', aplicado.getvalue())
        normal.refresh_from_db()
        self.assertEqual(set(normal.groups.values_list('name', flat=True)), {'Vecinos', 'Cliente'})
        self.assertTrue(staff.is_staff)
        self.assertFalse(staff.groups.filter(name='Cliente').exists())
        self.assertFalse(superuser.groups.filter(name='Cliente').exists())
        self.assertFalse(interno.groups.filter(name='Cliente').exists())
        self.assertFalse(con_permiso.groups.filter(name='Cliente').exists())
        self.assertTrue(superuser.is_superuser)

        otra = StringIO()
        call_command('asignar_grupo_cliente', stdout=otra)
        self.assertIn('Usuarios actualizados: 0', otra.getvalue())
        self.assertEqual(normal.groups.filter(name='Cliente').count(), 1)
