"""Asigna el grupo Cliente a cuentas normales anteriores. No toca personal ni producción por sí solo."""
from django.core.management.base import BaseCommand

from core.cuentas import cuentas_normales_sin_cliente, obtener_grupo_cliente


class Command(BaseCommand):
    help = (
        'Asigna el grupo Cliente a los usuarios normales que todavía no lo tienen. '
        'Omite personal, superusuarios y cuentas con permisos o grupos internos.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra cuántas cuentas se actualizarían, sin guardar cambios.',
        )

    def handle(self, *args, **options):
        grupo = obtener_grupo_cliente()
        permisos = grupo.permissions.count()
        if permisos:
            self.stdout.write(self.style.WARNING(
                f'El grupo Cliente tiene {permisos} permisos. No se eliminan.'
            ))
        candidatos = list(cuentas_normales_sin_cliente())
        if options['dry_run']:
            cantidad = len(candidatos)
            palabra = 'usuario' if cantidad == 1 else 'usuarios'
            self.stdout.write(f'Se asignaría el grupo Cliente a {cantidad} {palabra}.')
            for usuario in candidatos:
                self.stdout.write(f'  {usuario.username}')
            return
        for usuario in candidatos:
            usuario.groups.add(grupo)
        self.stdout.write(self.style.SUCCESS(f'Usuarios actualizados: {len(candidatos)}'))
