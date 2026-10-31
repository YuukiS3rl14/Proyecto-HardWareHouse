from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.catalogo_migracion import (
    CatalogoMigracionError,
    destino_legible,
    importar_documento,
    leer_documento,
)


class Command(BaseCommand):
    help = (
        'Compara un JSON de catálogo con la base actual e inserta solo faltantes. '
        'Sin --apply no escribe. --apply exige --confirmo-respaldo. '
        'No actualiza ni borra productos, precios, stock, proveedores, pedidos, '
        'boletas, IPN ni usuarios.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--archivo', required=True, help='JSON generado por exportar_catalogo.')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Fuerza el modo de solo lectura. Es el comportamiento por defecto.',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Inserta proveedores y productos que no existen. No actualiza nada.',
        )
        parser.add_argument(
            '--confirmo-respaldo',
            action='store_true',
            help='Confirma que hay un respaldo verificado de la base de destino.',
        )

    def handle(self, *args, **options):
        if options['apply'] and options['dry_run']:
            raise CommandError('Usa solo una opción: --dry-run o --apply.')
        if options['apply'] and not options['confirmo_respaldo']:
            raise CommandError(
                'Escritura cancelada. --apply exige --confirmo-respaldo '
                'después de verificar un respaldo de la base de destino.'
            )
        self.stdout.write(destino_legible())
        try:
            documento = leer_documento(Path(options['archivo']))
            resumen = importar_documento(documento, apply=options['apply'])
        except CatalogoMigracionError as exc:
            raise CommandError(str(exc)) from exc

        modo = 'apply' if resumen['apply'] else 'dry-run'
        self.stdout.write(f'Modo: {modo}')
        self.stdout.write(f"Proveedores por crear: {resumen['proveedores_crear']}")
        self.stdout.write(f"Proveedores reutilizados: {resumen['proveedores_reutilizar']}")
        self.stdout.write(f"Proveedores ambiguos, sin cambios: {resumen['proveedores_ambiguos']}")
        self.stdout.write(f"Productos por insertar: {resumen['insertar']}")
        self.stdout.write(f"Productos ya existentes, sin actualizar: {resumen['ya_existe']}")
        self.stdout.write(f"Existentes con datos distintos, sin actualizar: {resumen['distintos']}")
        self.stdout.write(f"Coincidencias ambiguas, sin insertar ni actualizar: {resumen['ambiguos']}")
        self._ejemplos(resumen)
        if resumen['apply']:
            self.stdout.write(self.style.SUCCESS('Altas de catálogo confirmadas. Lo demás no se modificó.'))
        else:
            self.stdout.write('Dry-run: no se escribió en la base.')

    def _ejemplos(self, resumen: dict) -> None:
        ambiguos = [item for item in resumen['productos'] if item['accion'] == 'ambiguo'][:20]
        distintos = [
            item for item in resumen['productos']
            if item['accion'] == 'ya_existe' and item['distinto']
        ][:20]
        for item in ambiguos:
            self.stdout.write(
                f"  ambiguo ({item['motivo']}): {item['familia']} / {item['proveedor']} / {item['nombre']}"
            )
        for item in distintos:
            self.stdout.write(
                f"  distinto, conservado: {item['familia']} / {item['proveedor']} / {item['nombre']}"
            )
